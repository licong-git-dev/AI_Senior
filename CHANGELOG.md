# Changelog

> 本仓库的版本演进记录。最新条目在最上面。
>
> 版本号语义：自治轮次 (rN) → commit short hash → 主题。
>
> 准则：每条 entry 标明"修了/加了什么"和"用户/运营/开发的可感知变化"。

---

## r11 — `<pending>` · 数字生命陪伴 Phase 1 alpha · 完整 4 阶段 RFC 与骨架

🚀 **战略转向**：从"工具型应用" → "AI 数字生命陪伴"。本轮交付完整 4 阶段架构 RFC + Phase 1 骨架 + 风险与成本评估。所有新代码 alpha 状态，由 `COMPANION_ENABLED=true` 显式开启，**不破坏现有 `/api/chat`**。

### 文档（3 份）
- [`docs/DIGITAL_COMPANION_RFC.md`](anxinbao-server/docs/DIGITAL_COMPANION_RFC.md) — 4 阶段架构主文档（行业锚定 / 差距分析 / 路线图 / 安全护栏 / 评审流程）
- [`docs/DIGITAL_COMPANION_COST.md`](anxinbao-server/docs/DIGITAL_COMPANION_COST.md) — 成本模型（Phase 1+2 ¥19/月、Phase 4 完整体 ¥45-81/月、三档套餐建议）
- [`docs/DIGITAL_COMPANION_RISKS.md`](anxinbao-server/docs/DIGITAL_COMPANION_RISKS.md) — 4 项 P0 + 6 项 P1 + 合规清单 + kill switch

### 服务层骨架（11 个新文件）
- [`app/services/persona.py`](anxinbao-server/app/services/persona.py) — `AnxinbaoPersona` 不可变人格（性格五项 / 口头禅 / 禁忌 / 必做 / 必不说）+ `build_system_prompt()`
- [`app/services/memory_engine.py`](anxinbao-server/app/services/memory_engine.py) — SQLite 长期记忆引擎，5 类记忆（fact/preference/relation/event/mood）+ 关键词召回 + 时间衰减打分；MemoryVisibility 三级（self_only/family/never_share）防止隐私泄漏
- [`app/services/companion_tools.py`](anxinbao-server/app/services/companion_tools.py) — function calling 工具池（9 个工具，4 级安全）；与 Anthropic Tool Use 格式兼容
- [`app/services/agents/`](anxinbao-server/app/services/agents/) 包：
  - `base.py` — `BaseAgent` + `AgentReport` 统一汇报结构 + 异常兜底
  - `hermes.py` — 协调者 / 唯一对外人格；当前降级到 qwen_service
  - `health_agent.py` — 健康监控（规则引擎，无 LLM）
  - `social_agent.py` — 家庭关系图谱
  - `memory_agent.py` — 长期记忆管理 + 心境聚合
  - `safety_agent.py` — SOS / 跌倒 / 长时间静默
  - `schedule_agent.py` — 用药 / 服务 / 出行规划

### API 层
- [`app/api/companion.py`](anxinbao-server/app/api/companion.py) — `/api/companion/*`：
  - `GET /persona` 查看人格配置
  - `POST /chat` 与数字生命对话（骨架版，降级到 qwen_service）
  - `GET /memory/stats` 记忆统计
  - `GET /memory/list` 列出记忆
  - `POST /memory/save` 写入记忆
  - `DELETE /memory/{id}` 老人主动忘记
  - `DELETE /memory/all/clear?confirm=true` GDPR 一键清空
  - `GET /tools` 列出可用工具池
- [`main.py`](anxinbao-server/main.py) 注册 router；新增 `_ALPHA_ROUTERS_HIDE_IN_PROD={"companion"}` 在生产 OpenAPI 隐藏（即便启用也不让普通用户发现）

### 安全设计（贯穿）
- 默认关闭：`COMPANION_ENABLED=false`；启用还需运维显式设置
- 老人对 AI 倾诉默认 `SELF_ONLY`，永不暴露给家属
- 老人随时可一键删除全部记忆
- LLM 不直答健康/用药建议（必经规则引擎）
- 与现有 `/api/chat` 完全并行，零破坏

