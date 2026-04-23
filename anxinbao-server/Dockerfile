# ============================================================
# 安心宝云端服务 Dockerfile
# 多阶段构建，优化镜像体积和安全性
# ============================================================

# ============ 第一阶段：构建依赖 ============
FROM python:3.12-slim AS builder

WORKDIR /build

# 安装编译所需的系统依赖（构建完成后不会保留在最终镜像中）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境，避免与系统 Python 冲突
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 先复制依赖清单，利用 Docker 缓存层（依赖不变时跳过安装）
COPY requirements.txt .

# 仅安装生产依赖（排除测试/开发工具以减小体积）
# 使用 --no-cache-dir 避免 pip 缓存占用空间
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============ 第二阶段：生产运行环境 ============
FROM python:3.12-slim AS runner

# 镜像元数据
LABEL maintainer="安心宝技术团队 <support@anxinbao.com>"
LABEL description="安心宝智能养老平台后端服务"
LABEL version="1.0.0"

WORKDIR /app

# 安装运行时所需的最小系统依赖
# - libpq5: PostgreSQL 客户端库（asyncpg/psycopg2 运行时需要）
# - curl: 用于容器健康检查
# - tini: 轻量级 init 进程，正确处理信号转发和僵尸进程回收
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash --uid 1000 appuser

# 从构建阶段复制已安装好的 Python 虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 设置 Python 运行时优化
# - PYTHONDONTWRITEBYTECODE: 不生成 .pyc 文件（容器中不需要）
# - PYTHONUNBUFFERED: 禁用输出缓冲，确保日志即时输出
# - PYTHONFAULTHANDLER: 遇到段错误时打印回溯信息
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# 复制应用代码（.dockerignore 排除了不必要的文件）
COPY --chown=appuser:appuser . .

# 创建应用所需的目录并设置权限
RUN mkdir -p /app/static /app/templates /app/logs /app/uploads && \
    chown -R appuser:appuser /app

# 切换到非 root 用户运行（安全最佳实践）
USER appuser

# 暴露服务端口
EXPOSE 8000

# 健康检查：使用 curl 探测 /health 端点
# - interval: 每30秒检查一次
# - timeout: 单次检查超时10秒
# - start-period: 启动后等待15秒再开始检查（给应用初始化时间）
# - retries: 连续失败3次标记为不健康
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 使用 tini 作为 PID 1 进程，确保信号正确传递给 uvicorn
ENTRYPOINT ["tini", "--"]

# 启动命令：
# - workers: 根据 CPU 核心数设置工作进程（可通过 WEB_CONCURRENCY 环境变量覆盖）
# - access-log: 启用访问日志
# - proxy-headers: 信任反向代理传递的 X-Forwarded-* 头
# - forwarded-allow-ips: 允许所有内网 IP 传递代理头（Docker 网络需要）
CMD ["uvicorn", "main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--workers", "2", \
    "--access-log", \
    "--proxy-headers", \
    "--forwarded-allow-ips", "*"]
