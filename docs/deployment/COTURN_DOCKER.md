# 自建 coturn 部署指南（视频通话生产化）

> 落地 [VIDEO_CALL_SETUP.md](../../anxinbao-server/docs/VIDEO_CALL_SETUP.md) 方案 A。
> 本文给出**最简一行 docker-compose 部署 + 监控 + 凭据管理** 全链路。

---

## 一、为什么必须自建 coturn

- 国内家庭宽带 70%+ 是双层 NAT
- 没有 TURN 中继 → 视频通话直接打不通
- 云厂商 TURN 服务（如阿里云 RTC）月费 ¥3000+
- 自建 coturn 月费 ¥40-80（1 核 1G 公网带宽 5Mbps）

---

## 二、最简部署（docker-compose 一行起）

### Step 1 · 准备云服务器
- 阿里云 / 腾讯云 ECS：1 核 1G 起 + 5 Mbps 公网带宽
- 操作系统：Ubuntu 22.04 LTS
- 域名：turn.your-domain.com（自备 DNS A 记录指向 ECS 公网 IP）

### Step 2 · 安装 docker-compose
```bash
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin
```

### Step 3 · 创建 docker-compose.yml
```yaml
# /opt/coturn/docker-compose.yml
version: '3'
services:
  coturn:
    image: coturn/coturn:4.6
    container_name: anxinbao-coturn
    network_mode: host  # 必须 host 网络让 coturn 拿到真实 IP
    restart: unless-stopped
    volumes:
      - ./turnserver.conf:/etc/coturn/turnserver.conf:ro
      - ./logs:/var/log/coturn
    environment:
      - DETECT_EXTERNAL_IP=yes
```

### Step 4 · 创建 turnserver.conf
```bash
# /opt/coturn/turnserver.conf
listening-port=3478
tls-listening-port=5349

# 公网 IP（从 ECS 控制台拷贝，或用 dig +short turn.your-domain.com）
external-ip=YOUR.PUBLIC.IP.HERE

# realm 域（任意，但必须与客户端配置一致）
realm=anxinbao.com

# 媒体端口范围（防火墙也要放通）
min-port=49152
max-port=49200

# 静态用户（生产环境换为 use-auth-secret 见后文）
user=anxinbao:CHANGE_ME_LONG_RANDOM_PASSWORD

# 不允许中继到本地（防 SSRF）
no-multicast-peers
denied-peer-ip=10.0.0.0-10.255.255.255
denied-peer-ip=172.16.0.0-172.31.255.255
denied-peer-ip=192.168.0.0-192.168.255.255
denied-peer-ip=127.0.0.0-127.255.255.255

# 日志
log-file=/var/log/coturn/turn.log
verbose

# 限速（防滥用）
total-quota=100
user-quota=10

# DDoS 防护
no-stale-nonce
```

### Step 5 · 防火墙
```bash
# 阿里云安全组 / 腾讯云安全组：放通以下端口
# - TCP 3478 (STUN/TURN)
# - UDP 3478
# - TCP 5349 (TURN over TLS, 推荐)
# - UDP 5349
# - UDP 49152-49200 (媒体流)

# 系统层防火墙
ufw allow 3478/tcp
ufw allow 3478/udp
ufw allow 5349/tcp
ufw allow 5349/udp
ufw allow 49152:49200/udp
```

### Step 6 · 启动
```bash
cd /opt/coturn
docker compose up -d
docker compose logs -f coturn
# 观察是否成功 listen 和拿到 external-ip
```

### Step 7 · 前端配置（VITE 环境变量）
```bash
# anxinbao-pwa/.env.production
VITE_TURN_URL=turn:turn.your-domain.com:3478
VITE_TURN_USERNAME=anxinbao
VITE_TURN_CREDENTIAL=CHANGE_ME_LONG_RANDOM_PASSWORD
```

