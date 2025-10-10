# gRPC消息系统调试指南

## 问题诊断

### 1. 检查HTTP服务器是否启动

当你启动villager节点时，应该看到以下日志：
```
[Villager-node1] 村民节点启动在端口 50053
[Villager-node1] 正在启动HTTP服务器，端口: 51053
[Villager-node1] HTTP服务器启动，端口: 51053
```

如果没有看到HTTP服务器启动的日志，说明HTTP服务器启动失败。

### 2. 测试HTTP服务器

```bash
# 测试node1的HTTP服务器（假设gRPC端口为50053）
curl http://localhost:51053/test

# 应该返回：
{"message":"HTTP server working for node1","port":51053}
```

### 3. 运行自动化测试脚本

```bash
cd architecture1_grpc

# 测试node1
python test_message.py --grpc-port 50053 --node-id node1

# 测试node2
python test_message.py --grpc-port 50054 --node-id node2
```

## 常见问题

### 问题1: Flask未安装

**症状**：启动villager节点时没有看到"HTTP服务器启动"的日志

**解决方案**：
```bash
cd architecture1_grpc
pip install -r requirements.txt
```

### 问题2: 端口被占用

**症状**：启动失败，显示"Address already in use"

**解决方案**：
```bash
# 查找占用端口的进程
lsof -i :51053

# 杀掉进程
kill -9 <PID>
```

### 问题3: 消息发送但接收不到

**可能原因**：
1. HTTP服务器端口计算错误
2. 节点地址解析错误
3. 消息未正确存储到villager_service.messages

**调试步骤**：

1. 检查发送方日志，应该看到：
```
[Villager-node1] 发送消息: private -> node2: hello
```

2. 检查接收方日志，应该看到：
```
[Villager-node2] 收到消息: node1 -> node2: hello
```

3. 如果接收方没有收到消息日志，说明HTTP请求失败了

4. 手动测试消息发送：
```bash
# 向node2发送测试消息（假设node2的gRPC端口为50054）
curl -X POST http://localhost:51054/messages/receive \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "test_1",
    "from": "node1",
    "to": "node2",
    "content": "Test message",
    "type": "private",
    "timestamp": 1234567890,
    "is_read": false
  }'

# 应该返回：
{"success":true,"message":"消息接收成功"}
```

5. 在node2的CLI中检查：
```
[Day 1 - morning] > msgs
```

## 完整测试流程

### 步骤1: 安装依赖
```bash
cd architecture1_grpc
pip install -r requirements.txt
```

### 步骤2: 启动Coordinator
```bash
python coordinator.py --port 50051
```

### 步骤3: 启动Merchant
```bash
python merchant.py --port 50052
```

### 步骤4: 启动Villager节点
```bash
# 终端1: 启动node1
python villager.py --port 50053 --id node1

# 终端2: 启动node2
python villager.py --port 50054 --id node2
```

### 步骤5: 测试HTTP服务器
```bash
# 终端3: 测试HTTP服务器
curl http://localhost:51053/test
curl http://localhost:51054/test
```

### 步骤6: 测试消息系统
```bash
# 终端4: 连接到node1的CLI
python interactive_cli.py --port 50053

# 在CLI中：
> create test1 farmer male friendly
> send node2 Hello from node1!
> msgs
```

```bash
# 终端5: 连接到node2的CLI
python interactive_cli.py --port 50054

# 在CLI中：
> create test2 chef male friendly
> msgs  # 应该能看到来自node1的消息
```

## 重要提示

1. **端口对应关系**：
   - gRPC端口: 50053, 50054, 50055...
   - HTTP端口: 51053, 51054, 51055...（gRPC端口 + 1000）

2. **消息传递流程**：
   - node1通过gRPC调用SendMessage
   - SendMessage获取node2的地址（localhost:50054）
   - 计算HTTP端口：50054 + 1000 = 51054
   - 发送HTTP POST到 http://localhost:51054/messages/receive
   - node2的HTTP服务器接收消息并存储到messages列表
   - node2调用GetMessages时返回消息

3. **确保Flask已安装**：
   ```bash
   python -c "import flask; print('Flask已安装')"
   ```

## 如果还是不工作

请提供以下信息：
1. villager节点启动时的完整日志
2. 运行`test_message.py`的输出
3. 运行`curl http://localhost:51053/test`的输出
4. CLI中运行`send`命令后的完整输出

