"""
run_letters_sentence.py —— 第 15 个任务：句子级字母统计

设计目标：用**程序算真值**，完全不依赖 LLM 当裁判，所以结果 100% 可验证。
语料：抓下来存在 repro/data/raw_corpus.txt（不联网也能跑）。

支持方法：1_only_ques / All_text / All_code_CoT / AutoGen / Text_code_summarizer
执行顺序约束：Text_code_summarizer 必须在 All_text 和 All_code_CoT 跑完之后。

用法：
    python run_letters_sentence.py --method All_text
    python run_letters_sentence.py --method all        # 按正确顺序全跑
"""
import os
import re
import sys
import json
import time
import subprocess
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(os.path.dirname(HERE), "CodeSteer-v1.0")

from env_win import ds_chat, THINK_MODE, DS_MODEL      # noqa: E402
from prompt import (text_output_prompt, with_COT_code_output_prompt,   # noqa: E402
                    AutoGen_prompt, combined_agent_prompt)

DATA = os.path.join(HERE, "data")
CORPUS = os.path.join(DATA, "raw_corpus.txt")
TASKS = os.path.join(DATA, "letters_sentence_tasks.json")
OUT_ROOT = os.path.join(HERE, "results", "letters_sentence")

LETTERS = ["r", "e", "s", "t", "a", "z", "q", "x"]
N_PER_LETTER = 8
MIN_WORDS, MAX_WORDS = 8, 25


# ------------------------------------------------------------------ 语料
def build_tasks(force=False):
    """按固定规则从语料里切句子并出题。生成后写 json，之后一律读 json。"""
    if os.path.exists(TASKS) and not force:
        with open(TASKS, encoding="utf-8") as f:
            return json.load(f)

    if not os.path.exists(CORPUS):
        sys.exit(f"找不到语料 {CORPUS}，先运行 fetch_corpus.py")

    raw = open(CORPUS, encoding="utf-8", errors="replace").read()
    # 切句：按 . ! ? 切，滤掉太短太长的、含非 ASCII 的
    sents = re.split(r"(?<=[.!?])\s+", raw)
    clean = []
    seen = set()
    for s in sents:
        s = " ".join(s.split())
        if not (MIN_WORDS <= len(s.split()) <= MAX_WORDS):
            continue
        if any(ord(c) > 127 for c in s):
            continue
        if not re.fullmatch(r"[A-Za-z0-9 ,.'\"\-;:!?()]+", s):
            continue
        if s.lower() in seen:
            continue
        seen.add(s.lower())
        clean.append(s)

    print(f"[letters_sentence] 可用句子 {len(clean)} 条")

    tasks = []
    tid = 0
    for letter in LETTERS:
        # 固定规则选句：优先挑该字母出现次数多样的句子，保证区分度
        scored = sorted(clean, key=lambda s: -s.lower().count(letter))
        if letter in "zesqax":          # 低频字母：取出现次数最多的
            picked = scored[:N_PER_LETTER]
        else:                            # 高频字母：在 1~6 次之间均匀取
            buckets = {}
            for s in clean:
                c = s.lower().count(letter)
                buckets.setdefault(c, []).append(s)
            picked = []
            for c in [1, 2, 3, 4, 5, 6]:
                picked.extend(buckets.get(c, [])[:2])
            picked = picked[:N_PER_LETTER]

        for s in picked:
            pos = [i + 1 for i, ch in enumerate(s.replace(" ", "").lower()) if ch == letter]
            tasks.append({
                "id": tid,
                "letter": letter,
                "sentence": s,
                "count": len(pos),
                "positions": pos,
                "num_words": len(s.split()),
                "num_chars": len(s),
            })
            tid += 1

    os.makedirs(DATA, exist_ok=True)
    with open(TASKS, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=1)
    print(f"[letters_sentence] 生成 {len(tasks)} 道题 -> {TASKS}")
    return tasks


def make_question(t):
    q = (f"How many times does the letter '{t['letter']}' appear in the following sentence, "
         f"and at what positions?\n")
    q += ("Counting rule: delete ONLY the space characters, then number the remaining "
          "characters from 1. Punctuation marks (, . ' \" - ; : ! ? ( )) are characters too "
          "and DO take a position.\n")
    q += ("Worked example: sentence \"Hi, ok.\" -> after deleting spaces: Hi,ok. -> "
          "positions: 1=H, 2=i, 3=,, 4=o, 5=k, 6=. . "
          "So the letter 'o' appears at position 4.\n")
    q += f"Sentence: \"{t['sentence']}\"\n"
    q += ("Surround the answer with <<<content>>>. "
          "Please respond in the format: <<<Count: X, Positions: [Y, Z, ...]>>>, "
          "such as <<<Count: 2, Positions: [1, 3]>>>.\nYour answer:\n")
    return q


# ------------------------------------------------------------------ 判分
def parse_answer(text):
    """从模型输出里抽 Count / Positions。纯正则，不调 LLM。

    取**最后一个** <<<...>>> 块：开思考（THINK_MODE=on）时正文前面会掺进
    推理内容，里面常有中间猜测（"maybe <<<Count: 3, Positions: [1,2,3]>>>"），
    真正的最终答案在最后。早期版本用 re.search 取第一个，导致 on 组
    letters_sentence 被判成 12%（实际末尾答案是对的）。
    """
    if not text:
        return None, None
    body = None
    for m in re.finditer(r"<<<(.*?)>>>", text, re.S):
        if re.search(r"Count:", m.group(1), re.I):
            body = m.group(1)
    if body is None:
        body = text
    mc = re.search(r"Count:\s*(\d+)", body, re.I)
    if not mc:
        return None, None
    count = int(mc.group(1))
    mp = re.search(r"Positions:\s*\[([^\]]*)\]", body, re.I)
    if mp:
        pos = [int(x) for x in re.findall(r"\d+", mp.group(1))]
    else:
        pos = []
    return count, pos


