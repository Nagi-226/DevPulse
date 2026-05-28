# DevPulse Backend — 多阶段 Docker 构建
# 基于 Python 3.11-slim，最终镜像约 200MB

# ── Stage 1: 依赖安装 ────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# 安装系统依赖（Playwright 浏览器需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements-docker.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-docker.txt

# 安装 Playwright 浏览器（仅 Chromium，减少镜像体积）
RUN python -m playwright install chromium --with-deps || true

# ── Stage 2: 生产运行镜像 ────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制 Python 包 + Playwright 浏览器
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# 复制应用代码
COPY devpulse/ ./devpulse/
COPY alembic.ini ./
COPY migrations/ ./migrations/

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash devpulse && \
    chown -R devpulse:devpulse /app
USER devpulse

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "devpulse.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
