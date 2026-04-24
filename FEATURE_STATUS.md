# 安心宝功能就绪度三色灯（FEATURE_STATUS）

> 最后更新：2026-04-23（v2，含安全门 + 守卫修复轮）· 基于静态代码审计 + 关键链路代码核实

## v2 增量（本轮 commit 内升降级）

| 模块 | v1 | v2 | 变化原因 |
|---|---|---|---|
| API `users` | 🔴 内存存储 | 🟢 已显式废弃 + 生产返回 410 | [users.py](anxinbao-server/app/api/users.py) 全部端点 `deprecated=True`，DEBUG=False 强制 410 Gone，无消费者可证（参见迁移指引）|
| API `admin` | 🔴 假数据 | 🟡 生产隐藏 + 0 数据 | [main.py](anxinbao-server/main.py) 中 `_include_router_safely` + [admin_service.py](anxinbao-server/app/services/admin_service.py) 中 `_SafeRandom` 守卫 |
| API `analytics` | 🔴 假数据 | 🟡 生产隐藏 + 0 数据 | 同上 |
| API `ai` | 🔴 重复职责 | 🟡 生产隐藏 | 与 chat 域重叠，从 Swagger 隐藏避免误用 |
| Service `admin_service` | 🔴 23 random | 🟡 DEBUG 门控 | 生产环境一律返回 0/0.0/首项 |
| Service `analytics_service` | 🔴 96 random | 🟡 DEBUG 门控 | 同上 |
| 视频通话 | 🔴 无 TURN | 🟡 ICE env 化 + 失败提示 + 部署文档 | 见 [VIDEO_CALL_SETUP.md](anxinbao-server/docs/VIDEO_CALL_SETUP.md) |
| 启动安全门 | ❌ 无 | ✅ 强校验 | [main.py](anxinbao-server/main.py) `_enforce_production_secrets`：JWT/ENCRYPTION 缺失则拒绝启动 |
| CI 守卫 | ❌ 无 | 📋 模板就绪待启用 | [anxinbao-server/docs/ci/integration-self-check.yml](anxinbao-server/docs/ci/integration-self-check.yml) 同时验证"缺凭据应被拦"和"齐凭据应通过"。需要 PAT `workflow` scope 才能 push 到 `.github/workflows/`，启用步骤见 [docs/ci/README.md](anxinbao-server/docs/ci/README.md) |

## v3 增量（第四 + 第五轮）

| 模块 | v2 | v3 | 变化原因 |
|---|---|---|---|
| API `life` (天气) | 🔴 random | 🟡 生产 501 | [life_service.py](anxinbao-server/app/services/life_service.py) 抛 `LifeServiceNotImplemented`，[life.py](anxinbao-server/app/api/life.py) `_life_route` 装饰器翻译为 HTTP 501 + fallback 建议 |
| API `admin` 鉴权 | ⚠️ 任意登录用户可访问 | ✅ 强校验 admin 角色 | [admin.py](anxinbao-server/app/api/admin.py) 修历史"演示目的"提权漏洞 |
| Service `integration_service` | 🔴 4 random（伪医疗记录/设备读数） | 🟡 生产 NotImplemented | [integration_service.py](anxinbao-server/app/services/integration_service.py) `_enforce_real_integration` 守卫 |
| Service `ai_service` | 🔴 假信心值 | 🟡 _SafeRandom 门控 | [ai_service.py](anxinbao-server/app/services/ai_service.py) 推荐评分/语音情感置信度生产清零，真业务逻辑（按 pitch/energy 阈值判定情绪）保留 |
| Service `voice_feedback_service` | 🔴 7 random | 🟢 重新分类 | 经核实 random 都是 `template_pool` 的合法抽取（与 dialect_companion 同模式），并非伪造业务数据；澄清归类 |
| 子女端视频通话入口 | ✅ | ✅ + 进入前预提醒 | [ChildDashboard.tsx](anxinbao-pwa/src/pages/ChildDashboard.tsx) 顶部视频按钮在 `VITE_TURN_URL` 缺失时弹 confirm，避免老人家属盲目尝试 |
| 文档 / 开发体验 | — | ✅ | 新增 [Makefile](Makefile)（`make verify` 一行自检）、[MIGRATION_users_api.md](anxinbao-server/docs/MIGRATION_users_api.md)（5 端点 1:1 迁移代码）、[PAYMENT_ALIPAY_SETUP.md](anxinbao-server/docs/PAYMENT_ALIPAY_SETUP.md)（90 分钟跑通沙箱） |

