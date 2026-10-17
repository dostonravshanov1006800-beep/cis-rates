import { api } from 'sdk';
import { getRates } from '../lib/rates.js';
import { getUser, touch } from '../lib/users.js';
import * as ui from '../lib/ui.js';

export default async function (message) {
  const chatId = message.chat.id, text = (message.text || '').trim();
  if (!text || message.chat.type !== 'private') return;
  api.sendChatAction({ chat_id: chatId, action: 'typing' }).catch(() => {});
  const [R, u] = await Promise.all([getRates(), getUser(chatId)]);
  const cc = R.countries[u.country] ? u.country : 'UZ';
  const cmd = text.startsWith('/') ? text.split(/\s+/)[0].split('@')[0].toLowerCase() : '';
  let out;
  if (['/start', '/menu', '/help'].includes(cmd)) out = ui.menu(R, cc, message.from?.first_name);
  else if (['/rates', '/cur'].includes(cmd)) out = ui.cur(R, cc);
  else if (cmd === '/crypto') out = ui.cry(R, 0);
  else if (cmd === '/catalog') out = ui.catalog(R, 'cis');
  else if (cmd === '/pick') out = ui.pickHelp();
  else if (cmd === '/country') out = ui.ctry(R, 'cis');
  else if (cmd === '/alerts') out = ui.alertsScreen();
  else if (cmd === '/convert') out = ui.conv();
  else {
    const p = ui.parse(text);
    if (!p) out = ui.menu(R, cc);
    else if (p.dst) {
      const res = ui.convert(R, p.amt, p.src, p.dst, cc);
      out = res == null ? ['🤔 Не знаю такую валюту. Пример: <code>100 usd</code>', { inline_keyboard: [[ui.btn('« Меню', 'menu')]] }]
        : [`💱 ${ui.fmt(p.amt)} ${p.src} = <b>${ui.fmt(res)} ${p.dst}</b>\n<i>${ui.upd(R)}</i>`,
           { inline_keyboard: [[ui.btn('🎯 Подбор по странам', `pk:${p.amt}:${p.src}:all`)], [ui.btn('« Меню', 'menu')]] }];
    } else out = ui.pick(R, p.amt, p.src, 'all', cc);
  }
  await api.sendMessage({ chat_id: chatId, text: out[0], parse_mode: 'HTML', reply_markup: out[1], link_preview_options: { is_disabled: true } });
  await touch(chatId);
}
