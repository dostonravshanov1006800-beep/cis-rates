import { register } from 'node:module';
register('./loader.mjs', import.meta.url);
import fs from 'fs';
const R = JSON.parse(fs.readFileSync('/app/conversations/6ad37e329db9e88d5cb968f9/uz-rates/data/rates.json','utf8'));
const ui = await import('./tgcloud/lib/ui.js');
const strip = h => h.replace(/<[^>]+>/g,'');
const num = s => parseFloat(s.replace(/\s/g,'').replace(',','.'));
// эталон вручную: официальные ЦБ где есть, иначе рынок
const usd = {}; for (const [k,c] of Object.entries(R.countries)) { const o=R.official[k]?.rates?.USD; usd[k]= o? o.rate : R.world[c.cur]; }
let bad=0, n=0;
for (const amtUsd of [1, 100, 500, 12345.67]) {
  const [txt] = ui.pick(R, amtUsd, 'USD', 'all', 'UZ'); const t = strip(txt);
  for (const [k,c] of Object.entries(R.countries)) {
    if (c.cur==='USD') continue;
    const line = t.split('\n').find(l => l.includes(c.name+' —')); if(!line) { console.log('✗ нет страны',c.name); bad++; continue; }
    const m = line.match(/—\s*([\d\s,]+)/); const got = num(m[1]); const exp = amtUsd*usd[k]; n++;
    const tol = exp>=100? 0.0006 : 0.006;   // округление вывода
    if (Math.abs(got-exp)/exp > tol) { bad++; console.log(`✗ ${amtUsd} USD → ${c.name}: бот ${got}, по ЦБ/рынку ${exp.toFixed(4)}`); }
  }
}
console.log('проверено строк:', n, '| расхождений:', bad);
// страны, у которых нет курса вообще
const miss = Object.entries(R.countries).filter(([k,c])=>c.cur!=='USD' && !usd[k]).map(([k])=>k); console.log('страны без курса:', miss.length?miss:'нет');
// конвертер: типовые фразы
const say = (t) => { const p=ui.parse(t); const r=ui.convert(R,p.amt,p.src,p.dst,'UZ'); return `${t.padEnd(18)} → ${r==null?'нет':r.toFixed(4)}`; };
console.log(say('100 usd uzs'), '| ручн:', (100*R.official.UZ.rates.USD.rate).toFixed(4));
console.log(say('100 eur uzs'), '| ручн:', (100*R.official.UZ.rates.EUR.rate).toFixed(4));
console.log(say('1000000 uzs usd'), '| ручн:', (1e6/R.official.UZ.rates.USD.rate).toFixed(4));
console.log(say('10000 rub uzs'), '| ручн:', (10000*R.official.UZ.rates.RUB.rate).toFixed(4));
console.log(say('1 btc usd'), '| ручн:', R.crypto.find(x=>x.sym==='BTC').usd);
console.log(say('1 btc uzs'), '| ручн:', (R.crypto.find(x=>x.sym==='BTC').usd*R.official.UZ.rates.USD.rate).toFixed(2));
