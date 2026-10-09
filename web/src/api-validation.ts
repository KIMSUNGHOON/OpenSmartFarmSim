export class ApiError extends Error {
  constructor(public readonly code:string, public readonly status:number|null = null) {
    super(code); this.name = 'ApiError';
  }
}
export function need(value:unknown):asserts value { if (!value) throw new ApiError('response_rejected'); }
export function object(value:unknown):value is Record<string,unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
export function member<T extends string>(value:unknown, options:readonly T[]):value is T {
  return typeof value === 'string' && options.some(option=>option===value);
}
export function date(value:unknown):value is string {
  return typeof value === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.test(value)
    && Number.isFinite(Date.parse(value)) && Number(value.slice(0,4)) >= 1
    && new Date(value.slice(0,19)+'Z').toISOString().slice(0,19) === value.slice(0,19);
}
export function uuid(value:unknown):value is string {
  return typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(value);
}
export function closed(value:Record<string,unknown>, keys:readonly string[]) {
  need(Object.keys(value).length === keys.length && keys.every(key=>Object.hasOwn(value,key)));
}
