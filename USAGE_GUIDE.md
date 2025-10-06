# 使用指南 - 改进版

## 🎯 核心改进

### 1. 灵活的节点创建
- 基础设施（协调器+商人）自动启动
- 村民节点按需手动创建
- 每个村民一个独立终端

### 2. 清晰的时间流逝机制
- **3个行动点 = 3次生产机会**
- 生产消耗行动点，交易和睡眠不消耗
- 行动点用完时会有明确提示
- 推进时间是全局操作，需要确认

---

## 🚀 快速开始（4个终端）

### 终端1：启动基础设施

```bash
cd /home/siyi/projects/distribu-town
conda activate distribu-town
bash start_interactive.sh
```

你会看到：
```
✓ 基础设施已启动！
  协调器:  http://localhost:5000
  商人:    http://localhost:5001

创建村民节点：
  在新终端中启动村民节点...
```

**保持这个终端运行！**

---

### 终端2：启动Alice节点 + 控制

**步骤1：启动村民节点**
```bash
cd /home/siyi/projects/distribu-town/architecture2_rest
conda activate distribu-town
python villager.py --port 5002 --id alice
```

你会看到：
```
[Villager-alice] 节点初始化
[Villager-alice] REST村民节点启动在端口 5002
[Villager-alice] 成功注册到协调器: localhost:5000
```

**步骤2：在新终端（或tmux分屏）连接CLI**
```bash
cd /home/siyi/projects/distribu-town
conda activate distribu-town
python architecture2_rest/interactive_cli.py --port 5002
```

**步骤3：创建村民并游戏**
```
[Day 1 - morning] > create
名字: Alice
职业: farmer
性别: female
性格: 勤劳的农夫

[Day 1 - morning] > help
[Day 1 - morning] > buy seed 5
[Day 1 - morning] > produce
💡 提示: 剩余 2 个行动点

[Day 1 - morning] > produce
💡 提示: 剩余 1 个行动点

[Day 1 - morning] > produce
⚠️  行动点已用完！
   当前时段的工作已完成，你可以：
   1. 进行不消耗行动点的操作（交易、睡眠）
   2. 输入 'advance' 推进到下一个时段

[Day 1 - morning] > sell wheat 10
[Day 1 - morning] > advance
⚠️  推进时间将影响所有村民！确认推进？(y/n): y
✓ 时间已推进！
☀️  已到中午
```

---

### 终端3：启动Bob节点 + 控制

```bash
# 启动节点
cd /home/siyi/projects/distribu-town/architecture2_rest
python villager.py --port 5003 --id bob

# 在另一个终端连接
python architecture2_rest/interactive_cli.py --port 5003
```

```
> create
名字: Bob
职业: chef
性格: 热情的厨师

> info
🎯 行动点: 3/3 [早晨 - 新时段开始]
```

---

### 终端4：启动Charlie节点 + 控制

```bash
# 启动节点
cd /home/siyi/projects/distribu-town/architecture2_rest
python villager.py --port 5004 --id charlie

# 在另一个终端连接
python architecture2_rest/interactive_cli.py --port 5004
```

```
> create
名字: Charlie
职业: carpenter
性格: 细心的木工

> buy wood 20
> produce
> info
📦 物品:
   - house: 1
```

---

## ⏰ 时间系统详解

### 时间流逝规则

```
Day 1
├── 早晨 (morning)   - 3行动点
├── 中午 (noon)      - 3行动点  
└── 晚上 (evening)   - 3行动点，可睡眠

Day 2
├── 早晨 (morning)   - 新一天开始，扣除饥饿体力
...
```

### 行动点机制

**消耗行动点的操作（每次1点）：**
- ✅ `produce` - 生产

**不消耗行动点的操作：**
- ✅ `buy` - 购买
- ✅ `sell` - 出售
- ✅ `sleep` - 睡眠
- ✅ `info` - 查看状态
- ✅ `time` - 查看时间
- ✅ `prices` - 查看价格

### 行动点状态提示

查看 `info` 时会显示：
```
🎯 行动点: 3/3 [早晨 - 新时段开始]     ← 满行动点
🎯 行动点: 2/3 [已工作1次]            ← 已使用1点
🎯 行动点: 1/3 [已工作2次]            ← 已使用2点
🎯 行动点: 0/3 [⚠️ 行动点用完，建议推进时间] ← 该推进了
```

### 推进时间

**命令：** `advance` 或 `a`

**效果：**
- ⚠️  这是**全局操作**，会影响所有村民
- 需要确认才能执行
- 所有村民同步推进到下一时段
- 新时段所有村民行动点重置为3

**推进时会看到：**
```
[Day 1 - morning] > advance
当前时间: Day 1 - morning
⚠️  推进时间将影响所有村民！确认推进？(y/n): y

✓ 时间已推进！
   Time advanced to Day 1 noon
☀️  已到中午

你的村民状态更新：
==================================================
  Alice - farmer
==================================================
⚡ 体力: 80/100
🎯 行动点: 3/3 [早晨 - 新时段开始]
```

---

## 🎮 典型游戏流程

### 场景：Alice的完整一天

