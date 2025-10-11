# DistribuTown Docker部署指南

## 🐳 Docker镜像说明

本项目提供6个Docker镜像：

### 1. `distribu-town-base:latest`
- **用途**: 基础镜像，包含common模块和Python环境
- **依赖**: Python 3.11, common模块
- **系统工具**: gcc, procps, lsof, curl

### 2. `distribu-town-grpc-services:latest`
- **用途**: gRPC版本的基础服务（Coordinator + Merchant）
- **端口**: 50051 (Coordinator), 50052 (Merchant)
- **依赖**: distribu-town-base
- **健康检查**: gRPC连接测试

### 3. `distribu-town-grpc-villager:latest`
- **用途**: gRPC版本的村民启动器
- **端口**: 50053-50099 (村民节点)
- **模式**: 
  - `--cli`: 手动CLI模式
  - `--ai`: AI代理模式（toy样例）
  - `--service`: 村民节点模式
- **依赖**: distribu-town-base

### 4. `distribu-town-rest-services:latest`
- **用途**: REST版本的基础服务（Coordinator + Merchant）
- **端口**: 5000 (Coordinator), 5001 (Merchant)
- **依赖**: distribu-town-base
- **健康检查**: HTTP连接测试

### 5. `distribu-town-rest-villager:latest`
- **用途**: REST版本的村民启动器
- **端口**: 5002-50099 (村民节点)
- **模式**: 
  - `--cli`: 手动CLI模式
  - `--ai`: AI代理模式（完整功能）
  - `--service`: 村民节点模式
- **依赖**: distribu-town-base

### 6. `distribu-town-dev:latest` ⭐ 新增
- **用途**: 开发环境镜像，包含所有架构和工具
- **功能**: 支持交互式开发、调试、测试
- **工具**: ipython, jupyter, pytest, black, flake8
- **端口**: 5000-50099 (所有端口)

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

### 3. 使用Docker工具脚本 ⭐ 推荐
```bash
cd docker
chmod +x docker-tools.sh

# 查看帮助
./docker-tools.sh help

# 启动所有服务
./docker-tools.sh start

# 查看状态
./docker-tools.sh status

# 查看日志
./docker-tools.sh logs
./docker-tools.sh logs-follow grpc-services
```

## 🛠️ 开发环境

### 启动开发环境
```bash
cd docker
./docker-tools.sh dev
```

开发环境提供以下命令：
- `start-grpc-services` - 启动gRPC基础服务
- `start-rest-services` - 启动REST基础服务
- `start-grpc-villager <port> <id>` - 启动gRPC村民节点
- `start-rest-villager <port> <id>` - 启动REST村民节点
- `cli-grpc <port>` - 启动gRPC CLI
- `cli-rest <port>` - 启动REST CLI
- `ai-grpc <port>` - 启动gRPC AI代理
- `ai-rest <port>` - 启动REST AI代理
- `bash` - 进入bash shell

### 开发环境特性
- 代码热重载（通过volume挂载）
- 调试模式支持
- 完整的开发工具链
- 交互式shell访问

## 🎮 交互式操作

### CLI模式（手动操作）
```bash
# 使用工具脚本
./docker-tools.sh cli-grpc 50053
./docker-tools.sh cli-rest 5002

# 或直接使用docker run
docker run -it --rm --network docker_distribu-town-grpc \
    distribu-town-grpc-villager:latest --cli --port 50053
```

### AI模式（自动代理）
```bash
# 使用工具脚本
./docker-tools.sh ai-grpc 50053
./docker-tools.sh ai-rest 5002

# 或直接使用docker run
docker run -it --rm --network docker_distribu-town-rest \
    distribu-town-rest-villager:latest --ai --port 5002
```

## 🔧 服务管理

### 使用Docker工具脚本
```bash
# 查看服务状态
./docker-tools.sh status

# 查看日志
./docker-tools.sh logs
./docker-tools.sh logs-follow grpc-services

# 进入容器shell
./docker-tools.sh shell grpc-services

# 停止服务
./docker-tools.sh stop

# 重启服务
./docker-tools.sh restart
```

### 传统方式
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs
docker-compose logs grpc-services

# 停止服务
docker-compose down
```

## 🌐 网络配置

- **gRPC网络**: `docker_distribu-town-grpc`
- **REST网络**: `docker_distribu-town-rest`

## 📝 环境变量

### 服务配置
- `PYTHONPATH=/app` - Python模块路径
- `DEBUG=true` - 开发模式（仅开发环境）
- `VILLAGER_PORT` - 村民节点端口
- `COORDINATOR_ADDR` - 协调器地址

### AI代理配置
- `OPENAI_API_KEY` - OpenAI API密钥（AI模式需要）
- `MODEL` - AI模型名称（默认: gpt-4）

## 🧪 测试

### 运行性能测试
```bash
./docker-tools.sh test
```

### 手动测试
```bash
# 启动服务
./docker-tools.sh start

# 等待服务启动
sleep 10

# 运行测试
docker run --rm --network docker_distribu-town-rest \
    -v "$(pwd)/../performance_tests:/app" \
    python:3.11-slim \
    bash -c "cd /app && pip install requests && python benchmark.py --requests 10"
```

## 📋 注意事项

1. **gRPC AI代理**: 目前使用toy样例，功能有限
2. **REST AI代理**: 功能完整，支持ReAct模式
3. **端口冲突**: 确保端口5000-50099未被占用
4. **资源需求**: 建议至少2GB内存用于运行多个服务
5. **网络隔离**: gRPC和REST服务使用独立网络

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

### 服务启动失败
```bash
# 查看详细日志
./docker-tools.sh logs-follow grpc-services

# 检查健康状态
docker-compose ps
```

## 🔄 更新和维护

### 清理资源
```bash
./docker-tools.sh clean
```

### 重新构建
```bash
./docker-tools.sh build
```

### 开发环境重置
```bash
./docker-tools.sh clean
./docker-tools.sh build-dev
./docker-tools.sh dev
```

## 📚 更多信息

- 项目文档: `../README.md`
- 快速开始: `../QUICKSTART.md`
- 项目总结: `../PROJECT_SUMMARY.md`