## r10 — [`ddda28d`](https://github.com/licong-git-dev/AI_Senior/commit/ddda28d) · DLQ UI + 4 个集成守卫 + health 拓展 + 审计权限收敛 + manifest

- **🛡️ RR DLQ 端点**：[`/api/admin/dlq`](anxinbao-server/app/api/admin.py) GET 列表（按 channel/severity 过滤、limit 1-500）+ POST `/dlq/clear` 清空（须 confirm=true）；两端点都受 admin 强鉴权 + 审计日志记录
- **🛡️ SS integration_service 4 个新守卫**：除已有的 `sync_medical_records` / `sync_device_data`，再加：
  - `book_appointment`（伪挂号会让老人到现场没号，是医疗事故源）
  - `pair_device`（不做 BLE 握手就标 ONLINE，血压数据永不到）
  - `create_order`（社区服务订单只本地存储，社区方不知道）
  - `submit_claim`（保险理赔仅本地状态变更，保险公司无记录）
- **🛡️ TT `/health/integrations` 拓展**：新增 `cors` 检查项（含 issues 列表）+ `dead_letter_queue`（size + critical_count + counts_by_channel + blocking_production）+ `scheduler.metrics`（jobs_errored/missed/max_instances）；DLQ critical ≥10 也计入 `critical_missing`，作为生产门
- **🛡️ UU audit-logs 权限收敛**：[`/api/auth/audit-logs`](anxinbao-server/app/api/auth.py) 旧版任意 admin 可查全量是合规风险。新版按角色作用域：
  - `super_admin` / `admin`（含 `admin_service` 注册）→ 全量 + 可按 user_id 过滤
  - 其他角色 → 只能查自己；显式传他人 user_id → 403
  - 防 token 伪造：admin 角色仍要在 admin_service 中注册才放行
- **📱 VV PWA manifest 优化**：
  - `start_url=/?source=pwa` 标记 PWA 流量
  - `scope=/` 显式作用域；`display_override` 桌面 PWA 兼容
  - `orientation=portrait-primary` 锁定竖屏（老人翻屏易误操作）
  - `background_color=#1e1b4b` 与 StandbyScreen 深色调对齐，启动不白闪
  - icons 拆 `any` + `maskable` 两组（旧版 `any maskable` 在 iOS 兼容差）
  - `shortcuts` 长按桌面图标：SOS / 聊天 / 用药
  - 配套文档 [`PWA_MANIFEST.md`](anxinbao-pwa/docs/PWA_MANIFEST.md) 含图标资产清单 + 一键生成命令 + index.html 配套 meta tags + 适老化考量

## r9 — [`777d40d`](https://github.com/licong-git-dev/AI_Senior/commit/777d40d) · 通知重试+死信 / CORS 守卫 / 迁移文档 / Bundle 减重

- **🛡️ LL+MM 通知重试 + 死信队列**：
  - 新增 [`app/core/retry.py`](anxinbao-server/app/core/retry.py) 异步重试装饰器（指数退避+抖动+显式 retryable 类）
  - 新增 [`app/core/dead_letter.py`](anxinbao-server/app/core/dead_letter.py) 死信队列（线程安全 + ERROR 日志 + 计数）
  - WeChatPusher 的 `_get_access_token` 与 `push` 加 retry（仅命中 httpx.TransportError/TimeoutException）
  - notification_service.send_notification 中"紧急通知 + 该家属所有通道都失败" → 强制 DLQ critical 记录，运维可追溯
- **🛡️ NN CORS 启动守卫**：[`_enforce_production_secrets`](anxinbao-server/main.py) 加 CORS 校验：
  - `*` 通配符 → 拒绝启动
  - 含 localhost / 127.x / 0.0.0.0 → 拒绝启动
  - 含 http:// （非 https） → 拒绝启动
  - 空 → 拒绝启动
