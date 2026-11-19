"""进度看板：把 9 个分片 worker 的 state 文件汇总成一张表。

用法：
    C:\\Users\\13988\\anaconda3\\envs\\CodeSteer\\python.exe -X utf8 progress.py
"""
import glob
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "logs")

MODES = {"off": "A 关思考", "strip": "B 弃思考", "on": "C 留思考"}


def load_state(mode, tag):
    path = os.path.join(LOGS, f"main_run_{mode}_{tag}.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main():
    total_calls = {m: 0 for m in MODES}
    total_ok = {m: 0 for m in MODES}
    total_sec = {m: 0.0 for m in MODES}
    rows = []
    for mode, label in MODES.items():
        for tag in ("s1", "s2", "s3"):
            st = load_state(mode, tag)
            ok = [k for k, v in st.items() if v.get("ok")]
            calls = sum(v.get("calls") or 0 for v in st.values())
            sec = sum(v.get("sec") or 0 for v in st.values())
            samples = sum(v.get("samples") or 0 for v in st.values())
            total_calls[mode] += calls
            total_ok[mode] += len(ok)
            total_sec[mode] += sec
            last = max((v.get("done_at") or "" for v in st.values()), default="")
            rows.append((label, tag, len(ok), len(st), samples, calls, sec / 60, last))
    print(f"{'组':10s} {'分片':4s} {'完成/记录':10s} {'样本':>6s} {'调用':>6s} {'耗时min':>8s}  最后完成")
    print("-" * 78)
    for r in rows:
        print(f"{r[0]:10s} {r[1]:4s} {str(r[2]) + '/' + str(r[3]):10s} {r[4]:6d} {r[5]:6d} {r[6]:8.1f}  {r[7]}")
    print("-" * 78)
    for mode, label in MODES.items():
        print(f"{label}: {total_ok[mode]} 个(任务,方法)完成, 调用 {total_calls[mode]}, 累计 {total_sec[mode]/60:.1f} min")
    # 最近 3 分钟的调用速率
    print()
    for jf in sorted(glob.glob(os.path.join(LOGS, "llm_calls_*_s*.jsonl"))):
        name = os.path.basename(jf)
        try:
            mtime = os.path.getmtime(jf)
            with open(jf, "r", encoding="utf-8", errors="replace") as f:
                n = sum(1 for _ in f)
        except Exception:
            continue
        age = time.time() - mtime
        print(f"{name:32s} 行数 {n:6d}  {'活跃' if age < 180 else '停 ' + str(int(age // 60)) + 'min'}  {time.strftime('%H:%M:%S', time.localtime(mtime))}")


if __name__ == "__main__":
    main()
