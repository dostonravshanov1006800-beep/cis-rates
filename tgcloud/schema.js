import { table, integer, text } from 'sdk/db';

// Пользователи: страна и подписка на алерты
export const users = table('users', {
  chatId:  integer('chat_id').primaryKey(),
  country: text('country').default('UZ'),
  alerts:  integer('alerts').default(0),
  seen:    integer('seen').default(0),
});

// Кэш курсов (одна строка), чтобы не ходить на GitHub Pages при каждом нажатии
export const cache = table('cache', {
  k:  text('k').primaryKey(),
  v:  text('v'),
  at: integer('at'),
});

