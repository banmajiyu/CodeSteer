"""
env_win.py —— 在 Windows + 国产模型 API 上跑 CodeSteer-v1.0 的环境补丁层

设计原则：**原仓库零改动**。所有修补都在 import 期通过 monkey-patch 完成。

用法：
    import env_win          # 必须放在 import 仓库模块之前
    import run_game24_baseline_methods as R
    ...

环境变量：
    DEEPSEEK_API_KEY        必填
    DS_MODEL                主模型，默认 deepseek-flash
    DS_JUDGE_MODEL          裁判模型，默认 deepseek-flash
    THINK_MODE              on / off / strip   思考模式三组（见下）
    CODE_TIMEOUT            代码执行超时秒数，默认 30（论文口径）
    REPRO_LOG               可选，记录每次 LLM 调用的 jsonl 路径

THINK_MODE 三组（对应实验设计）：
    off    thinking disabled，只拿 content            —— 组 A，纯答案
    strip  thinking enabled，丢掉 reasoning_content    —— 组 B，"忽略思考内容"
    on     thinking enabled，把 reasoning_content 拼回 content —— 组 C，"保留思考内容"
"""
import os
import re
import sys
import json
import time
import subprocess
import builtins

# ---------------------------------------------------------------- 路径准备
# 原仓库零改动：把它加到 sys.path，并切换工作目录（各 runner 用 './dataset_gather' 相对路径）
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(os.path.dirname(HERE), "CodeSteer-v1.0")
VENDOR = os.path.join(HERE, "vendor")
for _p in (os.path.join(VENDOR, "_stubs"), VENDOR, os.path.join(REPO, "benchmark"), REPO):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
if os.path.isdir(REPO) and os.path.abspath(os.getcwd()) != os.path.abspath(REPO):
    os.chdir(REPO)

# 载入 .env（仓库根目录那份，也就是 repro/ 的上一级）
try:
    from dotenv import load_dotenv as _load_dotenv
    for _envf in (os.path.join(os.path.dirname(HERE), ".env"),
                  os.path.join(HERE, ".env"),
                  os.path.join(REPO, ".env")):
        if os.path.exists(_envf):
            _load_dotenv(_envf, override=False)
            break
except ImportError:
    # 没有 python-dotenv 时手搓一个最小解析
    for _envf in (os.path.join(os.path.dirname(HERE), ".env"), os.path.join(REPO, ".env")):
        if os.path.exists(_envf):
            for _line in open(_envf, encoding="utf-8"):
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip().strip('"\''))
            break

# ---------------------------------------------------------------- 基本配置
DS_MODEL = os.getenv("DS_MODEL", "deepseek-flash")
DS_JUDGE_MODEL = os.getenv("DS_JUDGE_MODEL", "deepseek-flash")
THINK_MODE = os.getenv("THINK_MODE", "off").strip().lower()
CODE_TIMEOUT = int(os.getenv("CODE_TIMEOUT", "30"))
# 每次 LLM 调用都记一行，用来事后核对"到底花了多少钱、调了多少次"
REPRO_LOG = os.getenv("REPRO_LOG") or os.path.join(HERE, "logs", "llm_calls.jsonl")
DS_BASE_URL = os.getenv("DS_BASE_URL", "https://api.deepseek.com")

if THINK_MODE not in ("off", "strip", "on"):
    raise SystemExit(f"THINK_MODE 只能是 off/strip/on，收到的是 {THINK_MODE!r}")

# 这些"模型名"都走 DeepSeek 分支。故意复用原仓库里已有的 'DeepSeek-R1'
# 这个名字，这样**不用改任何 runner 的模型白名单**，runner 里照旧传 'DeepSeek-R1' 即可。
DS_ALIASES = {"DeepSeek-R1", DS_MODEL, "deepseek-flash", "deepseek-v4-pro"}


def log_line(path, record):
    if not path:
        return
    record = dict(record)
    record.setdefault("ts", time.strftime("%Y-%m-%d %H:%M:%S"))
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- 1. patch subprocess：python3 -> 当前解释器
_orig_run = subprocess.run
_orig_Popen = subprocess.Popen


def _fix_cmd(cmd):
    """"python3" 在 Windows 上不存在，换成当前解释器；同时修 -c 里的路径。

    ⚠️ 关键坑：runner 用 `python -c "exec(open('{save_code_dir}/code_1_0.py').read())"`
    这种方式执行生成的代码。save_code_dir 是 Windows 绝对路径（C:\\Users\\...），
    塞进 -c 的字符串字面量后 `\\U` 会被当成 unicode 转义 → SyntaxError，
    于是**代码根本不执行、stdout 永远为空**，所有依赖代码输出的判分全部退化成
    只看模型正文。修法：把 -c 脚本里 exec(open('...')) 内的反斜杠换成正斜杠
    （Windows 的 open() 也认），这样字符串里不再有转义序列。
    """
    if not isinstance(cmd, (list, tuple)) or not cmd:
        return cmd
    cmd = list(cmd)
    if str(cmd[0]) in ("python3", "python"):
        cmd[0] = sys.executable
    # -c 后面那一段脚本：只处理 exec(open(...)) 形式，避免误伤其它转义
    for idx, arg in enumerate(cmd):
        if not isinstance(arg, str) or "exec(open(" not in arg:
            continue
        cmd[idx] = arg.replace("\\", "/")
    return cmd


