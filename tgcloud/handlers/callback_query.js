import { api, BotApiError } from 'sdk';
import { route } from '../lib/router.js';
import { setCountry } from '../lib/users.js';
import { sendCard } from '../lib/card.js';

export default async function (q) {
  if (!q.message) return;
  const chatId = q.message.chat.id, mid = q.message.message_id; let data = q.data || 'menu', note = '';
  if (data === 'img') { await sendCard(q, chatId); return; }
  if (data.startsWith('cc:')) { await setCountry(chatId, data.slice(3)); note = 'Страна выбрана ✅'; data = 'cur'; }
  const [text, markup] = await route(chatId, data);
  await api.answerCallbackQuery({ callback_query_id: q.id, text: note }).catch(() => {});
  try {
    await api.editMessageText({ chat_id: chatId, message_id: mid, text, parse_mode: 'HTML', reply_markup: markup, link_preview_options: { is_disabled: true } });
  } catch (e) {
    if (!(e instanceof BotApiError && /not modified/i.test(e.description || ''))) throw e; // «🔄» без изменений — не ошибка
  }
}