def judge(text, t):
    count, pos = parse_answer(text)
    if count is None:
        return False, "no_match"
    if count != t["count"]:
        return False, "wrong_count"
    if sorted(pos) != sorted(t["positions"]):
        return False, "wrong_positions"
    return True, "correct"


# ------------------------------------------------------------------ 执行代码
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


def extract_code(text):
    if not text:
        return None
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
    return m.group(1).strip() if m else None


# ------------------------------------------------------------------ 主流程
def run_one_method(method, tasks, model=DS_MODEL):
    out_dir = os.path.join(OUT_ROOT, f"{method}_{THINK_MODE}")
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    t0 = time.time()

    for k, t in enumerate(tasks):
        sdir = os.path.join(out_dir, f"sample_{t['id']}")
        os.makedirs(sdir, exist_ok=True)
        question = make_question(t)

        if method == "1_only_ques":
            prompt = question
        elif method == "All_text":
            prompt = text_output_prompt + question
        elif method == "All_code_CoT":
            prompt = with_COT_code_output_prompt + question
        elif method == "AutoGen":
            prompt = AutoGen_prompt + question
        elif method == "Text_code_summarizer":
            p_text = os.path.join(OUT_ROOT, f"All_text_{THINK_MODE}", f"sample_{t['id']}",
                                  "conversation_data.json")
            p_code = os.path.join(OUT_ROOT, f"All_code_CoT_{THINK_MODE}", f"sample_{t['id']}",
                                  "conversation_data.json")
            if not (os.path.exists(p_text) and os.path.exists(p_code)):
                rows.append({"id": t["id"], "correct": None, "reason": "skipped_no_deps"})
                continue
            r_text = json.load(open(p_text, encoding="utf-8"))["response"]
            r_code = json.load(open(p_code, encoding="utf-8"))["response"]
            prompt = combined_agent_prompt + "###The input question is: \n" + question + "\n\n"
            prompt += f"\nThe response from Agent_1 is: {r_text}"
            prompt += f"\n\nThe response from Agent_2 is: {r_code}"
            prompt += ("\n\nNow you need to analyze the problem based on their answers and "
                       "output final answer with the required format in the original question. "
                       "Your analysis and answer:\n")
        else:
            raise SystemExit(f"未知方法 {method}")

        print(f"[{method}][{THINK_MODE}] {k+1}/{len(tasks)} id={t['id']} "
              f"letter={t['letter']} count={t['count']}")
        try:
            resp = ds_chat([{"role": "user", "content": prompt}], model=model,
                           temperature=0.0, max_tokens=2000, tag=f"ls_{method}")
        except Exception as e:
            print(f"  !! 调用失败 {e}")
            rows.append({"id": t["id"], "correct": False, "reason": f"api_error:{e}"})
            continue

        code = extract_code(resp)
        exec_out = run_code(code, sdir) if code else ""

        ok1, why1 = judge(resp, t)
        ok2, why2 = judge(exec_out, t) if exec_out else (False, "no_exec")
        ok = ok1 or ok2

        with open(os.path.join(sdir, "conversation_data.json"), "w", encoding="utf-8") as f:
            json.dump({"question": question, "prompt": prompt, "response": resp,
                       "code": code, "exec_out": exec_out}, f, ensure_ascii=False, indent=1)

        rows.append({"id": t["id"], "letter": t["letter"], "count": t["count"],
                     "num_words": t["num_words"],
                     "correct": ok, "reason": why1 if ok1 else why2,
                     "used_code": bool(code)})
        print(f"  -> {'OK ' if ok else 'X  '} ({why1 if ok1 else why2})")

    # 汇总
    graded = [r for r in rows if r.get("correct") is not None]
    acc = sum(r["correct"] for r in graded) / len(graded) if graded else 0
    summary = {
        "method": method, "think_mode": THINK_MODE, "model": model,
        "n": len(graded), "correct": sum(r["correct"] for r in graded),
        "acc": round(acc, 4), "elapsed_s": round(time.time() - t0, 1),
        "by_letter": {}, "by_length": {}, "by_count": {},
    }
    for field, key in (("letter", "by_letter"), ("count", "by_count")):
        for r in graded:
            kk = str(r.get(field))
            d = summary[key].setdefault(kk, {"n": 0, "c": 0})
            d["n"] += 1
            d["c"] += int(r["correct"])
    for r in graded:
        nw = r.get("num_words") or 0
        bucket = "8-12" if nw <= 12 else ("13-18" if nw <= 18 else "19-25")
        d = summary["by_length"].setdefault(bucket, {"n": 0, "c": 0})
        d["n"] += 1
        d["c"] += int(r["correct"])

    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "rows": rows}, f, ensure_ascii=False, indent=1)

    print(f"\n=== {method} / {THINK_MODE} : {summary['correct']}/{summary['n']} "
          f"= {acc:.1%}  ({summary['elapsed_s']}s)")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", default="1_only_ques")
    ap.add_argument("--rebuild", action="store_true", help="重新从语料切句出题")
    args = ap.parse_args()

    tasks = build_tasks(force=args.rebuild)
    order = (["1_only_ques", "All_text", "All_code_CoT", "AutoGen", "Text_code_summarizer"]
             if args.method == "all" else [args.method])
    for m in order:
        run_one_method(m, tasks)
