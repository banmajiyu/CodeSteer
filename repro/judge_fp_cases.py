"""打印裁判判对、但本地精确比较算错的样本，用于人工确认是谁错了。"""
import json
import os
import glob

from judge_validate import DATASETS, last_boxed_only_string, remove_boxed, read, same, to_val

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

show = 0
for taskname, ddir in DATASETS.items():
    targets = {}
    for fn in os.listdir(ddir):
        if fn.endswith(".json"):
            try:
                d = json.load(open(os.path.join(ddir, fn), encoding="utf-8"))
            except Exception:
                continue
            t = remove_boxed(last_boxed_only_string(d.get("solution", "")))
            if t:
                targets[fn[:-5]] = t

    for mode in ["off"]:
        root = os.path.join("results", f"main_{mode}", "save_input")
        for sf in glob.glob(os.path.join(root, f"result_{taskname}_*", "**", "success_failure.txt"),
                            recursive=True):
            d = os.path.dirname(sf)
            sid = os.path.basename(d).replace("Sample_", "")
            if sid not in targets or read(sf) != "True":
                continue
            a1 = read(os.path.join(d, "extracted_answer_1.txt"))
            a2 = read(os.path.join(d, "extracted_answer_2.txt"))
            if same(a1, targets[sid]) or same(a2, targets[sid]):
                continue
            show += 1
            print(f"\n[{show}] {taskname} / {os.path.basename(os.path.dirname(d))} / Sample_{sid}")
            print(f"   标准答案 : {targets[sid]!r}   (sympy: {to_val(targets[sid])})")
            print(f"   抽取答案1: {a1!r}   (sympy: {to_val(a1)})")
            print(f"   抽取答案2: {a2!r}   (sympy: {to_val(a2)})")
            if show >= 12:
                raise SystemExit
