# 安心宝云端服务 - 部署指南

## 概述

本文档详细说明如何在各种环境中部署安心宝云端服务，包括本地开发、Docker部署、Kubernetes部署等。

## 目录

1. [环境要求](#环境要求)
2. [本地开发部署](#本地开发部署)
3. [Docker部署](#docker部署)
4. [生产环境部署](#生产环境部署)
5. [Kubernetes部署](#kubernetes部署)
6. [配置说明](#配置说明)
7. [监控配置](#监控配置)
8. [常见问题](#常见问题)

---

## 环境要求

### 最低配置

| 组件 | 要求 |
|------|------|
| CPU | 2核心 |
| 内存 | 4GB |
| 存储 | 20GB SSD |
| 操作系统 | Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+ |

### 推荐配置（生产）

| 组件 | 要求 |
|------|------|
| CPU | 4核心+ |
| 内存 | 8GB+ |
| 存储 | 100GB SSD |
| 网络 | 100Mbps+ |

### 软件依赖

- Python 3.11+
- PostgreSQL 15+ (生产)
- Redis 7+ (可选，推荐)
- Docker 24+ / Docker Compose 2.x (容器化部署)
- Nginx 1.24+ (反向代理)

---

## 本地开发部署

### 1. 克隆项目

```bash
git clone https://github.com/your-org/anxinbao-server.git
cd anxinbao-server
```

### 2. 创建虚拟环境

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，至少配置以下必需项：

```env
# 必需配置
DASHSCOPE_API_KEY=sk-your-api-key
XFYUN_APPID=your-appid
XFYUN_API_KEY=your-api-key
XFYUN_API_SECRET=your-api-secret

# 数据库（开发环境使用SQLite）
DATABASE_URL=sqlite:///./anxinbao.db

# 调试模式
DEBUG=true
```

### 5. 初始化数据库

```bash
# 数据库表会在首次启动时自动创建
python -c "from app.models.database import init_db; init_db()"
```

### 6. 启动服务

```bash
# 开发模式（热重载）
python main.py

# 或使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# API文档
open http://localhost:8000/docs
```

---

## Docker部署

### 快速启动

```bash
# 仅启动API服务（开发用）
docker-compose up -d api

# 启动完整服务（API + PostgreSQL + Redis）
docker-compose up -d
```

### 自定义构建

```bash
# 构建镜像
docker build -t anxinbao-server:latest .

# 运行容器
docker run -d \
  --name anxinbao-api \
  -p 8000:8000 \
  -e DASHSCOPE_API_KEY=sk-xxx \
  -e DATABASE_URL=sqlite:///./data/anxinbao.db \
  -v $(pwd)/data:/app/data \
  anxinbao-server:latest
```

### Docker Compose 配置详解

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://anxinbao:password@postgres:5432/anxinbao
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: anxinbao
      POSTGRES_PASSWORD: password
      POSTGRES_DB: anxinbao
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U anxinbao"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

---

## 生产环境部署

### 架构概览

```
                    ┌─────────────────┐
                    │   负载均衡器     │
                    │  (Nginx/ALB)    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
        │  API-1    │  │  API-2    │  │  API-N    │
        │ Container │  │ Container │  │ Container │
        └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
  ┌─────▼─────┐        ┌─────▼─────┐        ┌─────▼─────┐
  │PostgreSQL │        │   Redis   │        │  对象存储  │
  │  主从复制  │        │   集群    │        │   (OSS)   │
  └───────────┘        └───────────┘        └───────────┘
```

### 1. 服务器准备

```bash
# Ubuntu 22.04
sudo apt update
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx

# 启动Docker
sudo systemctl enable docker
sudo systemctl start docker

# 添加当前用户到docker组
sudo usermod -aG docker $USER
```

### 2. SSL证书配置

```bash
# 使用Let's Encrypt获取证书
sudo certbot --nginx -d api.anxinbao.com

# 自动续期
sudo crontab -e
# 添加: 0 0 * * * certbot renew --quiet
```

### 3. Nginx配置

```nginx
# /etc/nginx/sites-available/anxinbao
upstream anxinbao_api {
    least_conn;
    server 127.0.0.1:8001 weight=1;
    server 127.0.0.1:8002 weight=1;
    server 127.0.0.1:8003 weight=1;
    keepalive 32;
}

server {
    listen 80;
    server_name api.anxinbao.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.anxinbao.com;

    ssl_certificate /etc/letsencrypt/live/api.anxinbao.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.anxinbao.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 请求限流
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;
    limit_req zone=api burst=200 nodelay;

    location / {
        proxy_pass http://anxinbao_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket支持
    location /ws {
        proxy_pass http://anxinbao_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态文件
    location /static {
        alias /var/www/anxinbao/static;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # 健康检查（内部访问）
    location /health {
        proxy_pass http://anxinbao_api;
        access_log off;
    }
}
```

### 4. 环境变量配置

创建 `.env.production` 文件：

```env
# 基础配置
DEBUG=false
HOST=0.0.0.0
PORT=8000

# 数据库
DATABASE_URL=postgresql://anxinbao:StrongPassword123!@postgres.internal:5432/anxinbao

# Redis
REDIS_URL=redis://:RedisPassword@redis.internal:6379/0

# JWT安全密钥（至少32位随机字符串）
JWT_SECRET_KEY=your-production-secret-key-at-least-32-characters
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 加密密钥
ENCRYPTION_KEY=your-32-char-encryption-key-here

# AI服务
DASHSCOPE_API_KEY=sk-production-api-key
XFYUN_APPID=production-appid
XFYUN_API_KEY=production-api-key
XFYUN_API_SECRET=production-api-secret

# CORS
ALLOWED_ORIGINS=https://app.anxinbao.com,https://admin.anxinbao.com

# 限流
API_RATE_LIMIT=100/minute

# 日志
LOG_LEVEL=INFO
```

### 5. 启动生产服务

```bash
# 使用生产配置启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 查看日志
docker-compose logs -f api

# 扩容
docker-compose up -d --scale api=3
```

### 6. 数据库迁移

```bash
# 进入API容器
docker exec -it anxinbao-api-1 bash

# 执行数据库初始化
python -c "from app.models.database import init_db; init_db()"
```

---

## Kubernetes部署

### ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: anxinbao-config
data:
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  API_RATE_LIMIT: "100/minute"
```

### Secret

```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: anxinbao-secrets
type: Opaque
stringData:
  DATABASE_URL: postgresql://user:password@postgres:5432/anxinbao
  REDIS_URL: redis://:password@redis:6379/0
  JWT_SECRET_KEY: your-secret-key
  DASHSCOPE_API_KEY: sk-xxx
```

### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anxinbao-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: anxinbao-api
  template:
    metadata:
      labels:
        app: anxinbao-api
    spec:
      containers:
      - name: api
        image: ghcr.io/your-org/anxinbao-server:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: anxinbao-config
        - secretRef:
            name: anxinbao-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: anxinbao-api
spec:
  selector:
    app: anxinbao-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: anxinbao-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.anxinbao.com
    secretName: anxinbao-tls
  rules:
  - host: api.anxinbao.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: anxinbao-api
            port:
              number: 80
```

### HPA (自动扩缩容)

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: anxinbao-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: anxinbao-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 部署命令

```bash
# 应用配置
kubectl apply -f k8s/

# 查看状态
kubectl get pods -l app=anxinbao-api
kubectl get svc anxinbao-api
kubectl get ingress anxinbao-ingress

# 查看日志
kubectl logs -f deployment/anxinbao-api
```

---

## 配置说明

### 环境变量完整列表

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| DEBUG | 否 | false | 调试模式 |
| HOST | 否 | 0.0.0.0 | 监听地址 |
| PORT | 否 | 8000 | 监听端口 |
| DATABASE_URL | 是 | sqlite:///./anxinbao.db | 数据库连接字符串 |
| REDIS_URL | 否 | - | Redis连接字符串 |
| JWT_SECRET_KEY | 是 | - | JWT签名密钥 |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | 否 | 30 | 访问令牌过期时间 |
| JWT_REFRESH_TOKEN_EXPIRE_DAYS | 否 | 7 | 刷新令牌过期时间 |
| ENCRYPTION_KEY | 否 | - | 数据加密密钥 |
| DASHSCOPE_API_KEY | 是 | - | 通义千问API密钥 |
| XFYUN_APPID | 是 | - | 科大讯飞AppID |
| XFYUN_API_KEY | 是 | - | 科大讯飞API Key |
| XFYUN_API_SECRET | 是 | - | 科大讯飞API Secret |
| ALLOWED_ORIGINS | 否 | * | CORS允许的源 |
| API_RATE_LIMIT | 否 | 100/minute | API限流配置 |
| HEALTH_RISK_THRESHOLD | 否 | 7 | 健康风险通知阈值 |
| LOG_LEVEL | 否 | INFO | 日志级别 |

---

## 监控配置

### Prometheus配置

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'anxinbao-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: /metrics
    scrape_interval: 15s
```

### Grafana仪表板

导入仪表板ID: `XXXXX`（待发布）

或使用以下JSON配置关键面板：

```json
{
  "panels": [
    {
      "title": "请求速率",
      "targets": [{
        "expr": "rate(anxinbao_http_requests_total[5m])"
      }]
    },
    {
      "title": "响应延迟",
      "targets": [{
        "expr": "histogram_quantile(0.95, rate(anxinbao_http_request_duration_seconds_bucket[5m]))"
      }]
    },
    {
      "title": "高风险告警",
      "targets": [{
        "expr": "increase(anxinbao_high_risk_alerts_total[1h])"
      }]
    }
  ]
}
```

### 告警规则

```yaml
# alerting-rules.yml
groups:
- name: anxinbao
  rules:
  - alert: HighErrorRate
    expr: rate(anxinbao_http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "高错误率告警"

  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(anxinbao_http_request_duration_seconds_bucket[5m])) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "响应时间过长"

  - alert: HighRiskAlertSpike
    expr: increase(anxinbao_high_risk_alerts_total[1h]) > 10
    for: 0m
    labels:
      severity: warning
    annotations:
      summary: "高风险告警数量异常"
```

---

## 常见问题

### 1. 数据库连接失败

**症状：** `sqlalchemy.exc.OperationalError: could not connect to server`

**解决方案：**
```bash
# 检查数据库服务状态
docker-compose ps postgres

# 检查连接字符串
echo $DATABASE_URL

# 测试连接
docker exec -it postgres psql -U anxinbao -c "SELECT 1"
```

### 2. Redis连接问题

**症状：** `redis.exceptions.ConnectionError`

**解决方案：**
```bash
# 检查Redis服务
docker-compose ps redis

# 测试连接
docker exec -it redis redis-cli ping
```

### 3. API限流触发

**症状：** 返回 `429 Too Many Requests`

**解决方案：**
- 调整 `API_RATE_LIMIT` 配置
- 实现客户端重试和退避策略
- 使用API密钥进行不同限流级别

### 4. SSL证书问题

**症状：** `SSL: CERTIFICATE_VERIFY_FAILED`

**解决方案：**
```bash
# 检查证书有效期
sudo certbot certificates

# 手动续期
sudo certbot renew

# 重新加载Nginx
sudo nginx -s reload
```

### 5. 内存不足

**症状：** 容器被OOM Killer终止

**解决方案：**
- 增加容器内存限制
- 优化Python内存使用
- 配置合适的gunicorn worker数量

```bash
# 调整Docker内存限制
docker update --memory=2g anxinbao-api-1
```

---

## 备份与恢复

### 数据库备份

```bash
# PostgreSQL备份
docker exec postgres pg_dump -U anxinbao anxinbao > backup_$(date +%Y%m%d).sql

# 定时备份（crontab）
0 2 * * * docker exec postgres pg_dump -U anxinbao anxinbao | gzip > /backups/anxinbao_$(date +\%Y\%m\%d).sql.gz
```

### 数据库恢复

```bash
# 恢复数据库
cat backup.sql | docker exec -i postgres psql -U anxinbao anxinbao
```

---

## 更新升级

### 滚动更新

```bash
# 拉取新镜像
docker-compose pull api

# 滚动更新（零停机）
docker-compose up -d --no-deps api
```

### 回滚

```bash
# 查看历史版本
docker images anxinbao-server

# 回滚到指定版本
docker-compose down
docker tag anxinbao-server:backup anxinbao-server:latest
docker-compose up -d
```
