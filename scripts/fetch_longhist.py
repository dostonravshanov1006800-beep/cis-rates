#!/usr/bin/env python3
"""Длинная история для графиков 1М / 3М / 1Г: запускается раз в сутки (GitHub Actions).

Валюты: курсы к USD за 365 дней (currency-api на jsDelivr), все валюты проекта, включая CNY/TRY/AED.
Крипта: цены за 365 дней (CoinGecko, дневные точки), все монеты проекта.
Пишет data/longhist.json. При сбое источника берёт прежние данные, график не пропадает.
Формат: {"ts":..., "days":[даты], "fx":{CODE:[курс за 1 USD по дням]}, "crypto":{SYM:[цена USD по дням]}}
"""
import json, os, sys, time, urllib.request, concurrent.futures as cf
from datetime import date, timedelta

N = 365
P = "data/longhist.json"
UA = {"User-Agent": "cis-rates/1.0"}

def get(url, t=25, tries=3):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last = e; time.sleep(1.2 * (i + 1))
    raise last

try: old = json.load(open(P, encoding="utf-8"))
except Exception: old = {}
out = {"ts": int(time.time()), "days": old.get("days", []), "fx": dict(old.get("fx", {})), "crypto": dict(old.get("crypto", {}))}

# ---------- валюты ----------
FX = ["UZS", "RUB", "KZT", "UAH", "BYN", "AMD", "AZN", "GEL", "KGS", "TJS", "MDL", "TMT",
      "EUR", "CNY", "TRY", "GBP", "CHF", "PLN", "AED", "CZK", "HUF", "RON", "BGN", "SEK", "NOK", "DKK", "RSD"]
today = date.today()
days = [(today - timedelta(days=N - 1 - k)).isoformat() for k in range(N)]

def one(d):
    u = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{d}/v1/currencies/usd.json"
    try: return d, get(u, 20, 2)["usd"]
    except Exception: return d, None

try:
    with cf.ThreadPoolExecutor(12) as ex: res = dict(ex.map(one, days))
    got = sum(1 for v in res.values() if v)
    print(f"валюты: получено {got} из {len(days)} дней")
    if got >= N * 0.8:
        series = {c: [] for c in FX}
        last = {}
        for d in days:
            u = res.get(d)
            for c in FX:
                v = u.get(c.lower()) if u else None
                if v and v > 0: last[c] = v          # пропуск дня закрываем предыдущим значением
                series[c].append(round(last[c], 6) if c in last else None)
        # убираем ведущие None (если валюта появилась позже)
        for c in FX:
            s = series[c]
            first = next((x for x in s if x is not None), None)
            series[c] = [x if x is not None else first for x in s] if first else []
        out["fx"] = {c: s for c, s in series.items() if s}
        out["days"] = days
    else:
        print("валюты: слишком мало дней, оставляю прежние данные")
except Exception as e:
    print("валюты FAIL:", e)

# ---------- крипта ----------
try: rates = json.load(open("data/rates.json", encoding="utf-8"))
except Exception: rates = {}
IDS = {"BTC": "bitcoin", "ETH": "ethereum", "USDT": "tether", "TON": "the-open-network", "BNB": "binancecoin", "XRP": "ripple",
       "SOL": "solana", "TRX": "tron", "ZEC": "zcash", "HYPE": "hyperliquid", "DOGE": "dogecoin", "XMR": "monero",
       "LINK": "chainlink", "LEO": "leo-token", "ADA": "cardano", "XLM": "stellar", "NEAR": "near", "BCH": "bitcoin-cash",
       "RAIN": "rain", "DAI": "dai"}
def cid(x): return IDS.get(x["sym"]) or x["name"].lower().replace(" ", "-")

def from_binance(sym):
    """свечи 1д с Binance (без ключа, лимиты щедрые): основной источник"""
    j = get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}USDT&interval=1d&limit={N}", 20, 2)
    return [float(k[4]) for k in j]            # цена закрытия дня

def from_gate(sym):
    j = get(f"https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair={sym}_USDT&interval=1d&limit={N}", 20, 2)
    return [float(k[2]) for k in j]            # [t, volume, close, high, low, open]

def from_gecko(x):
    j = get(f"https://api.coingecko.com/api/v3/coins/{cid(x)}/market_chart?vs_currency=usd&days={N}&interval=daily", 25, 1)
    return [p[1] for p in j["prices"] if p and p[1]]

CUR = {x["sym"]: x["usd"] for x in rates.get("crypto", []) if x.get("usd")}

def ok(pr, sym=None):
    """ряд годен: достаточно точек, цены положительные и последняя точка близка к текущей цене проекта (защита от мёртвых пар)"""
    if not (pr and len(pr) >= 30 and all(v and v > 0 for v in pr[-30:])): return False
    cur = CUR.get(sym)
    if cur and abs(pr[-1] / cur - 1) > 0.05:
        print("   отброшено", sym, "последняя точка", pr[-1], "против текущей", cur); return False
    return True

need_gecko = []
for x in rates.get("crypto", []):
    sym = x["sym"]; pr = None; src = ""
    if sym in ("USDT", "DAI"):                 # стейблкоины на биржах как база не торгуются: берём CoinGecko
        need_gecko.append(x); continue
    for name, fn in (("Binance", lambda: from_binance(sym)), ("Gate", lambda: from_gate(sym))):
        try:
            pr = fn()
            if ok(pr, sym): src = name; break
            pr = None
        except Exception: pr = None
    if pr: out["crypto"][sym] = [round(v, 8) for v in pr[-N:]]; print("крипта", sym, src, len(pr))
    else: need_gecko.append(x)

# что не нашлось на биржах (TON, XMR, DAI, USDT...) берём у CoinGecko с паузой и повтором при лимите
for x in need_gecko:
    sym = x["sym"]; pr = None
    for attempt in range(3):
        try: pr = from_gecko(x); break
        except Exception as e:
            if "429" in str(e): time.sleep(25 * (attempt + 1))
            else: break
    if ok(pr, sym): out["crypto"][sym] = [round(v, 8) for v in pr[-N:]]; print("крипта", sym, "CoinGecko", len(pr))
    else: print("крипта", sym, "нет данных, остаётся прежнее:", "есть" if sym in out["crypto"] else "нет")
    time.sleep(6)

for sym in list(out["crypto"]):
    if CUR.get(sym) and abs(out["crypto"][sym][-1] / CUR[sym] - 1) > 0.05:
        print("удалён негодный старый ряд", sym); del out["crypto"][sym]
os.makedirs("data", exist_ok=True)
json.dump(out, open(P, "w", encoding="utf-8"), separators=(",", ":"))
print("записано", P, os.path.getsize(P) // 1024, "КБ | валют", len(out["fx"]), "| монет", len(out["crypto"]))
