"""Общий движок отрисовки CIS Rates: баннер и стикеры. Только Pillow + numpy, без внешних API."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

F = lambda n, s, w=None: _font(n, s, w)
def _font(name, size, wght=None):
    p = {"mont": "fonts/Montserrat.ttf", "unb": "fonts/Unbounded.ttf", "inter": "fonts/Inter-Bold.otf"}[name]
    f = ImageFont.truetype(p, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f

GOLD1, GOLD2, GOLD3 = (255, 232, 160), (240, 180, 50), (150, 95, 15)
BLUE, GREEN, RED = (60, 140, 255), (40, 220, 140), (255, 80, 90)

def gradient(w, h, top, bot, angle=0):
    y = np.linspace(0, 1, h)[:, None, None]; x = np.linspace(0, 1, w)[None, :, None]
    t = (y * math.cos(angle) + x * math.sin(angle)); t = (t - t.min()) / (t.max() - t.min())
    a = np.array(top, float)[None, None, :]; b = np.array(bot, float)[None, None, :]
    return Image.fromarray((a + (b - a) * t).astype("uint8"), "RGB").convert("RGBA")

def glow(img, xy_r, color, strength=1.0, blur=60):
    """Мягкое свечение: круг с размытием поверх сцены (режим screen)."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    x, y, r = xy_r; d.ellipse([x - r, y - r, x + r, y + r], fill=color + (int(255 * strength),))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(img, layer)

def vgrad_mask(size, a0, a1):
    w, h = size; m = np.tile(np.linspace(a0, a1, h)[:, None], (1, w)); return Image.fromarray(m.astype("uint8"), "L")

def coin(size, symbol, kind="gold", font_scale=0.46, tilt=0):
    """3D-монета: ободок, градиент, внутренний рельеф, блик, символ с тенью."""
    S = size * 3; c = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    pal = {"gold": ((255, 240, 180), (235, 170, 40), (140, 85, 10), (70, 40, 5)),
           "blue": ((190, 225, 255), (70, 150, 255), (20, 70, 170), (8, 28, 80)),
           "silver": ((250, 252, 255), (190, 200, 215), (110, 120, 140), (50, 56, 70)),
           "green": ((190, 255, 225), (50, 215, 140), (10, 120, 80), (4, 50, 34)),
           "red": ((255, 205, 205), (255, 90, 100), (160, 30, 45), (70, 10, 20))}[kind]
    hi, mid, lo, dk = pal; m = S // 2
    d.ellipse([4, 4, S - 4, S - 4], fill=dk + (255,))
    ring = gradient(S, S, hi, lo, 0.9); mk = Image.new("L", (S, S), 0); ImageDraw.Draw(mk).ellipse([10, 10, S - 10, S - 10], fill=255)
    c.paste(ring, (0, 0), mk)
    inset = int(S * 0.075); face = gradient(S, S, mid, lo, 2.4); mk = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mk).ellipse([inset, inset, S - inset, S - inset], fill=255); c.paste(face, (0, 0), mk)
    d.ellipse([inset, inset, S - inset, S - inset], outline=hi + (255,), width=max(3, S // 90))
    inner = int(S * 0.15); d.ellipse([inner, inner, S - inner, S - inner], outline=dk + (120,), width=max(2, S // 140))
    for i in range(48):  # насечки по ободку
        a = i / 48 * 2 * math.pi; r1, r2 = m - S * 0.045, m - S * 0.015
        d.line([m + r1 * math.cos(a), m + r1 * math.sin(a), m + r2 * math.cos(a), m + r2 * math.sin(a)], fill=dk + (110,), width=max(2, S // 200))
    f = _font("unb", int(S * font_scale), 800)
    bb = d.textbbox((0, 0), symbol, font=f); tw, th = bb[2] - bb[0], bb[3] - bb[1]; tx, ty = m - tw / 2 - bb[0], m - th / 2 - bb[1]
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((tx + S * 0.012, ty + S * 0.02), symbol, font=f, fill=dk + (230,))
    c = Image.alpha_composite(c, sh.filter(ImageFilter.GaussianBlur(S * 0.006)))
    ImageDraw.Draw(c).text((tx - S * 0.006, ty - S * 0.008), symbol, font=f, fill=dk + (255,))
    tl = Image.new("RGBA", (S, S), (0, 0, 0, 0)); tg = gradient(S, S, hi, mid, 0); tm = Image.new("L", (S, S), 0)
    ImageDraw.Draw(tm).text((tx, ty), symbol, font=f, fill=255); tl.paste(tg, (0, 0), tm); c = Image.alpha_composite(c, tl)
    gl = Image.new("RGBA", (S, S), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)  # блик
    gd.ellipse([S * 0.14, S * 0.08, S * 0.66, S * 0.48], fill=(255, 255, 255, 95)); gl = gl.filter(ImageFilter.GaussianBlur(S * 0.03))
    cm = Image.new("L", (S, S), 0); ImageDraw.Draw(cm).ellipse([6, 6, S - 6, S - 6], fill=255)
    gl.putalpha(ImageChops.multiply(gl.getchannel("A"), cm)); c = Image.alpha_composite(c, gl)
    if tilt: c = c.resize((int(S * (1 - abs(tilt) * 0.0)), S)); 
    return c.resize((size, size), Image.LANCZOS)

def shadow_paste(base, sprite, xy, blur=24, op=150, off=(0, 18), tint=(0, 0, 0)):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); a = sprite.getchannel("A").point(lambda v: int(v * op / 255))
    blk = Image.new("RGBA", sprite.size, tint + (255,)); blk.putalpha(a); sh.paste(blk, (xy[0] + off[0], xy[1] + off[1]), blk)
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(blur)))
    base.alpha_composite(sprite, xy); return base

def candles(w, h, seed=7, n=34, up=True, drift=0.55):
    """Свечной график: тени, тела, градиентная заливка под линией."""
    rnd = random.Random(seed); S = 3; img = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    v, pts = 0.5, []
    for i in range(n):
        o = v; v += (rnd.random() - (0.5 - (drift - 0.5) * (1 if up else -1) * 0.55)) * 0.16; v = max(0.06, min(0.94, v)); cl = v
        hi = max(o, cl) + rnd.random() * 0.05; lo = min(o, cl) - rnd.random() * 0.05; pts.append((o, cl, hi, lo))
    cw = w * S / n
    for i, (o, cl, hi, lo) in enumerate(pts):
        col = GREEN if cl >= o else RED; X = i * cw + cw / 2
        Y = lambda p: (1 - p) * h * S
        d.line([X, Y(hi), X, Y(lo)], fill=col + (255,), width=max(2, S))
        d.rounded_rectangle([X - cw * 0.3, Y(max(o, cl)), X + cw * 0.3, Y(min(o, cl)) + 2], radius=3, fill=col + (255,))
    return img.resize((w, h), Image.LANCZOS)

def text_grad(img, xy, text, font, c1, c2, shadow=True):
    d = ImageDraw.Draw(img); bb = d.textbbox(xy, text, font=font); w, h = bb[2] - bb[0] + 8, bb[3] - bb[1] + 8
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((xy[0] + 3, xy[1] + 6), text, font=font, fill=(0, 0, 0, 200))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    m = Image.new("L", img.size, 0); ImageDraw.Draw(m).text(xy, text, font=font, fill=255)
    g = gradient(img.size[0], img.size[1], c1, c2, 0); img.paste(g, (0, 0), m); return bb
