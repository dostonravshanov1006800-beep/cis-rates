#!/usr/bin/env python3
"""Держит в канале ОДНО живое сообщение с карточкой курсов: бот не спамит, а редактирует фото (editMessageMedia).
Состояние (id сообщения) хранится в data/channel_card.json. Если сообщение удалили, публикуется новое."""
import json, os, sys, time, uuid, urllib.request, urllib.error

TOKEN, CHANNEL = os.environ.get("BOT_TOKEN"), os.environ.get("CHANNEL_ID")
if not TOKEN or not CHANNEL: print("BOT_TOKEN/CHANNEL_ID не заданы, пропуск"); sys.exit(0)
API = f"https://api.telegram.org/bot{TOKEN}/"
ST = "data/channel_card.json"
try: st = json.load(open(ST, encoding="utf-8"))
except Exception: st = {}

R = json.load(open("data/rates.json", encoding="utf-8"))
btc = next((c for c in R["crypto"] if c["sym"] == "BTC"), None)
hhmm = time.strftime("%H:%M", time.gmtime(time.time() + 5 * 3600))   # Ташкент UTC+5
cap = (f"📊 <b>CIS Rates</b> · живая карточка\n🕒 обновлено {hhmm} (Ташкент)"
       + (f"\n₿ BTC <b>${btc['usd']:,.0f}</b> ({btc['ch24h']:+.2f}% за 24ч)".replace(",", " ") if btc else "")
       + "\n\n🤖 @Well_Currency_bot · 🌐 сайт с ценами онлайн в меню бота")

def multipart(fields, fname, data):
    b = uuid.uuid4().hex; out = b""
    for k, v in fields.items(): out += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    out += f'--{b}\r\nContent-Disposition: form-data; name="photo"; filename="{fname}"\r\nContent-Type: image/png\r\n\r\n'.encode() + data + f"\r\n--{b}--\r\n".encode()
    return out, f"multipart/form-data; boundary={b}"

def call(method, fields, img=None):
    if img is not None:
        body, ct = multipart(fields, "rates.png", img)
        req = urllib.request.Request(API + method, data=body, headers={"Content-Type": ct})
    else:
        import urllib.parse
        req = urllib.request.Request(API + method, data=urllib.parse.urlencode(fields).encode())
    try:
        with urllib.request.urlopen(req, timeout=40) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read())
        except Exception: return {"ok": False, "description": f"http {e.code}"}
    except Exception as e: return {"ok": False, "description": str(e)}

img = open("docs/rates.png", "rb").read()
mid = st.get("message_id")
done = False
if mid:
    # редактируем существующее сообщение: подмена фото + подпись
    media = json.dumps({"type": "photo", "media": "attach://photo", "caption": cap, "parse_mode": "HTML"})
    r = call("editMessageMedia", {"chat_id": CHANNEL, "message_id": mid, "media": media}, img)
    if r.get("ok"): print("карточка обновлена, сообщение", mid); done = True
    elif "not modified" in str(r.get("description", "")).lower(): print("без изменений"); done = True
    else: print("не удалось отредактировать:", r.get("description"), "-> публикуем заново")
if not done:
    r = call("sendPhoto", {"chat_id": CHANNEL, "caption": cap, "parse_mode": "HTML", "disable_notification": "true"}, img)
    if r.get("ok"):
        st = {"message_id": r["result"]["message_id"], "posted": int(time.time())}
        json.dump(st, open(ST, "w")); print("карточка опубликована, сообщение", st["message_id"])
        # закрепляем, чтобы всегда была сверху
        call("pinChatMessage", {"chat_id": CHANNEL, "message_id": st["message_id"], "disable_notification": "true"})
    else:
        print("ОШИБКА публикации:", r.get("description")); sys.exit(0)   # не роняем весь запуск обновления
