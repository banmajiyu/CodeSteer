"""判分可信度审计（零成本，只读已落盘结果，不发 API 请求）。

背景：原仓库多数 runner 的判定是
    if True_false_result_1 == 'False' and True_false_result_2 == 'False': 记为错
    else: 记为对
两个 True_false_result 来自裁判模型回复里最后一个 `<<<...>>>`；如果裁判这次回复
没有 `<<<>>>`（被截断、跑偏、回空），取到的是空字符串，既不是 'True' 也不是
'False'，于是**静默算作答对**。本脚本把这个口径数出来。

只统计写这两个文件的 runner：gsm / MATH_geometry / MATH_cp / number_multiply /
big_bench_hard / blocksworld / path_plan。
（BoxNet1、BoxLift 走状态模拟判分，game24、letters 走本地精确比较，没有这些文件。）

用法：python -X utf8 score_audit.py
"""
import glob
import os
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

VALS = {"True", "False"}
METHODS = ["1_only_ques", "All_text", "All_code_CoT", "AutoGen", "Text_code_summarizer"]


def read(p):
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception:
        return None


def task_of(dirname):
    marker = dirname.find("_deepseek-flash")
    head = dirname[:marker] if marker > 0 else dirname
    for m in METHODS:
        if f"_{m}" in head:
            return head[:head.index(f"_{m}")], m
    return head, "?"


def main():
    print("=" * 80)
    print("判分可信度审计：有多少样本是「裁判回复解析不出来 → 被静默算对」")
    print("=" * 80)

    for mode in ["off", "strip", "on"]:
        root = os.path.join("results", f"main_{mode}", "save_input")
        if not os.path.isdir(root):
            continue
        judged = 0          # 有 True_false_result 文件的样本（走 LLM 裁判的）
        unparsed_ok = 0     # 裁判解析不出、却记成 True
        unparsed_all = 0    # 裁判解析不出（不论记成什么）
        by_task = defaultdict(lambda: [0, 0, 0])  # task -> [judged, unparsed_ok, unparsed_all]
        for f1 in glob.glob(os.path.join(root, "**", "True_false_result_1.txt"), recursive=True):
            d = os.path.dirname(f1)
            judged += 1
            r1 = read(f1)
            r2 = read(os.path.join(d, "True_false_result_2.txt"))
            ok = read(os.path.join(d, "success_failure.txt"))
            unparsed = (r1 not in VALS) and (r2 not in VALS)
            t, _ = task_of(os.path.basename(d))
            by_task[t][0] += 1
            if unparsed:
                unparsed_all += 1
                by_task[t][2] += 1
                if ok == "True":
                    unparsed_ok += 1
                    by_task[t][1] += 1
        if not judged:
            continue
        print(f"\n【{mode}】走 LLM 裁判的样本 {judged} 个")
        print(f"  裁判两个候选都解析不出：{unparsed_all} ({unparsed_all/judged*100:.1f}%)，"
              f"其中被记成答对 {unparsed_ok} ({unparsed_ok/judged*100:.1f}%)")
        for t in sorted(by_task):
            j, uo, ua = by_task[t]
            if ua:
                print(f"    {t:<30} {uo:>3}/{j:<4} 记对  (解析不出共 {ua})")
        if unparsed_ok:
            print(f"  → 这些样本把准确率至少抬高约 {unparsed_ok/judged*100:.1f} 个百分点（若全部改判为错）")

    # 交叉验证：按任务重算（含 MATH_c_p 别名）
    print("\n" + "=" * 80)
    print("按任务重算正确率（与 summarize.py 交叉验证）")
    print("=" * 80)
    for mode in ["off", "strip", "on"]:
        root = os.path.join("results", f"main_{mode}", "save_input")
        if not os.path.isdir(root):
            continue
        agg = defaultdict(lambda: [0, 0])
        for sf in glob.glob(os.path.join(root, "**", "success_failure.txt"), recursive=True):
            top = os.path.relpath(sf, root).split(os.sep)[0]   # result_<task>_<method>_<model>
            t, _ = task_of(top)
            t = t.replace("result_", "", 1)
            agg[t][1] += 1
            if read(sf) == "True":
                agg[t][0] += 1
        print(f"\n[{mode}]")
        for t in sorted(agg):
            c, n = agg[t]
            print(f"  {t:<32} {c:>4}/{n:<4} = {c/n*100:5.1f}%")


if __name__ == "__main__":
    main()
