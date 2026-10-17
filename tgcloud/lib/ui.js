import { FLAG, OFF, rate, convert, toUSD } from './rates.js';
import { ALERT_CHANNEL } from './config.js';

export const fmt = (n, d) => {
  if (n == null || isNaN(n)) return '—';
  const a = Math.abs(n); d = d ?? (a >= 100000 ? 0 : a < 0.001 ? 6 : a < 0.1 ? 5 : a < 1 ? 4 : 2);
  return n.toLocaleString('ru-RU', { minimumFractionDigits: d, maximumFractionDigits: d }).replace(/[\u00a0\u202f]/g, ' ');
};
const arrow = d => d > 0 ? '🟢▲' : d < 0 ? '🔴▼' : '⚪';
export const btn = (text, data) => ({ text, callback_data: data });
const kb = rows => ({ inline_keyboard: rows });
const upd = R => R.updated.slice(11, 16) + ' UTC';
const BACK = [btn('« Меню', 'menu')];

export function menu(R, cc) {
  const c = R.countries[cc], r = rate(R, cc, 'USD') || { r: 1, d: 0, src: '' };
  return [`⭐ <b>CIS Rates</b> — курсы СНГ и Европы 24/7\n\n${c.flag} ${c.name}: <b>1 USD = ${fmt(r.r)} ${c.sym}</b> ${arrow(r.d)}\n<i>${r.src} · ${upd(R)}</i>\n\nВыбери раздел 👇`,
    kb([[btn('💵 Курс валют', 'cur'), btn('🎯 Подбор', 'pick')],
        [btn('₿ Крипта', 'cry:0'), btn('🗂 Каталог стран', 'cat:cis')],
        [btn('💱 Конвертер', 'conv'), btn('🔔 Алерты', 'alerts')],
        [btn('🌍 Моя страна', 'ctry'), btn('ℹ️ О боте', 'about')]])];
}

export function cur(R, cc) {
  const c = R.countries[cc], L = [`${c.flag} <b>${c.name}</b> · сколько стоит в ${c.sym}\n`]; let src = '';
  for (const x of OFF) { const r = rate(R, cc, x); if (!r) continue; src ||= r.src;
    L.push(`${FLAG[x] || ''} <b>${x}</b>  ${fmt(r.r)} ${arrow(r.d)}${r.d ? ' ' + Math.abs(r.d).toFixed(2) : ''}`); }
  L.push(`\n<i>${src} · ${upd(R)}</i>`);
  return [L.join('\n'), kb([[btn('🌍 Другая страна', 'ctry'), btn('🔄', 'cur')], BACK])];
}

export function ctry(R, region) {
  const cs = Object.entries(R.countries).filter(([, c]) => !region || c.region === region), rows = []; let row = [];
  for (const [k, c] of cs) { row.push(btn(`${c.flag} ${c.name}`, 'cc:' + k)); if (row.length === 2) { rows.push(row); row = []; } }
  if (row.length) rows.push(row);
  rows.unshift([btn(region === 'cis' ? '• СНГ •' : 'СНГ', 'ctry:cis'), btn(region === 'eu' ? '• Европа •' : 'Европа', 'ctry:eu')]);
  rows.push(BACK);
  return ['🌍 <b>Выбери страну</b>\nВсе курсы будут в её валюте:', kb(rows)];
}

export function catalog(R, region) {
  const cs = Object.entries(R.countries).filter(([, c]) => c.region === region);
  const L = [`🗂 <b>Каталог · ${region === 'cis' ? 'СНГ' : 'Европа'}</b>\n<i>1 USD в местной валюте</i>\n`];
  for (const [k, c] of cs) { const r = rate(R, k, 'USD'); if (!r) continue;
    L.push(`${c.flag} <b>${c.name}</b>  ${fmt(r.r)} ${c.sym} ${r.off ? '🏛' : ''}${r.d ? arrow(r.d) : ''}`); }
  L.push(`\n🏛 — официальный курс ЦБ · остальное рыночное\n<i>${upd(R)}</i>`);
  return [L.join('\n'), kb([[btn(region === 'cis' ? '• СНГ •' : 'СНГ', 'cat:cis'), btn(region === 'eu' ? '• Европа •' : 'Европа', 'cat:eu')], [btn('🎯 Подбор', 'pick'), BACK[0]]])];
}

export function pick(R, amt, src, region, cc) {
  const base = toUSD(R, src), usd = amt * base;
  if (!base) return ['🤔 Не знаю такую валюту. Пример: <code>500 usd</code>, <code>20000 rub</code>', kb([BACK])];
  const rows = Object.entries(R.countries).filter(([, c]) => region === 'all' || c.region === region).map(([k, c]) => {
    const o = rate(R, k, 'USD'); return { k, c, got: convert(R, amt, src, c.cur, k), off: !!o?.off };
  }).filter(x => x.got != null && x.c.cur !== src);
  const names = { all: 'Всё', cis: 'СНГ', eu: 'Европа' };
  const L = [`🎯 <b>Подбор обмена</b>\n${fmt(amt)} ${src} ≈ <b>$${fmt(usd)}</b>\n`];
  const group = (title, reg) => { const part = rows.filter(x => x.c.region === reg); if (!part.length) return;
    L.push(`<b>${title}</b>`); for (const x of part) L.push(`${x.c.flag} ${x.c.name} — <b>${fmt(x.got)} ${x.c.sym}</b>${x.off ? ' 🏛' : ''}`); L.push(''); };
  if (region !== 'eu') group('🌏 СНГ', 'cis'); if (region !== 'cis') group('🇪🇺 Европа', 'eu');
  const f = s => R.crypto.find(x => x.sym === s);
  const cr = [f('USDT') && `${fmt(usd / f('USDT').usd)} USDT`, f('TON') && `${fmt(usd / f('TON').usd)} TON`, f('BTC') && `${fmt(usd / f('BTC').usd, 6)} BTC`].filter(Boolean);
  if (cr.length) L.push(`₿ <b>Крипто-маршрут</b>: ${cr.join(' · ')}`);
  L.push(`\n<i>🏛 официальный курс ЦБ · остальное рыночное · ${upd(R)}</i>`);
  const sw = r => btn(region === r ? `• ${names[r]} •` : names[r], `pk:${amt}:${src}:${r}`);
  return [L.join('\n'), kb([[sw('all'), sw('cis'), sw('eu')],
    [btn('×10', `pk:${amt * 10}:${src}:${region}`), btn('÷10', `pk:${amt / 10}:${src}:${region}`), btn('USD', `pk:${amt}:USD:${region}`), btn('EUR', `pk:${amt}:EUR:${region}`), btn('RUB', `pk:${amt}:RUB:${region}`)],
    [btn('🗂 Каталог', 'cat:cis'), BACK[0]]])];
}

