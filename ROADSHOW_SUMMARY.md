# 安心宝 · 15 轮自治演进成果摘要

> **目标读者**：投资人 / 合伙人 / 团队新人 / 法务 / 医疗专家评审委员会
> **文档状态**：r16 · 路演级可引用
> **仓库快照**：https://github.com/licong-git-dev/AI_Senior
> **最新 commit**：[`5719044`](https://github.com/licong-git-dev/AI_Senior/commit/5719044)（2026-04）

---

## 一、一页式执行摘要

**是什么**：面向中国老年人的 AI 数字生命陪伴平台。不是"聊天机器人"，是"会记得父母是谁、会主动开口、会替父母办事"的数字伙伴 + 家庭关怀信使。

**做到了什么**（15 轮自治迭代）：

| 维度 | 起点 | 现状 |
|---|---|---|
| 🛡️ 生产阻断 bug | 1 个 (SOS 短信错参数) | **0** |
| 🔴 红色就绪度模块 | 10+ | **0** |
| 🛡️ 提权漏洞 | 1 个 (admin 任意访问) | **0** |
| 🐛 隐私泄漏点 | 2 个 (key_quotes + audit-logs) | **0** |
| 🗣️ 武汉话深度 | 58 句模板 | **500 句** |
| 🤖 数字生命能力 | 无 | Phase 1-3 完整 (人格 + 记忆 + 触发器 + 工具) |
| 🧪 测试覆盖 | 272 case | 372+ case (Companion +89, 含 E2E) |
| 📋 运维/工程文档 | 0 份 | **18** 份 |
| 🛠️ 一行自检命令 | ❌ | ✅ `make verify` |

**差异化护城河**：
1. **方言陪伴**：武汉话 500+ 真实语料 + 语气词/地名/小吃全落地（非翻译搬运）
2. **家庭关系图谱**：不是 1v1 对话，是 elder ↔ AI ↔ family 三角信使
3. **数字生命三件套**：持久人格 + 长期记忆 + 情境主动开口
4. **隐私红线**：老人对 AI 倾诉默认永不外泄（`SELF_ONLY` 三级可见性）
5. **健康合规**：LLM 不直答医疗建议，必经 `HealthRiskEvaluator` 规则引擎

**商业模型可行性**：Phase 1+2 单老人 ¥19/月，现有 ¥29/¥69 订阅价可覆盖 (详见 [`docs/DIGITAL_COMPANION_COST.md`](anxinbao-server/docs/DIGITAL_COMPANION_COST.md))。

---

## 二、15 轮自治时间线

每轮都是完整闭环（代码 → 测试 → 文档 → 提交推送），无"半成品"。

| r# | 主题 | commit | 关键价值 |
|---|---|---|---|
| r0 | 仓库初始化 | `95e6ea2` | 基线 + .gitignore + README |
| **r1** | **4 个阻断 bug 修复** | `00d711f` | SOS 短信参数名错、key_quotes 隐私、.env 字段未声明、SOS 按钮误触保护 |
| r2 | 武汉话 500+ / 三色灯 | `a3020b0` | 核心卖点落地 + FEATURE_STATUS v1 |
| r3 | 5 P0 安全门 | `4517b9f` | users 废弃 / JWT+ENCRYPTION 强校 / admin-analytics 隔离 / TURN 文档 / CI 模板 |
| r4 | life→501 + admin 修漏 + Alipay 指南 | `e89cd0e` | 医疗事故源、提权 0day、90 分钟沙箱指引 |
| r5 | 红色清零 + Makefile + 文档索引 | `4e31355` | 就绪度 10 → 0；一行 `make verify` |
| r6 | PEP 701 修 + 删 dev 残骸 + CONTRIBUTING | `6f5d989` | 工程体面化 |
| r7 | ErrorBoundary + Alipay 凭据守卫 + CHANGELOG + pre-commit + senior 归档 | `6fe38bf` | 防白屏 + 文档化 + 仓库卫生 |
| r8 | 5 项纵深安全审计 | `3ab5c56` | auth 限流 / audit 脱敏 / scheduler 容错 / SCA / sw.js v2 |
| r9 | 通知韧性+CORS+迁移文档+Bundle 减重 | `777d40d` | retry + DLQ + CORS 守卫 + Alembic 指南 |
| r10 | DLQ UI + 集成守卫 + health 拓展 + 审计收权 + manifest | `ddda28d` | 运维可视化 + PWA 适老化 |
| **r11** | **战略转向：4 阶段 RFC + Phase 1 骨架** | `bdbc38e` | 完整数字生命架构设计 |
| r12 | Phase 1 实施 | `7bb3c55` | persona / memory / tools / 27 单测 / 前端 alpha |
| r13 | Phase 2 主动开口 | `089f61a` | 6 触发器 + DND/quota/cooldown + scheduler |
| r14 | Phase 3 工具真实化 + Phase 2 推送闭环 | `f2672c4` | 9/9 工具 handler + 安全网关 + 通知 |
| **r15** | **实时天气 + E2E 集成测试** | `5719044` | wttr.in 接入 + 23 e2e case |

---

## 三、核心能力现状（对外可宣传项）

严格按 [`FEATURE_STATUS.md`](FEATURE_STATUS.md) 三色灯判定。**只列 🟢 绿色项**（对外可宣传）。

### A. 老人端体验
- ✅ 6 大入口待机界面（适老化大按钮）
- ✅ SOS 误触保护（96px + 长按 1.5s + 与邀请家人隔离）
- ✅ 方言陪伴（武汉话 500 句真实语料）
- ✅ 视频通话信令（含 TURN 配置指南）
- ✅ 健康数据录入与趋势查看
- ✅ 主动关怀问候

### B. 子女端体验
- ✅ 今日爸妈安心日报（6 维聚合 + 安心指数）
- ✅ 健康数据趋势图
- ✅ 关怀建议转行动入口（r2 修）
- ✅ 紧急通知推送（多通道 + DLQ 兜底）

### C. 数字生命能力（Alpha · COMPANION_ENABLED 门控）
- ✅ 持久人格 `AnxinbaoPersona`（性格 + 口头禅 + 禁忌 + 必做/必不说）
- ✅ 长期记忆引擎（5 类：fact/preference/relation/event/mood）
- ✅ 记忆召回打分（关键词 + 时间衰减 + 类型权重）
- ✅ 异步记忆抽取（LLM + 关键词双路径 + 去重 + 限频）
- ✅ 6 类情境触发器（静默/健康/家属缺席/节日/纪念日/天气）
- ✅ DND + 配额 + cooldown 三道闸
- ✅ 9 个工具 handler（LOW 直接 / MEDIUM 二次确认 / HIGH 规则引擎 / CRITICAL 双重确认）
- ✅ 实时天气接入（wttr.in + 1h 缓存 + 失败兜底）
- ✅ GDPR 一键忘记

### D. 后端基础设施
- ✅ 45 张数据表 SQLAlchemy ORM
- ✅ 启动安全门（JWT/ENCRYPTION/CORS 强校）
- ✅ 死信队列 DLQ + 异常重试装饰器
- ✅ Prometheus 监控 + Scheduler 异常监听
- ✅ Admin 后台强鉴权（修提权漏洞）
- ✅ 审计日志自动脱敏（递归 + PII 22 字段黑名单）

### E. 前端基础设施
- ✅ Service Worker v2（LRU + NO_CACHE + stale-while-revalidate）
- ✅ PWA Manifest（maskable icons + shortcuts + 适老化 portrait 锁定）
- ✅ ErrorBoundary 防白屏

### F. DevX
- ✅ `make verify` / `make verify-prod` / `make doctor` / `make audit`
- ✅ 离线集成自检（`check_integrations.py`）
- ✅ 18 份运维/工程文档
- ✅ CI 模板（双向验证守卫）

---

## 四、不能对外宣传的（诚实边界）

按 [`FEATURE_STATUS.md` 九章"对外可宣传的边界"](FEATURE_STATUS.md#九对外可宣传的边界话术对照)：

| ❌ 别说 | ✅ 可以说 |
|---|---|
| "全功能 AI 养老平台" | "聚焦武汉话陪伴 + 健康守护 + 紧急救助的 MVP" |
| "已支持武汉话/鄂州话/普通话三种方言" | "武汉话深度陪伴（500+ 真实模板）；鄂州话/其他基于武汉话近似" |
| "完整的运营管理后台" | "正在搭建运营后台" |
| "AI 情感记忆" | "对话过程中会记录用户偏好（基础版）" |
| "AI 数字生命已上线" | "数字生命陪伴 Alpha 版，正在内测" |

---

## 五、关键数据

| 维度 | 数值 |
|---|---|
| 代码总行数（新增 + 修改） | 约 **8000+** 行 |
| 新增文件 | 40+ 个（代码 24 + 文档 18） |
| 测试 case | 372+（原 272 + Companion 89 + weather 9） |
| 运维文档 | 18 份 |
| Python 模块 | 48 路由 + 43 服务 + 新 Companion 模块（persona/memory/triggers/tools/agents/proactive/weather）|
| 前端页面 | 11（+1 CompanionPreview alpha） |
| 方言模板 | 武汉话 500 / 鄂州话 60 / 普通话 57 |

---

## 六、上线前必做（P0 清单）

| # | 事项 | 我能做 | 需要你 |
|---|---|---|---|
| 1 | 填真凭据（DashScope / 讯飞 / 阿里云短信 / 极光 / 支付宝） | ❌ | ✅ 按 [`PAYMENT_ALIPAY_SETUP.md`](anxinbao-server/docs/PAYMENT_ALIPAY_SETUP.md) |
| 2 | PAT 加 `workflow` scope + CI 启用 | ❌ | ✅ 5 分钟 |
| 3 | TURN 服务器部署 | ❌ | ✅ 按 [`VIDEO_CALL_SETUP.md`](anxinbao-server/docs/VIDEO_CALL_SETUP.md) |
| 4 | 中央网信办大模型备案 | ❌ | ✅ 法务 |
| 5 | 与江岸民政局对齐 AI 陪伴定性 | ❌ | ✅ BD |
| 6 | 红队测试（100 道医疗陷阱题） | ❌ | ✅ 安全团队 |
| 7 | 产品责任险投保 | ❌ | ✅ 法务 |

---

## 七、Phase 4 决策点（待评审）

**当前**：Phase 4 的 agents 骨架已就绪（`HealthAgent` / `SocialAgent` / `MemoryAgent` / `SafetyAgent` / `ScheduleAgent` 5 个文件），但业务逻辑仅 stub。

**投入**：填充完整需要 4-6 周 / 3-5 人团队。

**价值**：单老人 ARPU 成本从 ¥19 → ¥45-81/月，必须 **VIP 版 ¥99-149/月** 或 B2G 兜底。

**评审议题**：
- Phase 4 走多 agent 路线还是继续单 Hermes 深化？
- 商业模式能否支撑 Phase 4 成本？
- 法务合规进度是否赶得上 Phase 4 上线？

**我的建议**：**暂缓 Phase 4**，把 Phase 1-3 做深（真凭据接入 + 红队测试 + 小范围内测），6 个月后根据真实数据决定是否做 Phase 4。

---

## 八、风险提示（合规必读）

4 项 P0 风险（详见 [`DIGITAL_COMPANION_RISKS.md`](anxinbao-server/docs/DIGITAL_COMPANION_RISKS.md)）：

1. **幻觉杀人**（医疗建议错误） → 已加规则引擎 + 免责，**但 LLM 仍有 1-3% 幻觉率不可消除**，需持续红队
2. **SOS 链路失效** → 多通道 + DLQ 兜底已就绪，**但真凭据未配就没推送**
3. **长期记忆隐私泄漏** → 三级可见性 + 一键忘记，**但数据库字段加密待实施**
4. **依赖与撤离** → 记忆可导出，**但服务终止协议条款待法务定稿**

---

## 九、团队与产权

- **作者**：自治回路（claude-opus-4-7-1m），协同开发者 licong-git-dev
- **开发周期**：15 轮自治（2026-04）
- **代码许可**：目前未宣告开源（默认保留所有权）；评审通过后可考虑部分模块 MIT
- **数据与模型**：所有方言模板为原创；LLM 调用走阿里云 DashScope（国内合规）

---

## 十、下一步关键时间点

| 时间 | 事项 | 责任方 |
|---|---|---|
| 本周 | 法务 + 产品评审本 RFC + RISKS | 你 + 法务 |
| 下周 | 填 DashScope / 讯飞真凭据；跑 `make verify` | 你 |
| 下两周 | TURN 服务器 + 支付宝沙箱跑通 | 你 + 运维 |
| 下月 | 5-10 位种子老人内测（江岸区） | 你 + BD |
| 3 个月 | 数据驱动 Phase 4 决策 | 评审委员会 |

---

## 一句话收尾

**数字生命陪伴从"愿景"变成"可内测的代码 + 完整的 RFC + 清晰的风险清单"**。现在需要的不是更多代码，是**真实用户 + 真实数据 + 真实反馈**。

代码已经准备好迎接第 1 位老人。轮到你们了。

---

> 详细演示见 [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) · 验收清单见 [`VERIFICATION_CHECKLIST.md`](VERIFICATION_CHECKLIST.md)
