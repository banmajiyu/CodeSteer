"""按阶段 / 按思考模式统计 API 用量与费用，输出可直接贴进报告的 Markdown。

价格（DeepSeek 官方价目表，deepseek-flash，2026-11）：
  输入 缓存命中  空闲 0.02 元/百万   高峰 0.04
  输入 缓存未命中 空闲 1    元/百万   高峰 2
  输出            空闲 4    元/百万   高峰 8
高峰时段：北京时间周一至周五 9:00-12:00、14:00-18:00（法定节假日除外）。

用法：python -X utf8 cost_report.py
"""
import glob
import json
import os
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

# 每百万 token 的价格区间（空闲→高峰，缓存未命中口径；缓存命中的输入价另算）
P_IN = (1.0, 2.0)
P_IN_HIT = (0.02, 0.04)
P_OUT = (4.0, 8.0)


def stage_of(path):
    p = path.replace("\\", "/")
    name = os.path.basename(p)
    if "archive_broken_path" in p:
        return "废跑（-c 路径 bug 未修时）"
    if name.startswith("archive_b8192_"):
        return "废跑（思考预算 8000 未调时）"
    if "archive_llm_calls_smoke" in name:
        return "冒烟测试"
    if "sens" in name:
        return "敏感性补跑"
    if "probe" in name or "debug" in name:
        return "调试探测"
    if "_off" in name or name == "llm_calls_off.jsonl":
        return "A 组 off"
    if "_strip" in name:
        return "B 组 strip"
    if "_on" in name:
        return "C 组 on"
    return "其它"


def main():
    agg = defaultdict(lambda: {"n": 0, "in": 0, "out": 0})
    for f in glob.glob("logs/**/*.jsonl", recursive=True):
        st = stage_of(f)
        for line in open(f, encoding="utf-8", errors="ignore"):
            try:
                d = json.loads(line)
            except Exception:
                continue
            u = d.get("usage") or {}
            a = agg[st]
            a["n"] += 1
            a["in"] += u.get("prompt_tokens", 0)
            a["out"] += u.get("completion_tokens", 0)

    order = ["A 组 off", "B 组 strip", "C 组 on", "敏感性补跑", "冒烟测试", "调试探测",
             "废跑（-c 路径 bug 未修时）", "废跑（思考预算 8000 未调时）", "其它"]
    keys = [k for k in order if k in agg] + [k for k in agg if k not in order]

    print("| 阶段 | 调用次数 | 输入 tokens | 输出 tokens | 费用（元） |")
    print("|---|---|---|---|---|")
    tot = {"n": 0, "in": 0, "out": 0}
    lo_sum = hi_sum = 0.0
    for k in keys:
        a = agg[k]
        lo = a["in"] / 1e6 * P_IN[0] + a["out"] / 1e6 * P_OUT[0]
        hi = a["in"] / 1e6 * P_IN[1] + a["out"] / 1e6 * P_OUT[1]
        lo_sum += lo
        hi_sum += hi
        for kk in tot:
            tot[kk] += a[kk]
        print(f"| {k} | {a['n']:,} | {a['in']/1e6:.2f}M | {a['out']/1e6:.2f}M | {lo:.1f} ~ {hi:.1f} |")
    print(f"| **合计** | **{tot['n']:,}** | **{tot['in']/1e6:.2f}M** | **{tot['out']/1e6:.2f}M** | **{lo_sum:.1f} ~ {hi_sum:.1f}** |")

    print()
    print(f"若输入全部命中缓存（0.02~0.04 元/百万），输入侧费用降至 "
          f"{tot['in']/1e6*P_IN_HIT[0]:.2f} ~ {tot['in']/1e6*P_IN_HIT[1]:.2f} 元，"
          f"总费用约 {tot['in']/1e6*P_IN_HIT[0] + tot['out']/1e6*P_OUT[0]:.1f} ~ "
          f"{tot['in']/1e6*P_IN_HIT[1] + tot['out']/1e6*P_OUT[1]:.1f} 元。")


if __name__ == "__main__":
    main()
