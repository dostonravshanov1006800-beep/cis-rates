#!/usr/bin/env python3
"""Публикует сигналы в Telegram-канал, если курс заметно изменился.
Нужны секреты репозитория: BOT_TOKEN и CHANNEL_ID (например @cis_rates_alerts). Бот должен быть админом канала."""
import json, os, time, urllib.error, urllib.request, urllib.parse

TOKEN, CHANNEL = os.environ.get("BOT_TOKEN"), os.environ.get("CHANNEL_ID")
if not TOKEN or not CHANNEL:
    print("BOT_TOKEN/CHANNEL_ID не заданы — алерты пропущены"); raise SystemExit

# Пороги сигналов: валюты СНГ 0,3%, крипта 1% (3% срабатывали бы раз в несколько дней и канал молчал бы)
FIAT_THR, CRYPTO_THR = 0.003, 0.01
R = json.load(open("data/rates.json", encoding="utf-8"))
try: last = json.load(open("data/alert_state.json", encoding="utf-8"))
except Exception: last = {}

def fmt(n):
    d = 0 if abs(n) >= 100000 else (2 if abs(n) >= 1 else 4)
    return f"{n:,.{d}f}".replace(",", " ")

def usd_rate(cc):
    o = R["official"].get(cc, {}).get("rates", {}).get("USD")
    return o["rate"] if o else R["world"].get(R["countries"][cc]["cur"])

now, msgs = {}, []
for cc in ("UZ", "RU", "KZ", "UA", "BY"):           # страны с официальным курсом
    v = usd_rate(cc)
    if not v: continue
    now[f"{cc}:USD"] = v; c = R["countries"][cc]; p = last.get(f"{cc}:USD")
    if p and abs(v - p) / p >= 0.003:
        msgs.append(f"{'📈' if v > p else '📉'} {c['flag']} <b>USD</b>: {fmt(p)} → <b>{fmt(v)}</b> {c['sym']} ({(v/p-1)*100:+.2f}%)")
for x in R["crypto"]:
    if x["sym"] == "USDT": continue                    # стейблкоин: скачков нет
    k = f"c:{x['sym']}"; now[k] = x["usd"]; p = last.get(k)
    if p and abs(x["usd"] - p) / p >= CRYPTO_THR:
        msgs.append(f"{'🚀' if x['usd'] > p else '🔻'} <b>{x['sym']}</b>: ${fmt(p)} → <b>${fmt(x['usd'])}</b> ({(x['usd']/p-1)*100:+.1f}%)")

sent_ok = True
CARD = "docs/rates.png"
try: IMG = open(CARD, "rb").read()
except Exception: IMG = None

def multipart(fields, fname, blob):
    """собираем multipart/form-data вручную (без внешних библиотек)"""
    b = "----cisrates%d" % int(time.time() * 1000)
    out = b""
    for k, v in fields.items():
        out += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (b, k, v)).encode()
    out += ("--%s\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"%s\"\r\nContent-Type: image/png\r\n\r\n" % (b, fname)).encode() + blob + b"\r\n"
    out += ("--%s--\r\n" % b).encode()
    return out, "multipart/form-data; boundary=" + b

def send(text):
    """сначала фото с карточкой (подпись до 1024 символов), при неудаче обычный текст; возвращает True при доставке"""
    for attempt in range(3):
        try:
            if IMG and len(text) <= 1024:
                body, ct = multipart({"chat_id": CHANNEL, "caption": text, "parse_mode": "HTML"}, "rates.png", IMG)
                req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data=body, headers={"Content-Type": ct})
            else:
                data = urllib.parse.urlencode({"chat_id": CHANNEL, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
                req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=data)
            urllib.request.urlopen(req, timeout=40); return True
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            if e.code == 429:                                       # слишком часто: ждём сколько просит Telegram
                try: time.sleep(min(30, json.loads(body)["parameters"]["retry_after"] + 1))
                except Exception: time.sleep(5)
            else:
                print("ошибка отправки:", e.code, body[:120]); time.sleep(2)
                if IMG and e.code == 400: globals()["IMG"] = None   # фото не принято: дальше обычным текстом, чтобы сигнал дошёл
        except Exception as e:
            print("ошибка отправки:", e); time.sleep(2)
    return False

if msgs:
    # подпись к фото ограничена 1024 символами: режем на пачки по этому лимиту
    chunks, cur = [], ""
    HEAD, FOOT = "⚡ <b>Сигнал CIS Rates</b>\n\n", "\n🤖 @Well_Currency_bot"
    LIM = 1024 - len(HEAD) - len(FOOT) - 10
    for m in msgs:
        if cur and len(cur) + len(m) + 1 > LIM: chunks.append(cur); cur = ""
        cur += m + "\n"
    chunks.append(cur)
    for i, ch in enumerate(chunks):
        if send(HEAD + ch + FOOT): print("отправлено", len(msgs), "сигналов, часть", i + 1, "(с картинкой)" if IMG else "(текстом)")
        else: sent_ok = False; print("СИГНАЛ НЕ ДОСТАВЛЕН, повторим в следующем цикле")

# базу сравнения обновляем только при заметном движении И только если сигнал доставлен
# (иначе при сбое Telegram скачок был бы потерян навсегда)
keep = dict(last)
if sent_ok:
    for k, v in now.items():
        thr = CRYPTO_THR if k.startswith("c:") else FIAT_THR
        if k not in keep or abs(v - keep[k]) / keep[k] >= thr: keep[k] = v
json.dump(keep, open("data/alert_state.json", "w"))
