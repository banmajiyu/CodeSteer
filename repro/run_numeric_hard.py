# -*- coding: utf-8 -*-
"""数值计算加码实验：浮点数 + ln/根号/三角函数 复合表达式。

动机（用户 m02621）：整数乘法连 18 位都能心算全对，没有区分度；
换成「不规则小数 + 超越函数复合」后，手算几乎不可能，才能把
「必须写代码」和「靠语言推理」区分开。

设计要点：
1. 三档难度，各 12 题（固定种子，可复现）
   L1 单个函数：      ln(37.4821)
   L2 两三个函数组合：sqrt(17.34) * ln(2.7183) + sin(0.5021)
   L3 嵌套复合：      ln(sqrt(123.456) + exp(-0.7413))
2. 全部用**弧度**，题面明说，避免角度单位歧义造成假失败
3. 真值用 Python math 双精度算，判分用**相对误差**，并同时给出
   1e-3 / 1e-6 / 1e-9 三档通过率（容差口径透明，不靠单一口径下结论）
4. 每行记录相对误差，可以看「答错是差一点还是差很远」

用法：
    python -X utf8 run_numeric_hard.py --method 1_only_ques,All_text,All_code_CoT
    python -X utf8 run_numeric_hard.py --report
"""
import argparse
import json
import math
import os
import random
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)

from env_win import ds_chat, THINK_MODE, DS_MODEL          # noqa: E402
from prompt import (text_output_prompt, with_COT_code_output_prompt,   # noqa: E402
                    AutoGen_prompt, combined_agent_prompt)

DATA = os.path.join(HERE, "data")
OUT_ROOT = os.path.join(HERE, "results", "numeric_hard")
TASKS_JSON = os.path.join(DATA, "numeric_hard_tasks.json")
METHODS = ["1_only_ques", "All_text", "All_code_CoT", "AutoGen", "Text_code_summarizer"]
FUNCS = ["ln", "log10", "sqrt", "sin", "cos", "tan", "atan", "asin", "exp"]
TOL = {"loose": 1e-3, "main": 1e-6, "strict": 1e-9}


# ---------------------------------------------------------------- 造题
def _uni(rng, lo, hi, nd):
    """lo~hi 之间的不规则小数（nd 位小数），避免整数或熟数。"""
    v = rng.uniform(lo, hi)
    return round(v, nd)


def _eval_display(expr):
    """把展示式（ln/sqrt/sin...）换成 math.xxx 求值。"""
    def rep(m):
        name = m.group(1)
        return "math.log(" if name == "ln" else f"math.{name}("
    py = re.sub(r"\b(ln|log10|sqrt|sin|cos|tan|atan|asin|exp)\(", rep, expr)
    return float(eval(py, {"math": math}))


