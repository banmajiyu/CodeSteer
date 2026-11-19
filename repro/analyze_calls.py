"""统计 llm_calls_*.jsonl 的调用量/token/延迟，并给出剩余工作量与预计完成时间。

用法：
    python analyze_calls.py            # 汇总所有分片
    python analyze_calls.py --watch    # 每 60s 刷新一次
"""
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "logs")

# 每个任务真实样本数（与 run_all.NATURAL 一致；bbh 是 4 子任务 × 50）
SAMPLES = {
    "game24": 46, "number_multiply": 60, "letters": 75, "gsm": 53,
    "MATH_geometry": 50, "MATH_cp": 50, "big_bench_hard": 200,
    "BoxNet1": 30, "blocksworld": 48, "BoxLift": 20,
    "path_plan": 50, "letters_sentence": 50,
}
TOTAL_SAMPLES = sum(SAMPLES.values())


def scan():
    per_mode = {}
    for path in sorted(glob.glob(os.path.join(LOGS, "llm_calls_*_s*.jsonl"))):
        base = os.path.basename(path)
        parts = base[len("llm_calls_"):-len(".jsonl")].split("_")
        modes = parts[0]
        d = per_mode.setdefault(modes, {"calls": 0, "p": 0, "c": 0, "lat": 0.0,
                                        "main": 0, "judge": 0, "r": 0, "files": 0, "mtime": 0})
        d["files"] += 1
        d["mtime"] = max(d["mtime"], os.path.getmtime(path))
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                u = rec.get("usage") or {}
                d["calls"] += 1
                d["p"] += u.get("prompt_tokens") or 0
                d["c"] += u.get("completion_tokens") or 0
                d["lat"] += rec.get("latency_s") or 0
                d["r"] += rec.get("reasoning_chars") or 0
                if str(rec.get("tag", "")).startswith("judge"):
                    d["judge"] += 1
                else:
                    d["main"] += 1
    return per_mode


def report(prev=None):
    per_mode = scan()
    now = time.time()
    print(f"任务样本合计 {TOTAL_SAMPLES}/组，方法样本 {TOTAL_SAMPLES*5}/组")
    print(f"{'组':8s} {'调用':>7s} {'其中judge':>9s} {'prompt_tok':>10s} {'compl_tok':>10s} "
          f"{'均延迟':>7s} {'调用/分钟':>9s} {'预计总量':>8s} {'ETA':>7s}")
    print("-" * 88)
    total_calls = total_p = total_c = 0
    rate_info = {}
    for mode, d in sorted(per_mode.items()):
        rate = ""
        eta = ""
        if prev and mode in prev:
            dt = now - prev["ts"]
            dn = d["calls"] - prev[mode]["calls"]
            if dt > 5:
                rpm = dn / dt * 60
                rate = f"{rpm:9.1f}"
                rate_info[mode] = rpm
                est_total = 3660 * 1.5  # 方法样本 × 保守 1.5 次调用/样本
                left = est_total - d["calls"]
                if rpm > 0.5 and left > 0:
                    eta = f"{left/rpm/60:6.1f}h"
                elif left <= 0:
                    eta = "  完成"
        avg = d["lat"] / d["calls"] if d["calls"] else 0
        print(f"{mode:8s} {d['calls']:7d} {d['judge']:9d} {d['p']:10d} {d['c']:10d} "
              f"{avg:6.2f}s {rate} {int(3660*1.5):8d} {eta}")
        total_calls += d["calls"]
        total_p += d["p"]
        total_c += d["c"]
    print("-" * 88)
    print(f"总计 {total_calls} 次调用, prompt {total_p} tok, completion {total_c} tok")
    print(f"最后写入：{time.strftime('%H:%M:%S')}（本次 {time.strftime('%H:%M:%S', time.localtime(now))}）")
    return {m: d for m, d in per_mode.items()}


def main():
    watch = "--watch" in sys.argv
    prev = None
    if not watch:
        report()
        return
    while True:
        now = time.time()
        if prev:
            dt = now - prev["ts"]
            print(f"\n=== {time.strftime('%H:%M:%S')} (间隔 {dt:.0f}s) ===")
        report(prev)
        cur = scan()
        prev = {"ts": now}
        for m, d in cur.items():
            prev[m] = d
        time.sleep(60)


if __name__ == "__main__":
    main()
