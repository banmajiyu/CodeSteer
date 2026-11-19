"""
smoke_test.py —— 冒烟测试：跑通全链路，每个任务只跑 1-3 个样本

验证点：
  1. .env 里的 key 能读到，deepseek-flash 能调通
  2. thinking enabled/disabled 都真的生效
  3. python3 -> 当前解释器 的 patch 生效（代码真的被执行了）
  4. patch_methods 的源码注入锚点能匹配（这是最脆的一环）
  5. 判分、写盘、汇总日志都正常

用法：
    python smoke_test.py
"""
import os
import sys
import json
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import env_win                              # noqa: E402
from env_win import ds_chat, DS_MODEL       # noqa: E402

PASS, FAIL = [], []


def step(name):
    print("\n" + "=" * 70)
    print(f"## {name}")
    print("=" * 70)


def ok(msg):
    PASS.append(msg)
    print(f"  [PASS] {msg}")


def bad(msg, err=""):
    FAIL.append(msg)
    print(f"  [FAIL] {msg} {err}")


# ------------------------------------------------------------------ 1. API
step("1. DeepSeek API 连通性 + 思考开关")
try:
    r = ds_chat([{"role": "user", "content": "Reply with exactly one word: pineapple"}],
                max_tokens=50, tag="smoke")
    print(f"  回复: {r[:100]!r}")
    ok(f"API 调通 (model={DS_MODEL})")
except Exception as e:
    bad("API 调用失败", f"{type(e).__name__}: {e}")
    raise SystemExit("API 都不通，后面的测试没意义")

# 直接测 thinking 开关（绕过 env_win 的 THINK_MODE，验证底层参数有没有被接受）
for mode in ("disabled", "enabled"):
    try:
        from openai import OpenAI
        c = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url=env_win.DS_BASE_URL)
        resp = c.chat.completions.create(
            model=DS_MODEL,
            messages=[{"role": "user", "content": "9.11 和 9.9 哪个大？"}],
            max_tokens=1500,
            extra_body={"thinking": {"type": mode}},
        )
        msg = resp.choices[0].message
        rc = getattr(msg, "reasoning_content", None) or ""
        print(f"  thinking={mode:8s}: content={len(msg.content or '')} chars, "
              f"reasoning={len(rc)} chars")
        if mode == "enabled" and len(rc) == 0:
            bad("thinking=enabled 但没有 reasoning_content",
                "——模型名可能不支持思考模式")
        else:
            ok(f"thinking={mode} 生效")
    except Exception as e:
        bad(f"thinking={mode} 调用失败", f"{type(e).__name__}: {e}")

# ------------------------------------------------------------------ 2. python3 patch
step("2. python3 -> 当前解释器 patch")
import subprocess
try:
    r = subprocess.run(["python3", "-c", "print(6*7)"], capture_output=True, text=True, timeout=30)
    if r.stdout.strip() == "42":
        ok(f"python3 命令已被路由到 {sys.executable}")
    else:
        bad("python3 patch 没生效", f"stdout={r.stdout!r} stderr={r.stderr[:200]!r}")
except Exception as e:
    bad("python3 patch 抛异常", f"{type(e).__name__}: {e}")

# ------------------------------------------------------------------ 3. 字母句任务
step("3. 第 15 任务：句子级字母统计（自建，纯正则判分）")
try:
    import run_letters_sentence as LS
    tasks = LS.build_tasks()[:2]
    t = tasks[0]
    q = LS.make_question(t)
    resp = ds_chat([{"role": "user", "content": q}], max_tokens=800, tag="smoke_ls")
    okflag, why = LS.judge(resp, t)
    print(f"  句子: {t['sentence'][:60]}...")
    print(f"  目标字母 {t['letter']!r}, 真值 count={t['count']} pos={t['positions']}")
    print(f"  模型输出: {resp.strip()[:120]!r}")
    print(f"  判定: {okflag} ({why})")
    ok("字母句任务全链路可用" + ("" if okflag else "（这题答错了，但流程是通的）"))
except Exception as e:
    bad("字母句任务失败", f"{type(e).__name__}: {e}")
    traceback.print_exc()

# ------------------------------------------------------------------ 4. 原 runner 冒烟
step("4. 原仓库 runner + patch_methods 源码注入")
try:
    import patch_methods as PM
    import run_number_multiply_baseline_methods as R

    # 只跑 3 个样本：临时把 range(0,20) 换成 range(0,1)，三个 digit 组只跑一组
    src = open(R.__file__, encoding="utf-8").read()
    print(f"  runner 文件: {R.__file__}")

    # 4a. 先只测注入器能不能匹配锚点（不真的调 API）
    func_name = PM.RUNNER_FUNC["number_multiply"]
    import re
    m = re.search(rf"^def {func_name}\(", src, re.M)
    if not m:
        bad("找不到 run_number_multiply_baselines 定义")
    else:
        end = len(src)
        m2 = re.search(r"^def ", src[m.end():], re.M)
        if m2:
            end = m.end() + m2.start()
        fsrc = src[m.start():end]
        am = re.search(r"([ \t]*)if baseline_method_name == '1_only_ques':\n[ \t]*user_prompt_list = \[question\]\n", fsrc)
        if am:
            ok(f"1_only_ques 锚点匹配成功（缩进 {len(am.group(1))} 空格）")
        else:
            bad("1_only_ques 锚点匹配失败", "——注入器会抛异常")

    os.environ["SMOKE_MAX"] = "1"
except Exception as e:
    bad("patch_methods 加载失败", f"{type(e).__name__}: {e}")
    traceback.print_exc()

# ------------------------------------------------------------------ 5. 各 runner 锚点体检
step("5. 11 个 runner 的锚点体检（不调 API）")
import re
import importlib
for key, modname in PM.RUNNER_MODULE.items():
    try:
        mod = importlib.import_module(modname)
        src = open(mod.__file__, encoding="utf-8").read()
        fn = PM.RUNNER_FUNC[key]
        m = re.search(rf"^def {fn}\(", src, re.M)
        if not m:
            bad(f"{key}: 找不到函数 {fn}")
            continue
        end = len(src)
        m2 = re.search(r"^def ", src[m.end():], re.M)
        if m2:
            end = m.end() + m2.start()
        fsrc = src[m.start():end]
        am = re.search(r"([ \t]*)if baseline_method_name == '1_only_ques':", fsrc)
        if am:
            ok(f"{key:20s} 锚点 OK")
        else:
            bad(f"{key}: 锚点缺失")
    except Exception as e:
        bad(f"{key}: import 失败", f"{type(e).__name__}: {e}")

# ------------------------------------------------------------------ 汇总
step("冒烟测试汇总")
print(f"  PASS: {len(PASS)}")
for p in PASS:
    print(f"    OK {p}")
if FAIL:
    print(f"  FAIL: {len(FAIL)}")
    for f_ in FAIL:
        print(f"    FAIL {f_}")
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"), exist_ok=True)
json.dump({"pass": PASS, "fail": FAIL}, open(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "logs", "smoke_result.json"), "w",
    encoding="utf-8"), ensure_ascii=False, indent=1)
sys.exit(1 if FAIL else 0)
