"""
fetch_corpus.py —— 抓句子级字母统计任务的语料，存在本地

为什么固定存本地：抓一次、存死，之后跑多少次都用同一份语料，
别人复现时也不依赖网站在线（Project Gutenberg 今天就 503 了）。

用法：
    python fetch_corpus.py
"""
import os
import re
import html
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(DATA, "raw_corpus.txt")

# 公版书 / 公版剧本，纯英文，无版权顾虑
SOURCES = [
    ("Alice's Adventures in Wonderland (Gutenberg Australia)",
     "https://gutenberg.net.au/ebooks01/0100021h.html"),
    ("Hamlet (MIT Shakespeare)",
     "https://shakespeare.mit.edu/hamlet/full.html"),
]


def clean_html(raw):
    # 去掉 script/style
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    # 段落标签转换成句界，避免整段粘成一句
    raw = re.sub(r"(?i)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?i)</(p|div|h\d|li|tr|blockquote)>", "\n", raw)
    # 去剩余标签
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = raw.replace("\r", "\n")

    # 按行处理，丢掉目录/页眉这类"不像句子"的行
    kept = []
    for line in raw.split("\n"):
        line = " ".join(line.split())
        if len(line) < 40:          # 页码、标题、空行
            continue
        if line.lower().count("gutenberg") or "contents" in line.lower():
            continue
        if sum(c.isdigit() for c in line) > len(line) * 0.2:   # 目录页码行
            continue
        kept.append(line)
    return "\n".join(kept)


def main():
    os.makedirs(DATA, exist_ok=True)
    chunks = []
    for name, url in SOURCES:
        print(f"抓取 {name} ...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        except Exception as e:
            print(f"  !! 失败: {e}")
            continue
        text = clean_html(raw)
        print(f"  得到 {len(text)} 字符")
        chunks.append(f"##### SOURCE: {name}\n{text}\n")

    if not chunks:
        raise SystemExit("没有抓到任何语料，检查网络")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(chunks))
    print(f"\n已保存 -> {OUT}  ({os.path.getsize(OUT)} bytes)")


if __name__ == "__main__":
    main()
