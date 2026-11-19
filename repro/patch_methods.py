"""
patch_methods.py —— 给 11 个 runner 补上缺失的 4 个方法分支

原仓库只有 run_Logic_Game_baseline_methods.py 实现了 6 个方法；另外 11 个
runner 只有 '1_only_ques'，传别的名字会 UnboundLocalError。

做法：源码级注入。每个 runner 都有这几行锚点
    if baseline_method_name == '1_only_ques':
        user_prompt_list = [question]
锚点之后插入通用 `elif` 链 + 汇总逻辑。**所有 44 个分支用同一个模板**，
保证 5 个方法的语义在每个任务上完全一致（这是跨任务比较的前提）。

为了不改原文件，注入后的源码用 exec 编译成新函数，覆盖模块里的同名函数。
"""
import os
import re
import sys
import json
import traceback

# --------------------------------------------------------------- 通用注入块
# DIR 变量名：每个 runner 用不同的目录名，注入时替换
INJECT_TEMPLATE = '''
                elif baseline_method_name == 'AutoGen':
                    user_prompt_list = [AutoGen_prompt + question]
                elif baseline_method_name == 'All_code_CoT':
                    user_prompt_list = [with_COT_code_output_prompt + question]
                elif baseline_method_name == 'All_text':
                    user_prompt_list = [text_output_prompt + question]
                elif baseline_method_name == 'Text_code_summarizer':
                    _code_dir = {CODE_DIR}
                    _sum_prompt = repro_collect_two_agents(_code_dir, save_code_dir)
                    if _sum_prompt is None:
                        # 前置产物缺失：这个样本记为失败，不调用 LLM
                        _repro_write_result(save_code_dir, gather_save_input_dir, model_name,
                                            f"CodeSteer, {{_task_label}}, Text_code_summarizer(SKIPPED_NO_DEPS), {{model_name}}",
                                            total_sample_num, total_correct_num)
                        continue
                    user_prompt_list = [_sum_prompt]
'''

# 每个 runner 的目录名模板（与原 runner 的 base_save_code_dir 一致）
CODE_DIR_MAP = {
    "game24":            ("save_input_dir + f'/result_game24_{m}_{model_name}/sample_{{i}}'", "Game24"),
    "number_multiply":   ("save_input_dir + f'/result_number_multiply_{m}_{model_name}_CodeSteer/' + dir_digit_name + f'/sample_{{i}}'", "Number Multiply"),
    "letters":           ("save_input_dir + f'/result_letters_{m}_{model_name}/min_length_{{min_length}}_max_length_{{max_length}}/{{letter}}_{{letter_freq}}_{{index}}'", "Letters"),
    "gsm":               ("save_input_dir + f'/result_gsm_{m}_{model_name}/Sample_{{i}}'", "GSM"),
    "MATH_geometry":     ("save_input_dir + f'/result_MATH_geometry_{m}_{model_name}/Sample_{{i}}'", "MATH-Geometry"),
    "MATH_cp":           ("save_input_dir + f'/result_MATH_c_p_{m}_{model_name}/Sample_{{i}}'", "MATH-Count&Probability"),
    "big_bench_hard":    ("save_input_dir + f'/result_big_bench_hard_{m}_{model_name}/{{env_name}}/sample_{{i}}'", "BBH"),
    "BoxNet1":           ("save_input_dir + f'/result_boxnet1_{m}_{model_name}' + f'/{{pg_row_num}}_{{pg_column_num}}_{{iteration_num}}'", "BoxNet1"),
    "blocksworld":       ("save_input_dir + f'/result_blocksworld_{m}_{model_name}' + f'/{{num_blocks}}_{{initial_stacks}}_{{goal_stacks}}_{{index}}'", "Blocksworld"),
    "BoxLift":           ("save_input_dir + f'/result_boxlift_{m}_{model_name}' + f'/{{num_boxes}}_{{num_lifters}}_{{iteration_num}}'", "BoxLift"),
    "path_plan":         ("save_input_dir + f'/result_path_plan_{m}_{model_name}/sample_{{env_index}}_{{index}}'", "Path Plan"),
}

# 各 runner 汇总函数的名字
RUNNER_FUNC = {
    "game24": "run_game24_baselines",
    "number_multiply": "run_number_multiply_baselines",
    "letters": "run_letters_baselines",
    "gsm": "run_gsm_baselines",
    "MATH_geometry": "run_MATH_geometry_baselines",
    "MATH_cp": "run_MATH_counting_and_probability_baselines",
    "big_bench_hard": "run_big_bench_hard_baselines",
    "BoxNet1": "run_boxnet1_baselines",
    "blocksworld": "run_blocksworld_baselines",
    "BoxLift": "run_boxlift_baselines",
    "path_plan": "run_path_plan_baselines",
}

