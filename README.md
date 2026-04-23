# 安心宝 · AI Senior

> 面向中国老年人的 AI 智能养老平台 —— 用方言陪伴、健康守护、紧急救助和家庭关怀，让父母安心、子女放心。

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178c6)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/license-Proprietary-lightgrey)](#)

---

## 目录

- [项目简介](#项目简介)
- [核心差异化](#核心差异化)
- [仓库结构](#仓库结构)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [架构概览](#架构概览)
- [前端：三种访问模式](#前端三种访问模式)
- [第三方集成](#第三方集成)
- [测试与质量](#测试与质量)
- [生产部署](#生产部署)
- [API 文档与监控](#api-文档与监控)
- [开发约定](#开发约定)
- [产品与执行文档](#产品与执行文档)
- [路线图](#路线图)
- [安全说明](#安全说明)

---

## 项目简介

**安心宝**是一款面向中国老年群体（尤其是空巢、独居老人）的 AI 智能养老平台，集成 **语音 AI 交互、健康监测、用药管理、紧急求助、家庭关怀** 等功能，目标是：

- 让 **老人** 用最自然的方式（方言对话）享受陪伴和健康守护；
- 让 **子女** 通过"今日爸妈"日报和实时预警，每天 1 分钟掌握父母状态；
- 让 **平台** 通过 6 维数据聚合的"安心指数"，做出有温度的主动关怀。

> 本仓库代码注释、业务文案与产品文档均以**中文为主**，符合目标用户与开发团队的语言习惯。

---

## 核心差异化

| 卖点 | 实现 | 价值 |
|---|---|---|
| **方言陪伴** | `dialect_companion.py` 内置 150+ 模板，支持普通话 / 武汉话 / 鄂州话，按时段（早 / 午 / 晚 / 夜）和场景（问候 / 关怀 / 提醒 / 闲聊）分类 | 降低老年人学习门槛，建立情感粘性 |
| **安心指数 + "今日爸妈"日报** | `daily_report.py` 聚合情绪 / 健康 / 对话 / 活动 / 用药 / 社交 6 维数据，输出 1–10 分综合评分 | 子女一眼看懂父母今日状态 |
| **健康风险评分 + 食疗建议** | `health_evaluator.py` 评估血压、心率、血糖、体温等指标；`qwen_service.py` 生成无恐吓式建议，优先食疗而非药物 | 适合居家养老场景，避免医疗焦虑 |
| **AI 情感记忆系统** | `memory_service.py` 从对话中提炼用户画像、重要日期、人生故事 | 跨会话情感连续性 |
| **多通道紧急救助** | `emergency_service.py` 同时通过极光推送、阿里云短信、应用内消息通知家属 | 任意一个通道可达即可救助 |

---

## 仓库结构

```
AI_Senior/
├── anxinbao-server/      # Python FastAPI 后端（核心 API 服务）
│   ├── main.py           # 应用入口，注册 48+ 路由
│   ├── app/
│   │   ├── api/          # 48 个路由模块（共 730+ 端点）
│   │   ├── services/     # 43 个业务服务（AI、健康、紧急、家庭等）
│   │   ├── models/       # SQLAlchemy ORM（45 张数据表）
│   │   ├── schemas/      # Pydantic 请求/响应模型
│   │   └── core/         # 配置、安全、限流、缓存、调度、监控
│   ├── tests/            # 272+ 测试，覆盖率 ≥70%
│   ├── alembic/          # 数据库迁移
│   ├── docker-compose.yml
│   └── Dockerfile        # 多阶段构建，python:3.12-slim
├── anxinbao-pwa/         # React + TypeScript + Vite 前端 PWA
│   ├── src/pages/        # 10+ 页面（待机屏、对话、健康趋势、子女面板等）
│   ├── src/lib/api.ts    # 后端 API 客户端
│   └── public/           # PWA manifest、Service Worker
├── senior/               # 早期 Supabase MVP（11 个子系统，独立运行）
├── prd/                  # 产品需求与竞品分析
├── Product_plan/         # 核心卖点精细化、市场分析
├── Execute_Plan/         # 5 阶段交付方案、运维手册
├── 执行计划.md           # 6 阶段开发路线图（含进度）
├── CLAUDE.md             # 开发指南（身份模型、限流模式、权限校验）
└── README.md             # 本文档
```

---

## 技术栈

### 后端
- **框架**：FastAPI 0.115+ / Uvicorn / Pydantic v2
- **数据库**：PostgreSQL 16（生产）/ SQLite（开发）/ Alembic（迁移）
- **缓存**：Redis 7（可选，无则回退内存）
- **AI**：阿里云 DashScope（通义千问 `qwen-turbo`）
- **认证**：JWT（python-jose）+ bcrypt
- **限流**：slowapi
- **调度**：APScheduler
- **监控**：Prometheus + 结构化 JSON 日志
- **测试**：pytest + pytest-asyncio + pytest-cov + factory-boy

### 前端
- **框架**：React 19 + TypeScript 5.9
- **构建**：Vite 7
- **样式**：TailwindCSS 4
- **图表**：Recharts 3
- **图标**：Lucide React
- **PWA**：Service Worker + Web Manifest

### 基础设施
- **容器化**：Docker + Docker Compose
- **反向代理**：Nginx（生产环境）
- **CI/CD**：GitHub Actions

---

## 快速开始

### 前置要求
- Python ≥ 3.12
- Node.js ≥ 18
- PostgreSQL 16 / Redis 7（可选，开发可不用）

### 1) 启动后端

```bash
cd anxinbao-server
pip install -r requirements.txt
cp .env.example .env          # 填入 API 密钥（DASHSCOPE / XFYUN / SMS / 极光等）
python main.py                # 默认监听 0.0.0.0:8000
```

开发模式默认使用 SQLite（`DATABASE_URL=sqlite:///./anxinbao.db`），无需安装数据库即可启动。

### 2) 启动前端

```bash
cd anxinbao-pwa
npm install
npm run dev                   # Vite 开发服务器，http://localhost:3000
```

`/api/*` 请求会自动代理到 `http://localhost:8000`。

### 3) 访问应用

| 角色 | 入口 |
|---|---|
| 老人（默认） | http://localhost:3000 |
| 子女监护 | http://localhost:3000/?mode=child |
| 营销落地页 | http://localhost:3000/?mode=landing |

---

## 架构概览

### 后端三层架构

```
API 路由（app/api/）
        ↓
业务服务（app/services/）
        ↓
数据模型（app/models/database.py）
```

**48 个路由模块**按业务域组织，共暴露 **730+ 端点**，主要包括：

| 业务域 | 关键模块 | 代表端点 |
|---|---|---|
| 认证 | `auth.py` | `POST /register` `POST /login` `POST /refresh` |
| 对话 | `chat.py` `voice.py` | `POST /send_message` `POST /speech_to_text` `POST /text_to_speech` |
| 健康 | `health.py` `medication.py` | `POST /health_records` `GET /health_trend` |
| 紧急 | `emergency.py` `safety.py` | `POST /sos` `POST /fall_detection` |
| 家庭 | `family.py` `daily_report.py` | `GET /family_members` `GET /daily_report` |
| 设备 | `iot.py` `smart_home.py` | `POST /device_bind` `GET /device_status` |
| 主动关怀 | `proactive.py` | `POST /proactive_greeting` |
| 订阅 | `subscription.py` `payment.py` | `GET /subscription_plans` `POST /subscribe` |
| 实时通信 | `ws.py` | `WebSocket` |

**45 张数据表** 涵盖：用户认证、家庭绑定、对话历史、健康记录、用药管理、紧急事件、情感记忆、认知训练、生活记录（饮食 / 运动 / 睡眠 / 情绪）等。

### 关键身份模型

```
UserAuth.id     ↔ UserInfo.user_id     # JWT sub 字段
UserAuth.user_id → User.id              # 老人信息表
UserAuth.family_id → FamilyMember.id    # 家庭成员关系
```

> ⚠️ `UserInfo.user_id` 是 `UserAuth.id` 而非 `User.id`，详见 [CLAUDE.md](CLAUDE.md)。

---

## 前端三种访问模式

一套代码、URL 参数 `?mode=` 切换入口：

| URL | 模式 | 入口页面 | 适用场景 |
|---|---|---|---|
| `/` | elder（默认） | `StandbyScreen` | 老人触屏设备：6 个大按钮（紧急呼叫 / 语音陪伴 / 健康测量 / 用药提醒 / 视频通话 / 预约服务） |
| `/?mode=child` | child | `ChildDashboard` | 子女手机：今日概览、健康摘要、预警列表 |
| `/?mode=landing` | landing | `LandingPage` | 推广营销：产品介绍、注册入口 |

**主要页面**：`StandbyScreen` `ChatPage` `HealthTrendsPage` `ChildDashboard` `VideoCallPage` `NotificationsPage` `LandingPage` `LoginPage` `MedicationPage` `FamilyBindingGuide`。

---

## 第三方集成

| 服务 | 环境变量 | 用途 |
|---|---|---|
| **阿里云 DashScope** | `DASHSCOPE_API_KEY` | 通义千问 AI 多轮对话、情绪识别、食疗建议 |
| **科大讯飞** | `XFYUN_APPID` `XFYUN_API_KEY` `XFYUN_API_SECRET` | 语音识别 / 合成，方言（普通话 / 武汉话 / 鄂州话） |
| **阿里云短信** | `SMS_ACCESS_KEY_ID` `SMS_ACCESS_KEY_SECRET` | 健康告警、SOS 短信通知 |
| **极光推送** | `JPUSH_APP_KEY` `JPUSH_MASTER_SECRET` | 应用推送、紧急预警 |
| **SMTP 邮件** | `SMTP_HOST` `SMTP_USER` `SMTP_PASSWORD` | 邮件通知（备用通道） |

完整环境变量见 [`anxinbao-server/.env.example`](anxinbao-server/.env.example)。

---

## 测试与质量

```bash
cd anxinbao-server
pytest                                # 全量 272+ 测试
pytest tests/unit -v                  # 单元测试
pytest tests/api -v                   # API 测试
pytest -k "test_chat"                 # 按名称匹配
pytest --cov=app --cov-report=html    # 覆盖率报告（最低阈值 70%）
pytest -m "not slow"                  # 跳过慢速测试
```

**测试体系**：

| 类别 | 数量 | 覆盖范围 |
|---|---|---|
| `tests/unit/` | ~70 | 缓存、AI 服务、安全模块 |
| `tests/api/` | ~188 | 认证、聊天、健康、紧急、用药、家庭等 |
| `tests/integration/` | ~15 | 数据库 CRUD、级联、会话、通知 |

测试使用内存 SQLite（`sqlite://`），每个测试函数自动清理所有表；`asyncio_mode = auto` 已全局配置。

---

## 生产部署

### Docker 一键部署

```bash
cd anxinbao-server

# 开发环境：API + PostgreSQL + Redis
docker-compose up -d

# 生产环境：额外启动 Nginx 反向代理（含 SSL/TLS）
docker-compose --profile production up -d
```

完整生产部署步骤、SSL 证书申请、第三方 API 配置见：

- [`anxinbao-server/DEPLOYMENT.md`](anxinbao-server/DEPLOYMENT.md)
- [`Execute_Plan/01_部署方案.md`](Execute_Plan/01_部署方案.md)
- [`Execute_Plan/03_运维手册.md`](Execute_Plan/03_运维手册.md)

### 部署成本预估

| 阶段 | 用户规模 | 月度成本 |
|---|---|---|
| 起步 | 0–1000 | ¥200–500 |
| 增长 | 1000–10000 | ¥4000–13000 |
| 规模 | 10000+ | 按需扩容 |

---

## API 文档与监控

| 路径 | 说明 |
|---|---|
| `/docs` | Swagger UI 交互式文档 |
| `/redoc` | ReDoc 文档 |
| `/health` | 简单健康检查 |
| `/health/live` | Kubernetes Liveness Probe |
| `/health/ready` | Kubernetes Readiness Probe |
| `/health/detailed` | 数据库 / Redis / 调度器详细状态 |
| `/metrics` | Prometheus 指标（请求量、延迟、AI 调用、消息数等） |

---

## 开发约定

### 限流装饰器顺序

```python
@router.post("/endpoint")
@limiter.limit("5/minute")            # 紧跟在路由装饰器后
async def handler(
    request: Request,                 # 第一个参数必须命名为 request
    body: SomeRequest,                # Pydantic body 不能命名为 request
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ...
```

> GET 端点查询参数须使用 `Query()` 而非 `Field()`。

### 权限校验

私有 helper 函数 + 角色守卫，详见 `app/api/daily_report.py::_check_elder_access`：

```python
def _check_elder_access(elder_id, current_user, db):
    # admin → 全量
    # elder → 仅自己（UserAuth.user_id == elder_id）
    # family → 必须有 FamilyMember 绑定
    # device → 仅绑定老人
```

### Agent 角色提示词

`.claude/prompts/` 目录提供专用角色提示词（`developer` / `backend_engineer` / `db_engineer` / `devops_engineer` / `qa_engineer` / `ai_engineer` / `product_manager` / `designer`），便于将工作限定到特定领域。

---

## 产品与执行文档

| 目录 / 文件 | 内容 |
|---|---|
| [`prd/`](prd/) | 产品需求规格、竞品分析、功能完成度评估、TODO 清单 |
| [`Product_plan/`](Product_plan/) | 核心卖点精细化方案、市场创业机会分析 |
| [`Execute_Plan/`](Execute_Plan/) | 5 阶段交付方案：部署 / 推广 / 运维 / 时间线 / 第一周行动清单 |
| [`执行计划.md`](执行计划.md) | 6 阶段开发路线图与进度（已完成阶段 1–5） |
| [`CLAUDE.md`](CLAUDE.md) | 工程指南（身份模型、限流模式、权限校验、测试 Fixtures） |

---

## 路线图

| 阶段 | 状态 | 关键交付 |
|---|---|---|
| 一、代码修复与基础设施加固 | ✅ | 修复 100+ 引号 bug、数据库迁移（8→45 表）、Redis 集成 |
| 二、后端功能补全 | ✅ | 健康评估、紧急服务、家庭绑定、对话持久化、通知服务 |
| 三、前后端集成 | 🟡 大部分完成 | 健康 / 日报 / 通知 API 已对接，待完善视频通话 WebSocket、TTS 自动播放 |
| 四、测试体系建设 | ✅ | 272+ 测试，覆盖率 ≥70% |
| 五、生产就绪 | ✅ | 安全加固、性能优化、Prometheus 监控、Docker 多阶段构建、CI/CD |
| 六、增强功能开发 | 🔵 规划中 | 主动交互、情感记忆、药品 OCR、认知训练游戏 |

### 北极星指标

| 指标 | 3 月目标 | 6 月目标 |
|---|---|---|
| 安心日报打开率 | 60% | 75% |
| 老人日均对话次数 | 5 次 | 8 次 |
| 次月留存率 | 40% | 55% |
| 付费转化率 | 8% | 15% |
| NPS 净推荐值 | 30 | 50 |

---

## 安全说明

- **生产前必须** 重新生成 `JWT_SECRET_KEY`（至少 32 字符随机）。
- **不要** 将 `.env`、`*.db`、`uploads/` 等含敏感信息的文件提交到仓库（已通过 `.gitignore` 排除）。
- 默认启用安全响应头（X-Frame-Options、X-Content-Type-Options、HSTS 等）。
- 限流规则参考：登录 5/min、注册 3/min、SOS 10/min、聊天 30/min。
- 账户锁定：登录失败超阈值后临时锁定，避免暴力破解。

---

## License

本项目代码及产品文档版权归原作者所有，未经书面许可不得用于商业用途。

---

> **关于命名**：「安心宝」取自「让父母安心、让子女放心」。技术再先进，也要让七十岁的老人能用、愿意用、用得开心 —— 这是我们设计每一处交互的初心。

