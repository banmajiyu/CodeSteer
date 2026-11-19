"""把 runner 的样本循环压成"只跑 1 个样本"，只给冒烟测试用。

原仓库每个 runner 的样本数硬编码在循环里，写法五花八门：

    game24:       for i in range(j, min(len(df), 1500), 30):     -> 46
    gsm:          for i in range(1, len(question_json_list), 25): -> 53
    MATH:         for i in range(0, 1000):  + if os.path.exists() -> 文件编号从 1 起
    letters:      长度(3) x 字母(5) x 频率(5) x index 四重循环      -> 75
    blocksworld:  24 组配置 x index                              -> 48
    BoxNet1:      3 组网格 x iteration(10)                       -> 30
    BoxLift:      4 组配置 x iteration(5)                        -> 20
    path_plan:    env_index(14) x index(len(instructions))        -> 上百
    BBH:          4 个 env x 内部 range                          -> 每 env 若干

手写每个 runner 的循环正则太脆（第一版被 path_plan / BoxNet1 里无关的
`for i in range(...)` 骗到，注入到了环境描述拼接的循环上）。改成所有
runner 都有的锚点 `total_sample_num += 1`，往上反推包住它的循环链。

两层守卫，位置不同：

1. 内层（最靠近锚点的循环）—— 守卫插在 **锚点行正上方**：
       if not __import__('smoke_limits').first('MATH_geometry#0'): break
       total_sample_num += 1
   为什么不能插在循环体开头：MATH 的循环体是
   `problem_path = ...` / `if os.path.exists(problem_path):`，
   编号从 1 开始，i=0 不存在。守卫若在循环开头，i=0 那次就放行（白跑），
   i=1 就 break —— 结果 0 个样本（前两版都栽在这）。
   贴到锚点前面，只有真正读到样本的那一刻才计数。

2. 外层循环 —— 守卫插在循环体第一句（这些循环体一定读得到样本）。
   否则内层 break 之后外层还会继续跑（blocksworld 24 组、path_plan 14 个场景）。

只改内存里的源码，磁盘文件一个字节都不动。
"""
import re

_SEEN = set()
COUNTER_RE = re.compile(r"^[ \t]*total_sample_num\s*\+=\s*1[ \t]*$", re.M)
FOR_RE = re.compile(r"^[ \t]*for\b")


def first(tag):
    """第一次调用返回 True，之后返回 False。"""
    if tag in _SEEN:
        return False
    _SEEN.add(tag)
    return True


def reset():
    _SEEN.clear()


def _lines(src):
    """返回 [(start, end, text, indent)]，end 指向换行符之后。"""
    out = []
    i = 0
    n = len(src)
    while i < n:
        j = src.find("\n", i)
        if j < 0:
            j = n
        text = src[i:j]
        out.append((i, j + 1, text, len(text) - len(text.lstrip(" \t"))))
        i = j + 1
    return out


def _header_end(src, start):
    """从 for 行起点按括号配平扫到表头结束（返回其后第一个字符的下标）。

    blocksworld / BoxLift / BBH 的表头跨多行，不能只吃一行。
    """
    depth = 0
    i = start
    n = len(src)
    while i < n:
        j = src.find("\n", i)
        if j < 0:
            j = n
        code = src[i:j]
        if depth == 0:
            code = code.split("#", 1)[0]
        depth += code.count("[") + code.count("(") + code.count("{")
        depth -= code.count("]") + code.count(")") + code.count("}")
        stripped = code.rstrip()
        if depth == 0 and stripped.endswith(":") and not stripped.endswith("\\"):
            return j + 1
        i = j + 1
    return None


def _body_start(src, pos):
    """跳过头之后的空行和注释行，返回 (start, end, text, indent)。"""
    for start, end, text, ind in _lines(src[pos:]):
        s = text.strip()
        if s and not s.startswith("#"):
            return pos + start, pos + end, text, ind
    return None, None, None, None


def _enclosing_loops(src):
    """锚点行往上反推包住它的 for 循环链，按位置升序（外层在前）。"""
    m = COUNTER_RE.search(src)
    if not m:
        return []

    line_start = src.rfind("\n", 0, m.start()) + 1
    line_end = src.find("\n", m.start())
    if line_end < 0:
        line_end = len(src)
    anchor_line = src[line_start:line_end]
    target_indent = len(anchor_line) - len(anchor_line.lstrip(" \t"))

    rows = _lines(src)
    idx = None
    for k, (start, end, text, ind) in enumerate(rows):
        if start <= m.start() < end:
            idx = k
            break
    if idx is None:
        return []

    loops = []
    cur = target_indent
    for k in range(idx - 1, -1, -1):
        _start, _end, text, ind = rows[k]
        s = text.strip()
        if not s or s.startswith("#"):
            continue
        if ind >= cur:
            continue                      # 同一块的兄弟语句
        if s[0] in ")]}":
            continue                      # 多行表头的收尾行（blocksworld 的 `]:`），不改变层级
        if FOR_RE.match(text):
            loops.append(_start)
            cur = ind
        elif re.match(r"^[ \t]*(def|class)\b", text):
            break                         # 进了函数/类定义，链到头
        elif s.rstrip().endswith(":"):
            cur = ind                     # if / with / try / else 等块，继续往外找
        else:
            break                         # 普通语句，说明已经跳出这个块
    return sorted(loops)


def _guard_line(indent, tag):
    return " " * indent + f"if not __import__('smoke_limits').first({tag!r}): break\n"


def limit(src, task_key, verbose=True):
    """把 runner 源码压成"只跑 1 个样本"。"""
    loops = _enclosing_loops(src)
    if not loops:
        if verbose:
            print(f"    [smoke-limit] {task_key}: 没找到 total_sample_num 锚点，未限制！")
        return src

    n_ok = 0
    # 外层循环：从外往里插（插入点在锚点之前，倒序不会互相干扰）
    for depth, pos in enumerate(loops[:-1]):
        end = _header_end(src, pos)
        if end is None:
            continue
        _bs, _be, text, ind = _body_start(src, end)
        if text is None:
            continue
        src = src[:end] + _guard_line(ind, f"{task_key}#outer{depth}") + src[end:]
        n_ok += 1

    # 内层循环：守卫贴在锚点行正上方（缩进与锚点一致）
    m = COUNTER_RE.search(src)
    if m is None:
        return src
    line_start = src.rfind("\n", 0, m.start()) + 1
    line_end = src.find("\n", m.start())
    anchor_line = src[line_start: line_end if line_end > 0 else len(src)]
    ind = len(anchor_line) - len(anchor_line.lstrip(" \t"))
    src = src[:line_start] + _guard_line(ind, f"{task_key}#anchor") + src[line_start:]
    n_ok += 1

    if verbose:
        print(f"    [smoke-limit] {task_key}: 压住 {n_ok}/{len(loops)} 层（锚点 1 层 + 外层 {len(loops)-1} 层）")
    return src
