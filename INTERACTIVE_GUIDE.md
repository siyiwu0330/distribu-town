# 交互式多终端控制指南

这个指南将教你如何在不同终端运行不同的村民节点，并通过CLI进行交互控制。

## 🎮 场景：多玩家模拟

想象你和朋友一起玩这个虚拟小镇：
- **终端1**: 运行协调器和商人（系统管理员）
- **终端2**: Alice（农夫） - 你控制
- **终端3**: Bob（厨师） - 朋友控制
- **终端4**: Charlie（木工） - 另一个朋友控制

## 📋 完整步骤

### 准备工作

所有终端都需要激活环境：
```bash
conda activate distribu-town
cd /home/siyi/projects/distribu-town
```

---

### 终端1：启动基础设施（协调器 + 商人）

```bash
# 启动协调器
cd architecture2_rest
python coordinator.py --port 5000 &

# 等待2秒
sleep 2

# 启动商人
python merchant.py --port 5001 --coordinator localhost:5000 &

echo "基础设施已启动！"
```

保持这个终端运行，你会看到所有系统消息。

---

### 终端2：Alice（农夫）

**步骤1：启动村民节点**
```bash
cd /home/siyi/projects/distribu-town/architecture2_rest
conda activate distribu-town
python villager.py --port 5002 --id alice --coordinator localhost:5000
```

**步骤2：在新终端打开CLI控制台**

打开一个新终端：
```bash
cd /home/siyi/projects/distribu-town/architecture2_rest
conda activate distribu-town
python interactive_cli.py --port 5002
```

**步骤3：创建Alice并开始游戏**
```
> create
名字: Alice
职业: farmer
性别: female  
性格: 勤劳的农夫

> info
> prices
> buy seed 5
> produce
> info
```

---

### 终端3：Bob（厨师）

**步骤1：启动村民节点**
```bash
cd /home/siyi/projects/distribu-town/architecture2_rest
conda activate distribu-town
python villager.py --port 5003 --id bob --coordinator localhost:5000
```

**步骤2：在新终端打开CLI控制台**
```bash
cd /home/siyi/projects/distribu-town/architecture2_rest
conda activate distribu-town
python interactive_cli.py --port 5003
```

**步骤3：创建Bob**
```
> create
名字: Bob
职业: chef
性别: male
性格: 热情的厨师

> info
> buy wheat 10     # 买小麦（简化，实际应该从Alice买）
> produce          # 制作面包
```

---

### 终端4：Charlie（木工）

**步骤1：启动村民节点**
```bash
cd /home/siyi/projects/distribu-town/architecture2_rest
conda activate distribu-town
python villager.py --port 5004 --id charlie --coordinator localhost:5000
```

**步骤2：在新终端打开CLI控制台**
```bash
cd /home/siyi/projects/distribu-town/architecture2_rest
conda activate distribu-town
python interactive_cli.py --port 5004
```

**步骤3：创建Charlie**
```
> create
名字: Charlie
职业: carpenter
性别: male
性格: 细心的木工

> buy wood 20
> produce
> info
```

---

## 🎯 典型游戏流程

### Alice的一天（农夫）

```bash
# 终端：Alice CLI
> info                  # 查看初始状态
> prices               # 查看价格
> buy seed 5           # 购买5个种子（花费10金币）
> produce              # 种植（获得5小麦，消耗1种子20体力）
> produce              # 再种植一次
> produce              # 第三次种植
> info                 # 查看状态（应该有15小麦，体力40）
> sell wheat 10        # 出售10小麦（获得80金币）
> time                 # 查看当前时间
```

### Bob的一天（厨师）

```bash
# 终端：Bob CLI
> info
> buy wheat 9          # 购买9小麦（实际游戏中应该从Alice买）
> produce              # 制作面包（3小麦→2面包）
> produce              # 再做一次
> produce              # 第三次
> info                 # 现在有6个面包
> sell bread 5         # 出售5个面包给商人
```

### Charlie的一天（木工）

```bash
# 终端：Charlie CLI
> info
> buy wood 20          # 购买20木材（花费100金币）
> produce              # 建造房屋（10木材→1房屋，30体力）
> info                 # 查看房屋
```

### 晚上时间

在任意一个终端（比如Alice）：
```bash
> advance              # 推进到中午
> advance              # 推进到晚上
> sleep                # Charlie睡觉（有房子，免费）
```

在Alice的终端：
```bash
> sleep                # Alice睡觉（需要支付10金币租房）
```

### 新的一天

```bash
> advance              # 推进到新一天
> info                 # 查看状态（体力-10因为饥饿，行动点重置）
```

---

## 🎮 CLI命令速查表

