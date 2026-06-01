<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  modelValue: { type: [File, null], default: null },
})

const emit = defineEmits(['update:modelValue'])

const fileInput = ref(null)
const previewUrl = ref('')

// 创建/销毁预览 URL
watch(
  () => props.modelValue,
  (file) => {
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value)
      previewUrl.value = ''
    }
    if (file) {
      previewUrl.value = URL.createObjectURL(file)
    }
  },
  { immediate: true }
)

onUnmounted(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})

const isEmpty = computed(() => !props.modelValue)

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileChange(e) {
  const file = e.target.files?.[0] || null
  emit('update:modelValue', file)
}

function handleRemove() {
  if (fileInput.value) fileInput.value.value = ''
  emit('update:modelValue', null)
}
</script>

<template>
  <div
    class="upload-box"
    :class="{ empty: isEmpty, filled: !isEmpty }"
    :style="previewUrl ? { backgroundImage: `url(${previewUrl})` } : {}"
    @click="isEmpty && triggerFileInput()"
  >
    <!-- 空状态 -->
    <div v-if="isEmpty" class="placeholder">
      <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M12 16V4m0 0L8 8m4-4l4 4" />
        <path d="M3 15v2a2 2 0 002 2h14a2 2 0 002-2v-2" />
      </svg>
      <span class="label-text">{{ label }}</span>
    </div>

    <!-- 已选状态：hover 遮罩 -->
    <div v-if="!isEmpty" class="overlay">
      <button class="overlay-btn" @click.stop="triggerFileInput">更换</button>
      <button class="overlay-btn danger" @click.stop="handleRemove">移除</button>
    </div>

    <!-- 隐藏的 file input -->
    <input
      ref="fileInput"
      type="file"
      accept="image/*"
      class="hidden-input"
      @change="handleFileChange"
    />
  </div>
</template>

<style scoped>
.upload-box {
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

.upload-box.empty {
  border: 2px dashed var(--border);
  background: var(--bg);
}

.upload-box.empty:hover {
  border-color: var(--accent);
  background: var(--accent-bg);
  box-shadow: var(--shadow);
}

.upload-box.filled {
  border: none;
  background-size: cover;
  background-position: center;
}

.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--text);
  pointer-events: none;
}

.upload-icon {
  width: 40px;
  height: 40px;
  opacity: 0.5;
}

.label-text {
  font-size: 14px;
  opacity: 0.7;
}

.overlay {
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

.upload-box.filled:hover .overlay {
  opacity: 1;
}

.overlay-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  transition: background 0.2s;
}

.overlay-btn:hover {
  background: #fff;
}

.overlay-btn.danger {
  background: rgba(255, 80, 80, 0.85);
  color: #fff;
}

.overlay-btn.danger:hover {
  background: rgb(255, 60, 60);
}

.hidden-input {
  display: none;
}
</style>
