"""看守卫到底插在哪：python show_guards.py [task ...]"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import smoke_limits as SL  # noqa: E402
from check_limits import CASES, BENCH  # noqa: E402

want = sys.argv[1:]
for task, fname in CASES:
    if want and task not in want:
        continue
    with open(os.path.join(BENCH, fname), encoding="utf-8") as fh:
        src = fh.read()
    out = SL.limit(src, task, verbose=False)
    lines = out.splitlines()
    print("=" * 70)
    print(task)
    for i, line in enumerate(lines):
        if "__import__('smoke_limits').first" in line:
            lo = max(0, i - 3)
            for j in range(lo, min(len(lines), i + 3)):
                mark = ">>" if j == i else "  "
                print(f"{mark}{j+1:5d}| {lines[j]}")
            print("   " + "-" * 50)
