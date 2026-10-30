"""Show only the lines of an item batch that item_auto.py cannot translate.
usage: item_todo.py <NNN>"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import item_auto  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
num = sys.argv[1]
for n, l in enumerate(open(os.path.join(item_auto.ROOT, "src", "item", num + ".jsonl"), encoding="utf-8"), 1):
    en = json.loads(l)["en"]
    if not item_auto.auto(en):
        print("%d|%s" % (n, en.replace("\n", "\\n")))
