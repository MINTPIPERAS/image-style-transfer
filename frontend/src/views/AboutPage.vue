<script setup>
</script>

<template>
  <div class="about-page">
    <div class="glass-card about-card">
      <h1>关于本项目</h1>

      <section>
        <h2>什么是神经风格迁移？</h2>
        <p>
          神经风格迁移（Neural Style Transfer）是一种利用卷积神经网络（CNN）
          将一张图片的<strong>艺术风格</strong>与另一张图片的<strong>内容</strong>相结合的技术。
          它由 Gatys 等人在 2015 年首次提出，开创了 AI 艺术创作的新范式。
        </p>
      </section>

      <section>
        <h2>技术原理</h2>
        <ul>
          <li><strong>VGG16 网络</strong> — 使用预训练的 VGG16 作为特征提取器，浅层捕获纹理风格，深层捕获内容结构</li>
          <li><strong>内容损失</strong> — 衡量生成图像与内容图像在高层特征上的差异</li>
          <li><strong>风格损失</strong> — 通过 Gram 矩阵衡量生成图像与风格图像在纹理统计上的差异</li>
          <li><strong>L-BFGS 优化</strong> — 使用拟牛顿法迭代优化像素值，最小化总损失函数</li>
        </ul>
      </section>

      <section>
        <h2>技术栈</h2>
        <div class="tech-tags">
          <span class="tag">Python</span>
          <span class="tag">TensorFlow / Keras</span>
          <span class="tag">FastAPI</span>
          <span class="tag">Vue 3</span>
          <span class="tag">Vite</span>
          <span class="tag">SSE</span>
          <span class="tag">SciPy</span>
        </div>
      </section>

      <section>
        <h2>开源协议</h2>
        <p>本项目基于 MIT 协议开源，欢迎贡献代码和提出建议。</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.about-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 100px 24px 60px;
}

.about-card {
  padding: 40px;
}

.about-card h1 {
  font-family: var(--heading);
  font-size: 32px;
  color: var(--text-h);
  margin: 0 0 28px;
  text-align: center;
}

section {
  margin-bottom: 28px;
}

section h2 {
  font-family: var(--heading);
  font-size: 18px;
  color: var(--accent);
  margin: 0 0 10px;
}

section p {
  font-size: 15px;
  line-height: 1.8;
  color: var(--text);
  margin: 0;
}

section ul {
  margin: 0;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

section li {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text);
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  padding: 4px 14px;
  font-size: 13px;
  font-family: var(--mono);
  border-radius: 6px;
  background: var(--accent-bg);
  color: var(--accent);
  border: 1px solid var(--accent-border);
}
</style>
