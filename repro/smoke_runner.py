"""
smoke_runner.py —— 真跑一次原仓库 runner（不是只匹配锚点）

每个任务只跑 1 个样本，验证这条链路：
  数据读取 -> patch_methods 注入的 elif 分支 -> DeepSeek API ->
  生成代码 -> subprocess 执行(python3 patch) -> 判分 -> 写盘

用法：
    python smoke_runner.py                          # 11 个 runner，默认 1_only_ques
    python smoke_runner.py --only gsm               # 只跑一个任务
    python smoke_runner.py --method All_code_CoT --only gsm
    python smoke_runner.py --methods all --only gsm   # 5 个方法都跑一遍

注意 Text_code_summarizer 依赖同一任务已跑出的 All_text 和 All_code_CoT
结果，所以 --methods all 的顺序不能乱（PM.supported_methods 已排好）。
"""
import os
import sys
import re
import json
import time
import argparse
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import env_win                                     # noqa: E402
import patch_methods as PM                         # noqa: E402
from env_win import DS_MODEL                       # noqa: E402

SAVE_INPUT = os.path.join(HERE, "results", "smoke", "save_input")
SAVE_GATHER = os.path.join(HERE, "results", "smoke", "gather")
# runner 是用 'a' 模式追加 acc 日志的，目录不存在会直接 FileNotFoundError
os.makedirs(SAVE_INPUT, exist_ok=True)
os.makedirs(SAVE_GATHER, exist_ok=True)

from smoke_limits import limit as _limit_samples   # noqa: E402


def _log_count():
    try:
        with open(env_win.REPRO_LOG, encoding="utf-8") as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0


def _skip_count():
    """summarizer 找不到前置产物时会写 SKIPPED_NO_DEPS 并 continue，
    表面上不报错，所以单独数一下，别让"静默跳过"混进 PASS。"""
    p = os.path.join(SAVE_GATHER, f"acc_result_log_{DS_MODEL}.txt")
    try:
        with open(p, encoding="utf-8") as f:
            return f.read().count("SKIPPED_NO_DEPS")
    except FileNotFoundError:
        return 0


def run_one(task_key, method):
    modname = PM.RUNNER_MODULE[task_key]
    func_name = PM.RUNNER_FUNC[task_key]
    t0 = time.time()
    calls0 = _log_count()
    skip0 = _skip_count()
    # 守卫是进程级的一次性开关，同一进程里连着跑多个方法必须重置，
    # 否则第二个方法一进循环就 break（表现为 0 次调用、什么都没跑）
    import smoke_limits
    smoke_limits.reset()
    print("\n" + "=" * 70)
    print(f"## {task_key} / {method}  ({modname})")
    print("=" * 70)
    try:
        import importlib
        module = importlib.import_module(modname)

        # 源码裁剪：只跑 1 个样本
        _raw = open(module.__file__, encoding="utf-8").read()
        for _old, _new in PM.SOURCE_FIXES.get(task_key, ()):
            _raw = _raw.replace(_old, _new)
        src = env_win._whitelist_inject_source(
            os.path.abspath(module.__file__),
            _limit_samples(_raw, task_key, verbose=False))

        m = re.search(rf"^def {func_name}\(", src, re.M)
        if not m:
            print(f"  [FAIL] 找不到 {func_name}")
            return False, "no_func"
        start = m.start()
        m2 = re.search(r"^def ", src[m.end():], re.M)
        end = len(src) if not m2 else m.end() + m2.start()
        func_src = src[start:end]

        am = re.search(r"([ \t]*)if baseline_method_name == '1_only_ques':\n[ \t]*user_prompt_list = \[question\]\n",
                       func_src)
        if not am:
            print("  [FAIL] 锚点缺失")
            return False, "no_anchor"
        indent, anchor = am.group(1), am.group(0)

        tpl = PM._reindent_template(PM.INJECT_TEMPLATE, indent)
        dir_tpl, label = PM.CODE_DIR_MAP[task_key]
        tpl = tpl.replace("{CODE_DIR}", dir_tpl.format(m="{m}", model_name="{model_name}"))
        tpl = tpl.replace("{{_task_label}}", label)
        tpl = tpl.replace("{{model_name}}", "{model_name}")

        injected = func_src.replace(anchor, anchor + tpl, 1)
        injected = injected.replace("{m}", "{baseline_method_name}")

        _orig_src = module.__file__
        PM._install_helpers(module.__dict__)

        module.__dict__["__repro_patched_src__"] = injected
        code = compile(injected, _orig_src + "<smoke>", "exec")
        exec(code, module.__dict__)
        fn = module.__dict__[func_name]

        fn(SAVE_INPUT, SAVE_GATHER, DS_MODEL, method, "./llama3_8B_CodeSteer.yaml")
        dt = time.time() - t0
        calls = _log_count() - calls0
        skips = _skip_count() - skip0
        if skips:
            print(f"  [PART] {method} 有 {skips} 个样本因缺前置产物被跳过（0 次 API 调用）")
            return False, {"sec": round(dt, 1), "calls": calls,
                           "error": f"summarizer skipped {skips} sample(s)"}
        print(f"  [PASS] {method} 完成，用时 {dt:.1f}s，API 调用 {calls} 次")
        return True, {"sec": round(dt, 1), "calls": calls}
    except Exception as e:
        print(f"  [FAIL] {type(e).__name__}: {e}")
        traceback.print_exc()
        return False, f"{type(e).__name__}: {e}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="只跑一个任务")
    ap.add_argument("--method", default="1_only_ques")
    ap.add_argument("--methods", default=None, help="'all' 或逗号分隔")
    args = ap.parse_args()

    if args.methods == "all":
        methods = PM.supported_methods()
    elif args.methods:
        methods = [m.strip() for m in args.methods.split(",") if m.strip()]
    else:
        methods = [args.method]

    keys = [args.only] if args.only else list(PM.RUNNER_MODULE.keys())
    res = {}
    for k in keys:
        for meth in methods:
            ok, info = run_one(k, meth)
            res[f"{k}/{meth}"] = {"ok": ok, "info": info}

    print("\n" + "=" * 70)
    print("## 汇总")
    print("=" * 70)
    total_calls = 0
    for k, v in res.items():
        info = v["info"]
        if isinstance(info, dict):
            shown = f"{info['sec']}s / {info['calls']} calls"
            total_calls += info["calls"]
        else:
            shown = str(info)
        print(f"  {'PASS' if v['ok'] else 'FAIL'}  {k:40s} {shown}")
    print(f"\n  合计 API 调用 {total_calls} 次")
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    json.dump(res, open(os.path.join(HERE, "logs", "smoke_runner.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=str)
    sys.exit(0 if all(v["ok"] for v in res.values()) else 1)
