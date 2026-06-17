<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import ImageUploadBox from '../components/ImageUploadBox.vue'
import StyleSelector from '../components/StyleSelector.vue'
import ProgressPanel from '../components/ProgressPanel.vue'
import ResultDisplay from '../components/ResultDisplay.vue'

const router = useRouter()
const authStore = useAuthStore()

// ---- 状态 ----
const contentImage = ref(null)
const styleImage = ref(null)           // File 对象（用于预览）
const styleMeta = ref(null)            // { type, presetId?, name, file? }
const showStyleSelector = ref(false)
const isProcessing = ref(false)
const resultImageUrl = ref('')
const progress = ref({ iteration: 0, total: 10, loss: 0 })
const errorMessage = ref('')

// 风格预览 URL（非 File 对象时手动创建）
const stylePreviewUrl = ref('')

let eventSource = null

// ---- 计算属性 ----
const canSubmit = computed(() => contentImage.value && styleImage.value && !isProcessing.value)

// 风格的显示标签
const styleLabel = computed(() => {
  if (!styleMeta.value) return ''
  return styleMeta.value.name || '自定义风格'
})

// ---- 方法 ----
function resetAll() {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  if (stylePreviewUrl.value) {
    URL.revokeObjectURL(stylePreviewUrl.value)
    stylePreviewUrl.value = ''
  }
  contentImage.value = null
  styleImage.value = null
  styleMeta.value = null
  resultImageUrl.value = ''
  isProcessing.value = false
  errorMessage.value = ''
  progress.value = { iteration: 0, total: 10, loss: 0 }
}

async function handleStyleSelect(result) {
  showStyleSelector.value = false

  if (result.type === 'preset') {
    // 从后端获取预设图片作为 File
    try {
      const resp = await fetch(result.thumbnailUrl)
      if (!resp.ok) throw new Error('Failed to fetch preset')
      const blob = await resp.blob()
      const file = new File([blob], result.file, { type: blob.type || 'image/png' })
      styleImage.value = file
      styleMeta.value = {
        type: 'preset',
        presetId: result.presetId,
        name: result.name,
      }
      if (stylePreviewUrl.value) URL.revokeObjectURL(stylePreviewUrl.value)
      stylePreviewUrl.value = URL.createObjectURL(file)
    } catch (e) {
      console.error('加载预设风格失败:', e)
      errorMessage.value = '加载预设风格失败'
    }
  } else {
    // 自定义上传
    styleImage.value = result.file
    styleMeta.value = {
      type: 'custom',
      name: result.name,
    }
    if (stylePreviewUrl.value) URL.revokeObjectURL(stylePreviewUrl.value)
    stylePreviewUrl.value = URL.createObjectURL(result.file)
  }
}

