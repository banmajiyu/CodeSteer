"""单样本调试：跑 blocksworld All_code_CoT 的 code_1_0.py，看 stdout/stderr。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import env_win  # noqa: F401  （装 subprocess / API 补丁）
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
d = sys.argv[1] if len(sys.argv) > 1 else "results/main_off/save_input/result_blocksworld_All_code_CoT_deepseek-flash/2_3_2_1"
code_path = os.path.abspath(os.path.join(env_win.REPO if hasattr(env_win, "REPO") else HERE, d))
if not os.path.exists(code_path):
    code_path = os.path.abspath(os.path.join(HERE, d))
print("code_path:", code_path, os.path.exists(code_path))
src = open(os.path.join(code_path, "code_1_0.py"), encoding="utf-8").read()
print("---- CODE ----")
print(src)
print("---- RUN ----")
cmd = [sys.executable, "-c", "exec(open(r'%s/code_1_0.py').read())" % code_path]
p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
print("rc =", p.returncode)
print("stdout:", repr(p.stdout))
print("stderr:", repr(p.stderr[-600:]))
