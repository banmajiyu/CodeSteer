"""检查 run_all.py 的样本上限注入：bbh 是否按子任务分别计数。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
import run_all  # noqa: E402

src_path = os.path.join(HERE, "..", "CodeSteer-v1.0", "benchmark",
                        "run_big_bench_hard_baseline_methods.py")
src = open(os.path.abspath(src_path), encoding="utf-8").read()
expr = "'big_bench_hard#All_text' + '/' + str(env_name)"
out = run_all._inject_cap(src, "big_bench_hard#All_text", key_expr=expr, guard_mode="break")
i = out.find("tick(")
print(out[i - 260:i + 200])
print("守卫数:", out.count("tick("))

# 普通任务对照
src2 = open(os.path.abspath(os.path.join(HERE, "..", "CodeSteer-v1.0", "benchmark",
                                        "run_game24_baseline_methods.py")), encoding="utf-8").read()
out2 = run_all._inject_cap(src2, "game24#All_text")
j = out2.find("tick(")
print("game24:", out2[j - 40:j + 90].replace("\n", " | "))
