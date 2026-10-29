import { api } from 'sdk';
import { getRates } from '../lib/rates.js';
import * as ui from '../lib/ui.js';
import { APP_URL } from '../lib/config.js';

const plain = h => h.replace(/<[^>]+>/g, '');

// @infowallet_app 100 usd  →  быстрые карточки в любом чате
export default async function (q) {
  const R = await getRates(), text = (q.query || '').trim(), res = [];
  const BOT = 'infowallet_app', ICON = APP_URL + 'assets/avatar-256.webp';
  // кнопки под сообщением: мини-апп и бот (сообщение в группе подписывается «via @Well_Currency_bot»)
  const markup = { inline_keyboard: [[{ text: '🌐 Открыть Info Wallet', url: `https://t.me/${BOT}?startapp` }, { text: '🤖 Бот', url: `https://t.me/${BOT}` }]] };
  const add = (id, title, desc, html) => res.push({ type: 'article', id, title, description: desc, thumbnail_url: ICON, thumbnail_width: 256, thumbnail_height: 256,
    input_message_content: { message_text: html, parse_mode: 'HTML', link_preview_options: { is_disabled: true } }, reply_markup: markup });
  const p = ui.parse(text);
  if (p) {
    const dsts = p.dst ? [p.dst] : ['UZS', 'RUB', 'KZT', 'USD', 'EUR'].filter(c => c !== p.src);
    for (const d of dsts) {
      const v = ui.convert(R, p.amt, p.src, d, 'UZ'); if (v == null) continue;
      add(`c-${d}`, `${ui.fmt(p.amt)} ${p.src} = ${ui.fmt(v)} ${d}`, `CIS Rates · ${ui.upd(R)}`,
        `💱 ${ui.fmt(p.amt)} ${p.src} = <b>${ui.fmt(v)} ${d}</b>\n<i>CIS Rates · ${ui.upd(R)}</i>`);
    }
  }
  if (!text) add('card', 'Info Wallet · курсы валют СНГ и Европы', 'Официальные курсы и топ-20 крипты. Отправить карточку в чат',
    `🌍 <b>Info Wallet</b>\nКурсы валют СНГ и Европы и топ-20 крипты\n<i>${ui.upd(R)}</i>`);
  if (!res.length || !text) {
    for (const cc of ['UZ', 'RU', 'KZ', 'UA']) {
      const c = R.countries[cc], r = R.official[cc]?.rates?.USD; if (!r) continue;
      add(`r-${cc}`, `${c.flag} 1 USD = ${ui.fmt(r.rate)} ${c.sym}`, `Официальный курс · ${c.name}`,
        `${c.flag} <b>1 USD = ${ui.fmt(r.rate)} ${c.sym}</b>\n<i>${R.official[cc].src} · ${ui.upd(R)}</i>`);
    }
    for (const x of R.crypto.slice(0, 4)) add(`k-${x.sym}`, `${x.sym} $${ui.fmt(x.usd)}`, `${x.ch24h > 0 ? '+' : ''}${x.ch24h}% за 24ч`,
      `₿ <b>${x.sym}</b> $${ui.fmt(x.usd)} (${x.ch24h > 0 ? '+' : ''}${x.ch24h}% за 24ч)\n<i>CIS Rates</i>`);
  }
  await api.answerInlineQuery({ inline_query_id: q.id, results: res.slice(0, 20), cache_time: 30, is_personal: false });
}