def build_tasks(force=False):
    if os.path.exists(TASKS_JSON) and not force:
        with open(TASKS_JSON, encoding="utf-8") as f:
            return json.load(f)

    rng = random.Random(20261120)
    items = []

    def add(level, expr):
        items.append({"id": len(items), "level": level, "expr": expr,
                      "target": _eval_display(expr)})

    # L1：单个函数套在不规则小数上
    # 注意取值范围：避开饱和区（asin→1、atan→∞、sin/cos→±1），饱和会让答案
    # 对输入不敏感，白送分，失去区分度
    singles = [
        ("ln", 8.0, 400.0, 4), ("log10", 2.0, 900.0, 3), ("sqrt", 8.0, 9000.0, 3),
        ("sin", 0.2, 1.2, 5), ("cos", 0.2, 1.2, 5), ("tan", 0.2, 1.1, 5),
        ("atan", 0.5, 8.0, 4), ("asin", 0.1, 0.7, 5), ("exp", 0.4, 3.0, 4),
    ]
    for i in range(12):
        fn, lo, hi, nd = singles[i % len(singles)]
        add("L1", f"{fn}({_uni(rng, lo, hi, nd)})")

    # L2：两个函数相乘/相加
    A_RANGE = {"sqrt": (1.5, 90.0, 4), "ln": (1.5, 90.0, 4),
               "log10": (1.5, 90.0, 4), "exp": (0.3, 2.5, 4)}
    B_RANGE = {"sin": (0.2, 1.2, 5), "cos": (0.2, 1.2, 5),
               "tan": (0.2, 1.1, 5), "atan": (0.5, 8.0, 4)}
    for i in range(12):
        a_fn = rng.choice(list(A_RANGE))
        b_fn = rng.choice(list(B_RANGE))
        a = f"{a_fn}({_uni(rng, *A_RANGE[a_fn])})"
        b = f"{b_fn}({_uni(rng, *B_RANGE[b_fn])})"
        op = rng.choice(["*", "+", "-"])
        c = ""
        if i % 3 == 0:
            c = f" + sqrt({_uni(rng, 2.0, 400.0, 3)})"
        add("L2", f"{a} {op} {b}{c}")

    # L3：嵌套复合
    for i in range(12):
        inner = rng.choice([
            f"sqrt({_uni(rng, 20.0, 900.0, 3)}) + exp(-{_uni(rng, 0.2, 2.0, 4)})",
            f"ln({_uni(rng, 5.0, 300.0, 3)}) * {_uni(rng, 0.5, 3.0, 4)}",
            f"sin({_uni(rng, 0.3, 1.3, 5)}) / sqrt({_uni(rng, 1.5, 60.0, 3)})",
            f"atan({_uni(rng, 1.0, 30.0, 3)}) + cos({_uni(rng, 0.2, 1.2, 5)})",
        ])
        outer = rng.choice(["ln", "sqrt", "atan", "exp", "sin"])
        tail = ""
        if i % 2 == 0:
            tail = f" * {_uni(rng, 0.4, 2.5, 4)}"
        add("L3", f"{outer}({inner}){tail}")

    os.makedirs(DATA, exist_ok=True)
    with open(TASKS_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    print(f"[num] {len(items)} 题 -> {TASKS_JSON}")
    for it in items[:3]:
        print(f"   {it['level']} {it['expr']} = {it['target']:.12g}")
    return items


# ---------------------------------------------------------------- 题面与判分
def make_question(it):
    return (
        "Compute the exact value of the following expression:\n\n"
        f"    {it['expr']}\n\n"
        "Rules:\n"
        "- ln is the natural logarithm, log10 is base 10, sqrt is the square root.\n"
        "- **All trigonometric functions take their argument in RADIANS.**\n"
        "- atan/asin are the principal values, in radians.\n"
        "- Report at least 10 significant digits (scientific notation is fine).\n"
        "Surround the final numeric value with <<<content>>>, exactly <<<the number>>>."
        "\nYour answer:\n"
    )


NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def parse_value(text):
    """从最后一个 <<<...>>> 里抠一个浮点数（兼容千分位、≈、单位）。"""
    if not text:
        return None, ""
    cands = [m.group(1) for m in re.finditer(r"<<<(.*?)>>>", text, re.S)]
    body = cands[-1] if cands else text
    body2 = body.replace(",", "")
    nums = NUM_RE.findall(body2)
    if not nums:
        return None, body
    for tok in reversed(nums):
        try:
            return float(tok), body
        except ValueError:
            continue
    return None, body


def rel_err(got, target):
    if got is None:
        return None
    denom = max(abs(target), 1e-12)
    return abs(got - target) / denom


def judge(text, it):
    got, body = parse_value(text)
    e = rel_err(got, it["target"])
    if e is None:
        return False, "not_numeric", None, body
    if e <= TOL["main"]:
        return True, f"ok(rel={e:.1e})", e, body
    return False, f"err(rel={e:.1e})", e, body


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
    # 模型常写 import mpmath（高精度库），已手动解压到 vendor；子进程要能 import 到
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(HERE, "vendor") + os.pathsep + env.get("PYTHONPATH", "")
    for var in ("result", "answer", "Answer"):
        try:
            r = subprocess.run([sys.executable, "-c",
                                f"exec(open(r'{path}').read()); print({var})"],
                               capture_output=True, text=True, timeout=30, env=env)
            if r.stdout.strip():
                return r.stdout
        except Exception:
            pass
    return ""


def base_prompt(method, question):
    if method == "1_only_ques":
        return question
    if method == "All_text":
        return text_output_prompt + question
    if method == "All_code_CoT":
        return with_COT_code_output_prompt + question
    if method == "AutoGen":
        return AutoGen_prompt + question
    raise SystemExit(f"未知方法 {method}")


def run_one(method, items):
    out_dir = os.path.join(OUT_ROOT, f"{method}_{THINK_MODE}")
    os.makedirs(out_dir, exist_ok=True)
    rows, t0 = [], time.time()
    for it in items:
        sdir = os.path.join(out_dir, f"sample_{it['id']}")
        os.makedirs(sdir, exist_ok=True)
        question = make_question(it)

        if method == "Text_code_summarizer":
            pt = os.path.join(OUT_ROOT, f"All_text_{THINK_MODE}",
                              f"sample_{it['id']}", "conversation_data.json")
            pc = os.path.join(OUT_ROOT, f"All_code_CoT_{THINK_MODE}",
                              f"sample_{it['id']}", "conversation_data.json")
            if not (os.path.exists(pt) and os.path.exists(pc)):
                rows.append({"id": it["id"], "level": it["level"], "correct": None,
                             "reason": "skipped_no_deps"})
                continue
            r_text = json.load(open(pt, encoding="utf-8"))["response"]
            r_code = json.load(open(pc, encoding="utf-8"))["response"]
            prompt = (combined_agent_prompt + "###The input question is: \n" + question)
            prompt += f"\nThe response from Agent_1 is: {r_text}"
            prompt += f"\n\nThe response from Agent_2 is: {r_code}"
            prompt += ("\n\nNow you need to analyze the problem based on their answers and "
                       "output final answer with the required format in the original question."
                       "\nYour analysis and answer:\n")
        else:
            prompt = base_prompt(method, question)

        print(f"[num/{method}/{THINK_MODE}] id={it['id']:2d} {it['level']} "
              f"{it['expr'][:46]:46s} target={it['target']:.10g}")
        cached = os.path.join(sdir, "conversation_data.json")
        if os.path.exists(cached):
            # 断点续跑：已有回答直接复用，不重复花钱
            try:
                conv = json.load(open(cached, encoding="utf-8"))
                resp, code, exec_out = conv["response"], conv.get("code"), conv.get("exec_out", "")
                print("  [cached]")
            except Exception:
                resp, code, exec_out = None, None, ""
        else:
            resp, code, exec_out = None, None, ""

        if resp is None:
            try:
                resp = ds_chat([{"role": "user", "content": prompt}], model=DS_MODEL,
                               temperature=0.0, max_tokens=2500, tag=f"num_{method}")
            except Exception as e:
                rows.append({"id": it["id"], "level": it["level"], "correct": False,
                             "reason": f"api_error:{e}"})
                print(f"  !! {e}")
                continue
            code = extract_code(resp)
            exec_out = run_code(code, sdir) if code else ""
            with open(cached, "w", encoding="utf-8") as f:
                json.dump({"question": question, "prompt": prompt, "response": resp,
                           "code": code, "exec_out": exec_out}, f, ensure_ascii=False, indent=1)

        ok1, why1, e1, _ = judge(resp, it)
        ok2, why2, e2, _ = judge(exec_out, it) if exec_out else (False, "no_exec", None, "")
        ok = ok1 or ok2
        row = {"id": it["id"], "level": it["level"], "expr": it["expr"],
               "target": it["target"], "correct": ok,
               "reason": why1 if ok1 else (why2 if ok2 else why1),
               "rel_err": e1 if ok1 else e2,
               "rel_err_text": e1,
               "rel_err_exec": e2,
               "used_code": bool(code)}
        rows.append(row)
        print(f"  -> {'OK ' if ok else 'X  '} {row['reason']}")

    graded = [r for r in rows if r.get("correct") is not None]
    c = sum(1 for r in graded if r["correct"])
    summary = {"method": method, "think_mode": THINK_MODE, "n": len(graded),
               "correct": c, "acc": round(c / len(graded), 4) if graded else 0,
               "elapsed_s": round(time.time() - t0, 1),
               "used_code": sum(1 for r in graded if r.get("used_code")),
               "tol": TOL["main"]}
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "rows": rows}, f, ensure_ascii=False, indent=1)
    print(f"=== {method}: {c}/{len(graded)} = {summary['acc']*100:.1f}% "
          f"({summary['elapsed_s']}s)")


