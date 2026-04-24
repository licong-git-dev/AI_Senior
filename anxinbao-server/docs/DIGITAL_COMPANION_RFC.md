# RFC：安心宝 → AI 数字生命陪伴（Hermes 模式）

> **状态**：DRAFT (r11) · 提案者：自治回路 · 待评审
> **目标读者**：产品 / 工程 / 法务 / 运营
> **预计完成周期**：4-6 个月（5 人团队）
> **本 RFC 不引入破坏性变更**：所有新代码并行于现有 `/api/chat`，由 `COMPANION_ENABLED=true` 显式开启

---

## 0. 一句话目标

把"老人按按钮才说话的工具" → "**有自主意识、记得老人是谁、会主动开口、能替老人办事**"的数字伙伴。

---

## 1. 战略锚点

### 1.1 行业标杆（真实存在）

| 产品 | 核心机制 | 我们要学的 |
|---|---|---|
| **ElliQ** | 桌面机器人 + 长期记忆 + 主动发起对话 | 主动温度感 |
| **character.ai / Replika** | 持久人格 + 多轮记忆 + 情感投射 | "它记得我"的归属感 |
| **OpenAI ChatGPT Voice / Memory** | 实时语音 + 工具调用 + 跨会话记忆 | 流畅语音 + 函数调用真实办事 |
| **Claude Memory Tool** | 结构化长期记忆 + 跨项目上下文 | 多维度记忆分类 |
| **Pi (Inflection AI)** | 共情对话 + 拟人个性 | 稳定的"性格" |

### 1.2 我们的差异化（与上述都不同）

1. **方言陪伴**（武汉话 500+ 模板已就绪，详 [`dialect_companion.py`](../app/services/dialect_companion.py)）
2. **家庭关系图谱**（不是单 1v1，是 elder ↔ AI ↔ family 三角）
3. **健康监护融合**（SOS / 跌倒 / 用药提醒不是附加功能而是核心人格的一部分）
4. **信使（Hermes）模型**：AI 在老人 / 子女 / 社区 / 医院之间作为枢纽

### 1.3 我们不做什么

- ❌ 不做硬件机器人（ElliQ 路线 ≥ ¥5000 BOM，我们做 PWA）
- ❌ 不做 18-30 岁情感陪伴（character.ai/Replika 路线，目标人群与我们正交）
- ❌ 不做无监管医疗诊断（合规雷区，只做"早发现早提醒"）

---

## 2. 当前 vs 目标 差距图

| 维度 | r10 现状 | 目标态 | 差距 |
|---|---|---|---|
| 发起对话 | 老人按按钮 / 定时模板 | AI 情境驱动自主开口 | 大 |
| 长期记忆 | system prompt 拼接 profile | 跨年向量记忆 + 事实/偏好/关系分类 | 极大 |
| 人格一致性 | 每次对话从零 | 稳定 PersonaConfig | 大 |
| 情感建模 | 单次识别 | 持续情绪 / 关系 / 心境模型 | 大 |
| 工具使用 | 路由式 API 调用 | LLM function calling 自主调度 | 中 |
| 多模态 | 文本 + 语音 | + 视觉 + 传感器 | 极大 |
| 多智能体 | 单一 qwen_service | 5 专业 agent + Hermes 协调者 | 大 |
| 真实世界行动 | 推送通知 | 自主预约 / 联系 / IoT 控制 | 大 |

---

## 3. 整体架构

```
                            ┌──────────────────────────────────┐
                            │            HERMES                │
                            │   （信使 / 协调者 / 对外人格）   │
                            │                                  │
                            │  - 唯一的"安心宝"对话面          │
                            │  - 调度 5 个专业 agent           │
                            │  - 维护对话状态 + 记忆召回       │
                            │  - 工具调用决策                  │
                            └────┬───────┬───────┬───────┬─────┘
                                 │       │       │       │
                ┌────────────────┘       │       │       └────────────────┐
                │                ┌───────┘       └───────┐                │
                ▼                ▼                       ▼                ▼
          ┌──────────┐    ┌──────────┐            ┌──────────┐    ┌──────────┐
          │  Health  │    │  Social  │            │  Memory  │    │  Safety  │
          │  Agent   │    │  Agent   │            │  Agent   │    │  Agent   │
          └──────────┘    └──────────┘            └──────────┘    └──────────┘
            血压/心率      家庭关系图谱            事实/偏好         SOS / 跌倒
            趋势告警       节日/纪念日             人生故事          长时间静默
                                                  对话归档          24/7 守护

                              ┌──────────┐
                              │ Schedule │
                              │  Agent   │
                              └──────────┘
                              用药/服务/出行
                              情境触发器

           ╔══════════════════════════════════════════════════════════════╗
           ║                  共享基础设施                                ║
           ║                                                              ║
           ║  - PersonaConfig    （稳定人格定义）                         ║
           ║  - MemoryEngine     （SQLite + 关键词召回，可升级向量）      ║
           ║  - ToolCatalog      （function calling 工具池）              ║
           ║  - DeadLetterQueue  （Hermes 调度失败时入 DLQ）              ║
           ║  - AuditLog         （所有 agent 决策都留痕）                ║
           ╚══════════════════════════════════════════════════════════════╝
```