async function startTransfer() {
  if (!canSubmit.value) return

  isProcessing.value = true
  errorMessage.value = ''
  resultImageUrl.value = ''
  progress.value = { iteration: 0, total: 10, loss: 0 }

  try {
    // 使用登录后的 /api/convert/submit（如果已登录），否则用体验模式 /api/transfer
    const endpoint = authStore.isLoggedIn ? '/api/convert/submit' : '/api/transfer'

    const formData = new FormData()
    formData.append('content_image', contentImage.value)

    if (styleMeta.value?.type === 'preset') {
      formData.append('style_preset', styleMeta.value.presetId)
      formData.append('style_name', styleMeta.value.name)
    } else {
      formData.append('style_image', styleImage.value)
      formData.append('style_name', styleMeta.value?.name || '自定义风格')
    }

    // 获取 access token
    const headers = {}
    if (authStore.isLoggedIn) {
      headers['Authorization'] = `Bearer ${authStore.accessToken}`
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData,
      headers,
    })

    if (!response.ok) {
      const text = await response.text().catch(() => '')
      console.error('后端返回错误:', response.status, text)
      throw new Error(`创建任务失败 (${response.status})`)
    }

    const rawText = await response.text()
    console.log('POST response:', rawText.substring(0, 200))
    const { task_id } = JSON.parse(rawText)
    console.log('task_id:', task_id)

    // SSE 连接监听进度（直连后端，绕过 Vite 代理避免缓冲）
    const baseUrl = 'http://127.0.0.1:8000'
    const streamEndpoint = authStore.isLoggedIn
      ? `${baseUrl}/api/convert/task/${task_id}`
      : `${baseUrl}/api/transfer/stream/${task_id}`

    eventSource = new EventSource(streamEndpoint)

    eventSource.addEventListener('progress', (e) => {
      const data = JSON.parse(e.data)
      progress.value = {
        iteration: data.iteration,
        total: data.total,
        loss: data.loss,
      }
    })

    eventSource.addEventListener('complete', async (e) => {
      const data = JSON.parse(e.data)
      const imgResponse = await fetch(`${baseUrl}/api/output/${data.filename}`)
      if (imgResponse.ok) {
        const blob = await imgResponse.blob()
        resultImageUrl.value = URL.createObjectURL(blob)
      }
      isProcessing.value = false
      eventSource?.close()
      eventSource = null
    })

    eventSource.addEventListener('failed', (e) => {
      const data = JSON.parse(e.data)
      errorMessage.value = `风格迁移失败: ${data.message}`
      isProcessing.value = false
      eventSource?.close()
      eventSource = null
    })

    eventSource.onerror = () => {
      if (eventSource?.readyState === EventSource.CLOSED && isProcessing.value) {
        errorMessage.value = '连接中断，请检查后端服务'
        isProcessing.value = false
      }
    }

  } catch (err) {
    console.error('请求失败:', err)
    if (err instanceof TypeError && err.message === 'Failed to fetch') {
      errorMessage.value = '无法连接到后端，请确认 python app.py 已启动（端口 8000）'
    } else if (err.message) {
      errorMessage.value = `请求失败: ${err.message}`
    } else {
      errorMessage.value = '请求失败，请检查后端是否启动'
    }
    isProcessing.value = false
  }
}

onUnmounted(() => {
  if (eventSource) eventSource.close()
})
</script>

<template>
  <div class="tool-container">
    <div class="glass-card tool-card">
      <header class="tool-header">
        <h1>🎨 图像风格迁移</h1>
        <p class="subtitle">将艺术风格应用到您的照片上</p>
        <p v-if="!authStore.isLoggedIn" class="login-hint">
          💡 体验模式不保存记录 —
          <router-link to="/login">登录</router-link> 后可使用全部功能
        </p>
      </header>

      <main class="main-layout">
        <!-- 左栏：图片选择 -->
        <div class="left-panel">
          <ImageUploadBox label="选择内容图片" v-model="contentImage" />

          <!-- 风格选择：点击打开浮窗 -->
          <div
            class="upload-box style-trigger"
            :class="{ empty: !styleImage, filled: !!styleImage }"
            :style="stylePreviewUrl ? { backgroundImage: `url(${stylePreviewUrl})` } : {}"
            @click="showStyleSelector = true"
          >
            <div v-if="!styleImage" class="placeholder">
              <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 16V4m0 0L8 8m4-4l4 4" />
                <path d="M3 15v2a2 2 0 002 2h14a2 2 0 002-2v-2" />
              </svg>
              <span class="label-text">选择风格图片</span>
            </div>
            <div v-else class="overlay">
              <button class="overlay-btn" @click.stop="showStyleSelector = true">更换风格</button>
              <button class="overlay-btn danger" @click.stop="styleImage = null; styleMeta = null">移除</button>
            </div>
            <span v-if="styleMeta" class="style-badge">{{ styleMeta.name }}</span>
          </div>

          <button
            class="submit-btn"
            :disabled="!canSubmit"
            @click="startTransfer"
          >
            {{ isProcessing ? '⏳ 处理中...（请勿离开界面）' : '🚀 开始风格迁移' }}
          </button>

          <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
        </div>

        <!-- 右栏：进度 / 结果 / 占位 -->
        <div class="right-panel">
          <ProgressPanel
            v-if="isProcessing"
            :iteration="progress.iteration"
            :total="progress.total"
            :loss="progress.loss"
            :visible="isProcessing"
          />

          <ResultDisplay
            v-else-if="resultImageUrl"
            :image-url="resultImageUrl"
            :visible="!!resultImageUrl"
            @restart="resetAll"
          />

          <div v-else class="empty-state">
            <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
              <rect x="2" y="2" width="20" height="20" rx="3" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <path d="M21 15l-5-5L5 21" />
            </svg>
            <p>上传内容图片和风格图片，<br/>点击按钮开始风格迁移</p>
          </div>
        </div>
      </main>
    </div>

    <!-- 风格选择浮窗 -->
    <StyleSelector
      v-if="showStyleSelector"
      @select="handleStyleSelect"
      @close="showStyleSelector = false"
    />
  </div>
