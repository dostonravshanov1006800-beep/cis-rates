# ⭐ CIS Rates — курсы валют СНГ и Европы + Telegram-бот

Сайт + бот **@Well_Currency_bot**. Бесплатно: данные собирает GitHub Actions, сайт на GitHub Pages, бот работает на **Telegram Serverless** (серверы Telegram, ответ мгновенный).

```
GitHub Actions (каждые 5 мин) → data/rates.json → GitHub Pages (сайт + JSON)
                                                        ↓ fetch
                              Telegram Serverless (бот: кнопки, подбор, каталог, SQLite)
GitHub Actions → сигналы о скачках → Telegram-канал
```

## Шаг 1. GitHub: сайт и данные
1. Создай **публичный** репозиторий, залей все файлы (включая папку `.github`).
2. **Settings → Pages** → Source: `Deploy from a branch` → `main` / `/docs` → Save.
3. **Actions → Update rates → Run workflow**. Через минуту открой `https://ЛОГИН.github.io/РЕПО/data/rates.json` — должен показать JSON.

## Шаг 2. Бот на Telegram Serverless
Нужен Node.js 18+ (nodejs.org).
1. В `tgcloud/lib/config.js` впиши свой `RATES_URL` (адрес из шага 1.3) и `ALERT_CHANNEL`.
2. @BotFather → твой бот → **Serverless** (включено) → **CLI Access** → скопируй Access token (вид `app123:abc...`, это НЕ токен бота).
3. В папке проекта:
```bash
npm i -D @tgcloud/cli
npx tgcloud login      # вставь CLI-токен
npx tgcloud push       # залить код
npx tgcloud migrate    # создать таблицы (подтверди)
```
4. Напиши боту `/start`. Если молчит: `npx tgcloud webhook sync`, затем `npx tgcloud run handlers/message '{ chat: { id: 1, type: "private" }, text: "/start" }'` покажет логи.

## Шаг 3. Канал с сигналами (по желанию)
1. Создай публичный Telegram-канал, например `@cis_rates_alerts`, добавь бота админом.
2. В репозитории **Settings → Secrets and variables → Actions** добавь: `BOT_TOKEN` (токен бота) и `CHANNEL_ID` (`@cis_rates_alerts`).
3. В `tgcloud/lib/config.js` впиши этот же юзернейм в `ALERT_CHANNEL`, `npx tgcloud push`.

## Оформление
@BotFather → `/setuserpic` → `docs/assets/avatar.png`; `/setdescriptionpic` → `docs/assets/banner.png`.

## Что умеет бот
💵 Курс валют (твоя страна) · 🎯 Подбор (`500 usd` → сумма по всем странам СНГ и Европы + крипто-маршрут) · 🗂 Каталог СНГ/Европа · ₿ Крипта (листание) · 💱 Конвертер (`5000 rub uzs`) · 🌍 Выбор страны (запоминается) · 🔔 Канал сигналов.

## Монетизация
Реклама на сайте (Adsterra, Monetag, AdSense) · платные посты обменников в боте и канале · партнёрки бирж и P2P · SEO «курс доллара сегодня».
