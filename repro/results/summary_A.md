# 复现结果：15 任务 × 5 方法 × 3 种思考模式

数字为准确率(%)；n = 该任务样本数；AveNorm = 论文 Table 2 的归一化均值。

## A 关思考（THINK_MODE=off）

| 任务 | OnlyQ | AllText | AllCode+CoT | AutoGen | Code+Text+Sum | n |
|---|---|---|---|---|---|---|
| Number Multiplying |  96.0 | 100.0 | 100.0 |  96.0 | 100.0 | 25 |
| Game 24 |  76.0 |  92.0 |  84.0 |  84.0 |  96.0 | 24 |
| GSM-Hard |  92.0 |  92.0 |  92.0 |  92.0 |  92.0 | 23 |
| MATH-Geometry |  92.0 |  84.0 |  96.0 |  96.0 |  96.0 | 24 |
| Date Understanding |  96.0 |  96.0 |  96.0 |  96.0 | 100.0 | 25 |
| Web of Lies | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 25 |
| Logical Deduction | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 25 |
| Navigate | 100.0 | 100.0 | 100.0 |  90.9 | 100.0 | 11 |
| Path Plan |  56.0 |  36.0 |  60.0 |  44.0 |  64.0 | 16 |
| Letters | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 25 |
| Blocksworld | 100.0 | 100.0 |  12.0 |  96.0 | 100.0 | 25 |
| Letters(sentence) |  88.0 |  78.0 |  70.0 |  82.0 |  80.0 | 44 |
| **AveNorm** | **90.3** | **88.7** | **77.9** | **87.0** | **99.4** | |

## B 丢思考（THINK_MODE=strip）

| 任务 | OnlyQ | AllText | AllCode+CoT | AutoGen | Code+Text+Sum | n |
|---|---|---|---|---|---|---|
| Game 24 | 100.0 | 100.0 |   -   |   -   |   -   | 25 |
| MATH-Geometry |  86.7 |   -   |   -   |   -   |   -   | 13 |
| Date Understanding |  95.5 |   -   |   -   |   -   |   -   | 21 |
| **AveNorm** | **100.0** | **100.0** |   -   |   -   |   -   | |

## C 留思考（THINK_MODE=on）

| 任务 | OnlyQ | AllText | AllCode+CoT | AutoGen | Code+Text+Sum | n |
|---|---|---|---|---|---|---|
| Game 24 |  96.0 | 100.0 |   -   |   -   |   -   | 24 |
| MATH-Geometry |  92.3 |   -   |   -   |   -   |   -   | 12 |
| Date Understanding | 100.0 |   -   |   -   |   -   |   -   | 18 |
| **AveNorm** | **98.7** | **100.0** |   -   |   -   |   -   | |

## 三种思考模式的横向对比（AveNorm %）

| 方法 | A 关思考 | B 丢思考 | C 留思考 |
|---|---|---|---|
| OnlyQ | 90.3 | 100.0 | 98.7 |
| AllText | 88.7 | 100.0 | 100.0 |
| AllCode+CoT | 77.9 |   -   |   -   |
| AutoGen | 87.0 |   -   |   -   |
| Code+Text+Sum | 99.4 |   -   |   -   |
