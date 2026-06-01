<script setup>
defineProps({
  imageUrl: { type: String, required: true },
  visible: { type: Boolean, default: false },
})

const emit = defineEmits(['restart'])
</script>

<template>
  <Transition name="scale-fade">
    <div v-if="visible" class="result-panel">
      <h2 class="result-title">✨ 风格迁移完成</h2>

      <div class="image-wrapper">
        <img :src="imageUrl" alt="风格化结果" class="result-img" />
      </div>

      <div class="actions">
        <a :href="imageUrl" download="styled_result.png" class="btn btn-primary">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />
          </svg>
          下载结果
        </a>
        <button class="btn btn-secondary" @click="emit('restart')">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 4v6h6M23 20v-6h-6" />
            <path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" />
          </svg>
          重新开始
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.result-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 20px;
  height: 100%;
}

.result-title {
  font-family: var(--heading);
  font-size: 24px;
  color: var(--text-h);
  margin: 0;
}

.image-wrapper {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow);
}

.result-img {
  width: 100%;
  display: block;
}

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-family: var(--sans);
  cursor: pointer;
  text-decoration: none;
  transition: background 0.2s, box-shadow 0.2s;
}

.btn-primary {
  background: var(--accent);
  color: #fff;
}

.btn-primary:hover {
  box-shadow: var(--shadow);
}

.btn-secondary {
  background: var(--accent-bg);
  color: var(--accent);
  border: 2px solid var(--accent-border);
}

.btn-secondary:hover {
  background: var(--accent);
  color: #fff;
}

.btn-icon {
  width: 18px;
  height: 18px;
}

/* ---- Transition ---- */
.scale-fade-enter-active {
  transition: all 0.5s ease;
}
.scale-fade-leave-active {
  transition: all 0.3s ease;
}
.scale-fade-enter-from {
  opacity: 0;
  transform: scale(0.9);
}
.scale-fade-leave-to {
  opacity: 0;
}
</style>
