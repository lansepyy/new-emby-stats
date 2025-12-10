#!/bin/bash
# Docker 镜像构建与集成测试脚本
# 自动化完成 Docker 镜像构建、容器启动、测试和清理

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# 配置
IMAGE_NAME="emby-stats-beta"
CONTAINER_NAME="emby-stats-test"
PORT="8899"
TEST_TIMEOUT=120

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BOLD}================================================================================${NC}"
    echo -e "${BOLD}$1${NC}"
    echo -e "${BOLD}================================================================================${NC}"
}

# 清理函数
cleanup() {
    log_info "Cleaning up test environment..."
    
    # 停止并删除测试容器
    if docker ps -a | grep -q $CONTAINER_NAME; then
        log_info "Stopping container: $CONTAINER_NAME"
        docker stop $CONTAINER_NAME 2>/dev/null || true
        docker rm $CONTAINER_NAME 2>/dev/null || true
        log_success "Container removed"
    fi
    
    # 可选：删除测试镜像（取消注释以启用）
    # if docker images | grep -q $IMAGE_NAME; then
    #     log_info "Removing image: $IMAGE_NAME"
    #     docker rmi $IMAGE_NAME 2>/dev/null || true
    # fi
}

# 检查 Docker 是否运行
check_docker() {
    log_section "1. 检查 Docker 环境"
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Docker is ready"
    docker --version
}

