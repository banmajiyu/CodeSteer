"""测 stdout 型输入：纯数字/元组/带换行，看判分抽取器能否识别。"""
import sys

import env_win  # noqa: F401

sys.path.insert(0, env_win.REPO)
sys.path.insert(0, env_win.os.path.join(env_win.REPO, "benchmark"))

from run_number_multiply_baseline_methods import extract_equation_with_GPT4  # noqa: E402
from run_math_geometry_baseline_methods import extract_and_check  # noqa: E402

CASES = [
    "-171220551",
    "-171220551\n",
    "(18, -18)",
    "(18, -18)\n",
    "  -171220551  ",
]

for c in CASES:
    out = extract_equation_with_GPT4(c)
    got, _ = extract_and_check(out)
    print(f"输入 {c!r}\n  judge -> {out!r}\n  抽取  -> {got!r}\n")
