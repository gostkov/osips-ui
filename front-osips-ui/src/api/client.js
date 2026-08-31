import axios from 'axios'

const client = axios.create({ baseURL: '/api', timeout: 30000 })

let onUnauthorized = () => {}

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('osips-ui-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    if (status === 401) {
      onUnauthorized()
    }
    // единый текст ошибки для UI
    error.uiMessage =
      error.response?.data?.detail ||
      (Array.isArray(error.response?.data) ? error.response.data[0]?.msg : null) ||
      error.message ||
      'Неизвестная ошибка'
    if (typeof error.uiMessage !== 'string') {
      error.uiMessage = JSON.stringify(error.uiMessage)
    }
    return Promise.reject(error)
  },
)

export default client
