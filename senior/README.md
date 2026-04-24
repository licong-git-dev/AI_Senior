# `senior/` · 早期 MVP（已归档）

> ⚠️ **本目录为历史 MVP，不是当前主线产品**。当前主线请看仓库根的 [`anxinbao-server/`](../anxinbao-server/) 与 [`anxinbao-pwa/`](../anxinbao-pwa/)。

## 这是什么

2026 年早期基于 Supabase 的初代探索，含 11 个独立子系统：

| 子目录 | 说明 |
|---|---|
| `elderly-care-pwa/` | 第一代 PWA，部署在 https://age6pmb0f3z5.space.minimaxi.com |
| `ai-health-analyzer/` | AI 健康分析器，部署在 https://sznot2b3blsb.space.minimaxi.com |
| `health-analytics-dashboard/` | 数据分析仪表盘，部署在 https://f7p1fplqdgdw.space.minimaxi.com（⚠️ 已知 JS 错误，未修复）|
| `elderly-care-system/` | 老人护理系统 |
| `enhanced-features-platform/` | 增强功能平台 |
| `hardware-management-system/` | 硬件管理系统 |
| `platform-management/` `platform-management-v2/` | 平台管理 V1 / V2 |
| `user-feedback-system/` | 用户反馈系统 |
| `supabase/` | Supabase 配置 |
| `docs/` | 历史文档 |

技术栈：React + TypeScript + Vite + Tailwind + Supabase（数据库 / Edge Functions / Storage）。

## 为什么保留

1. **历史参考**：里面有一些 UI 设计、Supabase Edge Function 写法、产品功能拆分思路，可借鉴
2. **部署在外部 minimaxi 域名**：还有少量真实用户在用，下线需评估通知策略
3. **数据库 schema**：部分表设计与当前 anxinbao-server 不同，可作为对照

## 为什么不再开发

- 主线已迁到 FastAPI + 自管 SQLAlchemy（不再依赖 Supabase）
- 多子系统拆分难维护，主线收敛为单后端 + 单 PWA + 三访问模式
- Supabase 国内访问稳定性差，且按 Row 计费模型不适合规模化

## 如果你刚加入项目

**不要在这里改代码**。改 [`anxinbao-server/`](../anxinbao-server/) 与 [`anxinbao-pwa/`](../anxinbao-pwa/) 才能影响真用户。

## 何时彻底删除？

- 触发条件：minimaxi.com 上的部署都迁回主线，且历史 schema 已被吸收进 [`anxinbao-server/app/models/database.py`](../anxinbao-server/app/models/database.py)
- 当前估计：2026 Q3 之后；在此之前作为只读历史保留

## 历史评估文档

- [`系统概览.md`](系统概览.md) — 11 个子系统的清单与状态
- [`数据库API文档.md`](数据库API文档.md) — Supabase schema + Edge Functions
- [`部署指南.md`](部署指南.md) — Minimaxi 部署步骤
- [`PROJECT_DELIVERY.md`](PROJECT_DELIVERY.md) — 交付报告
- [`USER_ACCEPTANCE_TEST.md`](USER_ACCEPTANCE_TEST.md) — 验收测试报告

---

> 主线产品就绪度参见 [`../FEATURE_STATUS.md`](../FEATURE_STATUS.md)。
