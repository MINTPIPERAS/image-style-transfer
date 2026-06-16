<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../api/index.js'

const router = useRouter()
const authStore = useAuthStore()

const records = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(12)
const loading = ref(true)

// 大图预览
const previewImage = ref('')

onMounted(async () => {
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  await loadRecords()
})

async function loadRecords() {
  loading.value = true
  try {
    const { data } = await api.get('/api/convert/history', {
      params: { page: page.value, page_size: pageSize.value },
    })
    records.value = data.items
    total.value = data.total
  } catch (err) {
    console.error('加载历史记录失败:', err)
  } finally {
    loading.value = false
  }
}

async function deleteRecord(id) {
  if (!confirm('确定要删除这条记录吗？')) return
  try {
    await api.delete(`/api/convert/record/${id}`)
    records.value = records.value.filter((r) => r.id !== id)
    total.value--
  } catch (err) {
    alert('删除失败: ' + (err.response?.data?.detail || '未知错误'))
  }
}

function downloadImage(url) {
  const a = document.createElement('a')
  a.href = url
  a.download = ''
  a.click()
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function changePage(p) {
  page.value = p
  loadRecords()
}

const totalPages = () => Math.max(1, Math.ceil(total.value / pageSize.value))
</script>

<template>
  <div class="history-page">
    <!-- 头部独立容器 -->
    <div class="history-top-bar">
      <div class="history-top-inner">
        <h1>📋 我的作品</h1>
        <span class="count-badge" v-if="total > 0">共 {{ total }} 条</span>
      </div>
    </div>

    <!-- 主体内容区 -->
    <div class="history-container">
      <!-- 加载中 -->
      <div v-if="loading" class="empty">加载中...</div>

      <!-- 空状态 -->
      <div v-else-if="records.length === 0" class="empty-state">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <rect x="2" y="2" width="20" height="20" rx="3" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <path d="M21 15l-5-5L5 21" />
        </svg>
        <p>还没有作品，<br/>去 <router-link to="/tool">风格迁移</router-link> 试试吧</p>
      </div>

      <!-- 记录网格 -->
      <div v-else class="record-grid">
        <div v-for="item in records" :key="item.id" class="record-card glass-card">
          <div class="card-img" @click="previewImage = item.result_url">
            <img :src="item.result_url" :alt="item.original_filename" loading="lazy" />
          </div>
          <div class="card-info">
            <div class="info-top">
              <span class="style-tag">{{ item.style_type }}</span>
              <span class="date">{{ formatDate(item.created_at) }}</span>
            </div>
            <div class="info-bottom">
              <span class="filename" :title="item.original_filename">{{ item.original_filename }}</span>
              <span class="size">{{ formatSize(item.result_size) }}</span>
            </div>
          </div>
          <div class="card-actions">
            <button class="card-btn" @click="downloadImage(item.result_url)" title="下载">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />
              </svg>
            </button>
            <button class="card-btn danger" @click="deleteRecord(item.id)" title="删除">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="total > pageSize" class="pagination">
        <button :disabled="page <= 1" @click="changePage(page - 1)">← 上一页</button>
        <span>{{ page }} / {{ totalPages() }}</span>
        <button :disabled="page >= totalPages()" @click="changePage(page + 1)">下一页 →</button>
      </div>
    </div>

    <!-- 大图预览遮罩 -->
    <div v-if="previewImage" class="preview-overlay" @click="previewImage = ''">
      <img :src="previewImage" alt="预览" />
    </div>
  </div>
</template>

<style scoped>
.history-page {
  height: 100%;
  padding: 88px 16px 16px;
  box-sizing: border-box;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* ---- 头部独立容器 ---- */
.history-top-bar {
  max-width: 960px;
  width: 100%;
  margin: 0 auto 16px;
  padding: 20px 24px;
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow);
  flex-shrink: 0;
}

.history-top-inner {
  display: flex;
  align-items: center;
  gap: 12px;
}

.history-top-inner h1 {
  font-family: var(--heading);
  font-size: 26px;
  color: var(--text-h);
  margin: 0;
}

.count-badge {
  font-size: 13px;
  color: var(--text);
  opacity: 0.5;
  background: var(--accent-bg);
  padding: 2px 10px;
  border-radius: 20px;
}

/* ---- 主体内容区 ---- */
.history-container {
  max-width: 960px;
  width: 100%;
  margin: 0 auto;
  flex: 1;
  min-height: 0;
}

/* 空状态 */
.empty, .empty-state {
  text-align: center;
  color: var(--text);
  opacity: 0.5;
  padding: 60px 20px;
}

.empty-icon {
  width: 56px;
  height: 56px;
  margin-bottom: 14px;
}

.empty-state a {
  color: var(--accent);
  text-decoration: none;
}

/* 记录网格 */
.record-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.record-card {
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.card-img {
  aspect-ratio: 1;
  cursor: pointer;
  overflow: hidden;
  background: var(--bg);
}

.card-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.card-img:hover img {
  transform: scale(1.05);
}

.card-info {
  padding: 10px 12px 6px;
}

.info-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.style-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--accent-bg);
  color: var(--accent);
  font-weight: 500;
}

.date {
  font-size: 11px;
  color: var(--text);
  opacity: 0.5;
}

.info-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filename {
  font-size: 12px;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 130px;
}

.size {
  font-size: 11px;
  color: var(--text);
  opacity: 0.5;
  flex-shrink: 0;
}

.card-actions {
  display: flex;
  border-top: 1px solid var(--border);
}

.card-btn {
  flex: 1;
  padding: 8px 0;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--text);
  opacity: 0.5;
  transition: background 0.2s, opacity 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-btn:hover {
  opacity: 1;
  background: var(--accent-bg);
  color: var(--accent);
}

.card-btn.danger:hover {
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 24px 0 40px;
}

.pagination button {
  padding: 8px 18px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text);
  cursor: pointer;
  font-size: 14px;
  font-family: var(--sans);
}

.pagination button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.pagination button:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.pagination span {
  font-size: 14px;
  color: var(--text);
}

/* 预览遮罩 */
.preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 40px;
}

.preview-overlay img {
  max-width: 90%;
  max-height: 90%;
  border-radius: 8px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4);
}
</style>
