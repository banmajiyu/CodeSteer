# -*- coding: utf-8 -*-
"""抽查加难度版数字乘法的真实回答：确认 100% 不是判分放水造成的。"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)

OUT = os.path.join(HERE, "results", "nm_rewrite")

items = json.load(open(os.path.join(HERE, "data", "nm_rewrite_hard.json"), encoding="utf-8"))
by_id = {it["id"]: it for it in items}

for variant, method in (("hard_orig", "1_only_ques"), ("hard_rewrite", "1_only_ques"),
                        ("hard_orig", "All_code_CoT")):
    d = os.path.join(OUT, f"{variant}_{method}_off")
    rows = json.load(open(os.path.join(d, "summary.json"), encoding="utf-8"))["rows"]
    print("=" * 70)
    print(variant, method, "acc=", sum(1 for r in rows if r.get("correct")) / len(rows))
    for r in rows[:2]:
        it = by_id[r["id"]]
        sample = os.path.join(d, f"sample_{r['id']}")
        conv = json.load(open(os.path.join(sample, "conversation_data.json"), encoding="utf-8"))
        resp = conv["response"]
        print("-" * 70)
        print(f"id={r['id']} values={it['values']}")
        print(f"true product = {it['target']}")
        print(f"response 长度 {len(resp)}，前 200 字：")
        print(resp[:200].replace("\n", " | "))
        print("末尾 300 字：")
        print(resp[-300:].replace("\n", " | "))
        files = [f for f in os.listdir(sample) if f.endswith(".py")]
        print("代码文件:", files)
        # 独立复核：真值自洽
        p = 1
        for v in it["values"]:
            p *= v
        print("重算一致:", p == it["target"])