def _norm_kwargs(kwargs):
    """统一超时；并把子进程 stdio 改成"落文件 -> 再读回"。

    为什么不用 capture_output / PIPE：这台机器的沙箱**禁止匿名管道**
    （_winapi.CreatePipe 报 WinError 5 拒绝访问），PIPE 一开就炸。
    文件重定向不受限制，行为与 PIPE 等价（拿到 stdout/stderr 文本）。
    """
    if "timeout" in kwargs and kwargs["timeout"] is not None:
        kwargs["timeout"] = CODE_TIMEOUT

    want_capture = kwargs.pop("capture_output", False)
    stdout = kwargs.pop("stdout", None)
    stderr = kwargs.pop("stderr", None)
    text = kwargs.pop("text", None)
    encoding = kwargs.pop("encoding", None)
    errors = kwargs.pop("errors", None)
    if text is None:
        text = bool(kwargs.pop("universal_newlines", False))

    if want_capture:
        stdout = stderr = _OrigPipe
    wrap = isinstance(stdout, _PipeMarker) or isinstance(stderr, _PipeMarker)
    if not wrap:
        return kwargs, False, text, encoding, errors

    tmpdir = os.path.join(HERE, "logs", "_stdio")
    os.makedirs(tmpdir, exist_ok=True)
    tag = f"{os.getpid()}_{time.time_ns()}"
    if isinstance(stdout, _PipeMarker):
        kwargs["stdout"] = open(os.path.join(tmpdir, f"o_{tag}.txt"), "w+", encoding="utf-8")
    if isinstance(stderr, _PipeMarker):
        kwargs["stderr"] = open(os.path.join(tmpdir, f"e_{tag}.txt"), "w+", encoding="utf-8")
    return kwargs, True, text, encoding, errors


class _PipeMarker:
    pass


_OrigPipe = _PipeMarker()


def _wrap_result(rc, _, text, encoding, errors):
    """把文件里的输出读回来，拼成和 PIPE 一样的结果对象。"""
    if text is None:
        text = True

    def _read(f):
        if f is None:
            return b""
        f.flush()
        f.seek(0)
        data = f.read()
        f.close()
        try:
            os.unlink(f.name)
        except OSError:
            pass
        return data

    out = _read(_.get("_out_file"))
    err = _read(_.get("_err_file"))
    if text:
        out = out.decode(encoding or "utf-8", errors or "replace") if isinstance(out, bytes) else out
        err = err.decode(encoding or "utf-8", errors or "replace") if isinstance(err, bytes) else err
    return rc, out, err


def _patched_run(cmd, *args, **kwargs):
    cmd = _fix_cmd(cmd)
    kwargs, wrapped, text, encoding, errors = _norm_kwargs(kwargs)
    if not wrapped:
        return _orig_run(cmd, *args, **kwargs)

    timeout = kwargs.pop("timeout", None)      # Popen 不收 timeout，留给 wait()
    p = _orig_Popen(cmd, *args, **kwargs)
    out_file, err_file = kwargs.get("stdout"), kwargs.get("stderr")
    try:
        p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
        raise
    _, out, err = _wrap_result(p.returncode, {"_out_file": out_file, "_err_file": err_file},
                               text, encoding, errors)
    return subprocess.CompletedProcess(cmd, p.returncode, out, err)


class _PatchedPopen(_orig_Popen):
    def __init__(self, cmd, *args, **kwargs):
        super().__init__(_fix_cmd(cmd), *args, **kwargs)


subprocess.run = _patched_run
subprocess.Popen = _PatchedPopen

# ------------------------------------------- 1b. 把模型名塞进各 runner 的 API 白名单
# 原仓库每个 runner 都这么写：
#     if model_name in ['o1', ..., 'claude-3-haiku-20240307']:
#         response = GPT_response(...)     # 走 API
#     else:
#         response = run_response(...)     # 走本地 HF 权重
# deepseek-flash 不在列表里 → 掉进 HF 分支 → NameError: run_response。
# 做法：import 期间临时改写内置 open，让 benchmark/ 下的 .py 被读取时
#       白名单自动多出 DS_ALIASES。**磁盘文件一个字节都不改。**
_WHITELIST_RE = re.compile(
    r"(model_name\s+in\s+\[[^\]]*?['\"])"      # 白名单本体，跨行也算
    r"(\s*\])")
