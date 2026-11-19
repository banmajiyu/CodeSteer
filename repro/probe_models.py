"""
探测三家国产 API 的可用模型名。
用法：set 好环境变量后  python probe_models.py
需要的环境变量（有几个填几个，没有的会跳过）：
  DEEPSEEK_API_KEY
  DASHSCOPE_API_KEY   (阿里云百炼 Qwen)
  MOONSHOT_API_KEY    (Kimi)
"""
import os
import sys

try:
    from openai import OpenAI
except ImportError:
    sys.exit("请先安装 openai: pip install openai")

PROVIDERS = {
    "deepseek": {
        "env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
    },
    "qwen": {
        "env": "DASHSCOPE_API_KEY",
        # 老域名仍然可用；新域名需要 WorkspaceId
        "base_url": os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ),
    },
    "kimi": {
        "env": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
    },
}


def probe(name, conf):
    key = os.getenv(conf["env"])
    if not key:
        print(f"[{name}] 跳过：未设置 {conf['env']}")
        return
    client = OpenAI(api_key=key, base_url=conf["base_url"])
    print(f"\n=== {name}  ({conf['base_url']}) ===")
    try:
        models = client.models.list()
        for m in sorted({x.id for x in models.data}):
            print("  -", m)
    except Exception as e:
        print(f"  [!] models.list() 失败：{type(e).__name__}: {e}")
        print("  改用 chat 探针（猜名字）+ 看报错信息里的提示")


if __name__ == "__main__":
    print("Python:", sys.version.split()[0])
    for name, conf in PROVIDERS.items():
        probe(name, conf)
    print("\n把上面列出的模型名发给我（每个平台挑一个你想用的）。")
