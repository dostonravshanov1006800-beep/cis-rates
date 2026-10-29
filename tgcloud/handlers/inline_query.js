import { api } from 'sdk';
import { getRates } from '../lib/rates.js';
import * as ui from '../lib/ui.js';
import { APP_URL } from '../lib/config.js';

// @infowallet_app 100 usd | 0.5 btc | btc | доллар  →  карточки в любом чате (подпись «via @бот» ставит сам Telegram)
const BOT = 'infowallet_app', ICON = APP_URL + 'assets/avatar-256.webp';

// Эмодзи из пака RestrictedEmoji (видны владельцам Premium; остальные увидят обычный символ внутри тега)
const CE = { swap: ['💱', '5471899089425667918'], money: ['💰', '5375296873982604963'], up: ['📈', '5373001317042101552'], down: ['📉', '5361748661640372834'],
  chart: ['📊', '5431577498364158238'], coin: ['🪙', '5379600444098093058'], bank: ['🏦', '5264895611517300926'], rocket: ['🚀', '5445284980978621387'],
  gem: ['💎', '5471952986970267163'], bolt: ['⚡', '5431449001532594346'], globe: ['🌍', '5399898266265475100'], bell: ['🔔', '5242628160297641831'], fire: ['🔥', '5420315771991497307'] };
const em = k => `<tg-emoji emoji-id="${CE[k][1]}">${CE[k][0]}</tg-emoji>`;
const chg = v => (v > 0 ? '+' : '') + String(Math.round(v * 100) / 100).replace('.', ',') + '%';
const arrow = v => (v >= 0 ? em('up') : em('down'));

// расшифровка названий монет: «биткоин», «bitcoin», «btc» → BTC
const COIN_WORDS = {};
const FIAT_NAMES = { USD: 'Доллар США', EUR: 'Евро', RUB: 'Российский рубль', UZS: 'Узбекский сум', KZT: 'Казахстанский тенге', UAH: 'Украинская гривна', BYN: 'Белорусский рубль',
  CNY: 'Китайский юань', TRY: 'Турецкая лира', GBP: 'Британский фунт', AED: 'Дирхам ОАЭ', PLN: 'Польский злотый', CHF: 'Швейцарский франк', GEL: 'Грузинский лари', AMD: 'Армянский драм',
  AZN: 'Азербайджанский манат', KGS: 'Киргизский сом', TJS: 'Таджикский сомони', MDL: 'Молдавский лей', JPY: 'Японская иена', KRW: 'Южнокорейская вона', CZK: 'Чешская крона' };