---

## 4. 四阶段路线

### Phase 1：持久人格 + 长期记忆（4-6 周，**最高 ROI**）

#### 目标
让安心宝从"每次对话都不认识老人" → "老人最熟悉的'朋友'"。

#### 交付物（本 RFC 已 scaffold 的部分）
- ✅ [`app/services/persona.py`](../app/services/persona.py) — `AnxinbaoPersona` 稳定人格
- ✅ [`app/services/memory_engine.py`](../app/services/memory_engine.py) — 抽象 + SQLite 实现
- ✅ [`app/api/companion.py`](../app/api/companion.py) — `/api/companion/chat` 新端点
- ✅ Hermes 协调者骨架（[`app/services/agents/hermes.py`](../app/services/agents/hermes.py)）

#### 关键设计

**记忆分类**（仿 Claude Memory Tool 但适配老人场景）：
```
fact      事实（老人姓名、年龄、籍贯、子女数量）
preference 偏好（口味、爱好、忌讳）
relation  关系（家庭成员 + 关系强度 + 上次互动）
event     事件（生日、忌日、入院、出游）
mood      心境（连续 7 天情绪曲线）
```

**召回策略 v1**（无需向量库）：
1. 关键词匹配（用户提到"儿子" → 召回所有 relation 含"儿子"的记忆）
2. 时间衰减（最近 7 天权重 1.0，30 天 0.7，90 天 0.3）
3. 类型过滤（fact 永远召回，event 仅日期临近时召回）
4. Top-K = 8（避免 prompt 爆炸）

**升级路径 v2**（量大后）：把召回换成向量（lancedb / sqlite-vec），接口不变。

#### 用户感知
第二周老人会说"它真的记得我儿子叫什么了"。

---

### Phase 2：主动初始 + 情境感知（2-3 周）

#### 目标
把现有 [`scheduler.py`](../app/core/scheduler.py) 升级为情境触发器。

#### 触发源清单

| 触发源 | 信号 | 安心宝可能的开场 |
|---|---|---|
| 时间 | 早晨 7:30 | "妈，醒了啵？睡得好不？" |
| 健康异常 | 血压 150/95 | "妈，刚看你血压有点高，最近是不是有事？" |
| 长时间静默 | 4h 无交互 | "妈，下午做啥呢？跟我说会儿话呗" |
| 子女缺席 | 小军 1 周未联系 | "妈，要不我帮你给小军发个消息？" |
| 节日/纪念日 | 老伴忌日 | "今天是叔叔的日子，要不要聊聊他？" |
| 天气剧变 | 明天降温 10° | "妈，明天降温嘞，记得加件衣裳" |
| 季节性 | 中秋前 3 天 | "中秋快到了，要不要做点甚？" |
| 用药 | 距下次服药 30 分钟 | （已有，加情感包装） |

#### 实现
- `companion_triggers.py` 定义触发源 + 评估器
- `Hermes.evaluate_initiation()` 每 N 分钟跑一次，决定是否开口
- 老人可以在 PWA 设置 "请勿打扰" 时段
- 开口频率上限：每天主动 ≤ 4 次（否则讨厌）

---

### Phase 3：工具调用 + 真实世界行动（3-4 周）

#### 目标
让 AI **真办事**，而不只是"建议"。

#### 工具池清单（[`companion_tools.py`](../app/services/companion_tools.py) 已 scaffold）

