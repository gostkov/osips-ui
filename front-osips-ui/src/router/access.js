// Одинаковые правила для переходов по URL и отображения меню.
export function canAccessRoute(auth, meta) {
  if (meta.permissionsAny) return meta.permissionsAny.some((permission) => auth.can(permission))
  return auth.can(meta.permission)
}
