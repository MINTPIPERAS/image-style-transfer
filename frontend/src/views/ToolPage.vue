<script setup>
import { ref, computed, onUnmounted } from 'vue'
import ImageUploadBox from '../components/ImageUploadBox.vue'
import ProgressPanel from '../components/ProgressPanel.vue'
import ResultDisplay from '../components/ResultDisplay.vue'

// ---- 状态 ----
const contentImage = ref(null)
const styleImage = ref(null)
const isProcessing = ref(false)
const resultImageUrl = ref('')
const progress = ref({ iteration: 0, total: 10, loss: 0 })
const errorMessage = ref('')

let eventSource = null

// ---- 计算属性 ----
const canSubmit = computed(() => contentImage.value && styleImage.value && !isProcessing.value)

// ---- 方法 ----
function resetAll() {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  contentImage.value = null
  styleImage.value = null
  resultImageUrl.value = ''
  isProcessing.value = false
  errorMessage.value = ''
  progress.value = { iteration: 0, total: 10, loss: 0 }
}

async function startTransfer() {
  if (!canSubmit.value) return

  isProcessing.value = true
  errorMessage.value = ''
  resultImageUrl.value = ''
  progress.value = { iteration: 0, total: 10, loss: 0 }

  try {
    // 1. POST 上传图片，获取 task_id
    const formData = new FormData()
    formData.append('content_image', contentImage.value)
    formData.append('style_image', styleImage.value)

    const response = await fetch('/api/transfer', {
      method: 'POST',
      body: formData,
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

    // 2. 建立 SSE 连接，监听进度（直连后端，绕过 Vite 代理避免缓冲）
    const baseUrl = 'http://127.0.0.1:8000'
    eventSource = new EventSource(`${baseUrl}/api/transfer/stream/${task_id}`)

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
      </header>

      <main class="main-layout">
        <!-- 左栏：图片选择 -->
        <div class="left-panel">
          <ImageUploadBox label="选择内容图片" v-model="contentImage" />
          <ImageUploadBox label="选择风格图片" v-model="styleImage" />

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
</style>