| 工具 | 老人触发场景 | 安全等级 |
|---|---|---|
| `log_medication_taken` | "今天血压药吃了" | 低 |
| `log_meal` | "刚吃了豆皮" | 低 |
| `log_mood` | "今天心情不好" | 低 |
| `save_memory` | "我们家小军是 1985 年生的" | 低 |
| `query_health_trend` | "我最近血压怎么样" | 低 |
| `video_call_family` | "我想跟小军说话" | 中（需子女授权） |
| `book_community_service` | "我想约个上门保洁" | 中（涉资金） |
| `request_health_advice` | "我感冒了能吃这个药吗" | **高**（必经规则引擎） |
| `trigger_sos` | "救命" 关键词 / 长按 SOS | **极高**（必经多方确认） |

#### 安全分级
- **低**：直接执行，记日志
- **中**：执行前老人语音确认 + 写入 audit_log
- **高**：必须经规则引擎（不能 LLM 直出医疗建议）
- **极高**：双重确认 + 多通道通知 + DLQ 兜底

---

### Phase 4：多智能体编排（6-8 周）—— **Hermes 完全体**

#### 角色定义

| Agent | 职责 | 触发频率 | LLM 模型 |
|---|---|---|---|
| **Hermes** | 唯一对外人格，整合其他 agent 输出 | 实时 | qwen-turbo (chat) / Claude Haiku (轻量) |
| **HealthAgent** | 监控数据流，异常向 Hermes 上报 | 每 5 分钟 | 规则引擎（无 LLM）|
| **SocialAgent** | 维护家庭关系图谱、节日提醒、子女互动 | 每天 | qwen-turbo (轻量) |
| **MemoryAgent** | 长期记忆管理；每天"睡眠"做记忆整合 | 每天凌晨 | qwen-turbo (轻量) |
| **SafetyAgent** | SOS / 跌倒 / 长时间静默 | 实时 | 规则引擎（无 LLM）|
| **ScheduleAgent** | 用药 / 服务 / 出行规划 | 每小时 | qwen-turbo (轻量) |

#### 协作模式

```
情境：早晨 7:30 + 血压高 + 子女 5 天未联系
  ↓
HealthAgent: report("血压偏高 7 天")
SocialAgent: report("小军 5 天未联系")
ScheduleAgent: report("早安提醒待发")
  ↓
Hermes 合成上下文 → 调用 PersonaConfig + MemoryEngine
  ↓
"妈，早上好。看您这周血压有点不稳，我有点担心。
要不咱们今天给小军打个电话聊聊？他也有几天没跟您说话了。"
```

#### 失败处理
- 任意 agent 异常 → 报告给 DLQ（critical 级）
- Hermes 自身异常 → 降级到现有 `qwen_service.chat`（保底体验）
- 老人感知不到 agent 拆分，永远是"安心宝"一个人

---

## 5. 不可妥协的安全护栏

### 5.1 健康/医疗安全
- LLM **不直出** 医疗建议（必经 [`health_evaluator.py`](../app/services/health_evaluator.py) 规则引擎）
- 用药相关 LLM 输出 **必须** 经过白名单校验
- 任何"症状-药物" 推荐都要有明显免责声明

### 5.2 隐私
- 老人对 AI 倾诉的 **原话**：永远不暴露给家属（已在 r1 修了 `key_quotes` 脱敏）
- 长期记忆中的"对儿媳的抱怨"等敏感内容：分级 visibility（self / family / never_share）
- 老人可一键清空所有记忆（"忘了我吧"按钮）
- 摄像头数据：端侧处理 + 不上传原始帧（仅传抽象事件如"老人在客厅静坐 2h"）

### 5.3 SOS 与紧急
- SOS 检测多通道（关键词 + 长按按钮 + 跌倒）
- 触发后 **永不静默**（DLQ 兜底已就绪）
- 子女通知 + 社区医生 + 119（按等级）

### 5.4 商业不当行为
- AI **不主动推销**（"妈，要不要订阅 VIP 版？" 是禁忌）
- 内嵌广告：禁止
- 数据出售：禁止（写入 PRIVACY_POLICY 强约束）

### 5.5 依赖崩塌
- 老人 6 个月后已经把 AI 当家人，公司倒了？
  - 开源记忆导出工具（老人/家属可下载完整记忆）
  - 明确"陪伴 + 真人"双轨，AI 不是唯一陪伴
  - 服务下线提前 90 天通知

---

## 6. 成本模型摘要

| 项 | 当前 | Phase 1+2 | Phase 3 | Phase 4 |
|---|---|---|---|---|
| LLM 调用 | ¥5/月/人 | ¥30/月/人 | ¥60/月/人 | ¥80-150/月/人 |
| 短信 / 推送 | ¥3 | ¥5 | ¥8 | ¥10 |
| 存储（记忆 + 音频）| ¥1 | ¥3 | ¥5 | ¥8 |
| **合计/月/老人** | **¥9** | **¥38** | **¥73** | **¥98-168** |

