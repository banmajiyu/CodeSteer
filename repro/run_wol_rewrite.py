"""题面改写实验：Web of Lies（原题 100% 饱和）的自造改写版 vs 原版。

问题：这个任务三组都 100%、五个方法毫无差异，是"真会"还是"见过"？
做法：同一个逻辑骨架（一条链式的真话/谎话推理 + 一个已知事实 + 一个追问），
      换掉场景、用词、人名、链长、追问位置，用传播算法算真值（不调 LLM 裁判）。
      同时用**同一个本地判分器**重跑原版 25 题，保证 apples-to-apples。

用法：
    python -X utf8 run_wol_rewrite.py --set both --method all
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(os.path.dirname(HERE), "CodeSteer-v1.0")

from env_win import ds_chat, THINK_MODE, DS_MODEL          # noqa: E402
from prompt import (text_output_prompt, with_COT_code_output_prompt,   # noqa: E402
                    AutoGen_prompt, combined_agent_prompt)

DATA = os.path.join(HERE, "data")
OUT_ROOT = os.path.join(HERE, "results", "wol_rewrite")
BBH = os.path.join(REPO, "dataset_gather", "BIG-Bench-Hard", "bbh", "web_of_lies.json")
N = 25
METHODS = ["1_only_ques", "All_text", "All_code_CoT", "AutoGen", "Text_code_summarizer"]

TASKS_JSON = os.path.join(DATA, "wol_rewrite_tasks.json")


# ---------------------------------------------------------------- 造题
NAMES = ["Voss", "Adair", "Pell", "Rune", "Kessler", "Odell", "Brandt", "Mercer",
         "Halloway", "Crane", "Tobias", "Vance", "Ellery", "Rowe", "Sable",
         "Winslow", "Durand", "Fisk", "Grimm", "Holt", "Ives", "Jarvis"]


def build_rewritten(force=False):
    """自造 25 题：链式真话/谎话，用传播算法算真值。"""
    if os.path.exists(TASKS_JSON) and not force:
        with open(TASKS_JSON, encoding="utf-8") as f:
            return json.load(f)

    rng = random.Random(20261119)
    items, tries = [], 0
    cap_each = (N + 1) // 2                       # 每类最多 13 题，保证 Yes/No 平衡
    cnt = {"Yes": 0, "No": 0}
    while len(items) < N and tries < 20000:
        tries += 1
        n = rng.choice([4, 5, 5, 6, 6, 7])
        names = rng.sample(NAMES, n)
        truth = [rng.random() < 0.5 for _ in range(n)]     # 各人的真实属性
        # 每条陈述由被问者的属性决定真假，所以陈述内容是确定的
        stmts = []
        for i in range(1, n):
            claim_true = "reports accurately" if truth[i - 1] else "fabricates"
            claim_false = "fabricates" if truth[i - 1] else "reports accurately"
            stmts.append(claim_true if truth[i] else claim_false)
        k = rng.randrange(1, n)                            # 追问的人（可中可末）
        lines = [f"Question: In the archive, every clerk either always reports accurately "
                 f"or always fabricates."]
        lines.append(f"Clerk {names[0]} "
                     + ("reports accurately." if truth[0] else "fabricates."))
        for i in range(1, n):
            lines.append(f"Clerk {names[i]} says Clerk {names[i-1]} {stmts[i-1]}.")
        lines.append(f"Does Clerk {names[k]} report accurately?")
        q = " ".join(lines)

        # 反向校验：从已知事实出发做传播，看能否唯一推出答案
        prop = [None] * n
        prop[0] = truth[0]
        for i in range(1, n):
            prev_says_true = stmts[i - 1] == "reports accurately"
            # 若 i 说真话 → 陈述为真 → prev 的属性与陈述一致；反之相反
            prop[i] = (prop[i - 1] == prev_says_true)
        if prop != truth:
            continue
        ans = "Yes" if truth[k] else "No"
        if cnt[ans] >= cap_each:                  # 该类别已满，换一题
            continue
        cnt[ans] += 1
        items.append({"id": len(items), "question": q, "n": n,
                      "ask_index": k, "answer": ans})
    if len(items) < N:
        sys.exit(f"只造出 {len(items)} 题，放宽约束再来")

    os.makedirs(DATA, exist_ok=True)
    with open(TASKS_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    yes = sum(1 for it in items if it["answer"] == "Yes")
    print(f"[wol] 自造 {len(items)} 题（Yes {yes} / No {len(items)-yes}）-> {TASKS_JSON}")
    return items


def build_original():
    """原版：从数据集里按 Yes/No 平衡取 25 题（13 Yes + 12 No），和改写版对齐。

    直接取前 25 题会得到 10 Yes / 15 No，一个"永远答 No"的模型就能白拿 60%，
    而改写版是 13/12 —— 两个集合的基线不一致，比出来的差值不能信。
    """
    with open(BBH, encoding="utf-8") as f:
        d = json.load(f)
    yes, no, out = 0, 0, []
    for ex in d["examples"]:
        tgt = ex["target"].strip()
        if tgt == "Yes" and yes < 13:
            yes += 1
        elif tgt == "No" and no < 12:
            no += 1
        else:
            continue
        out.append({"id": len(out), "question": ex["input"].strip(), "answer": tgt})
        if len(out) >= N:
            break
    return out


# ---------------------------------------------------------------- 判分
def judge(text, item):
    """取最后一个 <<<...>>>；没有就找独立的 Yes/No。纯正则，不调 LLM。"""
    if not text:
        return False, "empty"
    cands = [m.group(1).strip() for m in re.finditer(r"<<<(.*?)>>>", text, re.S)]
    body = cands[-1] if cands else text
    m = re.search(r"\b(YES|NO)\b", body.upper())
    if not m:
        m = re.search(r"\b(YES|NO)\b", text.upper())
    if not m:
        return False, "no_match"
    got = "Yes" if m.group(1) == "YES" else "No"
    if got != item["answer"]:
        return False, f"wrong(got {got})"
    return True, "correct"


# ---------------------------------------------------------------- 执行代码
def extract_code(text):
    if not text:
        return None
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
    return m.group(1).strip() if m else None


def run_code(code, workdir):
    if not code:
        return ""
    path = os.path.join(workdir, "code_1_0.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    for var in ("result", "answer", "Answer"):
        try:
            r = subprocess.run([sys.executable, "-c",
                                f"exec(open(r'{path}').read()); print({var})"],
                               capture_output=True, text=True, timeout=30)
            if r.stdout.strip():
                return r.stdout
        except Exception:
            pass
    return ""


def make_prompt(method, item):
    q = item["question"]
    q += ("\nSurround the final answer with <<<content>>>, exactly <<<Yes>>> or <<<No>>>."
          "\nYour answer:\n")
    if method == "1_only_ques":
        return q
    if method == "All_text":
        return text_output_prompt + q
    if method == "All_code_CoT":
        return with_COT_code_output_prompt + q
    if method == "AutoGen":
        return AutoGen_prompt + q
    raise SystemExit(f"未知方法 {method}")


def run_one(method, items, variant):
    out_dir = os.path.join(OUT_ROOT, f"{variant}_{method}_{THINK_MODE}")
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    t0 = time.time()
    for k, it in enumerate(items):
        sdir = os.path.join(out_dir, f"sample_{it['id']}")
        os.makedirs(sdir, exist_ok=True)

        if method == "Text_code_summarizer":
            pt = os.path.join(OUT_ROOT, f"{variant}_All_text_{THINK_MODE}",
                              f"sample_{it['id']}", "conversation_data.json")
            pc = os.path.join(OUT_ROOT, f"{variant}_All_code_CoT_{THINK_MODE}",
                              f"sample_{it['id']}", "conversation_data.json")
            if not (os.path.exists(pt) and os.path.exists(pc)):
                rows.append({"id": it["id"], "correct": None, "reason": "skipped_no_deps"})
                continue
            r_text = json.load(open(pt, encoding="utf-8"))["response"]
            r_code = json.load(open(pc, encoding="utf-8"))["response"]
            base = it["question"] + ("\nSurround the final answer with <<<content>>>, "
                                     "exactly <<<Yes>>> or <<<No>>>.\nYour answer:\n")
            prompt = combined_agent_prompt + "###The input question is: \n" + base + "\n\n"
            prompt += f"\nThe response from Agent_1 is: {r_text}"
            prompt += f"\n\nThe response from Agent_2 is: {r_code}"
            prompt += ("\n\nNow you need to analyze the problem based on their answers and "
                       "output final answer with the required format in the original question."
                       "\nYour analysis and answer:\n")
        else:
            prompt = make_prompt(method, it)

        print(f"[{variant}/{method}/{THINK_MODE}] {k+1}/{len(items)} id={it['id']} "
              f"ans={it['answer']}")
        try:
            resp = ds_chat([{"role": "user", "content": prompt}], model=DS_MODEL,
                           temperature=0.0, max_tokens=2000, tag=f"wol_{variant}_{method}")
        except Exception as e:
            rows.append({"id": it["id"], "correct": False, "reason": f"api_error:{e}"})
            print(f"  !! {e}")
            continue

        code = extract_code(resp)
        exec_out = run_code(code, sdir) if code else ""
        ok1, why1 = judge(resp, it)
        ok2, why2 = judge(exec_out, it) if exec_out else (False, "no_exec")
        ok = ok1 or ok2

        with open(os.path.join(sdir, "conversation_data.json"), "w", encoding="utf-8") as f:
            json.dump({"question": it["question"], "prompt": prompt, "response": resp,
                       "code": code, "exec_out": exec_out}, f, ensure_ascii=False, indent=1)
        rows.append({"id": it["id"], "answer": it["answer"], "correct": ok,
                     "reason": why1 if ok1 else why2, "used_code": bool(code)})
        print(f"  -> {'OK ' if ok else 'X  '} ({why1 if ok1 else why2})")

    graded = [r for r in rows if r.get("correct") is not None]
    c = sum(r["correct"] for r in graded)
    acc = c / len(graded) if graded else 0
    summary = {"variant": variant, "method": method, "think_mode": THINK_MODE,
               "n": len(graded), "correct": c, "acc": round(acc, 4),
               "elapsed_s": round(time.time() - t0, 1),
               "used_code": sum(1 for r in graded if r.get("used_code"))}
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "rows": rows}, f, ensure_ascii=False, indent=1)
    print(f"=== {variant}/{method}: {c}/{len(graded)} = {acc:.1%} ({summary['elapsed_s']}s)")
    return summary


def report():
    print("\n" + "=" * 62)
    print("Web of Lies：原版 vs 题面改写版（同一判分器、同一样本量）")
    print("=" * 62)
    print(f"  {'方法':24s} {'原版':>8s} {'改写版':>8s} {'差':>7s}")
    tot = {"orig": [], "rewrite": []}
    for m in METHODS:
        row = []
        for variant in ("orig", "rewrite"):
            p = os.path.join(OUT_ROOT, f"{variant}_{m}_{THINK_MODE}", "summary.json")
            if os.path.exists(p):
                j = json.load(open(p, encoding="utf-8"))["summary"]
                row.append(j["acc"] * 100)
                tot[variant].append(j["acc"])
            else:
                row.append(None)
        if row[0] is not None and row[1] is not None:
            print(f"  {m:24s} {row[0]:7.1f}% {row[1]:7.1f}% {row[1]-row[0]:+7.1f}")
        elif row[0] is not None:
            print(f"  {m:24s} {row[0]:7.1f}% {'--':>8s}")
    for variant in ("orig", "rewrite"):
        if tot[variant]:
            print(f"  平均（{variant}）: {sum(tot[variant])/len(tot[variant])*100:.1f}%")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="both", choices=["orig", "rewrite", "both"])
    ap.add_argument("--method", default="all")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()

    if a.report:
        report()
        sys.exit(0)

    sets = {}
    if a.set in ("orig", "both"):
        sets["orig"] = build_original()
    if a.set in ("rewrite", "both"):
        sets["rewrite"] = build_rewritten(force=a.rebuild)

    order = METHODS if a.method == "all" else [a.method]
    for variant, items in sets.items():
        for m in order:
            run_one(m, items, variant)
    report()
