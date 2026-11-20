"""检查 success_failure.txt 的取值分布：确认没有"其实答对了但写的是 success/其它"的情况。"""
import glob
import os
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

TASKS = ["game24", "number_multiply", "letters", "gsm", "MATH_geometry", "MATH_cp",
         "big_bench_hard", "boxnet1", "blocksworld", "boxlift", "path_plan"]

for mode in ["off", "strip", "on"]:
    root = os.path.join("results", f"main_{mode}", "save_input")
    if not os.path.isdir(root):
        continue
    print(f"\n===== [{mode}] =====")
    for t in TASKS:
        vals = Counter()
        for sf in glob.glob(os.path.join(root, f"result_{t}_*", "**", "success_failure.txt"), recursive=True):
            try:
                vals[open(sf, encoding="utf-8", errors="ignore").read().strip()] += 1
            except Exception:
                vals["<ERR>"] += 1
        if not vals:
            print(f"  {t:<16} （无）")
            continue
        top = ", ".join(f"{k!r}:{v}" for k, v in vals.most_common(5))
        print(f"  {t:<16} 共 {sum(vals.values()):>4} 个  取值: {top}")
