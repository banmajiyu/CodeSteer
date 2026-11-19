"""sample_cap.py —— 正式跑时的样本上限（替代冒烟用的 smoke_limits）

和 smoke_limits 的区别：
  * smoke_limits 让每个循环只转一圈（冒烟）；
  * 这里是**计数**：同一个 (任务, 方法) 跑够 CAP 个样本就停。

为什么用 raise 而不是 break：这些 runner 的样本循环有 1~4 层嵌套
（letters 4 层、bbh 4 个 env × 单层、BoxNet1 3×10），
在最内层 break 只会退出最内层，外层还会继续跑。
所以注入的守卫直接抛 _ReproStop（继承 BaseException，
不会被 runner 里的 except Exception 吞掉），由 run_all 捕获。

用法（由 run_all.py 的注入器写进源码）：
    if __import__('sample_cap').tick('<task>#<method>'):
        raise __import__('sample_cap')._ReproStop()
"""
import os

CAP = int(os.environ.get("REPRO_CAP", "50"))
_counts = {}


class _ReproStop(BaseException):
    """跑到样本上限了，正常结束，不是错误。"""


def tick(key):
    """返回 True 表示"该停了"。第一次调用返回 False（这个样本要跑）。"""
    n = _counts.get(key, 0)
    if n >= CAP:
        return True
    _counts[key] = n + 1
    return False


def done(key):
    return _counts.get(key, 0)


def reset():
    _counts.clear()
