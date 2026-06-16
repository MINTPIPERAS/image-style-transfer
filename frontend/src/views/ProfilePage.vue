<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../api/index.js'

const router = useRouter()
const authStore = useAuthStore()

const profile = ref(null)
const loading = ref(true)

// 修改密码
const showPwdForm = ref(false)
const pwdForm = ref({ old_password: '', new_password: '', confirm: '' })
const pwdError = ref('')
const pwdSuccess = ref('')
const pwdSubmitting = ref(false)

onMounted(async () => {
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  try {
    await authStore.fetchProfile()
    profile.value = authStore.user
  } finally {
    loading.value = false
  }
})

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

async function changePassword() {
  pwdError.value = ''
  pwdSuccess.value = ''

  if (!pwdForm.value.old_password || !pwdForm.value.new_password) {
    pwdError.value = '请填写完整'
    return
  }
  if (pwdForm.value.new_password.length < 6) {
    pwdError.value = '新密码至少 6 位'
    return
  }
  if (pwdForm.value.new_password !== pwdForm.value.confirm) {
    pwdError.value = '两次密码输入不一致'
    return
  }

  pwdSubmitting.value = true
  try {
    await api.put('/api/users/me/password', {
      old_password: pwdForm.value.old_password,
      new_password: pwdForm.value.new_password,
    })
    pwdSuccess.value = '密码修改成功'
    pwdForm.value = { old_password: '', new_password: '', confirm: '' }
    showPwdForm.value = false
  } catch (err) {
    pwdError.value = err.response?.data?.detail || '修改失败'
  } finally {
    pwdSubmitting.value = false
  }
}

function goHistory() {
  router.push('/history')
}
</script>

<template>
  <div class="profile-page">
    <div class="glass-card profile-card">
      <h1>👤 个人中心</h1>

      <div v-if="loading" class="loading">加载中...</div>

      <template v-else-if="profile">
        <!-- 基本信息 -->
        <section class="info-section">
          <div class="info-row">
            <span class="info-label">用户名</span>
            <span class="info-value">{{ profile.username }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">邮箱</span>
            <span class="info-value">{{ profile.email }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">注册时间</span>
            <span class="info-value">{{ formatDate(profile.created_at) }}</span>
          </div>
        </section>

        <!-- 快捷操作 -->
        <div class="actions">
          <button class="action-btn" @click="goHistory">📋 我的作品</button>
          <button class="action-btn secondary" @click="showPwdForm = !showPwdForm">
            🔒 {{ showPwdForm ? '取消' : '修改密码' }}
          </button>
        </div>

        <!-- 修改密码表单 -->
        <form v-if="showPwdForm" class="pwd-form" @submit.prevent="changePassword">
          <div class="form-group">
            <label>旧密码</label>
            <input v-model="pwdForm.old_password" type="password" />
          </div>
          <div class="form-group">
            <label>新密码</label>
            <input v-model="pwdForm.new_password" type="password" placeholder="至少 6 位" />
          </div>
          <div class="form-group">
            <label>确认新密码</label>
            <input v-model="pwdForm.confirm" type="password" />
          </div>
          <p v-if="pwdError" class="error-msg">{{ pwdError }}</p>
          <p v-if="pwdSuccess" class="success-msg">{{ pwdSuccess }}</p>
          <button class="submit-btn" type="submit" :disabled="pwdSubmitting">
            {{ pwdSubmitting ? '提交中...' : '确认修改' }}
          </button>
        </form>
      </template>

      <div v-else class="empty">无法加载用户信息</div>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 78px 16px 16px;
  box-sizing: border-box;
}

.profile-card {
  width: 100%;
  max-width: 500px;
  padding: 36px 32px 28px;
}

.profile-card h1 {
  font-family: var(--heading);
  font-size: 26px;
  color: var(--text-h);
  margin: 0 0 24px;
  text-align: center;
}

.loading, .empty {
  text-align: center;
  color: var(--text);
  opacity: 0.5;
  padding: 20px;
}

/* 信息区 */
.info-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.info-label {
  font-size: 13px;
  color: var(--text);
  opacity: 0.65;
}

.info-value {
  font-size: 15px;
  color: var(--text-h);
  font-weight: 500;
}

/* 操作按钮 */
.actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  flex: 1;
  padding: 10px 0;
  font-size: 15px;
  font-family: var(--sans);
  font-weight: 500;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.action-btn.secondary {
  background: var(--accent-bg);
  color: var(--accent);
  border: 1px solid var(--accent-border);
}

.action-btn:hover {
  opacity: 0.9;
}

/* 修改密码 */
.pwd-form {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-size: 13px;
  color: var(--text);
  opacity: 0.75;
}

.form-group input {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 14px;
  font-family: var(--sans);
  background: var(--bg);
  color: var(--text-h);
  outline: none;
}

.form-group input:focus {
  border-color: var(--accent);
}

.error-msg { color: #e74c3c; font-size: 13px; margin: 0; text-align: center; }
.success-msg { color: #27ae60; font-size: 13px; margin: 0; text-align: center; }

.submit-btn {
  padding: 10px 0;
  font-size: 15px;
  font-family: var(--sans);
  font-weight: 500;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.submit-btn:disabled {
  background: var(--border);
  color: var(--text);
  cursor: not-allowed;
}
</style>
