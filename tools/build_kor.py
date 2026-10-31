"""Build the Korean patch from trans/ko/*.

Outputs (build/):
  Korean.azp        LOCAL.TXT (+ ITEMINFO, sector INI, ... as translations exist)
  e6q.txt           encrypted Quests\\E1P\\e6q.txt replacement (installed next to the original)
  kor_strings.txt   display-time substitutions (key-binding names etc.)
  kor_quest.txt     Blue Sun quest literal table (English<TAB>Korean, CP949 at load by the DLL)
  report.txt        validation problems

Rules checked per string: format specifiers, ^ count, leading/trailing spaces,
no '"', no tab, all Korean in KS X 1001 (EUC-KR) range.
"""
import codecs
import glob
import json
import os
import re
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import azp  # noqa: E402
from vfs import GAME, VFS  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TR = os.path.join(ROOT, "trans")
OUT = os.path.join(ROOT, "build")

codecs.register_error("keepbyte", lambda e: ("".join(chr(b) for b in e.object[e.start:e.end]), e.end))
FMT = re.compile(r"%[-+#0]*\d*(?:\.\d+)?[hlL]?[sdifuxXcgeE%]")
problems = []


def enc_game(s):
    """Unicode -> game bytes: CP949 for Korean, cp1252 for the rest."""
    out = bytearray()
    for ch in s:
        try:
            out += ch.encode("cp1252")
            continue
        except UnicodeEncodeError:
            pass
        if ord(ch) < 0x100:
            out.append(ord(ch))          # byte preserved by keepbyte decoding
            continue
        b = ch.encode("cp949", "replace")
        if len(b) != 2 or not (0xA1 <= b[0] <= 0xFE and 0xA1 <= b[1] <= 0xFE):
            raise ValueError("not KS X 1001: %r" % ch)
        out += b
    return bytes(out)


def check(key, en, ko):
    errs = []
    if sorted(FMT.findall(en)) != sorted(FMT.findall(ko)):
        errs.append("format %s vs %s" % (FMT.findall(en), FMT.findall(ko)))
    if en.count("^") != ko.count("^"):
        errs.append("^ count %d vs %d" % (en.count("^"), ko.count("^")))
    if (en[:1] == " ") != (ko[:1] == " ") or (en[-1:] == " ") != (ko[-1:] == " "):
        errs.append("edge spaces")
    if '"' in ko or "\t" in ko:
        errs.append("quote/tab")
    try:
        enc_game(ko)
    except ValueError as e:
        errs.append(str(e))
    for e in errs:
        problems.append("%s: %s | EN=%r KO=%r" % (key, e, en[:80], ko[:80]))
    return not any(e.startswith("not KS") or e == "quote/tab" for e in errs)


def load():
    keys = json.load(open(os.path.join(TR, "keys.json"), encoding="utf-8"))
    tm = {}                                 # english -> korean
    for f in sorted(glob.glob(os.path.join(TR, "ko", "*", "*.jsonl"))):
        src = os.path.join(TR, "src", os.path.relpath(f, os.path.join(TR, "ko")))
        en_of = {}
        for ln in open(src, encoding="utf-8"):
            d = json.loads(ln)
            en_of[d["k"]] = d["en"]
        for n, ln in enumerate(open(f, encoding="utf-8")):
            if not ln.strip():
                continue
            try:
                d = json.loads(ln)
            except json.JSONDecodeError as e:
                problems.append("%s:%d bad json %s" % (f, n + 1, e))
                continue
            en = en_of.get(d["k"])
            if en is None:
                problems.append("%s: unknown key %s" % (f, d["k"]))
                continue
            if check(d["k"], en, d["ko"]):
                tm[en] = d["ko"]
    return keys, tm


def id_file(raw, prefix, keys, tm, exclude=()):
    """Replace "text" of `ID "text"` lines that have a translation."""
    out, n = [], 0
    for ln in raw.split(b"\r\n"):
        m = re.match(rb'^(\d+)(\s+)"(.*)"(\s*)$', ln)
        if m:
            k = "%s:%d" % (prefix, int(m.group(1)))
            en = keys.get(k)
            if en is not None and en in tm and en not in exclude:
                ln = m.group(1) + m.group(2) + b'"' + enc_game(tm[en]) + b'"' + m.group(4)
                n += 1
        out.append(ln)
    return b"\r\n".join(out), n


def requote(raw, pattern, key_of, keys, tm):
    """Replace the quoted value matched by `pattern` (group 'v') when the key
    built by key_of(match) has a translation. Works on bytes so everything else
    stays byte-identical."""
    n = 0

    def rep(m):
        nonlocal n
        en = keys.get(key_of(m))
        if en is None or en not in tm or m.group("v").decode("cp1252", "keepbyte") != en:
            return m.group(0)
        n += 1
        s, e = m.span("v")
        return m.group(0)[:s - m.start()] + enc_game(tm[en]) + m.group(0)[e - m.start():]

    return re.sub(pattern, rep, raw, flags=re.M), n