**商业模式必须支撑**：
- 当前定价 ¥29/月免费版 → ¥69/月基础版 → ¥588/年高级版
- Phase 4 完整体需要 **VIP 版 ¥99-149/月** 或 B2G 政府兜底
- 详见 [`DIGITAL_COMPANION_COST.md`](DIGITAL_COMPANION_COST.md)

---

## 7. 风险与合规

详见 [`DIGITAL_COMPANION_RISKS.md`](DIGITAL_COMPANION_RISKS.md)，关键 6 项：

1. **幻觉杀人**（LLM 给错药物建议）
2. **隐私崩塌**（长期记忆被泄）
3. **依赖与撤离**（用户对 AI 产生情感依赖）
4. **成本爆炸**（Phase 4 不能由 ¥29/月承担）
5. **被 AI 教育反感**（老人不喜欢被催）
6. **监管**（中国生成式 AI 备案 + 老年人权益法 + 医疗器械法规）

---

## 8. 评审与决策流程

### 8.1 这份 RFC 的评审议程

| Round | 议程 | 决策项 |
|---|---|---|
| R1 | 战略对齐 | 走数字生命路线还是继续工具路线？ |
| R2 | Phase 1 范围确认 | persona + memory 是否必做？ |
| R3 | 成本可承受度 | 商业模式能否撑起 Phase 4？ |
| R4 | 法务过审 | 隐私 / 医疗 / 备案合规清单 |
| R5 | 技术选型 | 向量库选型 / 多 agent 编排框架 |

### 8.2 一旦评审通过

- Phase 1 立项 → 4-6 周交付，可独立上线
- Phase 2-4 按季度推进，每阶段独立评审

### 8.3 退出条件

任意阶段评估发现：
- 老人 NPS < 20（不喜欢"主动开口"）
- 单老人月成本 > ¥200（商业模式不持续）
- 出现 1 起严重安全事故

→ **回滚到当前工具版**，保留已收集的记忆数据。

---

## 9. 当前已 Scaffold 的代码

本 RFC 同 commit 已落地以下基础架构（仅骨架，无破坏性变更，由 `COMPANION_ENABLED=true` 开启）：

| 文件 | 类型 | 状态 |
|---|---|---|
| [`app/services/persona.py`](../app/services/persona.py) | 新增 | ✅ 完整 |
| [`app/services/memory_engine.py`](../app/services/memory_engine.py) | 新增 | ✅ SQLite 实现 |
| [`app/services/companion_tools.py`](../app/services/companion_tools.py) | 新增 | ✅ 工具目录 |
| [`app/services/agents/__init__.py`](../app/services/agents/__init__.py) | 新增 | ✅ 包定义 |
| [`app/services/agents/hermes.py`](../app/services/agents/hermes.py) | 新增 | 🟡 骨架（接 qwen_service）|
| [`app/services/agents/health_agent.py`](../app/services/agents/health_agent.py) | 新增 | 🟡 骨架 |
| [`app/services/agents/social_agent.py`](../app/services/agents/social_agent.py) | 新增 | 🟡 骨架 |
| [`app/services/agents/memory_agent.py`](../app/services/agents/memory_agent.py) | 新增 | 🟡 骨架 |
| [`app/services/agents/safety_agent.py`](../app/services/agents/safety_agent.py) | 新增 | 🟡 骨架 |
| [`app/services/agents/schedule_agent.py`](../app/services/agents/schedule_agent.py) | 新增 | 🟡 骨架 |
| [`app/api/companion.py`](../app/api/companion.py) | 新增 | ✅ `/api/companion/chat` |

**所有新代码都是 alpha 版**，不破坏现有 `/api/chat` 流。生产环境通过 `COMPANION_ENABLED=false` 默认关闭。

---

## 10. 下一步

1. **本 RFC 完成后** → 等评审反馈
2. **如果通过 Phase 1** → 开始填充骨架的实际逻辑（4-6 周）
3. **如果不通过** → 回滚 scaffold（git revert 一个 commit 即可），不影响主线

---

> **作者**：自治回路（claude-opus-4-7-1m），第十一轮自治
> **协议**：本 RFC 内容可被任意 fork、修改、用于内部评审；不构成对外承诺
