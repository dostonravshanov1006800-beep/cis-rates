#!/usr/bin/env python3
"""Заменяет стикеры в премиум-паке CIS Rates на свежие (по текущим курсам).
Нужны секреты: BOT_TOKEN, STICKER_OWNER_ID. Набор создаётся один раз вручную."""
import json, os, sys, time, urllib.request, urllib.parse, uuid, glob

T, OWNER = os.environ.get("BOT_TOKEN"), os.environ.get("STICKER_OWNER_ID")
NAME = os.environ.get("STICKER_SET", "cisrates_v1_by_Well_Currency_bot")
if not T or not OWNER: print("BOT_TOKEN/STICKER_OWNER_ID не заданы — пропуск"); sys.exit(0)

def call(method, fields=None, files=None):
    b = uuid.uuid4().hex; body = b""
    for k, v in (fields or {}).items(): body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for k, (fn, data) in (files or {}).items(): body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{fn}"\r\nContent-Type: video/webm\r\n\r\n'.encode() + data + b"\r\n"
    body += f"--{b}--\r\n".encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{T}/{method}", body, {"Content-Type": f"multipart/form-data; boundary={b}"})
    try: return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e: return json.load(e)

cur = call("getStickerSet", {"name": NAME})
if not cur.get("ok"): print("набор не найден:", cur); sys.exit(1)
stickers = cur["result"]["stickers"]
files = sorted(glob.glob("design/pack/*.webm")); print("в наборе:", len(stickers), "| новых файлов:", len(files))
if len(stickers) != len(files): print("число стикеров не совпадает — замена пропущена"); sys.exit(1)
ok = bad = 0
for old, f in zip(stickers, files):
    em = json.load(open(f.replace(".webm", ".json")))["emoji"]
    for attempt in range(3):
        r = call("replaceStickerInSet", {"user_id": OWNER, "name": NAME, "old_sticker": old["file_id"],
                 "sticker": json.dumps({"sticker": "attach://s", "format": "video", "emoji_list": em})}, {"s": (os.path.basename(f), open(f, "rb").read())})
        if r.get("ok"): ok += 1; break
        time.sleep(4)
    else: bad += 1; print("не заменён:", os.path.basename(f), r.get("description"))
    time.sleep(1.2)
print(f"обновлено {ok}, ошибок {bad}")
sys.exit(1 if bad > 3 else 0)