_orig_builtin_open = builtins.open
_EXTRA_NAMES = "".join(f", '{n}'" for n in sorted(DS_ALIASES))


def _whitelist_inject_source(path, src):
    """把 DS_ALIASES 追加进 model_name 白名单。只处理 benchmark/ 下的 .py。"""
    if not path.endswith(".py") or os.path.dirname(path) != os.path.join(REPO, "benchmark"):
        return src
    return _WHITELIST_RE.sub(lambda m: m.group(1) + _EXTRA_NAMES + m.group(2), src)


def _patched_builtin_open(file, *args, **kwargs):
    mode = args[0] if args else kwargs.get("mode", "r")
    if mode not in ("r", "rt"):
        return _orig_builtin_open(file, *args, **kwargs)
    try:
        src = _orig_builtin_open(file, *args, **kwargs).read()
    except Exception:
        return _orig_builtin_open(file, *args, **kwargs)
    import io
    return io.StringIO(_whitelist_inject_source(os.path.abspath(str(file)), src))


builtins.open = _patched_builtin_open

# ---------------------------------------------------------------- 2. patch GPT_response：接 DeepSeek，支持思考三组
import generation_models as GM   # noqa: E402  必须在 subprocess patch 之后 import

builtins.open = _orig_builtin_open     # 白名单注入只在 import 期间生效

_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        key = os.getenv("DEEPSEEK_API_KEY")
        if not key:
            raise SystemExit("缺少环境变量 DEEPSEEK_API_KEY")
        _client = OpenAI(api_key=key, base_url=DS_BASE_URL)
    return _client


def ds_chat(messages, model=None, temperature=0.0, max_tokens=2000, tag=""):
    """统一的 DeepSeek 调用入口。返回最终文本（按 THINK_MODE 处理思考内容）。"""
    model = model or DS_MODEL
    # 判分始终关思考：三组实验里裁判必须完全一致，否则"分数变化"说不清
    # 是主模型变了还是裁判变了
    think = "off" if str(tag).startswith("judge") else THINK_MODE
    if think != "off":
        # 思考 token 也算预算：给太少会让正文被挤空（out=0，判分必然错），
        # 给太多（8000）模型会一路写到上限，单次 70s+，正文依旧是碎片。
        # 折中取 REPRO_THINK_TOKENS（默认 2500），三组实验里保持同一数值。
        think_tokens = int(os.environ.get("REPRO_THINK_TOKENS", "2500"))
        max_tokens = max(max_tokens, think_tokens)
    kwargs = dict(model=model, messages=messages, max_tokens=max_tokens)
    extra = {}
    if think == "off":
        # 官方文档：关闭思考
        extra["thinking"] = {"type": "disabled"}
        kwargs["temperature"] = temperature
    else:
        # 官方文档：开启思考时 temperature 会被忽略（会报警但不生效）
        extra["thinking"] = {"type": "enabled"}
    kwargs["extra_body"] = extra

    t0 = time.time()
    resp = _get_client().chat.completions.create(**kwargs)
    msg = resp.choices[0].message
    content = msg.content or ""
    reasoning = getattr(msg, "reasoning_content", None) or ""

    if think == "on" and reasoning:
        # 组 C：把思考内容拼回正文（模拟"保留思考过程"）
        content = reasoning + "\n\n" + content

    log_line(REPRO_LOG, {
        "tag": tag, "model": model, "think_mode": think,
        "in_chars": sum(len(m.get("content") or "") for m in messages),
        "out_chars": len(content), "reasoning_chars": len(reasoning),
        "latency_s": round(time.time() - t0, 2),
        "usage": getattr(resp, "usage", None).model_dump() if getattr(resp, "usage", None) else None,
    })
    return content


def _patched_GPT_response_once(system_message, question, model_name, code_interpreter,
                               user_prompt_list, response_total_list, logprobs,
                               max_tokens_num, temperature):
    if model_name not in DS_ALIASES:
        raise ValueError(f"env_win 只接管 DeepSeek，收到 {model_name!r}")
    if code_interpreter:
        raise NotImplementedError("DeepSeek 无 Code Interpreter，code_interpreter 方法已弃用")

    # 复用原仓库的消息构造，保证 prompt 语义完全一致
    messages = GM.message_construct_func(user_prompt_list, response_total_list,
                                         system_message, "DeepSeek-R1")
    text = ds_chat(messages, model=DS_MODEL, temperature=temperature,
                   max_tokens=max_tokens_num, tag="main")
    if logprobs:
        raise NotImplementedError("DeepSeek 不支持 logprobs，本复现不使用")
    return text


