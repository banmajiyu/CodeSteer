"""题面改写实验 2：数字乘法（Number Multiplying）。

背景：原题的形式是 `What is the result of 3*-45*6789?`——一个裸表达式。
      数字来自数据集（固定，不是每次随机生成，见
      benchmark/run_number_multiply_baseline_methods.py:157-158 读的是
      dataset_gather/number_multiply/.../input_value_list.txt）。

做法：**同一批数字、同一个判分器**，只改题面写法：
      orig    = 原版裸表达式
      rewrite = 交易台对账场景，三个「带符号的头寸调整」列成清单相乘
      真值用精确整数比较（不调 LLM 裁判）。

用法：
    python -X utf8 run_nm_rewrite.py --variant both --method all
    python -X utf8 run_nm_rewrite.py --report
"""
import argparse
import ast
import json
import os
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
OUT_ROOT = os.path.join(HERE, "results", "nm_rewrite")
NM_DIR = os.path.join(REPO, "dataset_gather", "number_multiply")
METHODS = ["1_only_ques", "All_text", "All_code_CoT", "AutoGen", "Text_code_summarizer"]

# 三个数字长度组，各取若干题，共 25 题
PLAN = [("digit_1_2_4", 9), ("digit_1_3_4", 8), ("digit_1_2_2_4", 8)]
TASKS_JSON = os.path.join(DATA, "nm_rewrite_tasks.json")


