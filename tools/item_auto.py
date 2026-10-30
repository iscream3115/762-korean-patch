"""Pattern translations for repetitive ITEMINFO strings, merged with a hand draft.

usage: item_auto.py <NNN> [hand.txt]
  Prints auto lines for ids not in hand.txt; with hand.txt, writes
  trans/raw/item/NNN.txt = hand lines + auto lines (hand wins) and lists ids
  still untranslated.
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "trans"))

RANK = {"Private": "이등병", "Sergeant": "하사", "Lieutenant": "중위", "Captain": "대위", "Major": "소령", "Colonel": "대령"}
ORG = {"Algeira Police": "알헤이라 경찰", "Algeira Army": "알헤이라 육군", "Algeira Civil Guard": "알헤이라 시민 경비대",
       "Algeira Elite": "알헤이라 정예군", "Palinero Army": "팔리네로 육군", "Palinero Special Forces": "팔리네로 특수부대",
       "Palinero Police": "팔리네로 경찰", "Palinero Elite": "팔리네로 정예군"}
GRANK = {"Gunman": "총잡이", "Junior Attack Leader": "하급 돌격대장", "Senior Attack Leader": "상급 돌격대장",
         "Brigade Leader": "여단장", "Comandante": "코만단테"}
GORG = {"Tanya's": "타냐 부대", "Olvega": "올베가", "Indigenous": "원주민"}
CLIP = {"Rifle": "소총", "Pistol": "권총", "SMG": "기관단총", "Sniper rifle": "저격소총", "Sniper Rifle": "저격소총",
        "Assault Rifle": "돌격소총", "Assault rifle": "돌격소총", "Double SMG": "기관단총 2연", "Machine gun": "기관총",
        "Shotgun": "산탄총", "Revolver": "리볼버"}
AMMO_WORDS = [("Armor Piercing", "철갑"), ("Armour Piercing", "철갑")]


def alt(d):
    return "|".join(sorted(map(re.escape, d), key=len, reverse=True))


WTYPE = [("sniper rifles", "저격소총"), ("assault rifles", "돌격소총"), ("submachine guns", "기관단총"),
         ("machine guns", "기관총"), ("shotguns", "산탄총"), ("sniper rifle", "저격소총"), ("Sniper Rifle", "저격소총"), ("assault rifle", "돌격소총"),
         ("Assault Rifle", "돌격소총"), ("submachine-gun", "기관단총"), ("submachine gun", "기관단총"),
         ("Submachine Gun", "기관단총"), ("machine gun", "기관총"), ("Machine Gun", "기관총"), ("combat shotgun", "전투 산탄총"), ("shotgun", "산탄총"),
         ("revolver", "리볼버"), ("Revolver", "리볼버"), ("rifles", "소총"), ("rifle", "소총"), ("Rifle", "소총"),
         ("pistols", "권총"), ("pistol", "권총"), ("Pistol", "권총"), ("carbine", "카빈"), ("Carbine", "카빈")]


def wt(x):
    x = re.sub(r"^(.+?) family of (.+)$", r"\1 계열 \2", x)
    x = x.replace(" and ", "·").replace("Kalashnikov", "칼라시니코프")
    for a, b in [("handguns", "권총"), ("handgun", "권총"), ("weapons", "무기")]:
        x = re.sub(r"(?<![A-Za-z])%s(?![A-Za-z])" % a, b, x)
    for a, b in WTYPE:
        x = re.sub(r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(a), b, x)
    return x


def pl(x):
    x = x.replace("Parabellum", "파라벨룸").replace("12 gauge", "12게이지")
    x = re.sub(r"\bplastic box\b", "플라스틱 상자형", x)
    x = re.sub(r"\bbox\b", "상자형", x)
    return re.sub(r"\bplastic\b", "플라스틱", x)


def rtype(x):
    """'5.56x45 AP' -> '5.56x45 철갑', FMJ -> 완전피갑."""
    x = ammo(x)
    x = re.sub(r"(?<![A-Za-z])AP(?![A-Za-z])", "철갑", x)
    x = re.sub(r"(?<![A-Za-z-])FMJ(?![A-Za-z-])", "완전피갑", x)
    return x


def ammo(x):
    for a, b in AMMO_WORDS:
        x = x.replace(a, b)
    return x


RULES = [
    (r"^(?:The )?[Uu]niform of an? (%s) (%s)$" % (alt(ORG), alt(RANK)),
     lambda m: "%s %s 제복" % (ORG[m[1]], RANK[m[2]])),
    (r"^The uniform of an? (%s) (%s) ?\. Level (\d) camouflage\.$" % (alt(ORG), alt(RANK)),
     lambda m: "%s %s 제복. 위장 %s단계." % (ORG[m[1]], RANK[m[2]], m[3])),
    (r"^(?:an? )?(%s) (%s)'s Fatigues$" % (alt(GORG), alt(GRANK)),
     lambda m: "%s %s 전투복" % (GORG[m[1]], GRANK[m[2]])),
    (r"^The fatigues of (?:an? )?(%s) (%s)\. Level (\d) camouflage\.$" % (alt(GORG), alt(GRANK)),
     lambda m: "%s %s의 전투복. 위장 %s단계." % (GORG[m[1]], GRANK[m[2]], m[3])),
    (r"^Big Ammo [Bb]ox (.+)$", lambda m: "대형 탄약 상자 " + ammo(m[1])),
    (r"^Ammunition Box FMJ Ball (\(.+\))$", lambda m: "탄약 상자 완전피갑 보통탄 " + m[1]),
    (r"^Ammunition Box (.+)$", lambda m: "탄약 상자 " + ammo(m[1])),
    (r"^A factory-packed (\d+)-round box of (\S+) Full Metal Jacket cartridges with a lead core\. Proudly made in Palinero\.$",
     lambda m: "납 심을 넣은 %s 완전피갑탄 %s발이 든 공장 포장 상자. 팔리네로산임을 자랑스럽게 밝힌다." % (m[2], m[1])),
    (r"^A spare barrel for the (.+?) machine gun is used when the main barrel overheats or becomes otherwise unusable\.$",
     lambda m: "%s 기관총의 예비 총열. 주 총열이 과열되거나 쓸 수 없게 되었을 때 쓴다." % m[1]),
    (r"^A standard folding bipod for (?:the )?(.+?)\. The bipod improves shooting accuracy while prone, but somewhat disrupts the weapon's balance when firing from other positions\.$",
     lambda m: "%s용 표준 접이식 양각대. 엎드려 쏠 때 정확도가 높아지지만, 다른 자세로 쏠 때는 총의 균형을 다소 해친다." % wt(re.sub(r"^the ", "", m[1]))),
    (r"^An? (?:large )?(?:ammo )?box containing (\d+) (?:caliber |cal\.? )?(.+?) (?:rounds|cartridges|bullets)\.$",
     lambda m: "%s탄 %s발이 든 탄약 상자." % (rtype(m[2]), m[1])),
    (r"^Magazine for caliber (.+?) rifles capable of holding (\d+) rounds\.$",
     lambda m: "%s 구경 소총용 %s발들이 탄창." % (m[1], m[2])),
    (r"^Magazine for (.+?) capable of holding (\d+) rounds\.$",
     lambda m: "%s용 %s발들이 탄창." % (wt(m[1]), m[2])),
    (r"^(.+) Operations Manual$", lambda m: "%s 운용 교범" % m[1]),
    (r"^An operational manual for the (.+?) family of (assault rifles|rifles|submachine guns|machine guns|pistols|shotguns)\. (\(.+\))$",
     lambda m: "%s 계열 %s 운용 교범. %s" % (m[1], wt(m[2]), m[3].replace(" to ", " ~ "))),
    (r"^An operational manual for the (.+?)\. (\(.+\))$", lambda m: "%s 운용 교범. %s" % (wt(m[1]), m[2].replace(" to ", " ~ "))),
    (r"^Ammo Belt Box (.+)$", lambda m: "탄띠 상자 " + m[1]),
    (r"^Ammo Belt (.+)$", lambda m: "탄띠 " + m[1]),
    (r"^Ammo (.+)$", lambda m: "탄약 " + ammo(m[1])),
    (r"^A double (\d+)-round (.+?) magazine for the (.+?)\.$",
     lambda m: "%s용 %s %s발 탄창 두 개를 이은 것." % (wt(m[3]), pl(m[2]), m[1])),
    (r"^(.+) Machine Gun Spare Barrel$", lambda m: "%s 기관총 예비 총열" % m[1]),
    (r"^Box holding (\d+) (?:caliber |rounds of )?(.+?) (?:cartridges|rounds|shells)\.$",
     lambda m: "%s탄 %s발이 든 상자." % (ammo(m[2]), m[1])),
    (r"^Caliber (.+?) (?:cartridges|rounds|shells)\.$", lambda m: ammo(m[1]) + "탄."),
    (r"^(%s) (?:ammo )?[Cc]lip (\(.+\))$" % alt(CLIP), lambda m: "%s 탄창 %s" % (CLIP[m[1]], m[2])),
    (r"^Machinegun [Cc]lip (\(.+\))$", lambda m: "기관총 탄창 " + m[1]),
    (r"^(%s) [Mm]agazine (\(.+\))$" % alt(CLIP), lambda m: "%s 탄창 %s" % (CLIP[m[1]], m[2])),
    (r"^Box Magazine (\(.+\))$", lambda m: "상자형 탄창 " + m[1]),
    (r"^Drum Magazine (\(.+\))$", lambda m: "드럼 탄창 " + m[1]),
    (r"^An? curved (\d+)[- ]round box magazines? for the (.+?)\.$",
     lambda m: "%s용 %s발들이 곡선형 상자형 탄창." % (wt(m[2]), m[1])),
    (r"^An? (\d+)[- ]round (\S+) box magazine for the (.+?)\.$",
     lambda m: "%s용 %s발들이 %s 상자형 탄창." % (wt(m[3]), m[1], pl(m[2]))),
    (r"^An? (\d+)-round box magazine for the (.+?)\.$", lambda m: "%s용 %s발들이 상자형 탄창." % (wt(m[2]), m[1])),
    (r"^An? stock (\d+)-round (.+?) box magazine for the (.+?)\.$",
     lambda m: "%s용 표준 %s발들이 %s 상자형 탄창." % (wt(m[3]), m[1], pl(m[2]))),
    (r"^An? stock (\d+)-round (.+?) magazine\.$", lambda m: "표준 %s발들이 %s 탄창." % (m[1], pl(wt(m[2])))),
    (r"^An? (?:stock |[Ii]ncreased capacity )?(\d+)-round (?:magazine )?(.+?) magazine for (?:the )?(.+?)\.$",
     lambda m: "%s용 %s발들이 %s 탄창." % (wt(m[3]), m[1], pl(m[2]))),
    (r"^An? (?:stock )?(\d+)-round magazine (.+?) for (?:the )?(.+?)\.$",
     lambda m: "%s용 %s발들이 %s 탄창." % (wt(m[3]), m[1], pl(m[2]))),
    (r"^A double (\d+)-round (?:box )?(.+?) (?:box )?magazine for (?:the )?(.+?), with a total capacity of (\d+) rounds\.$",
     lambda m: "%s용 %s %s발 탄창 두 개를 이은 것으로, 총 %s발이 들어간다." % (wt(m[3]), pl(m[2]), m[1], m[4])),
    (r"^Double Plastic Mag (\(.+\))$", lambda m: "플라스틱 2연 탄창 " + m[1]),
    (r"^Double Mag (\(.+\))$", lambda m: "2연 탄창 " + m[1]),
    (r"^Plastic Box Magazine (\(.+\))$", lambda m: "플라스틱 상자형 탄창 " + m[1]),
    (r"^Modified\s+(.+?) w/ Foregrip (\(.+\))$", lambda m: "개조 %s + 앞손잡이 %s" % (m[1], m[2])),
    (r"^Modified\s+(.+?) w/ (\S+) (\(.+\))$", lambda m: "개조 %s + %s %s" % (m[1], m[2], m[3])),
    (r"^Modified\s+(.+?) (\d+mm) Grenade Launcher$", lambda m: "개조 %s %s 유탄발사기" % (m[1], m[2])),
    (r"^Modified\s+(.+?)\s+Multi-shot grenade launcher$", lambda m: "개조 %s 연발 유탄발사기" % m[1]),
    (r"^Modified\s+(.+)$", lambda m: "개조 " + m[1]),
    (r"^Submachine-gun (.+?) with Foregrip (\(.+\))$", lambda m: "기관단총 %s + 앞손잡이 %s" % (m[1], m[2])),
    (r"^(.+?) w/ Foregrip (\(.+\))$", lambda m: "%s + 앞손잡이 %s" % (m[1], m[2])),
    (r"^(.+?) with silencer (\(.+\))$", lambda m: "%s + 소음기 %s" % (m[1], m[2])),
    (r"^(.+?) Level (\d) camouflage\.$", None),
]


def auto(en):
    for rx, fn in RULES:
        m = re.match(rx, en)
        if m and fn:
            return fn(m)
    return None


def main():
    num = sys.argv[1]
    rows = [json.loads(l)["en"] for l in open(os.path.join(ROOT, "src", "item", num + ".jsonl"), encoding="utf-8")]
    hand = {}
    if len(sys.argv) > 2:
        for ln in open(sys.argv[2], encoding="utf-8"):
            i, _, ko = ln.rstrip("\n").partition("|")
            if i.strip().isdigit():
                hand[int(i)] = ko
    out, todo = {}, []
    for n, en in enumerate(rows, 1):
        if n in hand:
            out[n] = hand[n]
        else:
            a = auto(en)
            if a:
                out[n] = a
            else:
                todo.append(n)
    if len(sys.argv) > 2:
        with open(os.path.join(ROOT, "raw", "item", num + ".txt"), "w", encoding="utf-8") as f:
            for n in sorted(out):
                f.write("%d|%s\n" % (n, out[n]))
        print("written %d lines, untranslated: %s" % (len(out), todo))
    else:
        for n in sorted(out):
            print("%d|%s" % (n, out[n]))
        print("# todo:", " ".join(map(str, todo)))


if __name__ == "__main__":
    main()
