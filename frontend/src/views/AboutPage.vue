<script setup>
</script>

<template>
  <div class="about-page">
    <div class="glass-card about-card">
      <h1>关于本项目</h1>

      <section>
        <h2>什么是神经风格迁移？</h2>
        <p>
          神经风格迁移（Neural Style Transfer，NST）是一种利用卷积神经网络（CNN）
          将一张图片的<strong>艺术风格</strong>与另一张图片的<strong>内容</strong>相融合的技术。
          它由 Leon A. Gatys 等人在 2015 年的论文
          <em>"A Neural Algorithm of Artistic Style"</em> 中首次提出，
          开创了 AI 辅助艺术创作的全新范式。
        </p>
        <p>
          与传统的图像滤镜不同，NST 不是简单的像素级叠加，而是从神经网络内部
          特征表示出发，分别建模内容与风格的"感知"差异，通过优化生成一张新图片
          来同时匹配两个目标。
        </p>
      </section>

      <section>
        <h2>核心原理</h2>

        <h3>1. VGG16 特征提取网络</h3>
        <p>
          本系统使用在 ImageNet 上预训练的 <strong>VGG16</strong> 卷积网络作为特征提取器。
          VGG16 由 13 个卷积层和 3 个全连接层堆叠而成，卷积层之间穿插着最大池化层。
          我们只使用其卷积部分（去掉全连接分类头），因为卷积层学到的特征具有层次化结构：
        </p>
        <ul>
          <li><strong>浅层（conv1_1 ~ conv2_2）</strong>：捕获边缘、角点、颜色梯度等低级视觉特征，对纹理和笔触敏感</li>
          <li><strong>中层（conv3_1 ~ conv4_4）</strong>：组合低级特征形成形状、图案等中级语义，兼顾内容与风格</li>
          <li><strong>深层（conv5_1 ~ conv5_4）</strong>：编码高级语义信息，如物体整体结构和空间布局，主要反映图像内容</li>
        </ul>
        <p>
          正是这种<strong>浅层偏风格、深层偏内容</strong>的特性，使我们能够从同一个网络中
          分别提取风格表征和内容表征。
        </p>

        <h3>2. 内容损失（Content Loss）</h3>
        <p>
          内容损失衡量生成图像与原内容图像在高层特征空间中的差异。具体做法是：
        </p>
        <ol>
          <li>将内容图像和生成图像分别送入 VGG16</li>
          <li>取出某一深层（如 conv4_2）输出的特征图 <strong>F</strong>（内容图）和 <strong>P</strong>（生成图）</li>
          <li>计算两者的均方误差（MSE）：<code>L<sub>content</sub> = ½ Σ(F<sub>ij</sub> − P<sub>ij</sub>)²</code></li>
        </ol>
        <p>
          MSE 越小，说明生成图在高层语义上与内容图越接近——物体仍在原位，
          整体构图得以保留，但纹理、颜色可以自由变化。
        </p>

        <h3>3. 风格损失与 Gram 矩阵</h3>
        <p>
          风格损失是 NST 最核心的创新。它不直接比较像素，而是比较
          <strong>特征通道之间的相关性</strong>，这种相关性通过 <strong>Gram 矩阵</strong> 来度量：
        </p>
        <p>
          对于某一层的特征图，假设有 C 个通道、每个通道有 H×W 个激活值，
          将其展平为 C×(H·W) 的矩阵 <strong>A</strong>。Gram 矩阵定义为：
          <code>G<sub>ij</sub> = Σ<sub>k</sub> A<sub>ik</sub> · A<sub>jk</sub></code>
          ——即第 i 和第 j 通道激活值的内积。
        </p>
        <p>
          Gram 矩阵的每个元素表示两个通道特征<strong>同时激活</strong>的程度：
          如果一幅画的"红色"通道激活时"曲线纹理"通道也倾向激活，
          Gram 矩阵就会捕获这种共现关系。这种统计信息不依赖空间位置，
          因此能描述"风格"而不受内容构图的干扰。
        </p>
        <p>
          风格损失是多层的加权组合，对 conv1_1、conv2_1、conv3_1、conv4_1、conv5_1
          五个层分别计算 Gram 矩阵差异，每层权重相等：
        </p>
        <code class="formula">L<sub>style</sub> = Σ<sub>ℓ</sub> w<sub>ℓ</sub> · ¼C<sub>ℓ</sub>² · Σ(G<sub>ℓ</sub> − A<sub>ℓ</sub>)²</code>

        <h3>4. 总损失与 L-BFGS 优化</h3>
        <p>
          最终目标是让生成图同时满足两个条件——内容像原图、风格像参考图。
          总损失函数为两者的线性组合：
        </p>
        <code class="formula">L<sub>total</sub> = α · L<sub>content</sub> + β · L<sub>style</sub></code>
        <p>
          其中 α 和 β 控制内容/风格的比例。α/β 越大，结果越偏向内容/风格。
          本系统默认 α=1, β=10⁴，这个比例源自原论文，在实践中效果最好。
        </p>
        <p>
          优化算法选用 <strong>L-BFGS</strong>（Limited-memory Broyden–Fletcher–Goldfarb–Shanno），
          一种拟牛顿法。相比常用的 Adam/SGD，L-BFGS 在这种"单张图像优化"任务中
          收敛更快、结果更稳定——因为我们优化的不是网络权重，而是图像本身的像素值，
          解空间相对平滑，适合二阶方法。
        </p>
      </section>

      <section>
        <h2>系统架构</h2>

        <h3>子进程隔离设计</h3>
        <p>
          TensorFlow 1.x 的图模式（Graph Mode）要求每次调用都在独立的计算图中执行，
          否则会出现 Variable 命名冲突。因此后端通过
          <code>asyncio.create_subprocess_exec</code> 为每个转换任务
          启动一个<strong>独立的 Python 子进程</strong>，任务完成后自动退出，
          天然实现了图隔离，无需管理进程池。
        </p>

        <h3>实时进度推送（SSE）</h3>
        <p>
          子进程通过 stdout 逐行输出 JSON 格式的进度/完成/失败事件，父进程轮询管道、
          推入 <code>asyncio.Queue</code>，前端通过
          <strong>Server-Sent Events（SSE）</strong> 长连接实时接收进度。
          相比 WebSocket，SSE 实现更轻量、天然支持自动重连，非常适合这种单向推送场景。
        </p>

        <h3>数据存储</h3>
        <p>
          用户账户和转换历史使用 <strong>SQLite</strong> 持久化存储（<code>data.db</code>），
          上传文件以 UUID 前缀命名保存到用户隔离目录（<code>storage/user_{id}/</code>），
          产出图输出到 <code>outputs/</code>。删除记录采用软删除策略，
          便于数据恢复。
        </p>
      </section>

      <section>
        <h2>技术栈</h2>
        <div class="tech-tags">
          <span class="tag">Python 3.10</span>
          <span class="tag">TensorFlow 2.13</span>
          <span class="tag">Keras</span>
          <span class="tag">VGG16</span>
          <span class="tag">SciPy (L-BFGS)</span>
          <span class="tag">FastAPI</span>
          <span class="tag">Uvicorn</span>
          <span class="tag">SQLAlchemy</span>
          <span class="tag">SQLite</span>
          <span class="tag">JWT (python-jose)</span>
          <span class="tag">bcrypt</span>
          <span class="tag">Vue 3 (Composition API)</span>
          <span class="tag">Vite</span>
          <span class="tag">Pinia</span>
          <span class="tag">Axios</span>
          <span class="tag">SSE</span>
        </div>
      </section>

      <section>
        <h2>参考文献</h2>
        <ol class="refs">
          <li>Gatys, L. A., Ecker, A. S., & Bethge, M. (2016).
            <em>Image Style Transfer Using Convolutional Neural Networks.</em> CVPR 2016.</li>
          <li>Gatys, L. A., Ecker, A. S., & Bethge, M. (2015).
            <em>A Neural Algorithm of Artistic Style.</em> arXiv:1508.06576.</li>
          <li>Simonyan, K., & Zisserman, A. (2014).
            <em>Very Deep Convolutional Networks for Large-Scale Image Recognition.</em> arXiv:1409.1556.</li>
        </ol>
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
  height: 100%;
  max-width: 860px;
  margin: 0 auto;
  padding: 100px 24px 60px;
  overflow-y: auto;
  box-sizing: border-box;
  scrollbar-width: none;           /* Firefox */
  -ms-overflow-style: none;        /* IE/Edge */
}

