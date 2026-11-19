"""核对每个方法到底发了什么 prompt、拿回什么，确认分支真的生效。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE = os.path.join(HERE, "results", "smoke", "save_input")


def check(task_dir):
    d = os.path.join(SAVE, task_dir)
    print("=" * 74)
    print("##", task_dir)
    if not os.path.isdir(d):
        print("  目录不存在")
        return
    n = 0
    for root, _dirs, files in os.walk(d):
        if "conversation_data.json" not in files:
            continue
        p = os.path.join(root, "conversation_data.json")
        with open(p, encoding="utf-8") as fh:
            cd = json.load(fh)
        msgs = cd.get("user_prompt_list") or []
        first = msgs[0] if msgs else ""
        rel = os.path.relpath(root, d)
        print(f"  [{rel}]")
        print(f"    prompt 首 110 字: {first[:110]!r}")
        markers = {
            "Agent_1": "Agent_1" in first,
            "Agent_2": "Agent_2" in first,
            "代码格式": ("```python" in first) or ("code" in first.lower()),
        }
        print(f"    标记: {markers}")
        print(f"    回答首 110 字: {(cd.get('response_list') or [''])[-1][:110]!r}")
        files_here = sorted(files)
        print(f"    产物: {files_here}")
        n += 1
        if n >= 2:
            break


if __name__ == "__main__":
    for t in sys.argv[1:]:
        check(t)
