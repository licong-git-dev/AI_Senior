# 安心宝 · 30 分钟演示脚本

> 适用场景：投资人路演 / 合伙人答辩 / 新人 onboarding / 法务评审
> 前置条件：Python 3.12+、Node 18+、一张 DashScope API Key（可用 CI 测试 key 降级演示）

---

## 0. 开场（2 分钟）

**说辞**：
> "接下来 30 分钟，我会演示安心宝的三层能力：**工具版**（老人能主动按按钮用）、**陪伴版**（AI 主动开口，记得老人）、**信使版**（替老人办事，跨家庭协调）。全程现场执行，无 PPT。"

**打开浏览器两个标签**：
1. `http://localhost:3000/` — 老人端主入口
2. `http://localhost:3000/?mode=child` — 子女端面板

**打开终端两个标签**：
1. 后端 uvicorn 日志（对观众隐藏）
2. curl 命令面板

---

## 1. 环境准备（3 分钟）

### 1.1 克隆并跑预检

```bash
git clone https://github.com/licong-git-dev/AI_Senior.git
cd AI_Senior
make doctor       # 综合诊断 Python/Node/Git/.env/集成
```

**预期输出**：
```
===== 安心宝综合诊断 =====
→ Python 版本
Python 3.12.x
→ Node 版本
v20.x.x
→ 当前分支：main  待提交文件数：0
→ 集成真实性
🟢 dashscope_qwen ... [real]
🔴 aliyun_sms ... [missing]
...
✅ 守卫按预期拦截了缺凭据的生产配置
```

**演示点**：
> "看这个 doctor 脚本 —— 不用跑服务就知道哪些集成是 real / placeholder / missing。这是我们 15 轮演进的 DNA：**诚实就绪度**，不允许'看起来 OK 实际 mock'。"

### 1.2 启动服务

```bash
cd anxinbao-server
export COMPANION_ENABLED=true    # 开启数字生命模式
export DEBUG=true
export DASHSCOPE_API_KEY=sk-xxx  # 你的真 key
python main.py
```

```bash
# 另一个终端
cd anxinbao-pwa
npm install  # 首次
npm run dev  # localhost:3000
```

**预期日志包含**：
```
INFO: 安心宝云端服务启动中...
INFO: 数据库初始化完成
INFO: Companion Phase 2 主动评估任务已注册（8/13/19 点）
INFO: 安心宝云端服务启动完成
```

---

## 2. Phase 1 演示 · 持久人格 + 长期记忆（8 分钟）

### 2.1 打开 Alpha 预览页

浏览器 → `http://localhost:3000/?mode=companion-preview`

**讲解**：
- 顶部卡片展示 **AnxinbaoPersona**（不可变人格）：温暖 0.9 / 耐心 0.95 / 主动 0.6
- 展示"口头禅"：您讲，我听着嘞 / 莫急莫急 / 我陪您
- 展示记忆统计（当前 0 条）

### 2.2 第一次对话

在对话框输入：**"我叫张老头，今年 72 岁，有三个孙子"**

**观察**：
- 1-2 秒内返回文本
- 消息下方显示"🔗 召回了 0 条记忆"（新用户）

### 2.3 查看记忆（后端异步抽取）

等 3-5 秒，刷新页面，看顶部记忆统计从 0 → 2-3

**curl 查看**：
```bash
TOKEN=$(curl -sX POST localhost:8000/api/auth/login \
  -d '{"username":"13800138000","password":"Test123456"}' \
  -H 'Content-Type: application/json' | jq -r .access_token)

curl -s localhost:8000/api/companion/memory/list \
  -H "Authorization: Bearer $TOKEN" | jq '.items[] | {type, content, keywords}'
```

**预期输出**（由 MemoryConsolidator LLM 自动抽取）：
```json
{
  "type": "fact",
  "content": "老人叫张老头",
  "keywords": ["姓名"]
}
{
  "type": "fact",
  "content": "今年 72 岁",
  "keywords": ["年龄"]
}
{
  "type": "relation",
  "content": "有三个孙子",
  "keywords": ["孙子"]
}
```

**演示亮点**：
> "注意，**不是我显式存的，是 AI 从对话中自己抽出来的**。这就是数字生命的核心：它不只是回复，它在**主动学习老人是谁**。"

