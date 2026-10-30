"""Walk the zlib streams of an AZP pack (no directory needed) and dump them.

usage: python scan_azp.py <pack.azp> <outdir>
Each stream is written as <outdir>/<offset_hex>.bin and listed in index.tsv.
"""
import os
import struct
import sys
import zlib


def walk(data):
    magic, data_start, ver, count = struct.unpack_from("<4sIII", data, 0)
    assert magic == b"AZP\x01", magic
    o = data_start
    while o < len(data):
        z = zlib.decompressobj()
        out = z.decompress(data[o:])
        if not z.eof:
            raise ValueError("truncated stream at %#x" % o)
        n = len(data) - o - len(z.unused_data)
        yield o, n, out
        o += n


def main():
    src, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    data = open(src, "rb").read()
    with open(os.path.join(outdir, "index.tsv"), "w", encoding="utf-8") as idx:
        for i, (o, n, out) in enumerate(walk(data)):
            with open(os.path.join(outdir, "%08x.bin" % o), "wb") as f:
                f.write(out)
            idx.write("%d\t%#x\t%d\t%d\t%r\n" % (i, o, n, len(out), out[:40]))
    print("streams:", i + 1)


if __name__ == "__main__":
    main()