# 构建 Docker 镜像
build_image() {
    log_section "2. 构建 Docker 镜像"
    
    log_info "Building image: $IMAGE_NAME"
    log_info "This may take a few minutes..."
    
    if docker build -t $IMAGE_NAME . ; then
        log_success "Docker image built successfully"
        
        # 显示镜像信息
        log_info "Image details:"
        docker images $IMAGE_NAME
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# 启动容器
start_container() {
    log_section "3. 启动 Docker 容器"
    
    # 清理可能存在的旧容器
    if docker ps -a | grep -q $CONTAINER_NAME; then
        log_warning "Removing existing container: $CONTAINER_NAME"
        docker stop $CONTAINER_NAME 2>/dev/null || true
        docker rm $CONTAINER_NAME 2>/dev/null || true
    fi
    
    log_info "Starting container: $CONTAINER_NAME"
    log_info "Port mapping: $PORT:8000"
    
    # 创建测试用的临时目录
    TEST_CONFIG_DIR=$(mktemp -d)
    TEST_DATA_DIR=$(mktemp -d)
    
    log_info "Test config directory: $TEST_CONFIG_DIR"
    log_info "Test data directory: $TEST_DATA_DIR"
    
    # 创建测试用的数据库文件（空文件，仅用于测试容器启动）
    touch "$TEST_DATA_DIR/playback_reporting.db"
    touch "$TEST_DATA_DIR/users.db"
    touch "$TEST_DATA_DIR/authentication.db"
    
    # 启动容器
    docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:8000 \
        -v "$TEST_CONFIG_DIR:/config" \
        -v "$TEST_DATA_DIR:/data:ro" \
        -e TZ=Asia/Shanghai \
        -e PLAYBACK_DB=/data/playback_reporting.db \
        -e USERS_DB=/data/users.db \
        -e AUTH_DB=/data/authentication.db \
        -e EMBY_URL=http://localhost:8096 \
        -e EMBY_API_KEY=test_api_key \
        $IMAGE_NAME
    
    if [ $? -eq 0 ]; then
        log_success "Container started successfully"
        
        # 保存目录路径供后续清理
        echo "$TEST_CONFIG_DIR" > /tmp/emby-stats-test-config-dir
        echo "$TEST_DATA_DIR" > /tmp/emby-stats-test-data-dir
    else
        log_error "Failed to start container"
        rm -rf "$TEST_CONFIG_DIR" "$TEST_DATA_DIR"
        exit 1
    fi
}

# 检查容器状态
check_container() {
    log_section "4. 检查容器状态"
    
    log_info "Waiting for container to be ready..."
    sleep 5
    
    # 检查容器是否运行
    if docker ps | grep -q $CONTAINER_NAME; then
        log_success "Container is running"
        
        # 显示容器信息
        log_info "Container details:"
        docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        log_error "Container is not running"
        log_info "Container logs:"
        docker logs $CONTAINER_NAME
        exit 1
    fi
    
    # 检查日志
    log_info "Recent container logs:"
    docker logs --tail 20 $CONTAINER_NAME
}

# 运行集成测试
run_tests() {
    log_section "5. 运行集成测试"
    
    # 检查 Python 是否可用
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # 安装测试依赖
    log_info "Installing test dependencies..."
    pip3 install requests -q 2>/dev/null || log_warning "Failed to install requests, assuming it's already installed"
    
    # 运行测试脚本
    log_info "Running integration tests..."
    log_info "Test URL: http://localhost:$PORT"
    
    if python3 integration_test.py --url "http://localhost:$PORT" --timeout $TEST_TIMEOUT; then
        log_success "All tests passed!"
        return 0
    else
        log_error "Some tests failed"
        return 1
    fi
}

# 查看测试报告
show_report() {
    log_section "6. 测试报告"
    
    if [ -f "integration_test_report.json" ]; then
        log_info "Test report generated:"
        cat integration_test_report.json | python3 -m json.tool 2>/dev/null || cat integration_test_report.json
    else
        log_warning "No test report found"
    fi
}

# 检查容器日志
check_logs() {
    log_section "7. 容器日志检查"
    
    log_info "Checking for errors in container logs..."
    
    # 获取完整日志
    LOGS=$(docker logs $CONTAINER_NAME 2>&1)
    
    # 检查是否有错误
    if echo "$LOGS" | grep -i "error" | grep -v "0 errors" > /dev/null; then
        log_warning "Found errors in logs:"
        echo "$LOGS" | grep -i "error" | head -10
    else
        log_success "No critical errors found in logs"
    fi
    
    # 保存完整日志
    LOG_FILE="docker_container_logs.txt"
    docker logs $CONTAINER_NAME > $LOG_FILE 2>&1
    log_info "Full logs saved to: $LOG_FILE"
}

# 停止容器并清理
stop_and_cleanup() {
    log_section "8. 清理测试环境"
    
    log_info "Stopping container..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    
    log_info "Removing container..."
    docker rm $CONTAINER_NAME 2>/dev/null || true
    
    # 清理临时目录
    if [ -f /tmp/emby-stats-test-config-dir ]; then
        TEST_CONFIG_DIR=$(cat /tmp/emby-stats-test-config-dir)
        rm -rf "$TEST_CONFIG_DIR"
        rm /tmp/emby-stats-test-config-dir
        log_info "Cleaned up config directory: $TEST_CONFIG_DIR"
    fi
    
    if [ -f /tmp/emby-stats-test-data-dir ]; then
        TEST_DATA_DIR=$(cat /tmp/emby-stats-test-data-dir)
        rm -rf "$TEST_DATA_DIR"
        rm /tmp/emby-stats-test-data-dir
        log_info "Cleaned up data directory: $TEST_DATA_DIR"
    fi
    
    log_success "Cleanup complete"
}

# 主函数
main() {
    log_section "Emby Stats Beta - Docker 集成测试"
    
    echo "This script will:"
    echo "  1. Check Docker environment"
    echo "  2. Build Docker image"
    echo "  3. Start container"
    echo "  4. Check container status"
    echo "  5. Run integration tests"
    echo "  6. Show test report"
    echo "  7. Check container logs"
    echo "  8. Cleanup"
    echo ""
    
    # 注册清理函数
    trap cleanup EXIT
    
    # 执行测试流程
    check_docker
    build_image
    start_container
    check_container
    
    # 运行测试（捕获退出码）
    set +e  # 临时禁用错误退出
    run_tests
    TEST_RESULT=$?
    set -e  # 重新启用错误退出
    
    show_report
    check_logs
    stop_and_cleanup
    
    # 最终结果
    log_section "测试完成"
    
    if [ $TEST_RESULT -eq 0 ]; then
        log_success "✓ All integration tests passed!"
        log_info "Docker image: $IMAGE_NAME is ready for deployment"
        exit 0
    else
        log_error "✗ Some tests failed. Please check the logs above."
        exit 1
    fi
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-build)
            SKIP_BUILD=true
            shift
            ;;
        --keep-container)
            KEEP_CONTAINER=true
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-build         Skip Docker image build"
            echo "  --keep-container   Keep container running after tests"
            echo "  --port PORT        Use custom port (default: 8899)"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# 修改清理函数以支持保持容器
if [ "$KEEP_CONTAINER" = true ]; then
    cleanup() {
        log_info "Skipping cleanup (--keep-container flag set)"
    }
fi

# 如果设置了跳过构建，修改主函数
if [ "$SKIP_BUILD" = true ]; then
    build_image() {
        log_section "2. 跳过镜像构建 (--no-build)"
        log_warning "Using existing image: $IMAGE_NAME"
    }
fi

# 运行主函数
main
