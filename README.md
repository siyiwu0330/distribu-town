# 分布式虚拟小镇 (Distributed Virtual Town)

一个分布式多智能体虚拟小镇模拟系统，实现了两种不同的系统架构和通信模型。支持多终端交互式操作，每个村民作为独立的节点运行，可以进行生产、交易、时间同步等活动。

## 项目概述

这是一个模拟虚拟小镇的分布式系统，每个村民作为独立的节点运行。村民有不同的职业（农夫、厨师、木工），可以进行生产、交易等活动。系统实现了全局时间同步和资源管理，支持P2P村民间交易和与商人的交易。

## 五个功能需求

1. **村民管理** - 创建和管理虚拟村民（捏人系统）
2. **生产系统** - 不同职业进行生产活动（木工→住房，农夫→小麦，厨师→面包）
3. **交易系统** - 村民之间及与商人的交易，村民之间的交易
4. **时间同步** - 全局时间管理（早中晚三个时段）
5. **资源管理** - 管理体力、货币、物品（木材、小麦、面包、住房）

## 两种系统架构

### 架构1：微服务架构 + gRPC
- 位置：`architecture1_grpc/`
- 特点：
  - 每个村民作为独立的gRPC服务
  - 中央时间协调器管理全局时钟
  - 使用Protocol Buffers定义消息格式
  - 高效的二进制通信

### 架构2：RESTful资源导向 + HTTP
- 位置：`architecture2_rest/`
- 特点：
  - 每个村民暴露REST API端点
  - 使用HTTP JSON进行通信
  - 资源导向设计
  - 易于测试和调试

## 快速开始

### 1. 配置环境

```bash
# 创建conda环境
conda env create -f environment.yml
conda activate distribu-town

# 或使用pip安装依赖
pip install flask requests grpcio protobuf numpy matplotlib openai
```

### 2. 启动基础服务

```bash
cd architecture2_rest
bash start_services.sh
```

这将启动：
- **Coordinator** (端口5000) - 时间协调器
- **Merchant** (端口5001) - 商人服务

### 3. 启动村民节点

```bash
# 启动第一个村民节点
./start_villager.sh 5002 node1

# 启动第二个村民节点（新终端）
./start_villager.sh 5003 node2
```

### 4. 连接村民节点

#### 使用交互式CLI控制村民：

```bash
# 连接到node1 (端口5002)
python interactive_cli.py --port 5002

# 连接到node2 (端口5003) - 新终端
python interactive_cli.py --port 5003
```

#### 使用AI Agent自动控制村民：

```bash
# AI控制node1
python ai_villager_agent.py --port 5002 --react

# AI控制node2 - 新终端  
python ai_villager_agent.py --port 5003 --react
```

## 系统架构

```
┌─────────────────┐
│ Time Coordinator│ (同步各节点的时间)
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    │         │        │        │
┌───▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐
│Merchant│ │Farmer│ │ Chef │ │Carpenter│
└────────┘ └──────┘ └──────┘ └────────┘
```

## 村民属性

- **体力**：0-100，每天因饥饿-10，工作消耗，睡眠恢复
- **职业**：木工、农夫、厨师（商人为系统NPC）
- **性别**：男/女
- **性格**：自定义
- **资产**：货币和物品（木材、小麦、面包、住房）

## 基本操作

### 创建村民
在CLI中输入 `create`，然后按提示输入：
- 名字
- 职业（farmer/chef/carpenter）
- 性别（male/female）
- 性格描述

### 常用命令
- `info` - 查看村民状态
- `produce` - 生产物品
- `buy <物品> <数量>` - 从商人购买
- `sell <物品> <数量>` - 出售给商人
- `sleep` - 睡眠恢复体力
- `eat` - 吃面包恢复体力
- `prices` - 查看商人价格
- `help` - 查看所有命令

### 村民间交易
- `trade <节点ID> buy <物品> <数量> <价格>` - 向其他村民购买
- `trade <节点ID> sell <物品> <数量> <价格>` - 向其他村民出售
- `mytrades` - 查看所有交易
- `accept <交易ID>` - 接受交易请求
- `confirm <交易ID>` - 确认交易

### 消息系统
- `send <节点ID> <消息>` - 发送私聊消息
- `broadcast <消息>` - 发送广播消息
- `messages` - 查看消息列表

