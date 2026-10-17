#!/usr/bin/env python3
"""Рисует карточку «Курсы сейчас» из data/rates.json -> docs/rates.png. Только Pillow, без внешних API."""
import json, os, sys, datetime as dt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "design"))
os.chdir(os.path.join(os.path.dirname(__file__), "..", "design"))
from art import *

R = json.load(open("../data/rates.json", encoding="utf-8"))
W, H = 1280, 900
fmt = lambda n: (f"{n:,.0f}" if abs(n) >= 100 else f"{n:,.2f}" if abs(n) >= 1 else f"{n:.4f}").replace(",", " ")
img = gradient(W, H, (10, 14, 28), (4, 6, 14), 0.3)
img = glow(img, (260, 80, 320), (60, 110, 255), 0.22, 140); img = glow(img, (1150, 120, 260), (255, 190, 60), 0.16, 140)
d = ImageDraw.Draw(img)
def txt(xy, s, f, fill, anchor="la"): d.text(xy, s, font=f, fill=fill, anchor=anchor)
def card(x, y, w, h):
    d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=(20, 26, 46, 255), outline=(60, 72, 110, 255), width=2)

# шапка
txt((50, 40), "CIS Rates", F("unb", 46, 800), GOLD2 + (255,))
now = dt.datetime.fromisoformat(R["updated"]).astimezone(dt.timezone(dt.timedelta(hours=5)))
txt((W - 50, 46), now.strftime("%d.%m.%Y  %H:%M") + "  (UZ)", F("mont", 26, 700), (190, 200, 225, 255), "ra")
txt((W - 50, 82), "официальные курсы ЦБ и рыночные", F("mont", 18, 500), (120, 135, 170, 255), "ra")

# левая колонка: 12 стран СНГ, цена 1 USD
txt((50, 120), "1 USD в странах СНГ", F("mont", 26, 800), (255, 255, 255, 255))
cis = [(k, c) for k, c in R["countries"].items() if c["region"] == "cis"]
for i, (k, c) in enumerate(cis):
    y = 165 + i * 58
    card(50, y, 590, 50)
    d.rounded_rectangle([62, y + 9, 108, y + 41], radius=8, fill=GOLD2 + (255,)); txt((85, y + 25), k, F("mont", 20, 800), (20, 14, 4, 255), "mm")
    txt((124, y + 25), c["name"], F("mont", 22, 600), (230, 236, 250, 255), "lm")
    o = R["official"].get(k, {}).get("rates", {}).get("USD")
    val = o["rate"] if o else R["world"][c["cur"]]
    txt((600, y + 25), f"{fmt(val)} {c['sym']}", F("mont", 24, 800), (255, 255, 255, 255), "rm")
    if o and o.get("diff"):
        up = o["diff"] > 0; col = (255, 90, 100, 255) if up else (40, 220, 140, 255); cx, cy = 622, y + 25   # рост курса к USD = валюта слабее
        d.polygon([(cx - 8, cy + 6), (cx + 8, cy + 6), (cx, cy - 8)] if up else [(cx - 8, cy - 6), (cx + 8, cy - 6), (cx, cy + 8)], fill=col)

# правая колонка: крипта
txt((680, 120), "Криптовалюты, USD", F("mont", 26, 800), (255, 255, 255, 255))
for i, x in enumerate(R["crypto"][:12]):
    y = 165 + i * 58
    card(680, y, 550, 50)
    txt((700, y + 25), x["sym"], F("mont", 22, 800), GOLD2 + (255,), "lm")
    txt((830, y + 25), x["name"][:14], F("mont", 18, 500), (150, 165, 200, 255), "lm")
    txt((1075, y + 25), "$" + fmt(x["usd"]), F("mont", 24, 800), (255, 255, 255, 255), "rm")
    ch = x["ch24h"]; col = (40, 220, 140, 255) if ch >= 0 else (255, 90, 100, 255)
    txt((1212, y + 25), f"{ch:+.1f}%", F("mont", 22, 800), col, "rm")

# подвал
avg = sum(x["ch24h"] for x in R["crypto"][:10]) / 10
txt((50, 868), "t.me/Well_Currency_bot", F("mont", 22, 700), (150, 165, 200, 255), "lm")
txt((W - 50, 868), f"рынок крипты 24ч: {avg:+.1f}%", F("mont", 22, 800), (40, 220, 140, 255) if avg >= 0 else (255, 90, 100, 255), "rm")
os.makedirs("../docs", exist_ok=True)
img.convert("RGB").save("../docs/rates.png", optimize=True)
print("карточка готова", os.path.getsize("../docs/rates.png") // 1024, "КБ")
