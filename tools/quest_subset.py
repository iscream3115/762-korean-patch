"""Write a filtered kor_quest.txt into the game folder for bisecting script problems.

usage: python quest_subset.py exclude <NNN,...>   drop literals that come from these bsq batches
       python quest_subset.py only <NNN,...>      keep only literals from these batches
       python quest_subset.py lines <NNN>:<a>-<b> keep everything except lines a..b of batch NNN
"""
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GAME = r"C:\Program Files (x86)\Steam\steamapps\common\7.62"


def batch_en(num, lo=None, hi=None):
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "trans", "src", "bsq", num + ".jsonl"), encoding="utf-8")]
    if lo is not None:
        rows = rows[lo - 1:hi]
    return {r["en"] for r in rows}


def main():
    mode, arg = sys.argv[1], sys.argv[2]
    lines = open(os.path.join(ROOT, "build", "kor_quest.txt"), encoding="utf-8").read().splitlines()
    if mode == "onlylines":
        num, rng = arg.split(":")
        a, b = map(int, rng.split("-"))
        sel = batch_en(num, a, b)
        keep = [l for l in lines if l.split("\t", 1)[0] in sel]
    elif mode == "lines":
        num, rng = arg.split(":")
        a, b = map(int, rng.split("-"))
        drop = batch_en(num, a, b)
        keep = [l for l in lines if l.split("\t", 1)[0] not in drop]
    else:
        sel = set()
        for n in arg.split(","):
            sel |= batch_en(n)
        if mode == "exclude":
            keep = [l for l in lines if l.split("\t", 1)[0] not in sel]
        else:
            keep = [l for l in lines if l.split("\t", 1)[0] in sel]
    with open(os.path.join(GAME, "kor_quest.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(keep) + "\n")
    print("kept %d of %d" % (len(keep), len(lines)))


if __name__ == "__main__":
    main()
