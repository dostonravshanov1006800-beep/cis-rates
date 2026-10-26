#!/usr/bin/env python3
"""CIS Rates: официальные курсы ещё 16 центробанков. Без ключей. Каждый банк независим:
упал или вернул мусор, страна остаётся на рыночном курсе. Формат ответа как в fetch_rates:
{"cur": "AMD", "src": "ЦБ Армении", "rates": {"USD": {"rate": 360.88, "diff": 0}, ...}}
rate = сколько местной валюты за 1 единицу иностранной (как у cbu/cbr/nbu)."""
import json, re, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

WANT = ("USD", "EUR", "RUB", "CNY", "TRY", "GBP", "KZT", "UAH", "AED", "PLN", "CZK", "CHF")
UA = {"User-Agent": "Mozilla/5.0 (CIS-Rates/2.0)"}


def raw(url, timeout=18, enc="utf-8"):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read().decode(enc, "replace")


def num(x):
    return float(str(x).strip().replace(" ", "").replace("\xa0", "").replace(",", "."))


def pack(cur, src, rates):
    """оставляем только нужные валюты и только положительные числа"""
    d = {k: {"rate": v, "diff": 0.0} for k, v in rates.items() if k in WANT and isinstance(v, (int, float)) and v > 0}
    if not d:
        raise ValueError("пусто")
    return {"cur": cur, "src": src, "rates": d}


def cross(base_usd, quotes):
    """quotes: {код: сколько ЕДИНИЦ валюты за 1 USD или за 1 EUR...}. Здесь не используется."""
    raise NotImplementedError


# ---------- 1. банки, которые дают курс ВАЛЮТЫ К МЕСТНОЙ ----------
def am():  # Армения: цена 1 единицы в драмах
    j = json.loads(raw("https://cb.am/latest.json.php"))
    return pack("AMD", "ЦБ Армении", {k: num(v) for k, v in j.items() if v not in (None, "")})


def ge():  # Грузия: quantity единиц = rate лари
    j = json.loads(raw("https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/en/json"))
    d = {}
    for c in j[0]["currencies"]:
        q = float(c.get("quantity") or 1)
        d[c["code"]] = float(c["rate"]) / q
    return pack("GEL", "НБ Грузии", d)


def kg():  # Кыргызстан: Nominal единиц = Value сом, запятая как разделитель
    root = ET.fromstring(raw("https://www.nbkr.kg/XML/daily.xml").encode("utf-8", "ignore") if False else raw("https://www.nbkr.kg/XML/daily.xml", enc="cp1251").split("?>", 1)[-1])
    d = {}
    for c in root.iter("Currency"):
        d[c.get("ISOCode")] = num(c.findtext("Value")) / (num(c.findtext("Nominal")) or 1)
    return pack("KGS", "НБ Кыргызстана", d)


def tj():  # Таджикистан: Nominal единиц = Value сомони
    t = datetime.now(timezone.utc).date().isoformat()
    root = ET.fromstring(raw(f"https://nbt.tj/en/kurs/export_xml.php?date={t}&export=xmlout").split("?>", 1)[-1])
    d = {}
    for v in root.iter("Valute"):
        d[v.findtext("CharCode")] = num(v.findtext("Value")) / (num(v.findtext("Nominal")) or 1)
    return pack("TJS", "НБ Таджикистана", d)


def md():  # Молдова: Nominal единиц = Value лей
    t = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    root = ET.fromstring(raw(f"https://www.bnm.md/en/official_exchange_rates?get_xml=1&date={t}").split("?>", 1)[-1])
    d = {}
    for v in root.iter("Valute"):
        d[v.findtext("CharCode")] = num(v.findtext("Value")) / (num(v.findtext("Nominal")) or 1)
    return pack("MDL", "НБ Молдовы", d)


def pl():  # Польша, таблица A: mid = злотых за 1 единицу
    j = json.loads(raw("https://api.nbp.pl/api/exchangerates/tables/A/?format=json"))[0]["rates"]
    return pack("PLN", "НБ Польши", {r["code"]: float(r["mid"]) for r in j})


def cz():  # Чехия: Amount единиц = Rate крон
    d = {}
    for line in raw("https://www.cnb.cz/en/financial-markets/foreign-exchange-market/central-bank-exchange-rate-fixing/central-bank-exchange-rate-fixing/daily.txt").splitlines()[2:]:
        p = line.split("|")
        if len(p) == 5:
            d[p[3]] = num(p[4]) / (num(p[2]) or 1)
    return pack("CZK", "ЧНБ Чехии", d)


def ro():  # Румыния: Rate лей за 1 единицу (multiplier для некоторых валют)
    root = ET.fromstring(raw("https://curs.bnr.ro/nbrfxrates.xml").split("?>", 1)[-1])
    ns = {"n": root.tag.split("}")[0].strip("{")} if root.tag.startswith("{") else {}
    d = {}
    for r in root.iter():
        if r.tag.split("}")[-1] == "Rate" and r.get("currency"):
            m = float(r.get("multiplier") or 1)
            d[r.get("currency")] = num(r.text) / m
    return pack("RON", "НБ Румынии", d)


