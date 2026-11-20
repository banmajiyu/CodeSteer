# 复现报告：Steering LLMs between Code Execution and Textual Reasoning（ICLR 2025）

## 摘要

本仓库是对 ICLR 2025 论文 *Steering LLMs between Code Execution and Textual Reasoning* 的独立复现，以及在复现基础上的三组扩展实验。

| 项目 | 说明 |
|---|---|
| 论文 | [*Steering LLMs between Code Execution and Textual Reasoning*](https://arxiv.org/abs/2410.03524)（ICLR 2025） |
| 官方实现 | [CodeSteer-v1.0](https://github.com/yongchao98/CodeSteer-v1.0)，以子目录形式原样收录，未作任何修改 |
| 复现规模 | 15 个任务 × 5 个方法 × 3 种思考模式（225 个配置）；正式实验 23,648 次 API 调用 |
| 底座模型 / 裁判模型 | DeepSeek `deepseek-flash`（裁判在三组中始终关闭思考） |
| 适配方式 | 零侵入补丁层（`repro/`）：`sys.path` 注入、运行时 monkey-patch、源码级模板注入 |

复现通过一层零侵入的补丁完成：在官方实现未作任何修改的前提下，补全其缺失的 4 个基线方法分支（`All_text`、`All_code_CoT`、`AutoGen`、`Text_code_summarizer`），将代码执行入口由 `python3` 改为当前解释器，并将 LLM 裁判由 GPT-4o 替换为 DeepSeek。

## 主要结果与发现

结论方向与论文一致：`Code+Text+Sum.` 在三种思考模式下均排名第一（AveNorm 99.4 / 99.4 / 99.7）；代码类方法并不必然优于文本方法（A 组 `All_code_CoT` 77.2 < `All_text` 88.8；Blocksworld 上 `All_code_CoT` 的代码率为 92%，准确率仅 12%）。

复现过程中发现三个会影响结论的问题，论文未涉及：

1. **判分聚合规则偏松。** 官方实现采用双裁判、任一判对即计为正确。改为「两个裁判都判对」后重新统计，总分下降 2 分，代码类方法下降 7~12 分。以 sympy 对 1,000 个样本做独立复核，裁判与本地精确解的一致率为 99.6%，表明偏差来源是聚合规则而非裁判本身。
2. **思考预算会表现为方法差异。** 思考 token 与答案共用 completion 预算。预算为 2,500 时，B 组 27.9% 的样本正文为空，Path Plan 与 BoxNet 被判为 0%；同一批样本将预算提高至 8,000 后恢复至 12~40%。
3. **难度仅在要求精度时产生区分度。** 整数乘法从 8 位增至 18 位、题面改写为场景描述后，准确率仍为 100%（该任务对当前模型已饱和）；改为浮点超越函数复合、要求 10 位有效数字后，代码方法为 100%、纯文本方法为 75~81%；将容差放宽至 1e-3，五个方法又全部回到 100%。

## 文档索引

| 文档 | 内容 |
|---|---|
| [repro/results/复现摘要_两页.pdf](repro/results/复现摘要_两页.pdf) | 两页摘要：主结果、主要发现、实现问题与成本 |
| [repro/results/REPORT.md](repro/results/REPORT.md) | 完整报告：与论文逐条对照、判分可信度审计、偏差分析、成本核算 |
| [repro/results/summary_final.md](repro/results/summary_final.md) | 逐任务结果表（A / B / C 三组） |
| [repro/TASKS_AND_GAPS.md](repro/TASKS_AND_GAPS.md) | 论文任务与官方 runner 的对应关系及缺口清单 |
| [doc/](doc) | 论文 PDF（英文原版与中文版）及抽取正文 `steering_extracted.txt` |
| [CodeSteer-v1.0/README.md](CodeSteer-v1.0/README.md) | 官方使用说明（训练、微调、模型权重） |

---

## 复现方式

```text
任务数据/原版 runner ──► repro/env_win.py（环境补丁）
                          repro/patch_methods.py（方法注入）
                          └─► DeepSeek API ──► 子进程执行代码 ──► 判分
                                                    └─► repro/results/*
```

---

## 目录结构

| 路径 | 内容 |
|---|---|
| [CodeSteer-v1.0/](CodeSteer-v1.0) | 官方代码、数据、模型配置与论文原版 README（保持原样，未作修改） |
| [repro/](repro) | 本次复现的全部代码：环境补丁、方法注入、runner、判分、汇总、成本统计 |
| [repro/results/](repro/results) | 汇总表（`summary*.md` / `summary.csv` / `summary.json`）、两页摘要 PDF 与逐样本产物 |
| [repro/results/复现摘要_两页.pdf](repro/results/复现摘要_两页.pdf) | 两页摘要：主结果表、主要发现、实现问题与成本 |
| [repro/results/REPORT.md](repro/results/REPORT.md) | 完整报告：结果表、与论文逐条对照、偏差分析、成本核算 |
| [repro/TASKS_AND_GAPS.md](repro/TASKS_AND_GAPS.md) | 论文 14 个任务在官方仓库中的对应情况与缺口清单 |
| [doc/](doc) | 论文 PDF（英文原版与中文版）及抽取正文 `steering_extracted.txt` |

复现层核心文件：

| 文件 | 作用 |
|---|---|
| [repro/env_win.py](repro/env_win.py) | 运行环境补丁：`python3`→`sys.executable`、注册 `deepseek-flash`、`THINK_MODE` 三组思考模式、超时统一 30 s、逐次 LLM 调用记账 |
| [repro/patch_methods.py](repro/patch_methods.py) | 为 11 个 runner 注入缺失的 `All_text` / `All_code_CoT` / `AutoGen` / `Text_code_summarizer` 分支（共 44 个分支，同一模板保证语义一致） |
| [repro/run_all.py](repro/run_all.py) | 运行全部任务 × 5 方法，支持断点续跑、样本上限、任务与方法筛选 |
| [repro/run_letters_sentence.py](repro/run_letters_sentence.py) | 新增的第 15 个任务（句级字母统计） |
| [repro/summarize.py](repro/summarize.py) | 由逐样本目录汇总对比表，按论文口径计算 `AveNorm` |
| [repro/cost_report.py](repro/cost_report.py) | 按阶段与思考模式统计 token 与费用 |
| [repro/smoke_runner.py](repro/smoke_runner.py) | 验证性运行：每任务运行 1 个样本，确认取数、注入、API、执行、判分、落盘的完整链路 |

---

## 复现结论

### 主结果：`AveNorm`（%）

| 方法 | A 关思考 | B 丢思考 | C 留思考 |
|---|---|---|---|
| `1_only_ques`（OnlyQ） | 90.3 | 94.8 | 94.3 |
| `All_text` | 88.8 | 89.7 | 91.4 |
| `All_code_CoT` | **77.2** | 89.1 | 90.5 |
| `AutoGen` | 87.1 | 92.7 | 93.2 |
| `Text_code_summarizer`（Code+Text+Sum.） | **99.4** | **99.4** | **99.7** |

与论文一致的三条核心结论：

1. `Code+Text+Sum.` 在三种思考模式下均排名第一。
2. 代码类方法并不必然优于文本方法：A 组 `All_code_CoT`（77.2）明显低于 `All_text`（88.8）；Blocksworld 上 `All_code_CoT` 的代码率为 92%，准确率仅 12%。
3. 仅提供问题而不指定通道时，模型也会自发编写代码：OnlyQ 在 Blocksworld 15%、Path Plan 14% 的样本中产出可执行代码，但「编写了代码」并不等于「代码对结果有用」。

逐任务明细见 [repro/results/summary_final.md](repro/results/summary_final.md) 与 [repro/results/REPORT.md](repro/results/REPORT.md)。

### 结果解读的三点限制

- **分数饱和**：`deepseek-flash` 在 MATH / GSM / BBH 上已接近饱和（多数任务 96~100%），方法间差异被压缩到数点以内。真正具备区分度的是 Game 24、MATH-Geometry、Path Plan、BoxLift、Blocksworld、Letters(sentence)。
- **绝对分数不可直接比较**：归一化所用的 `max` 仅在本次 5 个方法内取值（论文为 10 个方法），且底座模型不同。因此本文只比较名次与方向，不比较绝对数值。
- **B 组 BoxNet / Path Plan 的 0% 由预算截断造成**：2,500 token 输出预算被思考内容占满、正文为空所致；预算提高至 8,000 后恢复至 12~40%（见完整报告第 6 节敏感性重跑）。

---

## 实验设置

| 项目 | 设置 |
|---|---|
| 任务 | 论文 Table 2 的 14 个任务，另加「句级字母统计」= 15 个 |
| 方法 | 5 个：`1_only_ques`、`All_text`、`All_code_CoT`、`AutoGen`、`Text_code_summarizer` |
| 未纳入的方法 | `Code Interpreter` 系（DeepSeek 无 CI 通道）、`AutoGen System`（runner 未接入 system message 分支）、`Self-estimate Score`（官方仓库未实现） |
| 样本量 | 每任务 25 个（Navigate 11、BoxLift 20，三组统一） |
| 代码执行 | 子进程，超时 30 s（论文口径） |
| 思考模式 | A=`off`（不思考）、B=`strip`（开启思考但丢弃 `reasoning_content`）、C=`on`（思考内容与正文一并下传） |
| 思考预算 | 2,500 tokens（敏感性实验 8,000） |
| 归一化 | `AveNorm_j = (1/N) Σ_i s_ij / max_i(s_ij)` |
| 规模 | 正式三组 23,648 次 API 调用；含返工与验证性运行共 56,084 次，约 117~234 元 |

---

## 快速开始

### 1. 环境

```powershell
conda create -n CodeSteer python=3.10
conda activate CodeSteer
pip install -r CodeSteer-v1.0/requirements.txt
```

仅进行 API 推理（不训练、不使用 GPU）时，`deepspeed` / `trl` / `peft` 等训练依赖可以不安装；必需的是 `openai`、`anthropic`、`python-dotenv`、`datasets`、`pandas`、`sympy`、`python-constraint`。
网络受限时可用仓库自带的离线包：

```powershell
pip install --no-index --find-links repro/wheels -r CodeSteer-v1.0/requirements.txt
```

> `repro/vendor/` 和 `repro/wheels/` 体积大且可由 pip 重装，已被 `.gitignore` 忽略。

### 2. 配置 API Key

在**仓库根目录**新建 `.env`（已被 `.gitignore` 忽略，切勿提交）：

```ini
DEEPSEEK_API_KEY=sk-xxxxxxxx
```

### 3. 验证性运行（以小样本确认完整链路）

```powershell
cd repro
python -X utf8 smoke_runner.py --only gsm
python -X utf8 smoke_runner.py --methods all --only gsm   # 5 个方法各验证一遍
```

### 4. 正式实验

```powershell
cd repro
python -X utf8 run_all.py --estimate                              # 仅估算调用次数与耗时，不产生费用
$env:THINK_MODE='off'
python -X utf8 run_all.py --cap 25                                # 每组思考模式各运行一次
python -X utf8 run_all.py --tasks gsm,game24 --methods 1_only_ques   # 仅运行指定子集
python -X utf8 run_all.py --force                                 # 忽略完成记录并重跑
```

需要缩短墙钟时间时可按分片并行运行（3 种思考模式 × 3 个任务分片）。本机 PowerShell 执行策略会拦截未签名脚本（`SecurityError: 未对文件 ... 进行数字签名`），因此需要内联启动，例如：

```powershell
cd repro
$env:THINK_MODE='off'; $env:REPRO_STATE_TAG='s1'; $env:REPRO_LOG="$PWD\logs\llm_calls_off_s1.jsonl"
& <python.exe 路径> -X utf8 run_all.py --cap 25 --tasks game24,number_multiply,letters,gsm 2>&1 |
  Tee-Object -FilePath logs\run_off_s1.log
```

分片划分：`s1` = game24,number_multiply,letters,gsm；`s2` = MATH_geometry,MATH_cp,BoxNet1,blocksworld,BoxLift；`s3` = big_bench_hard,path_plan,letters_sentence。同一任务不应同时由两个 worker 运行，否则会写入同一结果目录。

### 5. 汇总与成本

```powershell
python -X utf8 summarize.py --md results/summary.md
python -X utf8 cost_report.py
```

---

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | — | **必填** |
| `DS_MODEL` | `deepseek-flash` | 主模型 |
| `DS_JUDGE_MODEL` | `deepseek-flash` | 裁判模型（始终关闭思考，保证三组可比） |
| `DS_BASE_URL` | `https://api.deepseek.com` | API 地址 |
| `THINK_MODE` | `off` | `off` / `strip` / `on`，对应 A / B / C 三组 |
| `CODE_TIMEOUT` | `30` | 代码执行超时（秒） |
| `REPRO_LOG` | `repro/logs/llm_calls.jsonl` | 逐次 LLM 调用记录（token、耗时、阶段） |
| `REPRO_STATE_TAG` | `main` | 分片使用的断点记录标签 |
| `REPRO_DIR_TAG` | 空 | 覆盖结果目录名（默认 `results/main_{THINK_MODE}`） |

---

## 已知偏差

- **Path Plan 是 continuous 变体**：官方仓库该 runner 对应 AutoTAMP 的连续路径规划，论文中的 Path Plan 是离散 waypoint 序列。
- **BoxNet 是 BoxNet1**：官方仓库提供的是 BoxNet1 数据集，任务定义一致但版本号不同。
- **裁判模型不同**：论文用 GPT-4o 作裁判，本次统一换成 `deepseek-flash`（temperature=0、关闭思考），本地可判的任务仍走本地判分。
- **输入口径**：`All_code_CoT` 的代码率并非 100%（BoxNet 33%、BoxLift 60%、Path Plan 46%），即「代码方法」在这些任务上实际退化成文本方法——这与论文「模型偏好文本通道」的观察方向一致，但不构成严格复刻。

各条偏差的原始证据与敏感性重跑见 [repro/results/REPORT.md](repro/results/REPORT.md) 第 6 节。

---

## 引用

```bibtex
@misc{chen2025codesteersymbolicaugmentedlanguagemodels,
      title={CodeSteer: Symbolic-Augmented Language Models via Code/Text Guidance},
      author={Yongchao Chen and Yilun Hao and Yueying Liu and Yang Zhang and Chuchu Fan},
      year={2025},
      eprint={2502.04350},
      archivePrefix={arXiv}
}

@inproceedings{chen2025steering,
      title={Steering Large Language Models between Code Execution and Textual Reasoning},
      author={Yongchao Chen and Harsh Jhamtani and Srinagesh Sharma and Chuchu Fan and Chi Wang},
      booktitle={International Conference on Learning Representations (ICLR)},
      year={2025}
}
```

## License

`CodeSteer-v1.0/` 采用 [Apache License 2.0](CodeSteer-v1.0/LICENSE)，版权归原作者所有。`repro/` 与 `doc/` 为本次复现产物，遵循同一许可证；论文 PDF 版权归原出版方，仅供学习研究使用。
