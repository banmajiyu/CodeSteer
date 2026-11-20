# CodeSteer 复现：Steering LLMs between Code Execution and Textual Reasoning (ICLR'25)

对本仓库目标论文的独立复现：

- 论文：[*Steering LLMs between Code Execution and Textual Reasoning*](https://arxiv.org/abs/2410.03524)（ICLR'25）
- 官方代码：[CodeSteer-v1.0](https://github.com/yongchao98/CodeSteer-v1.0)（本仓库以子目录形式原样收录，**未做任何修改**）
- 复现规模：**15 个任务 × 5 个方法 × 3 种思考模式**
- 主模型 / 裁判模型：DeepSeek `deepseek-flash`（裁判始终关闭思考）

复现的方法是给官方仓库补一个**零侵入的补丁层**（`repro/`）：通过 `sys.path` + monkey-patch + 源码级注入，补齐原仓库缺失的 4 个 baseline 方法分支、把 `python3` 换成当前解释器、把 GPT-4o 裁判换成 DeepSeek 裁判，然后跑完全部实验。

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
| [CodeSteer-v1.0/](CodeSteer-v1.0) | 官方代码、数据、模型配置与论文原版 README（**保持原样，不要改**） |
| [repro/](repro) | 本次复现的全部代码：环境补丁、方法注入、runner、判分、汇总、成本统计 |
| [repro/results/](repro/results) | 汇总表（`summary*.md` / `summary.csv` / `summary.json`）与逐样本产物 |
| [repro/results/REPORT.md](repro/results/REPORT.md) | **完整复现报告**：结果表、与论文逐条对照、偏差分析、成本账单 |
| [repro/TASKS_AND_GAPS.md](repro/TASKS_AND_GAPS.md) | 论文 14 个任务在官方仓库里的落地情况与缺口清单 |
| [doc/](doc) | 论文 PDF（英文原版 + 中文版）与抽取出的正文 `steering_extracted.txt` |

复现层核心文件：

| 文件 | 作用 |
|---|---|
| [repro/env_win.py](repro/env_win.py) | Windows + 国产模型环境补丁：`python3`→`sys.executable`、注册 `deepseek-flash`、`THINK_MODE` 三组思考模式、超时统一 30 s、逐次 LLM 调用记账 |
| [repro/patch_methods.py](repro/patch_methods.py) | 给 11 个 runner 注入缺失的 `All_text` / `All_code_CoT` / `AutoGen` / `Text_code_summarizer` 分支（共 44 个分支，同一模板保证语义一致） |
| [repro/run_all.py](repro/run_all.py) | 正式跑全部任务 × 5 方法，支持断点续跑、样本上限、任务/方法筛选 |
| [repro/run_letters_sentence.py](repro/run_letters_sentence.py) | 自加的 15 号任务（句级字母统计） |
| [repro/summarize.py](repro/summarize.py) | 从逐样本目录汇总出对比表，按论文口径算 `AveNorm` |
| [repro/cost_report.py](repro/cost_report.py) | 按阶段 / 思考模式统计 token 与费用 |
| [repro/smoke_runner.py](repro/smoke_runner.py) | 冒烟测试：每任务跑 1 个样本，验证「取数 → 注入 → API → 执行 → 判分 → 落盘」整条链路 |

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

1. **`Code+Text+Sum.` 在三组里全部排第一**。
2. **「代码类方法不一定比文本方法好」**：A 组 `All_code_CoT`(77.2) 明显低于 `All_text`(88.8)；Blocksworld 上 `All_code_CoT` 代码率 92% 但准确率只有 12%。
3. **「只给问题，模型也会自发写代码」**：OnlyQ 在 Blocksworld 15%、Path Plan 14% 的样本里自行产出可执行代码——「写了代码」不等于「代码有用」。

逐任务明细见 [repro/results/summary_final.md](repro/results/summary_final.md) 与 [repro/results/REPORT.md](repro/results/REPORT.md)。

### 必须打折的三点

- **分数天花板**：2026 年的 `deepseek-flash` 在 MATH/GSM/BBH 上已接近满分（多数任务 96~100%），方法间差异被压缩到几个点以内；真正能区分方法的是 Game 24、MATH-Geometry、Path Plan、BoxLift、Blocksworld、Letters(sentence)。
- **绝对分数不可比**：归一化的 `max` 只在本次 5 个方法内取（论文是 10 个），且模型不同，因此**只能比名次与方向，不能比绝对数值**。
- **B 组 BoxNet / Path Plan 的 0% 是假象**：2500 token 输出预算被思考内容吃光、正文为空所致；提到 8000 后回到 12~40%（见报告第 6 节敏感性重跑）。

---

## 实验设置

| 项目 | 设置 |
|---|---|
| 任务 | 论文 Table 2 的 14 个任务 + 自加「句级字母统计」= 15 个 |
| 方法 | 5 个：`1_only_ques`、`All_text`、`All_code_CoT`、`AutoGen`、`Text_code_summarizer` |
| 砍掉的方法 | `Code Interpreter` 系（DeepSeek 无 CI 通道）、`AutoGen System`（runner 未接 system message 分支）、`Self-estimate Score`（仓库未实现） |
| 样本量 | 每任务 25 个（Navigate 11、BoxLift 20，三组统一） |
| 代码执行 | 子进程，超时 30 s（论文口径） |
| 思考模式 | A=`off`（不思考）、B=`strip`（开思考但丢弃 `reasoning_content`）、C=`on`（思考+正文一起下传） |
| 思考预算 | 2500 tokens（敏感性实验 8000） |
| 归一化 | `AveNorm_j = (1/N) Σ_i s_ij / max_i(s_ij)` |
| 规模 | 正式三组 23,648 次 API 调用；含返工与冒烟共 56,084 次，约 117~234 元 |

---

## 快速开始

### 1. 环境

```powershell
conda create -n CodeSteer python=3.10
conda activate CodeSteer
pip install -r CodeSteer-v1.0/requirements.txt
```

只跑 API 推理（不训练、不用 GPU）时，`deepspeed` / `trl` / `peft` 等训练依赖可以不装，必需的是 `openai`、`anthropic`、`python-dotenv`、`datasets`、`pandas`、`sympy`、`python-constraint`。
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

### 3. 冒烟测试（先花几分钱确认链路通）

```powershell
cd repro
python -X utf8 smoke_runner.py --only gsm
python -X utf8 smoke_runner.py --methods all --only gsm   # 5 个方法都过一遍
```

### 4. 正式跑

```powershell
cd repro
python -X utf8 run_all.py --estimate                       # 只估调用次数与耗时，不花钱
$env:THINK_MODE='off'
python -X utf8 run_all.py --cap 25                         # 三组思考模式各跑一次
python -X utf8 run_all.py --tasks gsm,game24 --methods 1_only_ques   # 只跑子集
python -X utf8 run_all.py --force                          # 忽略已完成记录重跑
```

追求速度用并行分片启动器（3 种思考模式 × 3 个任务分片 = 9 个 worker，各自独立记账与日志）：

```powershell
pwsh -File launch_shards.ps1
```

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

## 已知偏差（引用本结果前必读）

- **Path Plan 是 continuous 变体**：官方仓库该 runner 对应 AutoTAMP 的连续路径规划，论文中的 Path Plan 是离散 waypoint 序列。
- **BoxNet 是 BoxNet1**：官方仓库提供的是 BoxNet1 数据集，任务定义一致但版本号不同。
- **裁判模型不同**：论文用 GPT-4o 作裁判，本次统一换成 `deepseek-flash`（temperature=0、关闭思考），本地可判的任务仍走本地判分。
- **输入口径**：`All_code_CoT` 的代码率并非 100%（BoxNet 33%、BoxLift 60%、Path Plan 46%），即「代码方法」在这些任务上实际退化成文本方法——这与论文「模型偏好文本通道」的观察方向一致，但不构成严格复刻。

各条偏差的原始证据与敏感性重跑见 [repro/results/REPORT.md](repro/results/REPORT.md) 第 6 节。

---

## 文档索引

| 想了解 | 看这里 |
|---|---|
| 论文原文 | [doc/](doc)（PDF 英文 / 中文，及抽取正文） |
| 官方使用说明（训练、微调、模型权重） | [CodeSteer-v1.0/README.md](CodeSteer-v1.0/README.md) |
| 复现结果与偏差分析 | [repro/results/REPORT.md](repro/results/REPORT.md) |
| 论文任务 → 仓库 runner 的映射与缺口 | [repro/TASKS_AND_GAPS.md](repro/TASKS_AND_GAPS.md) |

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
