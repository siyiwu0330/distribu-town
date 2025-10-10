# gRPC版本中心化交易系统

## 概述

gRPC版本现已实现与REST版本相同的中心化交易系统，所有交易由Merchant节点统一管理。

## 架构特点

### 中心化交易管理
- **Merchant节点**: 负责交易ID生成、状态管理、原子执行
- **Villager节点**: 提供TradeExecute端点支持原子操作
- **交易流程**: Create → Accept → Confirm (双方) → Execute

### 交易状态
- `pending`: 等待target接受
- `accepted`: 已接受，等待双方确认
- `rejected`: 已拒绝
- `completed`: 交易完成（记录已删除）

## 使用方法

### 1. 启动节点

```bash
# 终端1: 启动协调器
cd architecture1_grpc
python coordinator.py --port 50051

# 终端2: 启动商人
python merchant.py --port 50052

# 终端3: 启动村民1
python villager.py --port 50053 --id node1

# 终端4: 启动村民2
python villager.py --port 50054 --id node2
```

### 2. 创建村民

```bash
# 终端5: 连接node1的CLI
python interactive_cli.py --id node1 --address localhost:50053

# 在CLI中创建村民
> info  # 查看状态
```

### 3. 发起交易

```bash
# 在node1的CLI中
> nodes  # 查看在线村民

> trade node2 sell wheat 5 50
# 向node2发起交易：出售5个wheat，价格50

# 查看我的交易
> mytrades
```

### 4. 处理交易

```bash
# 终端6: 连接node2的CLI
python interactive_cli.py --id node2 --address localhost:50054

# 在node2的CLI中
> trades  # 查看待处理的交易

> accept trade_1  # 接受交易

> confirm trade_1  # 确认交易
```

### 5. 完成交易

```bash
# 回到node1
> confirm trade_1  # 发起方确认

# 双方确认后，Merchant自动执行原子交易
# 资源转移：
#   1. node1（买方）支付50货币
#   2. node2（卖方）移除5个wheat
#   3. node1获得5个wheat
#   4. node2收到50货币
```

## 交易命令

### 基本操作
- `info` - 查看我的信息
- `produce` - 执行生产
- `sleep` - 睡眠
- `time` - 查看当前时间
- `advance` - 推进时间

### 商人交易
- `price` - 查看商人价格表
- `buy <item> <qty>` - 从商人购买
- `sell <item> <qty>` - 向商人出售

### 村民交易
- `nodes` - 刷新并查看在线村民
- `trade <node_id> <buy/sell> <item> <qty> <price>` - 发起交易
- `trades` - 查看待处理的交易
- `mytrades` - 查看我发起的交易
- `accept <trade_id>` - 接受交易
- `reject <trade_id>` - 拒绝交易
- `confirm <trade_id>` - 确认交易
- `cancel <trade_id>` - 取消交易

## API说明

### Merchant gRPC服务

#### CreateTrade
创建交易请求

```protobuf
message CreateTradeRequest {
    string initiator_id = 1;
    string initiator_address = 2;
    string target_id = 3;
    string target_address = 4;
    string offer_type = 5;  // "buy" or "sell"
    string item = 6;
    int32 quantity = 7;
    int32 price = 8;
}
```

#### ListTrades
查询交易列表

```protobuf
message ListTradesRequest {
    string node_id = 1;
    string type = 2;  // "pending", "sent", "all"
}
```

#### AcceptTrade / ConfirmTrade / CancelTrade / RejectTrade
交易操作

```protobuf
message AcceptTradeRequest {
    string trade_id = 1;
    string node_id = 2;
}
```

### Villager gRPC服务

#### TradeExecute
执行交易原子操作（由Merchant调用）

```protobuf
message TradeExecuteRequest {
    string action = 1;  // "pay", "refund", "add_item", "remove_item", "receive"
    string item = 2;
    int32 quantity = 3;
    int32 money = 4;
}
```

## 与REST版本对比

### 相似之处
- 中心化交易管理架构
- 相同的交易流程和状态机
- 原子操作和回滚机制
- 交易ID生成和管理

### 差异之处
- **通信协议**: gRPC vs HTTP/JSON
- **类型安全**: Protobuf强类型 vs JSON动态类型
- **性能**: gRPC使用HTTP/2和二进制序列化
- **客户端**: 需要编译proto文件生成stub

## 注意事项

1. **proto编译**: 修改proto文件后需要重新编译
   ```bash
   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/town.proto
   ```

2. **地址格式**: gRPC使用 `host:port` 格式，如 `localhost:50053`

3. **错误处理**: gRPC使用context.set_code()和status返回错误

4. **连接管理**: 每次调用需要创建和关闭channel

## AI Agent支持

gRPC版本的AI Agent实现较为复杂，建议：
1. 使用REST版本（architecture2_rest）进行AI Agent实验
2. gRPC版本主要用于演示分布式架构和协议差异
3. 如需gRPC版本的AI Agent，可参考REST版本进行适配

## 示例场景

完整的交易场景示例请参考 `test_scenario.py`。

## 故障排查

### 交易创建失败
- 检查目标节点是否在线（使用`nodes`命令）
- 确认Merchant节点正常运行
- 查看Merchant日志

### 交易执行失败
- 检查双方资源是否充足
- 查看Villager节点日志
- 确认交易状态正确（先accept再confirm）

### 连接问题
- 确认所有节点地址正确
- 检查防火墙设置
- 验证gRPC端口未被占用

