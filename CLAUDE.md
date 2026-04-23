# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

安心宝是一款面向中国老年人的AI智能养老平台，集成语音AI交互、健康监测、用药管理、紧急求助和家庭关怀等功能。**代码注释和业务逻辑以中文为主。**

仓库包含两个主应用和一个早期MVP：
- **anxinbao-pwa/** — React前端（PWA）
- **anxinbao-server/** — Python FastAPI后端
- **senior/** — 早期基于Supabase的MVP（独立运行）
- **prd/**、**Product_plan/**、**Execute_Plan/** — 产品文档、规划和落地执行方案

## 常用命令

### 前端 (anxinbao-pwa/)

```bash
cd anxinbao-pwa
npm install
npm run dev          # Vite开发服务器，端口3000，/api代理到localhost:8000
npm run build        # tsc -b && vite build（TypeScript编译 + Vite打包）
npm run lint         # eslint .
```

### 后端 (anxinbao-server/)

```bash
cd anxinbao-server
pip install -r requirements.txt
cp .env.example .env   # 配置API密钥等（必须）
python main.py         # 启动uvicorn，端口8000
```

开发环境默认使用SQLite（`DATABASE_URL=sqlite:///./anxinbao.db`）；测试环境使用内存SQLite（`sqlite://`）。

### 测试（后端）

```bash
cd anxinbao-server
pytest                                               # 运行所有测试（共330+个）
pytest tests/unit -v                                 # 仅单元测试
pytest tests/api -v                                  # 仅API测试
pytest -k "test_function_name"                       # 运行单个测试（按名称匹配）
pytest tests/api/test_chat.py::TestChatAPI::test_send_message  # 运行单个测试（完整路径）
pytest -m "not slow"                                 # 跳过慢速测试
pytest --cov=app --cov-report=html                   # 带覆盖率报告（最低阈值70%）
```

测试标记：`unit`、`integration`、`api`、`slow`、`security`、`ai`。`asyncio_mode = auto` 已全局配置，无需单测 async 装饰器。`addopts = -v --tb=short --strict-markers -ra`（pytest.ini 自动生效）。

### Docker

```bash
cd anxinbao-server
docker-compose up -d                       # 开发环境：api + PostgreSQL + Redis
docker-compose --profile production up -d  # 生产环境：额外启动Nginx反向代理
```

## 架构说明

### 后端 (FastAPI) — 三层架构

**API路由 → 服务层 → 数据模型**

- **`main.py`** — 应用入口。注册48+个路由、中间件（CORS、slowapi限流、Prometheus、请求日志）以及生命周期事件（数据库初始化、调度器启停）。
- **`app/api/`** — 48个路由模块，每个文件导出一个 `router`，按业务领域划分。
- **`app/services/`** — 43个业务逻辑服务。核心服务：
  - `qwen_service.py` — 阿里通义千问AI对话，含情感识别、食疗建议、主动关怀
  - `xfyun_service.py` — 科大讯飞语音识别/合成，支持方言（普通话、武汉话、鄂州话）
  - `dialect_companion.py` — 方言情感陪伴模板库（150+模板，核心卖点）
  - `daily_report.py` — "今日爸妈"安心日报，聚合情绪/健康/对话/活动，生成安心指数1-10
  - `health_evaluator.py` — 健康风险评分（1-10分），超阈值自动通知家属
  - `emergency_service.py` — SOS求助和跌倒检测事件处理
- **`app/models/database.py`** — SQLAlchemy ORM模型（所有表定义）和 `init_db()`
- **`app/schemas/`** — Pydantic请求/响应模式定义
- **`app/core/`** — 基础设施层：
  - `config.py` — Pydantic Settings，通过 `get_settings()` 获取，从 `.env` 加载
  - `security.py` — JWT令牌创建/验证、`get_current_user` 依赖、`UserInfo` 模型
  - `limiter.py` — slowapi限流器实例（`debug=True`时自动禁用，测试无需处理限流）
  - `cache.py` — Redis客户端封装（`ConversationStore` 支持Redis/内存双模式）
  - `metrics.py` — Prometheus中间件和健康探针端点
  - `scheduler.py` — APScheduler定时任务（健康检查、设备监控、用药提醒）
  - `deps.py` — FastAPI依赖注入：`get_db`（SQLAlchemy Session）、角色守卫（`get_current_elder`、`get_current_family`、`get_current_admin`）

### 关键身份模型（容易踩坑）

`UserInfo.user_id` 是 `UserAuth.id`（认证表主键），**不是** `User.id`（老人信息表主键）。

```
UserAuth.id  ←→  UserInfo.user_id（JWT sub字段，字符串）
UserAuth.user_id  →  User.id（老人信息）
UserAuth.family_id  →  FamilyMember.id  →  FamilyMember.user_id（关联老人）
```

查询当前用户绑定的老人时，需要通过 `UserAuth` 中转：
```python
auth = db.query(UserAuth).filter(UserAuth.id == int(current_user.user_id)).first()
elder_id = auth.user_id  # 老人的 User.id
```

### 限流装饰器模式

**必须严格遵循此顺序**，否则 slowapi 会报 `No "request" argument` 错误：

```python
@router.post("/endpoint")
@limiter.limit("5/minute")           # 紧跟在路由装饰器后
async def handler(
    request: Request,                # 第一个参数必须命名为 request
    body: SomeRequest,               # Pydantic body 用 body/其他名称，不能命名为 request
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
```

GET端点的查询参数须用 `Query()` 而非 `Field()`（否则被误判为body）。

### 权限校验模式

日报等需要访问控制的接口使用私有 helper 函数模式（见 `app/api/daily_report.py`）：

```python
def _check_elder_access(elder_id, current_user, db):
    # admin → 全量
    # elder → 只能查自己（UserAuth.user_id == elder_id）
    # family → 必须有 FamilyMember 绑定（FamilyMember.user_id == elder_id）
    # device → 只能查绑定老人
```

### 前端 (React + TypeScript + Vite)

**访问模式**通过 URL 参数 `?mode=` 控制，一套代码三个入口：

| URL | 模式 | 初始页面 |
|-----|------|---------|
| `/`（默认） | elder | StandbyScreen（待机界面） |
| `/?mode=child` | child | ChildDashboard（子女监护面板） |
| `/?mode=landing` | landing | LandingPage（营销落地页） |

- **`src/pages/`** — 7个页面：StandbyScreen、ChatPage、HealthTrendsPage、ChildDashboard、VideoCallPage、NotificationsPage、LandingPage（营销落地页）
- **`src/lib/api.ts`** — 后端API调用客户端，`getUserId()` / `getFamilyId()` 在此定义
- UI使用TailwindCSS 4，Recharts数据可视化，Lucide图标

### 第三方集成

| 服务 | 环境变量 | 用途 |
|------|---------|------|
| 阿里云DashScope | `DASHSCOPE_API_KEY` | 通义千问AI对话（`qwen-turbo`） |
| 科大讯飞 | `XFYUN_APPID`、`XFYUN_API_KEY`、`XFYUN_API_SECRET` | 语音识别/合成，方言支持 |
| 阿里云短信 | `SMS_ACCESS_KEY_ID/SECRET` | 健康告警通知 |
| 极光推送 | `JPUSH_APP_KEY/MASTER_SECRET` | 消息推送 |

### API文档与监控

```
/docs            Swagger UI
/redoc           ReDoc
/health          简单健康检查
/health/detailed 详细状态（数据库、Redis、调度器）
/metrics         Prometheus指标
```

### 测试Fixtures（tests/conftest.py）

| Fixture | 角色 | user_id来源 |
|---------|------|------------|
| `auth_headers` | elder | `str(sample_user_auth.id)` |
| `family_auth_headers` | family | `str(sample_family_auth.id)` |
| `admin_auth_headers` | admin | 硬编码 `"admin-001"` |
| `device_auth_headers` | device | `str(sample_device_auth.id)` |

数据库测试使用内存SQLite（`sqlite://`），通过 `override_get_db` fixture 注入，每个测试函数清理所有表。

## Agent角色提示词

`.claude/prompts/` 目录包含专用角色提示词（developer、backend_engineer、db_engineer、devops_engineer、qa_engineer、ai_engineer、product_manager、designer），可用于将工作限定到特定领域。
