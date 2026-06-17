<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/index.js'

const emit = defineEmits(['select', 'close'])

const presets = ref([])
const activeTab = ref('preset') // 'preset' | 'custom'
const selectedPreset = ref(null)

// 自定义
const customFile = ref(null)
const customPreviewUrl = ref('')
const customName = ref('')

const customFileInput = ref(null)

onMounted(async () => {
  try {
    const { data } = await api.get('/api/styles')
    presets.value = data.presets
  } catch (e) {
    console.error('获取预设风格失败:', e)
  }
})

function selectPreset(preset) {
  selectedPreset.value = preset.id
}

function confirmPreset() {
  if (!selectedPreset.value) return
  const preset = presets.value.find((p) => p.id === selectedPreset.value)
  if (!preset) return
  emit('select', {
    type: 'preset',
    presetId: preset.id,
    name: preset.name,
    file: preset.file,
    thumbnailUrl: preset.thumbnail_url,
  })
}

function handleCustomFile(e) {
  const file = e.target.files?.[0] || null
  customFile.value = file
  if (customPreviewUrl.value) {
    URL.revokeObjectURL(customPreviewUrl.value)
    customPreviewUrl.value = ''
  }
  if (file) {
    customPreviewUrl.value = URL.createObjectURL(file)
  }
}

function confirmCustom() {
  if (!customFile.value) return
  emit('select', {
    type: 'custom',
    name: customName.value.trim() || '自定义风格',
    file: customFile.value,
  })
}

function handleOverlayClick(e) {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}
</script>

<template>
  <div class="style-overlay" @click="handleOverlayClick">
    <div class="style-panel glass-card">
      <div class="panel-header">
        <h2>选择风格</h2>
        <button class="close-btn" @click="$emit('close')">&times;</button>
      </div>

      <!-- 标签栏 -->
      <div class="tab-bar">
        <button
          :class="['tab', { active: activeTab === 'preset' }]"
          @click="activeTab = 'preset'"
        >
          🎨 预设风格
        </button>
        <button
          :class="['tab', { active: activeTab === 'custom' }]"
          @click="activeTab = 'custom'"
        >
          📁 自定义上传
        </button>
      </div>

      <!-- 预设风格 -->
      <div v-if="activeTab === 'preset'" class="tab-content">
        <div class="preset-grid">
          <div
            v-for="preset in presets"
            :key="preset.id"
            :class="['preset-card', { selected: selectedPreset === preset.id }]"
            @click="selectPreset(preset)"
          >
            <img :src="preset.thumbnail_url" :alt="preset.name" />
            <span class="preset-name">{{ preset.name }}</span>
            <span class="preset-check" v-if="selectedPreset === preset.id">✓</span>
          </div>
        </div>
        <button class="confirm-btn" :disabled="!selectedPreset" @click="confirmPreset">
          使用选中风格
        </button>
      </div>

      <!-- 自定义上传 -->
      <div v-if="activeTab === 'custom'" class="tab-content">
        <div
          class="custom-upload"
          :class="{ filled: customFile }"
          :style="customPreviewUrl ? { backgroundImage: `url(${customPreviewUrl})` } : {}"
          @click="customFileInput?.click()"
        >
          <div v-if="!customFile" class="custom-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="40" height="40">
              <path d="M12 16V4m0 0L8 8m4-4l4 4" />
              <path d="M3 15v2a2 2 0 002 2h14a2 2 0 002-2v-2" />
            </svg>
            <span>点击上传风格图片</span>
          </div>
          <div v-else class="custom-overlay">
            <button class="overlay-btn" @click.stop="customFileInput?.click()">更换</button>
          </div>
        </div>
        <input
          ref="customFileInput"
          type="file"
          accept="image/*"
          class="hidden-input"
          @change="handleCustomFile"
        />
        <div class="name-row">
          <label>风格名称（可选）</label>
          <input
            v-model="customName"
            type="text"
            class="name-input"
            placeholder="例如：水墨画风、赛博朋克..."
            maxlength="20"
          />
        </div>
        <button class="confirm-btn" :disabled="!customFile" @click="confirmCustom">
          使用自定义风格
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.style-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(30, 35, 18, 0.45);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 72px 24px 24px;
}

