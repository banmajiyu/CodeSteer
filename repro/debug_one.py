"""单样本调试：真的跑一个 number_multiply / All_code_CoT 样本，并把每次代码执行的结果打出来。

用法（在 repro 目录下）：
    set THINK_MODE=strip
    python -X utf8 debug_one.py
"""
import os
import subprocess
import sys

os.environ.setdefault("THINK_MODE", "strip")
os.environ["REPRO_LOG"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "llm_calls_debug.jsonl")

import env_win  # noqa: F401  patch 必须最先装好
import sample_cap
import patch_methods as PM

DBG = os.path.join(env_win.HERE, "results", "dbg")
SAVE_INPUT = os.path.join(DBG, "save_input")
SAVE_GATHER = os.path.join(DBG, "gather")
os.makedirs(SAVE_INPUT, exist_ok=True)
os.makedirs(SAVE_GATHER, exist_ok=True)

# 记录每次代码执行
_orig_run = subprocess.run


def logged_run(cmd, *a, **kw):
    r = _orig_run(cmd, *a, **kw)
    try:
        if isinstance(cmd, str):
            short = "[STR] " + cmd[-300:]
        else:
            short = " ".join(str(c) for c in cmd)[-160:]
        print("  [exec] cmd=...%s\n         rc=%s stdout=%r stderr=%r"
              % (short, r.returncode, (r.stdout or "")[:120], (r.stderr or "")[:120]), flush=True)
    except Exception:
        pass
    return r


subprocess.run = logged_run
env_win.subprocess.run = logged_run

sample_cap.reset()
sample_cap.CAP = 1

r = subprocess.run(["python3", "-c", "print(6*7)"], capture_output=True, text=True, timeout=15)
print("自检 subprocess: rc=%s stdout=%r stderr=%r" % (r.returncode, r.stdout, r.stderr[:100]), flush=True)

import importlib

task = "number_multiply"
method = "All_code_CoT"
mod = importlib.import_module(PM.RUNNER_MODULE[task])
print("runner module:", mod.__name__, flush=True)
PM.patch_runner(
    task, mod,
    save_input_dir=SAVE_INPUT,
    gather_save_input_dir=SAVE_GATHER,
    model_name=env_win.DS_MODEL,
    baseline_method_name=method,
    args_path="./llama3_8B_CodeSteer.yaml",
)
print("done", flush=True)
