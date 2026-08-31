import { defineStore } from 'pinia'
import { serversApi } from '@/api'

const SELECTED_KEY = 'osips-ui-server'

export const useServersStore = defineStore('servers', {
  state: () => ({
    items: [],
    selectedId: Number(localStorage.getItem(SELECTED_KEY)) || null,
    loaded: false,
    loading: false,
  }),
  getters: {
    selected: (state) => state.items.find((server) => server.id === state.selectedId) || null,
    activeItems: (state) => state.items.filter((server) => server.is_active),
  },
  actions: {
    async fetch(force = false) {
      if (this.loaded && !force) return this.items
      this.loading = true
      try {
        this.items = await serversApi.list()
        const stillExists = this.items.some((server) => server.id === this.selectedId)
        if (!stillExists) {
          this.select(this.activeItems[0]?.id ?? this.items[0]?.id ?? null)
        }
        this.loaded = true
        return this.items
      } finally {
        this.loading = false
      }
    },
    select(id) {
      this.selectedId = id
      if (id) {
        localStorage.setItem(SELECTED_KEY, String(id))
      } else {
        localStorage.removeItem(SELECTED_KEY)
      }
    },
  },
})