- **📋 OO Alembic 迁移指南**：新增 [`docs/DATABASE_MIGRATION.md`](anxinbao-server/docs/DATABASE_MIGRATION.md)
  - autogenerate 工作流 + autogenerate 漏检的 4 类场景手写指引
  - SQLite ALTER 限制与 batch_alter_table 模式
  - 数据迁移最佳实践（schema 与 drop 分两次 commit）
  - 多人协作 branch heads 合并
  - 与 init_db() 的关系 + 生产推荐改 alembic upgrade head
  - 回滚 SOP
- **📦 PP 前端 Bundle 减重**：
  - **移除 recharts**（package.json 在 src/ 零引用，节省 ~120 KB gzip）
  - 新增 [`anxinbao-pwa/docs/BUNDLE_OPTIMIZATION.md`](anxinbao-pwa/docs/BUNDLE_OPTIMIZATION.md)：
    - 当前 4 个生产依赖体积估算
    - 静态审计命令（grep 整包 import / depcheck）
    - 减重清单按 ROI 排序
    - 适老化场景下的优先级（首屏 < 3s）
    - 中文字体子集化方案

## r8 — [`3ab5c56`](https://github.com/licong-git-dev/AI_Senior/commit/3ab5c56) · 5 项纵深安全审计

- **🛡️ FF auth 限流补齐**：[`/device/login`](anxinbao-server/app/api/auth.py) 加 5/min（防设备 secret 暴力破解）；[`/device/bind`](anxinbao-server/app/api/auth.py) 加 10/min（防恶意枚举有效设备 ID）
- **🛡️ GG audit_service 脱敏加强**：[`_sanitize_params`](anxinbao-server/app/services/audit_service.py) 改为递归处理 dict/list/tuple；黑名单扩展到 PII（手机/身份证/地址/银行卡）+ 健康敏感（病例/诊断/处方）；`details/old_value/new_value` 三字段也强制脱敏（历史漏洞：调用方塞进整个 user dict 会原文落库）；占位改为 `***REDACTED(len=N)***` 保留长度便于排错
- **🛡️ HH scheduler 异常监听器**：注册 `EVENT_JOB_ERROR/MISSED/MAX_INSTANCES` 监听器，单任务异常计入 `metrics` 并打印；`job_defaults` 加 `coalesce=True / misfire_grace_time=300 / max_instances=1`，避免重复推送 / 写入冲突
- **🛡️ II 依赖 SCA**：新增 [`scripts/security_audit.sh`](anxinbao-server/scripts/security_audit.sh)（pip-audit 优先 / safety 备选 / 都没装给安装指引）；Makefile 加 `make audit`；CI 模板加 pip-audit 步骤（`continue-on-error`，仅警告不阻断）
- **🛡️ JJ PWA service worker 重写**：v1 → v2，`CACHE_NAME` 显式版本化；HTML 入口 network-first 避免老人卡旧 UI；新增 `NO_CACHE_PREFIXES`（`/api/`、`/sw.js`、`/health`、`/metrics` 都不缓存）；非 GET 请求一律不缓存；`MAX_CACHE_ITEMS=60` LRU 裁剪保护老人设备空间；离线 API 兜底响应改为 503 + 友好 hint；新增 `SKIP_WAITING` 消息让前端可强制更新

## r7 — [`6fe38bf`](https://github.com/licong-git-dev/AI_Senior/commit/6fe38bf) · devx + ErrorBoundary + 文档与残骸清理

- **🛡️ 前端**：新增 [`ErrorBoundary`](anxinbao-pwa/src/components/ErrorBoundary.tsx) 全局错误边界，杜绝白屏崩溃；适老化"出问题了"页面（大字号 + 重试/回首页按钮）
- **🔧 支付**：[`payment_service.py`](anxinbao-server/app/services/payment_service.py) 去掉 `'test_private_key'` 等硬编码 fallback；新增 `_credentials_ready()` 显式判定 + 生产环境凭据缺失直接拒绝走签名链路
- **📋 文档**：新增 [`CHANGELOG.md`](CHANGELOG.md)（本文）+ [`.pre-commit-config.yaml.template`](.pre-commit-config.yaml.template) + [`senior/README.md`](senior/README.md)（legacy 标记）

## r6 — [`6f5d989`](https://github.com/licong-git-dev/AI_Senior/commit/6f5d989) · 删 dev 残骸 + 修 PEP 701 + 文档基线

