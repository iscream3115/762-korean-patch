"""Convert a raw translation draft into a ko batch.

Draft: trans/raw/<source>/<NNN>.txt, one entry per line:  <id>|<translation>
(<id> is the part after "<source>:" in the key; for bsq it is the 1-based line
number in the source batch). Lines starting with # are ignored.
usage: python raw2jsonl.py <source> <NNN>
"""
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "trans"))


def fix_edges(en, ko):
    """Editors drop trailing spaces, so copy the English edge whitespace onto the Korean."""
    core = ko.strip(" ")
    lead = en[:len(en) - len(en.lstrip(" "))]
    trail = en[len(en.rstrip(" ")):]
    return lead + core + trail if core else ko


def main():
    src, num = sys.argv[1], sys.argv[2]
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "src", src, num + ".jsonl"), encoding="utf-8")]
    keys = [r["k"] for r in rows]
    en_of = {r["k"]: r["en"] for r in rows}
    idx = {k.split(":", 1)[1]: k for k in keys}
    out, seen = [], set()
    for n, ln in enumerate(open(os.path.join(ROOT, "raw", src, num + ".txt"), encoding="utf-8")):
        ln = ln.rstrip("\n")
        if not ln.strip() or ln.startswith("#"):
            continue
        i, _, ko = ln.partition("|")
        i = i.strip()
        if src in ("bsq", "item", "subs", "actor", "sector", "tips"):   # id = 1-based line number
            k = keys[int(i) - 1] if i.isdigit() and 1 <= int(i) <= len(keys) else None
        else:
            k = idx.get(i)
        if not k:
            sys.exit("line %d: unknown id %r" % (n + 1, i))
        seen.add(k)
        out.append({"k": k, "ko": fix_edges(en_of[k], ko)})
    missing = [k for k in keys if k not in seen]
    d = os.path.join(ROOT, "ko", src)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, num + ".jsonl"), "w", encoding="utf-8") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print("%s/%s: %d entries, %d missing %s" % (src, num, len(out), len(missing), missing[:5]))


if __name__ == "__main__":
    main()