</template>

<style scoped>
.tool-container {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 78px 16px 16px;
  box-sizing: border-box;
}

.tool-card {
  width: 100%;
  max-width: 1120px;
  max-height: 100%;
  padding: 24px 32px 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

/* ---- Header ---- */
.tool-header {
  text-align: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.tool-header h1 {
  font-family: var(--heading);
  font-size: 26px;
  color: var(--text-h);
  margin: 0 0 4px;
  letter-spacing: -0.5px;
}

.subtitle {
  color: var(--text);
  opacity: 0.55;
  margin: 0;
  font-size: 13px;
}

.login-hint {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text);
  opacity: 0.6;
  background: var(--accent-bg);
  padding: 6px 12px;
  border-radius: 8px;
  display: inline-block;
}

.login-hint a {
  color: var(--accent);
  font-weight: 500;
}

/* ---- 主布局 ---- */
.main-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 28px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

@media (max-width: 860px) {
  .main-layout {
    grid-template-columns: 1fr;
    overflow-y: auto;
  }
}

/* ---- 左栏 ---- */
.left-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: hidden;
}

.submit-btn {
  padding: 12px 0;
  font-size: 15px;
  font-family: var(--sans);
  font-weight: 600;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s, transform 0.1s;
  width: 100%;
  flex-shrink: 0;
}

.submit-btn:hover:not(:disabled) {
  box-shadow: var(--shadow);
  transform: translateY(-1px);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  background: var(--border);
  color: var(--text);
  cursor: not-allowed;
}

.error-msg {
  color: #e74c3c;
  font-size: 13px;
  text-align: center;
  margin: 0;
  flex-shrink: 0;
}

/* ---- 右栏 ---- */
.right-panel {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow-y: auto;
}

/* ---- 空状态占位 ---- */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  color: var(--text);
  opacity: 0.45;
  text-align: center;
  padding: 40px;
}

.empty-icon {
  width: 56px;
  height: 56px;
}

.empty-state p {
  margin: 0;
  line-height: 1.6;
  font-size: 15px;
}

/* ---- 风格选择触发器 ---- */
.style-trigger {
  width: 100%;
  aspect-ratio: 3 / 2;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.3s, box-shadow 0.3s, background-color 0.3s;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.style-trigger.empty {
  border: 2px dashed var(--border);
  background: var(--bg);
}

.style-trigger.empty:hover {
  border-color: var(--accent);
  background: var(--accent-bg);
  box-shadow: var(--shadow);
}

.style-trigger.filled {
  border: none;
  background-size: cover;
  background-position: center;
}

.style-trigger .overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.style-trigger.filled:hover .overlay {
  opacity: 1;
}

.style-trigger .overlay-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  transition: background 0.2s;
}

.style-trigger .overlay-btn:hover {
  background: #fff;
}

.style-trigger .overlay-btn.danger {
  background: rgba(255, 80, 80, 0.85);
  color: #fff;
}

.style-trigger .overlay-btn.danger:hover {
  background: rgb(255, 60, 60);
}

.style-trigger .placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--text);
  pointer-events: none;
}

.style-trigger .upload-icon {
  width: 40px;
  height: 40px;
  opacity: 0.5;
}

.style-trigger .label-text {
  font-size: 14px;
  opacity: 0.7;
}

.style-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 4px 12px;
  border-radius: 20px;
  background: var(--accent);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  pointer-events: none;
  z-index: 2;
}
</style>
