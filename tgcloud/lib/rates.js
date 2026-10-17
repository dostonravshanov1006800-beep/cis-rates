import { db, fetch } from 'sdk';
import { eq } from 'sdk/db';
import { cache } from '../schema.js';
import { RATES_URL, CACHE_SEC } from './config.js';

export const OFF = ['USD','EUR','RUB','CNY','TRY','GBP','AED','KZT','UAH','BYN','PLN','CHF'];
export const FLAG = {USD:'🇺🇸',EUR:'🇪🇺',RUB:'🇷🇺',CNY:'🇨🇳',TRY:'🇹🇷',GBP:'🇬🇧',AED:'🇦🇪',KZT:'🇰🇿',UAH:'🇺🇦',BYN:'🇧🇾',PLN:'🇵🇱',CHF:'🇨🇭',UZS:'🇺🇿'};

// Курсы: свежий кэш из SQLite → иначе GitHub Pages → иначе устаревший кэш
export async function getRates() {
  const now = Math.floor(Date.now() / 1000);
  const row = await db.select().from(cache).where(eq(cache.k, 'rates')).get();
  if (row && now - row.at < CACHE_SEC) return JSON.parse(row.v);
  try {
    const res = await fetch(RATES_URL + '?t=' + Math.floor(now / 60));
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const text = await res.text();
    const R = JSON.parse(text);
    await db.insert(cache).values({ k: 'rates', v: text, at: now })
      .onConflictDoUpdate({ target: cache.k, set: { v: text, at: now } }).run();
    return R;
  } catch (e) {
    console.error('rates fetch failed', String(e));
    if (row) return JSON.parse(row.v);
    throw e;
  }
}

export const toUSD = (R, c) => c === 'USD' ? 1 : R.world[c] ? 1 / R.world[c] : (R.crypto.find(x => x.sym === c) || {}).usd;

// сколько валюты страны cc стоит 1 ccy
export function rate(R, cc, ccy) {
  const cur = R.countries[cc].cur; if (ccy === cur) return null;
  const o = R.official[cc]?.rates?.[ccy];
  if (o) return { r: o.rate, d: o.diff, off: true, src: R.official[cc].src };
  const a = toUSD(R, ccy), b = R.world[cur];
  return a && b ? { r: a * b, d: 0, off: false, src: 'рыночный курс' } : null;
}

// Единое правило: всё считаем через USD, а «цена доллара» в каждой валюте берётся из ЦБ страны,
// если он её публикует, иначе из рынка. Тогда любые цепочки A→B→C замыкаются без расхождений.
export function localPerUsd(R, cc) {
  const cur = R.countries[cc]?.cur; if (!cur) return null;
  if (cur === 'USD') return 1;
  return R.official[cc]?.rates?.USD?.rate ?? R.world[cur] ?? null;
}
// сколько единиц валюты c даёт 1 USD (с приоритетом ЦБ выбранной страны)
function perUsd(R, c, cc) {
  if (c === 'USD') return 1;
  const off = R.official[cc]?.rates;
  if (off && c === R.countries[cc]?.cur) return localPerUsd(R, cc);          // валюта самой страны
  if (off?.[c] && off.USD) return off.USD.rate / off[c].rate;                // кросс из двух курсов ЦБ
  return R.world[c] ?? null;
}
export function convert(R, amt, src, dst, cc) {
  const k = s => R.crypto.find(x => x.sym === s);
  const usdOf = (c, a) => { const p = perUsd(R, c, cc); if (p) return a / p; const x = k(c); return x ? a * x.usd : null; };
  const fromUsd = (c, u) => { const p = perUsd(R, c, cc); if (p) return u * p; const x = k(c); return x ? u / x.usd : null; };
  // прямой официальный курс пары «валюта страны ↔ иностранная» даёт точное значение ЦБ
  const loc = R.countries[cc]?.cur;
  if (loc && R.official[cc]) {
    if (dst === loc && src !== loc) { const r = rate(R, cc, src); if (r?.off) return amt * r.r; }
    if (src === loc && dst !== loc) { const r = rate(R, cc, dst); if (r?.off) return amt / r.r; }
  }
  const u = usdOf(src, amt); if (u == null) return null;
  return fromUsd(dst, u);
}
