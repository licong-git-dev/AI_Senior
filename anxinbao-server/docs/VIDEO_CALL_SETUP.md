# 视频通话部署指南

> 截止 2026-04，[`VideoCallPage.tsx`](../../anxinbao-pwa/src/pages/VideoCallPage.tsx) 仅配置了 Google STUN（`stun:stun.l.google.com:19302`），**没有 TURN 中继**。在国内运营商家庭宽带 + 路由器双层 NAT 场景下，约 **70% 通话会无法建立**。

本文给出三种部署方案的对比与选型建议，配置完后只需在前端 `.env` 设置环境变量即可生效，**无需改代码**。

---

## 一、为什么需要 TURN

WebRTC 建立 P2P 连接时：

| 场景 | STUN 够用吗？ | TURN 必要吗？ |
|---|---|---|
| 公网直连 | ✅ | ❌ |
| 单层 NAT（公司宽带） | 大概率 ✅ | 不必要 |
| 双层 NAT（家庭宽带 + 自购路由） | ❌ 多数失败 | **必要** |
| 对称 NAT（部分运营商 4G/5G） | ❌ | **必要** |
| Wi-Fi 与 4G 切换 | 可能掉线 | **必要** |

老年用户家庭普遍是「电信光猫 + 自购路由」双层 NAT，**没有 TURN 视频通话功能等于不可用**。

---

## 二、三种方案对比

### 方案 A：自建 coturn（推荐）

| 维度 | 评估 |
|---|---|
| 月成本 | 阿里云/腾讯云 1 核 1G 公网带宽 ≈ ¥40-80/月（按 5Mbps 计算） |
| 时延 | 国内 BGP 机房 ≈ 30-80ms |
| 控制权 | ✅ 完全掌握用户音视频流量（合规可控） |
| 部署难度 | ⭐⭐ 单进程容器，1 小时即可上线 |
| 适合阶段 | **0 → 10000 用户** |

**最快部署步骤：**

```bash
# 在已购的阿里云/腾讯云 ECS 上
docker run -d --network=host --name coturn \
  -e DETECT_EXTERNAL_IP=yes \
  coturn/coturn \
  -n --log-file=stdout \
  --min-port=49152 --max-port=49200 \
  --user=anxinbao:CHANGE_ME_LONG_RANDOM \
  --realm=anxinbao.com \
  --no-tls --no-dtls
```

**安全组放通**：UDP 3478（STUN/TURN）+ UDP 49152-49200（媒体流）。

**前端配置**（`anxinbao-pwa/.env.local`）：

```bash
VITE_TURN_URL=turn:turn.your-domain.com:3478
VITE_TURN_USERNAME=anxinbao
VITE_TURN_CREDENTIAL=CHANGE_ME_LONG_RANDOM
```

**生产环境建议**：
- 加 TLS（`--cert` / `--pkey`），URL 改 `turns:turn.your-domain.com:5349`，避免运营商劫持
- 用动态用户凭证（`--use-auth-secret`）+ 后端按用户签发临时 token，比静态密码安全
- 监控带宽用量（`coturn` 自带 `--web-admin`），按账单预警

---

### 方案 B：云厂商 TURN 服务（懒人选择）

| 厂商 | 单价 | 备注 |
|---|---|---|
| 阿里云 RTC | ¥0.0048/分钟（视频） | 含 TURN 的全套 RTC 服务，可直接替代 WebRTC 自研 |
| 腾讯云 TRTC | ¥0.0050/分钟 | 同上 |
| 即构 ZEGO | ¥0.0070/分钟 | 国际化好，国内体验稳定 |

**月成本估算**：1000 用户 × 平均每人每月 5 分钟视频 = 5000 分钟 ≈ ¥24-35/月。

**选型判断**：
- 如果 **你不准备维护音视频技术栈**：直接用云 RTC SDK，节省 80% 后续工作量；前端代码也要改用厂商 SDK
- 如果 **你想留一手控制权 + 流量便宜**：自建 coturn

---

### 方案 C：免费/试用 TURN 服务（仅原型期）

- [Twilio Network Traversal Service](https://www.twilio.com/stun-turn) — 国内访问慢，有免费额度
- [Open Relay Project](https://www.metered.ca/tools/openrelay/) — 免费但容量小、国内出口受限

⚠️ **不推荐用于生产**：国内访问稳定性差，且无 SLA。仅适合内部 demo。

---

## 三、推荐路径

| 阶段 | 用户数 | 推荐 |
|---|---|---|
| MVP / 原型 | 0-100 | C（免费 TURN）+ 显式提示用户"通话功能为试用版" |
| 内测 / 早期付费 | 100-2000 | **A（自建 coturn）**：成本可控、控制权强 |
| 规模化 | 2000+ | A 维持 + 多区域机房；或评估迁移到 B（云 RTC SDK） |

---

## 四、前端配套校验

[`VideoCallPage.tsx`](../../anxinbao-pwa/src/pages/VideoCallPage.tsx) 已加入 `TURN_CONFIGURED` 探测：

- 通话失败时，如果未配置 TURN，**会展示明确提示**：
  > 当前未配置 TURN 中继服务器，在部分家庭网络（约 70% 国内 NAT 场景）下无法直连。建议改用语音电话；或联系管理员配置 TURN 服务

- 这避免老人/家属遇到神秘的"通话失败"，把锅甩给客服

---

## 五、监控与告警

部署后建议加一个简单的通话成功率指标：

```javascript
// 前端：通话结束时上报
authFetch('/api/video/metrics', {
  method: 'POST',
  body: JSON.stringify({
    call_id, duration_sec, ended_reason,
    turn_used: TURN_CONFIGURED,
    ice_state: pc.iceConnectionState,
  })
});
```

后端聚合：每天看 `connection_failed / total_calls` 比例。**理想 < 5%**。如果 > 20% 就要考虑增加 TURN 节点或迁云 RTC。

---

## 六、决策清单

在开通通话功能前，请逐项确认：

- [ ] 已选定方案（A/B/C）
- [ ] 已购买云资源 / 注册云 RTC 账号
- [ ] 已配置 `VITE_TURN_URL` 等环境变量到前端 `.env`
- [ ] 已在生产环境验证：测试设备分别在 4G、家庭 Wi-Fi、办公网下能跨网通话
- [ ] 已评估月度成本是否超出预算（带宽 + 通话时长）
- [ ] 已与客服团队对齐"通话失败"话术
- [ ] 已加监控告警（成功率 < 80% 时通知运维）

**未完成清单中任何一项 → 不建议在生产环境开放视频通话入口**（可在 [`StandbyScreen.tsx`](../../anxinbao-pwa/src/pages/StandbyScreen.tsx) 隐藏视频按钮）。
