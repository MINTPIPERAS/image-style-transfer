<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 模式切换：login / register
const mode = ref('login')
const isLogin = computed(() => mode.value === 'login')

// 表单数据
const form = ref({
  username: '',
  email: '',
  login: '',
  password: '',
  confirmPassword: '',
})

const errorMsg = ref('')
const isSubmitting = ref(false)

function switchMode(m) {
  mode.value = m
  errorMsg.value = ''
  form.value = { username: '', email: '', login: '', password: '', confirmPassword: '' }
}

async function handleSubmit() {
  errorMsg.value = ''
  isSubmitting.value = true

  try {
    if (isLogin.value) {
      // 登录
      if (!form.value.login || !form.value.password) {
        errorMsg.value = '请填写完整信息'
        isSubmitting.value = false
        return
      }
      await authStore.login(form.value.login, form.value.password)
    } else {
      // 注册
      if (!form.value.username || !form.value.email || !form.value.password) {
        errorMsg.value = '请填写完整信息'
        isSubmitting.value = false
        return
      }
      if (form.value.password !== form.value.confirmPassword) {
        errorMsg.value = '两次密码输入不一致'
        isSubmitting.value = false
        return
      }
      if (form.value.password.length < 6) {
        errorMsg.value = '密码长度至少 6 位'
        isSubmitting.value = false
        return
      }
      await authStore.register(form.value.username, form.value.email, form.value.password)
    }

    // 登录/注册成功，跳转回原页面或首页
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (err) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      errorMsg.value = detail
    } else if (err.response?.status === 401) {
      errorMsg.value = '用户名/邮箱或密码错误'
    } else if (err.response?.status === 409) {
      errorMsg.value = '用户名或邮箱已被注册'
    } else {
      errorMsg.value = '请求失败，请检查网络连接'
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="glass-card auth-card">
      <h1>{{ isLogin ? '👋 欢迎回来' : '✨ 创建账号' }}</h1>
      <p class="subtitle">{{ isLogin ? '登录后使用全部功能' : '注册即可开始创作' }}</p>

      <form class="auth-form" @submit.prevent="handleSubmit">
        <!-- 注册模式额外字段 -->
        <template v-if="!isLogin">
          <div class="form-group">
            <label>用户名</label>
            <input
              v-model="form.username"
              type="text"
              placeholder="2-50 个字符"
              autocomplete="username"
            />
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input
              v-model="form.email"
              type="email"
              placeholder="your@email.com"
              autocomplete="email"
            />
          </div>
        </template>

        <!-- 登录模式：用户名/邮箱 -->
        <div v-if="isLogin" class="form-group">
          <label>用户名或邮箱</label>
          <input
            v-model="form.login"
            type="text"
            placeholder="请输入用户名或邮箱"
            autocomplete="username"
          />
        </div>

        <div class="form-group">
          <label>密码</label>
          <input
            v-model="form.password"
            type="password"
            placeholder="至少 6 位密码"
            autocomplete="current-password"
          />
        </div>

        <div v-if="!isLogin" class="form-group">
          <label>确认密码</label>
          <input
            v-model="form.confirmPassword"
            type="password"
            placeholder="再次输入密码"
            autocomplete="new-password"
          />
        </div>

        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <button class="submit-btn" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? '处理中...' : (isLogin ? '登录' : '注册') }}
        </button>
      </form>

      <p class="switch-text">
        {{ isLogin ? '还没有账号？' : '已有账号？' }}
        <a href="#" @click.prevent="switchMode(isLogin ? 'register' : 'login')">
          {{ isLogin ? '立即注册' : '去登录' }}
        </a>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 78px 16px 16px;
  box-sizing: border-box;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  padding: 36px 32px 28px;
  text-align: center;
}

.auth-card h1 {
  font-family: var(--heading);
  font-size: 26px;
  color: var(--text-h);
  margin: 0 0 6px;
}

.subtitle {
  color: var(--text);
  opacity: 0.55;
  margin: 0 0 28px;
  font-size: 14px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  text-align: left;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  opacity: 0.75;
}

.form-group input {
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 15px;
  font-family: var(--sans);
  background: var(--bg);
  color: var(--text-h);
  outline: none;
  transition: border-color 0.2s;
}

.form-group input:focus {
  border-color: var(--accent);
}

.error-msg {
  color: #e74c3c;
  font-size: 13px;
  text-align: center;
  margin: 0;
}

.submit-btn {
  padding: 12px 0;
  font-size: 16px;
  font-family: var(--sans);
  font-weight: 600;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s;
  margin-top: 4px;
}

.submit-btn:hover:not(:disabled) {
  box-shadow: var(--shadow);
}

.submit-btn:disabled {
  background: var(--border);
  color: var(--text);
  cursor: not-allowed;
}

.switch-text {
  margin-top: 20px;
  font-size: 14px;
  color: var(--text);
  opacity: 0.6;
}

.switch-text a {
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
}

.switch-text a:hover {
  text-decoration: underline;
}
</style>
