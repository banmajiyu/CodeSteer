# -*- coding: utf-8 -*-
"""把纯 Python 的 mpmath 装进 repro/vendor（pip 在这台机器上不可用，只能手动解压 wheel）。"""
import io
import json
import os
import sys
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, "vendor")
os.makedirs(VENDOR, exist_ok=True)


def main():
    api = "https://pypi.org/pypi/mpmath/json"
    with urllib.request.urlopen(api, timeout=60) as r:
        meta = json.load(r)
    ver = meta["info"]["version"]
    whl = None
    for f in meta["releases"][ver]:
        if f["filename"].endswith("-py3-none-any.whl"):
            whl = f
            break
    if whl is None:
        print("没找到纯 Python wheel")
        return 1
    print("下载", whl["filename"])
    with urllib.request.urlopen(whl["url"], timeout=120) as r:
        data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(VENDOR)
    print("解压到", VENDOR)
    if VENDOR not in sys.path:
        sys.path.insert(0, VENDOR)
    import mpmath
    print("mpmath", mpmath.__version__, "->", mpmath.mp.dps)
    mpmath.mp.dps = 50
    print("sin(0.41293) =", mpmath.sin(mpmath.mpf("0.41293")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