## 职业系统

### 商人（Merchant）
- 系统NPC，固定物价
- 提供基础资源（种子、木材）
- 收购产品（小麦、面包）

### 木工（Carpenter）
- 消耗：木材 + 体力
- 生产：住房
- 收入：建造委托费

### 农夫（Farmer）
- 消耗：种子 + 体力
- 生产：小麦
- 收入：出售小麦

### 厨师（Chef）
- 消耗：小麦 + 体力
- 生产：面包
- 收入：出售面包

## 时间系统

每天分为三个时段：
- **早晨**：1行动点
- **中午**：1行动点
- **晚上**：1行动点

规则：
- 生产活动消耗1行动点和体力
- 交易和吃饭不消耗行动点
- 睡眠恢复体力（需要住房）
- 晚间不睡眠工作额外消耗20体力
- 每天结束扣除10体力（饥饿）

## 示例工作流程

### 典型的一天
1. **早上**：购买种子 → 生产小麦
2. **中午**：吃面包恢复体力 → 继续生产
3. **晚上**：睡眠恢复体力

### 多村民协作
1. 农夫生产小麦
2. 厨师购买小麦制作面包
3. 木工建造住房
4. 村民间进行P2P交易获得更好价格

### 创建村民节点

在新终端中启动村民节点（每个村民一个终端）：

```bash
# 终端A：启动node1节点
cd /path/to/distribu-town/architecture2_rest
conda activate distribu-town
python villager.py --port 5002 --id node1

# 终端B：启动node2节点  
python villager.py --port 5003 --id node2
```

### 连接CLI控制台

启动村民节点后，在另一个终端连接CLI控制：

```bash
# 控制node1（确保node1节点已启动在5002端口）
python interactive_cli.py --port 5002

# 控制node2（确保node2节点已启动在5003端口）
python interactive_cli.py --port 5003
```

## 使用指南

### CLI命令列表

在交互式CLI中，您可以使用以下命令：

**基本命令:**
- `info` / `i` - 查看村民状态
- `time` / `t` - 查看当前时间
- `status` / `s` - 查看所有村民的提交状态
- `prices` / `p` - 查看商人价格
- `help` / `h` / `?` - 显示帮助
- `quit` / `q` / `exit` - 退出

**村民操作:**
- `create` - 创建新村民
- `produce` / `work` - 执行生产（自动提交work）
- `sleep` / `rest` - 睡眠恢复体力（自动提交sleep）
- `idle` - 跳过当前时段（提交idle）
- `eat` / `e` - 吃面包恢复体力（不消耗行动，不提交）
- `buy <物品> <数量>` - 从商人购买
- `sell <物品> <数量>` - 出售给商人

**村民间交易（P2P）:**
- `trade <村民> buy <物品> <数量> <价格>` - 向其他村民购买
- `trade <村民> sell <物品> <数量> <价格>` - 向其他村民出售
- `trades` - 查看收到的交易请求
- `mytrades` - 查看自己发起的交易请求
- `accept <ID>` - 接受指定的交易请求
- `reject <ID>` - 拒绝指定的交易请求
- `confirm <ID>` - 确认并完成自己发起的交易
- `cancel <ID>` - 取消自己发起的交易

### 典型工作流程

**早上时段:**
```bash
create                    # 创建村民（如果未创建）
buy seed 10              # 购买种子（不消耗行动）
produce                   # 生产小麦（自动提交work）
# 等待其他村民提交行动...
```

**中午时段:**
```bash
eat                      # 吃面包恢复体力（不消耗行动）
produce                  # 再次生产（自动提交work）
# 等待其他村民提交行动...
```

**晚上时段:**
```bash
sleep                    # 睡眠（自动提交sleep）
# 等待其他村民提交行动...
```

**村民间交易:**
```bash
# 村民A发起交易
trade node2 buy wheat 5 10
mytrades                  # 查看发送的请求

# 村民B查看并接受
trades                    # 查看收到的请求
accept trade_0            # 接受交易

# 村民A完成交易
mytrades                  # 查询交易请求是否被接受
confirm trade_0           # 完成交易
```

## 系统特性

### 分布式时间同步
- 使用屏障同步（Barrier Synchronization）机制
- 所有村民必须提交行动后，时间才会推进
- 支持早中晚三个时段的时间管理

