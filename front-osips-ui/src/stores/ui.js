import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', {
  state: () => ({
    snackbar: { show: false, text: '', color: 'success', timeout: 4000 },
  }),
  actions: {
    notify(text, color = 'success', timeout = 4000) {
      this.snackbar = { show: true, text, color, timeout }
    },
    success(text) {
      this.notify(text, 'success')
    },
    error(text) {
      this.notify(text, 'error', 8000)
    },
  },
})
