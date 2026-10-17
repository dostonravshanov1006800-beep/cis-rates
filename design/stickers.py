"""Генератор премиум-пака CIS Rates: 10 видео-стикеров, зависят от текущего рынка."""
import json, math, os, subprocess, sys, shutil
from art import *

R = json.load(open("../data/rates.json", encoding="utf-8"))
OUT = sys.argv[1] if len(sys.argv) > 1 else "pack"
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
FPS, N = 15, 45

fmt = lambda n: (f"{n:,.0f}" if abs(n) >= 100 else f"{n:,.2f}" if abs(n) >= 1 else f"{n:.4f}").replace(",", " ")
cr = lambda s: next(x for x in R["crypto"] if x["sym"] == s)
uzd = R["official"]["UZ"]["rates"]["USD"]; usd = uzd["rate"]
def mood(ch):
    return ("up", GREEN, "▲") if ch > 0.3 else (("down", RED, "▼") if ch < -0.3 else ("flat", (150, 170, 210), "●"))

def label(img, text, y, size=44, fill=(255, 255, 255), stroke=(8, 12, 28), w=9):
    d = ImageDraw.Draw(img); f = F("unb", size, 800)
    bb = d.textbbox((0, 0), text, font=f)
    while bb[2] - bb[0] > 470 and size > 18: size -= 2; f = F("unb", size, 800); bb = d.textbbox((0, 0), text, font=f)
    x = (512 - (bb[2] - bb[0])) // 2 - bb[0]
    d.text((x, y), text, font=f, fill=fill + (255,), stroke_width=w, stroke_fill=stroke + (255,))

def pill(img, text, y, col, size=34):
    d = ImageDraw.Draw(img); f = F("mont", size, 800); bb = d.textbbox((0, 0), text, font=f); tw = bb[2] - bb[0]
    x0 = (512 - tw) // 2 - 22; d.rounded_rectangle([x0, y, x0 + tw + 44, y + size + 28], radius=(size + 28) // 2, fill=col + (255,), outline=(255, 255, 255, 255), width=4)
    d.text((x0 + 22 - bb[0], y + 12 - bb[1] + 4), text, font=f, fill=(10, 14, 30, 255))

def render(name, draw_frame, emoji):
    d = f"{OUT}/_{name}"; os.makedirs(d, exist_ok=True)
    for i in range(N):
        img = Image.new("RGBA", (512, 512), (0, 0, 0, 0)); draw_frame(img, i / N); img.save(f"{d}/f{i:03d}.png")
    out = f"{OUT}/{name}.webm"
    for crf in (34, 38, 42, 46, 50):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{d}/f%03d.png", "-vf", "format=yuva420p", "-c:v", "libvpx-vp9",
                        "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", str(crf), "-an", "-t", "3", "-auto-alt-ref", "0", "-metadata:s:v:0", "alpha_mode=1", out], check=True)
        if os.path.getsize(out) < 250_000: break
    shutil.rmtree(d); json.dump({"emoji": emoji}, open(f"{OUT}/{name}.json", "w")); print(f"{name}: {os.path.getsize(out)//1024} КБ, crf {crf}")

def spin(t, w=440): return max(24, int(w * abs(math.cos(t * math.pi * 2 * 0.5))))   # вращение монеты
def bob(t, a=14): return int(math.sin(t * 2 * math.pi) * a)                         # покачивание
def coin_frame(sym, kind, t, y0=40, size=430, fs=0.5):
    c = coin(size, sym, kind, fs); w = spin(t, size); return c.resize((w, size), Image.LANCZOS), (256 - w // 2, y0 + bob(t))

def sticker_coin(name, sym, kind, title, valtxt, chg, emoji):
    m, col, ar = mood(chg)
    def fr(img, t):
        c, xy = coin_frame(sym, kind, t, 14, 350, 0.5 if len(sym) == 1 else 0.36); img.alpha_composite(c, xy)
        label(img, title, 366, 40); pill(img, f"{ar} {abs(chg):.1f}%  {valtxt}", 428, col, 30)
    render(name, fr, emoji)

# 1-5: монеты и курсы дня
sticker_coin("01_usd", "$", "gold", "USD = " + fmt(usd), "сум", -uzd["diff"] / usd * 100, ["💵"])
b, e, tn, so = cr("BTC"), cr("ETH"), cr("TON"), cr("SOL")
sticker_coin("02_btc", "₿", "gold", "BTC $" + fmt(b["usd"]), "24ч", b["ch24h"], ["🚀"])
sticker_coin("03_eth", "Ξ", "silver", "ETH $" + fmt(e["usd"]), "24ч", e["ch24h"], ["💎"])
sticker_coin("04_ton", "TON", "blue", "TON $" + fmt(tn["usd"]), "24ч", tn["ch24h"], ["💠"])
sticker_coin("05_sol", "◎", "green", "SOL $" + fmt(so["usd"]), "24ч", so["ch24h"], ["⚡"])

# 6: «настроение рынка» (меняется от среднего изменения топ-10)
top = R["crypto"][:10]; avg = sum(x["ch24h"] for x in top) / len(top)
state, scol, sar = mood(avg)
TXT = {"up": ("К ЛУНЕ!", "рынок растёт", ["🚀"]), "down": ("БЕРЁМ?", "рынок падает", ["📉"]), "flat": ("ШТИЛЬ", "рынок стоит", ["😴"])}[state]
def fr_mood(img, t):
    ch = candles(440, 250, seed=3 + int(t * 6), n=26, up=(state != "down"), drift=0.78 if state == "up" else 0.22 if state == "down" else 0.5)
    sh = int(math.sin(t * 2 * math.pi) * 6); img.alpha_composite(ch, (36, 70 + sh))
    label(img, TXT[0], 326, 74, scol); pill(img, f"{TXT[1]} {avg:+.1f}%", 420, scol, 30)
render("06_mood", fr_mood, TXT[2])

# 7: «держу» / «паника» от BTC за 7 дней
c7 = b["ch7d"]; hold = c7 > -3
def fr_hold(img, t):
    c, xy = coin_frame("₿", "gold" if hold else "red", t, 36, 310, 0.5)
    shake = int(math.sin(t * 2 * math.pi * 6) * (3 if hold else 10)); img.alpha_composite(c, (xy[0] + shake, xy[1]))
    label(img, "ДЕРЖУ 💪".replace(" 💪", "") if hold else "ПАНИКА!", 352, 66, GOLD2 if hold else RED); pill(img, f"BTC 7д {c7:+.1f}%", 424, GREEN if c7 > 0 else RED, 30)
render("07_hold", fr_hold, ["💪"] if hold else ["😱"])

# 8-10: валюты СНГ
for name, sym, kind, cc, title, em in [("08_rub", "₽", "silver", "RU", "RUB", "🇷🇺"), ("09_kzt", "₸", "blue", "KZ", "KZT", "🇰🇿"), ("10_eur", "€", "silver", None, "EUR", "🇪🇺")]:
    if cc:
        o = R["official"][cc]["rates"]["USD"]; val = o["rate"]; chg = -o["diff"] / val * 100   # рост курса валюты к USD = валюта слабее
        txt = f"1$ = {fmt(val)}"
    else:
        val = R["world"]["EUR"]; chg = 0; txt = f"1$ = {val:.3f}€"
    sticker_coin(name, sym, kind, txt, title, chg, [em])
print("ГОТОВО", len(os.listdir(OUT)) // 2, "стикеров; рынок:", state, f"{avg:+.2f}%")