- **🐛 bug 修复**：[`life.py:335`](anxinbao-server/app/api/life.py#L335) f-string 嵌套同款引号在 Python <3.12 抛 SyntaxError，已拆分
- **🧹 清理**：删 8 个 `fix_*.py` 一次性引号修复脚本（dev artifact）；移走 monorepo 下不生效的 `anxinbao-server/.github/workflows`
- **📋 文档**：新增 [`CONTRIBUTING.md`](CONTRIBUTING.md)；[`CLAUDE.md`](CLAUDE.md) 加入 6 条新模式（`_SafeRandom`/`*NotImplemented`/`_gone()`/路由 schema 隔离/启动安全门/PEP 701）；同步 [prd 完成度](prd/功能完成度评估.md) 与 FEATURE_STATUS

## r5 — [`4e31355`](https://github.com/licong-git-dev/AI_Senior/commit/4e31355) · 红色清零 + 一行自检 + 文档索引

- **🟢 红色就绪度归零**（v1: 10 → v2: 4 → v3: **0**）
- **🛡️ integration_service**：医疗记录 / 设备读数 mock 生产抛 `IntegrationNotImplemented`
- **🛡️ ai_service**：评分 / 信心值 `_SafeRandom` 门控（保留真业务逻辑：按 pitch/energy 阈值判定情绪）
- **👵 ChildDashboard**：视频按钮在 `VITE_TURN_URL` 缺失时进入前 confirm，与 VideoCallPage 失败提示形成"事前+事后"双道防线
- **🔧 devx**：新增 [`Makefile`](Makefile) 一行 `make verify` / `make verify-prod` / `make doctor`
- **📋 文档**：[`README.md`](README.md) 新增"一键自检"段 + "关键运维与开发文档"6 份索引

## r4 — [`e89cd0e`](https://github.com/licong-git-dev/AI_Senior/commit/e89cd0e) · life→501 + admin 强鉴权 + Alipay 沙箱指南

- **🛡️ life_service**：天气 mock 生产抛 `LifeServiceNotImplemented`，[`_life_route`](anxinbao-server/app/api/life.py) 装饰器翻为 HTTP 501 + fallback 建议（指向 wttr.in / 高德 / 心知）
- **🛡️ admin 提权漏洞修复**：历史 `verify_admin` 自承"演示目的允许任意登录用户"是潜在 0day。改用 `get_current_admin` + 双重校验 `admin_service` 注册
- **📋 文档**：新增 [`MIGRATION_users_api.md`](anxinbao-server/docs/MIGRATION_users_api.md) 5 端点 1:1 迁移代码 + [`PAYMENT_ALIPAY_SETUP.md`](anxinbao-server/docs/PAYMENT_ALIPAY_SETUP.md) 90 分钟跑通沙箱

## r3 — [`4517b9f`](https://github.com/licong-git-dev/AI_Senior/commit/4517b9f) · 5 项 P0 安全门

- **🛡️ users.py 废弃**（红 → 绿）：DEBUG=False 返回 410 Gone + 迁移指引；DEBUG=True 返回 404 + 日志告警
- **🛡️ 启动安全门**：[`_enforce_production_secrets`](anxinbao-server/main.py) 强校验 JWT/ENCRYPTION，缺失即 SystemExit
- **🛡️ admin/analytics 隔离**：生产环境 OpenAPI schema 隐藏 + [`_SafeRandom`](anxinbao-server/app/services/admin_service.py) 模块级守卫，113+ 处 random 占位无需逐行重写
- **📺 视频通话**：ICE env 化 + 失败提示 + [`VIDEO_CALL_SETUP.md`](anxinbao-server/docs/VIDEO_CALL_SETUP.md) 三方案对比
- **🤖 CI 守卫模板**（暂存 [`docs/ci/`](anxinbao-server/docs/ci/)，需 PAT `workflow` scope 启用）

## r2 — [`a3020b0`](https://github.com/licong-git-dev/AI_Senior/commit/a3020b0) · 武汉话 500+ + 行动入口 + 三色灯

- **🗣️ 方言库**：武汉话从 58 句扩到 **500 句**，含语气词（嘞/唦/啵/咯）、特征词（老倌子/搞么斯/恰饭/造业）、武汉地名/小吃；新增防跌倒/护眼/防痴呆/思乡/怀念老伴等 14 个细分类目
- **👵 子女端日报**：[`ChildDashboard`](anxinbao-pwa/src/pages/ChildDashboard.tsx) 关怀 tip 改"看到 → 行动 → 焦虑被释放"模式：`inferTipAction()` 根据关键词匹配下一步动作（视频 / 电话 / 设提醒 / 发祝福 / 查趋势 / 记下）
- **🔧 凭据自检**：新增 [`scripts/check_integrations.py`](anxinbao-server/scripts/check_integrations.py) 离线自检脚本（不启动 FastAPI）
- **📋 文档**：[`FEATURE_STATUS.md`](FEATURE_STATUS.md) v1 三色灯看板（47 API + 43 Service 系统审计）

## r1 — [`00d711f`](https://github.com/licong-git-dev/AI_Senior/commit/00d711f) · 4 个生产/伦理/UX 阻断 bug

- **🐛 SOS 短信生产阻断**：[`emergency_service.py:413-418`](anxinbao-server/app/services/emergency_service.py#L413) 调用 `send_emergency_alert` 时用了错误关键字参数（phone_numbers vs phone_number 等），100% 抛 `TypeError` 但被同段 except 静默吞掉 —— 真实 SOS 短信永远发不出去。修复
- **⚠️ 隐私伦理炸弹**：[`daily_report.py:392`](anxinbao-server/app/services/daily_report.py#L392) 把老人最长的 2 条原话直接展示给家属（含对儿媳/老伴的抱怨）。改为基于已抽取 topics 的脱敏短语 + 敏感词回退过滤
- **🐛 隐藏配置 bug**：[`.env.example`](anxinbao-server/.env.example) 写 `SMS_ACCESS_KEY_ID` 等环境变量，但 [`Settings`](anxinbao-server/app/core/config.py) 中未声明对应字段，pydantic-settings 不加载未声明字段 → 用户填了 `.env` 也无效。补全字段声明 + `AliasChoices` 兼容
- **👵 SOS 误触保护**：[`StandbyScreen.tsx`](anxinbao-pwa/src/pages/StandbyScreen.tsx) 中 SOS 与"邀请家人"按钮相邻且仅 64px。SOS 抽到独立行、放大到 96px、改为长按 1.5 秒触发，配进度环
- **🔍 集成自检端点**：新增 [`/health/integrations`](anxinbao-server/main.py) 暴露每个第三方集成是 real/placeholder/missing/weak

## r0 — [`95e6ea2`](https://github.com/licong-git-dev/AI_Senior/commit/95e6ea2) · 仓库初始化

- **📋 文档**：仓库初始化 + 中文 [`README.md`](README.md) + [`.gitignore`](.gitignore)（排除 `.env`、SQLite 数据库、`uploads/`、构建产物）
- **📦 首次纳入**：anxinbao-server (FastAPI 后端) + anxinbao-pwa (React PWA) + senior (早期 Supabase MVP) + prd/Product_plan/Execute_Plan 产品文档

---

## 累计改动数据

| 维度 | r0 起点 | 当前 | 变化 |
|---|---|---|---|
| 🔴 红色就绪度模块 | 10+ | **0** | -10 |
| 🛡️ 历史提权漏洞 | 1 (admin) | **0** | -1 |
| 🚨 生产阻断 bug | 1 (SOS 短信) | **0** | -1 |
| 🗣️ 武汉话模板 | 58 | **500** | +442 |
| 📋 运维文档 | 0 | **8** 份 | +8 |
| 🐛 隐私伦理炸弹 | 1 (key_quotes) | **0** | -1 |
| 🐛 dev 残骸脚本 | 8 个 | **0** | -8 |
| 🛠️ 一行自检命令 | ❌ | ✅ `make verify` | — |

---

> 维护方式：每个 commit 推到 main 后，在文件顶部加一条 entry。版本号体现"自治轮次"，便于团队/投资人按时间线追溯。
