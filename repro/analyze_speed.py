"""分析 llm_calls_*.jsonl：延迟分布、token、每组耗时构成。"""
import collections
import json
import statistics
import sys

for m in sys.argv[1:] or ["off", "strip", "on"]:
    p = f"logs/llm_calls_{m}.jsonl"
    try:
        rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    except FileNotFoundError:
        print(f"== {m}: 无日志")
        continue
    if not rows:
        print(f"== {m}: 空")
        continue
    lat = [r["latency_s"] for r in rows]
    bytag = collections.defaultdict(list)
    for r in rows:
        bytag[r["tag"]].append(r["latency_s"])
    pt = sum((r["usage"] or {}).get("prompt_tokens", 0) for r in rows)
    ct = sum((r["usage"] or {}).get("completion_tokens", 0) for r in rows)
    rt = 0
    for r in rows:
        d = (r["usage"] or {}).get("completion_tokens_details") or {}
        rt += d.get("reasoning_tokens") or 0
    print(f"== {m}: n={len(rows)} sum_lat={sum(lat):.0f}s "
          f"mean={statistics.mean(lat):.2f}s p50={statistics.median(lat):.2f}s max={max(lat):.1f}s")
    for t, v in sorted(bytag.items()):
        print(f"   {t:8s} n={len(v):4d} mean={statistics.mean(v):5.2f}s "
              f"p50={statistics.median(v):5.2f}s max={max(v):6.1f}s sum={sum(v):6.0f}s")
    print(f"   prompt_tok={pt} completion_tok={ct} reasoning_tok={rt} "
          f"in_chars={sum(r['in_chars'] for r in rows)}")
