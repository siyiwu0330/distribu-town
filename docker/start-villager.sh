#!/bin/bash
# 启动村民节点

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检测Docker Compose命令
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    print_error "Docker Compose未安装"
    exit 1
fi

# 显示帮助
show_help() {
    echo "启动村民节点"
    echo ""
    echo "用法: $0 <architecture> <port> <node_id> [mode]"
    echo ""
    echo "参数:"
    echo "  architecture  - 架构类型: rest 或 grpc"
    echo "  port          - 村民节点端口"
    echo "  node_id       - 节点ID"
    echo "  mode          - 运行模式: service(默认), cli, ai"
    echo ""
    echo "示例:"
    echo "  $0 rest 5002 node1           # 启动REST村民节点"
    echo "  $0 rest 5002 node1 cli       # 启动REST CLI模式"
    echo "  $0 grpc 50053 node1         # 启动gRPC村民节点"
    echo "  $0 grpc 50053 node1 ai      # 启动gRPC AI模式"
    echo ""
    echo "端口范围:"
    echo "  REST: 5002-50099"
    echo "  gRPC: 50053-50099"
}

# 检查参数
if [ $# -lt 3 ]; then
    show_help
    exit 1
fi

ARCH=$1
PORT=$2
NODE_ID=$3
MODE=${4:-service}

# 验证架构
if [ "$ARCH" != "rest" ] && [ "$ARCH" != "grpc" ]; then
    print_error "无效的架构类型: $ARCH"
    echo "支持的类型: rest, grpc"
    exit 1
fi

# 验证端口
if [ "$ARCH" = "rest" ]; then
    if [ $PORT -lt 5002 ] || [ $PORT -gt 50099 ]; then
        print_error "REST端口必须在5002-50099范围内"
        exit 1
    fi
elif [ "$ARCH" = "grpc" ]; then
    if [ $PORT -lt 50053 ] || [ $PORT -gt 50099 ]; then
        print_error "gRPC端口必须在50053-50099范围内"
        exit 1
    fi
fi

# 验证模式
if [ "$MODE" != "service" ] && [ "$MODE" != "cli" ] && [ "$MODE" != "ai" ]; then
    print_error "无效的运行模式: $MODE"
    echo "支持的模式: service, cli, ai"
    exit 1
fi

print_info "启动${ARCH^^}村民节点..."
echo "  端口: $PORT"
echo "  节点ID: $NODE_ID"
echo "  模式: $MODE"

# 进入docker目录
cd "$(dirname "$0")"

# 检查基础服务是否运行
if [ "$ARCH" = "rest" ]; then
    if ! $COMPOSE_CMD ps rest-services | grep -q "Up"; then
        print_error "REST基础服务未运行"
        echo "请先运行: ./start-rest-services.sh"
        exit 1
    fi
    NETWORK="docker_distribu-town-rest"
    IMAGE="distribu-town-rest-villager:latest"
    COORDINATOR_ADDR="rest-services:5000"
elif [ "$ARCH" = "grpc" ]; then
    if ! $COMPOSE_CMD ps grpc-services | grep -q "Up"; then
        print_error "gRPC基础服务未运行"
        echo "请先运行: ./start-grpc-services.sh"
        exit 1
    fi
    NETWORK="docker_distribu-town-grpc"
    IMAGE="distribu-town-grpc-villager:latest"
    COORDINATOR_ADDR="grpc-services:50051"
fi

# 检查镜像是否存在
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    print_info "构建村民镜像..."
    if [ "$ARCH" = "rest" ]; then
        docker build -f Dockerfile.rest-villager -t "$IMAGE" ..
    else
        docker build -f Dockerfile.grpc-villager -t "$IMAGE" ..
    fi
fi

# 检查端口是否被占用
if docker ps --format "table {{.Ports}}" | grep -q ":$PORT->"; then
    print_warning "端口 $PORT 已被占用"
    print_info "尝试停止占用端口的容器..."
    docker ps --format "table {{.ID}}\t{{.Ports}}" | grep ":$PORT->" | awk '{print $1}' | xargs -r docker stop
    sleep 2
fi

# 启动村民节点
print_info "启动村民容器..."

if [ "$MODE" = "cli" ]; then
    print_info "启动CLI模式..."
    docker run -it --rm \
        --network "$NETWORK" \
        -p "$PORT:$PORT" \
        -e VILLAGER_PORT="$PORT" \
        -e COORDINATOR_ADDR="$COORDINATOR_ADDR" \
        "$IMAGE" \
        --cli --port "$PORT"
elif [ "$MODE" = "ai" ]; then
    print_info "启动AI模式..."
    docker run -it --rm \
        --network "$NETWORK" \
        -p "$PORT:$PORT" \
        -e VILLAGER_PORT="$PORT" \
        -e COORDINATOR_ADDR="$COORDINATOR_ADDR" \
        "$IMAGE" \
        --ai --port "$PORT"
else
    print_info "启动服务模式..."
    docker run -d \
        --name "villager-${ARCH}-${NODE_ID}" \
        --network "$NETWORK" \
        -p "$PORT:$PORT" \
        -e VILLAGER_PORT="$PORT" \
        -e COORDINATOR_ADDR="$COORDINATOR_ADDR" \
        "$IMAGE" \
        --service "$PORT" "$NODE_ID"
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if docker ps --format "table {{.Names}}" | grep -q "villager-${ARCH}-${NODE_ID}"; then
        print_success "村民节点启动成功！"
        echo ""
        echo "📋 节点信息:"
        echo "  容器名: villager-${ARCH}-${NODE_ID}"
        echo "  端口: $PORT"
        echo "  节点ID: $NODE_ID"
        echo "  架构: ${ARCH^^}"
        echo ""
        echo "🔧 管理命令:"
        echo "  docker logs villager-${ARCH}-${NODE_ID}     # 查看日志"
        echo "  docker stop villager-${ARCH}-${NODE_ID}     # 停止节点"
        echo "  docker exec -it villager-${ARCH}-${NODE_ID} bash  # 进入容器"
        echo ""
        echo "🎮 连接到节点:"
        if [ "$ARCH" = "rest" ]; then
            echo "  ./docker-tools.sh cli-rest $PORT"
        else
            echo "  ./docker-tools.sh cli-grpc $PORT"
        fi
    else
        print_error "村民节点启动失败"
        echo "查看日志: docker logs villager-${ARCH}-${NODE_ID}"
        exit 1
    fi
fi
