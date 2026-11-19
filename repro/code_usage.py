"""统计每个 (任务, 方法) 的代码使用率（论文 Table 3 口径的近似）。

论文 Table 3 说：模型有时会无视"请写代码"的指令，改用自然语言推理。
这里直接从落盘的 conversation_data.json 里数：
  - 样本是否有可执行代码（字段 code 非空 / 或者 response 里有 ```python 块）
  - 代码是否真的被执行成功（exec_out 非空或 success_failure 里判对）

用法：
  python -X utf8 code_usage.py                 # 默认 A 组 main_off
  python -X utf8 code_usage.py main_on
"""
import glob
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

METHODS = ["1_only_ques", "All_text", "All_code_CoT", "AutoGen", "Text_code_summarizer"]
CODE_BLOCK = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)


def _has_code(sample_dir, j=None):
    """样本目录里出现了非空 code_*.py 就算"写了可执行代码"。

    runner 把从回复里抠出来的代码写到 code_<turn>_<idx>.py；没写代码的样本
    要么没有这些文件，要么只有很小的占位。
    """
    codes = [p for p in glob.glob(os.path.join(sample_dir, "code_*.py"))
             if os.path.getsize(p) > 40]
    if codes:
        return True
    if j is None:
        return False
    for r in (j.get("response_list") or []):
        if isinstance(r, str) and CODE_BLOCK.search(r):
            return True
    return False


def main(run="main_off"):
    root = os.path.join(BASE, "results", run, "save_input")
    dirs = sorted(glob.glob(os.path.join(root, "result_*")))
    table = {}
    for d in dirs:
        name = os.path.basename(d)
        m = None
        for cand in METHODS:
            if "_" + cand + "_" in name:
                m = cand
                break
        if m is None:
            continue
        samples = glob.glob(os.path.join(d, "**", "conversation_data.json"), recursive=True)
        if not samples:
            continue
        # 任务名：去掉 result_ 前缀与 _<method>_<model> 后缀
        task = name[len("result_"):].split("_" + m + "_")[0]
        n_ok = n_sf = n_code = 0
        for p in samples:
            try:
                j = json.load(open(p, encoding="utf-8"))
            except Exception:
                continue
            sf = os.path.join(os.path.dirname(p), "success_failure.txt")
            if os.path.exists(sf):
                n_sf += 1
                if open(sf, encoding="utf-8", errors="ignore").read().strip() == "True":
                    n_ok += 1
            if _has_code(os.path.dirname(p), j):
                n_code += 1
        key = (task.lower(), m)
        prev = table.get(key)
        if prev:
            n_ok += prev[0]
            n_sf += prev[1]
            n_code += prev[2]
        table[key] = (n_ok, n_sf, n_code)

    tasks = sorted({k[0] for k in table})
    print(f"## 代码使用率（{run}）\n")
    print("| 任务 | " + " | ".join(METHODS) + " |")
    print("|---" * (len(METHODS) + 1) + "|")
    for t in tasks:
        cells = []
        for m in METHODS:
            r = table.get((t, m))
            if not r:
                cells.append("-")
                continue
            ok, tot, code = r
            acc = 100.0 * ok / tot if tot else 0.0
            cr = 100.0 * code / tot if tot else 0.0
            cells.append(f"{acc:.0f}%（码{cr:.0f}%）")
        print(f"| {t} | " + " | ".join(cells) + " |")

    print("\n> 括号里「码 X%」= 该 (任务,方法) 的样本中真正写出了可执行代码的比例。")
    print("> OnlyQ 本来就不要求写代码，它的代码率反映模型自发使用代码的倾向。")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main_off")
