"""统计三组里有"空响应"的样本比例 —— 检验 2500 预算的截断影响面。

用法: python -X utf8 truncation_audit.py [--per-task-cap 25]
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)

import summarize as S  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--per-task-cap", type=int, default=25)
args = ap.parse_args()
cap = args.per_task_cap

for mode in ("off", "strip", "on"):
    total = empty = 0
    per_task = {}
    for d in glob.glob(f"results/main_{mode}/save_input/result_*_deepseek-flash*"):
        files = S._sample_files(d, cap)
        for f in files:
            cj = os.path.join(os.path.dirname(f), "conversation_data.json")
            if not os.path.exists(cj):
                continue
            try:
                j = json.load(open(cj, encoding="utf-8"))
            except Exception:
                continue
            rs = j.get("response_list") or []
            total += 1
            if not rs or any((not str(r).strip()) for r in rs):
                empty += 1
                name = os.path.basename(d)
                per_task[name] = per_task.get(name, 0) + 1
    print(f"{mode:6s} samples={total:5d}  has_empty_response={empty:4d} ({100.0*empty/max(total,1):.1f}%)")
    for k, v in sorted(per_task.items(), key=lambda x: -x[1])[:6]:
        print(f"        {k}: {v}")
