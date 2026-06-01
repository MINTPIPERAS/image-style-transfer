<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goTool() {
  router.push('/tool')
}
</script>

<template>
  <div class="home-page">
    <!-- Hero 区域 -->
    <section class="hero-section">
      <!-- 浮动装饰 -->
      <div class="float-rings">
        <div class="ring ring-1"></div>
        <div class="ring ring-2"></div>
        <div class="ring ring-3"></div>
      </div>

      <!-- 主玻璃卡片 -->
      <div class="hero-card glass-card">
        <h1 class="hero-title">
          <span class="title-icon">🎨</span>
          图像风格迁移
        </h1>
        <p class="hero-desc">
          基于神经网络的深度学习技术，将世界名画的艺术风格应用到您的照片上。
          无需任何绘画技巧，一键生成令人惊叹的艺术作品。
        </p>

        <!-- 示例展示区 -->
        <div class="demo-row">
          <div class="demo-item">
            <div class="demo-label">内容图片</div>
            <div class="demo-box demo-content">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                <rect x="2" y="2" width="20" height="20" rx="3" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <path d="M21 15l-5-5L5 21" />
              </svg>
            </div>
          </div>
          <div class="demo-arrow">
            <span>+</span>
          </div>
          <div class="demo-item">
            <div class="demo-label">风格图片</div>
            <div class="demo-box demo-style">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v4m0 12v4M2 12h4m12 0h4" />
              </svg>
            </div>
          </div>
          <div class="demo-arrow">
            <span>→</span>
          </div>
          <div class="demo-item">
            <div class="demo-label">生成结果</div>
            <div class="demo-box demo-result">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                <rect x="2" y="2" width="20" height="20" rx="3" />
                <circle cx="12" cy="12" r="3" fill="currentColor" opacity="0.3" />
                <path d="M8 8l8 8M16 8l-8 8" opacity="0.4" />
              </svg>
            </div>
          </div>
        </div>

        <!-- CTA 按钮 -->
        <button class="cta-btn" @click="goTool">
          🚀 开始创作
        </button>

        <p class="hero-foot">
          使用 VGG16 深度神经网络 · L-BFGS 优化算法 · 实时进度反馈
        </p>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="home-footer">
      <p>2026 野生代言组 · XMU · 数字媒体技术</p>
    </footer>
  </div>
</template>

<style scoped>
.home-page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 100px 24px 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

/* ---- Hero ---- */
.hero-section {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
}

/* 浮动装饰圆环 */
.float-rings {
  position: absolute;
  inset: -30px;
  pointer-events: none;
  overflow: hidden;
}

.ring {
  position: absolute;
  border-radius: 50%;
  border: 2px solid;
  opacity: 0.25;
  animation: float-ring 20s ease-in-out infinite;
}

.ring-1 {
  width: 180px;
  height: 180px;
  border-color: var(--accent);
  top: 10%;
  left: -5%;
  animation-delay: 0s;
}

.ring-2 {
  width: 120px;
  height: 120px;
  border-color: #86efac;
  bottom: 5%;
  right: -3%;
  animation-delay: -7s;
  animation-duration: 24s;
}

.ring-3 {
  width: 80px;
  height: 80px;
  border-color: #f9a8d4;
  top: 60%;
  left: 50%;
  animation-delay: -13s;
  animation-duration: 16s;
}

@keyframes float-ring {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  25% { transform: translate(30px, -20px) rotate(5deg); }
  50% { transform: translate(-15px, 15px) rotate(-3deg); }
  75% { transform: translate(-25px, -10px) rotate(2deg); }
}

/* 主卡片 */
.hero-card {
  text-align: center;
  padding: 48px 40px 40px;
  position: relative;
}

.hero-title {
  font-family: var(--heading);
  font-size: 42px;
  color: var(--text-h);
  margin: 0 0 16px;
  letter-spacing: -1px;
}

.title-icon {
  display: inline-block;
  margin-right: 8px;
}

.hero-desc {
  font-size: 16px;
  line-height: 1.8;
  color: var(--text);
  opacity: 0.75;
  max-width: 600px;
  margin: 0 auto 36px;
}

/* 示例展示行 */
.demo-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 36px;
  flex-wrap: wrap;
}

.demo-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.demo-label {
  font-size: 12px;
  color: var(--text);
  opacity: 0.5;
  font-weight: 500;
}

.demo-box {
  width: 120px;
  height: 90px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed var(--border);
}

.demo-box svg {
  width: 32px;
  height: 32px;
  color: var(--text);
  opacity: 0.35;
}

.demo-content {
  background: var(--accent-bg);
  border-color: var(--accent-border);
}

.demo-style {
  background: rgba(134, 239, 172, 0.1);
  border-color: rgba(134, 239, 172, 0.4);
}

.demo-result {
  background: rgba(249, 168, 212, 0.1);
  border-color: rgba(249, 168, 212, 0.4);
}

.demo-arrow {
  font-size: 24px;
  color: var(--text);
  opacity: 0.3;
  font-weight: 300;
}

/* CTA 按钮 */
.cta-btn {
  padding: 14px 48px;
  font-size: 18px;
  font-family: var(--sans);
  font-weight: 600;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s, transform 0.15s;
}

.cta-btn:hover {
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

.cta-btn:active {
  transform: translateY(0);
}

.hero-foot {
  margin-top: 20px;
  font-size: 13px;
  color: var(--text);
  opacity: 0.4;
}

/* ---- 页脚 ---- */
.home-footer {
  text-align: center;
  padding: 16px 0 0;
  flex-shrink: 0;
}

.home-footer p {
  font-size: 13px;
  color: var(--text);
  opacity: 0.4;
  margin: 0;
}
</style>
