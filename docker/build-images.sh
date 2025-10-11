#!/bin/bash

# 构建分布式小镇Docker镜像脚本

set -e

echo "================================================"
echo "  构建分布式小镇Docker镜像"
echo "================================================"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "项目根目录: $PROJECT_ROOT"
echo "Docker目录: $SCRIPT_DIR"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 构建基础服务镜像
echo ""
echo "1. 构建基础服务镜像 (coordinator + merchant)..."
docker build -f docker/Dockerfile.base-services -t distribu-town-base-services:latest .

if [ $? -eq 0 ]; then
    echo "✓ 基础服务镜像构建成功"
else
    echo "✗ 基础服务镜像构建失败"
    exit 1
fi

# 构建村民CLI镜像
echo ""
echo "2. 构建村民CLI镜像..."
docker build -f docker/Dockerfile.villager-cli -t distribu-town-villager-cli:latest .

if [ $? -eq 0 ]; then
    echo "✓ 村民CLI镜像构建成功"
else
    echo "✗ 村民CLI镜像构建失败"
    exit 1
fi

# 构建村民AI镜像
echo ""
echo "3. 构建村民AI镜像..."
docker build -f docker/Dockerfile.villager-ai -t distribu-town-villager-ai:latest .

if [ $? -eq 0 ]; then
    echo "✓ 村民AI镜像构建成功"
else
    echo "✗ 村民AI镜像构建失败"
    exit 1
fi

echo ""
echo "================================================"
echo "  所有镜像构建完成！"
echo "================================================"
echo ""
echo "构建的镜像："
echo "  • distribu-town-base-services:latest  - 基础服务 (coordinator + merchant)"
echo "  • distribu-town-villager-cli:latest    - 村民CLI节点"
echo "  • distribu-town-villager-ai:latest     - 村民AI节点"
echo ""
echo "使用方法："
echo ""
echo "1. 启动基础服务："
echo "   docker run -d --name base-services -p 5000:5000 -p 5001:5001 distribu-town-base-services:latest"
echo ""
echo "2. 启动村民CLI节点："
echo "   docker run -it --name villager-cli --link base-services:coordinator --link base-services:merchant \\"
echo "     -e VILLAGER_PORT=5002 -e VILLAGER_NODE_ID=node1 \\"
echo "     distribu-town-villager-cli:latest"
echo ""
echo "3. 启动村民AI节点："
echo "   docker run -it --name villager-ai --link base-services:coordinator --link base-services:merchant \\"
echo "     -e VILLAGER_PORT=5003 -e VILLAGER_NODE_ID=node2 \\"
echo "     -e AI_NAME=Bob -e AI_OCCUPATION=chef -e AI_GENDER=male \\"
echo "     -e AI_PERSONALITY='聪明的厨师' -e AI_API_KEY=your_openai_api_key \\"
echo "     distribu-town-villager-ai:latest"
echo ""
echo "或者使用docker-compose（推荐）："
echo "   docker-compose up"
echo ""
