"""看护脚本：一眼看清 9 个 worker 是否还活着、有没有报错、跑完多少。

用法：
    python watch.py            # 人类可读报告
    python watch.py --json     # 机器可读

判定"卡死"：该分片的 llm_calls 日志超过 STALL_MIN 分钟没更新，且 state 里还有没跑完的任务。
"""
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "logs")

# 各分片负责的任务（与 launch 时 --tasks 一致）
SHARDS = {
    "s1": ["game24", "number_multiply", "letters", "gsm"],
    "s2": ["MATH_geometry", "MATH_cp", "BoxNet1", "blocksworld", "BoxLift"],
    "s3": ["big_bench_hard", "path_plan", "letters_sentence"],
}
MODES = ["off", "strip", "on"]
METHODS = 5
STALL_MIN = 12


def load_state(mode, tag):
    path = os.path.join(LOGS, f"main_run_{mode}_{tag}.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def count_lines(path):
    n = 0
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.strip():
                    n += 1
    except Exception:
        pass
    return n


def tail_errors(mode, tag, n=2):
    """分片 stderr 里的最后几条（过滤掉无害的提示）。"""
    path = os.path.join(LOGS, f"run_{mode}_{tag}.err.log")
    if not os.path.exists(path):
        path = os.path.join(LOGS, f"shard_{mode}_{tag}.err.log")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = [l.rstrip() for l in f if l.strip()]
    except Exception:
        return []
    bad = [l for l in lines if "Traceback" in l or "Error" in l or "错误" in l]
    return bad[-n:]


def main():
    as_json = "--json" in sys.argv
    now = time.time()
    rows = []
    problems = []
    for mode in MODES:
        for tag in ("s1", "s2", "s3"):
            st = load_state(mode, tag)
            ok = [k for k, v in st.items() if v.get("ok")]
            calls = sum(v.get("calls") or 0 for v in st.values())
            expect = len(SHARDS[tag]) * METHODS
            jf = os.path.join(LOGS, f"llm_calls_{mode}_{tag}.jsonl")
            age_min = (now - os.path.getmtime(jf)) / 60 if os.path.exists(jf) else 999
            lines = count_lines(jf) if os.path.exists(jf) else 0
            errs = tail_errors(mode, tag)
            done = len(ok) >= expect
            stalled = (not done) and age_min > STALL_MIN
            row = {
                "mode": mode, "shard": tag,
                "done": len(ok), "expect": expect,
                "calls": calls, "log_lines": lines,
                "idle_min": round(age_min, 1),
                "state": "done" if done else ("STALLED" if stalled else "running"),
                "errors": errs,
            }
            rows.append(row)
            if stalled:
                problems.append(f"{mode}/{tag} 卡了 {age_min:.0f} 分钟（{len(ok)}/{expect} 完成）")
            if errs:
                problems.append(f"{mode}/{tag} stderr: {errs[-1][:160]}")

    if as_json:
        print(json.dumps({"rows": rows, "problems": problems}, ensure_ascii=False, indent=1))
        return 0 if not problems else 1

    print(f"时间 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'组':6s} {'分片':4s} {'完成':>8s} {'调用':>6s} {'空闲min':>8s} 状态")
    print("-" * 56)
    for r in rows:
        print(f"{r['mode']:6s} {r['shard']:4s} {str(r['done'])+'/'+str(r['expect']):>8s} "
              f"{r['calls']:6d} {r['idle_min']:8.1f} {r['state']}")
    print("-" * 56)
    total_done = sum(r["done"] for r in rows)
    total_expect = sum(r["expect"] for r in rows)
    print(f"总进度 {total_done}/{total_expect} 个(任务,方法)")
    if problems:
        print("\n⚠️ 需要处理：")
        for p in problems:
            print("  - " + p)
    else:
        print("✅ 全部正常推进中")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