RUNNER_MODULE = {
    "game24": "run_game24_baseline_methods",
    "number_multiply": "run_number_multiply_baseline_methods",
    "letters": "run_letters_baseline_methods",
    "gsm": "run_gsm_baseline_methods",
    "MATH_geometry": "run_math_geometry_baseline_methods",
    "MATH_cp": "run_math_counting_and_probability_baseline_methods",
    "big_bench_hard": "run_big_bench_hard_baseline_methods",
    "BoxNet1": "run_BoxNet1_baseline_methods",
    "blocksworld": "run_Blocksworld_baseline_methods",
    "BoxLift": "run_BoxLift_baseline_methods",
    "path_plan": "run_path_plan_continuous_baseline_methods",
}

# 少数 runner 的输出目录名里**没有方法名**，5 个方法会写进同一棵树、
# 互相覆盖（number_multiply 就是这种），summarizer 也就找不到兄弟目录。
# 这里在内存里的源码上补上 {baseline_method_name}，磁盘文件不动。
SOURCE_FIXES = {
    "number_multiply": [
        ("f'/result_number_multiply_{model_name}_CodeSteer'",
         "f'/result_number_multiply_{baseline_method_name}_{model_name}_CodeSteer'"),
    ],
}


# --------------------------------------------------------------- 公共回调
def repro_collect_two_agents(base_dir, sample_dir=None):
    """复刻 run_Logic_Game_baseline_methods.py:497-541 的 summarizer 拼装逻辑。

    读 All_text 和 All_code_CoT 两个 run 在**同一个样本**上的产物，
    拼成论文附录 H 的 combined_agent_prompt 输入。
    缺任何一个 → 返回 None（调用方记 SKIPPED_NO_DEPS）。

    base_dir 是本方法自己的样本目录，形如
        .../result_gsm_Text_code_summarizer_deepseek-flash/Sample_1
    两个前置方法的目录是**兄弟目录**，只差方法名那一段：
        .../result_gsm_All_text_deepseek-flash/Sample_1
        .../result_gsm_All_code_CoT_deepseek-flash/Sample_1
    所以直接用字符串替换推出兄弟目录（原仓库也是这样拼的，
    见 run_Logic_Game_baseline_methods.py 里的 self_method_name 替换）。
    """
    if not base_dir:
        return None
    d_text = base_dir.replace("_Text_code_summarizer_", "_All_text_")
    d_code = base_dir.replace("_Text_code_summarizer_", "_All_code_CoT_")
    if d_text == base_dir or d_code == base_dir:
        print(f"[repro] 目录模板里没有方法名占位，无法定位前置产物: {base_dir}")
        return None

    def _load(d):
        p = os.path.join(d, "conversation_data.json")
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)["response_list"][-1]

    r_text, r_code = _load(d_text), _load(d_code)
    if r_text is None or r_code is None:
        print(f"[repro] 缺少前置产物，跳过: {d_text} / {d_code}")
        return None

    from prompt import combined_agent_prompt
    question = json.load(open(os.path.join(d_text, "conversation_data.json"),
                              encoding="utf-8"))["question"]

    p = combined_agent_prompt + "###The input question is: \n" + question + "\n\n"
    p += f"\nThe response from Agent_1 is: {r_text}"
    f1 = os.path.join(d_text, "extracted_answer_1.txt")
    if os.path.exists(f1):
        p += f"\nThe execution result from the Agent_1 code is: {open(f1, encoding='utf-8').read()}"
    p += f"\n\nThe response from Agent_2 is: {r_code}"
    f2 = os.path.join(d_code, "extracted_answer_1.txt")
    if os.path.exists(f2):
        p += f"\nThe execution result from the Agent_2 code is: {open(f2, encoding='utf-8').read()}"
    p += ("\n\nNow you need to analyze the problem based on their answers and output final "
          "answer with the required format in the original question. Your analysis and answer:\n")
    return p


def _repro_write_result(sample_dir, gather_dir, model_name, header, total, correct):
    print(f"[repro] {header} -> {correct}/{total}")
    p = os.path.join(gather_dir, f"acc_result_log_{model_name}.txt")
    os.makedirs(gather_dir, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"{header}\ncorrect/all:{correct}/{total}\n")


