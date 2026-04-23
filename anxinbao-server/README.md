# 安心宝云端服务

[![CI/CD](https://github.com/your-org/anxinbao-server/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/your-org/anxinbao-server/actions)
[![Coverage](https://codecov.io/gh/your-org/anxinbao-server/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/anxinbao-server)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

智能健康陪聊音箱后端服务 - 专为老年人设计的AI健康伴侣

## 核心特性

### AI对话服务
- ✅ 通义千问AI多轮对话
- ✅ 情绪识别与关怀（孤独/焦虑/悲伤/积极）
- ✅ 个性化对话记忆
- ✅ 主动关怀消息生成
- ✅ 健康风险自动评估（1-10分）
- ✅ 智能食疗建议

### 语音服务
- ✅ 科大讯飞语音识别（ASR）
- ✅ 科大讯飞语音合成（TTS）
- ✅ 方言支持（普通话/武汉话/鄂州话）

### 安全认证
- ✅ JWT双令牌认证（access + refresh）
- ✅ 设备认证支持
- ✅ 基于角色的访问控制（RBAC）
- ✅ 敏感数据加密存储
- ✅ API限流保护
- ✅ 审计日志

### 监控运维
- ✅ Prometheus指标导出
- ✅ 结构化JSON日志
- ✅ 健康检查探针（K8s兼容）
- ✅ Docker容器化部署
- ✅ CI/CD自动化流水线

## 目录结构

```
anxinbao-server/
├── app/
│   ├── api/                    # API路由
│   │   ├── auth.py            # 认证接口
│   │   ├── chat.py            # 对话接口
│   │   ├── voice.py           # 语音接口
│   │   ├── notify.py          # 通知接口
│   │   ├── users.py           # 用户管理
│   │   ├── health.py          # 健康数据
│   │   └── video.py           # 视频通话
│   ├── core/                   # 核心模块
│   │   ├── config.py          # 配置管理
│   │   ├── security.py        # 安全认证
│   │   ├── cache.py           # Redis缓存
│   │   ├── logging.py         # 日志系统
│   │   └── metrics.py         # 监控指标
│   ├── models/
│   │   └── database.py        # 数据库模型
│   └── services/
│       ├── qwen_service.py    # AI对话服务
│       ├── iflytek_service.py # 语音服务
│       └── health_evaluator.py # 健康评估
├── tests/                      # 测试套件
│   ├── conftest.py            # 测试配置
│   ├── unit/                  # 单元测试
│   ├── integration/           # 集成测试
│   ├── api/                   # API测试
│   └── performance/           # 性能测试
├── templates/                  # 模板文件
├── static/                     # 静态资源
├── .github/workflows/          # CI/CD配置
├── main.py                     # 应用入口
├── Dockerfile                  # Docker配置
├── docker-compose.yml          # 编排配置
├── nginx.conf                  # Nginx配置
├── pytest.ini                  # 测试配置
└── requirements.txt            # 依赖清单
```

## 快速开始

### 方式一：本地开发

```bash
# 1. 克隆项目
git clone https://github.com/your-org/anxinbao-server.git
cd anxinbao-server

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入API密钥

# 5. 启动服务
python main.py
```

### 方式二：Docker部署

```bash
# 开发环境
docker-compose up -d

# 生产环境（含PostgreSQL + Redis + Nginx）
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 访问服务

- Web演示界面: http://localhost:8000
- API文档: http://localhost:8000/docs
- Prometheus指标: http://localhost:8000/metrics
- 健康检查: http://localhost:8000/health

## 环境配置

### 必需配置

```env
# AI服务
DASHSCOPE_API_KEY=sk-xxxxx           # 通义千问API密钥

# 科大讯飞
XFYUN_APPID=你的APPID
XFYUN_API_KEY=你的APIKey
XFYUN_API_SECRET=你的APISecret
```

### 可选配置

```env
# 数据库（默认SQLite，生产推荐PostgreSQL）
DATABASE_URL=postgresql://user:password@localhost:5432/anxinbao

# Redis缓存
REDIS_URL=redis://localhost:6379/0

# JWT认证
JWT_SECRET_KEY=your-super-secret-key-at-least-32-chars
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 安全配置
ALLOWED_ORIGINS=http://localhost:3000,https://app.anxinbao.com
API_RATE_LIMIT=100/minute
ENCRYPTION_KEY=your-32-char-encryption-key-here

# 健康风险阈值
HEALTH_RISK_THRESHOLD=7
```

## API接口

### 认证接口

#### 用户登录
```http
POST /api/auth/login
Content-Type: application/json

{
    "username": "13800138000",
    "password": "your_password"
}
```

响应：
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

#### 设备登录
```http
POST /api/auth/device/login
Content-Type: application/json

{
    "device_id": "speaker-001",
    "device_secret": "device_secret_key"
}
```

### 对话接口

#### 发送消息
```http
POST /api/chat/message
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "message": "我今天头有点晕",
    "session_id": "optional-session-id"
}
```

响应：
```json
{
    "reply": "别担心，头晕很常见，可能是休息不好。您最近睡眠怎么样？",
    "session_id": "sess-abc123",
    "risk_info": {
        "risk_score": 3,
        "need_notify": false,
        "category": "health",
        "emotion": {
            "type": "neutral",
            "intensity": 2,
            "keywords": ["头晕"]
        }
    },
    "food_therapy": {
        "name": "枸杞菊花茶",
        "ingredients": ["枸杞10颗", "菊花5朵"],
        "steps": "开水冲泡，焖5分钟",
        "effect": "清肝明目，缓解头晕"
    },
    "timestamp": "2025-12-24T10:30:00Z"
}
```

## 风险评估规则

| 分数 | 级别 | 说明 | 操作 |
|------|------|------|------|
| 1-3 | 低风险 | 日常闲聊或轻微不适 | 正常回复 |
| 4-6 | 中风险 | 需要关注 | 提供食疗建议 |
| 7-8 | 高风险 | 建议就医 | 通知家属 |
| 9-10 | 紧急 | 疑似紧急情况 | 紧急通知家属 |

### 紧急关键词（自动高风险）
- 胸痛、胸闷、心口痛
- 喘不上气、呼吸困难
- 意识模糊、说不清话
- 剧烈头痛、头晕到站不稳
- 摔倒、跌倒受伤

## 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit -v

# 运行API测试
pytest tests/api -v

# 运行并生成覆盖率报告
pytest --cov=app --cov-report=html

# 性能测试
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## 监控

### Prometheus指标

访问 `/metrics` 获取以下指标：

- `anxinbao_http_requests_total` - HTTP请求总数
- `anxinbao_http_request_duration_seconds` - 请求延迟
- `anxinbao_ai_requests_total` - AI服务请求数
- `anxinbao_chat_messages_total` - 对话消息数
- `anxinbao_chat_risk_score` - 风险评分分布
- `anxinbao_high_risk_alerts_total` - 高风险告警数
- `anxinbao_emotion_detected_total` - 情绪检测分布

### 健康检查

```bash
# 存活探针（Kubernetes liveness）
curl http://localhost:8000/health/live

# 就绪探针（Kubernetes readiness）
curl http://localhost:8000/health/ready

# 详细健康状态
curl http://localhost:8000/health/detailed
```

## 部署架构

```
                    ┌─────────────┐
                    │   Nginx     │
                    │  (SSL/LB)   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌────▼─────┐ ┌────▼─────┐
        │  API-1    │ │  API-2   │ │  API-N   │
        │ (FastAPI) │ │(FastAPI) │ │(FastAPI) │
        └─────┬─────┘ └────┬─────┘ └────┬─────┘
              │            │            │
              └────────────┼────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
  ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
  │PostgreSQL │      │   Redis   │      │Prometheus │
  │(Database) │      │  (Cache)  │      │(Metrics)  │
  └───────────┘      └───────────┘      └───────────┘
```

## 技术栈

| 类别 | 技术 |
|------|------|
| Web框架 | FastAPI 0.115+ |
| 数据库 | SQLite/PostgreSQL |
| 缓存 | Redis |
| AI服务 | 阿里云通义千问 |
| 语音服务 | 科大讯飞 |
| 认证 | JWT (python-jose) |
| 容器化 | Docker + docker-compose |
| CI/CD | GitHub Actions |
| 监控 | Prometheus + Grafana |

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
