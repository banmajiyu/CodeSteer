"""平均准确率 vs AveNorm：看归一化这把尺子把分数抬高了多少。
也输出"任务饱和"清单：某任务上 5 个方法都 >= 95% 的，就算饱和。
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

import summarize as S  # noqa: E402


def main():
    S.PER_TASK_CAP = 25
    for mode in ["off", "strip", "on"]:
        data = S.collect(mode)
        tab = S.acc_table(data)
        methods = [m for m in S.METHODS]
        tasks = sorted(tab)
        print(f"\n===== [{mode}] 任务 {len(tasks)} =====")
        print(f"  {'方法':24s} {'平均准确率':>10s} {'AveNorm':>9s} {'抬高':>7s}")
        an = S.avenorm(tab)
        for m in methods:
            vals = [tab[t][m] for t in tasks if tab[t].get(m) is not None]
            if not vals:
                continue
            mean = sum(vals) / len(vals) * 100
            a = an.get(m)
            print(f"  {m:24s} {mean:10.1f} {a:9.1f} {a-mean:+7.1f}")

        sat, hard = [], []
        for t in tasks:
            vals = [tab[t][m] for m in methods if tab[t].get(m) is not None]
            if len(vals) < 3:
                continue
            lo = min(vals) * 100
            (sat if lo >= 95 else hard).append((t, lo, sum(vals) / len(vals) * 100))
        print(f"  饱和任务（5 方法最低分都 >= 95%）：{len(sat)}/{len(sat)+len(hard)}")
        for t, lo, avg in sat:
            print(f"      {t:38s} 最低 {lo:5.1f}  平均 {avg:5.1f}")
        print(f"  仍有区分度的任务：{len(hard)}")
        for t, lo, avg in sorted(hard, key=lambda x: x[2]):
            print(f"      {t:38s} 最低 {lo:5.1f}  平均 {avg:5.1f}")


if __name__ == "__main__":
    main()
