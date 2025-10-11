#!/bin/bash
# Docker工具脚本 - 管理DistribuTown容器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检测Docker Compose命令
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    print_error "Docker Compose未安装"
    exit 1
fi

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "DistribuTown Docker 管理工具"
    echo ""
    echo "用法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  build                    - 构建所有Docker镜像"
    echo "  build-dev                - 构建开发环境镜像"
    echo "  start                    - 启动所有服务"
    echo "  start-grpc               - 只启动gRPC服务"
    echo "  start-rest               - 只启动REST服务"
    echo "  stop                     - 停止所有服务"
    echo "  restart                  - 重启所有服务"
    echo "  status                   - 查看服务状态"
    echo "  logs [service]           - 查看日志"
    echo "  logs-follow [service]    - 实时查看日志"
    echo "  shell [service]          - 进入容器shell"
    echo "  cli-grpc <port>           - 启动gRPC CLI"
    echo "  cli-rest <port>           - 启动REST CLI"
    echo "  ai-grpc <port>            - 启动gRPC AI代理"
    echo "  ai-rest <port>            - 启动REST AI代理"
    echo "  dev                      - 启动开发环境"
    echo "  clean                    - 清理Docker资源"
    echo "  test                     - 运行测试"
    echo "  help                     - 显示此帮助"
}

# 构建所有镜像
build_all() {
    print_info "构建所有Docker镜像..."
    cd "$(dirname "$0")"
    ./build.sh
    print_success "所有镜像构建完成"
}

# 构建开发环境镜像
build_dev() {
    print_info "构建开发环境镜像..."
    cd "$(dirname "$0")"
    docker build -f Dockerfile.dev -t distribu-town-dev:latest ..
    print_success "开发环境镜像构建完成"
}

# 启动所有服务
start_all() {
    print_info "启动所有服务..."
    cd "$(dirname "$0")"
    $COMPOSE_CMD up -d
    print_success "所有服务已启动"
    show_status
}

# 启动gRPC服务
start_grpc() {
    print_info "启动gRPC服务..."
    cd "$(dirname "$0")"
    $COMPOSE_CMD up -d grpc-services grpc-villager-1 grpc-villager-2
    print_success "gRPC服务已启动"
}

# 启动REST服务
start_rest() {
    print_info "启动REST服务..."
    cd "$(dirname "$0")"
    $COMPOSE_CMD up -d rest-services rest-villager-1 rest-villager-2
    print_success "REST服务已启动"
}

# 停止所有服务
stop_all() {
    print_info "停止所有服务..."
    cd "$(dirname "$0")"
    $COMPOSE_CMD down
    print_success "所有服务已停止"
}

# 重启所有服务
restart_all() {
    print_info "重启所有服务..."
    stop_all
    sleep 2
    start_all
}

# 查看服务状态
show_status() {
    print_info "服务状态:"
    cd "$(dirname "$0")"
    $COMPOSE_CMD ps
    echo ""
    print_info "网络状态:"
    docker network ls | grep distribu-town
}

# 查看日志
show_logs() {
    local service=$1
    cd "$(dirname "$0")"
    
    if [ -z "$service" ]; then
        print_info "所有服务日志:"
        $COMPOSE_CMD logs --tail=50
    else
        print_info "服务 $service 日志:"
        $COMPOSE_CMD logs --tail=50 "$service"
    fi
}

# 实时查看日志
follow_logs() {
    local service=$1
    cd "$(dirname "$0")"
    
    if [ -z "$service" ]; then
        print_info "实时查看所有服务日志 (Ctrl+C退出):"
        $COMPOSE_CMD logs -f
    else
        print_info "实时查看服务 $service 日志 (Ctrl+C退出):"
        $COMPOSE_CMD logs -f "$service"
    fi
}

# 进入容器shell
enter_shell() {
    local service=$1
    cd "$(dirname "$0")"
    
    if [ -z "$service" ]; then
        print_error "请指定服务名称"
        echo "可用服务: grpc-services, grpc-villager-1, grpc-villager-2, rest-services, rest-villager-1, rest-villager-2"
        exit 1
    fi
    
    print_info "进入服务 $service 的shell..."
    $COMPOSE_CMD exec "$service" bash
}

