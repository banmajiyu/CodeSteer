# -*- coding: utf-8 -*-
"""生成两页 A4 摘要（docx），随后由 Word 导出 PDF。"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "复现摘要_两页.docx")

HEI = "微软雅黑"
SONG = "宋体"
GRAY = RGBColor(0x59, 0x59, 0x59)
ACCENT = RGBColor(0x1F, 0x3A, 0x5F)

BODY = 10.0
TBL = 8.6


def cn(run, font=SONG, size=BODY, bold=False, color=None):
    run.font.name = font
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    run.font.size = Pt(size)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color


def para(doc, space_before=0, space_after=2, line=1.0, align=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if align is not None:
        p.alignment = align
    return p


def add_text(doc, text, font=SONG, size=BODY, bold=False, color=None,
             space_before=0, space_after=3, line=1.1):
    p = para(doc, space_before, space_after, line)
    cn(p.add_run(text), font, size, bold, color)
    return p


def add_rich(doc, parts, space_before=0, space_after=3, line=1.1, indent=None):
    p = para(doc, space_before, space_after, line)
    if indent is not None:
        p.paragraph_format.left_indent = Cm(indent)
    for text, kw in parts:
        cn(p.add_run(text), kw.get("font", SONG), kw.get("size", BODY),
           kw.get("bold", False), kw.get("color"))
    return p


def heading(doc, text, size=11.5, space_before=9, space_after=4):
    p = para(doc, space_before, space_after, 1.0)
    cn(p.add_run(text), HEI, size, True, ACCENT)
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), "1F3A5F")
    pbdr.append(bottom)
    pPr.append(pbdr)
    return p


def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def vcenter(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    va = OxmlElement("w:vAlign")
    va.set(qn("w:val"), "center")
    tcPr.append(va)


def cell_text(cell, text, size=TBL, bold=False, color=None,
              align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.08
    cn(p.add_run(text), SONG, size, bold, color)
    vcenter(cell)


def fixed_layout(t, widths):
    tblPr = t._tbl.tblPr
    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:w"), str(int(sum(widths) * 567)))
    tblW.set(qn("w:type"), "dxa")
    tblPr.append(tblW)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    mar = OxmlElement("w:tblCellMar")
    for side, val in (("top", 40), ("left", 100), ("bottom", 40), ("right", 100)):
        el = OxmlElement("w:" + side)
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


def make_table(doc, headers, rows, widths, header_fill="1F3A5F",
               zebra="EEF1F5", size=TBL, center_cols=(), bold_last=False):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell_text(cell, h, size=size, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF),
                  align=WD_ALIGN_PARAGRAPH.CENTER)
        shade(cell, header_fill)
    for r_i, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            a = WD_ALIGN_PARAGRAPH.CENTER if i in center_cols else WD_ALIGN_PARAGRAPH.LEFT
            cell_text(cells[i], v, size=size,
                      bold=(bold_last and r_i == len(rows) - 1), align=a)
            if zebra and r_i % 2 == 1:
                shade(cells[i], zebra)
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w)
    fixed_layout(t, widths)
    return t


def build():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(1.6)
    sec.bottom_margin = Cm(1.6)
    sec.left_margin = Cm(1.8)
    sec.right_margin = Cm(1.8)

    style = doc.styles["Normal"]
    style.font.name = SONG
    style.font.size = Pt(BODY)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), SONG)

    # ---------- 标题 ----------
    p = para(doc, 0, 3, 1.1)
    cn(p.add_run("用文本还是用代码：一篇 ICLR'25 论文的独立复现与三项扩展实验"),
       HEI, 16, True, ACCENT)

    add_rich(doc, [
        ("复现对象：", dict(size=8.8, bold=True, color=GRAY)),
        ("Steering LLMs between Code Execution and Textual Reasoning", dict(size=8.8, color=GRAY)),
        ("（ICLR 2025, arXiv:2410.03524）", dict(size=8.8, color=GRAY)),
    ], space_after=1)
    add_rich(doc, [
        ("作者：", dict(size=8.8, bold=True, color=GRAY)),
        ("清华大学自动化系本科生（独立完成）", dict(size=8.8, color=GRAY)),
        ("　·　2026 年 11 月　·　代码与完整报告：github.com/banmajiyu/CodeSteer", dict(size=8.8, color=GRAY)),
    ], space_after=2)

    # ---------- 一 ----------
    heading(doc, "一、做了什么", space_before=6)
    add_text(doc, "为官方仓库 CodeSteer-v1.0 增加一层零侵入补丁，在未修改任何原始代码的前提下完成论文全部方法的实现与运行，"
                  "并在复现基础上补做三组论文未涉及的对照实验。")
    bullets = [
        ("规模", "15 个任务（论文 14 个 + 自建句级字母统计）× 5 个方法 × 3 种思考模式 = 225 个组合，"
                 "每任务 25 个样本（Navigate 11、BoxLift 20），正式实验 23,648 次 API 调用。"),
        ("五个方法", "Only Question / All Text / All Code+CoT / AutoGen / Code+Text+Summary。"
                    "原仓库只实现了 Only Question，其余四个用同一模板注入 44 个分支，保证语义一致。"),
        ("三组思考模式", "A 关闭思考；B 开启思考但丢弃 reasoning_content（只取正文）；"
                       "C 把思考内容与正文一起下传。裁判模型在三组中始终关闭思考，保证可比。"),
        ("零改动", "模型注册、裁判替换、python3 路由、缺失分支注入全部在独立目录内以 patch 方式挂载，"
                 "原仓库可直接 diff 核对。"),
    ]
    for k, v in bullets:
        add_rich(doc, [("· " + k + "：", dict(bold=True)), (v, dict())],
                 space_after=2.5, line=1.12)

    # ---------- 二 ----------
    heading(doc, "二、主结果：AveNorm（%，论文 Table 2 口径）")
    rows = [
        ["Only Question", "90.3", "94.8", "94.3"],
        ["All Text", "88.8", "89.7", "91.4"],
        ["All Code+CoT", "77.2", "89.1", "90.5"],
        ["AutoGen", "87.1", "92.7", "93.2"],
        ["Code+Text+Summary", "99.4", "99.4", "99.7"],
    ]
    make_table(doc, ["方法", "A 关思考", "B 丢思考", "C 留思考"], rows,
               [7.4, 3.4, 3.4, 3.4], center_cols=(1, 2, 3), bold_last=True)
    add_text(doc, "对应仓库方法名依次为 1_only_ques / All_text / All_code_CoT / AutoGen / Text_code_summarizer。",
             size=8.4, color=GRAY, space_before=3, space_after=1)
    add_text(doc, "AveNorm_j = (1/N) Σ_i s_ij / max_i(s_ij)，即每个任务先除以该任务 5 个方法中的最高分再平均。",
             size=8.4, color=GRAY, space_after=2)

    # ---------- 三 ----------
    heading(doc, "三、与论文一致的三条结论")
    for t in [
        "组合方法最优：文本与代码两路都提供、再汇总，在三组思考模式下都拿到最高分（99.4 / 99.4 / 99.7）。",
        "代码类方法并不必然更好：A 组 All Code+CoT（77.2）明显低于 All Text（88.8）；Blocksworld 上 "
        "All Code+CoT 的代码率 92%，准确率只有 12%——模型给出的答案没按 <<<>>> 格式输出，被判分器漏掉。",
        "不给指令模型也会自发写代码：Only Question 在 Blocksworld 15%、Path Plan 14% 的样本里自行产出代码，"
        "但成绩没有变好——「写了代码」不等于「代码有用」。",
    ]:
        add_text(doc, "· " + t, space_after=2.5, line=1.12)

    # ---------- 四 ----------
    heading(doc, "四、结果解读的三点限制")
    for t in [
        "天花板效应：deepseek-flash 在 MATH / GSM / BBH 上多数任务已到 96~100%，15 个任务里有 6 个是"
        "「五个方法最低分都 ≥95%」；方法差异被压缩到几个点，真正能区分的是 Game 24、MATH-Geometry、"
        "Path Plan、BoxLift、Blocksworld 与 Letters(sentence)。",
        "绝对数值不可比：AveNorm 里的 max 只在本次 5 个方法内取（论文是 10 个），底座模型也不同，"
        "因此只能比名次与方向，不能比绝对分数。",
        "与官方仓库的版本差异：Path Plan 跑的是 continuous 变体（论文为离散 waypoint），"
        "BoxNet 是 BoxNet1 数据集；裁判由 GPT-4o 换成 deepseek-flash（temperature=0、关闭思考）。",
    ]:
        add_text(doc, "· " + t, space_after=2.5, line=1.12)

    # ---------- 分页 ----------
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------- 五 ----------
    heading(doc, "五、复现中发现的三个问题（论文未涉及，但会改变结论）", space_before=0)
    make_table(
        doc,
        ["问题", "证据", "影响"],
        [
            ["判分聚合规则偏松",
             "原仓库用双裁判，任一判对即算对。改成「两个都判对」重算：总分只掉 2 分，"
             "代码类方法却掉 7~12 分。另用 sympy 独立复核 1,000 个样本，裁判与本地精确解一致率 99.6%"
             "——问题不在裁判，在聚合规则。",
             "代码类方法的一部分优势来自判定规则，而非计算能力。"],
            ["思考预算伪装成方法差异",
             "思考 token 与答案共享 completion 预算。预算 2,500 时，B 组 27.9% 的样本正文为空，"
             "Path Plan / BoxNet 被判 0%；同一批题把预算提到 8,000，分数变成 12~40%。",
             "预算不足会被误读成「方法本身不行」。"],
            ["难度只在要求精度时才区分方法",
             "整数乘法从 8 位加到 18 位、题面换成场景清单，准确率始终 100%（这批题已饱和）。"
             "换成浮点超越函数复合、要求 10 位有效数字后，代码方法 100%、纯文本 75~81%；"
             "但容差放宽到 1e-3，五个方法又全部回到 100%。",
             "方法优劣取决于任务需要什么；任务集里有没有「必须算准」的题，会直接决定方法排名。"],
        ],
        [3.6, 9.4, 4.4], size=8.2)

    # ---------- 六 ----------
    heading(doc, "六、复现中修正的问题（症状 → 根因 → 修正方式）")
    make_table(
        doc,
        ["症状", "根因", "修正方式"],
        [
            ["所有代码执行 stdout 恒空",
             "python -c 里的 Windows 路径 C:\\Users… 中 \\U 被当成 Unicode 转义 → SyntaxError，"
             "子进程从未执行到代码",
             "命令内路径改用正斜杠"],
            ["子进程一律 PermissionError", "运行环境禁止匿名管道", "capture_output 改为落文件再读回"],
            ["生成入口报 NameError: run_response", "模型白名单不含新模型，掉进本地 HF 权重分支",
             "源码级跨行正则注入白名单"],
            ["判分报 ValueError: 只接管 DeepSeek", "裁判硬编码 gpt-4o", "按模型名分流到裁判模型"],
            ["主模型调用被劫持成裁判", "无条件覆盖模块级 GPT_response", "只在裁判路径替换"],
            ["样本上限不生效 / 子任务被判 0",
             "守卫异常被 except Exception 吞掉；计数键是任务级，第一个子任务吃光配额",
             "改用 BaseException；按子任务分别计数"],
            ["汇总表整行消失", "结果目录名的大小写与别名不一致（math_c_p / boxnet1 / boxlift）",
             "加别名映射表"],
            ["自写判分脚本「发现」裁判 23 个错误",
             "本地解析器不支持 \\frac、\\sqrt、千分位逗号",
             "逐条修解析器：一致率 86.2% → 99.6%（23 个误判全是解析器错）"],
        ],
        [4.2, 8.0, 5.2], size=8.2)

    # ---------- 七 ----------
    heading(doc, "七、成本与可复现性")
    add_text(doc, "三组正式实验 23,648 次调用，约 58~116 元；含返工与验证性运行共 56,084 次，约 117~234 元"
                  "（deepseek-flash 官方价，逐次调用记账落在仓库 logs/）。"
                  "一条命令可复算：python -X utf8 run_all.py --estimate（仅估算调用次数与耗时，不产生费用）。"
                  "完整报告见 repro/results/REPORT.md，含判分可信度审计、已知偏差与逐任务明细。",
             size=9.2, line=1.18)

    # ---------- 八 ----------
    heading(doc, "八、接下来想做的")
    add_text(doc, "第三个问题指出的方向是：把「任务需要多少数值精度、是否需要外部计算」做成显式的路由信号，"
                  "而不是靠 prompt 诱导模型自己选通道。现有方法的共同点是让模型一次性决定用文本还是用代码，"
                  "而实验显示这个决定是否划算，几乎完全由任务对精度的要求在决定。如果能把这条信号提取出来，"
                  "文本/代码的选择就可以从「提示词技巧」变成「可检验的判据」。这是我下一步最想做的实验。",
             size=9.2, line=1.18)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    build()
