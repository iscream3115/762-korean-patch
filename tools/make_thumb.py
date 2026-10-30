"""Release thumbnail: game title art + "한글패치" in the title's white/gold grunge style.
usage: python make_thumb.py <title.jpg> <out.png>"""
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
FONT = r"C:\Users\rhksg\AppData\Local\Microsoft\Windows\Fonts\NanumGothicExtraBold.ttf"
GOLD = (196, 160, 62)
DARK = (28, 24, 18)

src = Image.open(sys.argv[1]).convert("RGB")
# Erase the English "HIGH CALIBRE" (art coords x 140-500, y 200-275) by cloning the plain
# grunge from just below it, with soft edges; "하이 캘리버" is drawn in its place later.
HC = (138, 212, 500, 283)
patch = src.crop((HC[0], 282, HC[2], 282 + HC[3] - HC[1]))
pm = Image.new("L", patch.size, 0)
pd = ImageDraw.Draw(pm)
pd.rectangle([6, 4, patch.width - 7, patch.height - 5], fill=255)
dx, dy = 243 - HC[0], 206 - HC[1]          # keep the "." of 7.62
pd.ellipse([dx - 17, dy - 17, dx + 17, dy + 17], fill=0)
pm = pm.filter(ImageFilter.GaussianBlur(3))
src.paste(patch, HC[:2], pm)
# background: the art scaled to cover, blurred; foreground: the art shrunk into the top
s = max(W / src.width, H / src.height)
bg = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
bx, by = (bg.width - W) // 2, bg.height - H
img = bg.crop((bx, by, bx + W, by + H)).filter(ImageFilter.GaussianBlur(14))
FH = 610
fg = src.resize((round(src.width * FH / src.height), FH), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
fx = (W - fg.width) // 2
mask = Image.new("L", fg.size, 255)
md = ImageDraw.Draw(mask)
for i in range(60):          # feather all four edges into the blurred background
    a = int(255 * i / 60)
    md.rectangle([i, i, fg.width - 1 - i, fg.height - 1 - i], outline=a)
img.paste(fg, (fx, 0), mask)

# darken the lower band a little so the new text reads on the bright grunge
shade = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(shade)
for y in range(H):
    t = max(0.0, (y - 520) / (H - 520))
    d.line([(0, y), (W, y)], fill=int(120 * t))
img = Image.composite(Image.new("RGB", (W, H), (10, 10, 12)), img, shade)


def grunge(size, seed):
    """Speckle mask that eats small holes out of the letters, like the title art."""
    random.seed(seed)
    m = Image.new("L", size, 255)
    dd = ImageDraw.Draw(m)
    for _ in range(size[0] * size[1] // 900):
        x, y = random.randrange(size[0]), random.randrange(size[1])
        r = random.choice((1, 1, 2, 2, 3, 5))
        dd.ellipse([x - r, y - r, x + r, y + r], fill=0)
    return m.filter(ImageFilter.GaussianBlur(0.6))


def stamp(text, font, xy, fill, stroke, sw, angle, seed):
    """Draw text with a dark drop shadow, a gold outline and a worn white face."""
    pad = sw * 4 + 20
    bbox = font.getbbox(text, stroke_width=sw)
    tw, th = bbox[2] + pad * 2, bbox[3] + pad * 2
    layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    # shadow
    sh = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(sh).text((pad + 8, pad + 10), text, font=font, fill=230, stroke_width=sw + 4, stroke_fill=230)
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    layer.paste((0, 0, 0, 255), (0, 0), sh)
    # dark rim, gold outline, white face
    ld.text((pad, pad), text, font=font, fill=DARK, stroke_width=sw + 5, stroke_fill=DARK)
    ld.text((pad, pad), text, font=font, fill=stroke, stroke_width=sw, stroke_fill=stroke)
    face = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(face).text((pad, pad), text, font=font, fill=255)
    face = ImageChops.multiply(face, grunge((tw, th), seed))
    layer.paste(fill + (255,), (0, 0), face)
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    img.paste(layer, (xy[0] - pad, xy[1] - pad), layer)


# "하이 캘리버" where HIGH CALIBRE was (art -> thumb: x*k + fx, y*k, k = FH / art height)
k = FH / src.height
mid = fx + (HC[0] + HC[2]) / 2 * k
sub = ImageFont.truetype(FONT, 104)
sw_ = sub.getbbox("하이 캘리버")[2]
stamp("하이 캘리버", sub, (int(mid - sw_ / 2), int(HC[1] * k) - 26), (250, 250, 246), GOLD, 6, 3, 11)

big = ImageFont.truetype(FONT, 142)
bw = big.getbbox("한글패치")[2]
stamp("한글패치", big, (640 - bw // 2, 505), (250, 250, 246), GOLD, 7, 2, 7)

img.save(sys.argv[2])
print("saved", sys.argv[2], img.size)