def data_files(v, keys, tm, files):
    """TIPS.TXT, SUBTITLES.INI, actor and sector INIs with translated strings."""
    tips = v.read("TIPS.TXT")
    idx = iter(range(10 ** 6))
    out, n = requote(tips, rb'^\s*\d+\s+"(?P<v>.*)"', lambda m: "tips:%d" % next(idx), keys, tm)
    if n:
        files.append(("TIPS.TXT", out))
    print("TIPS.TXT: %d" % n)

    sub = v.read(r"INI\SUBTITLES.INI")
    out, n = requote(sub, rb'^"(?P<k>[^"]*)"\s+"(?P<v>[^"]*)"',
                     lambda m: "subs:" + m.group("k").decode("cp1252", "keepbyte"), keys, tm)
    if n:
        files.append((r"INI\SUBTITLES.INI", out))
    print("SUBTITLES.INI: %d" % n)

    tot = cnt = 0
    for name in v.names(r"^ACTORSINI\\.*\.INI$"):
        raw = v.read(name)
        out, n = requote(raw, rb'^(?P<f>Biography|Default_Hint_Name)\s+"(?P<v>.*?)"',
                         lambda m, name=name: "actor:%s:%s" % (name, m.group("f").decode()), keys, tm)
        if n:
            files.append((name, out))
            tot += n
            cnt += 1
    print("actors: %d strings in %d files" % (tot, cnt))

    tot = cnt = 0
    for name in v.names(r"^WORLDINI\\SECTORS\\[^\\]*\.INI$"):
        raw = v.read(name)
        out, n = requote(raw, rb'^Desc\s+"(?P<v>.*?)"', lambda m, name=name: "sector:%s:desc" % name, keys, tm)
        if n:
            files.append((name, out))
            tot += n
            cnt += 1
    print("sectors: %d strings in %d files" % (tot, cnt))


def item_file(v, keys, tm, files):
    """INI\\ITEMS\\ITEMINFO: translate RealName and the description body.
    The ITEM "key" line is the engine's identifier and is never touched."""
    t = v.read(r"INI\ITEMS\ITEMINFO").decode("cp1252", "keepbyte")
    nn = nd = 0

    def rep(m):
        nonlocal nn, nd
        key, body = m.group(2), m.group(3)
        rn = re.search(r'^(\s*RealName\s+")([^"]*)("[^\r\n]*)', body, re.M)
        head, desc = (body[:rn.end()], body[rn.end():]) if rn else ("", body)
        en_d = "\n".join(l.strip() for l in desc.strip().splitlines()).strip()
        dk = "item:%s:desc" % key
        if rn:
            en_n = keys.get("item:%s:name" % key)
            if en_n is not None and en_n == rn.group(2) and en_n in tm:
                head = body[:rn.start(2)] + tm[en_n] + body[rn.end(2):rn.end()]
                nn += 1
        if en_d and keys.get(dk) == en_d and en_d in tm:
            desc = "\r\n" + "".join(l + "  \r\n" for l in tm[en_d].split("\n"))
            nd += 1
        return m.group(1) + head + desc

    out = re.sub(r'(^ITEM\s+"([^"]*)"[^\n]*\n)(.*?)(?=^END)', rep, t, flags=re.S | re.M)
    if nn or nd:
        files.append((r"INI\ITEMS\ITEMINFO", enc_game(out)))
    print("ITEMINFO: %d names, %d descriptions" % (nn, nd))

def main():
    os.makedirs(OUT, exist_ok=True)
    keys, tm = load()
    v = VFS()
    files = []

    # key binding names are stored in keys.cfg by their LOCAL text: keep English
    # in LOCAL.TXT and translate at display time instead.
    kc = open(os.path.join(GAME, "keys.cfg"), "rb").read().decode("cp1252", "keepbyte")
    keynames = set(re.findall(r'"([^"]*)"', kc))
    subst = {}

    loc = azp.xcrypt(v.read("LOCAL.TXT"))
    loc2, n = id_file(loc, "local", keys, tm, exclude=keynames)
    if len(loc2) >= 0x10000 - 1024:
        problems.append("LOCAL.TXT too large: %d" % len(loc2))
    files.append(("LOCAL.TXT", azp.xencrypt(loc2)))
    for k, en in keys.items():
        if k.startswith("local:") and en in keynames and en in tm:
            subst[en] = tm[en]
    print("LOCAL.TXT: %d translated, %d via display substitution" % (n, len(subst)))

    e6q_path = os.path.join(GAME, r"Quests\E1P\e6q.txt")
    e6q = azp.xcrypt(open(e6q_path, "rb").read())
    e6q2, n = id_file(e6q, "e6q", keys, tm)
    if n:
        open(os.path.join(OUT, "e6q.txt"), "wb").write(azp.xencrypt(e6q2))
    print("e6q.txt: %d translated" % n)

    # Blue Sun quest literals: table consumed by the DLL at quest load
    with open(os.path.join(OUT, "kor_quest.txt"), "w", encoding="utf-8", newline="\n") as f:
        m = 0
        for k, en in keys.items():
            if k.startswith("bsq:") and en in tm and en not in EVENT_LITERALS:
                f.write(esc(en) + "\t" + esc(tm[en]) + "\n")
                m += 1
    print("Blue Sun literals: %d" % m)

    data_files(v, keys, tm, files)
    item_file(v, keys, tm, files)
    open(os.path.join(OUT, "Korean.azp"), "wb").write(azp.build(files))
    with open(os.path.join(OUT, "kor_strings.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# generated by build_kor.py - original<TAB>translation (UTF-8)\n")
        for en, ko in sorted(subst.items()):
            f.write(esc(en) + "\t" + esc(ko) + "\n")
    with open(os.path.join(OUT, "report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(problems) + "\n")
    print("translations:", len(tm), "problems:", len(problems), "(build/report.txt)")


# Quest scripts build these into patterns such as 'Killed finally "<name>"' and
# 'Sector loading finished "<sector>"' and compare them with the engine's own
# English event messages. Translating them stops the triggers from firing
# (e.g. Evolution of Weapons enemies never turn hostile), so they stay English.
EVENT_LITERALS = {
    "Killed finally ", "Sector loading finished ", "Character ", " left sector",
    "Sector ", " unloading finished", " entered to sector",
}


def esc(s):
    return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")


if __name__ == "__main__":
    main()
