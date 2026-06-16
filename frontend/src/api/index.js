/**
 * Axios 实例 — 带 JWT 自动拦截器。
 * - 请求时自动附加 Access Token
 * - 401 时自动用 Refresh Token 续期
 * - 续期失败则跳转登录页
 */
import axios from 'axios'
import { useAuthStore } from '../stores/auth.js'

const api = axios.create({
  baseURL: '',          // 同源或走 Vite 代理
  timeout: 30000,
})

// 是否正在刷新 Token（避免并发请求同时刷新）
let isRefreshing = false
let refreshQueue = []

function resolveRefreshQueue(token) {
  refreshQueue.forEach(({ resolve }) => resolve(token))
  refreshQueue = []
}

function rejectRefreshQueue(error) {
  refreshQueue.forEach(({ reject }) => reject(error))
  refreshQueue = []
}

// 请求拦截器 — 附加 Token
api.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.accessToken) {
    config.headers.Authorization = `Bearer ${authStore.accessToken}`
  }
  return config
})

// 响应拦截器 — 401 自动刷新
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const authStore = useAuthStore()

    if (error.response?.status === 401 && !originalRequest._retry && authStore.refreshToken) {
      // 如果是刷新接口本身 401，直接登出
      if (originalRequest.url === '/api/auth/refresh') {
        authStore.logout()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (isRefreshing) {
        // 等待正在进行的刷新
        return new Promise((resolve, reject) => {
          refreshQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const { data } = await axios.post('/api/auth/refresh', {
          refresh_token: authStore.refreshToken,
        })
        authStore.setTokens(data.access_token, data.refresh_token)
        resolveRefreshQueue(data.access_token)
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return api(originalRequest)
      } catch (refreshError) {
        rejectRefreshQueue(refreshError)
        authStore.logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

export default api