export const pickHelp = () => ['🎯 <b>Подбор обмена</b>\n\nНапиши сумму и валюту, и я покажу, сколько это будет в каждой стране СНГ и Европы + крипто-маршрут:\n\n<code>500 usd</code>\n<code>100000 rub</code>\n<code>2000 eur</code>\n\nИли выбери готовую сумму 👇',
  kb([[btn('💵 100 USD', 'pk:100:USD:all'), btn('💶 500 EUR', 'pk:500:EUR:all')], [btn('🇷🇺 50000 RUB', 'pk:50000:RUB:all'), btn('🇰🇿 500000 KZT', 'pk:500000:KZT:all')], BACK])];

export function cry(R, p) {
  const P = 8, cs = R.crypto, pages = Math.ceil(cs.length / P); p = Math.max(0, Math.min(p, pages - 1));
  const L = ['₿ <b>Криптовалюты</b> · топ по капитализации\n'];
  cs.slice(p * P, (p + 1) * P).forEach((x, i) => L.push(`${p * P + i + 1}. <b>${x.sym}</b>  $${fmt(x.usd)}  ${x.ch24h >= 0 ? '🟢' : '🔴'} ${x.ch24h > 0 ? '+' : ''}${x.ch24h}%`));
  L.push(`\n<i>24ч · CoinGecko · ${upd(R)} · ${p + 1}/${pages}</i>`);
  const nav = []; if (p > 0) nav.push(btn('◀️', 'cry:' + (p - 1))); nav.push(btn('🔄', 'cry:' + p)); if (p < pages - 1) nav.push(btn('▶️', 'cry:' + (p + 1)));
  return [L.join('\n'), kb([nav, BACK])];
}

export const conv = () => ['💱 <b>Конвертер</b>\n\nПиши в чат пару валют:\n<code>5000 rub uzs</code>\n<code>0.5 btc usd</code>\n<code>1000 ton rub</code>\n\nА просто <code>500 usd</code> откроет <b>подбор</b> по всем странам СНГ и Европы.\n\nПоддерживаются 24 валюты и топ-20 крипты.', kb([[btn('🎯 Подбор', 'pick'), BACK[0]]])];
export const about = () => ['⭐ <b>CIS Rates</b>\n\n• 24 страны: СНГ + Европа\n• Официальные ЦБ: 🇺🇿 🇷🇺 🇰🇿 🇺🇦 🇧🇾\n• ТОП-20 криптовалют\n• Подбор лучшего обмена, конвертер, алерты\n• Обновление каждые 5 минут\n\n/start /rates /pick /crypto /catalog', kb([BACK])];
export const alertsScreen = () => [`🔔 <b>Сигналы о скачках курса</b>\n\nПодпишись на канал: бот публикует там мгновенные сигналы, когда USD в СНГ меняется ≥0.3% или BTC/ETH/TON/SOL ≥3%.\n\nУведомления приходят всем подписчикам канала, настраивать ничего не нужно.`,
  { inline_keyboard: [[{ text: '📢 Открыть канал', url: `https://t.me/${ALERT_CHANNEL}` }], [btn('« Меню', 'menu')]] }];

// парсер «500 usd», «5000 rub uzs»
const ALIAS = {'доллар':'USD','долл':'USD','доллары':'USD','$':'USD','бакс':'USD','евро':'EUR','€':'EUR','руб':'RUB','рубль':'RUB','рублей':'RUB','₽':'RUB',
  'сум':'UZS','сумов':'UZS','тенге':'KZT','₸':'KZT','гривна':'UAH','грн':'UAH','юань':'CNY','лира':'TRY','фунт':'GBP','злотый':'PLN','франк':'CHF',
  'биткоин':'BTC','биткойн':'BTC','тон':'TON','эфир':'ETH','солана':'SOL'};
const norm = w => { w = w.toLowerCase().replace(/[.,]$/, ''); return ALIAS[w] || w.toUpperCase(); };
export function parse(text) {
  const m = text.match(/^\s*([\d\s]+(?:[.,]\d+)?)\s*([^\s\d]+)(?:\s+(?:в|to|->|→)?\s*([^\s\d]+))?\s*$/); if (!m) return null;
  const amt = parseFloat(m[1].replace(/\s/g, '').replace(',', '.')); if (!amt) return null;
  return { amt, src: norm(m[2]), dst: m[3] ? norm(m[3]) : null };
}
export { convert, upd };