```bash
# === 早晨 ===
> create    # 创建Alice（农夫）
> buy seed 5
> produce   # 种植1 (行动点: 3 → 2)
> produce   # 种植2 (行动点: 2 → 1)
> produce   # 种植3 (行动点: 1 → 0)
⚠️  行动点已用完！

> sell wheat 10  # 出售（不消耗行动点）
> info           # 查看状态

# === 推进到中午 ===
> advance
确认？y
☀️  已到中午

> buy seed 3
> produce   # 继续种植
> produce
> produce
⚠️  行动点已用完！

# === 推进到晚上 ===
> advance
确认？y
🌙 已到晚上
   - 可以睡眠恢复体力

> sell wheat 15
> sleep     # 睡眠（需要租房，扣10金币）
✓ 睡眠成功，恢复体力 30

# === 推进到新一天 ===
> advance
确认？y
🌅 新的一天开始！
   - 所有村民行动点重置为3
   - 每日饥饿扣除10体力

> info
⚡ 体力: 90/100  (恢复30 - 饥饿10 = 净恢复20)
🎯 行动点: 3/3
```

---

## 🎯 多人协作场景

### 场景1：分工合作

**Alice（农夫）：**
```
> produce  # 种小麦
> produce
> produce
> advance  # 推进时间
```

**Bob（厨师）：**
```
> buy wheat 9   # 等Alice种出小麦（简化）
> produce       # 做面包
> produce
> produce
```

**Charlie（木工）：**
```
> buy wood 20
> produce  # 建房子
> info     # 有房子了！
```

### 场景2：时间同步

当一个玩家推进时间：
```
Alice终端:
> advance
⚠️  推进时间将影响所有村民！确认推进？y
✓ 时间已推进到中午
```

**所有其他玩家终端会收到时间推进通知：**
```
Bob终端: （villager.py日志）
[Villager-bob] 时间推进: Day 1 noon
[Villager-bob] 新时段！行动点: 3

Charlie终端:
[Villager-charlie] 时间推进: Day 1 noon
```

**其他玩家输入命令时会看到更新的时间：**
```
[Day 1 - noon] > info
🎯 行动点: 3/3 [早晨 - 新时段开始]
```

---

## 📋 命令速查表

| 命令 | 简写 | 说明 | 消耗行动点 |
|------|------|------|------------|
| `create` | - | 创建村民 | ❌ |
| `info` | `i` | 查看状态 | ❌ |
| `time` | `t` | 查看时间 | ❌ |
| `prices` | `p` | 查看价格 | ❌ |
| `help` | `h`, `?` | 显示帮助 | ❌ |
| `produce` | `work` | 生产 | ✅ 1点 |
| `buy <item> <qty>` | - | 购买 | ❌ |
| `sell <item> <qty>` | - | 出售 | ❌ |
| `sleep` | `rest` | 睡眠 | ❌ |
| `advance` | `a` | 推进时间 | ❌（全局） |
| `quit` | `q`, `exit` | 退出 | - |

---

## 💡 使用技巧

### 1. 使用tmux管理多个终端

```bash
# 启动tmux
tmux

# 分屏
Ctrl+b "    # 水平分屏
Ctrl+b %    # 垂直分屏
Ctrl+b 方向键  # 切换窗格
Ctrl+b x    # 关闭当前窗格
```

推荐布局：
```
┌──────────────┬──────────────┐
│   基础设施    │  Alice CLI   │
│  (保持运行)   │              │
├──────────────┼──────────────┤
│   Bob CLI    │ Charlie CLI  │
│              │              │
└──────────────┴──────────────┘
```

### 2. 查看系统日志

```bash
# 协调器日志
tail -f /tmp/coordinator.log

# 商人日志
tail -f /tmp/merchant.log

# 村民节点的日志在运行节点的终端可以看到
```

### 3. 快速创建多个村民

创建一个脚本：
```bash
#!/bin/bash
# start_villagers.sh

tmux new-session -d -s town
tmux send-keys "python villager.py --port 5002 --id alice" C-m
tmux split-window -h
tmux send-keys "python villager.py --port 5003 --id bob" C-m
tmux split-window -v
tmux send-keys "python villager.py --port 5004 --id charlie" C-m
tmux attach-session -t town
```

---

## 🐛 常见问题

### Q: 为什么我的行动点没有恢复？
A: 行动点只在时间推进时恢复。使用 `advance` 命令推进时间。

### Q: 推进时间影响所有人，怎么协调？
A: 这是分布式系统的设计特点。建议：
- 多人游戏时，约定一个"时间管理员"
- 或在群聊中沟通"大家都准备好了吗"
- 这模拟了真实分布式系统中的协调问题

### Q: 村民节点没有连接到协调器？
A: 确保：
1. 先启动基础设施 (`bash start_interactive.sh`)
2. 等待2秒后再启动村民节点
3. 检查端口没有被占用

### Q: 如何停止所有服务？
A: 
- 在基础设施终端按 `Ctrl+C`
- 在每个村民节点终端按 `Ctrl+C`
- 在CLI终端输入 `quit`

---

## 🎓 学习要点

通过这个系统，你可以理解：

1. **分布式节点**: 每个村民是独立的服务
2. **全局协调**: 时间由协调器统一管理
3. **状态同步**: 时间推进时通知所有节点
4. **资源管理**: 行动点、体力、货币的管理
5. **异步操作**: 不同玩家可以并行操作

---

祝你玩得愉快！🎮

