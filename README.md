# 分布式虚拟小镇 (Distributed Virtual Town)

一个分布式多智能体虚拟小镇模拟系统，实现了两种不同的系统架构和通信模型。

## 项目概述

这是一个模拟虚拟小镇的分布式系统，每个村民作为独立的节点运行。村民有不同的职业，可以进行生产、交易等活动。系统实现了全局时间同步和资源管理。

## 五个功能需求

1. **村民管理** - 创建和管理虚拟村民（捏人系统）
2. **生产系统** - 不同职业进行生产活动（木工→住房，农夫→小麦，厨师→面包）
3. **交易系统** - 村民之间及与商人的交易
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
- **晚上**：1行动点（可睡眠）

规则：
- 生产活动消耗1行动点和体力
- 交易和吃饭不消耗行动点
- 晚上睡眠恢复体力（需要住房）
- 不睡眠工作额外消耗20体力
- 每天结束扣除10体力（饥饿）

## 快速启动

### 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.9+（本地运行）

### 运行架构1（gRPC微服务）

```bash
cd architecture1_grpc
docker-compose up --build
```

访问控制面板：`http://localhost:8080`

### 运行架构2（RESTful HTTP）

```bash
cd architecture2_rest
docker-compose up --build
```

访问控制面板：`http://localhost:8081`

## 本地开发

### 架构1 - gRPC

```bash
# 安装依赖
cd architecture1_grpc
pip install -r requirements.txt

# 生成gRPC代码
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/town.proto

# 运行服务
python coordinator.py
python merchant.py
python villager.py --name "Alice" --occupation "farmer"
```

### 架构2 - REST

```bash
# 安装依赖
cd architecture2_rest
pip install -r requirements.txt

# 运行服务
python coordinator.py
python merchant.py
python villager.py --name "Bob" --occupation "chef"
```

## API示例

### 架构1 - gRPC

使用gRPC客户端调用（见`architecture1_grpc/client.py`）

### 架构2 - REST

```bash
# 创建村民
curl -X POST http://localhost:5001/villager \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","occupation":"farmer","gender":"female","personality":"hardworking"}'

# 查询村民状态
curl http://localhost:5001/villager/Alice

# 执行生产
curl -X POST http://localhost:5001/action/produce

# 交易
curl -X POST http://localhost:5001/action/trade \
  -H "Content-Type: application/json" \
  -d '{"target":"merchant","item":"wheat","quantity":5}'
```

## 性能测试

```bash
# 测试架构1
cd performance_tests
python test_grpc.py

# 测试架构2
python test_rest.py

# 生成对比报告
python compare_results.py
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
├── architecture2_rest/          # 架构2：RESTful+HTTP
│   ├── coordinator.py           # 时间协调器
│   ├── merchant.py              # 商人节点
│   ├── villager.py              # 村民节点
│   ├── client.py                # 测试客户端
│   ├── Dockerfile
│   └── docker-compose.yml
├── common/                      # 公共代码
│   └── models.py                # 数据模型
├── performance_tests/           # 性能测试
│   ├── test_grpc.py
│   ├── test_rest.py
│   └── compare_results.py
└── README.md
```

## 开发日志

使用AI工具（Claude/Cursor）协助：
- 系统架构设计
- gRPC和REST API实现
- Docker配置优化
- 性能测试脚本

## 许可证

MIT License

