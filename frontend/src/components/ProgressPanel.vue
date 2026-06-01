<script setup>
import { computed } from 'vue'

const props = defineProps({
  iteration: { type: Number, default: 0 },
  total: { type: Number, default: 10 },
  loss: { type: Number, default: 0 },
  visible: { type: Boolean, default: false },
})

const percent = computed(() => {
  if (props.total <= 0) return 0
  return Math.round((props.iteration / props.total) * 100)
})
</script>

<template>
  <Transition name="fade">
    <div v-if="visible" class="progress-panel">
      <!-- 旋转加载圆环 -->
      <div class="spinner"></div>

      <!-- 迭代轮数 -->
      <div class="counter-badge">
        第 <strong>{{ iteration }}</strong> / {{ total }} 轮
      </div>

      <!-- 进度条 -->
      <div class="progress-bar-wrapper">
        <div class="progress-bar-fill" :style="{ width: percent + '%' }"></div>
      </div>

      <!-- 百分比和 Loss -->
      <div class="stats">
        <span>{{ percent }}%</span>
        <span class="loss">Loss: {{ loss.toFixed(2) }}</span>
      </div>

      <p class="status-text">正在处理中，请稍候...</p>
    </div>
  </Transition>
</template>

<style scoped>
.progress-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
  padding: 32px 20px;
  height: 100%;
  box-sizing: border-box;
}

/* ---- 旋转圆环 ---- */
.spinner {
  width: 60px;
  height: 60px;
  border: 4px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ---- 数字徽章 ---- */
.counter-badge {
  font-family: var(--mono);
  font-size: 18px;
  padding: 6px 18px;
  border-radius: 8px;
  color: var(--accent);
  background: var(--accent-bg);
  border: 2px solid var(--accent-border);
}

.counter-badge strong {
  font-size: 24px;
}

/* ---- 进度条 ---- */
.progress-bar-wrapper {
  width: 100%;
  max-width: 320px;
  height: 8px;
  border-radius: 4px;
  background: var(--border);
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 4px;
  transition: width 0.4s ease;
}

/* ---- 统计信息 ---- */
.stats {
  display: flex;
  gap: 24px;
  font-family: var(--mono);
  font-size: 14px;
  color: var(--text);
}

.loss {
  opacity: 0.7;
}

/* ---- 状态文字 ---- */
.status-text {
  color: var(--text);
  opacity: 0.6;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* ---- Transition ---- */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