### 2.4 第二次对话 —— 验证记忆召回

输入：**"我想跟我孙子视频聊聊"**

**观察**：
- 消息下方显示"🔗 召回了 1 条记忆"
- 回复会带上"您家三个孙子里想先跟哪个说？"之类（具体措辞取决于 LLM）

**讲解**：
> "它**记得**我说过"三个孙子"。这就是 character.ai 级的体验，但架构是我们自研的 SQLite + 关键词召回（升级路径清晰：v2 换向量库即可）。"

### 2.5 一键忘记（GDPR 合规演示）

点击右上角"忘记我吧"按钮 → window.confirm 二次确认 → 清空

**讲解**：
> "老人随时可以说'忘了我吧'。这是合规红线。不是说说，是真删 DB 记录。"

---

## 3. Phase 2 演示 · 主动开口（8 分钟）

### 3.1 DND 配置

**curl 看默认 DND**：
```bash
curl -s localhost:8000/api/companion/dnd -H "Authorization: Bearer $TOKEN" | jq
```

```json
{
  "dnd_start": "22:00",
  "dnd_end": "07:00",
  "daily_quota": 4,
  "push_proactive": 1,
  "enabled": true
}
```

**讲解**：
> "默认 22 点到 7 点请勿打扰，每天最多 4 条主动消息。老人可随时在设置页改。这是我们学 ElliQ 但改进的地方 —— **克制**是陪伴品的生命线。"

### 3.2 手动触发评估

Alpha 页面上点"手动触发评估"按钮。

**观察**：
- 几秒后 alert 弹"生成了 N 条主动消息"
- 主动消息卡片出现"安心宝来消息了"

**讲解 6 类触发器**：
| 触发 | 情境 |
|---|---|
| silence | 4h 无活动 → 问候 |
| health_anomaly | 连续 3 天血压偏高 → 关切 |
| family_absence | 子女 7 天无联系 → 暗示 |
| festival | 节日前 3 天 → 祝福 |
| memorial | 今日纪念日 → 温柔提及 |
| weather | 次日降温 8°C / 暴雨 / 高温 → 添衣 |

### 3.3 查看触发器注册表

```bash
curl -s localhost:8000/api/companion/proactive/triggers \
  -H "Authorization: Bearer $TOKEN" | jq
```

```json
{
  "triggers": [
    {"name": "silence", "cooldown_hours": 4},
    {"name": "health_anomaly", "cooldown_hours": 12},
    {"name": "family_absence", "cooldown_hours": 48},
    {"name": "festival", "cooldown_hours": 48},
    {"name": "memorial", "cooldown_hours": 12},
    {"name": "weather", "cooldown_hours": 24}
  ]
}
```

### 3.4 关键设计：推送 + 隐私

**讲解**：
> "主动消息会通过极光推送给老人设备，**但推送正文只显示前 40 字**，完整内容在 inbox。为什么？因为 LLM 输出可能含敏感话题（老人对 AI 抱怨儿媳等），**通知栏是公开区域**，隐私必须兜底。"

---

## 4. Phase 3 演示 · 工具调用真实化（6 分钟）

### 4.1 LOW 级工具 —— 直接执行

```bash
curl -sX POST localhost:8000/api/companion/tools/call \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"log_mood","params":{"mood":"happy","note":"今天跟孙子视频很开心"}}'
```

**预期**：
```json
{
  "tool": "log_mood",
  "safety_level": "low",
  "result": {"ok": true, "result": {"mood": "happy", "synced_to_memory": true}}
}
```

**讲解**：
> "LOW 级工具（打卡/记录）直接执行，秒级响应。不打断老人。"

### 4.2 MEDIUM 级工具 —— 二次确认

```bash
# 第一步：发起请求
curl -sX POST localhost:8000/api/companion/tools/call \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"video_call_family","params":{"family_member_id":"fam_123","family_member_name":"小军"}}'
```

**预期**：
```json
{
  "requires_confirmation": true,
  "safety_level": "medium",
  "confirm_token": "conf_xXxXxXxX",
  "ttl_seconds": 300,
  "hint": "请向老人二次确认后，带 confirm_token 再次调用 /tools/call"
}
```

**讲解**：
> "MEDIUM 级第一次不真执行，返回 token。前端弹'要打给小军吗？'。"