## v4 增量（第八轮 · 纵深安全审计）

| 模块 | v3 | v4 | 变化 |
|---|---|---|---|
| auth `/device/login` | 🟡 无限流 | 🟢 5/min（防暴力破解）| [auth.py](anxinbao-server/app/api/auth.py) |
| auth `/device/bind` | 🟡 无限流 | 🟢 10/min（防设备 ID 枚举）| 同上 |
| audit_service 脱敏 | 🟡 仅顶层 4 字段 | 🟢 递归 + PII + 健康敏感 + details/old/new | [audit_service.py](anxinbao-server/app/services/audit_service.py) |
| scheduler 失败容错 | 🟡 默认 log | 🟢 监听器 + metrics + job_defaults | [scheduler.py](anxinbao-server/app/core/scheduler.py) |
| 依赖 SCA | ❌ 无 | ✅ 脚本 + Makefile + CI 模板 | [security_audit.sh](anxinbao-server/scripts/security_audit.sh) |
| PWA service worker | 🟡 v1 / 静态 cache 全收 | 🟢 v2 / 显式版本 / NO_CACHE 列表 / LRU | [sw.js](anxinbao-pwa/public/sw.js) |

**v3 后剩余红色就绪度模块：0 个**（v1 起 10 → v2 4 → v3 0）。
所有曾标红的模块要么真正修好（user.py / admin 鉴权），要么生产环境抛 501（life / integration），要么 _SafeRandom 门控（admin / analytics / ai service）。**整体上线前 P0 = 配齐凭据 + 启用 CI 守卫**，剩下都是 P1 业务深度问题。

## 一、为什么需要这份文档