def _reindent_template(tpl, indent):
    """把模板的顶层语句统一到 indent，内部相对缩进保持不变。

    模板是按 16 空格顶层缩进写的（elif 与 elif 体相差 4 空格）。
    做法：先算出模板的最小缩进（顶层），全部左移到 0，再整体加 indent。
    """
    lines = tpl.split("\n")
    body = [ln for ln in lines if ln.strip()]
    if not body:
        return ""
    base = min(len(ln) - len(ln.lstrip(" ")) for ln in body)
    out = []
    for ln in lines:
        if not ln.strip():
            out.append("")
        else:
            out.append(indent + ln[base:])
    return "\n".join(out)


def _install_helpers(ns):
    ns["repro_collect_two_agents"] = repro_collect_two_agents
    ns["_repro_write_result"] = _repro_write_result
    # 判分器写死 model_name='gpt-4o'，换成 DeepSeek 裁判
    # 注意：不能无条件覆盖模块全局的 GPT_response —— 它同时是主模型的生成入口。
    # 原实现里判分函数调用时传 model_name='gpt-4o'，而 _patched_new_GPT_response
    # 本来就会把非 DS 模型名转去裁判，所以这里什么都不用做。
    pass


# --------------------------------------------------------------- 注入器
def patch_runner(task_key, module, save_input_dir, gather_save_input_dir, model_name,
                 baseline_method_name, args_path):
    """把 module 里的 run_xxx_baselines 换成"支持 5 方法"的版本并直接执行。

    返回函数返回值（通常是 None）。异常原样抛出，由调用方记录。
    """
    func_name = RUNNER_FUNC[task_key]
    src = open(module.__file__, "r", encoding="utf-8").read()
    # 注入白名单（模型名进 API 分支，否则会掉进本地 HF 权重分支）
    try:
        import env_win
        src = env_win._whitelist_inject_source(os.path.abspath(module.__file__), src)
    except Exception:
        pass

    # 0) 输出目录名的内存级修正（见 SOURCE_FIXES）
    for old, new in SOURCE_FIXES.get(task_key, ()):
        if old not in src:
            print(f"[repro] 警告：{task_key} 的目录修正没命中：{old}")
        src = src.replace(old, new)

    # 1) 定位目标函数的完整源码
    m = re.search(rf"^def {func_name}\(", src, re.M)
    if not m:
        raise RuntimeError(f"{module.__file__} 里找不到 {func_name}")
    start = m.start()
    end = len(src)
    m2 = re.search(r"^def ", src[m.end():], re.M)
    if m2:
        end = m.end() + m2.start()
    func_src = src[start:end]

    # 2) 插入 elif 链
    anchor = "    if baseline_method_name == '1_only_ques':\n        user_prompt_list = [question]\n"
    # 各 runner 缩进可能不同（有的在循环里，缩进 16 空格）
    am = re.search(r"([ \t]*)if baseline_method_name == '1_only_ques':\n[ \t]*user_prompt_list = \[question\]\n",
                   func_src)
    if not am:
        raise RuntimeError(f"{func_name}: 找不到 1_only_ques 锚点")
    indent = am.group(1)
    anchor = am.group(0)

    tpl = _reindent_template(INJECT_TEMPLATE, indent)

    dir_tpl, label = CODE_DIR_MAP[task_key]
    m_placeholder = "{m}"
    dir_code = dir_tpl.format(m=m_placeholder, model_name="{model_name}")
    # 用 .format 只替换 {CODE_DIR}，其余花括号留给运行时 f-string/format
    dir_code = dir_code.replace("{model_name}", "{model_name}")
    tpl = tpl.replace("{CODE_DIR}", dir_code)
    tpl = tpl.replace("{{_task_label}}", label)
    tpl = tpl.replace("{{model_name}}", "{model_name}")

    injected = func_src.replace(anchor, anchor + tpl, 1)

    # 3) 每个 runner 的局部目录变量名都不同，补上：
    #    CODE_DIR 里用到 _dir_digit_name / min_length / letter / env_name 等
    #    这些在各自循环里已存在，无需注入。
    #    但 {m} 要替换成 baseline_method_name：
    injected = injected.replace("{m}", "{baseline_method_name}")

    # 4) 编译并在"原模块的 global 环境"里执行，保证 import 全部可见
    code = compile(injected, module.__file__ + "<repro>", "exec")
    _install_helpers(module.__dict__)
    exec(code, module.__dict__)

    fn = module.__dict__[func_name]
    return fn(save_input_dir, gather_save_input_dir, model_name, baseline_method_name, args_path)


def supported_methods():
    return ["1_only_ques", "All_text", "All_code_CoT", "AutoGen", "Text_code_summarizer"]
