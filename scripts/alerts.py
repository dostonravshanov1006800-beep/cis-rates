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
if msgs:
    # Telegram ограничивает длину сообщения 4096 символами: режем на пачки
    chunks, cur = [], ""
    for m in msgs:
        if len(cur) + len(m) > 3500: chunks.append(cur); cur = ""
        cur += m + "\n"
    chunks.append(cur)
    for i, ch in enumerate(chunks):
        text = "⚡ <b>Сигнал CIS Rates</b>\n\n" + ch + "\n🤖 @Well_Currency_bot"
        data = urllib.parse.urlencode({"chat_id": CHANNEL, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
        ok = False
        for attempt in range(3):                                  # до 3 попыток
            try:
                urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=data), timeout=20)
                ok = True; break
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "ignore")
                if e.code == 429:                                   # слишком часто: ждём сколько просит Telegram
                    try: time.sleep(min(30, json.loads(body)["parameters"]["retry_after"] + 1))
                    except Exception: time.sleep(5)
                else: print("ошибка отправки:", e.code, body[:120]); time.sleep(2)
            except Exception as e:
                print("ошибка отправки:", e); time.sleep(2)
        if ok: print("отправлено", len(msgs), "сигналов, часть", i + 1)
        else: sent_ok = False; print("СИГНАЛ НЕ ДОСТАВЛЕН, повторим в следующем цикле")

# базу сравнения обновляем только при заметном движении И только если сигнал доставлен
# (иначе при сбое Telegram скачок был бы потерян навсегда)
keep = dict(last)
if sent_ok:
    for k, v in now.items():
        thr = CRYPTO_THR if k.startswith("c:") else FIAT_THR
        if k not in keep or abs(v - keep[k]) / keep[k] >= thr: keep[k] = v
json.dump(keep, open("data/alert_state.json", "w"))
