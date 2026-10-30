"""Scan compiled quest files (.gen/.cht/.pht/.rht) for inline string literals.

Literal = 0x23 0x00, u16 len (incl. NUL), len-1 bytes xcrypt(0x82549171), 0x00.
usage: python quest_strings.py <file> [...]   -> TSV: file, offset, len, text(cp1252, escaped)
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import azp  # noqa: E402

QKEY = 0x82549171
PAT = re.compile(rb"#\x00", re.S)


def scan(data):
    out = []
    for m in PAT.finditer(data):
        o = m.start()
        if o + 4 > len(data):
            continue
        (n,) = struct.unpack_from("<H", data, o + 2)
        # the terminator slot is not reliably 0 (.gen); the loader overwrites it
        if n < 2 or o + 4 + n > len(data):
            continue
        t = azp.xcrypt(data[o + 4:o + 4 + n - 1], QKEY)
        if any(c < 0x20 and c not in (9, 10, 13) for c in t):
            continue
        out.append((o, n, t))
    return out


def esc(b):
    return b.decode("cp1252", "replace").replace("\\", "\\\\").replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    for f in sys.argv[1:]:
        for o, n, t in scan(open(f, "rb").read()):
            print("%s\t%d\t%d\t%s" % (os.path.basename(f), o, n, esc(t)))
