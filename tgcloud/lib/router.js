import { getRates } from './rates.js';
import * as ui from './ui.js';
import { getUser } from './users.js';

// callback_data → экран
export async function route(chatId, data) {
  const R = await getRates(), u = await getUser(chatId), cc = R.countries[u.country] ? u.country : 'UZ';
  const [a, ...rest] = data.split(':'), arg = rest.join(':');
  switch (a) {
    case 'menu': return ui.menu(R, cc);
    case 'cur': return ui.cur(R, cc);
    case 'ctry': return ui.ctry(R, arg || 'cis');
    case 'cat': return ui.catalog(R, arg || 'cis');
    case 'cry': return ui.cry(R, +arg || 0);
    case 'conv': return ui.conv();
    case 'about': return ui.about();
    case 'alerts': return ui.alertsScreen();
    case 'pick': return ui.pickHelp();
    case 'pk': { const [amt, src, reg] = arg.split(':'); return ui.pick(R, +amt, src, reg || 'all', cc); }
    default: return ui.menu(R, cc);
  }
}