# 启动CLI
start_cli() {
    local arch=$1
    local port=$2
    
    if [ -z "$port" ]; then
        print_error "请指定端口号"
        echo "示例: $0 cli-grpc 50053"
        echo "示例: $0 cli-rest 5002"
        exit 1
    fi
    
    cd "$(dirname "$0")"
    
    if [ "$arch" = "grpc" ]; then
        print_info "启动gRPC CLI (端口 $port)..."
        docker run -it --rm \
            --network docker_distribu-town-grpc \
            distribu-town-grpc-villager:latest \
            --cli --port "$port"
    elif [ "$arch" = "rest" ]; then
        print_info "启动REST CLI (端口 $port)..."
        docker run -it --rm \
            --network docker_distribu-town-rest \
            distribu-town-rest-villager:latest \
            --cli --port "$port"
    fi
}

# 启动AI代理
start_ai() {
    local arch=$1
    local port=$2
    
    if [ -z "$port" ]; then
        print_error "请指定端口号"
        echo "示例: $0 ai-grpc 50053"
        echo "示例: $0 ai-rest 5002"
        exit 1
    fi
    
    cd "$(dirname "$0")"
    
    if [ "$arch" = "grpc" ]; then
        print_info "启动gRPC AI代理 (端口 $port)..."
        docker run -it --rm \
            --network docker_distribu-town-grpc \
            distribu-town-grpc-villager:latest \
            --ai --port "$port"
    elif [ "$arch" = "rest" ]; then
        print_info "启动REST AI代理 (端口 $port)..."
        docker run -it --rm \
            --network docker_distribu-town-rest \
            distribu-town-rest-villager:latest \
            --ai --port "$port"
    fi
}

# 启动开发环境
start_dev() {
    print_info "启动开发环境..."
    cd "$(dirname "$0")"
    
    # 检查开发镜像是否存在
    if ! docker image inspect distribu-town-dev:latest >/dev/null 2>&1; then
        print_warning "开发镜像不存在，正在构建..."
        build_dev
    fi
    
    print_info "启动开发环境容器..."
    docker run -it --rm \
        -p 5000-50099:5000-50099 \
        -v "$(pwd)/..:/app" \
        distribu-town-dev:latest
}

# 清理Docker资源
clean_docker() {
    print_warning "清理Docker资源..."
    
    # 停止所有相关容器
    $COMPOSE_CMD -f "$(dirname "$0")/docker-compose.yml" down 2>/dev/null || true
    
    # 删除相关镜像
    docker images | grep distribu-town | awk '{print $3}' | xargs -r docker rmi -f
    
    # 清理未使用的资源
    docker system prune -f
    
    print_success "Docker资源清理完成"
}

# 运行测试
run_tests() {
    print_info "运行测试..."
    cd "$(dirname "$0")"
    
    # 启动服务
    $COMPOSE_CMD up -d
    
    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10
    
    # 运行测试
    print_info "运行性能测试..."
    docker run --rm \
        --network docker_distribu-town-rest \
        -v "$(pwd)/../performance_tests:/app" \
        python:3.11-slim \
        bash -c "cd /app && pip install requests && python benchmark.py --requests 10"
    
    print_success "测试完成"
}

# 主函数
main() {
    case "$1" in
        "build")
            build_all
            ;;
        "build-dev")
            build_dev
            ;;
        "start")
            start_all
            ;;
        "start-grpc")
            start_grpc
            ;;
        "start-rest")
            start_rest
            ;;
        "stop")
            stop_all
            ;;
        "restart")
            restart_all
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "logs-follow")
            follow_logs "$2"
            ;;
        "shell")
            enter_shell "$2"
            ;;
        "cli-grpc")
            start_cli "grpc" "$2"
            ;;
        "cli-rest")
            start_cli "rest" "$2"
            ;;
        "ai-grpc")
            start_ai "grpc" "$2"
            ;;
        "ai-rest")
            start_ai "rest" "$2"
            ;;
        "dev")
            start_dev
            ;;
        "clean")
            clean_docker
            ;;
        "test")
            run_tests
            ;;
        "help"|"-h"|"--help"|"")
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
