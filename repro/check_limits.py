import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import smoke_limits as SL  # noqa: E402

CASES = [
    ("MATH_geometry", "run_math_geometry_baseline_methods.py"),
    ("MATH_cp", "run_math_counting_and_probability_baseline_methods.py"),
    ("letters", "run_letters_baseline_methods.py"),
    ("game24", "run_game24_baseline_methods.py"),
    ("gsm", "run_gsm_baseline_methods.py"),
    ("number_multiply", "run_number_multiply_baseline_methods.py"),
    ("big_bench_hard", "run_big_bench_hard_baseline_methods.py"),
    ("BoxNet1", "run_BoxNet1_baseline_methods.py"),
    ("blocksworld", "run_Blocksworld_baseline_methods.py"),
    ("BoxLift", "run_BoxLift_baseline_methods.py"),
    ("path_plan", "run_path_plan_continuous_baseline_methods.py"),
]

BENCH = os.path.join(HERE, "..", "CodeSteer-v1.0", "benchmark")
MARK = "__import__('smoke_limits').first"

bad = 0
for task, fname in CASES:
    with open(os.path.join(BENCH, fname), encoding="utf-8") as fh:
        src = fh.read()
    out = SL.limit(src, task, verbose=False)
    n = out.count(MARK)
    try:
        compile(out, fname, "exec")
        status = "OK"
    except SyntaxError as e:
        status = f"SYNTAX line {e.lineno}: {e.msg}"
        bad += 1
    print(f"{task:16s} guards={n}  {status}")

print("bad:", bad)
