"""run_all.py —— 正式跑：11 个原仓库 runner + 字母句任务 × 5 个方法

与 smoke_runner 的区别：
  * 不用 smoke_limits（那个只让循环转一圈），改用 sample_cap 计数，
    每个 (任务, 方法) 跑满上限就停；
  * 结果落到 results/main/，不和冒烟混；
  * 断点续跑：跑过的 (任务, 方法) 记在 logs/main_run.json，重跑自动跳过（--force 覆盖）。

用法：
    python run_all.py --estimate            # 只估调用次数和耗时，不花钱
    python run_all.py                       # 全跑
    python run_all.py --tasks gsm,game24    # 只跑几个
    python run_all.py --methods 1_only_ques # 只跑一个方法
    python run_all.py --cap 20              # 改每任务样本上限
    python run_all.py --force               # 忽略已完成记录
"""
import os
import re
import sys
import json
import time
import argparse
import importlib
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import env_win                                      # noqa: E402
import patch_methods as PM                          # noqa: E402
import sample_cap                                   # noqa: E402
from env_win import DS_MODEL                        # noqa: E402

THINK = env_win.THINK_MODE                       # off / strip / on，读环境变量
# 并行分片时用 --state-tag 区分记录文件，各 worker 互不覆盖
_STATE_TAG = os.environ.get("REPRO_STATE_TAG", "main")
_DIR_TAG = os.environ.get("REPRO_DIR_TAG", "").strip()
RESULTS = os.path.join(HERE, "results", _DIR_TAG or f"main_{THINK}")
SAVE_INPUT = os.path.join(RESULTS, "save_input")
SAVE_GATHER = os.path.join(RESULTS, f"gather_{_STATE_TAG}")   # 分片各写各的，避免并发追加打乱
STATE_PATH = os.path.join(HERE, "logs", f"main_run_{THINK}_{_STATE_TAG}.json")

# 每个任务"天然"有多少样本（runner 循环本身决定的），用来算估计值。
# bbh 是 4 个子集 × 250 例 / 每 4 例取 1 = 252；其余来自循环结构。
NATURAL = {
    "game24": 50, "number_multiply": 60, "letters": 75, "gsm": 53,
    "MATH_geometry": 50, "MATH_cp": 50, "big_bench_hard": 252,
    "BoxNet1": 30, "blocksworld": 48, "BoxLift": 20, "path_plan": 100,
    "letters_sentence": 64,
}
# bbh 内含 4 个独立子任务，上限按 4 倍给，否则只有第一个子集有样本
CAP_MULT = {"big_bench_hard": 4}

TASK_ORDER = list(PM.RUNNER_MODULE.keys()) + ["letters_sentence"]
METHOD_ORDER = PM.supported_methods()


def _log_count():
    try:
        with open(env_win.REPRO_LOG, encoding="utf-8") as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0


def _load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


def _calls_per_sample():
    """从冒烟日志里读每个 (任务, 方法) 跑 1 个样本用了几次 API。"""
    p = os.path.join(HERE, "logs", "smoke_runner.json")
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    out = {}
    for k, v in d.items():
        info = v.get("info")
        if isinstance(info, dict) and info.get("calls"):
            out[k] = info["calls"]
    return out


def estimate(cap):
    cps = _calls_per_sample()
    rows, tot_samples, tot_calls = [], 0, 0
    for task in TASK_ORDER:
        n = min(cap * CAP_MULT.get(task, 1), NATURAL.get(task, cap))
        per = [cps.get(f"{task}/{m}", 3) for m in METHOD_ORDER]
        c = sum(n * p for p in per)
        rows.append((task, n, sum(per), c))
        tot_samples += n * len(METHOD_ORDER)
        tot_calls += c
    print(f"{'任务':<18}{'样本/方法':>10}{'5方法调用/样本':>16}{'预计调用':>12}")
    print("-" * 58)
    for t, n, per, c in rows:
        print(f"{t:<18}{n:>10}{per:>16}{c:>12}")
    print("-" * 58)
    print(f"{'合计':<18}{tot_samples:>10}{'':>16}{tot_calls:>12}")
    # 冒烟实测：约 1.2s/次调用（含代码执行）
    print(f"\n预计耗时 ≈ {tot_calls * 1.2 / 3600:.1f} 小时（按 1.2s/次调用估）")
    return tot_calls


def _inject_cap(src, key, key_expr=None, guard_mode="raise"):
    """在每个 `total_sample_num += 1` 上面插一句守卫（同缩进）。

    key_expr：计数键的表达式。big_bench_hard 一个 runner 里跑 4 个子任务，
    必须按子任务分别计数（否则第一个子任务就把配额吃光，后面的全是 0 样本）。
    guard_mode：
      - "raise"：配额用完抛 _ReproStop 结束整个 runner（普通任务用，能穿透多重循环）
      - "break"：配额用完只 break 当前循环（bbh 用，否则第一个子任务就把
                 后面三个子任务的循环一起抛掉了）
    """
    pat = re.compile(r"^([ \t]*)total_sample_num\s*\+=\s*1[ \t]*$", re.M)
    action = ("raise __import__('sample_cap')._ReproStop()" if guard_mode == "raise"
              else "break")
    guard = (r"\1if __import__('sample_cap').tick(" + (key_expr or repr(key)) +
             r"):\n\1    " + action + "\n")
    return pat.sub(guard + r"\1total_sample_num += 1", src)


