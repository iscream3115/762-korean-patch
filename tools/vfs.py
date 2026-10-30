"""Effective-file view of the game's VFS (packs in INI\\vfs.ini order, first wins)."""
import os
import re
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import azp  # noqa: E402

GAME = r"C:\Program Files (x86)\Steam\steamapps\common\7.62"
# original Blue Sun order (Korean.azp excluded on purpose)
PACKS = ["BlueSun.azp", "HWM.azp", "patch_1_10.azp", "patch_1_02.azp", "patch_1_01.azp", "Pack0.azp"]


class VFS:
    def __init__(self, game=GAME, packs=PACKS):
        self.packs = []
        self.index = {}
        for p in packs:
            data = open(os.path.join(game, p), "rb").read()
            _, ents = azp.read_dir(data)
            self.packs.append((p, data))
            for name, a, b, c in ents:
                self.index.setdefault(name.upper(), (len(self.packs) - 1, a, b))

    def names(self, pattern=None):
        rx = re.compile(pattern, re.I) if pattern else None
        return sorted(n for n in self.index if not rx or rx.search(n))

    def pack_of(self, name):
        return self.packs[self.index[name.upper()][0]][0]

    def read(self, name):
        i, a, b = self.index[name.upper()]
        return zlib.decompress(self.packs[i][1][a:a + b])
