"""深一步：被判「对」的样本，裁判到底依据了什么？
- 判对的样本里，r1/r2 是否真的出现了 'True'（而不是靠 else 分支白捡的）
- 判对的样本里，抽取到的答案是不是空的 / 'No answer found'（说明裁判凭空判对）
"""
import glob
import os
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)


def read(p):
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception:
        return None


for mode in ["off", "strip", "on"]:
    root = os.path.join("results", f"main_{mode}", "save_input")
    if not os.path.isdir(root):
        continue
    pairs = Counter()
    empty_true = []
    total_true = 0
    for sf in glob.glob(os.path.join(root, "**", "success_failure.txt"), recursive=True):
        if read(sf) != "True":
            continue
        d = os.path.dirname(sf)
        f1 = os.path.join(d, "True_false_result_1.txt")
        if not os.path.exists(f1):
            continue          # 非 LLM 裁判的任务
        total_true += 1
        r1, r2 = read(f1), read(os.path.join(d, "True_false_result_2.txt"))
        pairs[(r1, r2)] += 1
        a1, a2 = read(os.path.join(d, "extracted_answer_1.txt")), read(os.path.join(d, "extracted_answer_2.txt"))
        bad = {"", "No answer found", "<<<No answer found>>>", None}
        if a1 in bad and a2 in bad:
            empty_true.append((d, a1, a2))

    print(f"\n===== [{mode}] 判对且走 LLM 裁判的样本 {total_true} 个 =====")
    for (r1, r2), c in pairs.most_common(6):
        print(f"  (r1={r1!r}, r2={r2!r}) : {c}  占 {c/total_true*100:.1f}%")
    print(f"  两个抽取答案都为空/No answer found 却判对：{len(empty_true)} 个 "
          f"({len(empty_true)/max(total_true,1)*100:.1f}%)")
    for d, a1, a2 in empty_true[:5]:
        print(f"    例：{d}  a1={a1!r} a2={a2!r}")
