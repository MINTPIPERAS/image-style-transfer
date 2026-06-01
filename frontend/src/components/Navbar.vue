<script setup>
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const navLinks = [
  { name: 'Home', path: '/', label: '首页' },
  { name: 'Tool', path: '/tool', label: '风格迁移' },
  { name: 'About', path: '/about', label: '关于' },
]

function isActive(path) {
  return route.path === path
}
</script>

<template>
  <nav class="navbar">
    <div class="nav-inner">
      <!-- Logo / 品牌名 -->
      <router-link to="/" class="brand" @click.prevent>
        <span class="brand-icon">🎨</span>
        <span class="brand-text">IST</span>
        <span class="brand-sub">图像风格转换</span>
      </router-link>

      <!-- 导航链接 -->
      <div class="nav-links">
        <router-link
          v-for="link in navLinks"
          :key="link.name"
          :to="link.path"
          class="nav-link"
          :class="{ active: isActive(link.path) }"
        >
          {{ link.label }}
        </router-link>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 12px 24px;
}

.nav-inner {
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(16px) saturate(1.3);
  -webkit-backdrop-filter: blur(16px) saturate(1.3);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 14px;
  padding: 10px 24px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
}

@media (prefers-color-scheme: dark) {
  .nav-inner {
    background: rgba(22, 23, 29, 0.6);
    border-color: rgba(255, 255, 255, 0.08);
    box-shadow: 0 2px 16px rgba(0, 0, 0, 0.2);
  }
}

/* ---- 品牌 ---- */
.brand {
  display: flex;
  align-items: baseline;
  gap: 6px;
  text-decoration: none;
  color: var(--text-h);
  font-family: var(--heading);
  user-select: none;
}

.brand-icon {
  font-size: 22px;
}

.brand-text {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 1px;
  color: var(--accent);
}

.brand-sub {
  font-size: 13px;
  color: var(--text);
  opacity: 0.6;
}

/* ---- 导航链接 ---- */
.nav-links {
  display: flex;
  gap: 4px;
}

.nav-link {
  padding: 8px 18px;
  border-radius: 8px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  transition: background 0.2s, color 0.2s;
}

.nav-link:hover {
  background: var(--accent-bg);
  color: var(--accent);
}

.nav-link.active {
  background: var(--accent);
  color: #fff;
}
</style>
