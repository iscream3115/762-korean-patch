"""Build a small test Korean.azp: Blue Sun LOCAL.TXT with a few entries in Korean.

usage: python make_test_pack.py <game_dir> <out.azp>
"""
import os
import re
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import azp  # noqa: E402

TEST = {
    90: "정말 종료하시겠습니까?",
    268: "불러오기",
    694: "정말 게임을 종료하시겠습니까?",
    729: "설정",
    831: "체력",
    832: "기력",
    833: "근력",
    837: "속사",
    1371: "남은 포인트",
    1436: "새 게임을 시작하기 전에 튜토리얼을 플레이하시겠습니까?",
    1437: "경고!^^선택한 난이도는 게임 전체에 적용됩니다!^^게임 설정 메뉴에서 변경할 수 있습니다.^^현재 난이도로 계속하시겠습니까?",
}


def main():
    game, out = sys.argv[1], sys.argv[2]
    data = open(os.path.join(game, "BlueSun.azp"), "rb").read()
    _, ents = azp.read_dir(data)
    name, a, b, c = next(e for e in ents if e[0] == "LOCAL.TXT")
    text = azp.xcrypt(zlib.decompress(data[a:a + b]))
    lines = text.split(b"\r\n")
    done = set()
    for i, ln in enumerate(lines):
        m = re.match(rb"^(\d+)(\s+)\"", ln)
        if m and int(m.group(1)) in TEST:
            k = int(m.group(1))
            lines[i] = m.group(1) + m.group(2) + b'"' + TEST[k].encode("cp949") + b'"'
            done.add(k)
    print("replaced", sorted(done))
    new = b"\r\n".join(lines)
    open(out, "wb").write(azp.build([("LOCAL.TXT", azp.xencrypt(new))]))
    print("wrote", out, len(new), "bytes text")


if __name__ == "__main__":
    main()
