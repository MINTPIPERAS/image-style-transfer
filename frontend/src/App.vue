<script setup>
import Navbar from './components/Navbar.vue'
</script>

<template>
  <!-- 彩色晕染背景 -->
  <div class="bg-aurora">
    <div class="aurora-blob blob-1"></div>
    <div class="aurora-blob blob-2"></div>
    <div class="aurora-blob blob-3"></div>
  </div>

  <!-- 导航栏 -->
  <Navbar />

  <!-- 页面内容 -->
  <main class="page-content">
    <router-view />
  </main>
</template>

<style scoped>
.page-content {
  height: 100svh;
  box-sizing: border-box;
}
</style>
