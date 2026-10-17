import { register } from 'node:module';
register('./loader.mjs', import.meta.url);
import fs from 'fs';
const R = JSON.parse(fs.readFileSync('/app/conversations/6ad37e329db9e88d5cb968f9/uz-rates/data/rates.json','utf8'));
const ui = await import('./tgcloud/lib/ui.js');
const strip = h => h.replace(/<[^>]+>/g,'');
console.log('--- разбор ввода');
for (const t of ['500 usd','500usd','500 $','$500','1 000 usd','1,5 btc usd','0.5 btc','1.000,50 eur','1 000,50 usd','500 долларов','100 евро в рубли','5000 rub uzs','5 000 000 uzs','-100 usd','0 usd','1e3 usd','100 usd usd','10 usdt rub','100 доллар сум','20000 руб','1000 сум','500 USD в сум','500 dollars']) {
  const p = ui.parse(t); console.log(JSON.stringify(t).padEnd(22), p ? `${p.amt} ${p.src}${p.dst?' → '+p.dst:''}` : 'НЕ РАЗОБРАНО');
}
console.log('--- автотест с ожидаемым');
const T=[['500 usd',500,'USD',null],['$500',500,'USD',null],['0.5 btc',0.5,'BTC',null],['0,5 btc',0.5,'BTC',null],['1.000,50 eur',1000.5,'EUR',null],['1,000.50 eur',1000.5,'EUR',null],
['1 000,50 usd',1000.5,'USD',null],['1 000 000 uzs',1e6,'UZS',null],['100 евро в рубли',100,'EUR','RUB'],['5000 rub uzs',5000,'RUB','UZS'],['500 долларов',500,'USD',null],
['1.5 ton usd',1.5,'TON','USD'],['2500 сум',2500,'UZS',null],['100 usd usd',100,'USD',null],['12.5 eth',12.5,'ETH',null],['1000 тенге в рубли',1000,'KZT','RUB'],['€100',100,'EUR',null],
['100 000 руб',1e5,'RUB',null],['3,5 usdt uzs',3.5,'USDT','UZS'],['500USD',500,'USD',null],['1000000 uzs',1e6,'UZS',null],['0.001 btc',0.001,'BTC',null],['1,234 usd',1.234,'USD',null]];
let f=0; for (const [t,a,s,d] of T){const p=ui.parse(t);const ok=p&&Math.abs(p.amt-a)<1e-9&&p.src===s&&p.dst===d;if(!ok){f++;console.log('✗',JSON.stringify(t),'→',JSON.stringify(p),'ожидали',a,s,d)}}
for (const t of ['-100 usd','0 usd','abc','привет','usd','','1e3 usd','100','5 6 usd','12.34.56.78 usd']) {const p=ui.parse(t); if(p){f++;console.log('✗ мусор принят:',JSON.stringify(t),JSON.stringify(p))}}
console.log(f?`ПРОВАЛОВ: ${f}`:'все '+(T.length+10)+' проверок ок');