# ---------------------------------------------------------------- 报告
def _effective_err(row):
    """这条样本「最接近真值」的相对误差：正文和代码输出各算一次，取更接近的那个。

    纯文本方法只有正文；代码方法可能正文里写的是错的、代码输出是对的，
    所以只看正文的误差会把代码方法冤枉成「全错」。
    """
    es = [e for e in (row.get("rel_err_text"), row.get("rel_err_exec")) if e is not None]
    return min(es) if es else None


def report():
    def load(m):
        p = os.path.join(OUT_ROOT, f"{m}_{THINK_MODE}", "summary.json")
        if not os.path.exists(p):
            return None
        return json.load(open(p, encoding="utf-8"))

    print("\n" + "=" * 78)
    print(f"浮点超越函数计算（THINK_MODE={THINK_MODE}；相对误差 ≤ {TOL['main']:g} 算对）")
    print("=" * 78)
    print(f"  {'方法':24s} {'总体':>8s} {'L1单函数':>10s} {'L2组合':>9s} "
          f"{'L3嵌套':>9s} {'写代码':>8s}")
    for m in METHODS:
        j = load(m)
        if not j:
            continue
        rows = [r for r in j["rows"] if r.get("correct") is not None]
        def acc(sel):
            s = [r for r in rows if sel(r)]
            return (sum(1 for r in s if r["correct"]) / len(s) * 100) if s else float("nan")
        print(f"  {m:24s} {j['summary']['acc']*100:7.1f}% {acc(lambda r: r['level']=='L1'):9.1f}% "
              f"{acc(lambda r: r['level']=='L2'):8.1f}% {acc(lambda r: r['level']=='L3'):8.1f}% "
              f"{j['summary']['used_code']:5d}/{j['summary']['n']}")

    # 容差敏感性 + 误差量级（用「最接近真值」的误差）
    print("\n  容差敏感性（同一批回答，只改「多接近才算对」）：")
    print(f"  {'方法':24s} {'1e-3':>7s} {'1e-6':>7s} {'1e-9':>7s} {'中位相对误差':>12s}")
    for m in METHODS:
        j = load(m)
        if not j:
            continue
        rows = [r for r in j["rows"] if r.get("correct") is not None]
        errs = [(r, _effective_err(r)) for r in rows]
        def rate(tol):
            ok = sum(1 for r, e in errs if (e is not None and e <= tol))
            return ok / len(rows) * 100 if rows else float("nan")
        vals = sorted(e for _, e in errs if e is not None)
        med = vals[len(vals) // 2] if vals else float("nan")
        print(f"  {m:24s} {rate(TOL['loose']):6.1f}% {rate(TOL['main']):6.1f}% "
              f"{rate(TOL['strict']):6.1f}% {med:12.2e}")

    # 典型失败样例
    print("\n  典型失败（纯文本方法里差得最远的 5 个）：")
    for m in ("1_only_ques", "All_text"):
        j = load(m)
        if not j:
            continue
        bad = [r for r in j["rows"]
               if r.get("correct") is False and r.get("rel_err_text") is not None]
        bad.sort(key=lambda r: -r["rel_err_text"])
        for r in bad[:5]:
            print(f"    {m:14s} {r['expr'][:40]:40s} rel={r['rel_err_text']:.1e}")


def rejudge(items):
    """离线重判：只读已存的 conversation_data.json，不调 API。"""
    for method in METHODS:
        out_dir = os.path.join(OUT_ROOT, f"{method}_{THINK_MODE}")
        if not os.path.isdir(out_dir):
            continue
        rows = []
        for it in items:
            p = os.path.join(out_dir, f"sample_{it['id']}", "conversation_data.json")
            if not os.path.exists(p):
                rows.append({"id": it["id"], "level": it["level"], "correct": None,
                             "reason": "missing"})
                continue
            conv = json.load(open(p, encoding="utf-8"))
            resp, exec_out = conv.get("response") or "", conv.get("exec_out") or ""
            ok1, why1, e1, _ = judge(resp, it)
            ok2, why2, e2, _ = judge(exec_out, it) if exec_out else (False, "no_exec", None, "")
            ok = ok1 or ok2
            rows.append({"id": it["id"], "level": it["level"], "expr": it["expr"],
                         "target": it["target"], "correct": ok,
                         "reason": why1 if ok1 else (why2 if ok2 else why1),
                         "rel_err": e1 if ok1 else e2,
                         "rel_err_text": e1, "rel_err_exec": e2,
                         "used_code": bool(conv.get("code"))})
        graded = [r for r in rows if r.get("correct") is not None]
        c = sum(1 for r in graded if r["correct"])
        summary = {"method": method, "think_mode": THINK_MODE, "n": len(graded),
                   "correct": c, "acc": round(c / len(graded), 4) if graded else 0,
                   "used_code": sum(1 for r in graded if r.get("used_code")),
                   "tol": TOL["main"]}
        with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "rows": rows}, f, ensure_ascii=False, indent=1)
        print(f"[rejudge] {method}: {c}/{len(graded)} = {summary['acc']*100:.1f}%")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", default="all")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--rejudge", action="store_true")
    a = ap.parse_args()

    items = build_tasks(force=a.rebuild)

    if a.rejudge:
        rejudge(items)
        report()
        sys.exit(0)

    if a.report:
        report()
        sys.exit(0)
    order = METHODS if a.method == "all" else [m.strip() for m in a.method.split(",") if m.strip()]
    for m in order:
        if m not in METHODS:
            print(f"未知方法 {m}，可选 {METHODS}")
            sys.exit(2)
    for m in order:
        run_one(m, items)
    report()
