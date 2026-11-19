# 任务盘点：ICLR'25 论文 14 个任务 → 仓库里的实际家

本文件记录“论文 14 任务”在 `CodeSteer-v1.0` 仓库里的落地情况，以及无法原样复现的那些**具体缺口**。
一条铁律：**缺什么、补什么都要写在这里**，不能悄悄用无关数据顶替。

## 一、论文原文的任务清单（doc/steering_extracted.txt 已核对）

14 tasks / 4 大类：

| 大类 | 任务 | 论文引用的数据来源 |
|---|---|---|
| math | Number Multiplying, Game 24, GSM-Hard, MATH-Geometry, MATH-Count&Probability | Hendrycks 2021; Gao 2023; Yao 2024; Zhou 2023a |
| logical | Date Understanding, Web of Lies, Logical Deduction, Navigate | BIG-Bench-Hard (Suzgun 2022); Gao 2023 |
| robot planning | BoxNet, Path Plan | Scalable-Robots (Chen 2024c); AutoTAMP (Chen 2024a); Li 2023a |
| symbolic | Letters, BoxLift, Blocksworld | Scalable-Robots; PlanBench (Valmeekam 2024) |

## 二、仓库现状（12 个 runner → 论文 14 任务）

| # | 论文任务 | 仓库 runner | 家 / 状态 |
|---|---|---|---|
| 1 | Number Multiplying | `run_number_multiply_baseline_methods.py` | ✅ 完整 |
| 2 | Game 24 | `run_game24_baseline_methods.py` | ✅ 完整（`game24_dataset/24.csv`） |
| 3 | GSM-Hard | `run_gsm_baseline_methods.py` | ✅ 完整（`dataset_gather/gsmhardv2.jsonl`） |
| 4 | MATH-Geometry | `run_MATH_geometry_baseline_methods.py` | ✅ 完整（`dataset_gather/MATH/train/geometry`） |
| 5 | MATH-Count&Probability | `run_MATH_counting_and_probability_baseline_methods.py` | ✅ 完整 |
| 6 | Date Understanding | `run_big_bench_hard_baseline_methods.py` | ✅ 完整（bbh/*.json） |
| 7 | Web of Lies | 同上 | ✅ 完整 |
| 8 | Logical Deduction | 同上 | ✅ 完整（seven_objects 版） |
| 9 | Navigate | 同上 | ✅ 完整 |
| 10 | Letters | `run_letters_baseline_methods.py` | ✅ 完整（`dataset_gather/Letters`） |
| 11 | BoxLift | `run_BoxLift_baseline_methods.py` | ✅ 完整 |
| 12 | Blocksworld | `run_Blocksworld_baseline_methods.py` | ✅ 完整 |
| 13 | **Path Plan** | `run_path_plan_continuous_baseline_methods.py` | ⚠️ **部分**：仓库版本是 **continuous** 连续路径规划（AutoTAMP 的连续版），论文的 Path Plan 是 **离散 waypoint 序列**。可跑，但要在报告里注明这是 continuous 变体。 |
| 14 | **BoxNet** | `run_BoxNet1_baseline_methods.py` | ⚠️ **部分**：仓库是 **BoxNet1**（官方首版数据集），论文是 Scalable-Robots 的 BoxNet。任务定义一致（robot arms + 彩色 box + goal 圆点），版本号不同。 |

**结论：14 个任务全部有对应的 runner，其中 12 个完全对齐，2 个（Path Plan / BoxNet）是仓库自带的变体版本。**

## 三、方法层面的大缺口（这个比任务更要命）

论文 10 个方法，仓库**只有 `run_Logic_Game_baseline_methods.py` 实现了 6 个**：

| 方法 | 逻辑类 runner（23 任务） | 其它 11 个 runner（含论文全部 14 任务） |
|---|---|---|
| 1_only_ques | ✅ | ✅ |
| All_text | ✅ | ❌ 只有 `if baseline_method_name == '1_only_ques'` 一个分支 |
| All_code_CoT | ✅ | ❌ 同上 |
| AutoGen | ✅ | ❌ 同上 |
| Text_code_summarizer（=论文方法 9 Code+Text+Sum.） | ✅ | ❌ 同上 |
| code_interpreter | ✅ | ❌ 同上 |

**原因**：这 11 个 runner 是在论文投稿**之后**为 CodeSteer 项目写的（SymBench 用的），当时只留了 `1_only_ques` 一条路。

**所以“补齐 15 个任务 × 5 个方法”= 给 11 个 runner 各移植 4 个方法分支（44 个分支）**，这是本复现最大的工作量来源。移植不是复制粘贴，因为每个 runner 的：
- `save_code_dir` 目录结构不同（`Test_sample_{i}/` vs `sample_{i}` vs `{letter}_{freq}_{index}/`）
- 判分逻辑不同（有的本地算，有的调 LLM 当裁判）
- 代码执行块不同（`subprocess.run(["python3", ...])` 的参数、变量名 `result`/`Answer`/`answer`）

## 四、判分器缺口

多个 runner 用 **GPT-4o 当裁判**（`input_prompt_equiv_func`），硬编码 `model_name='gpt-4o'`：

| runner | 判分方式 | 迁移到 DeepSeek 后的问题 |
|---|---|---|
| `run_big_bench_hard_baseline_methods.py` | GPT-4o 裁判 | **必须**换裁判，否则跑不了（没 OpenAI key） |
| `run_game24_baseline_methods.py` | `extract_equation_with_GPT4_game24` 硬编码 gpt-4o | 同上 |
| `run_number_multiply_baseline_methods.py` | `extract_equation_with_GPT4` 硬编码 gpt-4o | 同上 |
| `run_letters_baseline_methods.py` | LLM 裁判 | 同上 |
| `run_BoxLift / run_Blocksworld / run_path_plan` | LLM 裁判 | 同上 |
| `run_gsm / run_MATH_*` | 正则提取 `\boxed{}` 后本地比较 | ✅ 可本地化 |

**决策**：把所有 `model_name='gpt-4o'` 的裁判统一改成 **DeepSeek 裁判**（`deepseek-flash`，thinking disabled，temperature=0，保证裁判稳定），并在报告里注明“裁判模型与论文不同”。

## 五、代码执行缺口

- **79 处硬编码 `"python3"`**（Windows 上不存在，会静默失败）→ `env_win.py` 里 patch `subprocess.run`，把 `["python3", ...]` 改成 `[sys.executable, ...]`
- 执行超时：逻辑 runner 用 15s，论文写 30s → 统一改成 30s
- 执行变量名尝试链：`result` → `Answer` → `answer`（保留原逻辑）

## 六、模型接入缺口

- 每个 runner 的调用点都是 `if model_name in ['o1', 'gpt-4o', ...]` 才走 `GPT_response`，否则掉进本地 HF 分支
- `generation_models.py:313` 白名单里 DeepSeek 分支硬写 `deepseek-reasoner`，且**只读 `content` 不读 `reasoning_content`**
- → `env_win.py` 里 patch：白名单加 `deepseek-flash`，DeepSeek 分支按 `THINK_MODE` 环境变量支持三组（A/B/C）

## 七、本复现的口径（写进报告用）

1. **任务**：论文 14 个 + 自加「句子级字母统计」= 15 个
2. **Path Plan / BoxNet**：标明是仓库的 continuous / BoxNet1 变体
3. **方法**：只跑 5 个（1_only_ques、All_text、All_code_CoT、AutoGen、Text_code_summarizer），砍掉的理由写清楚：
   - `code_interpreter`：依赖 OpenAI Code Interpreter，DeepSeek 无此能力
   - `AutoGen System`：仓库 runner 未接 system message，硬加会改变 AutoGen 语义
   - `Code Interpreter+` / `Self-estimate Score`：仓库未实现
4. **模型**：先 `deepseek-flash`，思考模式三组 A/B/C
5. **判分**：统一 DeepSeek 裁判 + 可本地判分的走本地
