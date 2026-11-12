import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { createRouter, createMemoryHistory } from 'vue-router'
import { canAccessRoute } from '../src/router/access.js'
import { passwordByteLimit } from '../src/utils/password.js'

function makeRouter(permissions, initiallyLoaded = true) {
  const auth = {
    token: 'test-token',
    user: initiallyLoaded ? {} : null,
    get isAuthenticated() { return Boolean(this.token && this.user) },
    can(permission) { return !permission || (this.user && permissions.includes(permission)) },
    async fetchMe() { this.user = {} },
  }
  const source = readFileSync(new URL('../src/router/index.js', import.meta.url), 'utf8')
    .replace(/^import .*$/gm, '')
    .replace(/component: \(\) => import\('[^']+'\)/g, 'component: {}')
    .replace('export default router', 'return router')
  const router = new Function('createRouter', 'createWebHistory', 'useAuthStore', 'canAccessRoute', source)(
    createRouter, createMemoryHistory, () => auth, canAccessRoute,
  )
  return { router, auth }
}

for (const permissions of [['lb:read'], ['dispatcher:read'], ['lb:read', 'dispatcher:read']]) {
  test(`routing and navigation allow ${permissions.join(', ')}`, async () => {
    const { router, auth } = makeRouter(permissions, false)
    await router.push('/')
    assert.equal(router.currentRoute.value.path, '/dispatcher')
    const route = router.getRoutes().find(item => item.name === 'dispatcher')
    assert.equal(canAccessRoute(auth, route.meta), true)
    await router.push('/profile')
    await router.push('/dispatcher')
    assert.equal(router.currentRoute.value.path, '/dispatcher')
  })
}

for (const [permissions, fallback] of [
  [[], '/profile'],
  [['servers:read'], '/profile'],
  [['sipregs:read'], '/sip-regs'],
  [['rtpengine:read'], '/rtpengine'],
  [['dialplan:read'], '/dialplan'],
  [['blacklist:read'], '/blacklist'],
  [['address:read'], '/address'],
  [['servers:write'], '/servers'],
  [['users:manage'], '/users'],
  [['audit:read'], '/audit'],
]) {
  test(`dispatcher is denied without either permission; fallback ${fallback}`, async () => {
    const { router, auth } = makeRouter(permissions, false)
    await router.push('/')
    assert.equal(router.currentRoute.value.path, fallback)
    const route = router.getRoutes().find(item => item.name === 'dispatcher')
    assert.equal(canAccessRoute(auth, route.meta), false)
    await router.push('/dispatcher')
    assert.equal(router.currentRoute.value.path, fallback)
    await router.push('/login')
    assert.equal(router.currentRoute.value.path, fallback)
    await router.push('/unknown-page')
    assert.equal(router.currentRoute.value.path, fallback)
    await router.push('/profile')
    assert.equal(router.currentRoute.value.path, '/profile')
  })
}

test('password form limits UTF-8 bytes rather than characters', () => {
  for (const password of ['', 'a'.repeat(72), 'я'.repeat(36), '😀'.repeat(18)]) {
    assert.equal(passwordByteLimit(password), true)
  }
  for (const password of ['a'.repeat(73), 'я'.repeat(37), '😀'.repeat(19)]) {
    assert.equal(typeof passwordByteLimit(password), 'string')
  }
})
