"""Print a source batch as id|english (UTF-8). usage: show.py <source> <NNN>"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "trans"))
src, num = sys.argv[1], sys.argv[2]
for n, l in enumerate(open(os.path.join(ROOT, "src", src, num + ".jsonl"), encoding="utf-8")):
    d = json.loads(l)
    i = d["k"].split(":", 1)[1] if src in ("local", "e6q") else str(n + 1)
    print(i + "|" + d["en"].replace("\n", "\\n"))
