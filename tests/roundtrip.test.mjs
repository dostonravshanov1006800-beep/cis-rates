import { register } from 'node:module';
register('./loader.mjs', import.meta.url);
import fs from 'fs';
const R = JSON.parse(fs.readFileSync('/app/conversations/6ad37e329db9e88d5cb968f9/uz-rates/data/rates.json','utf8'));
const { convert } = await import('./tgcloud/lib/rates.js');
const all=[...Object.keys(R.world),...R.crypto.map(x=>x.sym)];
let bad=0,n=0,worst=0;
for (const cc of ['UZ','RU','KZ','UA','BY','AM','GE','PL','DE']) for (const s of all) for (const d of all) {
  if(s===d) continue; const a=convert(R,1000,s,d,cc); if(a==null) continue; const b=convert(R,a,d,s,cc); n++;
  const err=Math.abs(b-1000)/1000; worst=Math.max(worst,err); if(err>1e-6){bad++; if(bad<=8)console.log(`✗ ${cc}: 1000 ${s}→${d}→${s} = ${b.toFixed(4)}`);}
}
console.log('кругов проверено:',n,'| не вернулись к исходной сумме:',bad,'| худшее отклонение',worst.toExponential(1));
// транзитивность: A→B→C = A→C
let tb=0,tn=0;
for (const cc of ['UZ','RU']) for (const [a,b,c] of [['USD','EUR','RUB'],['BTC','USD','UZS'],['EUR','RUB','UZS'],['RUB','UZS','USD'],['TON','EUR','KZT'],['UZS','USD','BTC']]) {
  const x=convert(R,500,a,c,cc), y=convert(R,convert(R,500,a,b,cc),b,c,cc); tn++;
  if(Math.abs(x-y)/x>1e-6){tb++;console.log(`✗ ${cc}: ${a}→${c}=${x.toFixed(4)} но через ${b}=${y.toFixed(4)} (${((y/x-1)*100).toFixed(3)}%)`)}
}
console.log('цепочек:',tn,'| несогласованных:',tb);
