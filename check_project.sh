#!/bin/bash

echo "======================================"
echo "检查 Emby Stats 项目结构"
echo "======================================"

# 检查后端文件
echo -e "\n✓ 检查后端文件..."
backend_files=(
    "backend/config.py"
    "backend/config_storage.py"
    "backend/main.py"
    "backend/requirements.txt"
    "backend/routers/webhook.py"
    "backend/routers/config.py"
    "backend/services/webhook.py"
    "backend/services/tmdb.py"
    "backend/services/notification.py"
)

for file in "${backend_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (缺失)"
    fi
done

# 检查前端文件
echo -e "\n✓ 检查前端文件..."
frontend_files=(
    "frontend/src/pages/Notifications.tsx"
    "frontend/src/pages/NotificationTemplates.tsx"
    "frontend/src/pages/index.ts"
)

for file in "${frontend_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (缺失)"
    fi
done

# 检查Docker文件
echo -e "\n✓ 检查Docker文件..."
if [ -f "Dockerfile" ]; then
    echo "  ✓ Dockerfile"
else
    echo "  ✗ Dockerfile (缺失)"
fi

if [ -f "docker-compose.yml" ]; then
    echo "  ✓ docker-compose.yml"
else
    echo "  ✗ docker-compose.yml (缺失)"
fi

echo -e "\n======================================"
echo "检查 Python 依赖"
echo "======================================"

# 检查requirements.txt
if [ -f "backend/requirements.txt" ]; then
    echo "依赖列表:"
    cat backend/requirements.txt
else
    echo "✗ requirements.txt 缺失"
fi

echo -e "\n======================================"
echo "项目检查完成"
echo "======================================"
