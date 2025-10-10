#!/bin/bash
# Docker构建脚本

set -e

echo "🐳 Building DistribuTown Docker Images..."

# 构建基础镜像
echo "📦 Building base image..."
docker build -f docker/Dockerfile.base -t distribu-town-base:latest .

# 构建gRPC镜像
echo "📦 Building gRPC services image..."
docker build -f docker/Dockerfile.grpc-services -t distribu-town-grpc-services:latest .

echo "📦 Building gRPC villager image..."
docker build -f docker/Dockerfile.grpc-villager -t distribu-town-grpc-villager:latest .

# 构建REST镜像
echo "📦 Building REST services image..."
docker build -f docker/Dockerfile.rest-services -t distribu-town-rest-services:latest .

echo "📦 Building REST villager image..."
docker build -f docker/Dockerfile.rest-villager -t distribu-town-rest-villager:latest .

echo "✅ All images built successfully!"
echo ""
echo "📋 Available images:"
docker images | grep distribu-town

echo ""
echo "🚀 To start services:"
echo "  cd docker && docker-compose up -d"
echo ""
echo "🎮 To start with specific mode:"
echo "  # CLI mode:"
echo "  docker run -it --network docker_distribu-town-grpc distribu-town-grpc-villager:latest --cli --port 50055"
echo "  # AI mode:"
echo "  docker run -it --network docker_distribu-town-grpc distribu-town-grpc-villager:latest --ai --port 50055"
