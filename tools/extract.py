"""Extract every translatable string into translation batches.

Output: trans/src/<source>/<NNN>.jsonl  lines {"k": key, "en": text}
Sources (priority order = translation order):
  local   LOCAL.TXT                      key local:<id>
  e6q     Quests\\E1P\\e6q.txt (main)      key e6q:<id>
  bsq     Blue Sun quest literals        key bsq:<sha1(en)[:12]>
  tips    TIPS.TXT                       key tips:<n>
  subs    INI\\SUBTITLES.INI              key subs:<wav>
  actor   ACTORSINI Biography/hint       key actor:<file>:<field>
  sector  WORLDINI sector Desc           key sector:<file>:desc
  item    ITEMINFO RealName/description  key item:<ITEM>:name|desc

Duplicate English strings are emitted once (first source wins); the builder
reuses the translation for every key with the same English (trans/keys.json).
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import azp  # noqa: E402
import quest_strings  # noqa: E402
from vfs import GAME, VFS  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "trans")
BATCH = {"local": 250, "e6q": 120, "bsq": 120, "tips": 200, "subs": 200, "actor": 150, "sector": 200, "item": 80}

import codecs
codecs.register_error("keepbyte", lambda e: ("".join(chr(b) for b in e.object[e.start:e.end]), e.end))


def dec(b):
    return b.decode("cp1252", "keepbyte")


ID_LINE = re.compile(rb'^(\d+)(\s+)"(.*)"\s*$')


def id_text(raw):
    """ID "text" files -> list of (id, text)."""
    out = []
    for ln in raw.split(b"\n"):
        m = ID_LINE.match(ln.rstrip(b"\r"))
        if m:
            out.append((int(m.group(1)), m.group(3).decode("cp1252", "keepbyte")))
    return out


def data_identifiers(v):
    """Every quoted string in data files: possible keys a quest literal may refer to."""
    """Strings the engine uses as keys: item/addon/ammo/clip names, inventory
    entries, actor Name/Room/Actor, sector Name/Pack. Display-only text
    (subtitles, biographies, descriptions, RealName) is deliberately excluded."""
    ids = set()
    rx = re.compile(rb'"([^"\r\n]{1,120})"')
    keyfiles = v.names(r"^INI\\ITEMS\\|\.(INV|PLACES|ATT)$")
    for n in keyfiles:
        data = v.read(n)
        if n.endswith("ITEMINFO"):
            data = b"\n".join(l for l in data.split(b"\n") if l.lstrip().upper().startswith(b"ITEM"))
        for m in rx.finditer(data):
            ids.add(m.group(1).decode("cp1252", "keepbyte"))
    fld = re.compile(rb'^\s*(Name|Room|Actor|FromFile|Pack|CAR)\s+(.*)$', re.M)
    for n in v.names(r"^(ACTORSINI|WORLDINI)\\.*\.INI$|^INI\\CARS\.INI$"):
        for m in fld.finditer(v.read(n)):
            for q in rx.finditer(m.group(2)):
                ids.add(q.group(1).decode("cp1252", "keepbyte"))
    return ids


def is_dialogue(s, ids):
    t = s.strip()
    if len(t) < 2 or not re.search(r"[A-Za-z]", t):
        return False
    if s in ids or t in ids:
        return False
    if re.search(r"\\|/|\.(wav|ini|act|e5b|e6b|tga|dds|jpg|ogg|txt)\b", t, re.I):
        return False
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\s*=\s*", t) or re.search(r"[a-z][A-Z].*=", t):
        return False            # debug "Var=" output
    if " " in t:
        return True
    # single word: display fragment if padded, punctuated or line-broken
    return s != t or "^" in s or t[-1] in ".!?:,"


def main():
    v = VFS()
    units = {}     # source -> list of (key, en)
    keys = {}      # key -> en  (all keys incl. duplicates)
    seen = set()

    def add(src, key, en):
        if en is None or not en.strip():
            return
        keys[key] = en
        if en in seen:
            return
        seen.add(en)
        units.setdefault(src, []).append((key, en))

    # UI
    loc = azp.xcrypt(v.read("LOCAL.TXT"))
    for i, t in id_text(loc):
        add("local", "local:%d" % i, t)

    # main quest text
    e6q = azp.xcrypt(open(os.path.join(GAME, r"Quests\E1P\e6q.txt"), "rb").read())
    for i, t in id_text(e6q):
        add("e6q", "e6q:%d" % i, t)

    # Blue Sun quest literals, in script order
    ids = data_identifiers(v)
    skipped = []
    for ext in ("gen", "cht", "pht", "rht"):
        p = os.path.join(GAME, r"Quests\RAS\BlueSun.%s" % ext)
        for o, n, raw in quest_strings.scan(open(p, "rb").read()):
            s = raw.decode("cp1252", "keepbyte")
            if is_dialogue(s, ids):
                add("bsq", "bsq:" + hashlib.sha1(raw).hexdigest()[:12], s)
            else:
                skipped.append(s)

    # tips
    tips = v.read("TIPS.TXT").decode("cp1252", "keepbyte")
    for n, m in enumerate(re.finditer(r'^\s*\d+\s+"(.*)"', tips, re.M)):
        add("tips", "tips:%d" % n, m.group(1))

    # subtitles
    sub = v.read(r"INI\SUBTITLES.INI").decode("cp1252", "keepbyte")
    for m in re.finditer(r'^"([^"]*)"\s+"([^"]*)"', sub, re.M):
        add("subs", "subs:" + m.group(1), m.group(2))

    # actors
    for n in v.names(r"^ACTORSINI\\.*\.INI$"):
        t = v.read(n).decode("cp1252", "keepbyte")
        for fld in ("Biography", "Default_Hint_Name"):
            m = re.search(r'^%s\s+"(.*?)"' % fld, t, re.M)
            if m:
                add("actor", "actor:%s:%s" % (n, fld), m.group(1))

    # sectors
    for n in v.names(r"^WORLDINI\\SECTORS\\[^\\]*\.INI$"):
        t = v.read(n).decode("cp1252", "keepbyte")
        m = re.search(r'^Desc\s+"(.*?)"', t, re.M)
        if m:
            add("sector", "sector:%s:desc" % n, m.group(1))

    # items
    it = v.read(r"INI\ITEMS\ITEMINFO").decode("cp1252", "keepbyte")
    for m in re.finditer(r'^ITEM\s+"([^"]*)"[^\n]*\n(.*?)^END', it, re.S | re.M):
        key, body = m.group(1), m.group(2)
        rn = re.search(r'^\s*RealName\s+"([^"]*)"', body, re.M)
        if rn:
            add("item", "item:%s:name" % key, rn.group(1))
            desc = body[rn.end():]
        else:
            desc = body
        desc = "\n".join(l.strip() for l in desc.strip().splitlines()).strip()
        add("item", "item:%s:desc" % key, desc)

    os.makedirs(OUT, exist_ok=True)
    for src, lst in units.items():
        d = os.path.join(OUT, "src", src)
        os.makedirs(d, exist_ok=True)
        size = BATCH[src]
        for b in range(0, len(lst), size):
            with open(os.path.join(d, "%03d.jsonl" % (b // size)), "w", encoding="utf-8") as f:
                for k, en in lst[b:b + size]:
                    f.write(json.dumps({"k": k, "en": en}, ensure_ascii=False) + "\n")
        print("%-7s units %5d  chars %8d  batches %d" % (src, len(lst), sum(len(e) for _, e in lst), (len(lst) + size - 1) // size))
    json.dump(keys, open(os.path.join(OUT, "keys.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    with open(os.path.join(OUT, "bsq_skipped.txt"), "w", encoding="utf-8") as f:
        for s in sorted(set(skipped)):
            f.write(s.replace("\n", "\\n") + "\n")
    print("keys", len(keys), "bsq skipped (unique)", len(set(skipped)))


if __name__ == "__main__":
    main()
