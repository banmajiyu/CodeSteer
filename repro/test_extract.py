"""单独测判分/抽取链路：把 runner 里用的 extract_equation_with_GPT4 拎出来打几个输入。

用法：
    python test_extract.py
"""
import sys

import env_win  # noqa: F401  必须最先导入，装好 patch

sys.path.insert(0, env_win.REPO)
sys.path.insert(0, env_win.os.path.join(env_win.REPO, "benchmark"))

from run_math_geometry_baseline_methods import extract_equation_with_GPT4, extract_and_check  # noqa: E402

CASES = [
    "<<<(18,-18)>>>",
    "<<<18>>>",
    "The answer is 18.",
    "```python\nprint(1+1)\n```",
    "No answer found",
]

for c in CASES:
    out = extract_equation_with_GPT4(c)
    got, _ = extract_and_check(out)
    print(f"输入 {c!r}\n  -> judge 返回 {out!r}\n  -> 抽取结果 {got!r}\n")
