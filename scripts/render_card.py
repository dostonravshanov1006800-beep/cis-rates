#!/usr/bin/env python3
"""Карточка «Курсы сейчас»: data/rates.json + history.json -> docs/rates.png. Только Pillow, без внешних API и ключей."""
import json, os, sys, datetime as dt
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "design")); sys.path.insert(0, ".")
from art import *

R = json.load(open("../data/rates.json", encoding="utf-8"))
try: H = json.load(open("../data/history.json", encoding="utf-8"))
except Exception: H = []
S = 2                                   # рисуем в 2x и уменьшаем: сглаженные линии и текст
W, HH = 1280, 960
BG, CARD, LINE = (8, 10, 18), (17, 21, 34), (42, 50, 74)
TX, MUT, DIM = (244, 246, 252), (138, 150, 182), (84, 96, 128)
UP, DN = (46, 224, 138), (255, 91, 107)

fmt = lambda n: (f"{n:,.0f}" if abs(n) >= 100 else f"{n:,.2f}" if abs(n) >= 1 else f"{n:.4f}").replace(",", " ")
img = gradient(W * S, HH * S, (11, 14, 26), (5, 6, 12), 0.25)
img = glow(img, (200 * S, 40 * S, 300 * S), (60, 100, 255), 0.14, 120 * S)
img = glow(img, (1120 * S, 60 * S, 260 * S), (255, 190, 60), 0.12, 120 * S)
d = ImageDraw.Draw(img)
f = lambda n, s, w=None: F(n, s * S, w)
def T(x, y, s, font, fill, a="la"): d.text((x * S, y * S), s, font=font, fill=fill + (255,), anchor=a)
def box(x, y, w, h, r=16, fill=CARD, ol=LINE): d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=r * S, fill=fill + (255,), outline=ol + (255,), width=S)

def spark(x, y, w, h, vals, col):
    """Мини-график: линия + мягкая заливка. Шкала по min/max самого ряда."""
    if len(vals) < 3 or max(vals) == min(vals):
        d.line([x * S, (y + h / 2) * S, (x + w) * S, (y + h / 2) * S], fill=DIM + (255,), width=2 * S); return
    lo, hi = min(vals), max(vals)
    pts = [((x + i * w / (len(vals) - 1)) * S, (y + h - (v - lo) / (hi - lo) * h) * S) for i, v in enumerate(vals)]
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.polygon(pts + [(pts[-1][0], (y + h) * S), (pts[0][0], (y + h) * S)], fill=col + (46,))
    img.alpha_composite(lay)
    d.line(pts, fill=col + (255,), width=int(2.4 * S), joint="curve")
    px, py = pts[-1]; d.ellipse([px - 4 * S, py - 4 * S, px + 4 * S, py + 4 * S], fill=col + (255,))

def series(key, n=36):
    v = [p[key] for p in H if p.get(key)]; return v[-n:]
def tri(cx, cy, up, col):
    d.polygon([((cx - 6) * S, (cy + 4) * S), ((cx + 6) * S, (cy + 4) * S), (cx * S, (cy - 6) * S)] if up else [((cx - 6) * S, (cy - 4) * S), ((cx + 6) * S, (cy - 4) * S), (cx * S, (cy + 6) * S)], fill=col + (255,))

# ── шапка
now = dt.datetime.fromisoformat(R["updated"]).astimezone(dt.timezone(dt.timedelta(hours=5)))
age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(R["updated"])).total_seconds() / 60
T(48, 34, "CIS", f("unb", 40, 800), GOLD2); T(48 + 94, 34, "RATES", f("unb", 40, 800), TX)
T(48, 88, "курсы валют СНГ и крипты в реальном времени", f("mont", 17, 500), MUT)
live = age < 20
d.ellipse([(W - 330) * S, 44 * S, (W - 314) * S, 60 * S], fill=(UP if live else DN) + (255,))
T(W - 300, 40, "LIVE" if live else "ДАННЫЕ УСТАРЕЛИ", f("mont", 22, 800), UP if live else DN)
T(W - 48, 38, now.strftime("%H:%M"), f("unb", 30, 700), TX, "ra")
T(W - 48, 78, now.strftime("%d.%m.%Y") + "  ·  время Ташкента", f("mont", 15, 500), MUT, "ra")

