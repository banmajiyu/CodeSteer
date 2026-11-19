"""summarize.py —— 把 results/main_{mode}/save_input 下的逐样本判定汇总成对比表。

为什么不用 gather 里的 acc_result_log：那个文件只在 runner 跑完整个任务时追加一行，
而 sample_cap 是靠抛 _ReproStop 提前截断的，异常会跳过尾部写盘 —— 所以除了少数
天然样本数就 <= cap 的任务，gather 日志是缺的（这是记账问题，不影响判分本身）。
真正完整的是逐样本目录里的 success_failure.txt。

判定口径：
  * 每个 (任务, 方法) 的样本数 = 该目录下 success_failure.txt 的个数
  * 正确数 = 内容为 True 的个数
  * big_bench_hard 的四个子任务（date_understanding / web_of_lies /
    logical_deduction_seven_objects / navigate）按论文拆成 4 个任务
  * 字母句任务（letters_sentence）读它自己的 summary.json

AveNorm_j = (1/N) * sum_i ( s_ij / max_k s_ik )   —— 论文 Table 2 的归一化口径

用法：
    python -X utf8 summarize.py            # 打印表格
    python -X utf8 summarize.py --md out.md
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

MODES = [("off", "A 关思考"), ("strip", "B 丢思考"), ("on", "C 留思考")]
METHODS = ["1_only_ques", "All_text", "All_code_CoT", "AutoGen", "Text_code_summarizer"]
METHOD_SHORT = {
    "1_only_ques": "OnlyQ",
    "All_text": "AllText",
    "All_code_CoT": "AllCode+CoT",
    "AutoGen": "AutoGen",
    "Text_code_summarizer": "Code+Text+Sum",
}

# 展示名（顺序 = 论文 14 任务的顺序，最后加字母句）
TASKS = [
    ("number_multiply", "Number Multiplying"),
    ("game24", "Game 24"),
    ("gsm", "GSM-Hard"),
    ("MATH_geometry", "MATH-Geometry"),
    ("MATH_cp", "MATH-Count&Prob"),
    ("bbh:date_understanding", "Date Understanding"),
    ("bbh:web_of_lies", "Web of Lies"),
    ("bbh:logical_deduction_seven_objects", "Logical Deduction"),
    ("bbh:navigate", "Navigate"),
    ("BoxNet1", "BoxNet"),
    ("path_plan", "Path Plan"),
    ("letters", "Letters"),
    ("BoxLift", "BoxLift"),
    ("blocksworld", "Blocksworld"),
    ("letters_sentence", "Letters(sentence)"),
]

BBH = "big_bench_hard"
BBH_SUBS = ["date_understanding", "web_of_lies", "logical_deduction_seven_objects", "navigate"]

# 目录名里的任务键 → TASKS 里的标准键（runner 落盘用的小写/别名）
TASK_ALIAS = {
    "math_c_p": "MATH_cp",
    "math_cp": "MATH_cp",
    "boxnet1": "BoxNet1",
    "boxlift": "BoxLift",
    "box_net1": "BoxNet1",
    "box_lift": "BoxLift",
}


def _split_name(dirname):
    """result_<taskkey>_<method>_<model>  ->  (taskkey, method)"""
    base = dirname[len("result_"):]
    for m in METHODS:
        tag = "_" + m + "_"
        if tag in base:
            return base.split(tag)[0], m
    return None, None


PER_TASK_CAP = 0   # >0 时每个任务只取前 N 个样本（三组对齐用）
# 个别任务样本天然不足，A 组（cap=200 全局）只跑到 11 个 navigate；
# 三组统一按这 11 个样本比较，避免"样本集不同"带来的偏差。
TASK_CAP_OVERRIDE = {"bbh:navigate": 11}


def _sample_files(d, cap=None):
    """该任务目录下所有 success_failure.txt，按样本号（路径里的数字）排序。"""
    out = []
    for f in glob.glob(os.path.join(d, "**", "success_failure.txt"), recursive=True):
        rel = os.path.relpath(os.path.dirname(f), d)
        key = tuple(int(x) for x in re.findall(r"\d+", rel)) or (0,)
        out.append((key, f))
    out.sort()
    files = [f for _, f in out]
    cap = cap if cap is not None else PER_TASK_CAP
    if cap:
        files = files[:cap]
    return files


def _count(dirs, cap=None):
    total = correct = skipped = 0
    for d in dirs:
        for f in _sample_files(d, cap):
            try:
                v = open(f, encoding="utf-8", errors="replace").read().strip()
            except OSError:
                continue
            total += 1
            if v == "True":
                correct += 1
    return correct, total


def collect(mode):
    """返回 {(task_label, method): (correct, total)}"""
    out = {}
    root = os.path.join(HERE, "results", f"main_{mode}", "save_input")
    if not os.path.isdir(root):
        return out
    for dirname in os.listdir(root):
        if not dirname.startswith("result_"):
            continue
        taskkey, method = _split_name(dirname)
        if taskkey is None:
            continue
        taskkey = TASK_ALIAS.get(taskkey, TASK_ALIAS.get(taskkey.lower(), taskkey))
        full = os.path.join(root, dirname)
        if taskkey == BBH:
            for sub in BBH_SUBS:
                d = os.path.join(full, sub)
                if os.path.isdir(d):
                    c, t = _count([d], TASK_CAP_OVERRIDE.get(f"bbh:{sub}", PER_TASK_CAP))
                    if t:
                        out[(f"bbh:{sub}", method)] = (c, t)
        else:
            c, t = _count([full])
            if t:
                out[(taskkey, method)] = (c, t)

    # 字母句任务：自己的 summary.json
    for method in METHODS:
        p = os.path.join(HERE, "results", "letters_sentence", f"{method}_{mode}", "summary.json")
        if not os.path.exists(p):
            continue
        try:
            j = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        # run_letters_sentence 落盘结构 {"summary": {...}, "rows": [...]}
        rows = j.get("rows") if isinstance(j.get("rows"), list) else None
        if isinstance(j.get("summary"), dict):
            j = j["summary"]
        if rows and PER_TASK_CAP:
            rows = sorted(rows, key=lambda r: r.get("id", 0))[:PER_TASK_CAP]
            tot = len(rows)
            ok = sum(1 for r in rows if r.get("correct"))
        else:
            tot = j.get("n", j.get("total"))
            ok = j.get("correct", 0)
        if tot:
            out[("letters_sentence", method)] = (ok, tot)
    return out


def acc_table(data):
    """{(task,method):(c,t)} -> {task: {method: acc or None}}"""
    tab = {}
    for (task, method), (c, t) in data.items():
        tab.setdefault(task, {})[method] = (c / t) if t else None
    return tab


def avenorm(tab):
    """AveNorm per method over tasks where max>0"""
    res = {}
    for m in METHODS:
        vals = []
        for task, row in tab.items():
            best = max([v for v in row.values() if v is not None], default=None)
            v = row.get(m)
            if best and v is not None:
                vals.append(v / best)
        res[m] = (sum(vals) / len(vals)) if vals else None
    return res


def fmt(v):
    return "  -  " if v is None else f"{v * 100:5.1f}"


def render(mode_data):
    lines = []
    for mode, label in MODES:
        tab = acc_table(mode_data.get(mode, {}))
        if not tab:
            lines.append(f"\n## {label}（THINK_MODE={mode}）：还没有数据\n")
            continue
        lines.append(f"\n## {label}（THINK_MODE={mode}）\n")
        head = "| 任务 | " + " | ".join(METHOD_SHORT[m] for m in METHODS) + " | n |"
        sep = "|" + "---|" * (len(METHODS) + 2)
        lines.append(head)
        lines.append(sep)
        for key, disp in TASKS:
            if key not in tab:
                continue
            row = tab[key]
            ns = [t for (task, m), (c, t) in mode_data[mode].items() if task == key]
            n = max(ns) if ns else 0
            lines.append(f"| {disp} | " + " | ".join(fmt(row.get(m)) for m in METHODS) + f" | {n} |")
        av = avenorm(tab)
        lines.append("| **AveNorm** | " + " | ".join(
            ("  -  " if av[m] is None else f"**{av[m] * 100:.1f}**") for m in METHODS) + " | |")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--per-task-cap", type=int, default=0,
                    help="每个任务只统计前 N 个样本（三组样本数不一致时对齐用）")
    args = ap.parse_args()

    global PER_TASK_CAP
    PER_TASK_CAP = args.per_task_cap

    mode_data = {m: collect(m) for m, _ in MODES}
    lines = ["# 复现结果：15 任务 × 5 方法 × 3 种思考模式", ""]
    lines.append("数字为准确率(%)；n = 该任务样本数；AveNorm = 论文 Table 2 的归一化均值。")
    lines.extend(render(mode_data))

    # 三组合并透视：每任务每方法一行三列
    lines.append("\n## 三种思考模式的横向对比（AveNorm %）\n")
    lines.append("| 方法 | A 关思考 | B 丢思考 | C 留思考 |")
    lines.append("|---|---|---|---|")
    avs = {m: avenorm(acc_table(mode_data[m])) for m, _ in MODES}
    for m in METHODS:
        cells = []
        for mode, _ in MODES:
            v = avs[mode].get(m)
            cells.append("  -  " if v is None else f"{v * 100:.1f}")
        lines.append(f"| {METHOD_SHORT[m]} | " + " | ".join(cells) + " |")

    text = "\n".join(lines) + "\n"
    print(text)
    if args.md:
        open(args.md, "w", encoding="utf-8").write(text)
        print(f"已写 {args.md}", file=sys.stderr)
    if args.json:
        json.dump({m: {f"{k[0]}|{k[1]}": v for k, v in d.items()} for m, d in mode_data.items()},
                  open(args.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
