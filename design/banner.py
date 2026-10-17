import random, math
from art import *

W, H = 1920, 1080
img = gradient(W, H, (6, 9, 22), (2, 3, 10), 0.35)
# фоновое свечение
img = glow(img, (1500, 300, 520), (40, 90, 220), 0.55, 160)
img = glow(img, (1650, 820, 420), (255, 170, 30), 0.38, 150)
img = glow(img, (300, 980, 380), (20, 160, 130), 0.25, 160)

# сетка-перспектива
g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
for i in range(0, W, 80): gd.line([i, 0, i, H], fill=(120, 160, 255, 14), width=1)
for j in range(0, H, 80): gd.line([0, j, W, j], fill=(120, 160, 255, 14), width=1)
img = Image.alpha_composite(img, g)

# свечной график справа с градиентной тенью
ch = candles(1100, 560, seed=11, n=40, up=True, drift=0.72)
fade = vgrad_mask(ch.size, 255, 40); a = ch.getchannel("A"); ch.putalpha(ImageChops.multiply(a, fade))
chb = ch.filter(ImageFilter.GaussianBlur(14)); chb2 = Image.new("RGBA", ch.size, (0, 0, 0, 0)); chb2.paste(chb, (0, 0))
img.alpha_composite(chb2, (800, 360)); img.alpha_composite(ch, (800, 360))
# линия тренда
tr = Image.new("RGBA", (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(tr)
pts = [(830 + i * 26, 830 - (i ** 1.18) * 6.2 - math.sin(i / 2.1) * 26) for i in range(40)]
td.line(pts, fill=GREEN + (255,), width=6, joint="curve")
tr_b = tr.filter(ImageFilter.GaussianBlur(10)); img = Image.alpha_composite(img, tr_b); img = Image.alpha_composite(img, tr)

# карточки курсов (стекло)
def card(base, x, y, w, h, sym, name, val, ch_, up=True):
    L = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle([x, y, x + w, y + h], radius=34, fill=(255, 255, 255, 22), outline=(255, 255, 255, 60), width=2)
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([x, y + 14, x + w, y + h + 14], radius=34, fill=(0, 0, 0, 170))
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(26))); base = Image.alpha_composite(base, L)
    d = ImageDraw.Draw(base)
    d.text((x + 34, y + 24), name, font=F("mont", 26, 600), fill=(170, 185, 215, 255))
    d.text((x + 34, y + 62), val, font=F("unb", 44, 700), fill=(255, 255, 255, 255))
    col = GREEN if up else RED
    d.rounded_rectangle([x + 34, y + h - 58, x + 34 + 128, y + h - 20], radius=19, fill=col + (60,))
    d.text((x + 52, y + h - 55), ("▲ " if up else "▼ ") + ch_, font=F("mont", 24, 700), fill=col + (255,))
    return base
img = card(img, 1180, 140, 330, 150, "", "USD / UZS", "12 056", "+0.37%")
img = card(img, 1540, 250, 330, 150, "", "BTC / USD", "81 401", "+1.2%")
img = card(img, 1380, 420, 330, 150, "", "TON / USD", "1.35", "+0.3%")

# монеты
for sym, kind, size, xy, ang in [("$", "gold", 340, (1330, 640), 0), ("₿", "gold", 250, (1655, 600), 0), ("TON", "blue", 210, (960, 190), 0), ("€", "silver", 190, (1020, 760), 0), ("₽", "silver", 150, (1690, 850), 0)]:
    cn = coin(size, sym, kind, font_scale=0.4 if len(sym) > 1 else 0.5)
    img = glow(img, (xy[0] + size // 2, xy[1] + size // 2, size // 2 + 20), {"gold": (255, 180, 40), "blue": (60, 140, 255), "silver": (170, 190, 230)}[kind], 0.22, 50)
    img = shadow_paste(img, cn, xy, blur=28, op=170, off=(8, 28))

# частицы
rnd = random.Random(5); pl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(pl)
for _ in range(120):
    x, y, r = rnd.randint(0, W), rnd.randint(0, H), rnd.choice([1, 1, 2, 2, 3, 4]); c = rnd.choice([(255, 220, 140), (140, 190, 255), (255, 255, 255)])
    pd.ellipse([x - r, y - r, x + r, y + r], fill=c + (rnd.randint(70, 200),))
img = Image.alpha_composite(img, pl.filter(ImageFilter.GaussianBlur(0.8)))

# заголовок
bb = text_grad(img, (110, 300), "CIS", F("unb", 190, 900), GOLD1, GOLD3)
bb2 = text_grad(img, (110, 510), "RATES", F("unb", 190, 900), (255, 255, 255), (165, 190, 235))
d = ImageDraw.Draw(img)
d.rounded_rectangle([114, 270, 114 + 190, 278], radius=4, fill=GOLD2 + (255,))
d.text((116, 760), "Курсы валют СНГ и Европы + крипта", font=F("mont", 44, 700), fill=(225, 232, 248, 255))
d.text((116, 825), "24 страны  •  ТОП-20 монет  •  обновление 24/7", font=F("mont", 32, 600), fill=(140, 158, 195, 255))
# бейдж
d.rounded_rectangle([114, 910, 114 + 430, 910 + 78], radius=39, fill=(255, 255, 255, 18), outline=GOLD2 + (200,), width=2)
d.text((150, 925), "@Well_Currency_bot", font=F("mont", 36, 700), fill=GOLD1 + (255,))

# виньетка
vg = Image.new("L", (W, H), 0); vd = ImageDraw.Draw(vg); vd.ellipse([-300, -250, W + 300, H + 250], fill=255); vg = vg.filter(ImageFilter.GaussianBlur(200))
dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(ImageChops.invert(vg).point(lambda v: int(v * 0.7))); img = Image.alpha_composite(img, dark)
img.convert("RGB").save("banner_new.png", optimize=True)
img.convert("RGB").resize((1280, 720), Image.LANCZOS).save("banner_1280.jpg", quality=92)
print("OK", img.size)
