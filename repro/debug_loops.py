"""诊断：每个 runner 找到的循环链是哪几行。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import smoke_limits as SL  # noqa: E402
from check_limits import CASES, BENCH  # noqa: E402

for task, fname in CASES:
    with open(os.path.join(BENCH, fname), encoding="utf-8") as fh:
        src = fh.read()
    loops = SL._enclosing_loops(src)
    lines = src.splitlines()
    print(f"=== {task}: {len(loops)} 层")
    for pos in loops:
        ln = src[:pos].count("\n") + 1
        print(f"    L{ln}: {lines[ln-1].strip()[:70]}")
    out = SL.limit(src, task, verbose=False)
    print(f"    guards={out.count(chr(95)*2+'import__')}")