def _patched_new_GPT_response(system_message, question, model_name, code_interpreter,
                              user_prompt_list, response_total_list, logprobs,
                              max_tokens_num=2000, temperature=0.0):
    # 判分器专属入口：任何不属于 DS_ALIASES 的模型名都当成"裁判"
    if model_name not in DS_ALIASES:
        return judge_via_gm(system_message, question, user_prompt_list, response_total_list,
                            max_tokens_num)
    last_err = None
    for i in range(6):
        try:
            # 注意：用模块级函数名而不是闭包里的 _patched_GPT_response_once，
            # 保证运行时能拿到最新实现；日志统一由它内部的 ds_chat(tag="main") 写。
            return globals()["_patched_GPT_response_once"](
                system_message, question, model_name, code_interpreter,
                user_prompt_list, response_total_list, logprobs,
                max_tokens_num, temperature)
        except Exception as e:      # 原版重试 25 次、每次只 sleep 1s，网络抖动时很浪费
            last_err = e
            print(f"[env_win] DeepSeek 调用失败({i+1}/6): {type(e).__name__}: {e}")
            time.sleep(min(60, 2 ** i))
    raise RuntimeError(f"DeepSeek 调用连续失败: {last_err}")


def judge_via_gm(system_message, question, user_prompt_list, response_total_list, max_tokens):
    """跑分/裁判调用：统一走 DS_JUDGE_MODEL。

    原仓库判分器写死 `GPT_response(..., model_name='gpt-4o', ...)`，
    在国产模型复现里必须换成同一个 DeepSeek 模型，否则会去调 OpenAI。
    """
    messages = GM.message_construct_func(user_prompt_list or [question],
                                         response_total_list or [],
                                         system_message, "DeepSeek-R1")
    return ds_chat(messages, model=DS_JUDGE_MODEL, temperature=0.0,
                   max_tokens=max_tokens, tag="judge")


GM.GPT_response = _patched_new_GPT_response
GM.GPT_response_once = _patched_GPT_response_once


def judge(prompt, temperature=0.0, max_tokens=800):
    """裁判专用：走 DS_JUDGE_MODEL，稳定 temperature，便于复现。"""
    return ds_chat([{"role": "user", "content": prompt}],
                   model=DS_JUDGE_MODEL, temperature=temperature,
                   max_tokens=max_tokens, tag="judge")


# ---------------------------------------------------------------- 3. patch 各 runner 里硬编码的 gpt-4o 裁判
# 这些函数被 runner import 到自己的命名空间，所以要按模块逐个替换
_JUDGE_NAMES = ("extract_equation_with_GPT4", "extract_equation_with_GPT4_game24",
                "extract_equation_with_GPT4_logical_equation")


def patch_judge(module, names=_JUDGE_NAMES):
    """把模块里所有 *with_GPT4* 判分函数换成 DeepSeek 版。

    做法：找到模块里的函数对象，用闭包包一层：
    重新定义时把内部调用 GPT_response(..., model_name='gpt-4o') 的 model 参数改掉。
    为避免解析源码，这里直接替换一个带签名兼容的 wrapper —— wrapper 内部
    用 inspect 拿到原函数的源码太脆，改用更简单的方式：把模块全局的
    GPT_response 指向一个"强制走裁判模型"的版本。
    """
    orig = getattr(module, "GPT_response", None)
    if orig is None:
        return False

    def forced_judge(system_message, question, model_name=None, code_interpreter=False,
                     user_prompt_list=None, response_total_list=None, logprobs=False,
                     max_tokens_num=2000, temperature=0.0):
        # 原始调用点传的是 model_name='gpt-4o'；这里一律改成裁判模型
        return ds_chat(
            GM.message_construct_func(user_prompt_list or [question],
                                      response_total_list or [],
                                      system_message, "DeepSeek-R1"),
            model=DS_JUDGE_MODEL, temperature=0.0,
            max_tokens=max_tokens_num, tag="judge")

    module.GPT_response = forced_judge
    return True


# ---------------------------------------------------------------- 4. 自检
def selfcheck():
    print("=" * 60)
    print(f"python      : {sys.version.split()[0]}")
    print(f"DS_MODEL    : {DS_MODEL}")
    print(f"DS_JUDGE    : {DS_JUDGE_MODEL}")
    print(f"THINK_MODE  : {THINK_MODE}")
    print(f"CODE_TIMEOUT: {CODE_TIMEOUT}s")
    print(f"python3 路由: {_fix_cmd(['python3', '-c', 'print(1)'])[0]}")
    print("=" * 60)


if __name__ == "__main__":
    selfcheck()
    if os.getenv("DEEPSEEK_API_KEY"):
        print(ds_chat([{"role": "user", "content": "只回复：通达"}], max_tokens=20, tag="selfcheck"))
    else:
        print("未设置 DEEPSEEK_API_KEY，跳过联网自检")
