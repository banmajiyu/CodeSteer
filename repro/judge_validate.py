"""用数据集里的标准答案，本地复核 LLM 裁判的判定（零成本，不发 API）。

原理：MATH 的 runner 用 `Sample_{i}` 命名样本目录，i 就是数据文件名 `i.json` 的编号，
所以可以精确还原每道题的标准答案（`solution` 里的 `\\boxed{...}`）。
然后把「裁判判对/判错」与「本地精确比较」交叉核对，得到裁判的准确率。

用法：python -X utf8 judge_validate.py
"""
import json
import os
import re
import glob
from collections import defaultdict

from sympy import simplify, sympify, nan, pi, sqrt, E
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                        implicit_multiplication_application)

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
REPO = os.path.join(os.path.dirname(BASE), "CodeSteer-v1.0")

DATASETS = {
    "MATH_geometry": os.path.join(REPO, "dataset_gather", "MATH", "train", "geometry"),
    "MATH_c_p": os.path.join(REPO, "dataset_gather", "MATH", "train", "counting_and_probability"),
}


def last_boxed_only_string(string):
    idx = string.rfind("\\boxed")
    if idx < 0:
        idx = string.rfind("\\fbox")
    if idx < 0:
        return None
    i = idx
    right_brace_idx = None
    num_left_braces_open = 0
    while i < len(string):
        if string[i] == "{":
            num_left_braces_open += 1
        if string[i] == "}":
            num_left_braces_open -= 1
            if num_left_braces_open == 0:
                right_brace_idx = i
                break
        i += 1
    if right_brace_idx is None:
        return None
    return string[idx:right_brace_idx + 1]


def remove_boxed(s):
    if s is None:
        return None
    if "\\boxed " in s:
        left = "\\boxed "
        return s[len(left):]
    left = "\\boxed{"
    if s.startswith(left) and s.endswith("}"):
        return s[len(left):-1]
    return s


def to_val(x):
    """把 LaTeX / 普通文本答案规范成 sympy 表达式，失败返回 None。"""
    if x is None:
        return None
    s = str(x).strip()
    if s in ("", "None", "No answer found", "<<<No answer found>>>"):
        return None
    # 单位与修饰
    s = s.replace("\\$", "").replace("$", "")
    s = s.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    s = s.replace("^\\circ", "").replace("\\circ", "").replace("°", "")
    s = s.replace("\\left", "").replace("\\right", "")
    s = s.replace("\\text{", "{").replace("\\mathrm{", "{")
    s = s.replace("\\pi", "pi").replace("π", "pi")
    s = s.replace("\\cdot", "*").replace("\\times", "*")
    s = s.replace("\\!", "").replace("\\;", "").replace("\\,", "")
    s = s.replace("√", "sqrt")
    s = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", s)      # 1,000,000 -> 1000000
    s = re.sub(r"sqrt(\d+)", r"sqrt(\1)", s)
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r"sqrt(\1)", s)
    s = re.sub(r"\\frac\{?(-?\w+?)\}?\{([^{}]*)\}", r"((\1)/(\2))", s)   # 兼容 \frac1{216}、\frac12
    for _ in range(5):                      # 逐层展开 \frac{a}{b}
        s2 = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"((\1)/(\2))", s)
        if s2 == s:
            break
        s = s2
    s = s.replace("{", "(").replace("}", ")")
    s = re.sub(r"\\[a-zA-Z]+", "", s)       # 残留的 latex 命令
    s = re.sub(r"\s+", "", s)
    if s.startswith("."):
        s = "0" + s
    elif s.startswith("-."):
        s = "-0" + s[2:]
    s = s.rstrip(".").rstrip(",")
    if not s:
        return None
    try:
        v = parse_expr(s, local_dict={"pi": pi, "sqrt": sqrt, "e": E},
                       transformations=standard_transformations + (implicit_multiplication_application,),
                       evaluate=True)
        if v is nan:
            return None
        return v
    except Exception:
        try:
            return sympify(float(s))
        except Exception:
            return None


def same(a, b):
    va, vb = to_val(a), to_val(b)
    if va is None or vb is None:
        # 退化为字符串比较（去掉空白和大小写）
        na = re.sub(r"\s+", "", str(a or "")).lower()
        nb = re.sub(r"\s+", "", str(b or "")).lower()
        return bool(na) and na == nb
    try:
        if va == vb:
            return True
        d = simplify(va - vb)
        if d == 0:
            return True
    except Exception:
        pass
    try:
        fa, fb = float(va), float(vb)
        if fb == 0:
            return abs(fa) < 1e-9
        return abs(fa - fb) / abs(fb) < 1e-3
    except Exception:
        return False


def read(p):
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception:
        return None


def main():
    totals = defaultdict(lambda: [0, 0, 0, 0])  # mode -> [TP, FP, FN, TN]
    for taskname, ddir in DATASETS.items():
        targets = {}
        for fn in os.listdir(ddir):
            if not fn.endswith(".json"):
                continue
            sid = fn[:-5]
            try:
                d = json.load(open(os.path.join(ddir, fn), encoding="utf-8"))
            except Exception:
                continue
            t = remove_boxed(last_boxed_only_string(d.get("solution", "")))
            if t:
                targets[sid] = t

        for mode in ["off", "strip", "on"]:
            root = os.path.join("results", f"main_{mode}", "save_input")
            if not os.path.isdir(root):
                continue
            for sf in glob.glob(os.path.join(root, f"result_{taskname}_*", "**", "success_failure.txt"),
                                recursive=True):
                d = os.path.dirname(sf)
                sid = os.path.basename(d).replace("Sample_", "")
                if sid not in targets:
                    continue
                judged = read(sf) == "True"
                a1 = read(os.path.join(d, "extracted_answer_1.txt"))
                a2 = read(os.path.join(d, "extracted_answer_2.txt"))
                ok_local = same(a1, targets[sid]) or same(a2, targets[sid])
                t = totals[mode]
                if judged and ok_local:
                    t[0] += 1
                elif judged and not ok_local:
                    t[1] += 1
                elif not judged and ok_local:
                    t[2] += 1
                else:
                    t[3] += 1

    print("=" * 74)
    print("MATH-Geometry / MATH-C&P：LLM 裁判 vs 本地精确比较（sympy + 1e-3 相对误差）")
    print("=" * 74)
    print("  TP = 裁判判对且本地也对   FP = 裁判判对但本地算错（误判为对）")
    print("  FN = 裁判判错但本地算对（误判为错）  TN = 都判错")
    for mode in ["off", "strip", "on"]:
        tp, fp, fn, tn = totals[mode]
        n = tp + fp + fn + tn
        if not n:
            continue
        agree = (tp + tn) / n * 100
        print(f"\n[{mode}] 共 {n} 个样本，裁判与本地一致率 {agree:.1f}%")
        print(f"  TP {tp:>4}   FP {fp:>4}   FN {fn:>4}   TN {tn:>4}")
        print(f"  裁判判对 {tp+fp} 个里，本地确认对 {tp} 个 → 精确率 {tp/max(tp+fp,1)*100:.1f}%")
        print(f"  本地算对 {tp+fn} 个里，裁判也判对 {tp} 个 → 召回率 {tp/max(tp+fn,1)*100:.1f}%")


if __name__ == "__main__":
    main()