### 基本命令
| 命令 | 说明 |
|------|------|
| `info` 或 `i` | 查看村民状态 |
| `time` 或 `t` | 查看当前时间 |
| `advance` 或 `a` | 推进时间 |
| `prices` 或 `p` | 查看商人价格 |
| `help` 或 `h` | 显示帮助 |
| `quit` 或 `q` | 退出 |

### 操作命令
| 命令 | 说明 | 示例 |
|------|------|------|
| `create` | 创建村民 | `create` |
| `produce` 或 `work` | 执行生产 | `produce` |
| `buy <物品> <数量>` | 购买 | `buy seed 5` |
| `sell <物品> <数量>` | 出售 | `sell wheat 10` |
| `sleep` 或 `rest` | 睡眠 | `sleep` |

### 物品名称
- `seed` - 种子
- `wheat` - 小麦
- `bread` - 面包
- `wood` - 木材
- `house` - 住房

---

## 🚀 快速启动脚本

我为你创建了快速启动脚本：

### 启动所有基础服务
```bash
cd /home/siyi/projects/distribu-town
bash start_interactive.sh
```

然后在不同终端连接到不同的村民：
```bash
# 终端1
python architecture2_rest/interactive_cli.py --port 5002

# 终端2
python architecture2_rest/interactive_cli.py --port 5003

# 终端3
python architecture2_rest/interactive_cli.py --port 5004
```

---

## 💡 使用技巧

### 1. 使用tmux分屏
```bash
# 安装tmux（如果没有）
sudo apt install tmux

# 启动tmux
tmux

# 分屏快捷键
Ctrl+b "    # 水平分屏
Ctrl+b %    # 垂直分屏
Ctrl+b 方向键  # 切换窗格
```

### 2. 保持服务运行在后台
```bash
# 使用nohup
nohup python villager.py --port 5002 --id alice > alice.log 2>&1 &

# 查看日志
tail -f alice.log
```

### 3. 批量启动
创建一个启动脚本（已为你准备好）：
```bash
bash start_interactive.sh
```

---

## 🎬 演示场景示例

### 场景1：完整的生产链

**Alice（农夫）生产小麦**
```
> buy seed 10
> produce
> produce
> produce
```

**Bob（厨师）从Alice购买并制作面包**
```
> buy wheat 9
> produce
> produce
> produce
```

**所有人查看状态**
```
> info
> time
```

### 场景2：建造和租房

**Charlie建造房屋**
```
> buy wood 20
> produce
> info         # 有1个房屋
```

**时间推进到晚上**
```
> advance
> advance
```

**Charlie免费睡觉（有房子）**
```
> sleep
> info         # 体力恢复，货币不变
```

**Alice需要租房**
```
> sleep
> info         # 体力恢复，货币-10
```

---

## 🐛 故障排查

### 问题1：无法连接到村民节点
**原因**: 村民节点未启动
**解决**: 
```bash
python villager.py --port 5002 --id alice
```

### 问题2：村民未初始化
**原因**: 没有创建村民
**解决**: 在CLI中输入 `create` 命令

### 问题3：交易失败
**原因**: 
- 货币不足
- 物品不足
- 商人不出售/收购该物品

**解决**: 
- 输入 `info` 查看资产
- 输入 `prices` 查看可交易物品

### 问题4：端口被占用
**解决**:
```bash
# 查找占用端口的进程
lsof -i :5002

# 终止进程
kill <PID>
```

---

## 📊 系统架构图

```
┌─────────────────────────────────────────────────┐
│            时间协调器 (localhost:5000)            │
│          商人节点 (localhost:5001)              │
└──────────────┬──────────────────────────────────┘
               │
    ┌──────────┼──────────┬──────────┐
    │          │          │          │
┌───▼───┐  ┌──▼───┐  ┌───▼───┐  ┌──▼───┐
│ Alice │  │ Bob  │  │Charlie│  │Diana │
│ :5002 │  │:5003 │  │ :5004 │  │:5005 │
└───┬───┘  └──┬───┘  └───┬───┘  └──┬───┘
    │          │          │          │
┌───▼───┐  ┌──▼───┐  ┌───▼───┐  ┌──▼───┐
│  CLI  │  │ CLI  │  │  CLI  │  │ CLI  │
└───────┘  └──────┘  └───────┘  └──────┘
```

---

## 🎉 开始游戏！

1. **启动基础服务**: 运行 `bash start_interactive.sh`
2. **连接村民**: 在新终端运行 `python interactive_cli.py --port 5002`
3. **创建角色**: 输入 `create` 
4. **开始游戏**: 输入 `help` 查看所有命令

祝你玩得愉快！🎮

