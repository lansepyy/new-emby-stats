# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/ ./

# Build frontend
RUN npm run build

# Stage 2: Production
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（Playwright需要）
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libappindicator3-1 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# 安装依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright浏览器（仅Chromium）
RUN playwright install chromium --with-deps || echo "Playwright install failed, will use fallback"

# 复制后端代码
COPY backend/ .

# 复制构建好的前端代码
COPY --from=frontend-builder /app/frontend/dist /app/frontend

# 创建数据目录（用于存储webhook配置）
RUN mkdir -p /data && chmod 777 /data

# 暴露端口
EXPOSE 8000

# 启动
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