### Step 8 · 验证连通性
```bash
# 在浏览器开发工具 console 执行
const pc = new RTCPeerConnection({
  iceServers: [{
    urls: 'turn:turn.your-domain.com:3478',
    username: 'anxinbao',
    credential: 'YOUR_PASSWORD',
  }]
});
pc.createDataChannel('test');
pc.createOffer().then(o => pc.setLocalDescription(o));
pc.onicecandidate = e => e.candidate && console.log(e.candidate.candidate);
// 应看到 typ relay 候选 → TURN 工作正常
```

---

## 三、生产推荐：动态 secret（防密码泄漏）

### 改 turnserver.conf
```conf
# 注释掉静态 user 行
# user=anxinbao:xxx

# 启用动态密钥
use-auth-secret
static-auth-secret=GENERATE_64_CHAR_RANDOM_HEX_HERE
```

### 后端发临时凭据
```python
# anxinbao-server/app/api/turn.py（新建）
import time
import hmac
import base64
from hashlib import sha1

TURN_SECRET = "GENERATE_64_CHAR_RANDOM_HEX_HERE"  # 与 coturn 一致
TURN_TTL = 3600  # 1 小时

def generate_turn_credential(user_id: str):
    timestamp = int(time.time()) + TURN_TTL
    username = f"{timestamp}:{user_id}"
    digest = hmac.new(
        TURN_SECRET.encode(),
        username.encode(),
        sha1,
    ).digest()
    password = base64.b64encode(digest).decode()
    return {"username": username, "credential": password, "ttl": TURN_TTL}
```

前端在每次发起通话前调 `GET /api/turn/credential` 拿临时凭据。

---

## 四、监控与告警

### 关键指标
- 在线连接数：`docker exec coturn turnadmin -L`
- 带宽用量：`vnstat -i eth0`
- 失败率：解析 `/var/log/coturn/turn.log` 中的 401/438

### Prometheus exporter
```yaml
# 加到 docker-compose.yml
  coturn-exporter:
    image: prom/coturn-exporter
    network_mode: host
    command:
      - --turnstats=anxinbao:CHANGE_ME_LONG_RANDOM_PASSWORD@127.0.0.1:5766
```

### 告警阈值
- 在线连接数 > 80 → ⚠️ 接近 quota，扩容
- 带宽 > 80% 上限 → ⚠️ 升级带宽
- 单 IP 失败率 > 50% → 🚨 可能被攻击

---

## 五、成本估算

| 用户数 | 推荐配置 | 月成本 |
|---|---|---|
| 0-1000 | 1 核 1G + 5 Mbps | ¥40-80 |
| 1000-5000 | 2 核 4G + 20 Mbps | ¥200-400 |
| 5000-20000 | 4 核 8G + 50 Mbps | ¥600-1200 |
| 20000+ | 多节点 + LB | ¥3000+ 考虑迁云 RTC |

---

## 六、与 anxinbao-server/main.py 集成清单

- [x] [VIDEO_CALL_SETUP.md](../../anxinbao-server/docs/VIDEO_CALL_SETUP.md) 已存在（r3）
- [ ] anxinbao-server/app/api/turn.py 新建（动态凭据，生产推荐）
- [ ] anxinbao-pwa/.env.production 设 VITE_TURN_URL
- [ ] [VideoCallPage.tsx](../../anxinbao-pwa/src/pages/VideoCallPage.tsx) 已支持 ICE env 化（r3）
- [ ] CI 加 TURN 健康监测（curl https://turn.your-domain.com:5349 / 3478 测可达性）

---

## 七、紧急回滚

如 coturn 故障：
```bash
docker compose down
# 临时切回 STUN-only 模式
# 前端从 .env 删 VITE_TURN_URL → fallback 到 stun.l.google.com
```

70% NAT 场景会失败，但服务不会崩。修好 coturn 后重启 docker compose 即恢复。

---

> 配套阅读 → [VIDEO_CALL_SETUP.md](../../anxinbao-server/docs/VIDEO_CALL_SETUP.md)
