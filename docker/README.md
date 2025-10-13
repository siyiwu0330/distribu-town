# DistribuTown Docker Deployment Guide

## 🐳 Docker Images Description

This project provides 6 Docker images:

### 1. `distribu-town-base:latest`
- **Purpose**: Base image containing common modules and Python environment
- **Dependencies**: Python 3.11, common modules
- **System Tools**: gcc, procps, lsof, curl

### 2. `distribu-town-grpc-services:latest`
- **Purpose**: gRPC version of base services (Coordinator + Merchant)
- **Ports**: 50051 (Coordinator), 50052 (Merchant)
- **Dependencies**: distribu-town-base
- **Health Check**: gRPC connection test

### 3. `distribu-town-grpc-villager:latest`
- **Purpose**: gRPC version villager launcher
- **Ports**: 50053-50099 (villager nodes)
- **Modes**: 
  - `--cli`: Manual CLI mode
  - `--ai`: AI agent mode (toy example)
  - `--service`: Villager node mode
- **Dependencies**: distribu-town-base

### 4. `distribu-town-rest-services:latest`
- **Purpose**: REST version of base services (Coordinator + Merchant)
- **Ports**: 5000 (Coordinator), 5001 (Merchant)
- **Dependencies**: distribu-town-base
- **Health Check**: HTTP connection test

### 5. `distribu-town-rest-villager:latest`
- **Purpose**: REST version villager launcher
- **Ports**: 5002-50099 (villager nodes)
- **Modes**: 
  - `--cli`: Manual CLI mode
  - `--ai`: AI agent mode (full features)
  - `--service`: Villager node mode
- **Dependencies**: distribu-town-base

### 6. `distribu-town-dev:latest` ⭐ New
- **Purpose**: Development environment image with all architectures and tools
- **Features**: Supports interactive development, debugging, testing
- **Tools**: ipython, jupyter, pytest, black, flake8
- **Ports**: 5000-50099 (all ports)

## 🚀 Quick Start

### 1. Build All Images
```bash
cd docker
./build.sh
```

### 2. Start Complete Services
```bash
cd docker
docker-compose up -d
```

### 3. Use Docker Tools Script ⭐ Recommended
```bash
cd docker
chmod +x docker-tools.sh

# View help
./docker-tools.sh help

# Start all services
./docker-tools.sh start

# Check status
./docker-tools.sh status

# View logs
./docker-tools.sh logs
./docker-tools.sh logs-follow grpc-services
```

## 🛠️ Development Environment

### Start Development Environment
```bash
cd docker
./docker-tools.sh dev
```

Development environment provides the following commands:
- `start-grpc-services` - Start gRPC base services
- `start-rest-services` - Start REST base services
- `start-grpc-villager <port> <id>` - Start gRPC villager node
- `start-rest-villager <port> <id>` - Start REST villager node
- `cli-grpc <port>` - Start gRPC CLI
- `cli-rest <port>` - Start REST CLI
- `ai-grpc <port>` - Start gRPC AI agent
- `ai-rest <port>` - Start REST AI agent
- `bash` - Enter bash shell

### Development Environment Features
- Code hot reload (via volume mounting)
- Debug mode support
- Complete development toolchain
- Interactive shell access

## 🎮 Interactive Operations

### CLI Mode (Manual Operation)
```bash
# Using tool script
./docker-tools.sh cli-grpc 50053
./docker-tools.sh cli-rest 5002

# Or directly use docker run
docker run -it --rm --network docker_distribu-town-grpc \
    distribu-town-grpc-villager:latest --cli --port 50053
```

### AI Mode (Automatic Agent)
```bash
# Using tool script
./docker-tools.sh ai-grpc 50053
./docker-tools.sh ai-rest 5002

# Or directly use docker run
docker run -it --rm --network docker_distribu-town-rest \
    distribu-town-rest-villager:latest --ai --port 5002
```

## 🔧 Service Management

### Using Docker Tools Script
```bash
# View service status
./docker-tools.sh status

# View logs
./docker-tools.sh logs
./docker-tools.sh logs-follow grpc-services

# Enter container shell
./docker-tools.sh shell grpc-services

# Stop services
./docker-tools.sh stop

# Restart services
./docker-tools.sh restart
```

### Traditional Method
```bash
# View service status
docker-compose ps

# View logs
docker-compose logs
docker-compose logs grpc-services

# Stop services
docker-compose down
```

## 🌐 Network Configuration

- **gRPC Network**: `docker_distribu-town-grpc`
- **REST Network**: `docker_distribu-town-rest`

## 📝 Environment Variables

### Service Configuration
- `PYTHONPATH=/app` - Python module path
- `DEBUG=true` - Development mode (dev environment only)
- `VILLAGER_PORT` - Villager node port
- `COORDINATOR_ADDR` - Coordinator address

### AI Agent Configuration
- `OPENAI_API_KEY` - OpenAI API key (required for AI mode)
- `MODEL` - AI model name (default: gpt-4)

## 🧪 Testing

### Run Performance Tests
```bash
./docker-tools.sh test
```

### Manual Testing
```bash
# Start services
./docker-tools.sh start

# Wait for services to start
sleep 10

# Run tests
docker run --rm --network docker_distribu-town-rest \
    -v "$(pwd)/../performance_tests:/app" \
    python:3.11-slim \
    bash -c "cd /app && pip install requests && python benchmark.py --requests 10"
```

## 📋 Important Notes

1. **gRPC AI Agent**: Currently uses toy example, limited functionality
2. **REST AI Agent**: Full functionality, supports ReAct mode
3. **Port Conflicts**: Ensure ports 5000-50099 are not occupied
4. **Resource Requirements**: At least 2GB memory recommended for running multiple services
5. **Network Isolation**: gRPC and REST services use independent networks

## 🐛 Troubleshooting

### Port Occupied
```bash
# Check port usage
netstat -tulpn | grep :5000
netstat -tulpn | grep :50051

# Kill occupying process
sudo kill -9 <PID>
```

### Image Build Failure
```bash
# Clean Docker cache
docker system prune -a

# Rebuild
./build.sh
```

### Network Connection Issues
```bash
# Check networks
docker network ls
docker network inspect docker_distribu-town-grpc
```

### Service Startup Failure
```bash
# View detailed logs
./docker-tools.sh logs-follow grpc-services

# Check health status
docker-compose ps
```

## 🔄 Updates and Maintenance

### Clean Resources
```bash
./docker-tools.sh clean
```

### Rebuild
```bash
./docker-tools.sh build
```

### Development Environment Reset
```bash
./docker-tools.sh clean
./docker-tools.sh build-dev
./docker-tools.sh dev
```

## 📚 More Information

- Project Documentation: `../README.md`
- Quick Start: `../QUICKSTART.md`
- Project Summary: `../PROJECT_SUMMARY.md`
