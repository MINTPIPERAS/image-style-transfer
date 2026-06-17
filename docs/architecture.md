# 图像风格迁移系统 — 技术架构文档

> 版本 2.0 | 2026-06-17

---

## 目录

1. [总览](#1-总览)
2. [后端架构](#2-后端架构)
   - [项目结构](#21-项目结构)
   - [应用入口与生命周期](#22-应用入口与生命周期)
   - [配置系统](#23-配置系统)
   - [数据库层](#24-数据库层)
   - [数据模型](#25-数据模型)
   - [认证体系](#26-认证体系)
   - [路由模块](#27-路由模块)
   - [服务层](#28-服务层)
   - [风格迁移引擎](#29-风格迁移引擎)
3. [前端架构](#3-前端架构)
   - [项目结构](#31-项目结构)
   - [路由设计](#32-路由设计)
   - [全局状态管理](#33-全局状态管理)
   - [HTTP 通信层](#34-http-通信层)
   - [页面组件](#35-页面组件)
   - [通用组件](#36-通用组件)
4. [数据流](#4-数据流)
   - [认证流](#41-认证流)
   - [风格迁移流](#42-风格迁移流)
   - [历史记录流](#43-历史记录流)

---

## 1. 总览

```
┌──────────────────────────────────────────────────────────┐
│                    浏览器 (Vue 3 + Vite)                   │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌─────────────┐ │
│  │LoginPage│ │ToolPage  │ │HistoryPage│ │ AboutPage   │ │
│  │         │ │          │ │           │ │             │ │
│  └────┬────┘ └────┬─────┘ └─────┬─────┘ └──────┬──────┘ │
│       │           │             │               │        │
│  ┌────┴───────────┴─────────────┴───────────────┴────┐   │
│  │              api/index.js (Axios)                  │   │
│  │         JWT 自动附加 + 401 自动刷新                 │   │
│  └────────────────────────┬───────────────────────────┘   │
└───────────────────────────┼───────────────────────────────┘
                            │ HTTP + SSE
┌───────────────────────────┼───────────────────────────────┐
│                   FastAPI (端口 8000)                       │
│  ┌────────────────────────┴───────────────────────────┐   │
│  │  Middleware: CORS + JWT Bearer 鉴权                 │   │
│  ├──────────┬──────────┬───────────┬──────────────────┤   │
│  │auth.py   │users.py  │convert.py │  /api/styles     │   │
│  │注册/登录 │个人信息  │上传/转换  │  /api/preset     │   │
│  │刷新/登出 │改密码    │SSE/历史   │                  │   │
│  └────┬─────┴────┬─────┴─────┬─────┴────────┬─────────┘   │
│       │          │           │              │              │
│  ┌────┴──────────┴───────────┴──────────────┴────────┐    │
│  │            Service Layer                           │    │
│  │  auth_service.py  │  convert_service.py            │    │
│  └───────────────────┴───────────────────────────────┘    │
│  ┌────────────────────┬────────────────────────────────┐   │
│  │  SQLAlchemy ORM    │  subprocess → run_transfer.py  │   │
│  │  SQLite (data.db)  │  TensorFlow + VGG16 + L-BFGS   │   │
│  └────────────────────┴────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
```

---

## 2. 后端架构

### 2.1 项目结构

```
app/
├── main.py              # FastAPI 应用入口，注册路由与中间件
├── config.py            # 全局配置（数据库、JWT、预设风格等）
├── database.py          # SQLAlchemy 引擎与会话管理
├── models/
│   ├── user.py          # 用户 ORM 模型
│   └── conversion.py    # 转换记录 ORM 模型
├── schemas/
│   ├── user.py          # 用户请求/响应的 Pydantic 校验模型
│   └── conversion.py    # 转换记录的 Pydantic 校验模型
├── middleware/
│   └── auth.py          # JWT Bearer 鉴权依赖项
├── routers/
│   ├── auth.py          # 认证路由（注册/登录/刷新/登出）
│   ├── users.py         # 用户路由（个人信息/改密码）
│   └── convert.py       # 风格转换路由（上传/提交/SSE/历史/预设）
├── services/
│   ├── auth_service.py  # 密码哈希、JWT 签发/验证、用户注册/认证
│   └── convert_service.py # 文件存储、记录 CRUD、软删除

run_transfer.py           # 子进程入口脚本（进程隔离）
transfer_style.py         # 风格迁移核心算法

requirements.txt          # Python 依赖
```

### 2.2 应用入口与生命周期

**`app/main.py`** — FastAPI 应用工厂：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()   # 启动时自动创建所有数据库表
    yield
```

- 使用 `lifespan` 上下文管理器，替代已废弃的 `@app.on_event`
- 注册 CORS 中间件（允许 `http://localhost:5173` 跨域）
- 注册 3 个路由模块：`auth`、`users`、`convert`
- 附赠 `/api/health` 健康检查端点
- `__main__` 块：`uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)`

### 2.3 配置系统

**`app/config.py`** — 所有配置通过 `.env` 文件或环境变量覆盖：

| 键 | 默认值 | 说明 |
|---|---|---|
| `DATABASE_URL` | `sqlite:///{BASE_DIR}/data.db` | SQLite 文件路径 |
| `SECRET_KEY` | 占位符（生产务必修改） | JWT 签名密钥 |
| `ALGORITHM` | `HS256` | JWT 签名算法 |
| `ACCESS_TOKEN_EXPIRE` | `timedelta(hours=2)` | Access Token 有效期 |
| `REFRESH_TOKEN_EXPIRE` | `timedelta(days=7)` | Refresh Token 有效期 |
| `STORAGE_DIR` | `{BASE_DIR}/storage` | 用户文件存储根目录 |
| `MAX_UPLOAD_SIZE_MB` | `10` | 上传文件大小上限 |
| `DEFAULT_ITERATIONS` | `10` | 风格迁移默认迭代次数 |
| `FRONTEND_URL` | `http://localhost:5173` | CORS 允许的前端地址 |
| `PRESET_STYLES` | 4 种风格映射 | `{id: {name, file}}` 字典 |

预设风格字典：

```python
PRESET_STYLES = {
    "van_gogh":     {"name": "梵高",       "file": "style1.png"},
    "afremov":      {"name": "阿夫列莫夫", "file": "style2.png"},
    "picasso":      {"name": "毕加索",     "file": "style3.png"},
    "monet":        {"name": "莫奈",       "file": "style4.jpg"},
}
```

### 2.4 数据库层

**`app/database.py`** — SQLAlchemy 核心设施：

- 引擎：`create_engine(DATABASE_URL, connect_args={"check_same_thread": False})`
  - `check_same_thread=False` 是 SQLite 多线程访问的必要参数
- 会话工厂：`sessionmaker(autocommit=False, autoflush=False)`
- 声明基类：`declarative_base()` → 所有 ORM 模型继承自 `Base`
- `get_db()` — FastAPI 依赖生成器，请求结束时自动关闭会话
- `init_db()` — 调用 `Base.metadata.create_all()` 建表，幂等操作

### 2.5 数据模型

#### User（`app/models/user.py`）

| 列名 | 类型 | 约束 |
|---|---|---|
| `id` | `Integer` | PK，自增 |
| `username` | `String(50)` | UNIQUE，NOT NULL，INDEX |
| `email` | `String(100)` | UNIQUE，NOT NULL，INDEX |
| `password_hash` | `String(255)` | NOT NULL（bcrypt 哈希） |
| `created_at` | `DateTime` | `server_default=func.now()` |
| `updated_at` | `DateTime` | `server_default=func.now()`, `onupdate=func.now()` |

#### ConversionRecord（`app/models/conversion.py`）

| 列名 | 类型 | 约束 |
|---|---|---|
| `id` | `Integer` | PK，自增 |
| `user_id` | `Integer` | FK → users.id，CASCADE，INDEX |
| `original_filename` | `String(255)` | NOT NULL |
| `original_path` | `String(500)` | NOT NULL |
| `result_filename` | `String(255)` | NOT NULL |
| `result_path` | `String(500)` | NOT NULL |
| `style_type` | `String(50)` | NOT NULL，default="custom" |
| `original_size` | `Integer` | NOT NULL，default=0 |
| `result_size` | `Integer` | NOT NULL，default=0 |
| `status` | `String(20)` | NOT NULL，default="completed" |
| `created_at` | `DateTime` | `server_default=func.now()` |
| `is_deleted` | `Boolean` | default=False（软删除标记） |

### 2.6 认证体系

#### 密码哈希（`app/services/auth_service.py`）

使用 **bcrypt** 直接调用（非 passlib）：

```python
def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72]  # bcrypt 72 字节上限
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

def verify_password(plain_password, hashed_password) -> bool:
    plain_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(plain_bytes, hashed_bytes)
```

**为什么不用 passlib**：`passlib` 与 `bcrypt>=5.0` 不兼容（依赖 `bcrypt.__about__.__version__`，新版已移除）。

#### JWT 签发与验证

```python
def create_token(user_id: int, token_type: str = "access") -> str:
    expire = datetime.now(timezone.utc) + (ACCESS_TOKEN_EXPIRE if token_type == "access" else REFRESH_TOKEN_EXPIRE)
    payload = {
        "sub": str(user_id),   # ⚠️ python-jose 要求 sub 必须是字符串
        "type": token_type,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
```

- **Access Token**：2 小时有效期，用于 API 鉴权
- **Refresh Token**：7 天有效期，用于续期 Access Token
- `sub` 字段必须为字符串，鉴权时通过 `int(user_id_str)` 转回整数

#### 鉴权中间件（`app/middleware/auth.py`）

两个 FastAPI 依赖项：

- `get_current_user()` — **强制鉴权**。从 `Authorization: Bearer <token>` 解析 JWT → 验证 type=access → 查询数据库 → 返回 User 对象。任何步骤失败返回 401。
- `get_optional_user()` — **可选鉴权**。鉴权成功返回 User，失败返回 None（用于体验模式兼容）。

#### 用户注册与认证

```python
def register_user(db, data) -> User | None:
    # 检查用户名/邮箱唯一性 → 创建 User → 返回

def authenticate_user(db, login, password) -> User | None:
    # 支持用户名 OR 邮箱登录：filter(User.username == login) | (User.email == login)
```

### 2.7 路由模块

#### 认证路由（`app/routers/auth.py`）— 前缀 `/api/auth`

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/register` | 注册，直接返回 Token | 无 |
| POST | `/login` | 登录（用户名/邮箱），返回 Token | 无 |
| POST | `/refresh` | 用 Refresh Token 换新的 Access Token | 无 |
| POST | `/logout` | 登出（无状态，仅返回提示） | 需登录 |

#### 用户路由（`app/routers/users.py`）— 前缀 `/api/users`

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| GET | `/me` | 获取当前用户个人信息 | 需登录 |
| PUT | `/me/password` | 修改密码（需旧密码验证） | 需登录 |

#### 风格转换路由（`app/routers/convert.py`）— 前缀 `/api`

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| GET | `/styles` | 获取 4 种预设风格列表 | 无 |
| GET | `/preset/{filename}` | 获取预设风格缩略图 | 无 |
| POST | `/convert/upload` | 上传图片到用户隔离目录 | 需登录 |
| POST | `/convert/submit` | 提交风格迁移任务 | 需登录 |
| GET | `/convert/task/{task_id}` | SSE 进度流（登录用户） | 需登录 |
| GET | `/transfer/stream/{task_id}` | SSE 进度流（体验模式） | 无 |
| GET | `/output/{filename}` | 获取结果图片 | 无 |
| GET | `/storage/user/{user_id}/{filename}` | 获取用户上传原图 | 需登录 |
| GET | `/convert/history` | 分页获取历史记录 | 需登录 |
| DELETE | `/convert/record/{record_id}` | 软删除一条记录 | 需登录 |
| POST | `/transfer` | 体验模式风格迁移（无需登录） | 无 |

##### 提交任务的参数处理

`POST /api/convert/submit` 和 `POST /api/transfer` 支持 3 种风格指定方式：

1. **预设风格**：`style_preset="van_gogh"` → 后端从 `images/` 加载对应文件
2. **自定义上传**：`style_image=<File>` → 后端保存到 `images/` 临时目录
3. **未指定**：返回 400 "请选择预设风格或上传风格图片"

##### SSE 实时进度推送

```
Client: GET /api/convert/task/{task_id}
Server: text/event-stream

event: progress
data: {"iteration": 3, "total": 10, "loss": 1.23}

event: progress
data: {"iteration": 4, "total": 10, "loss": 0.98}

event: complete
data: {"filename": "styled_abc123.png"}
```

- 子进程 stdout 输出 JSON 行 → 父进程协程轮询管道 → 推入 `asyncio.Queue` → SSE 端点从队列消费
- 每秒发送 `: keepalive` 防止连接超时
- `complete` 或 `failed` 事件后自动关闭流

##### 任务注册表

```python
tasks: dict[str, dict] = {}       # task_id → {queue, status, user_id, ...}
tasks_lock = threading.Lock()     # 线程安全
```

- 任务完成后自动从字典移除（`_cleanup_task`）
- SSE 连接断开不影响子进程继续运行

### 2.8 服务层

#### 转换服务（`app/services/convert_service.py`）

| 函数 | 逻辑 |
|---|---|
| `get_user_storage_dir(user_id)` | 返回 `storage/user_{user_id}/`，不存在则创建 |
| `save_uploaded_file(user_id, bytes, filename)` | UUID 前缀防冲突，保存到隔离目录 |
| `create_conversion_record(db, ...)` | 创建一条 ConversionRecord |
| `get_user_records(db, user_id, page, page_size)` | 分页查询（排除已软删除，按时间倒序） |
| `soft_delete_record(db, record_id, user_id)` | 标记 `is_deleted=True` + 删除物理文件 |

### 2.9 风格迁移引擎

#### 子进程隔离设计

```
FastAPI 主进程
  │
  ├── asyncio.create_subprocess_exec(sys.executable, "run_transfer.py", ...)
  │
  └── run_transfer.py（独立进程）
        ├── import transfer_style.process_image
        ├── 每迭代通过 stdout 输出 JSON 进度行
        └── 完成/失败后 exit
```

**为什么用子进程？** TensorFlow 1.x 图模式（Graph Mode）要求在独立计算图中执行，否则 Variable 命名冲突。子进程天然隔离，无需管理进程池。

#### `run_transfer.py` — 子进程入口

```python
from transfer_style import process_image

def emit(event_type, data):
    print(json.dumps({"event": event_type, "data": data}), flush=True)

def progress_callback(iteration, total, loss):
    emit("progress", {"iteration": iteration, "total": total, "loss": round(loss, 2)})

if __name__ == "__main__":
    content_path, style_path, output_dir = sys.argv[1:4]
    result_filename = process_image(content_path, style_path, output_dir,
                                     progress_callback=progress_callback)
    emit("complete", {"filename": result_filename})
```

#### `transfer_style.py` — 核心算法

基于 Gatys et al. (2015) 的神经风格迁移：

```
1. 加载 VGG16（ImageNet 预训练权重），去掉全连接层
2. 构建内容模型 → 取 conv4_2 层特征图计算内容损失
3. 构建风格模型 → 取 conv1_1/2_1/3_1/4_1/5_1 五层 Gram 矩阵计算风格损失
4. 总损失: L_total = α·L_content + β·L_style  (α=1, β=10⁴)
5. L-BFGS 优化（SciPy fmin_l_bfgs_b）迭代更新生成图像像素值
6. 输出: outputs/styled_{uuid}.png
```

**内容损失**：MSE(生成图特征图, 内容图特征图) @ conv4_2  
**风格损失**：MSE(Gram(生成图), Gram(风格图)) @ 5 层加权求和  
**Gram 矩阵**：G_ij = Σ_k A_ik · A_jk，度量特征通道间的相关性，以此捕获纹理统计

---

## 3. 前端架构

### 3.1 项目结构

```
frontend/src/
├── main.js              # Vue 应用入口，挂载 Pinia + Router
├── App.vue              # 根组件（Navbar + 路由视图 + 背景）
├── style.css            # 全局样式（CSS 变量、玻璃卡片、主题色）
├── api/
│   └── index.js         # Axios 实例 + 拦截器
├── stores/
│   └── auth.js          # Pinia 认证状态管理
├── router/
│   └── index.js         # Vue Router 路由配置
├── components/
│   ├── Navbar.vue       # 全局导航栏
│   ├── ImageUploadBox.vue  # 图片上传/预览组件
│   ├── StyleSelector.vue   # 风格选择浮窗
│   ├── ProgressPanel.vue   # 进度条组件
│   └── ResultDisplay.vue   # 结果展示组件
└── views/
    ├── ToolPage.vue      # 风格迁移主页面
    ├── LoginPage.vue     # 登录/注册页
    ├── ProfilePage.vue   # 个人中心页
    ├── HistoryPage.vue   # 历史记录页
    └── AboutPage.vue     # 关于页面
```

### 3.2 路由设计

**`router/index.js`** — History 模式：

| 路径 | 组件 | 说明 |
|---|---|---|
| `/` | `ToolPage` | 主页（风格迁移） |
| `/tool` | `ToolPage` | 同上 |
| `/login` | `LoginPage` | 登录/注册 |
| `/profile` | `ProfilePage` | 个人中心 |
| `/history` | `HistoryPage` | 我的作品 |
| `/about` | `AboutPage` | 关于本项目 |

### 3.3 全局状态管理

**`stores/auth.js`** — Pinia Store（Composition API 风格）：

```javascript
// 状态
token: access_token (初始从 localStorage 恢复)
refreshToken: refresh_token
user: { id, username, email, created_at } | null

// 计算属性
isLoggedIn:  token 非空
accessToken: 返回 token 值

// 方法
login(login, password)       → POST /api/auth/login → 保存 token + user
register(username, email, password) → POST /api/auth/register
logout()                     → 清空状态 + localStorage + POST /api/auth/logout
fetchProfile()               → GET /api/users/me → 更新 user
refreshAccessToken()         → POST /api/auth/refresh → 更新 token
```

Token 持久化在 `localStorage`，页面刷新后自动恢复登录态。

### 3.4 HTTP 通信层

**`api/index.js`** — Axios 实例：

```javascript
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器：自动附加 Authorization header
api.interceptors.request.use(config => {
  const token = authStore.accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截器：401 自动刷新 token 并重试
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true
      await authStore.refreshAccessToken()
      error.config.headers.Authorization = `Bearer ${authStore.accessToken}`
      return api(error.config)
    }
    return Promise.reject(error)
  }
)
```

- 开发环境 Vite 代理 `/api` → `http://127.0.0.1:8000`

### 3.5 页面组件

#### ToolPage.vue — 风格迁移主页面

**状态变量**：

| 变量 | 类型 | 说明 |
|---|---|---|
| `contentImage` | `File \| null` | 内容图片文件 |
| `styleImage` | `File \| null` | 风格图片文件 |
| `styleMeta` | `{type, presetId?, name} \| null` | 风格元数据（预设/自定义） |
| `showStyleSelector` | `boolean` | 是否显示风格选择浮窗 |
| `stylePreviewUrl` | `string` | 风格预览图 blob URL |
| `isProcessing` | `boolean` | 是否正在处理中 |
| `resultImageUrl` | `string` | 结果图 blob URL |
| `progress` | `{iteration, total, loss}` | 当前进度 |
| `errorMessage` | `string` | 错误消息 |

**关键方法**：

- `handleStyleSelect(result)` — 接收 StyleSelector 的选择结果：
  - 预设：fetch 预设图片 → 转 File 对象 → 设置 `styleImage` + `styleMeta`
  - 自定义：直接使用上传的 File → 创建预览 URL → 设置 `styleMeta`
- `startTransfer()` — 发起转换：
  1. 根据登录状态选择 `/api/convert/submit` 或 `/api/transfer`
  2. FormData 中预设风格传 `style_preset` + `style_name`，自定义传 `style_image` + `style_name`
  3. POST 获取 `task_id`
  4. 连接 SSE 流监听进度
  5. `progress` 事件更新进度条
  6. `complete` 事件下载结果图并展示
  7. `failed` 事件显示错误

**布局**：左栏（图片选择 + 提交按钮）+ 右栏（进度/结果/空状态占位）

#### LoginPage.vue — 登录/注册双模式

- 同一个页面内切换「登录」和「注册」模式
- 登录支持用户名或邮箱
- 注册验证：用户名格式、邮箱、密码长度
- 成功后自动跳转到上一页或首页

#### HistoryPage.vue — 我的作品

**状态变量**：

| 变量 | 类型 | 说明 |
|---|---|---|
| `records` | `array` | 当前页记录列表 |
| `total` | `number` | 总记录数 |
| `page` | `number` | 当前页码 |
| `pageSize` | `number` | 每页条数（12） |
| `loading` | `boolean` | 加载状态 |
| `previewImage` | `string` | 大图预览 URL |
| `jumpPage` | `number` | 跳页输入框绑定值 |

**功能**：
- 网格布局展示所有转换结果（结果图缩略图 + 风格标签 + 日期 + 文件大小）
- 点击缩略图 → 全屏遮罩预览
- 下载 / 软删除按钮
- 分页栏：上一页 / 下一页 + 页码跳转输入框
- 页面加载时检查登录状态，未登录自动跳转

#### ProfilePage.vue — 个人中心

- 显示用户名、邮箱、注册时间
- 修改密码（需要旧密码 + 新密码两次确认）

#### AboutPage.vue — 关于本项目

- NST 技术原理解析（VGG16 分层特性 / 内容损失 / Gram 矩阵 / L-BFGS）
- 系统架构说明（子进程隔离 / SSE / 数据存储）
- 技术栈标签
- 参考文献（3 篇核心论文）

### 3.6 通用组件

#### Navbar.vue

- 固定顶部导航栏，毛玻璃效果
- 左侧 Logo + 导航链接（风格迁移、我的作品、关于）
- 右侧：已登录显示用户名 + 下拉菜单（个人中心、登出），未登录显示登录按钮
- 响应式：窄屏自动折叠

#### ImageUploadBox.vue

- Props：`label`（标题文字）、`modelValue`（File 或 null）
- Emits：`update:modelValue`
- 功能：
  - 空状态：虚线框 + 上传图标 + 标题
  - 已选状态：图片预览背景 + hover 显示更换/移除按钮
  - 内部管理 blob URL 生命周期（watch + onUnmounted）

#### StyleSelector.vue

- Emits：`select`（选中风格对象）、`close`（关闭浮窗）
- 双 Tab 切换：
  - **预设风格**：2×2 网格展示 4 种风格缩略图，点击选中 → 确认
  - **自定义上传**：上传区域 + 风格名称输入框
- 遮罩层点击关闭
- 黄绿清新色系

#### ProgressPanel.vue

- Props：`iteration`、`total`、`loss`、`visible`
- 显示当前迭代数 / 总数、损失值、进度条动画

#### ResultDisplay.vue

- Props：`imageUrl`、`visible`
- Emits：`restart`
- 展示最终结果图 + 重新开始按钮

---

## 4. 数据流

### 4.1 认证流

```
┌──────────┐    POST /api/auth/register    ┌──────────────┐
│          │──────────────────────────────> │              │
│          │   {username, email, password}  │  auth.py     │
│          │                                │              │
│  前端    │<────────────────────────────── │  register()  │
│          │   {access_token, refresh_token}│  → create    │
│          │                                │    Token     │
│  stores/ │                                └──────┬───────┘
│  auth.js │                                       │
│  保存    │                                ┌──────┴───────┐
│  token   │   POST /api/auth/login          │              │
│  + user  │──────────────────────────────> │  auth.py     │
│          │   {login, password}             │              │
│          │<────────────────────────────── │authenticate()│
│          │   {access_token, refresh_token} │  → bcrypt    │
│          │                                 │  → JWT       │
└──────────┘                                 └──────────────┘

后续请求自动附加 Authorization: Bearer <access_token>
401 时自动调用 /api/auth/refresh 续期，失败则清除登录态
```

### 4.2 风格迁移流

```
┌──────────┐                         ┌──────────────────────────┐
│  ToolPage │  POST /api/transfer     │  convert.py              │
│          │─────────────────────────>│                          │
│          │  FormData:               │  1. 解析 content_image   │
│          │    content_image          │  2. 解析 style（预设/上传）│
│          │    style_preset/          │  3. 保存文件到 images/   │
│          │    style_image            │  4. 启动子进程            │
│          │<─────────────────────────│  5. 返回 task_id          │
│          │  {"task_id":"abc123"}    │                          │
│          │                          │  asyncio.create_task(     │
│          │  GET /api/transfer/      │    _read_subprocess_     │
│          │      stream/abc123       │    stdout(...))           │
│          │─────────────────────────>│       │                  │
│          │                          │       │ 子进程            │
│          │  SSE: event: progress    │       │ run_transfer.py  │
│          │  data: {"iteration":1,   │<──────│ → VGG16+L-BFGS   │
│          │          "loss":5.2}     │  stdout JSON 行          │
│          │                          │       │                  │
│          │  SSE: event: complete    │       │                  │
│          │  data: {"filename":      │<──────│ 完成              │
│          │         "styled_xx.png"} │                          │
│          │                          │  6. 写 DB 记录           │
│          │  GET /api/output/        │  7. 清理 tasks 字典       │
│          │      styled_xx.png       │                          │
│          │─────────────────────────>│                          │
│          │<─── 结果图片 blob ───────│                          │
└──────────┘                         └──────────────────────────┘
```

### 4.3 历史记录流

```
┌─────────────┐  GET /api/convert/history?page=1&page_size=12  ┌────────────────┐
│ HistoryPage │───────────────────────────────────────────────>│ convert.py     │
│             │                                                │                │
│             │<───────────────────────────────────────────────│ get_user_      │
│             │  {items: [{id, style_type, result_url, ...}],  │ records()      │
│             │   total: 25, page: 1, page_size: 12}           │                │
│             │                                                │ convert_       │
│             │  结果图加载: img src="/api/output/xxx.png"      │ service.py     │
│             │───────────────────────────────────────────────>│                │
│             │<─────── 图片文件 ──────────────────────────────│                │
│             │                                                │                │
│             │  DELETE /api/convert/record/{id}               │                │
│             │───────────────────────────────────────────────>│ soft_delete_   │
│             │<────── {"message": "已删除"} ──────────────────│ record()       │
└─────────────┘                                                └────────────────┘
```

---

## 附录

### A. 关键技术选型

| 层 | 技术 | 理由 |
|---|---|---|
| 后端框架 | FastAPI | 原生 async、自动 OpenAPI 文档、Pydantic 集成 |
| ASGI 服务器 | Uvicorn | 轻量、支持 reload、与 FastAPI 最佳搭配 |
| ORM | SQLAlchemy | 成熟稳定、支持 SQLite |
| 数据库 | SQLite | 零配置、文件存储、适合单机部署 |
| 认证 | JWT (python-jose) | 无状态、适合 RESTful API |
| 密码 | bcrypt | 安全、自适应 salt |
| 子进程通信 | stdout JSON 行 | 简单可靠、天然隔离、无需 IPC 库 |
| 实时推送 | SSE | 单向流、自动重连、比 WebSocket 更轻量 |
| 前端框架 | Vue 3 Composition API | 逻辑复用、TypeScript 友好 |
| 构建工具 | Vite | 开发启动快、HMR 热更新 |
| 状态管理 | Pinia | Vue 3 官方推荐、轻量 |
| 样式方案 | CSS 变量 + 玻璃态 | 统一主题、无需 CSS 框架 |

### B. 文件存储路径约定

```
images/            # 原始图片（上传 + 预设风格图）
  CAT.png          # 示例内容图
  city.png         # 示例内容图
  style1.png       # 预设：梵高
  style2.png       # 预设：阿夫列莫夫
  style3.png       # 预设：毕加索
  style4.jpg       # 预设：莫奈
  {uuid}_{name}    # 用户上传的文件（UUID 前缀防冲突）

outputs/           # 风格迁移结果
  styled_{uuid}.png

storage/           # 用户隔离存储
  user_{id}/       # 每个用户独立目录
    {uuid}_{filename}

data.db            # SQLite 数据库（自动生成，.gitignore 排除）
```

### C. 启动命令

```bash
# 后端
conda activate ist310
python -m app.main
# → http://127.0.0.1:8000

# 前端
cd frontend
npm run dev
# → http://localhost:5173
```

### D. 参考文献

1. Gatys, L. A., Ecker, A. S., & Bethge, M. (2016). *Image Style Transfer Using Convolutional Neural Networks.* CVPR 2016.
2. Gatys, L. A., Ecker, A. S., & Bethge, M. (2015). *A Neural Algorithm of Artistic Style.* arXiv:1508.06576.
3. Simonyan, K., & Zisserman, A. (2014). *Very Deep Convolutional Networks for Large-Scale Image Recognition.* arXiv:1409.1556.