def build_tasks():
    if os.path.exists(TASKS_JSON):
        with open(TASKS_JSON, encoding="utf-8") as f:
            return json.load(f)
    items = []
    for group, n in PLAN:
        for i in range(n):
            d = os.path.join(NM_DIR, group, f"sample_{i}")
            vals = ast.literal_eval(open(os.path.join(d, "input_value_list.txt"),
                                         encoding="utf-8").read())
            tgt = int(open(os.path.join(d, "target_answer.txt"), encoding="utf-8").read())
            items.append({"id": len(items), "group": group, "sample": i,
                          "values": vals, "target": tgt})
    os.makedirs(DATA, exist_ok=True)
    with open(TASKS_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    print(f"[nm] {len(items)} 题 -> {TASKS_JSON}")
    return items


HARD_JSON = os.path.join(DATA, "nm_rewrite_hard.json")


def build_hard(force=False):
    """加难版：4 个因子，位数 [4,4,5,6]，乘积约 19~21 位。

    原版 25 题两个变体都是 100%，天花板了，看不出题面改写有没有影响；
    只有把算术本身加难，才能看出「模型是靠心算还是靠写代码」。
    """
    if os.path.exists(HARD_JSON) and not force:
        with open(HARD_JSON, encoding="utf-8") as f:
            return json.load(f)
    import random
    rng = random.Random(20261119)
    items = []
    while len(items) < 25:
        vals = []
        for d in (4, 4, 5, 6):
            v = rng.randint(10 ** (d - 1), 10 ** d - 1) * rng.choice([-1, 1])
            vals.append(v)
        tgt = 1
        for v in vals:
            tgt *= v
        items.append({"id": len(items), "group": "hard", "sample": len(items),
                      "values": vals, "target": tgt})
    os.makedirs(DATA, exist_ok=True)
    with open(HARD_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    print(f"[nm] 加难 {len(items)} 题（乘积 {len(str(items[0]['target']))} 位）-> {HARD_JSON}")
    return items


def make_question(it, variant):
    vals = it["values"]
    if variant.endswith("orig"):
        expr = "*".join(str(v) for v in vals)
        return f"What is the result of {expr}?"
    # rewrite：同一批数字，换成清单式场景，不出现 `*` 表达式
    lines = ["A trading desk must reconcile several signed position adjustments.",
             "Their values are:"]
    for k, v in enumerate(vals, 1):
        lines.append(f"  adjustment_{k} = {v}")
    lines.append("The net exposure is the product of all the adjustments.")
    lines.append("Compute the net exposure as an exact signed integer.")
    return "\n".join(lines)


def format_instruction():
    return ("\nSurround the final answer with <<<content>>>, "
            "exactly <<<the integer>>>.\nYour answer:\n")


# ---------------------------------------------------------------- 判分
def extract_numbers(text):
    """从 <<<...>>> 里抽整数；没有标记就看全文。返回 (列表, 用的文本)"""
    if not text:
        return [], ""
    cands = [m.group(1) for m in re.finditer(r"<<<(.*?)>>>", text, re.S)]
    body = cands[-1] if cands else text
    nums = []
    for tok in re.findall(r"-?\d[\d,]*", body):
        t = tok.replace(",", "")
        if t not in ("-", "") and re.fullmatch(r"-?\d+", t):
            nums.append(int(t))
    return nums, body


def judge(text, it):
    nums, body = extract_numbers(text)
    if it["target"] in nums:
        return True, "correct", body
    if not nums:
        return False, "no_number", body
    return False, f"wrong(got {nums[-1]})", body


# ---------------------------------------------------------------- 代码执行
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


def base_prompt(method, question, it, variant):
    q = question + format_instruction()
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
    rows, t0 = [], time.time()
    for k, it in enumerate(items):
        sdir = os.path.join(out_dir, f"sample_{it['id']}")
        os.makedirs(sdir, exist_ok=True)
        question = make_question(it, variant)

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
            prompt = (combined_agent_prompt + "###The input question is: \n"
                      + question + format_instruction() + "\n\n")
            prompt += f"\nThe response from Agent_1 is: {r_text}"
            prompt += f"\n\nThe response from Agent_2 is: {r_code}"
            prompt += ("\n\nNow you need to analyze the problem based on their answers and "
                       "output final answer with the required format in the original question."
                       "\nYour analysis and answer:\n")
        else:
            prompt = base_prompt(method, question, it, variant)

        print(f"[nm/{variant}/{method}/{THINK_MODE}] {k+1}/{len(items)} id={it['id']} "
              f"target={it['target']}")
        try:
            resp = ds_chat([{"role": "user", "content": prompt}], model=DS_MODEL,
                           temperature=0.0, max_tokens=2000, tag=f"nm_{variant}_{method}")
        except Exception as e:
            rows.append({"id": it["id"], "correct": False, "reason": f"api_error:{e}"})
            print(f"  !! {e}")
            continue

        code = extract_code(resp)
        exec_out = run_code(code, sdir) if code else ""
        ok1, why1, body = judge(resp, it)
        ok2, why2, _ = judge(exec_out, it) if exec_out else (False, "no_exec", "")
        ok = ok1 or ok2

        with open(os.path.join(sdir, "conversation_data.json"), "w", encoding="utf-8") as f:
            json.dump({"question": question, "prompt": prompt, "response": resp,
                       "code": code, "exec_out": exec_out}, f, ensure_ascii=False, indent=1)
        rows.append({"id": it["id"], "group": it["group"], "target": it["target"],
                     "correct": ok, "reason": why1 if ok1 else why2,
                     "used_code": bool(code)})
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
    def load(variant, m):
        p = os.path.join(OUT_ROOT, f"{variant}_{m}_{THINK_MODE}", "summary.json")
        if not os.path.exists(p):
            return None
        return json.load(open(p, encoding="utf-8"))["summary"]

    print("\n" + "=" * 64)
    print("数字乘法题面改写（同一批数字、同一判分器、精确整数比对）")
    print("=" * 64)
    for tag, v_orig, v_rew in (("原难度", "orig", "rewrite"),
                               ("加难度(4×4/4/5/6 位)", "hard_orig", "hard_rewrite")):
        print(f"\n  【{tag}】")
        print(f"  {'方法':24s} {'裸表达式':>9s} {'清单改写':>9s} {'差':>7s}")
        for m in METHODS:
            a, b = load(v_orig, m), load(v_rew, m)
            if a is None and b is None:
                continue
            x = f"{a['acc']*100:8.1f}%" if a else "      --"
            y = f"{b['acc']*100:8.1f}%" if b else "      --"
            d = f"{(b['acc']-a['acc'])*100:+7.1f}" if (a and b) else "     --"
            print(f"  {m:24s} {x} {y} {d}")

    # 加难版逐题错误类型（OnlyQ vs All_code_CoT）
    for variant in ("hard_orig", "hard_rewrite"):
        for m in ("1_only_ques", "All_code_CoT"):
            j = load(variant, m)
            if not j:
                continue
            rows = json.load(open(os.path.join(
                OUT_ROOT, f"{variant}_{m}_{THINK_MODE}", "summary.json"),
                encoding="utf-8"))["rows"]
            bad = [r for r in rows if r.get("correct") is False]
            code = sum(1 for r in rows if r.get("used_code"))
            print(f"\n  {variant}/{m}: {j['correct']}/{j['n']} = {j['acc']*100:.1f}%"
                  f"  写代码 {code}/{j['n']}  错 {len(bad)} 题")
            for r in bad[:5]:
                print(f"    id={r['id']:2d} target={r['target']} {r['reason']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="both",
                    choices=["orig", "rewrite", "both", "hard_orig", "hard_rewrite", "hard"])
    ap.add_argument("--method", default="all")
    ap.add_argument("--rebuild-hard", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()

    if a.report:
        report()
        sys.exit(0)

    easy = build_tasks()
    hard = build_hard(force=a.rebuild_hard)
    pools = {"orig": easy, "rewrite": easy, "hard_orig": hard, "hard_rewrite": hard}
    order = METHODS if a.method == "all" else [m.strip() for m in a.method.split(",") if m.strip()]
    for m in order:
        if m not in METHODS:
            print(f"未知方法 {m}，可选 {METHODS}")
            sys.exit(2)
    if a.variant == "both":
        variants = ["orig", "rewrite"]
    elif a.variant == "hard":
        variants = ["hard_orig", "hard_rewrite"]
    else:
        variants = [a.variant]
    for variant in variants:
        for m in order:
            run_one(m, pools[variant], variant)
    report()
