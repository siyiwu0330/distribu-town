# DistribuTown Docker部署指南

## 🐳 Docker镜像说明

本项目提供4个Docker镜像：

### 1. `distribu-town-base:latest`
- **用途**: 基础镜像，包含common模块和Python环境
- **依赖**: Python 3.11, common模块

### 2. `distribu-town-grpc-services:latest`
- **用途**: gRPC版本的基础服务（Coordinator + Merchant）
- **端口**: 50051 (Coordinator), 50052 (Merchant)
- **依赖**: distribu-town-base

### 3. `distribu-town-grpc-villager:latest`
- **用途**: gRPC版本的村民启动器
- **端口**: 50053-50099 (村民节点)
- **模式**: 
  - `--cli`: 手动CLI模式
  - `--ai`: AI代理模式（toy样例）
  - 默认: 村民节点模式
- **依赖**: distribu-town-base

### 4. `distribu-town-rest-services:latest`
- **用途**: REST版本的基础服务（Coordinator + Merchant）
- **端口**: 5000 (Coordinator), 5001 (Merchant)
- **依赖**: distribu-town-base

### 5. `distribu-town-rest-villager:latest`
- **用途**: REST版本的村民启动器
- **端口**: 5002-50099 (村民节点)
- **模式**: 
  - `--cli`: 手动CLI模式
  - `--ai`: AI代理模式（完整功能）
  - 默认: 村民节点模式
- **依赖**: distribu-town-base

## 🚀 快速开始

### 1. 构建所有镜像
```bash
cd docker
./build.sh
```

### 2. 启动完整服务
```bash
cd docker
docker-compose up -d
```

### 3. 启动特定模式

#### CLI模式（手动操作）
```bash
# gRPC版本
docker run -it --network docker_distribu-town-grpc distribu-town-grpc-villager:latest --cli --port 50055

# REST版本
docker run -it --network docker_distribu-town-rest distribu-town-rest-villager:latest --cli --port 5004
```

#### AI模式（自动代理）
```bash
# gRPC版本（toy样例）
docker run -it --network docker_distribu-town-grpc distribu-town-grpc-villager:latest --ai --port 50055

# REST版本（完整功能）
docker run -it --network docker_distribu-town-rest distribu-town-rest-villager:latest --ai --port 5004
```

## 🔧 服务管理

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs grpc-services
docker-compose logs rest-villager-1
```

### 停止服务
```bash
docker-compose down
```

## 🌐 网络配置

- **gRPC网络**: `docker_distribu-town-grpc`
- **REST网络**: `docker_distribu-town-rest`

## 📝 注意事项

1. **gRPC AI代理**: 目前使用toy样例，功能有限
2. **REST AI代理**: 功能完整，支持ReAct模式
3. **端口冲突**: 确保端口5000-50099未被占用
4. **资源需求**: 建议至少2GB内存用于运行多个服务

## 🐛 故障排除

### 端口被占用
```bash
# 查看端口占用
netstat -tulpn | grep :5000
netstat -tulpn | grep :50051

# 停止占用进程
sudo kill -9 <PID>
```

### 镜像构建失败
```bash
# 清理Docker缓存
docker system prune -a

# 重新构建
./build.sh
```

### 网络连接问题
```bash
# 检查网络
docker network ls
docker network inspect docker_distribu-town-grpc
```
