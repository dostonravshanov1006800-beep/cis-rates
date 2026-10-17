import { db } from 'sdk';
import { eq, sql } from 'sdk/db';
import { users } from '../schema.js';

export async function getUser(chatId) {
  const u = await db.select().from(users).where(eq(users.chatId, chatId)).get();
  if (u) return u;
  await db.insert(users).values({ chatId, country: 'UZ', alerts: 0, seen: 0 }).onConflictDoNothing().run();
  return { chatId, country: 'UZ', alerts: 0, seen: 0 };
}
export const setCountry = (chatId, country) => db.update(users).set({ country }).where(eq(users.chatId, chatId)).run();
export const setAlerts = (chatId, on) => db.update(users).set({ alerts: on ? 1 : 0 }).where(eq(users.chatId, chatId)).run();
export const touch = chatId => db.update(users).set({ seen: sql`${users.seen} + 1` }).where(eq(users.chatId, chatId)).run();