def bg():  # БНБ даёт «евро за 1 единицу». Лев жёстко привязан: 1 EUR = 1.95583 BGN (валютный совет), поэтому лев за единицу = REVERSERATE * 1.95583
    root = ET.fromstring(raw("https://www.bnb.bg/Statistics/StExternalSector/StExchangeRates/StERForeignCurrencies/index.htm?download=xml&search=&lang=EN").lstrip("\ufeff").split("?>", 1)[-1])
    d = {"EUR": 1.95583}
    for row in root.iter("ROW"):
        code, rev = row.findtext("CODE"), row.findtext("REVERSERATE")
        if code and rev and code != "Code":
            try:
                d[code] = num(rev) * 1.95583
            except ValueError:
                pass
    return pack("BGN", "БНБ Болгарии", d)


def rs():  # Сербия: exchange_middle = динаров за parity единиц
    j = json.loads(raw("https://kurs.resenje.org/api/v1/rates/today"))["rates"]
    return pack("RSD", "НБ Сербии", {r["code"]: float(r["exchange_middle"]) / (float(r.get("parity") or 1)) for r in j})


def ecb():  # ЕЦБ: к евро. EUR -> EUR=1; доллар и др.: 1 EUR = X валюты => 1 валюта = 1/X евро
    root = ET.fromstring(raw("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml").split("?>", 1)[-1])
    d = {"EUR": 1.0}
    for c in root.iter():
        if c.tag.split("}")[-1] == "Cube" and c.get("currency"):
            d[c.get("currency")] = 1.0 / float(c.get("rate"))
    return pack("EUR", "ЕЦБ", d)


def dk():  # Нацбанк Дании: rate = крон за 100 единиц валюты
    root = ET.fromstring(raw("https://www.nationalbanken.dk/_vti_bin/DN/DataService.svc/CurrencyRatesXML?lang=en").split("?>", 1)[-1])
    d = {}
    for c in root.iter("currency"):
        if c.get("code") and c.get("rate"):
            d[c.get("code")] = num(c.get("rate")) / 100.0
    return pack("DKK", "Нацбанк Дании", d)


def hu():  # MNB Венгрии: таблица HTML «код | название | единиц | курс»
    h = raw("https://www.mnb.hu/en/arfolyamok")
    d = {}
    for code, unit, rate in re.findall(r'<td class="fw-b">([A-Z]{3})</td>\s*<td>[^<]*</td>\s*<td>([\d.,]+)</td>\s*<td>([\d.,]+)</td>', h):
        d[code] = num(rate) / (num(unit) or 1)
    return pack("HUF", "МНБ Венгрии", d)


# ---------- 2. банки, у которых только курс к USD / нужен пересчёт ----------
def gb():  # Банк Англии: USD за 1 GBP  => фунтов за 1 USD = 1/x ; даём GBP-курс USD
    t = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%d/%b/%Y")
    csv = raw(f"https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom={t}&Dateto=now&SeriesCodes=XUDLUSS&CSVF=TN&UsingCodes=Y")
    last = [l for l in csv.strip().splitlines() if "," in l][-1].split(",")[1]
    usd_per_gbp = float(last)
    return pack("GBP", "Банк Англии", {"USD": 1.0 / usd_per_gbp})


def se():  # Riksbank: SEK за 1 USD
    j = json.loads(raw("https://api.riksbank.se/swea/v1/Observations/Latest/SEKUSDPMI"))
    return pack("SEK", "Риксбанк", {"USD": float(j["value"])})


def no():  # Norges Bank: NOK за 1 USD
    j = json.loads(raw("https://data.norges-bank.no/api/data/EXR/B.USD.NOK.SP?format=sdmx-json&lastNObservations=1"))
    obs = j["data"]["dataSets"][0]["series"]["0:0:0:0"]["observations"]
    return pack("NOK", "Норгес Банк", {"USD": float(list(obs.values())[-1][0])})


def ch():  # SNB: данные тяжёлые; берём курс USD/CHF через ЕЦБ-кросс в fetch (см. ниже), здесь пропускаем
    raise RuntimeError("SNB: используем кросс ЕЦБ")


# имя блока (код страны) -> функция
BANKS = {"AM": am, "GE": ge, "KG": kg, "TJ": tj, "MD": md, "PL": pl, "CZ": cz, "RO": ro, "BG": bg, "RS": rs,
         "EU": ecb, "GB": gb, "SE": se, "NO": no, "DK": dk, "HU": hu}


def fetch_all(log=print):
    out = {}
    for cc, fn in BANKS.items():
        try:
            out[cc] = fn()
        except Exception as e:  # ничего не роняем
            log(f"cb_more {cc}: {type(e).__name__}: {str(e)[:80]}")
    return out


if __name__ == "__main__":
    import time
    t = time.time()
    r = fetch_all()
    for cc, b in r.items():
        u = b["rates"].get("USD") or {}
        print(f"{cc} {b['cur']} {b['src']:<18} USD={u.get('rate')}  валют={len(b['rates'])}")
    print(f"готово: {len(r)}/{len(BANKS)} банков за {time.time()-t:.1f} с")
