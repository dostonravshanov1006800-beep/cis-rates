import { register } from 'node:module';
register('./loader.mjs', import.meta.url);
import fs from 'fs';
const R = JSON.parse(fs.readFileSync('/app/conversations/6ad37e329db9e88d5cb968f9/uz-rates/data/rates.json','utf8'));
const ui = await import('./tgcloud/lib/ui.js');
const S = h => h.replace(/<[^>]+>/g,'').replace(/&amp;/g,'&');
const N = s => parseFloat(s.replace(/\s/g,'').replace(',','.'));
let bad=0;
const eq=(name,got,exp,tol=0.0006)=>{ if(Math.abs(got-exp)<0.051 && Math.abs(exp)<1) return; if(!(Math.abs(got-exp)/Math.abs(exp)<tol)){bad++;console.log('✗',name,'бот',got,'ожидалось',exp);} };
// 1. карточка монеты
for (const sym of ['BTC','ETH','TON','SOL','XRP','DOGE']) {
  const x=R.crypto.find(c=>c.sym===sym); if(!x) continue;
  const t=S(ui.coin(R,sym,'UZ')[0]);
  eq(sym+' цена $', N(t.match(/💵\s*\$([\d\s,]+)/)[1]), x.usd, x.usd>=100?0.0006:0.006);
  const loc=t.match(/🇺🇿\s*([\d\s,]+)/); if(loc) eq(sym+' в сумах', N(loc[1]), x.usd*R.official.UZ.rates.USD.rate, 0.0006);
  for (const [lab,v] of [['1ч',x.ch1h],['24ч',x.ch24h],['7д',x.ch7d]]) { const m=t.match(new RegExp(lab+'\\s+\\S+\\s*([+\\-−]?[\\d,]+)%')); if(m) eq(sym+' '+lab, N(m[1].replace('−','-')), v, 0.06); }
}
// 2. шапка подбора и крипто-маршрут
for (const [a,s] of [[500,'USD'],[500,'RUB'],[1000,'EUR'],[2,'BTC'],[1e6,'UZS']]) {
  const t=S(ui.pick(R,a,s,'all','UZ')[0]);
  const toUsd = s==='USD'?a : R.world[s]? a/R.world[s] : a*R.crypto.find(x=>x.sym===s).usd;
  const head=t.match(/≈\s*\$([\d\s,]+)/); eq(`шапка ${a} ${s}`, N(head[1]), toUsd, toUsd>=100?0.0006:0.006);
  const usdt=t.match(/([\d\s,]+) USDT/), ton=t.match(/([\d\s,]+) TON/), btc=t.match(/([\d\s,]+) BTC/);
  if(usdt) eq('USDT', N(usdt[1]), toUsd/R.crypto.find(x=>x.sym==='USDT').usd, 0.006);
  if(ton) eq('TON', N(ton[1]), toUsd/R.crypto.find(x=>x.sym==='TON').usd, 0.006);
  if(btc) eq('BTC', N(btc[1]), toUsd/R.crypto.find(x=>x.sym==='BTC').usd, 0.01);
}
// 3. каталог: 1 USD в валюте страны
for (const reg of ['cis','eu']) { const t=S(ui.catalog(R,reg)[0]);
  for (const [k,c] of Object.entries(R.countries)) { if(c.region!==reg||c.cur==='USD') continue;
    const line=t.split('\n').find(l=>l.includes(c.name)); if(!line){bad++;console.log('✗ нет в каталоге',c.name);continue;}
    const exp=R.official[k]?.rates?.USD?.rate ?? R.world[c.cur]; eq('каталог '+c.name, N(line.replace(c.name,'').match(/(\d[\d\s]*(?:,\d+)?)/)[1]), exp, exp>=100?0.0006:0.006); } }
console.log(bad?`НАЙДЕНО ПРОБЛЕМ: ${bad}`:'все числа на экранах совпадают с эталоном');
