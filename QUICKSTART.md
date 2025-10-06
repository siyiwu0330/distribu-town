# 快速开始指南

## 环境准备

1. **激活conda环境**

```bash
conda activate distribu-town
```

## 架构1：gRPC微服务架构

### 方式1：使用启动脚本（推荐）

```bash
cd architecture1_grpc
bash start_demo.sh
```

这将启动：
- 时间协调器（端口50051）
- 商人节点（端口50052）
- 4个村民节点（端口50053-50056）

### 方式2：手动启动

在不同的终端窗口中运行：

```bash
# 终端1：启动协调器
cd architecture1_grpc
conda activate distribu-town
python coordinator.py --port 50051

# 终端2：启动商人
python merchant.py --port 50052 --coordinator localhost:50051

# 终端3-6：启动村民
python villager.py --port 50053 --id alice --coordinator localhost:50051
python villager.py --port 50054 --id bob --coordinator localhost:50051
python villager.py --port 50055 --id charlie --coordinator localhost:50051
python villager.py --port 50056 --id diana --coordinator localhost:50051
```

### 运行测试场景

在另一个终端运行：

```bash
cd architecture1_grpc
conda activate distribu-town
python test_scenario.py
```

### 使用交互式客户端

```bash
cd architecture1_grpc
conda activate distribu-town
python client.py
```

## 架构2：RESTful HTTP架构

### 方式1：使用启动脚本（推荐）

```bash
cd architecture2_rest
bash start_demo.sh
```

这将启动：
- 时间协调器（端口5000）
- 商人节点（端口5001）
- 4个村民节点（端口5002-5005）

### 方式2：手动启动

在不同的终端窗口中运行：

```bash
# 终端1：启动协调器
cd architecture2_rest
conda activate distribu-town
python coordinator.py --port 5000

# 终端2：启动商人
python merchant.py --port 5001 --coordinator localhost:5000

# 终端3-6：启动村民
python villager.py --port 5002 --id alice --coordinator localhost:5000
python villager.py --port 5003 --id bob --coordinator localhost:5000
python villager.py --port 5004 --id charlie --coordinator localhost:5000
python villager.py --port 5005 --id diana --coordinator localhost:5000
```

### 运行测试场景

在另一个终端运行：

```bash
cd architecture2_rest
conda activate distribu-town
python test_scenario.py
```

### 使用curl测试API

```bash
# 查看当前时间
curl http://localhost:5000/time

# 创建村民
curl -X POST http://localhost:5002/villager \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","occupation":"farmer","gender":"female","personality":"hardworking"}'

# 查看村民状态
curl http://localhost:5002/villager

# 从商人购买种子
curl -X POST http://localhost:5002/action/trade \
  -H "Content-Type: application/json" \
  -d '{"target":"merchant","item":"seed","quantity":5,"action":"buy"}'

# 执行生产
curl -X POST http://localhost:5002/action/produce

# 推进时间
curl -X POST http://localhost:5000/time/advance

# 睡觉
curl -X POST http://localhost:5002/action/sleep

# 出售给商人
curl -X POST http://localhost:5002/action/trade \
  -H "Content-Type: application/json" \
  -d '{"target":"merchant","item":"wheat","quantity":5,"action":"sell"}'

# 查看所有注册节点
curl http://localhost:5000/nodes

# 查看商人价格表
curl http://localhost:5001/prices
```

## 游戏机制

### 村民属性
- **体力**：0-100，初始100
- **职业**：farmer（农夫）, chef（厨师）, carpenter（木工）
- **货币**：初始100
- **行动点**：每天3点（早中晚）

### 时间系统
- 每天分为三个时段：morning（早晨）、noon（中午）、evening（晚上）
- 生产活动消耗1行动点
- 交易和吃饭不消耗行动点
- 晚上可以睡眠恢复体力

### 职业系统

**农夫（Farmer）**
- 消耗：1种子 + 20体力
- 生产：5小麦

**厨师（Chef）**
- 消耗：3小麦 + 15体力
- 生产：2面包

**木工（Carpenter）**
- 消耗：10木材 + 30体力
- 生产：1住房

### 商人价格

**出售（玩家购买）**
- 木材：5金币/个
- 种子：2金币/个

**收购（玩家出售）**
- 小麦：8金币/个
- 面包：15金币/个
- 住房：150金币/个

### 睡眠机制
- 晚上睡眠恢复30体力
- 有房子可以免费睡眠
- 没有房子需要支付10金币租金
- 不睡眠继续工作额外消耗20体力
- 每天因饥饿扣除10体力

## 典型游戏流程示例

### Alice（农夫）的一天

```bash
# 1. 购买5个种子（花费10金币）
# 货币：100 -> 90

# 2. 早晨：种植小麦（消耗1种子20体力）
# 种子：5 -> 4，体力：100 -> 80，获得5小麦

# 3. 中午：种植小麦（消耗1种子20体力）
# 种子：4 -> 3，体力：80 -> 60，获得5小麦

# 4. 晚上：出售10小麦给商人（获得80金币）
# 小麦：10 -> 0，货币：90 -> 170

# 5. 晚上：睡觉（支付10金币租金）
# 货币：170 -> 160，体力：60 -> 90

# 6. 新的一天开始（饥饿扣除10体力）
# 体力：90 -> 80，行动点重置为3
```

## 停止服务

在运行启动脚本的终端按 `Ctrl+C` 即可停止所有服务。

## 故障排查

### 服务无法启动
- 确保conda环境已激活：`conda activate distribu-town`
- 检查端口是否被占用：`lsof -i :50051` 或 `lsof -i :5000`

### 节点注册失败
- 确保协调器先启动
- 等待2-3秒后再启动其他节点

### gRPC代码未生成
```bash
cd architecture1_grpc
conda activate distribu-town
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/town.proto
```

## 下一步

- 查看 `README.md` 了解详细的系统设计
- 修改 `common/models.py` 调整游戏参数
- 添加更多村民节点测试scalability
- 查看性能测试结果对比两种架构

