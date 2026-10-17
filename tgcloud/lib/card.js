import { api, db } from 'sdk';
import { eq } from 'sdk/db';
import { cache } from '../schema.js';
import { getRates } from './rates.js';
import { RATES_URL } from './config.js';

const COOLDOWN = 20;          // секунд между картинками для одного пользователя
// Картинка живёт в отдельной ветке cards (одна версия, история репозитория не растёт)
const IMG_URL = 'https://raw.githubusercontent.com/dostonravshanov1006800-beep/cis-rates/cards/rates.png';

// Присылает свежую картинку курсов. Картинку рисует GitHub Actions при каждом обновлении, ключей не нужно.
export async function sendCard(q, chatId) {
  const now = Math.floor(Date.now() / 1000), key = 'img:' + chatId;
  const row = await db.select().from(cache).where(eq(cache.k, key)).get();
  if (row && now - row.at < COOLDOWN) {
    await api.answerCallbackQuery({ callback_query_id: q.id, text: 'Секунду, картинка уже отправлена 🙂' }).catch(() => {});
    return;
  }
  await db.insert(cache).values({ k: key, v: '1', at: now }).onConflictDoUpdate({ target: cache.k, set: { v: '1', at: now } }).run();
  await api.answerCallbackQuery({ callback_query_id: q.id, text: 'Готовлю картинку…' }).catch(() => {});
  let R = null; try { R = await getRates(); } catch (e) {}
  const stamp = R?.updated ? Date.parse(R.updated) : now * 1000;            // метка в ссылке: Telegram не отдаст старую копию из кэша
  try {
    await api.sendPhoto({ chat_id: chatId, photo: `${IMG_URL}?v=${stamp}`, caption: '⭐ <b>CIS Rates</b>: курсы сейчас\n<i>официальные ЦБ и рыночные</i>', parse_mode: 'HTML' });
  } catch (e) {
    await api.sendMessage({ chat_id: chatId, text: '🤔 Картинка пока не готова. Курсы смотри в разделе «💵 Курс валют».' }).catch(() => {});
  }
}
