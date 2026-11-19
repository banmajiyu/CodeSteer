"""复现 runner 的代码执行方式，检查某个样本的 code_1_0.py 到底输出了什么。

用法：
    python check_code_exec.py <样本目录>
"""
import os
import subprocess
import sys


def main():
    d = sys.argv[1]
    code = os.path.join(d, "code_1_0.py")
    if not os.path.exists(code):
        print("没有 code_1_0.py：", code)
        return 1
    print("代码前 200 字：")
    print(open(code, encoding="utf-8", errors="replace").read()[:200])
    for expr in ("result", "Answer", "answer"):
        cmd = [sys.executable, "-c", f"exec(open(r'{code}').read()); print({expr})"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        print(f"\n--- 尝试 print({expr}) ---")
        print("stdout:", repr(r.stdout[:300]))
        err = (r.stderr or "").strip().splitlines()
        print("stderr:", err[-1] if err else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
