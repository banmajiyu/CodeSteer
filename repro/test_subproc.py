"""验证 env_win 的 subprocess.run 补丁：捕获"先 print、后 NameError"的脚本输出。

用法：
    python test_subproc.py [code文件路径]
"""
import os
import subprocess
import sys

import env_win  # noqa: F401

code = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    env_win.HERE, "results", "main_strip", "save_input",
    "result_MATH_geometry_All_code_CoT_deepseek-flash", "Sample_1", "code_1_0.py")

for expr in ("result", "Answer"):
    r = subprocess.run(
        ["python3", "-c", f"exec(open(r'{code}').read()); print({expr})"],
        capture_output=True, text=True, timeout=15)
    print(f"[{expr}] rc={r.returncode} stdout={r.stdout!r} stderr_tail={(r.stderr or '').strip().splitlines()[-1:]!r}")
