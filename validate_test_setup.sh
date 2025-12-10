#!/bin/bash
# 验证测试环境设置是否正确

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "测试环境验证"
echo "======================================"
echo ""

# 检查文件是否存在
echo "1. 检查测试文件..."
FILES=(
    "integration_test.py"
    "docker-integration-test.sh"
    "INTEGRATION_TESTING.md"
    "TESTING_QUICKSTART.md"
    "DOCKER_TESTING_SUMMARY.md"
)

ALL_EXISTS=true
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (缺失)"
        ALL_EXISTS=false
    fi
done

echo ""

# 检查执行权限
echo "2. 检查执行权限..."
if [ -x "integration_test.py" ]; then
    echo -e "${GREEN}✓${NC} integration_test.py 可执行"
else
    echo -e "${YELLOW}!${NC} integration_test.py 无执行权限 (运行: chmod +x integration_test.py)"
fi

if [ -x "docker-integration-test.sh" ]; then
    echo -e "${GREEN}✓${NC} docker-integration-test.sh 可执行"
else
    echo -e "${YELLOW}!${NC} docker-integration-test.sh 无执行权限 (运行: chmod +x docker-integration-test.sh)"
fi

echo ""

# 检查 Python 语法
echo "3. 检查 Python 脚本语法..."
if python3 -m py_compile integration_test.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} integration_test.py 语法正确"
else
    echo -e "${RED}✗${NC} integration_test.py 语法错误"
    ALL_EXISTS=false
fi

echo ""

# 检查 Bash 语法
echo "4. 检查 Bash 脚本语法..."
if bash -n docker-integration-test.sh 2>/dev/null; then
    echo -e "${GREEN}✓${NC} docker-integration-test.sh 语法正确"
else
    echo -e "${RED}✗${NC} docker-integration-test.sh 语法错误"
    ALL_EXISTS=false
fi

echo ""

# 检查依赖
echo "5. 检查依赖..."

if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker 已安装: $(docker --version)"
else
    echo -e "${RED}✗${NC} Docker 未安装"
    ALL_EXISTS=false
fi

if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} Python 3 已安装: $(python3 --version)"
else
    echo -e "${RED}✗${NC} Python 3 未安装"
    ALL_EXISTS=false
fi

if python3 -c "import requests" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} requests 库已安装"
else
    echo -e "${YELLOW}!${NC} requests 库未安装 (运行: pip install requests)"
fi

echo ""

# 检查 Dockerfile 和 docker-compose
echo "6. 检查 Docker 配置文件..."
if [ -f "Dockerfile" ]; then
    echo -e "${GREEN}✓${NC} Dockerfile 存在"
else
    echo -e "${RED}✗${NC} Dockerfile 缺失"
    ALL_EXISTS=false
fi

if [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}✓${NC} docker-compose.yml 存在"
else
    echo -e "${YELLOW}!${NC} docker-compose.yml 缺失 (可选)"
fi

echo ""

# 检查 .gitignore
echo "7. 检查 .gitignore..."
if grep -q "integration_test_report.json" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✓${NC} 测试报告已添加到 .gitignore"
else
    echo -e "${YELLOW}!${NC} 测试报告未在 .gitignore 中"
fi

if grep -q "docker_container_logs.txt" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✓${NC} 容器日志已添加到 .gitignore"
else
    echo -e "${YELLOW}!${NC} 容器日志未在 .gitignore 中"
fi

echo ""
echo "======================================"

if [ "$ALL_EXISTS" = true ]; then
    echo -e "${GREEN}✓ 验证通过！测试环境设置正确${NC}"
    echo ""
    echo "运行测试："
    echo "  ./docker-integration-test.sh"
    exit 0
else
    echo -e "${RED}✗ 验证失败！请修复上述问题${NC}"
    exit 1
fi
