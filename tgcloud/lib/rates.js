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

export function convert(R, amt, src, dst, cc) {
  const loc = R.countries[cc]?.cur;
  if (loc) {
    if (dst === loc && src !== loc) { const r = rate(R, cc, src); if (r?.off) return amt * r.r; }
    if (src === loc && dst !== loc) { const r = rate(R, cc, dst); if (r?.off) return amt / r.r; }
  }
  const a = toUSD(R, src), b = toUSD(R, dst);
  return a && b ? amt * a / b : null;
}