然后 Alpha 页面会看到新的"待确认"卡片。点"确认"。

### 4.3 CRITICAL 级工具 —— 双重确认 + emergency 链路

```bash
# 第一步
curl -sX POST localhost:8000/api/companion/tools/call \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"trigger_sos","params":{"reason":"演示测试"}}'
```

**讲解**：
> "CRITICAL 级 TTL 只有 120 秒（更严），老人必须立刻确认。真执行会触发 `emergency_service.trigger_sos` —— 多通道通知 + DLQ 兜底（r9 实现）。"

**演示**：不要真确认 SOS（会真发短信），展示有个"取消"按钮让老人防误触。

---

## 5. 安全红线演示（2 分钟）

### 5.1 关闭 Companion 端点返 503

```bash
# 模拟生产关闭 Companion
COMPANION_ENABLED=false curl -s localhost:8000/api/companion/persona
```

```json
{
  "code": "companion_disabled",
  "message": "Companion (数字生命陪伴) 模式默认关闭。设置环境变量 COMPANION_ENABLED=true 启用",
  "doc": "anxinbao-server/docs/DIGITAL_COMPANION_RFC.md"
}
```

### 5.2 生产模式启动守卫

```bash
DEBUG=false python main.py
```

**预期**（如果缺凭据）：
```
[FATAL] 生产环境启动被拒绝，缺少以下不可妥协的密钥：
  - JWT_SECRET_KEY 必须通过环境变量显式设置...
  - ENCRYPTION_KEY 必须设置...
  - ALLOWED_ORIGINS 含不安全条目: localhost:3000（本地地址不应出现在生产 CORS）
```

**讲解**：
> "这是启动安全门 —— DEBUG=false 时缺关键凭据直接 SystemExit。上线前不可能悄悄部署测试配置。"

---

## 6. 一行自检演示（1 分钟）

```bash
make verify
```

**讲解**：
> "一行命令跑 272 单测 + 集成自检。CI 也跑这个。**不允许'手动测过一遍，应该没问题'上线**。"

---

## 7. Q&A 常见问题（可提问环节）

| 问 | 答 |
|---|---|
| 为什么是武汉话？ | 江岸区切入（武汉老龄化最高中心城区），先打透再扩 |
| 跟小度音箱有啥区别？ | 小度是工具，我们是伙伴（长期记忆 + 主动开口 + 家庭关系图谱） |
| 数据在哪？ | 端侧 SQLite + 云端加密。老人可一键导出 / 删除 |
| 跑一个老人月成本？ | Phase 1+2 约 ¥19，Phase 3 约 ¥32，Phase 4 约 ¥45-81。详见 COST.md |
| 监管风险？ | 中央网信办大模型备案进行中；不做诊断只做提醒；LLM 不直答医疗 |
| 代码质量？ | 372+ 测试，15 轮持续修复，[FEATURE_STATUS.md](FEATURE_STATUS.md) 三色灯公开 |

---

## 8. 演示结束语（1 分钟）

> "安心宝不是又一个 AI 聊天机器人。我们花了 15 轮自治把它做成一个**有人格、有记忆、会主动、能办事的数字伙伴**。
>
> 老人不孤独，子女不内疚，社区不被动。
>
> **代码已经准备好迎接第 1 位真老人。剩下的是你们的决策**：凭据、法务、试点。
>
> 谢谢。"

---

## 附录 · 故障排查

| 问题 | 原因 | 解决 |
|---|---|---|
| 对话无响应 | DASHSCOPE_API_KEY 错 | 换 key；或 mock_qwen fixture 看骨架 |
| 主动消息 0 条 | 还在 cooldown | `DELETE /api/companion/confirmations/*` 或删 `companion_proactive.db` |
| 视频通话失败 | TURN 未配置 | 见 [VIDEO_CALL_SETUP.md](anxinbao-server/docs/VIDEO_CALL_SETUP.md) |
| 推送无响应 | JPush 凭据 / 通道未接 | DLQ 会记录，看 `/api/admin/dlq` |
| Alpha 页面 503 | `COMPANION_ENABLED=false` | 检查环境变量 |

---

> **准备下次演示**：按本脚本从 0 打到 20 分钟，应顺利。超时意味着环境有问题，参照附录排查。