def run_runner(task, method, cap):
    modname = PM.RUNNER_MODULE[task]
    func_name = PM.RUNNER_FUNC[task]
    module = importlib.import_module(modname)

    src = open(module.__file__, encoding="utf-8").read()
    src = env_win._whitelist_inject_source(os.path.abspath(module.__file__), src)
    for old, new in PM.SOURCE_FIXES.get(task, ()):
        if old not in src:
            print(f"[warn] {task} 目录修正未命中: {old}")
        src = src.replace(old, new)

    key = f"{task}#{method}"
    if task == "big_bench_hard":
        # 四个子任务各自计数：键里带上 env_name
        src = _inject_cap(src, key, key_expr=f"{key!r} + '/' + str(env_name)",
                          guard_mode="break")
    else:
        src = _inject_cap(src, key)
    # 守卫读的是模块级 CAP，不设的话永远按默认 50 跑，--cap 就白给了
    sample_cap.CAP = cap * (1 if task == "big_bench_hard" else CAP_MULT.get(task, 1))

    m = re.search(rf"^def {func_name}\(", src, re.M)
    if not m:
        raise RuntimeError(f"{module.__file__} 找不到 {func_name}")
    m2 = re.search(r"^def ", src[m.end():], re.M)
    end = len(src) if not m2 else m.end() + m2.start()
    func_src = src[m.start():end]

    am = re.search(r"([ \t]*)if baseline_method_name == '1_only_ques':\n"
                   r"[ \t]*user_prompt_list = \[question\]\n", func_src)
    if not am:
        raise RuntimeError(f"{func_name}: 找不到 1_only_ques 锚点")
    indent, anchor = am.group(1), am.group(0)

    tpl = PM._reindent_template(PM.INJECT_TEMPLATE, indent)
    dir_tpl, label = PM.CODE_DIR_MAP[task]
    tpl = tpl.replace("{CODE_DIR}", dir_tpl.format(m="{m}", model_name="{model_name}"))
    tpl = tpl.replace("{{_task_label}}", label)
    tpl = tpl.replace("{{model_name}}", "{model_name}")

    injected = func_src.replace(anchor, anchor + tpl, 1)
    injected = injected.replace("{m}", "{baseline_method_name}")

    PM._install_helpers(module.__dict__)
    code = compile(injected, module.__file__ + "<run_all>", "exec")
    exec(code, module.__dict__)
    fn = module.__dict__[func_name]

    sample_cap.reset()
    try:
        fn(SAVE_INPUT, SAVE_GATHER, DS_MODEL, method, "./llama3_8B_CodeSteer.yaml")
    except sample_cap._ReproStop:
        pass
    return sample_cap.done(key)


def run_letters_sentence(method, cap):
    import run_letters_sentence as LS
    tasks = LS.build_tasks()[:cap]
    sample_cap.reset()
    s = LS.run_one_method(method, tasks)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default=None, help="逗号分隔，默认全部")
    ap.add_argument("--methods", default=None, help="逗号分隔，默认 5 个全跑")
    ap.add_argument("--cap", type=int, default=None, help="每任务样本上限")
    ap.add_argument("--force", action="store_true", help="忽略已完成记录")
    ap.add_argument("--estimate", action="store_true", help="只估计，不跑")
    ap.add_argument("--list", action="store_true", help="列出任务与方法名")
    args = ap.parse_args()

    if args.list:
        print("tasks:", ", ".join(TASK_ORDER))
        print("methods:", ", ".join(METHOD_ORDER))
        return

    cap = args.cap or int(os.environ.get("REPRO_CAP", "50"))
    if args.estimate:
        estimate(cap)
        return

    tasks = ([t.strip() for t in args.tasks.split(",")] if args.tasks else TASK_ORDER)
    methods = ([m.strip() for m in args.methods.split(",")] if args.methods
               else METHOD_ORDER)
    os.makedirs(SAVE_INPUT, exist_ok=True)
    os.makedirs(SAVE_GATHER, exist_ok=True)

    state = _load_state()
    print(f"think_mode={THINK}   结果目录={RESULTS}   记录={STATE_PATH}")
    grand_t0 = time.time()
    for task in tasks:
        for method in methods:
            key = f"{task}/{method}"
            if key in state and state[key].get("ok") and not args.force:
                print(f"[skip] {key} 已完成（{state[key].get('sec')}s）")
                continue
            print("\n" + "=" * 72)
            print(f"## {key}   cap={cap * CAP_MULT.get(task, 1)}")
            print("=" * 72)
            c0 = _log_count()
            t0 = time.time()
            try:
                if task == "letters_sentence":
                    info = run_letters_sentence(method, cap)
                    n = info.get("n", 0)
                else:
                    n = run_runner(task, method, cap)
                ok, err = True, None
            except Exception as e:
                n = sample_cap.done(f"{task}#{method}")
                ok, err = False, f"{type(e).__name__}: {e}"
                traceback.print_exc()
            dt = round(time.time() - t0, 1)
            calls = _log_count() - c0
            state[key] = {"ok": ok, "sec": dt, "calls": calls, "samples": n,
                          "error": err, "done_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            _save_state(state)
            print(f"  -> {'OK' if ok else 'FAIL'} {n} samples, {calls} calls, {dt}s"
                  + (f"  {err}" if err else ""))

    print(f"\n全部结束，总耗时 {(time.time() - grand_t0) / 3600:.2f} 小时")
    print(f"记录见 {STATE_PATH}")


if __name__ == "__main__":
    main()
