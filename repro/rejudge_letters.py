"""离线重判 letters_sentence 任务：不调 API，只按修好的 parse_answer 重算分数。

背景：parse_answer 原来取第一个 <<<...>>>，开思考模式下推理里的中间猜测会被
误当答案（on 组被判成 12%）。改成取最后一个之后，用已保存的
conversation_data.json 重新判一遍即可，无需重跑模型。

用法: python -X utf8 rejudge_letters.py
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE
sys.path.insert(0, HERE)
os.chdir(HERE)

import run_letters_sentence as RLS  # noqa: E402

tasks = {t["id"]: t for t in RLS.build_tasks()}
METHODS = ["1_only_ques", "All_text", "All_code_CoT", "AutoGen", "Text_code_summarizer"]
OUT_ROOT = os.path.join(BASE, "results", "letters_sentence")

for mode in ("off", "strip", "on"):
    for method in METHODS:
        d = os.path.join(OUT_ROOT, f"{method}_{mode}")
        if not os.path.isdir(d):
            continue
        rows = []
        for sid, t in sorted(tasks.items()):
            cj = os.path.join(d, f"sample_{sid}", "conversation_data.json")
            if not os.path.exists(cj):
                continue
            j = json.load(open(cj, encoding="utf-8"))
            resp = j.get("response") or ""
            exec_out = j.get("exec_out") or ""
            ok1, why1 = RLS.judge(resp, t)
            ok2, why2 = RLS.judge(exec_out, t) if exec_out else (False, "no_exec")
            rows.append({"id": sid, "letter": t["letter"], "count": t["count"],
                         "num_words": t["num_words"],
                         "correct": bool(ok1 or ok2), "reason": why1 if ok1 else why2,
                         "used_code": bool(j.get("code"))})
        if not rows:
            continue
        acc = sum(r["correct"] for r in rows) / len(rows)
        summary = {"method": method, "think_mode": mode,
                   "n": len(rows), "correct": sum(r["correct"] for r in rows),
                   "acc": round(acc, 4), "by_letter": {}, "by_length": {}, "by_count": {}}
        for f_, key in (("letter", "by_letter"), ("count", "by_count")):
            for r in rows:
                e = summary[key].setdefault(str(r.get(f_)), {"n": 0, "c": 0})
                e["n"] += 1
                e["c"] += int(r["correct"])
        for r in rows:
            nw = r.get("num_words") or 0
            b = "8-12" if nw <= 12 else ("13-18" if nw <= 18 else "19-25")
            e = summary["by_length"].setdefault(b, {"n": 0, "c": 0})
            e["n"] += 1
            e["c"] += int(r["correct"])
        json.dump({"summary": summary, "rows": rows},
                  open(os.path.join(d, "summary.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"{mode:6s} {method:22s} {summary['correct']:3d}/{summary['n']:3d} = {acc:.1%}")
