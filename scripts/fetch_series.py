#!/usr/bin/env python3
"""7-дневные ряды для шкал: крипта (CoinGecko, 168 точек) и все валюты СНГ (дневные курсы). Без ключей.
Пишет data/series.json. Если источник недоступен, берёт прежние данные, чтобы шкалы не пропадали."""
import json, os, time, urllib.request
from datetime import datetime, timedelta, timezone

def get(url, t=25):
    req = urllib.request.Request(url, headers={"User-Agent": "cis-rates/1.0"})
    with urllib.request.urlopen(req, timeout=t) as r: return json.loads(r.read().decode())

P = "data/series.json"
try: old = json.load(open(P, encoding="utf-8"))
except Exception: old = {"crypto": {}, "fx": {}, "day": ""}
out = {"crypto": dict(old.get("crypto", {})), "fx": dict(old.get("fx", {})), "day": old.get("day", ""),
       "ts": int(time.time())}

def ds(v, n=48):  # прореживание до n точек, последнюю точку сохраняем
    if len(v) <= n: return [round(x, 8) for x in v]
    step = (len(v) - 1) / (n - 1)
    return [round(v[round(i * step)], 8) for i in range(n)]

# 1. Крипта: один запрос на все монеты
try:
    d = get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc"
            "&per_page=30&page=1&sparkline=true&price_change_percentage=24h")
    for c in d:
        sp = (c.get("sparkline_in_7d") or {}).get("price") or []
        if len(sp) > 10: out["crypto"][c["symbol"].upper()] = ds(sp)
    # монеты проекта, которых нет в топ-30 (TON, HYPE и т.д.): добираем по id
    rates = {}
    try: rates = json.load(open("data/rates.json", encoding="utf-8"))
    except Exception: pass
    need = [x for x in rates.get("crypto", []) if x["sym"] not in out["crypto"] or len(out["crypto"][x["sym"]]) < 10]
    ids = {"TON": "the-open-network", "HYPE": "hyperliquid", "XMR": "monero", "ZEC": "zcash", "TRX": "tron", "LEO": "leo-token"}
    for x in need:
        cid = ids.get(x["sym"]) or x["name"].lower().replace(" ", "-")
        try:
            j = get(f"https://api.coingecko.com/api/v3/coins/{cid}/market_chart?vs_currency=usd&days=7", 20)
            out["crypto"][x["sym"]] = ds([p[1] for p in j["prices"]]); time.sleep(1.5)
        except Exception as e: print("series", x["sym"], "FAIL:", e)
    print("series crypto:", len(out["crypto"]))
except Exception as e: print("series crypto FAIL:", e)

# 2. Валюты: дневные курсы за 7 дней. Тяжело, поэтому раз в сутки обновляем историю, а сегодняшнюю точку добавляем всегда.
CUR = ["uzs","rub","kzt","uah","byn","amd","azn","gel","kgs","tjs","mdl","tmt","eur","pln","czk","huf","ron","bgn","chf","gbp","sek","nok","dkk","rsd"]
today = datetime.now(timezone.utc).date()
if out["day"] != str(today) or not out["fx"]:
    days = {}
    for back in range(7, -1, -1):
        dt = today - timedelta(days=back)
        for base in (f"https://{dt}.currency-api.pages.dev/v1/currencies/usd.json",
                     f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{dt}/v1/currencies/usd.json"):
            try:
                days[str(dt)] = get(base, 15)["usd"]; break
            except Exception: continue
    if len(days) >= 4:
        keys = sorted(days)
        out["fx"] = {c.upper(): [round(days[k][c], 6) for k in keys if c in days[k]] for c in CUR}
        out["day"] = str(today); print("series fx дней:", len(keys))
    else: print("series fx FAIL: получено дней", len(days))
json.dump(out, open(P, "w", encoding="utf-8"), separators=(",", ":"))