export default async function (q) {
  const R = await getRates(), text = (q.query || '').trim(), res = [];
  const upd = ui.upd(R);
  // кнопки в один ряд на всю ширину: длинный текст не обрезается
  const markup = { inline_keyboard: [[ui.ico({ text: '🌐 Info Wallet', url: `https://t.me/${BOT}?startapp` })], [ui.ico({ text: '💱 Курсы и конвертер в боте', url: `https://t.me/${BOT}?start=rates` })]] };
  const seen = new Set();
  const add = (id, title, desc, html, thumb) => { if (seen.has(id) || res.length >= 40) return; seen.add(id);
    res.push({ type: 'article', id: String(id).slice(0, 60), title, description: desc, thumbnail_url: thumb || ICON, thumbnail_width: 256, thumbnail_height: 256,
      input_message_content: { message_text: html, parse_mode: 'HTML', link_preview_options: { is_disabled: true } }, reply_markup: markup }); };

  const coin = sym => R.crypto.find(x => x.sym === sym);
  const isCoin = c => !!coin(c);
  const isFiat = c => c === 'USD' || R.world[c] != null;
  const label = c => isCoin(c) ? c : (R.countries && Object.values(R.countries).find(x => x.cur === c)?.flag || (c === 'USD' ? '🇺🇸' : c === 'EUR' ? '🇪🇺' : '')) + ' ' + c;

  // карточка одной монеты
  const coinCard = x => {
    const loc = ['UZS', 'RUB', 'KZT'].map(c => { const v = ui.convert(R, 1, x.sym, c, 'UZ'); return v == null ? null : `${ui.fmt(v)} ${c}`; }).filter(Boolean).join('\n');
    add(`k-${x.sym}`, `${x.sym} · $${ui.fmt(x.usd)}`, `${chg(x.ch24h)} за 24ч · ${x.name}`,
      `${em('coin')} <b>${x.name} (${x.sym})</b>\n${em('money')} <b>$${ui.fmt(x.usd)}</b>\n${arrow(x.ch24h)} 1ч ${chg(x.ch1h)} · 24ч <b>${chg(x.ch24h)}</b> · 7д ${chg(x.ch7d)}\n${loc ? '\n' + loc + '\n' : ''}\n<i>Info Wallet · ${upd}</i>`, x.img);
  };
  // карточка валюты: курс к основным
  const fiatCard = c => {
    const to = ['UZS', 'RUB', 'KZT', 'EUR', 'USD'].filter(d => d !== c);
    const lines = to.map(d => { const v = ui.convert(R, 1, c, d, 'UZ'); return v == null ? null : `1 ${c} = <b>${ui.fmt(v)} ${d}</b>`; }).filter(Boolean);
    if (!lines.length) return;
    add(`f-${c}`, `${label(c)} · ${FIAT_NAMES[c] || c}`, lines[0].replace(/<[^>]+>/g, ''), `${em('bank')} <b>${FIAT_NAMES[c] || c}</b>\n${lines.join('\n')}\n\n<i>Info Wallet · ${upd}</i>`);
  };

  const p = ui.parse(text);
  if (p) {
    // сумма + валюта/монета: конвертация во все ключевые валюты И в крипту, включая доллар
    const fiatTo = ['USD', 'UZS', 'RUB', 'KZT', 'EUR', 'UAH', 'CNY', 'TRY', 'GBP', 'AED'];
    const coinTo = ['BTC', 'ETH', 'TON', 'USDT', 'SOL', 'BNB'];
    const dsts = p.dst ? [p.dst] : [...fiatTo, ...coinTo].filter(c => c !== p.src);
    for (const d of dsts) {
      if (!(isFiat(d) || isCoin(d))) continue;
      const v = ui.convert(R, p.amt, p.src, d, 'UZ'); if (v == null || !isFinite(v)) continue;
      const out = isCoin(d) && v < 1 ? ui.fmt(v, v < 0.0001 ? 8 : 6) : ui.fmt(v);
      add(`c-${p.src}-${d}`, `${ui.fmt(p.amt)} ${p.src} = ${out} ${d}`, `Info Wallet · ${upd}`,
        `${em('swap')} ${ui.fmt(p.amt)} ${p.src} = <b>${out} ${d}</b>\n<i>Info Wallet · ${upd}</i>`);
    }
    if (isCoin(p.src)) coinCard(coin(p.src));
  } else if (text) {
    // поиск по названию: монета или валюта (btc, bitcoin, ton, usd, доллар, рубль…)
    const w = text.toLowerCase();
    const code = ui.norm ? ui.norm(w) : w.toUpperCase();
    for (const x of R.crypto) if (x.sym.toLowerCase() === w || x.name.toLowerCase().includes(w) || x.sym === code) coinCard(x);
    if (isFiat(code)) fiatCard(code);
    for (const c of Object.keys(R.world)) if (c.toLowerCase().startsWith(w) || (FIAT_NAMES[c] || '').toLowerCase().includes(w)) fiatCard(c);
  }

  if (!res.length) {
    // пустой или непонятный запрос: визитка, доллар, топ-крипта, лидеры дня
    add('card', 'Info Wallet · курсы и крипта', 'Официальные курсы СНГ, Европы и топ-20 крипты',
      `${em('globe')} <b>Info Wallet</b>\nКурсы валют СНГ и Европы и топ-20 крипты\n\n<i>${upd}</i>`);
    const usd = ['UZ', 'RU', 'KZ', 'UA'].map(cc => { const c = R.countries[cc], r = R.official[cc]?.rates?.USD; return r ? { c, r } : null; }).filter(Boolean);
    if (usd.length) add('usd', `🇺🇸 1 USD = ${ui.fmt(usd[0].r.rate)} ${usd[0].c.sym}`, usd.map(u => `${u.c.flag} ${ui.fmt(u.r.rate)} ${u.c.sym}`).join(' · '),
      `${em('money')} <b>1 USD</b>\n` + usd.map(u => `${u.c.flag} <b>${ui.fmt(u.r.rate)} ${u.c.sym}</b> · ${u.c.name}`).join('\n') + `\n\n<i>${R.official.UZ?.src || 'ЦБ'} · ${upd}</i>`);
    const top = [...R.crypto].sort((a, b) => b.ch24h - a.ch24h);
    const best = top[0], worst = top[top.length - 1];
    add('movers', 'Лидеры дня', `${best.sym} ${chg(best.ch24h)} · ${worst.sym} ${chg(worst.ch24h)}`,
      `${em('fire')} <b>Лидеры 24ч</b>\n${em('up')} ${best.sym} <b>${chg(best.ch24h)}</b> ($${ui.fmt(best.usd)})\n${em('down')} ${worst.sym} <b>${chg(worst.ch24h)}</b> ($${ui.fmt(worst.usd)})\n\n<i>Info Wallet · ${upd}</i>`);
    for (const x of R.crypto) coinCard(x);
    for (const c of ['EUR', 'RUB', 'UZS', 'KZT', 'CNY', 'TRY']) fiatCard(c);
  }
  await api.answerInlineQuery({ inline_query_id: q.id, results: res.slice(0, 50), cache_time: 20, is_personal: false });
}
