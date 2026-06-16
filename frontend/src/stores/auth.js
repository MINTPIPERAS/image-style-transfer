/**
 * 认证状态管理 (Pinia Store)
 * 管理 Token、用户信息，提供登录/注册/登出操作。
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/index.js'

export const useAuthStore = defineStore('auth', () => {
  // ---- 状态 ----
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const user = ref(null)            // { id, username, email, created_at }

  // ---- 计算属性 ----
  const isLoggedIn = computed(() => !!accessToken.value)
  const username = computed(() => user.value?.username || '')

  // ---- 方法 ----
  function setTokens(access, refresh) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearAuth() {
    accessToken.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function register(username, email, password) {
    const { data } = await api.post('/api/auth/register', { username, email, password })
    setTokens(data.access_token, data.refresh_token)
    await fetchProfile()
    return data
  }

  async function login(loginStr, password) {
    const { data } = await api.post('/api/auth/login', { login: loginStr, password })
    setTokens(data.access_token, data.refresh_token)
    await fetchProfile()
    return data
  }

  async function fetchProfile() {
    try {
      const { data } = await api.get('/api/users/me')
      user.value = data
    } catch {
      user.value = null
    }
  }

  function logout() {
    clearAuth()
  }

  // 初始化时如果有 Token 就拉取用户信息
  if (accessToken.value) {
    fetchProfile()
  }

  return {
    accessToken,
    refreshToken,
    user,
    isLoggedIn,
    username,
    setTokens,
    clearAuth,
    register,
    login,
    fetchProfile,
    logout,
  }
})
