"""定点探测：被 2500 预算截断的样本，给更大预算后正文会不会出来？

从 strip 结果里找出 response 为空的样本，用它的 conversation_data.json
还原 prompt，分预算 2500 / 8000 / 16000 重发，记录正文长度与是否把预算写满。

用法: python -X utf8 probe_truncation.py [--n 6]
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE          # env_win 导入后会 os.chdir(REPO)，路径必须提前固定成绝对路径
sys.path.insert(0, HERE)
os.chdir(HERE)
os.environ.setdefault("THINK_MODE", "strip")
os.environ["REPRO_LOG"] = os.path.join(BASE, "logs", "probe_truncation.jsonl")
import env_win  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=6)
ap.add_argument("--budgets", default="2500,8000,16000")
args = ap.parse_args()
budgets = [int(x) for x in args.budgets.split(",")]

cands = []
for cj in glob.glob(os.path.join(BASE, "results/main_strip/save_input/result_*/**/conversation_data.json"),
                    recursive=True):
    try:
        j = json.load(open(cj, encoding="utf-8"))
    except Exception:
        continue
    rs = j.get("response_list") or []
    if rs and all(str(r).strip() for r in rs):
        continue
    if not (j.get("question") and j.get("user_prompt_list")):
        continue
    cands.append(cj)
print(f"候选空响应样本: {len(cands)}")


def last_log():
    lines = open(os.environ["REPRO_LOG"], encoding="utf-8").read().strip().splitlines()
    return json.loads(lines[-1]) if lines else {}


rows = []
for cj in cands[:args.n]:
    j = json.load(open(cj, encoding="utf-8"))
    sys_msg = j.get("system_message") or ""
    upl = j["user_prompt_list"]
    prompt = upl[0] + j["question"] if len(upl) == 1 else upl[-1]
    msgs = ([{"role": "system", "content": sys_msg}] if sys_msg else []) + \
           [{"role": "user", "content": prompt}]
    rec = {"file": os.path.relpath(cj, HERE).replace("\\", "/"), "in_chars": len(prompt)}
    for b in budgets:
        os.environ["REPRO_THINK_TOKENS"] = str(b)
        try:
            out = env_win.ds_chat(msgs, max_tokens=b, tag="probe")
            lg = last_log()
            rec[f"b{b}"] = {"out_chars": len(out), "think_chars": lg.get("reasoning_chars"),
                            "completion": (lg.get("usage") or {}).get("completion_tokens"),
                            "hit_cap": (lg.get("usage") or {}).get("completion_tokens") == b}
        except Exception as e:  # noqa: BLE001
            rec[f"b{b}"] = {"error": str(e)[:200]}
        print(rec["file"], b, rec[f"b{b}"], flush=True)
    rows.append(rec)

json.dump(rows, open(os.path.join(BASE, "logs/probe_truncation.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("saved logs/probe_truncation.json")
