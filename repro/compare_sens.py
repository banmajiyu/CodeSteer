"""预算敏感性对照：同一批任务，B/C 组在 2500 与 8000 输出预算下的准确率。

背景：THINK_MODE=strip 时模型可能把整个输出预算花在 reasoning 上，正文被截成空串
（completion_tokens 恰好等于预算）。path_plan / BoxNet1 在 B 组因此判 0%。
这里把这两个任务在 8000 预算下重跑一遍，看 0% 有多少是"预算不够"造成的假象。

用法: python -X utf8 compare_sens.py
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE
sys.path.insert(0, HERE)
os.chdir(HERE)

import summarize as S  # noqa: E402

METHODS = S.METHODS
CAP = 25
PAIRS = [("strip", "results/main_strip", "results/sens_strip_b8k"),
         ("on", "results/main_on", "results/sens_on_b8k")]


def collect(root):
    out = {}
    d0 = os.path.join(BASE, root, "save_input")
    if not os.path.isdir(d0):
        return out
    for dirname in sorted(os.listdir(d0)):
        if not dirname.startswith("result_"):
            continue
        taskkey, method = S._split_name(dirname)
        if taskkey is None:
            continue
        taskkey = S.TASK_ALIAS.get(taskkey, S.TASK_ALIAS.get(taskkey.lower(), taskkey))
        c, t = S._count([os.path.join(d0, dirname)], CAP)
        if t:
            out[(taskkey, method)] = (c, t)
    return out


print("| 组 | 任务 | 方法 | 预算2500 | n | 预算8000 | n |")
print("|---|---|---|---|---|---|---|")
for label, r25, r80 in PAIRS:
    a, b = collect(r25), collect(r80)
    for task in ("path_plan", "BoxNet1"):
        for m in METHODS:
            k = (task, m)
            x, y = a.get(k), b.get(k)
            if not x and not y:
                continue
            f = lambda v: "  -  " if not v else f"{100.0*v[0]/v[1]:5.1f}"
            print(f"| {label} | {S.TASK_LABEL.get(task, task) if hasattr(S,'TASK_LABEL') else task} "
                  f"| {S.METHOD_SHORT[m]} | {f(x)} | {x[1] if x else 0} | {f(y)} | {y[1] if y else 0} |")
