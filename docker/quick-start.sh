#!/bin/bash
# DistribuTown Docker 快速启动脚本

set -e

echo "🏘️  DistribuTown Docker 快速启动"
echo "=================================="
echo ""

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 进入docker目录
cd "$(dirname "$0")"

echo "📦 检查Docker镜像..."
if ! docker image inspect distribu-town-base:latest >/dev/null 2>&1; then
    echo "🔨 构建Docker镜像..."
    ./build.sh
else
    echo "✅ Docker镜像已存在"
fi

echo ""
echo "🚀 启动服务..."
./docker-tools.sh start

echo ""
echo "⏳ 等待服务启动..."
sleep 10

echo ""
echo "📊 服务状态:"
./docker-tools.sh status

echo ""
echo "🎉 启动完成！"
echo ""
echo "📋 可用操作:"
echo "  ./docker-tools.sh cli-rest 5002    # 启动REST CLI"
echo "  ./docker-tools.sh cli-grpc 50053   # 启动gRPC CLI"
echo "  ./docker-tools.sh ai-rest 5002     # 启动REST AI代理"
echo "  ./docker-tools.sh logs             # 查看日志"
echo "  ./docker-tools.sh status           # 查看状态"
echo "  ./docker-tools.sh stop             # 停止服务"
echo ""
echo "🛠️  开发环境:"
echo "  ./docker-tools.sh dev              # 启动开发环境"
echo ""
echo "📚 更多帮助:"
echo "  ./docker-tools.sh help"
