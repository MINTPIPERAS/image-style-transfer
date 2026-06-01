# 🎨 Image Style Transfer — AI图像风格迁移

基于 VGG16 深度神经网络的图像风格迁移工具，提供 Web 交互界面，支持实时进度反馈。

> 原始项目：[mozaffari-sadaf/image-style-transfer](https://github.com/mozaffari-sadaf/image-style-transfer)

---

## 📖 简介

图像风格迁移（Neural Style Transfer）是一种利用卷积神经网络（CNN）将一张图片的**艺术风格**与另一张图片的**内容**相结合的技术。由 Gatys et al. 在 2015 年首次提出（[A Neural Algorithm of Artistic Style](https://arxiv.org/abs/1508.06576)）。

本项目在原作基础上进行了大幅重构，将命令行脚本升级为**前后端分离的 Web 应用**，提供直观的图形界面和实时处理反馈。

---

## 🆕 本项目的改进

### 架构升级

| 项目 | 原始版本 | 当前版本 |
|------|---------|---------|
| 运行方式 | CLI 命令行脚本 | Web 应用（FastAPI + Vue 3） |
| 参数传入 | `argparse` 命令行参数 | Web 表单上传图片 |
| 结果展示 | `matplotlib` 弹窗保存 | 浏览器在线预览 + 下载 |
| 进度反馈 | 终端 `print()` | 浏览器实时进度条 + Loss 曲线 |
| 图片管理 | 手动放入 `images/` 目录 | 任意位置上传，自动 UUID 存储 |

### 后端改进

- **FastAPI Web 框架** — 替代原始的 `argparse` CLI，提供 RESTful API
- **Subprocess 进程隔离** — 每次风格迁移在独立子进程中执行（`asyncio.create_subprocess_exec`），通过 stdout 管道 JSON 行通信，彻底避免 TF1 graph mode 的跨调用变量冲突
- **Server-Sent Events (SSE)** — 实时推送每轮迭代的 iteration / total / loss
- **文件管理** — 上传文件自动 UUID 前缀命名存入 `images/`，结果输出到 `outputs/`
- **进度回调** — `transfer_style.py` 新增 `progress_callback` 参数，每轮迭代后回调
- **跨域支持** — CORS 中间件，允许前端开发服务器跨域访问

### 前端改进

- **Vue 3 Composition API** — 组件化架构，`<script setup>` 语法
- **Vue Router** — 多页面路由：首页（Home）、风格迁移工具（Tool）、关于（About）
- **组件化 UI**：
  - `Navbar` — 毛玻璃导航栏，品牌标识 + 页面跳转
  - `ImageUploadBox` — 图片上传框，选中即预览，hover 显示更换/移除
  - `ProgressPanel` — 旋转加载动画 + 进度条 + 迭代轮数徽章 + Loss 显示
  - `ResultDisplay` — 结果图预览 + 下载 + 重新开始
- **玻璃卡片设计** — `backdrop-filter` 毛玻璃效果，黄/绿/粉三色晕染背景
- **响应式布局** — CSS Grid 左右分栏，视口高度约束
- **Vite 代理** — 开发环境代理 `/api` 到后端 `127.0.0.1:8000`

### 工程化

- 前后端分离，独立启动，Vite 代理转发
- `transfer_style.py` 从独立脚本重构为可调用模块（`process_image()` 函数）
- `requirements.txt` 补充 `fastapi`、`uvicorn`、`python-multipart`、`future` 依赖

---

## 🏗️ 项目结构

```
image-style-transfer/
├── app.py                    # FastAPI 后端入口（API + SSE + subprocess 管理）
├── run_transfer.py           # 子进程执行脚本（独立进程，stdout JSON 通信）
├── transfer_style.py         # 风格迁移核心模块
├── requirements.txt          # Python 依赖
├── models/
│   └── vgg.py                # VGG16 平均池化模型定义
├── utils/
│   ├── image_utils.py        # 图片加载与预处理工具
│   └── style_utils.py        # 风格损失（Gram 矩阵）计算
├── unittest/
│   └── test_style_transfer.py
├── images/                   # 示例图片 + 用户上传图片（UUID 前缀防冲突）
├── outputs/                  # 风格迁移结果（运行时生成）
└── frontend/                 # Vue 3 前端
    ├── index.html
    ├── vite.config.js        # Vite 配置（含 API 代理）
    ├── package.json
    └── src/
        ├── main.js           # 入口
        ├── App.vue           # 根布局（背景 + Navbar + router-view）
        ├── style.css         # 全局样式 + 晕染背景 + 玻璃卡片
        ├── router/
        │   └── index.js      # 路由配置
        ├── components/
        │   ├── Navbar.vue         # 导航栏
        │   ├── ImageUploadBox.vue # 图片上传框
        │   ├── ProgressPanel.vue  # 进度面板
        │   └── ResultDisplay.vue  # 结果展示
        └── views/
            ├── HomePage.vue       # 首页
            ├── ToolPage.vue       # 风格迁移工具页
            └── AboutPage.vue      # 关于页面
```

---

## 🚀 运行方法

### 环境要求

- **Python 3.8+**（推荐使用 Conda 虚拟环境）
- **Node.js 18+**（前端构建）
- 操作系统：Windows / macOS / Linux

### 1. 创建 Conda 虚拟环境

```bash
conda create -n style-transfer python=3.8
conda activate style-transfer
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

> **注意**：`tensorflow==2.13.0` 需要根据你的 CUDA 版本调整。如果没有 GPU，安装 CPU 版本：
> ```bash
> pip install tensorflow-cpu==2.13.0
> ```

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 启动后端

```bash
# 在项目根目录，确保 conda 环境已激活
python app.py
```

后端默认运行在 `http://127.0.0.1:8000`

### 5. 启动前端开发服务器

```bash
# 新开终端，cd 到 frontend 目录
cd frontend
npm run dev
```

前端默认运行在 `http://localhost:5173`

### 6. 打开浏览器

访问 **http://localhost:5173** 即可使用。

> ⚠️ 务必通过前端地址访问（`localhost:5173`），不要直接打开 HTML 文件，否则 API 代理不会生效。

---

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/transfer` | 上传内容图 + 风格图，返回 `task_id` |
| `GET` | `/api/transfer/stream/{task_id}` | SSE 流式推送处理进度 |
| `GET` | `/api/output/{filename}` | 获取结果图片文件 |

### SSE 事件类型

| 事件 | 数据 | 说明 |
|------|------|------|
| `progress` | `{iteration, total, loss}` | 每轮迭代进度 |
| `complete` | `{filename}` | 处理完成，返回文件名 |
| `failed` | `{message}` | 处理失败，返回错误信息 |

---

## 🪲 BUG 调试记录

### #1 核心难题：TF1 Graph Mode 变量冲突导致子进程崩溃

**现象**：后端连续返回 200 OK，但风格迁移无法正常完成。终端充斥以下 TF 警告：

```
Operation 'Variable/Assign' was changed by setting attribute after it was run
by a session. This mutation will have no effect, and will trigger an error in
the future. Either don't modify nodes after running them or create a new session.

→ Variable → Variable_1 → Variable_2 → ... → Variable_N → 进程崩溃
```

**根因**：原始项目使用 `tf.compat.v1.disable_eager_execution()` 运行在 TF1 graph mode。每次 `process_image()` 调用都会在全局默认图中创建 VGG16 变量节点。服务长期运行期间，多次调用导致变量名累积冲突，最终图操作无法执行。

原始 CLI 脚本没有此问题，因为每次运行是独立进程，退出即销毁 TF 图。

**❌ 错误路线 1**：在 `process_image()` 结尾加 `K.clear_session()` → 无效，线程环境下图状态无法完全重置。

**❌ 错误路线 2**：`multiprocessing.Process` + `mp.Queue` + progress_callback → 仍然失败。`mp.Queue` 在 Windows spawn 模式下通过后台 feeder 线程工作，progress_callback 将跨进程对象引入 TF 图线程上下文，仍导致阻塞。

**✅ 最终修复**：**`asyncio.create_subprocess_exec` + stdout 管道通信**

- 每次创建全新的 Python 子进程运行 `run_transfer.py`
- 进度通过 `print(JSON, flush=True)` 写到 stdout
- 父进程通过 `process.stdout.readline()` 异步逐行读取
- 子进程退出后 TF 图随进程彻底销毁

```
app.py (父进程)        run_transfer.py (子进程)
    │                        │
    ├─ subprocess_exec ────→ │ import transfer_style
    │                        │ process_image()
    │   stdout ◂──── JSON ── │   progress_callback
    │   .readline()          │     → print(JSON, flush)
    │                        │
    │   ◂── EOF / exit ────→ X (进程退出, TF 图销毁)
```

### #2 Vite 代理缓冲 SSE 导致前端收不到进度

**现象**：后端 SSE 正常推送，但浏览器 EventSource 超时断开，前端显示"请求失败"。

**根因**：Vite 开发服务器使用 `http-proxy` 转发请求，默认缓冲 `text/event-stream` 响应，导致 SSE 事件无法实时到达浏览器。

**修复**：SSE 连接绕过 Vite 代理，直连后端 `http://127.0.0.1:8000`（CORS 已开启）。POST 上传仍走代理，不影响。

### #3 前端上传后图片路径不一致

**现象**：用户期望上传图片存入 `images/` 目录，但实际存入了 `uploads/`。

**根因**：`app.py` 中 `UPLOAD_DIR = Path("uploads")`，与原始项目约定不一致。

**修复**：改为 `UPLOAD_DIR = Path("images")`，UUID 前缀命名保证不与示例图片冲突。

---

## 🧠 技术原理

1. **VGG16 特征提取** — 使用预训练 VGG16，浅层 `conv1` 层捕获纹理风格，深层捕获内容结构
2. **内容损失** — 生成图与内容图在高层特征的 MSE 差异
3. **风格损失** — 通过 Gram 矩阵衡量生成图与风格图在纹理统计上的差异
4. **L-BFGS 优化** — 拟牛顿法迭代优化像素值，最小化加权总损失（10 轮迭代，每轮 20 次函数评估）

---

## 📦 技术栈

| 层级 | 技术 |
|------|------|
| 深度学习 | TensorFlow 2.13 / Keras 2.13 / SciPy (L-BFGS) |
| 后端 | FastAPI / Uvicorn / SSE (Server-Sent Events) |
| 前端 | Vue 3 (Composition API) / Vue Router / Vite |
| 样式 | CSS Grid / backdrop-filter 毛玻璃 / CSS 动画 |

---

## 📄 许可证

本项目基于原始项目 [mozaffari-sadaf/image-style-transfer](https://github.com/mozaffari-sadaf/image-style-transfer) 修改，遵循 MIT 协议。
