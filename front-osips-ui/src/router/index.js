import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true, title: 'Вход' },
  },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    children: [
      {
        path: '',
        redirect: () => {
          const auth = useAuthStore()
          if (auth.can('dispatcher:read')) return '/dispatcher'
          if (auth.can('dialplan:read')) return '/dialplan'
          return '/sip-regs'
        },
      },
      {
        path: 'dispatcher',
        name: 'dispatcher',
        component: () => import('@/views/DispatcherView.vue'),
        meta: { title: 'Распределение вызовов', icon: 'mdi-call-split', permission: 'dispatcher:read', nav: true },
      },
      {
        path: 'dialplan',
        name: 'dialplan',
        component: () => import('@/views/DialplanView.vue'),
        meta: { title: 'Dialplan', icon: 'mdi-swap-horizontal-bold', permission: 'dialplan:read', nav: true },
      },
      {
        path: 'rtpengine',
        name: 'rtpengine',
        component: () => import('@/views/RtpengineView.vue'),
        meta: { title: 'RTPEngine', icon: 'mdi-multimedia', permission: 'rtpengine:read', nav: true },
      },
      {
        path: 'blacklist',
        name: 'blacklist',
        component: () => import('@/views/BlacklistView.vue'),
        meta: { title: 'Списки номеров', icon: 'mdi-phone-cancel', permission: 'blacklist:read', nav: true },
      },
      {
        path: 'address',
        name: 'address',
        component: () => import('@/views/AddressView.vue'),
        meta: { title: 'Доверенные адреса', icon: 'mdi-shield-check-outline', permission: 'address:read', nav: true },
      },
      {
        path: 'sip-regs',
        name: 'sip-regs',
        component: () => import('@/views/SipRegsView.vue'),
        meta: { title: 'SIP-регистрации', icon: 'mdi-phone-check', permission: 'sipregs:read', nav: true },
      },
      {
        path: 'servers',
        name: 'servers',
        component: () => import('@/views/ServersView.vue'),
        meta: { title: 'Серверы OpenSIPS', icon: 'mdi-server-network', permission: 'servers:write', nav: true },
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('@/views/UsersView.vue'),
        meta: { title: 'Пользователи', icon: 'mdi-account-group', permission: 'users:manage', nav: true },
      },
      {
        path: 'roles',
        name: 'roles',
        component: () => import('@/views/RolesView.vue'),
        meta: { title: 'Роли и права', icon: 'mdi-shield-key-outline', permission: 'users:manage', nav: true },
      },
      {
        path: 'audit',
        name: 'audit',
        component: () => import('@/views/AuditView.vue'),
        meta: { title: 'Журнал действий', icon: 'mdi-history', permission: 'audit:read', nav: true },
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/ProfileView.vue'),
        meta: { title: 'Профиль' },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    return auth.isAuthenticated ? { path: '/' } : true
  }

  if (!auth.token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (!auth.user) {
    await auth.fetchMe()
    if (!auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
  }

  if (to.meta.permission && !auth.can(to.meta.permission)) {
    return { path: '/' }
  }
  return true
})

export default router
