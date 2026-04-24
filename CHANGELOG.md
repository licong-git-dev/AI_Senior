# Changelog

> 本仓库的版本演进记录。最新条目在最上面。
>
> 版本号语义：自治轮次 (rN) → commit short hash → 主题。
>
> 准则：每条 entry 标明"修了/加了什么"和"用户/运营/开发的可感知变化"。

---

## r8 — `<pending>` · 5 项纵深安全审计

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