.style-panel {
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  padding: 28px 24px 24px;
  overflow-y: auto;
  border-radius: 18px;
  background: rgba(255, 255, 250, 0.95);
  border: 1px solid rgba(147, 197, 86, 0.25);
  box-shadow: 0 16px 48px rgba(60, 80, 20, 0.15);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.panel-header h2 {
  font-family: var(--heading);
  font-size: 20px;
  color: #4a5e2e;
  margin: 0;
}

.close-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(147, 197, 86, 0.12);
  color: #7eb356;
  border-radius: 8px;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, color 0.2s;
}

.close-btn:hover {
  background: rgba(147, 197, 86, 0.22);
  color: #5a8a2a;
}

/* ---- 标签栏 ---- */
.tab-bar {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #e8eeda;
  margin-bottom: 18px;
}

.tab {
  flex: 1;
  padding: 10px 0;
  border: none;
  background: transparent;
  color: #6b7a55;
  font-size: 14px;
  font-family: var(--sans);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: color 0.2s, border-color 0.2s;
}

.tab:hover {
  color: #7eb356;
}

.tab.active {
  color: #5a8a2a;
  border-bottom-color: #93c556;
  font-weight: 600;
}

/* ---- 预设卡片 ---- */
.tab-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preset-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.preset-card {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  aspect-ratio: 4/3;
  cursor: pointer;
  border: 3px solid transparent;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s;
}

.preset-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(60, 80, 20, 0.15);
}

.preset-card.selected {
  border-color: #93c556;
  box-shadow: 0 0 0 4px rgba(147, 197, 86, 0.2);
}

.preset-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preset-name {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 10px 12px;
  background: linear-gradient(transparent, rgba(40, 55, 10, 0.75));
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.preset-check {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #93c556;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(147, 197, 86, 0.4);
}

/* ---- 确认按钮 ---- */
.confirm-btn {
  width: 100%;
  padding: 12px 0;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #93c556, #7eb356);
  color: #fff;
  font-size: 15px;
  font-family: var(--sans);
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s, box-shadow 0.2s;
  box-shadow: 0 2px 8px rgba(126, 179, 86, 0.3);
}

.confirm-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  box-shadow: none;
}

.confirm-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(126, 179, 86, 0.4);
}

/* ---- 自定义上传 ---- */
.custom-upload {
  aspect-ratio: 3/2;
  border-radius: 10px;
  border: 2px dashed #c8dba0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  background: rgba(147, 197, 86, 0.06);
  background-size: cover;
  background-position: center;
  position: relative;
  overflow: hidden;
}

.custom-upload:hover {
  border-color: #93c556;
  background: rgba(147, 197, 86, 0.1);
}

.custom-upload.filled {
  border: none;
}

.custom-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #5a7a30;
  pointer-events: none;
  font-size: 15px;
  font-weight: 500;
}

.custom-placeholder svg {
  color: #93c556;
  opacity: 0.7;
}

.custom-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.custom-upload.filled:hover .custom-overlay {
  opacity: 1;
}

.overlay-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  background: rgba(255,255,255,0.9);
  color: #333;
  font-size: 14px;
  cursor: pointer;
}

.name-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.name-row label {
  font-size: 13px;
  color: #5a7a30;
  font-weight: 500;
}

.name-input {
  padding: 10px 12px;
  border: 1px solid #c8dba0;
  border-radius: 8px;
  background: rgba(255,255,250,0.8);
  color: #3a5020;
  font-size: 14px;
  font-family: var(--sans);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.name-input:focus {
  border-color: #93c556;
  box-shadow: 0 0 0 3px rgba(147, 197, 86, 0.15);
}

.name-input::placeholder {
  color: #a0b888;
}

.hidden-input {
  display: none;
}
</style>
