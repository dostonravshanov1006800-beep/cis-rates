// Загрузчик для тестов: подменяет модули 'sdk' и 'sdk/db' заглушками, чтобы проверять чистую логику (разбор, расчёты) без Telegram Serverless.
export async function resolve(spec, ctx, next) {
  if (spec === 'sdk' || spec === 'sdk/db') return { url: 'data:text/javascript,' + encodeURIComponent(STUBS[spec]), shortCircuit: true };
  return next(spec, ctx);
}
const STUBS = {
  'sdk': `export const db = new Proxy({}, { get: () => () => new Proxy(function(){}, { get: () => () => ({ get: async () => null, all: async () => [], run: async () => {} }), apply: () => ({}) }) });
          export const fetch = globalThis.fetch; export const api = new Proxy({}, { get: () => async () => ({}) }); export const kv = {};`,
  'sdk/db': `const col = () => new Proxy({}, { get: (t, k) => (k === 'primaryKey' || k === 'notNull' || k === 'default' || k === 'unique' || k === 'references') ? () => col() : undefined });
          export const table = (name, cols) => cols; export const integer = col, text = col, real = col, blob = col, index = () => ({});
          export const eq = () => ({}); export const sql = () => ({}); export const and = () => ({}); export const or = () => ({});
          export const desc = () => ({}); export const asc = () => ({}); export const gt = () => ({}); export const lt = () => ({}); export const inArray = () => ({});`,
};
