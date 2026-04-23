# 安心宝部署指南

## 目录
1. [环境要求](#环境要求)
2. [本地开发部署](#本地开发部署)
3. [Docker部署](#docker部署)
4. [生产环境部署](#生产环境部署)
5. [配置说明](#配置说明)
6. [常见问题](#常见问题)

---

## 环境要求

### 后端
- Python 3.10+
- PostgreSQL 14+ (生产环境) 或 SQLite (开发环境)
- Redis 7+ (可选，用于缓存)

### 前端
- Node.js 18+
- npm 9+ 或 pnpm 8+

---

## 本地开发部署

### 1. 克隆代码
```bash
git clone https://github.com/your-repo/anxinbao-server.git
cd anxinbao-server
```

### 2. 后端部署

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要参数

# 初始化数据库
alembic upgrade head

# 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端部署

```bash
cd web-app

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端访问地址: http://localhost:5173
后端API地址: http://localhost:8000
API文档: http://localhost:8000/docs

---

## Docker部署

### 使用Docker Compose (推荐)

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 单独构建镜像

```bash
# 构建后端镜像
docker build -t anxinbao-server .

# 运行后端容器
docker run -d \
  --name anxinbao-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/anxinbao \
  anxinbao-server
```

---

## 生产环境部署

### 1. 服务器准备

推荐配置:
- CPU: 4核+
- 内存: 8GB+
- 存储: 100GB SSD
- 系统: Ubuntu 22.04 LTS

### 2. 安装依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo apt install docker-compose-plugin

# 安装Nginx
sudo apt install nginx -y
```

### 3. 配置Nginx反向代理

```nginx
# /etc/nginx/sites-available/anxinbao
server {
    listen 80;
    server_name api.anxinbao.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket支持
    location /api/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}

server {
    listen 80;
    server_name anxinbao.com www.anxinbao.com;

    root /var/www/anxinbao/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 4. 配置SSL证书

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d anxinbao.com -d www.anxinbao.com -d api.anxinbao.com
```

### 5. 部署应用

```bash
# 创建部署目录
sudo mkdir -p /opt/anxinbao
cd /opt/anxinbao

# 克隆代码
git clone https://github.com/your-repo/anxinbao-server.git .

# 配置环境变量
cp .env.example .env
sudo nano .env  # 编辑配置

# 启动服务
docker-compose -f docker-compose.prod.yml up -d
```

### 6. 构建前端

```bash
cd web-app
npm install
npm run build

# 复制到Nginx目录
sudo cp -r dist/* /var/www/anxinbao/
```

---

## 配置说明

### 环境变量 (.env)

```env
# 应用配置
APP_NAME=anxinbao
DEBUG=false
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/anxinbao

# Redis配置（可选）
REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI服务配置
DASHSCOPE_API_KEY=your-dashscope-api-key

# CORS配置
ALLOWED_ORIGINS=https://anxinbao.com,https://www.anxinbao.com

# 文件存储
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760

# 日志级别
LOG_LEVEL=INFO
```

### 生产环境检查清单

- [ ] 修改JWT_SECRET_KEY为随机强密钥
- [ ] 配置正确的DATABASE_URL
- [ ] 设置DEBUG=false
- [ ] 配置ALLOWED_ORIGINS为实际域名
- [ ] 启用HTTPS
- [ ] 配置日志文件轮转
- [ ] 设置防火墙规则
- [ ] 配置数据库备份

---

## 监控和维护

### 健康检查

```bash
# API健康检查
curl http://localhost:8000/health

# 详细健康状态
curl http://localhost:8000/health/detailed
```

### 日志查看

```bash
# Docker日志
docker-compose logs -f api

# 应用日志
tail -f /var/log/anxinbao/app.log
```

### 数据库备份

```bash
# PostgreSQL备份
pg_dump -h localhost -U anxinbao anxinbao > backup_$(date +%Y%m%d).sql

# 恢复
psql -h localhost -U anxinbao anxinbao < backup_20240112.sql
```

### 性能监控

访问 http://localhost:8000/metrics 查看Prometheus指标

---

## 常见问题

### Q: 数据库连接失败
A: 检查DATABASE_URL配置，确保数据库服务已启动

### Q: WebSocket连接断开
A: 检查Nginx配置中的proxy_read_timeout，建议设置为86400

### Q: 静态文件404
A: 确保前端构建文件已正确复制到Nginx配置的root目录

### Q: 内存占用过高
A: 检查是否有内存泄漏，考虑增加服务器内存或优化代码

---

## 技术支持

如遇问题，请通过以下方式获取帮助:
- GitHub Issues: https://github.com/your-repo/anxinbao-server/issues
- 邮箱: support@anxinbao.com
