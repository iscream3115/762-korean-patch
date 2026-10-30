"""AZP pack tool for 7.62 High Calibre (E6 engine, "new-style package").

Format (from EB.exe 1.11 b286, loader 0x6904B0 / xcrypt 0x6AF9B0):
  header  : char[4] "AZP\\x01", u32 data_start, u32 unk(=6), u32 count
  dir     : data_start-16 bytes, encrypted with xcrypt(key=0xF69DA025)
            per entry: u32 name_len, name (no NUL), u32 a, u32 b, u32 c
  data    : zlib streams

usage:
  azp.py list  <pack.azp>
  azp.py x     <pack.azp> <outdir> [glob]
  azp.py pack  <srcdir> <out.azp>
"""
import fnmatch
import os
import struct
import sys
import zlib

KEY = 0xF69DA025


def xcrypt(buf, key=KEY):
    """Exact emulation of the x86 routine at 006af9b0 (symmetric? no: decrypt).

    Register model: eax/edx 32-bit, 16-bit mul on ax*dx -> dx:ax.
    """
    out = bytearray(buf)
    eax = (key >> 16) & 0xFFFF
    edx = key & 0xFFFF
    for i in range(len(out)):
        prod = (eax & 0xFFFF) * (edx & 0xFFFF)
        ax = (prod - 1) & 0xFFFF            # mul dx ; dec ax
        dx = (prod >> 16) & 0xFFFF
        eax = (eax & 0xFFFF0000) | ax
        edx = (edx & 0xFFFF0000) | dx
        eax ^= edx                          # xor eax, edx
        k = eax & 0xFF                      # edx = 0xff & eax
        eax = (eax & 0xFFFFFF00) | out[i]   # mov al, [edi]
        edx = k ^ eax                       # xor edx, eax
        out[i] = edx & 0xFF
    return bytes(out)


def xencrypt(plain, key=KEY):
    """Inverse of xcrypt: the keystream depends on the cipher byte (al)."""
    out = bytearray(len(plain))
    eax = (key >> 16) & 0xFFFF
    edx = key & 0xFFFF
    for i, p in enumerate(plain):
        prod = (eax & 0xFFFF) * (edx & 0xFFFF)
        ax = (prod - 1) & 0xFFFF
        dx = (prod >> 16) & 0xFFFF
        eax = (eax & 0xFFFF0000) | ax
        edx = (edx & 0xFFFF0000) | dx
        eax ^= edx
        k = eax & 0xFF
        c = p ^ k
        out[i] = c
        eax = (eax & 0xFFFFFF00) | c
        edx = k ^ eax
    return bytes(out)


def read_dir(data):
    magic, data_start, unk, count = struct.unpack_from("<4sIII", data, 0)
    if magic != b"AZP\x01":
        raise ValueError("not an AZP pack")
    d = xcrypt(data[16:data_start])
    entries = []
    p = 0
    for _ in range(count):
        (n,) = struct.unpack_from("<I", d, p)
        name = d[p + 4:p + 4 + n].decode("cp1251")
        a, b, c = struct.unpack_from("<III", d, p + 4 + n)
        entries.append((name, a, b, c))
        p += 16 + n
    return (data_start, unk, count), entries


def build(files, unk=6, level=6):
    """files: list of (name, bytes). Returns AZP pack bytes."""
    names = [n.replace("/", "\\").upper().encode("cp1251") for n, _ in files]
    blobs = [zlib.compress(b, level) for _, b in files]
    dir_len = sum(16 + len(n) for n in names)
    data_start = 16 + dir_len
    d = bytearray()
    off = data_start
    for n, (_, raw), z in zip(names, files, blobs):
        d += struct.pack("<I", len(n)) + n + struct.pack("<III", off, len(z), len(raw))
        off += len(z)
    out = bytearray(struct.pack("<4sIII", b"AZP\x01", data_start, unk, len(files)))
    out += xencrypt(bytes(d))
    for z in blobs:
        out += z
    return bytes(out)


def main():
    cmd = sys.argv[1]
    if cmd == "list":
        data = open(sys.argv[2], "rb").read()
        hdr, ents = read_dir(data)
        print("data_start=%#x unk=%d count=%d" % hdr)
        for e in ents:
            print("%-60s %10d %10d %10d" % e)
    elif cmd == "x":
        data = open(sys.argv[2], "rb").read()
        outdir = sys.argv[3]
        pat = sys.argv[4].upper() if len(sys.argv) > 4 else None
        _, ents = read_dir(data)
        n = 0
        for name, a, b, c in ents:
            if pat and not fnmatch.fnmatch(name.upper(), pat):
                continue
            raw = zlib.decompress(data[a:a + b])
            dst = os.path.join(outdir, name.replace("\\", os.sep))
            os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
            open(dst, "wb").write(raw)
            n += 1
        print("extracted", n)
    elif cmd == "pack":
        src, dst = sys.argv[2], sys.argv[3]
        files = []
        for root, _, fs in os.walk(src):
            for fn in sorted(fs):
                p = os.path.join(root, fn)
                files.append((os.path.relpath(p, src), open(p, "rb").read()))
        open(dst, "wb").write(build(files))
        print("packed", len(files), "->", dst)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
