#!/bin/bash
# 启动gRPC基础服务（Coordinator + Merchant）

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

# 检测Docker Compose命令
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    print_error "Docker Compose未安装"
    exit 1
fi

print_info "启动gRPC基础服务..."

# 进入docker目录
cd "$(dirname "$0")"

# 检查镜像是否存在
if ! docker image inspect distribu-town-grpc-services:latest >/dev/null 2>&1; then
    print_info "构建gRPC服务镜像..."
    docker build -f Dockerfile.grpc-services -t distribu-town-grpc-services:latest ..
fi

# 启动gRPC基础服务
print_info "启动Coordinator和Merchant..."
$COMPOSE_CMD up -d grpc-services

# 等待服务启动
print_info "等待服务启动..."
sleep 5

# 检查服务状态
print_info "检查服务状态..."
if $COMPOSE_CMD ps grpc-services | grep -q "Up"; then
    print_success "gRPC基础服务启动成功！"
    echo ""
    echo "📋 服务信息:"
    echo "  Coordinator: localhost:50051"
    echo "  Merchant:    localhost:50052"
    echo ""
    echo "🎮 现在可以启动村民节点:"
    echo "  ./start-villager.sh grpc 50053 node1"
    echo "  ./start-villager.sh grpc 50054 node2"
    echo ""
    echo "🔧 管理命令:"
    echo "  $COMPOSE_CMD logs grpc-services    # 查看日志"
    echo "  $COMPOSE_CMD stop grpc-services     # 停止服务"
    echo "  $COMPOSE_CMD ps                     # 查看状态"
else
    print_error "服务启动失败"
    echo "查看日志: $COMPOSE_CMD logs grpc-services"
    exit 1
fi
