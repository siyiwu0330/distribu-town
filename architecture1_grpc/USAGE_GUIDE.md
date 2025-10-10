# gRPC版本使用指南

## 快速开始

### 1. 启动基础服务

```bash
cd architecture1_grpc
./start_services.sh
```

这会启动：
- Coordinator (端口 50051)
- Merchant (端口 50052)

### 2. 启动村民节点

```bash
# 启动第一个村民节点
./start_villager.sh 50053 node1

# 启动第二个村民节点（新终端）
./start_villager.sh 50054 node2
```

### 3. 使用交互式CLI

#### 连接到node1
```bash
python interactive_cli.py --port 50053
```

#### 基本操作流程
```
> create                    # 创建村民
  名字: Alice
  职业: farmer
  性别: female
  性格: 勤劳的农夫

> info                      # 查看信息
> produce                   # 生产
> price                     # 查看商人价格
> buy seed 2                # 从商人购买
> nodes                     # 查看在线村民
> trade node2 sell wheat 3 50  # 向node2发起交易
> mytrades                  # 查看我的交易
> exit
```

#### 连接到node2处理交易
```bash
python interactive_cli.py --port 50054
```

```
> create                    # 创建村民
  名字: Bob
  职业: carpenter
  性别: male
  性格: 强壮的木匠

> trades                    # 查看待处理交易
> accept trade_1            # 接受交易
> confirm trade_1           # 确认交易
> info                      # 查看结果
```

### 4. 使用AI Agent托管

```bash
python ai_agent_grpc.py --port 50054 --name Alice --occupation chef --gender female --personality "test" 
```

## 测试步骤

### 步骤1: 基础功能测试
1. 启动基础服务：`./start_services.sh`
2. 启动村民节点：`./start_villager.sh 50053 node1`
3. 创建村民：使用CLI创建Alice
4. 测试生产：`produce`命令
5. 测试商人交易：`buy`/`sell`命令

### 步骤2: 交易流程测试
1. 启动第二个村民：`./start_villager.sh 50054 node2`
2. Alice发起交易：`trade node2 sell wheat 3 50`
3. Bob查看交易：`trades`
4. Bob接受交易：`accept trade_1`
5. 双方确认：`confirm trade_1`
6. 检查结果：`info`

### 步骤3: AI Agent测试
1. 启动AI Agent
2. 观察AI的自动决策
3. 检查AI是否执行了正确的行动

## 常见问题

### 问题1: 基础服务启动失败
**症状**: `./start_services.sh`后没有输出
**解决**: 
```bash
# 检查端口占用
lsof -i :50051-50052

# 手动启动看错误
python coordinator.py --port 50051
```

### 问题2: 村民节点启动失败
**症状**: `./start_villager.sh`失败
**解决**: 确保基础服务已启动，检查端口冲突

### 问题3: CLI连接失败
**症状**: "无法连接到村民节点"
**解决**: 确保节点已启动，检查端口

### 问题4: 村民创建失败
**症状**: "Villager not initialized"
**解决**: 先运行`create`命令创建村民

### 问题5: 交易失败
**症状**: 交易创建/接受/确认失败
**解决**: 检查双方资源是否充足

## 反馈格式

请按以下格式反馈问题：

```
【问题描述】
具体描述遇到的问题

【操作步骤】
1. 执行了什么命令
2. 期望的结果
3. 实际的结果

【错误信息】
粘贴完整的错误信息

【环境信息】
- 操作系统: 
- Python版本:
- 节点状态: (运行/停止)
```

## 下一步

1. 先测试基础功能（创建村民、生产、商人交易）
2. 再测试村民间交易
3. 最后测试AI Agent
4. 每个步骤遇到问题请及时反馈

我会根据您的反馈逐步修复问题！