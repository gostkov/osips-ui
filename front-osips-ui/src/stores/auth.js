import { defineStore } from 'pinia'
import { authApi } from '@/api'

const TOKEN_KEY = 'osips-ui-token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: null,
    loading: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token && state.user),
    permissions: (state) => state.user?.permissions || [],
    role: (state) => state.user?.role || null,
    can: (state) => (permission) => !permission || (state.user?.permissions || []).includes(permission),
  },
  actions: {
    async login(username, password) {
      const data = await authApi.login(username, password)
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem(TOKEN_KEY, data.access_token)
      return data.user
    },
    async fetchMe() {
      if (!this.token) return null
      this.loading = true
      try {
        this.user = await authApi.me()
        return this.user
      } catch {
        this.logout()
        return null
      } finally {
        this.loading = false
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
    },
  },
})
