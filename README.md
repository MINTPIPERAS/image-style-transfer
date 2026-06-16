# 🎨 Image Style Transfer — AI图像风格迁移 v2.0

基于 VGG16 深度神经网络的图像风格迁移 Web 应用，支持多用户体系、JWT 认证、历史记录持久化存储。

> 原始项目：[mozaffari-sadaf/image-style-transfer](https://github.com/mozaffari-sadaf/image-style-transfer)

---

## 📖 简介

图像风格迁移（Neural Style Transfer）是一种利用卷积神经网络（CNN）将一张图片的**艺术风格**与另一张图片的**内容**相结合的技术。由 Gatys et al. 在 2015 年首次提出（[A Neural Algorithm of Artistic Style](https://arxiv.org/abs/1508.06576)）。

v2.0 在原有风格迁移核心基础上，新增了完整的用户体系与数据持久化能力。

---

## ✨ v2.0 新功能

### 用户体系
- **注册/登录** — 用户名或邮箱登录，密码 bcrypt 加密存储
- **JWT 认证** — Access Token（2h）+ Refresh Token（7d），自动续期
- **个人中心** — 查看个人信息、修改密码
- **权限校验** — 所有核心接口需要登录后使用

### 数据持久化
- **SQLite 数据库** — 用户表 + 转换记录表（轻量级，免安装）
- **文件隔离存储** — 每个用户独立目录 `storage/user_{id}/`
- **历史记录** — 分页查看、大图预览、下载、删除（软删除）

### 体验模式
- 未登录用户仍可使用风格迁移（调用 `/api/transfer`），但不保存记录
- 登录后转换结果自动存入"我的作品"

---

## 🏗️ 项目结构

```
image-style-transfer/
├── app/                        # FastAPI 后端包 (v2.0)
│   ├── main.py                 # 应用入口（路由注册、CORS、生命周期）
│   ├── config.py               # 配置管理（.env 支持）
│   ├── database.py             # SQLAlchemy + SQLite 连接
│   ├── models/
│   │   ├── user.py             # 用户表 ORM 模型
│   │   └── conversion.py       # 转换记录表 ORM 模型
│   ├── schemas/
│   │   ├── user.py             # Pydantic 请求/响应校验
│   │   └── conversion.py       # 转换记录校验
│   ├── routers/
│   │   ├── auth.py             # 认证路由（注册/登录/刷新/登出）
│   │   ├── users.py            # 用户路由（个人信息/修改密码）
│   │   └── convert.py          # 转换路由（上传/提交/SSE/历史/删除 + 体验模式）
│   ├── services/
│   │   ├── auth_service.py     # 密码哈希、JWT 生成验证
│   │   └── convert_service.py  # 文件管理、记录 CRUD
│   └── middleware/
│       └── auth.py             # JWT 认证依赖注入
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── main.js             # 入口（Pinia + Router）
│   │   ├── App.vue             # 根布局
│   │   ├── style.css           # 全局样式
│   │   ├── api/
│   │   │   └── index.js        # Axios 实例 + JWT 拦截器
│   │   ├── stores/
│   │   │   └── auth.js         # Pinia 认证状态管理
│   │   ├── router/
│   │   │   └── index.js        # 路由配置
│   │   ├── components/
│   │   │   ├── Navbar.vue      # 导航栏（含登录状态）
│   │   │   ├── ImageUploadBox.vue
│   │   │   ├── ProgressPanel.vue
│   │   │   └── ResultDisplay.vue
│   │   └── views/
│   │       ├── HomePage.vue    # 首页
│   │       ├── ToolPage.vue    # 风格迁移工具页
│   │       ├── AboutPage.vue   # 关于页面
│   │       ├── LoginPage.vue   # 登录/注册页
│   │       ├── ProfilePage.vue # 个人中心
│   │       └── HistoryPage.vue # 历史作品
│   ├── vite.config.js
│   └── package.json
├── transfer_style.py           # 风格迁移核心算法
├── run_transfer.py             # 子进程执行脚本（stdout JSON 通信）
├── models/
│   └── vgg.py                  # VGG16 平均池化模型
├── utils/
│   ├── image_utils.py          # 图片加载与预处理
│   └── style_utils.py          # 风格损失（Gram 矩阵）
├── images/                     # 上传图片临时目录
├── outputs/                    # 转换结果输出目录
├── storage/                    # 用户隔离文件存储 (v2.0)
│   └── user_{id}/              # 按用户ID隔离
├── data.db                     # SQLite 数据库文件（自动创建）
├── .env                        # 环境变量配置
├── requirements.txt            # Python 依赖
└── docs/
    └── PRD.md                  # 产品需求文档
```

---

## 🚀 快速开始

### 环境要求

- **Python 3.8+**（推荐使用 Conda 虚拟环境 3.10版本以上Py可能会部分依赖不兼容 建议3.8 - 3.10）
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

> **注意**：`tensorflow==2.13.0` 需要根据 CUDA 版本调整。如无 GPU：
> ```bash
> pip install tensorflow-cpu==2.13.0
> ```

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 配置环境变量

编辑项目根目录的 `.env` 文件（已生成默认值）：

```env
SECRET_KEY=change-me-to-a-random-string  # 生产环境务必修改
DATABASE_URL=sqlite:///./data.db
STORAGE_DIR=./storage
MAX_UPLOAD_SIZE_MB=10
DEFAULT_ITERATIONS=10
FRONTEND_URL=http://localhost:5173
```

### 5. 启动后端

```bash
# 在项目根目录，conda 环境已激活
python -m app.main
```

后端运行在 `http://127.0.0.1:8000`，首次启动自动创建数据库表。

### 6. 启动前端

```bash
# 新终端，cd 到 frontend 目录
cd frontend
npm run dev
```

前端运行在 `http://localhost:5173`

### 7. 使用

浏览器访问 **http://localhost:5173**

1. 点击右上角"登录"注册账号
2. 进入"风格迁移"页面上传内容图和风格图
3. 点击"开始风格迁移"等待完成
4. 在"我的作品"中查看历史记录

---

## 📡 API 接口文档

### 认证与用户

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| `POST` | `/api/auth/register` | 否 | 注册（返回 Token） |
| `POST` | `/api/auth/login` | 否 | 登录（返回 Token） |
| `POST` | `/api/auth/refresh` | 否 | 刷新 Token |
| `POST` | `/api/auth/logout` | 是 | 登出 |
| `GET` | `/api/users/me` | 是 | 获取个人信息 |
| `PUT` | `/api/users/me/password` | 是 | 修改密码 |

#### 注册示例

```json
POST /api/auth/register
{
  "username": "demo",
  "email": "demo@example.com",
  "password": "123456"
}

Response 201:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### 登录示例

```json
POST /api/auth/login
{
  "login": "demo",          // 用户名或邮箱均可
  "password": "123456"
}

Response 200:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### 图片转换

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| `POST` | `/api/convert/upload` | 是 | 上传图片到用户存储 |
| `POST` | `/api/convert/submit` | 是 | 提交转换任务（multipart） |
| `GET` | `/api/convert/task/{id}` | 否 | SSE 进度流 |
| `GET` | `/api/convert/history` | 是 | 历史记录（分页） |
| `DELETE` | `/api/convert/record/{id}` | 是 | 删除记录 |
| `GET` | `/api/output/{filename}` | 否 | 获取结果图片 |
| `GET` | `/api/storage/user/{uid}/{fn}` | 否 | 获取用户存储文件 |

#### 上传提交转换（已登录）

```bash
curl -X POST http://127.0.0.1:8000/api/convert/submit \
  -H "Authorization: Bearer <access_token>" \
  -F "content_image=@photo.jpg" \
  -F "style_image=@style.png" \
  -F "style_type=custom"

# Response: { "task_id": "a1b2c3..." }
```

#### SSE 监听进度

```javascript
const es = new EventSource('http://127.0.0.1:8000/api/convert/task/{task_id}')
es.addEventListener('progress', e => console.log(JSON.parse(e.data)))
// { "iteration": 3, "total": 10, "loss": 1234.56 }
es.addEventListener('complete', e => console.log('done:', JSON.parse(e.data).filename))
```

#### 体验模式（无需登录）

```bash
curl -X POST http://127.0.0.1:8000/api/transfer \
  -F "content_image=@photo.jpg" \
  -F "style_image=@style.png"

# SSE: GET /api/transfer/stream/{task_id}
```

#### 历史记录

```json
GET /api/convert/history?page=1&page_size=12
Authorization: Bearer <access_token>

Response 200:
{
  "items": [
    {
      "id": 1,
      "original_filename": "photo.jpg",
      "style_type": "custom",
      "original_size": 245760,
      "result_size": 180224,
      "status": "completed",
      "created_at": "2026-06-16T12:00:00",
      "result_url": "/api/output/styled_abc.png",
      "original_url": "/api/storage/user/1/uuid_photo.jpg"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 12
}
```

### SSE 事件类型

| 事件 | 数据 | 说明 |
|------|------|------|
| `progress` | `{iteration, total, loss}` | 每轮迭代进度 |
| `complete` | `{filename}` | 处理完成，返回文件名 |
| `failed` | `{message}` | 处理失败，返回错误信息 |

---

## 🔐 安全设计

- **密码加密**：bcrypt 哈希，不可逆
- **JWT**：Access Token 2 小时，Refresh Token 7 天
- **文件隔离**：每个用户独立目录 `storage/user_{id}/`
- **文件校验**：仅允许 jpg/png/webp，限制 10MB
- **软删除**：删除记录标记 `is_deleted`，非物理删除
- **CORS**：仅允许配置的前端地址跨域

---

## 🧠 技术原理

1. **VGG16 特征提取** — 预训练 VGG16，浅层 `conv1` 层捕获纹理风格，深层捕获内容结构
2. **内容损失** — 生成图与内容图在高层特征的 MSE 差异
3. **风格损失** — Gram 矩阵衡量纹理统计差异
4. **L-BFGS 优化** — 拟牛顿法迭代优化像素值（默认 10 轮，每轮 20 次函数评估）

---

## 📦 技术栈

| 层级 | 技术 |
|------|------|
| 深度学习 | TensorFlow 2.13 / Keras 2.13 / SciPy |
| 后端框架 | FastAPI / Uvicorn |
| 认证 | python-jose (JWT) / passlib (bcrypt) |
| 数据库 | SQLite + SQLAlchemy ORM |
| 前端 | Vue 3 (Composition API) / Pinia / Vue Router / Vite |
| HTTP | Axios（JWT 自动拦截器） |
| 实时通信 | Server-Sent Events (SSE) |

---

## 🪲 已知问题与记录

### TF1 Graph Mode 变量冲突

本项目使用 `tf.compat.v1.disable_eager_execution()`（graph mode），每次调用会创建 VGG16 变量节点。
**解决方案**：每次风格迁移在独立子进程中执行（`asyncio.create_subprocess_exec` + `run_transfer.py`），进程退出后 TF 图彻底销毁。

### Vite 代理 SSE 缓冲

Vite 开发服务器默认缓冲 `text/event-stream` 响应。**解决方案**：SSE 直连后端 `127.0.0.1:8000`，不走 Vite 代理。

---

## 📄 许可证

基于原始项目 [mozaffari-sadaf/image-style-transfer](https://github.com/mozaffari-sadaf/image-style-transfer)，遵循 MIT 协议。
