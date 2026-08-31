import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'

import { createVuetify } from 'vuetify'
import { ru } from 'vuetify/locale'

export default createVuetify({
  locale: {
    locale: 'ru',
    messages: { ru },
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#1867C0',
          secondary: '#4B5563',
          success: '#2E7D32',
          warning: '#ED6C02',
          error: '#C62828',
          background: '#F5F6F8',
        },
      },
      dark: {
        colors: {
          primary: '#5B9BD5',
          success: '#66BB6A',
          warning: '#FFA726',
          error: '#EF5350',
        },
      },
    },
  },
  defaults: {
    VTextField: { variant: 'outlined', density: 'comfortable' },
    VSelect: { variant: 'outlined', density: 'comfortable' },
    VTextarea: { variant: 'outlined', density: 'comfortable' },
    VCard: { elevation: 1 },
    VBtn: { variant: 'flat' },
  },
})