### P2P交易系统
- 村民间直接交易，不经过协调器
- 支持异步交易请求和响应
- 交易状态实时同步

### 职业生产系统
- **农夫**: 1种子 → 5小麦 (消耗20体力)
- **厨师**: 3小麦 → 2面包 (消耗15体力)  
- **木工**: 10木材 → 1住房 (消耗30体力)

### 物品和资源
- **基础物品**: seed(种子), wheat(小麦), bread(面包), wood(木材), house(住房)
- **特殊物品**: temp_room(临时房间券) - 用于睡眠
- **体力系统**: 0-100，工作消耗，睡眠恢复

## API示例

### REST API调用

```bash
# 创建村民
curl -X POST http://localhost:5002/villager \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","occupation":"farmer","gender":"female","personality":"hardworking"}'

# 查询村民状态
curl http://localhost:5002/villager

# 执行生产
curl -X POST http://localhost:5002/action/produce

# 与商人交易
curl -X POST http://localhost:5002/action/trade \
  -H "Content-Type: application/json" \
  -d '{"target":"merchant","item":"seed","quantity":10}'

# 村民间交易
curl -X POST http://localhost:5002/trade/request \
  -H "Content-Type: application/json" \
  -d '{"target":"node2","item":"wheat","quantity":5,"price":10}'
```

## 项目结构

```
distribu-town/
├── architecture1_grpc/          # 架构1：微服务+gRPC
│   ├── proto/                   # Protocol Buffer定义
│   ├── coordinator.py           # 时间协调器
│   ├── merchant.py              # 商人节点
│   ├── villager.py              # 村民节点
│   ├── client.py                # 测试客户端
│   ├── Dockerfile
│   └── docker-compose.yml
├── architecture2_rest/          # 架构2：RESTful+HTTP（推荐）
│   ├── coordinator.py           # 时间协调器
│   ├── merchant.py              # 商人节点
│   ├── villager.py              # 村民节点
│   ├── interactive_cli.py       # 交互式CLI客户端
│   ├── start_demo.sh            # 演示脚本
│   ├── test_scenario.py         # 测试场景
│   ├── requirements.txt         # Python依赖
│   ├── Dockerfile
│   └── docker-compose.yml
├── common/                      # 公共代码
│   └── models.py                # 数据模型
├── performance_tests/           # 性能测试
│   ├── test_grpc.py
│   ├── test_rest.py
│   └── compare_results.py
├── environment.yml              # Conda环境配置
├── start_interactive.sh         # 交互式启动脚本
├── demo_interactive.md          # 交互式演示说明
├── BARRIER_SYNC_GUIDE.md        # 屏障同步机制说明
└── README.md
```

## 日志和监控

系统运行时会生成以下日志文件：
- `/tmp/coordinator.log` - 协调器日志
- `/tmp/merchant.log` - 商人日志  
- `/tmp/alice.log` - Alice村民日志
- `/tmp/bob.log` - Bob村民日志
- `/tmp/charlie.log` - Charlie村民日志

查看实时日志：
```bash
tail -f /tmp/coordinator.log
tail -f /tmp/merchant.log
```

## 故障排除

### 常见问题

**1. 村民节点无法启动**
```bash
# 检查端口是否被占用
lsof -i :5002

# 检查conda环境
conda activate distribu-town
```

**2. CLI连接失败**
```bash
# 确保村民节点已启动
curl http://localhost:5002/health

# 检查节点状态
python interactive_cli.py --port 5002
```

**3. 交易无法完成**
- 确保两个村民节点都在线
- 检查交易ID是否正确
- 查看日志文件排查问题

**4. 时间不推进**
- 使用`status`命令检查所有村民是否已提交行动
- 确保所有村民节点都连接到协调器

### 调试技巧

```bash
# 查看协调器状态
curl http://localhost:5000/status

# 查看商人价格
curl http://localhost:5001/prices

# 查看村民信息
curl http://localhost:5002/villager
```

## 开发日志

使用AI工具（Claude/Cursor）协助开发：
- 分布式系统架构设计
- REST API和gRPC实现
- 屏障同步机制
- P2P交易系统
- 交互式CLI界面
- Docker配置优化


