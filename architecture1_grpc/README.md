# Architecture 1: gRPC分布式架构

## 概述

这是基于gRPC的分布式虚拟小镇实现，展示了使用Protocol Buffers和gRPC进行微服务通信的架构。

## 最新更新 ✨

### 中心化交易系统
- ✅ 实现了与REST版本相同的中心化交易管理
- ✅ Merchant节点作为交易协调器
- ✅ 支持完整的交易流程：Create → Accept → Confirm → Execute
- ✅ 原子操作和回滚机制
- ✅ 交互式CLI支持所有交易命令

详细说明请查看 [README_TRADING.md](README_TRADING.md)

## 架构特点

### gRPC通信
- 使用Protocol Buffers定义服务接口
- HTTP/2二进制协议，高性能
- 强类型检查
- 自动生成客户端代码

### 节点类型
1. **Coordinator** - 时间协调器
   - 管理全局时间
   - 同步所有节点
   - 节点注册和发现

2. **Merchant** - 商人节点
   - 提供物品买卖服务
   - **中心化交易管理** (新增)
   - 交易ID生成和状态管理
   - 交易原子执行

3. **Villager** - 村民节点
   - 村民信息管理
   - 生产、交易、睡眠
   - **原子交易执行** (新增)

## 目录结构

```
architecture1_grpc/
├── proto/                      # Protocol Buffers定义
│   ├── town.proto             # 服务和消息定义
│   ├── town_pb2.py            # 生成的消息类
│   └── town_pb2_grpc.py       # 生成的服务类
├── coordinator.py              # 协调器实现
├── merchant.py                 # 商人节点实现
├── villager.py                 # 村民节点实现
├── interactive_cli.py          # 交互式CLI (新增)
├── test_centralized_trade.py  # 交易系统测试 (新增)
├── start_test_nodes.sh         # 快速启动脚本 (新增)
├── README.md                   # 本文件
└── README_TRADING.md           # 交易系统详细说明 (新增)
```

## 快速开始

### 1. 安装依赖

```bash
cd architecture1_grpc
pip install -r requirements.txt
```

### 2. 编译Proto文件（如需修改）

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/town.proto
```

### 3. 启动节点

#### 方法1: 使用启动脚本（推荐）
```bash
./start_test_nodes.sh
```

#### 方法2: 手动启动
```bash
# 终端1: 协调器
python coordinator.py --port 50051

# 终端2: 商人
python merchant.py --port 50052

# 终端3: 村民1
python villager.py --port 50053 --id node1

# 终端4: 村民2
python villager.py --port 50054 --id node2
```

### 4. 测试交易系统

```bash
# 运行自动化测试
python test_centralized_trade.py

# 或使用交互式CLI
python interactive_cli.py --id node1 --address localhost:50053
```

## 使用示例

### 交互式CLI

```bash
# 启动CLI
python interactive_cli.py --id node1 --address localhost:50053

# 在CLI中
> info                              # 查看我的信息
> nodes                             # 查看在线村民
> trade node2 sell wheat 5 50      # 向node2发起交易
> mytrades                          # 查看我的交易
> confirm trade_1                   # 确认交易
```

### 编程接口

```python
import grpc
from proto import town_pb2, town_pb2_grpc

# 连接到商人节点
channel = grpc.insecure_channel('localhost:50052')
stub = town_pb2_grpc.MerchantNodeStub(channel)

# 创建交易
response = stub.CreateTrade(town_pb2.CreateTradeRequest(
    initiator_id='node1',
    initiator_address='localhost:50053',
    target_id='node2',
    target_address='localhost:50054',
    offer_type='sell',
    item='wheat',
    quantity=5,
    price=50
))

print(f"Trade ID: {response.trade_id}")
channel.close()
```

## 与REST版本对比

| 特性 | gRPC版本 | REST版本 |
|-----|---------|---------|
| 通信协议 | gRPC (HTTP/2) | HTTP/JSON |
| 类型系统 | Protobuf强类型 | JSON动态类型 |
| 性能 | 更高（二进制） | 较低（文本） |
| 调试难度 | 较高 | 较低 |
| 跨语言支持 | 优秀 | 优秀 |
| 浏览器支持 | 需要grpc-web | 原生支持 |
| 适用场景 | 内部微服务 | 公开API |

## 开发指南

### 修改Proto定义

1. 编辑 `proto/town.proto`
2. 重新编译：
   ```bash
   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/town.proto
   ```
3. 更新服务实现

### 添加新功能

1. 在proto文件中定义新消息和RPC
2. 重新编译proto
3. 实现服务端逻辑
4. 更新客户端代码

### 调试技巧

1. **查看日志**: 使用 `start_test_nodes.sh` 启动后，日志在 `logs/` 目录
2. **gRPC错误**: 检查 `e.code()` 和 `e.details()`
3. **连接问题**: 确认端口未被占用，使用 `lsof -i :50051`

## 测试

### 单元测试
```bash
python test_centralized_trade.py
```

### 压力测试
```bash
# TODO: 添加并发交易测试
```

## 已知限制

1. **AI Agent**: gRPC版本不包含AI Agent实现
   - 建议使用REST版本（architecture2_rest）进行AI实验
   - gRPC版本主要用于演示架构差异

2. **错误恢复**: 节点崩溃后交易状态可能丢失
   - 生产环境需要持久化存储

3. **并发控制**: 当前实现为简单锁机制
   - 高并发场景需要优化

## 常见问题

### Q: proto编译失败
A: 确保安装了 `grpcio-tools`:
```bash
pip install grpcio-tools
```

### Q: 连接失败
A: 检查节点是否正常启动：
```bash
# 查看进程
ps aux | grep python

# 查看端口
lsof -i :50051-50054
```

### Q: 交易失败
A: 查看详细文档 [README_TRADING.md](README_TRADING.md)

## 下一步

- [ ] 添加AI Agent支持（可选）
- [ ] 实现交易历史持久化
- [ ] 添加更多测试用例
- [ ] 性能基准测试
- [ ] Docker容器化部署

## 参考资源

- [gRPC Python文档](https://grpc.io/docs/languages/python/)
- [Protocol Buffers指南](https://developers.google.com/protocol-buffers)
- [REST版本对比](../architecture2_rest/README.md)

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

