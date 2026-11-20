"""两个"口径敏感性"重算，全部离线、零 API 成本。

1) 松口径 vs 严口径
   原仓库判定：r1=='False' and r2=='False' 才判错（只要一个对就算对 = 论文口径）。
   严口径：要求 r1=='True' and r2=='True'（两个抽取答案都判对）。
   —— 量化高分的多少来自这条宽松规则。

2) 前 25 个样本 vs 后 25 个样本（off 组有 50 个）
   —— 检验"取前 N 个是否偏容易"。

用法：python -X utf8 strict_recount.py
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

import summarize as S  # noqa: E402  复用已验证的目录解析与口径

METHODS = S.METHODS
CAP = 25


def read(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except OSError:
        return None


def samples(d, strict):
    """[(ok, ok_strict), ...]，只取前 CAP 个（按样本号排序）"""
    out = []
    for f in S._sample_files(d, CAP):
        sf = read(f)
        sd = os.path.dirname(f)
        r1 = read(os.path.join(sd, "True_false_result_1.txt"))
        r2 = read(os.path.join(sd, "True_false_result_2.txt"))
        ok = (sf == "True")
        if r1 is not None and r2 is not None:
            ok_s = (r1 == "True" and r2 == "True")
        else:                      # 非 LLM 裁判任务，两个口径同值
            ok_s = ok
        out.append((ok, ok_s))
    return out


def collect_all(mode, strict=False):
    """{(task_label, method): [ (ok, ok_strict), ... ]}"""
    out = {}
    root = os.path.join(BASE, "results", f"main_{mode}", "save_input")
    if os.path.isdir(root):
        for dirname in os.listdir(root):
            if not dirname.startswith("result_"):
                continue
            taskkey, method = S._split_name(dirname)
            if taskkey is None:
                continue
            taskkey = S.TASK_ALIAS.get(taskkey, S.TASK_ALIAS.get(taskkey.lower(), taskkey))
            full = os.path.join(root, dirname)
            if taskkey == S.BBH:
                for sub in S.BBH_SUBS:
                    d = os.path.join(full, sub)
                    if os.path.isdir(d):
                        v = samples(d, strict)
                        if v:
                            out[(f"bbh:{sub}", method)] = v
            else:
                v = samples(full, strict)
                if v:
                    out[(taskkey, method)] = v

    # 字母句：读 summary.json 的 rows，用同一套 CAP
    for method in METHODS:
        p = os.path.join(BASE, "results", "letters_sentence", f"{method}_{mode}", "summary.json")
        if not os.path.exists(p):
            continue
        try:
            j = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        rows = j.get("rows") if isinstance(j.get("rows"), list) else []
        rows = sorted(rows, key=lambda r: r.get("id", 0))[:CAP]
        if rows:
            out[("letters_sentence", method)] = [(bool(r.get("correct")), bool(r.get("correct")))
                                                 for r in rows]
    return out


def table(data, strict):
    """-> {(task, method): (ok, n)}"""
    return {k: (sum(1 for ok, oks in v if (oks if strict else ok)), len(v))
            for k, v in data.items()}


def avenorm(tb):
    tasks = sorted({t for (t, m) in tb})
    tot = {m: 0.0 for m in METHODS}
    n = 0
    for t in tasks:
        vals = {m: tb[(t, m)][0] / tb[(t, m)][1] for m in METHODS
                if (t, m) in tb and tb[(t, m)][1]}
        if len(vals) < 2:
            continue
        mx = max(vals.values())
        if mx <= 0:
            continue
        for m, v in vals.items():
            tot[m] += v / mx
        n += 1
    return {m: (tot[m] / n * 100 if n else None) for m in METHODS}, n


def main():
    global CAP
    res = {}
    print("=" * 74)
    print(f"1) 松口径（论文：一个对就算对） vs 严口径（两个都对）  每任务前 {CAP} 个样本")
    print("=" * 74)
    for mode in ["off", "strip", "on"]:
        data = collect_all(mode)
        lax, n1 = avenorm(table(data, False))
        strict, n2 = avenorm(table(data, True))
        print(f"\n[{mode}]  任务数 {n1}")
        print(f"    {'方法':24s} {'松口径':>8s} {'严口径':>8s} {'差':>7s}")
        for m in METHODS:
            if lax[m] is None:
                continue
            print(f"    {m:24s} {lax[m]:8.1f} {strict[m]:8.1f} {lax[m]-strict[m]:7.1f}")
        res[mode] = {"lax": lax, "strict": strict, "n_tasks": n1}

    print("\n" + "=" * 74)
    print("2) 样本切片：off 组，前 25 / 后 25 / 全 50（松口径）")
    print("=" * 74)
    root_off = os.path.join(BASE, "results", "main_off", "save_input")
    for label, cap, sl in [("前25", 25, slice(0, 25)), ("后25", 50, slice(25, 50)),
                           ("全50", 50, slice(0, 50))]:
        CAP = cap
        data = collect_all("off")
        data = {k: v[sl] for k, v in data.items() if len(v[sl]) >= 5}
        an, n = avenorm(table(data, False))
        line = "  ".join(f"{m[:14]}={an[m]:.1f}" for m in METHODS if an[m] is not None)
        print(f"  {label}（任务 {n}）: {line}")
    CAP = 25

    out = os.path.join(BASE, "results", "strict_recount.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f"\n写完 {out}")


if __name__ == "__main__":
    main()
