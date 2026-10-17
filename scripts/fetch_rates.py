#!/usr/bin/env python3
"""CIS Rates: официальные курсы ЦБ + мировые пары + крипта. Без API-ключей."""
import json, os, re, time, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

def raw(url):
    req = urllib.request.Request(url, headers={"User-Agent": "cis-rates/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode()
def get(url): return json.loads(raw(url))

COUNTRIES = {  # код: (флаг, название, валюта, символ)
 "UZ":("🇺🇿","Узбекистан","UZS","сум"), "RU":("🇷🇺","Россия","RUB","₽"),
 "KZ":("🇰🇿","Казахстан","KZT","₸"),  "UA":("🇺🇦","Украина","UAH","₴"),
 "BY":("🇧🇾","Беларусь","BYN","Br"),  "AM":("🇦🇲","Армения","AMD","֏"),
 "AZ":("🇦🇿","Азербайджан","AZN","₼"),"GE":("🇬🇪","Грузия","GEL","₾"),
 "KG":("🇰🇬","Кыргызстан","KGS","сом"),"TJ":("🇹🇯","Таджикистан","TJS","сомони"),
 "MD":("🇲🇩","Молдова","MDL","лей"),  "TM":("🇹🇲","Туркменистан","TMT","манат"),
}
EUROPE = {  # Европа (EU = еврозона)
 "EU":("🇪🇺","Еврозона","EUR","€"), "PL":("🇵🇱","Польша","PLN","zł"), "CZ":("🇨🇿","Чехия","CZK","Kč"),
 "HU":("🇭🇺","Венгрия","HUF","Ft"), "RO":("🇷🇴","Румыния","RON","lei"), "BG":("🇧🇬","Болгария","BGN","лв"),
 "CH":("🇨🇭","Швейцария","CHF","Fr"), "GB":("🇬🇧","Британия","GBP","£"), "SE":("🇸🇪","Швеция","SEK","kr"),
 "NO":("🇳🇴","Норвегия","NOK","kr"), "DK":("🇩🇰","Дания","DKK","kr"), "RS":("🇷🇸","Сербия","RSD","дин"),
}
REGION = {k:"cis" for k in COUNTRIES}; REGION.update({k:"eu" for k in EUROPE}); COUNTRIES.update(EUROPE)
EXTRA = ["USD","EUR","CNY","TRY","AED","GBP","PLN","CZK","HUF","RON","BGN","CHF","SEK","NOK","DKK","RSD","JPY","KRW"]
out = {"updated": datetime.now(timezone.utc).isoformat(), "countries": {k:{"flag":v[0],"name":v[1],"cur":v[2],"sym":v[3],"region":REGION[k]} for k,v in COUNTRIES.items()},
       "world": {}, "official": {}, "crypto": []}

# 1. Мировые курсы (USD base) — основа для всех стран
try:
    w = get("https://open.er-api.com/v6/latest/USD")["rates"]
    keep = {v[2] for v in COUNTRIES.values()} | set(EXTRA)
    out["world"] = {k: round(v, 6) for k, v in w.items() if k in keep}
except Exception as e: print("world:", e)

# 2. Официальные курсы центробанков: валюта -> курс к местной валюте страны
def safe(name, fn):
    try: out["official"][name] = fn()
    except Exception as e: print(name, "error:", e)

def cbu():
    d = {}
    for c in get("https://cbu.uz/ru/arkhiv-kursov-valyut/json/"):
        if c["Ccy"] in ("USD","EUR","RUB","KZT","CNY","TRY","GBP","AED"):
            n = float(c["Nominal"]) or 1
            d[c["Ccy"]] = {"rate": float(c["Rate"])/n, "diff": float(c["Diff"])/n}
    return {"cur":"UZS","src":"ЦБ Узбекистана","rates":d}
def cbr():
    j = get("https://www.cbr-xml-daily.ru/daily_json.js")["Valute"]
    d = {c:{"rate":j[c]["Value"]/j[c]["Nominal"],"diff":(j[c]["Value"]-j[c]["Previous"])/j[c]["Nominal"]} for c in ("USD","EUR","CNY","TRY","KZT","UAH","BYN","AED","GBP") if c in j}
    return {"cur":"RUB","src":"ЦБ России","rates":d}
def nbu():
    d = {}
    for c in get("https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"):
        if c["cc"] in ("USD","EUR","GBP","CNY","TRY","PLN"): d[c["cc"]] = {"rate": c["rate"], "diff": 0}
    return {"cur":"UAH","src":"НБУ","rates":d}
def nbrb():
    d = {}
    for c in get("https://api.nbrb.by/exrates/rates?periodicity=0"):
        if c["Cur_Abbreviation"] in ("USD","EUR","RUB","CNY","TRY","GBP","UAH"):
            d[c["Cur_Abbreviation"]] = {"rate": c["Cur_OfficialRate"]/c["Cur_Scale"], "diff": 0}
    return {"cur":"BYN","src":"НБ Беларуси","rates":d}
def nbk():
    dt = (datetime.now(timezone.utc)+timedelta(hours=5)).strftime("%d.%m.%Y")
    root = ET.fromstring(raw(f"https://nationalbank.kz/rss/get_rates.cfm?fdate={dt}"))
    d = {}
    for it in root.iter("item"):
        t = it.findtext("title"); q = float(it.findtext("quant") or 1); r = float(it.findtext("description"))
        ch = it.findtext("change"); diff = float(ch)/q if ch else 0
        if t in ("USD","EUR","RUB","CNY","TRY","GBP","AED"): d[t] = {"rate": r/q, "diff": diff}
    return {"cur":"KZT","src":"Нацбанк Казахстана","rates":d}
for n, f in (("UZ",cbu),("RU",cbr),("UA",nbu),("BY",nbrb),("KZ",nbk)): safe(n, f)

# 3. Крипта: топ-20 по капитализации, USD + локальные цены считаются на сайте/в боте
try:
    d = get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=30&page=1&sparkline=false&price_change_percentage=1h,24h,7d")
    skip = {"usdc","usds","wbt","figr_heloc","steth","wsteth","weth","wbtc","usde","bsc-usd"}
    for x in d:
        if x["symbol"].lower() in skip: continue
        out["crypto"].append({"sym":x["symbol"].upper(),"name":x["name"],"usd":x["current_price"],
            "ch1h":round(x.get("price_change_percentage_1h_in_currency") or 0,2),
            "ch24h":round(x.get("price_change_percentage_24h_in_currency") or 0,2),
            "ch7d":round(x.get("price_change_percentage_7d_in_currency") or 0,2),
            "cap":x["market_cap"],"vol":x["total_volume"],"img":x["image"]})
    # TON отдельно, если не попал в топ
    if not any(c["sym"]=="TON" for c in out["crypto"]):
        t = get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=the-open-network&price_change_percentage=1h,24h,7d")[0]
        out["crypto"].insert(3, {"sym":"TON","name":"Toncoin","usd":t["current_price"],"ch1h":round(t.get("price_change_percentage_1h_in_currency") or 0,2),
            "ch24h":round(t.get("price_change_percentage_24h_in_currency") or 0,2),"ch7d":round(t.get("price_change_percentage_7d_in_currency") or 0,2),
            "cap":t["market_cap"],"vol":t["total_volume"],"img":t["image"]})
    out["crypto"] = out["crypto"][:20]
except Exception as e: print("crypto:", e)

# Если ЦБ не ответил, сохраняем прошлые значения
prev = {}
try: prev = json.load(open("data/rates.json", encoding="utf-8"))
except Exception: pass
for k, v in prev.get("official", {}).items(): out["official"].setdefault(k, v)
if not out["crypto"]: out["crypto"] = prev.get("crypto", [])
if not out["world"]: out["world"] = prev.get("world", {})

os.makedirs("data", exist_ok=True)
json.dump(out, open("data/rates.json","w",encoding="utf-8"), ensure_ascii=False, separators=(",",":"))

# История (до 600 точек): USD в местных валютах + крипта
hp = "data/history.json"; hist = []
try: hist = json.load(open(hp, encoding="utf-8"))
except Exception: pass
pt = {"t": int(time.time())}
for k,(f,n,cur,s) in COUNTRIES.items():
    if k in EUROPE and k not in ("EU","GB","PL"): continue
    o = out["official"].get(k,{}).get("rates",{}).get("USD")
    pt[cur] = round(o["rate"],4) if o else (round(out["world"].get(cur,0),4) or None)
for c in out["crypto"]:
    if c["sym"] in ("BTC","ETH","TON","SOL"): pt[c["sym"]] = c["usd"]
hist.append(pt); json.dump(hist[-600:], open(hp,"w"), separators=(",",":"))
print("ok", out["updated"], "official:", list(out["official"]), "crypto:", len(out["crypto"]))