.about-page::-webkit-scrollbar {
  display: none;                   /* Chrome/Safari/Edge */
}

.about-card {
  padding: 48px;
}

@media (max-width: 600px) {
  .about-card {
    padding: 28px 20px;
  }
}

.about-card h1 {
  font-family: var(--heading);
  font-size: 32px;
  color: var(--text-h);
  margin: 0 0 32px;
  text-align: center;
}

section {
  margin-bottom: 32px;
}

section h2 {
  font-family: var(--heading);
  font-size: 20px;
  color: var(--accent);
  margin: 0 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

section h3 {
  font-family: var(--heading);
  font-size: 16px;
  color: var(--text-h);
  margin: 20px 0 8px;
}

section p {
  font-size: 15px;
  line-height: 1.85;
  color: var(--text);
  margin: 0 0 10px;
}

section ul, section ol {
  margin: 0 0 10px;
  padding-left: 22px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

section li {
  font-size: 14px;
  line-height: 1.75;
  color: var(--text);
}

code {
  font-family: var(--mono);
  font-size: 13px;
  background: var(--accent-bg);
  padding: 1px 6px;
  border-radius: 4px;
  color: var(--accent);
  white-space: nowrap;
}

.formula {
  display: block;
  font-family: var(--mono);
  font-size: 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  padding: 10px 16px;
  margin: 8px 0 12px;
  border-radius: 6px;
  overflow-x: auto;
  white-space: nowrap;
  color: var(--text-h);
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  padding: 5px 14px;
  font-size: 13px;
  font-family: var(--mono);
  border-radius: 6px;
  background: var(--accent-bg);
  color: var(--accent);
  border: 1px solid var(--accent-border);
}

.refs {
  padding-left: 22px !important;
}

.refs li {
  font-size: 13px !important;
  line-height: 1.7 !important;
  color: var(--text);
  opacity: 0.7;
}
</style>