历史问题：
- [`Execute_Plan/00_总纲.md:11`](Execute_Plan/00_总纲.md#L11) 写"316 测试通过、所有模块 ✅ 完成"
- [`prd/功能完成度评估.md:80`](prd/功能完成度评估.md#L80) 同时写"综合完成度 55%"
- 实际抽样：`payment_service` 用 `'test_private_key'`、`admin_service` 30+ 仪表盘指标返回 `random.randint()`、`sms_service` 缺凭据时静默走入 `MockSMSClient`

→ **团队对自己产品的状态都没有共识，对外宣传无法引用任何"已完成"的话术**

## 二、判定标准（严格）

| 颜色 | 标准 | 可对外宣传？ |
|---|---|---|
| 🟢 **绿（real）** | 真实业务逻辑 + 真实集成 + 数据库写入；无 mock/random/占位；端点能被前端实际调用并返回真实数据；关键凭据全部真实配置 | ✅ 可宣传"已上线"  |
| 🟡 **黄（partial）** | 核心 CRUD 通了，但缺集成 / 含少量 TODO / 仅本地可用 / 等待外部凭据 | ⚠️ 只能内部演示，需在文档明确"待补集成" |
| 🔴 **红（stub）** | 只有路由壳子 / 业务数据是 random/hardcoded / 标榜业务功能但无真实数据库写入 | ❌ 上线前必须改造或彻底下线（避免攻击面+口碑风险）|

**铁律**：任何对外材料（投资人 / PRD / 落地页）只能引用 🟢 绿色项。🟡 必须明确标注"测试中"。🔴 必须从导航/Swagger 隐藏。

## 三、整体快照

| 维度 | 🟢 绿 | 🟡 黄 | 🔴 红 | 总数 | 就绪率 |
|---|---|---|---|---|---|
| API 路由 | 10 | 33 | 4 | 47 | **21%** |
| Service | 4 | 33 | 6 | 43 | **9%** |
| **合计** | **14** | **66** | **10** | **90** | **16%** |

> "就绪率 16%" 才是当前对外可信的真实状态，与 [`prd/功能完成度评估.md`](prd/功能完成度评估.md) 自报的 55%、[`Execute_Plan/00_总纲.md`](Execute_Plan/00_总纲.md) 自报的 100% 都不同。**这才是建立信任的起点**。

---

## 四、API 路由（47 个）

### 🟢 绿色 · 真实可用（10）

| 模块 | 行数 | 真实信号 |
|---|---|---|
| [auth](anxinbao-server/app/api/auth.py) | 746 | DB 写 19 / 读 14；JWT/refresh 全链路 |
| [emergency](anxinbao-server/app/api/emergency.py) | 931 | DB 写 19 / 读 25；SOS 链路在本轮已修复参数名 bug |
| [family](anxinbao-server/app/api/family.py) | 894 | DB 写 6 / 读 23；3 处真实 HTTP |
| [health](anxinbao-server/app/api/health.py) | 849 | DB 写 8 / 读 15；阈值告警实装 |
| [medication](anxinbao-server/app/api/medication.py) | 755 | DB 写 9 / 读 20；提醒持久化 |
| [memory_api](anxinbao-server/app/api/memory_api.py) | 876 | DB 写 20 / 读 26；相册/故事/时光胶囊 |
| [proactive](anxinbao-server/app/api/proactive.py) | 854 | DB 写 16 / 读 30；主动问候 |
| [drug_api](anxinbao-server/app/api/drug_api.py) | 645 | DB 写 11 / 读 22；药物库查询 |
| [cognitive_api](anxinbao-server/app/api/cognitive_api.py) | 1474 | DB 写 14 / 读 35；认知训练数据持久化 |
| [notify](anxinbao-server/app/api/notify.py) | 275 | DB 写 5 / 读 6 |

### 🔴 红色 · 必须改造或下线（4）

| 模块 | 行数 | 问题 | 上线前必做 |
|---|---|---|---|
| [admin](anxinbao-server/app/api/admin.py) | 529 | 后台返回 `admin_service` 的随机仪表盘数据 | **从 Swagger 隐藏 + 加管理员鉴权 + 接真实统计** |
| [analytics](anxinbao-server/app/api/analytics.py) | 343 | 12 处 `random` 数据占位 | 实现真实数据聚合（接 Prometheus / DB SQL） |
| [users](anxinbao-server/app/api/users.py) | 195 | **内存 dict 存储老人/家属档案**，重启数据全丢 | 立刻改 SQLAlchemy 持久化 |
| [ai](anxinbao-server/app/api/ai.py) | 447 | `random` 占位 + 与 `chat`/`qwen` 重复 | 砍掉或合并到 chat 域 |

### 🟡 黄色 · 部分就绪（33）

| 模块 | 行数 | 阻塞项（按重要性） |
|---|---|---|
| accessibility | 298 | 待屏幕阅读器兼容性验证 |
| audit | 404 | 审计日志框架就绪，待 DB 索引 |
| chat | 184 | 多轮会话持久化未完成 |
| community | 653 | 缺内容审核集成 |
| daily_report | 467 | 日报核心已通；本轮已做 key_quotes 脱敏 |
| dialect | 291 | ASR 引擎集成验证中（鄂州话已改为回退武汉话）|
| entertainment | 404 | 内容库不足 |
| exercise | 591 | 缺可穿戴设备数据接入 |
| file | 447 | 缺对象存储（OSS/S3）集成 |
| games | 365 | 题库未填充 |
| i18n | 356 | 多地区测试未做 |
| integration | 542 | 等待具体第三方接入 |
| iot | 462 | 缺真实设备测试 |
| life | 315 | 业务规则未定义 |
| marketing | 431 | 等活动配置 |
| memory | 795 | 框架完整，缺照片处理/分享 |
| mental_health | 539 | 1 处 random 待移除 |
| messages | 523 | 实时同步与离线处理 |
| nutrition | 435 | 食物库未建 |
| onboarding | 415 | 缺个性化流程 |
| payment | 406 | **待支付宝/微信真实凭据** |
| preferences | 558 | 缺推荐引擎 |
| report | 480 | 数据聚合待完成 |
| safety | 602 | 跌倒检测算法已就绪，缺设备 |
| simple | 383 | UI 适配测试 |
| smart_home | 537 | 缺设备协议适配 |
| social | 644 | 实时通知未接 |
| subscription | 478 | 会员权限验证 |
| support | 534 | 工单系统未接 |
| video | 235 | **缺 TURN 服务器**，70% NAT 场景打不通 |
| voice | 178 | 方言支持验证中 |
| voice_feedback | 476 | 情感识别模型未集成 |
| ws | 400 | 缺 MQ 与心跳管理 |

---

## 五、Service 服务（43 个）

### 🟢 绿色 · 真实可用（4）

| 服务 | 行数 | 真实信号 |
|---|---|---|
| [community_service](anxinbao-server/app/services/community_service.py) | 870 | 5 处真实 HTTP 调用 |
| [family_service](anxinbao-server/app/services/family_service.py) | 748 | 4 处真实 HTTP，与通知系统打通 |
| [report_service](anxinbao-server/app/services/report_service.py) | 786 | 6 处真实 HTTP，导出链路完整 |
| [dialect_companion](anxinbao-server/app/services/dialect_companion.py) | 901 | 武汉话 500+ 模板，鄂州话已改为回退武汉话 |

### 🔴 红色 · 必须改造或下线（6）

| 服务 | 行数 | 问题 | 上线前必做 |
|---|---|---|---|
| [admin_service](anxinbao-server/app/services/admin_service.py) | 688 | **41 处 TODO + 23 处 random**，仪表盘"50000-60000 用户、500-800 万收入"全是假数据 | 从导航隐藏 + 接真实 SQL 聚合 |
| [analytics_service](anxinbao-server/app/services/analytics_service.py) | 513 | **96 处 random**，几乎全部业务指标都是占位 | 重写或下线 |
| [voice_feedback_service](anxinbao-server/app/services/voice_feedback_service.py) | 573 | 7 处 random，号称"情感识别"但无真模型 | 接入真情感识别或砍掉宣称 |
| [life_service](anxinbao-server/app/services/life_service.py) | 672 | 11 处 random，"个性化推荐"是随机 | 实现规则推荐或砍 |
| [integration_service](anxinbao-server/app/services/integration_service.py) | 799 | 4 处 random + 大量未接 | 接具体服务或拆分 |
| [ai_service](anxinbao-server/app/services/ai_service.py) | 812 | 4 处 random，与 qwen_service 职责重叠 | 合并到 qwen_service |

### 🟡 黄色 · 部分就绪（33）

| 服务 | 行数 | 阻塞项 |
|---|---|---|
| audit_service | 829 | DB 索引与查询优化 |
| cognitive_game_service | 656 | 21 处 random（部分是题目随机抽取，合理）；题库待扩 |
| daily_report | 683 | DB 读 9；本轮已做 key_quotes 脱敏 |
| dialect_service | 469 | 缺语音引擎 |
| email_service | 654 | 缺 SMTP/模板配置 |
| emergency_service | 779 | 本轮修复 SOS 短信参数名 bug |
| entertainment_service | 548 | 内容库不足 |
| exercise_service | 808 | 缺设备同步 |
| file_service | 632 | 缺对象存储 |
| health_evaluator | 201 | 评估算法待补 |
| iot_service | 703 | 缺 MQTT/协议 |
| localization_service | 689 | 多语言测试 |
| marketing_service | 675 | 1 处占位 |
| medication_service | 732 | 提醒引擎 |
| memory_service | 914 | 照片处理 |
| mental_health_service | 913 | 评估模型 |
| message_center_service | 677 | 1 处占位 + MQ |
| notification_service | 537 | DB 写 2/读 1，2 处 HTTP，覆盖待补 |
| notification_store | 667 | 持久化与查询 |
| nutrition_service | 662 | 食物库 |
| onboarding_service | 485 | 流程定制 |
| payment_service | 563 | **凭据是 `'test_private_key'` 占位** |
| personalization_service | 531 | 推荐算法 |
| qwen_service | 546 | prompt 工程深度待提升 |
| safety_service | 812 | 跌倒算法已就绪，缺设备 |
| simplified_mode | 508 | UI 测试 |
| smart_home_service | 851 | 设备协议 |
| sms_service | 491 | 1 处真实 HTTP；缺凭据时已加显式 mock 警告 |
| social_service | 616 | 1 处 random |
| subscription_service | 625 | 会员权限 |
| support_service | 859 | 2 处 random |
| websocket_service | 693 | 集群支持 |
| xfyun_service | 359 | 鄂州话 ASR 实际是武汉话近似（[xfyun_service.py:140](anxinbao-server/app/services/xfyun_service.py#L140)）|

---

## 六、关键集成真实性

> 直接复用 `GET /health/integrations`（本轮新增）的判定结构。运行 `python anxinbao-server/scripts/check_integrations.py` 即可离线核查。

| 集成 | 当前状态 | 关键文件 |
|---|---|---|
| 通义千问（qwen） | 🟡 待真凭据 | [qwen_service.py](anxinbao-server/app/services/qwen_service.py) |
| 讯飞 ASR/TTS | 🟡 待真凭据；鄂州话为武汉话近似 | [xfyun_service.py](anxinbao-server/app/services/xfyun_service.py) |
| 阿里云短信 | 🔴 SOS 模板未配置则发不出去 | [sms_service.py](anxinbao-server/app/services/sms_service.py) |
| 极光推送 | 🟡 待真凭据 | [notification_service.py](anxinbao-server/app/services/notification_service.py) |
| 支付宝 | 🔴 凭据是 `'test_private_key'` | [payment_service.py:222-225](anxinbao-server/app/services/payment_service.py#L222-L225) |
| 数据加密密钥 | 🔴 默认空，生产必须设置 | [config.py:40](anxinbao-server/app/core/config.py#L40) |
| JWT 密钥 | 🔴 默认走 `secrets.token_urlsafe(32)` 自动生成，重启就变，所有人被踢 | [config.py:30](anxinbao-server/app/core/config.py#L30) |
| TURN（视频通话） | 🔴 仅配置 Google STUN，国内 NAT 70% 场景打不通 | [VideoCallPage.tsx:111](anxinbao-pwa/src/pages/VideoCallPage.tsx#L111) |

---

## 七、上线前必清的 P0 清单

### 🔥 不解决就出事故的
1. **配置 `JWT_SECRET_KEY` 环境变量**（否则每次重启所有用户被踢）
2. **配置 `ENCRYPTION_KEY`**（否则敏感数据无加密）
3. **配置阿里云短信模板 `SMS_TEMPLATE_EMERGENCY`**（否则 SOS 发不出去）
4. **配置支付宝真实凭据**（否则订阅付费完全是假）
5. **`users.py` 内存存储改 DB**（否则重启数据全丢）
6. **隐藏 admin/analytics 路由 + 隐藏其 Swagger**（否则攻击者能看到内部数据结构）
7. **TURN 服务器部署**（或砍掉视频通话功能宣传）

### ⚠️ 不解决会损口碑的
8. **`admin_service` / `analytics_service` 中的 random 数据全部替换**（任何投资人/合伙人翻看都崩盘）
9. **方言库已扩到武汉话 500+，但鄂州话仍是武汉话回退**——产品话术应明确"目前只承诺武汉话深度"
10. **`payment` 端点需要前置鉴权**，否则任意请求即可触发"创建订单"

---

## 八、维护方式

### 谁来更新
- 每次 PR 合并后，开发者自己评估对应模块颜色变化，更新本文档
- 每周一晨会，TL 扫一遍 🔴 红色项，分配责任人
- 每次发版前，必须 `python anxinbao-server/scripts/check_integrations.py --strict` 通过

### 怎么从黄变绿
- 移除全部 TODO/Mock/`random.randint`（业务数据场景）
- 至少 1 个端到端测试覆盖
- 关键凭据真实配置且 `/health/integrations` 返回 `production_ready=true`

### 怎么从红变黄
- 拿掉 random/hardcoded
- 关键路径有 DB 写入或真实 HTTP 调用
- 接入对应集成的真凭据（哪怕仅在测试环境）

---

## 九、对外可宣传的边界（话术对照）

| 不能说的 | 可以说的 |
|---|---|
| ~~"全功能 AI 养老平台"~~ | "聚焦武汉话陪伴 + 健康守护 + 紧急救助的 MVP" |
| ~~"已支持武汉话/鄂州话/普通话三种方言"~~ | "已支持武汉话深度陪伴（500+ 真实场景模板），鄂州话/其他方言基于武汉话近似" |
| ~~"完整的运营管理后台"~~ | "正在搭建运营后台" |
| ~~"已接通微信/支付宝订阅"~~ | "订阅功能正在与支付宝接入" |
| ~~"24 小时紧急救助通知"~~ | "SOS 紧急通知（需配置阿里云短信模板和家属手机号）" |
| ~~"AI 情感记忆"~~ | "对话过程中会记录用户偏好（基础版）" |

---

> 本文档与代码同源，是产品对外宣传的**事实根据**。任何与本文档不符的话术必须先更新本文档再发布。
