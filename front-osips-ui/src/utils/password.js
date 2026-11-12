export function passwordByteLimit(value) {
  return new TextEncoder().encode(String(value || '')).length <= 72 || 'Пароль слишком длинный: максимум 72 байта UTF-8'
}
