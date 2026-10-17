#!/usr/bin/env python3
"""Публикует сигналы в Telegram-канал, если курс заметно изменился.
Нужны секреты репозитория: BOT_TOKEN и CHANNEL_ID (например @cis_rates_alerts). Бот должен быть админом канала."""
import json, os, urllib.request, urllib.parse

TOKEN, CHANNEL = os.environ.get("BOT_TOKEN"), os.environ.get("CHANNEL_ID")
if not TOKEN or not CHANNEL:
    print("BOT_TOKEN/CHANNEL_ID не заданы — алерты пропущены"); raise SystemExit

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
    if x["sym"] not in ("BTC", "ETH", "TON", "SOL"): continue
    k = f"c:{x['sym']}"; now[k] = x["usd"]; p = last.get(k)
    if p and abs(x["usd"] - p) / p >= 0.03:
        msgs.append(f"{'🚀' if x['usd'] > p else '🔻'} <b>{x['sym']}</b>: ${fmt(p)} → <b>${fmt(x['usd'])}</b> ({(x['usd']/p-1)*100:+.1f}%)")

if msgs:
    text = "⚡ <b>Сигнал CIS Rates</b>\n\n" + "\n".join(msgs) + "\n\n🤖 @Well_Currency_bot"
    data = urllib.parse.urlencode({"chat_id": CHANNEL, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
    try: urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=data), timeout=20); print("отправлено", len(msgs))
    except Exception as e: print("ошибка отправки:", e)

# базу сравнения обновляем только при заметном движении (иначе медленный тренд никогда не сработает)
keep = dict(last)
for k, v in now.items():
    thr = 0.03 if k.startswith("c:") else 0.003
    if k not in keep or abs(v - keep[k]) / keep[k] >= thr: keep[k] = v
json.dump(keep, open("data/alert_state.json", "w"))
