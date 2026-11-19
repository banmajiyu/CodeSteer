"""看一眼某个任务的样本：问题、模型回答、抽出来的答案、真值。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE = os.path.join(HERE, "results", "smoke", "save_input")


def dump(task_dir, limit=1500):
    d = os.path.join(SAVE, task_dir)
    if not os.path.isdir(d):
        print(f"  目录不存在: {d}")
        return
    for root, _dirs, files in os.walk(d):
        for f in sorted(files):
            p = os.path.join(root, f)
            rel = os.path.relpath(p, d)
            print("-" * 70)
            print(f"  {rel}  ({os.path.getsize(p)} bytes)")
            if f.endswith(".json"):
                try:
                    with open(p, encoding="utf-8") as fh:
                        data = json.load(fh)
                    txt = json.dumps(data, ensure_ascii=False, indent=1)
                except Exception as e:
                    txt = f"<读不了: {e}>"
            elif f.endswith((".txt", ".py")):
                with open(p, encoding="utf-8", errors="replace") as fh:
                    txt = fh.read()
            else:
                continue
            print(txt[:limit])


if __name__ == "__main__":
    for t in sys.argv[1:]:
        print("=" * 74)
        print("##", t)
        dump(t, int(os.environ.get("DUMP_LIMIT", "1200")))