# ── левая колонка: 12 стран СНГ
LX, LW, TOP, RH, GAP = 48, 600, 138, 60, 8
T(LX, TOP - 4, "1 USD  =", f("mont", 17, 700), MUT)
T(LX + LW, TOP - 4, "за 24 ч / тренд", f("mont", 15, 500), DIM, "ra")
cis = [(k, c) for k, c in R["countries"].items() if c["region"] == "cis"]
for i, (k, c) in enumerate(cis):
    y = TOP + 26 + i * (RH + GAP); box(LX, y, LW, RH, 14)
    d.rounded_rectangle([(LX + 12) * S, (y + 14) * S, (LX + 58) * S, (y + 46) * S], radius=8 * S, fill=GOLD2 + (255,))
    T(LX + 35, y + 30, k, f("mont", 19, 800), (22, 14, 4), "mm")
    T(LX + 72, y + 22, c["name"], f("mont", 19, 700), TX, "lm"); T(LX + 72, y + 44, c["cur"], f("mont", 13, 600), MUT, "lm")
    o = R["official"].get(k, {}).get("rates", {}).get("USD")
    val = o["rate"] if o else R["world"][c["cur"]]
    T(LX + 372, y + 30, fmt(val), f("mont", 25, 800), TX, "rm"); T(LX + 380, y + 33, c["sym"], f("mont", 13, 600), MUT, "lm")
    sv = series(c["cur"])
    spark(LX + 440, y + 14, 100, 32, sv, DIM if (len(sv) < 3 or max(sv) == min(sv)) else (UP if sv[-1] >= sv[0] else DN))
    if o and o.get("diff"):
        up = o["diff"] > 0; tri(LX + 570, y + 30, up, DN if up else UP)   # курс доллара вырос = валюта слабее

# ── правая колонка: крипта
RX, RW = 692, 540
T(RX, TOP - 4, "КРИПТОВАЛЮТЫ  ·  USD", f("mont", 17, 700), MUT)
T(RX + RW, TOP - 4, "24 ч", f("mont", 15, 500), DIM, "ra")
for i, x in enumerate(R["crypto"][:12]):
    y = TOP + 26 + i * (RH + GAP); box(RX, y, RW, RH, 14)
    T(RX + 18, y + 22, x["sym"], f("mont", 20, 800), GOLD2, "lm"); T(RX + 18, y + 44, x["name"][:13], f("mont", 13, 600), MUT, "lm")
    sv = series(x["sym"]); ch = x["ch24h"]; col = UP if ch >= 0 else DN
    spark(RX + 150, y + 14, 90, 32, sv, col if len(sv) > 2 else DIM)
    T(RX + 392, y + 30, "$" + fmt(x["usd"]), f("mont", 24, 800), TX, "rm")
    d.rounded_rectangle([(RX + 408) * S, (y + 17) * S, (RX + 522) * S, (y + 43) * S], radius=8 * S, fill=col + (44,))
    T(RX + 465, y + 30, f"{ch:+.2f}%", f("mont", 17, 800), col, "mm")

# ── шкала настроения рынка
avg = sum(x["ch24h"] for x in R["crypto"][:10]) / 10
by = TOP + 26 + 12 * (RH + GAP) + 6
box(48, by, W - 96, 66, 16)
T(70, by + 22, "НАСТРОЕНИЕ РЫНКА КРИПТЫ  ·  24 ч", f("mont", 14, 700), MUT, "lm")
bx0, bx1, byy = 70, 760, by + 46
d.rounded_rectangle([bx0 * S, (byy - 5) * S, bx1 * S, (byy + 5) * S], radius=5 * S, fill=LINE + (255,))
mid = (bx0 + bx1) / 2; pos = max(-1, min(1, avg / 5))                 # шкала -5%..+5%
x1 = mid + pos * (bx1 - bx0) / 2; col = UP if avg >= 0 else DN
d.rounded_rectangle([min(mid, x1) * S, (byy - 5) * S, max(mid, x1) * S, (byy + 5) * S], radius=5 * S, fill=col + (255,))
d.ellipse([(x1 - 9) * S, (byy - 9) * S, (x1 + 9) * S, (byy + 9) * S], fill=TX + (255,), outline=col + (255,), width=3 * S)
d.line([mid * S, (byy - 11) * S, mid * S, (byy + 11) * S], fill=MUT + (255,), width=S)
T(bx0, by + 8, "", f("mont", 10), MUT)
mood = "Рынок растёт" if avg > 1 else "Рынок падает" if avg < -1 else "Боковик"
T(800, by + 33, mood, f("mont", 24, 800), col, "lm"); T(W - 70, by + 33, f"{avg:+.2f}%", f("unb", 26, 800), col, "rm")

T(48, HH - 26, "t.me/Well_Currency_bot", f("mont", 17, 700), MUT, "lm")
T(W - 48, HH - 26, "ЦБ стран СНГ · ExchangeRate-API · CoinGecko", f("mont", 14, 500), DIM, "rm")

os.makedirs("../docs", exist_ok=True)
img.convert("RGB").resize((W, HH), Image.LANCZOS).save("../docs/rates.png", optimize=True)
print("карточка готова", os.path.getsize("../docs/rates.png") // 1024, "КБ")
