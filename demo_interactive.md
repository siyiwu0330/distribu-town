# 交互式多终端演示

这是一个完整的交互式演示场景。

## 场景：三个村民的一天

### 准备（终端0）

启动所有服务：
```bash
cd /home/siyi/projects/distribu-town
conda activate distribu-town
bash start_interactive.sh
```

---

### 终端1：Alice（农夫）

**连接到Alice**
```bash
python architecture2_rest/interactive_cli.py --port 5002
```

**游戏流程**
```
[Day 1 - morning] > create
名字: Alice
职业: farmer
性别: female
性格: 勤劳的农夫

[Day 1 - morning] > prices
商人出售:
  wood: 5金币
  seed: 2金币
商人收购:
  wheat: 8金币
  bread: 15金币
  house: 150金币

[Day 1 - morning] > buy seed 5
✓ 购买成功: 5x seed, 花费 10

[Day 1 - morning] > info
==================================================
  Alice - farmer
==================================================
性别: female
性格: 勤劳的农夫
体力: 100/100
行动点: 3/3
💰 货币: 90
📦 物品:
   - seed: 5

[Day 1 - morning] > produce
✓ 生产成功: 5x wheat
体力: 80/100
货币: 90
物品: seed: 4, wheat: 5

[Day 1 - morning] > produce
✓ 生产成功: 5x wheat

[Day 1 - morning] > produce
✓ 生产成功: 5x wheat

[Day 1 - morning] > info
体力: 40/100
货币: 90
物品: seed: 2, wheat: 15

[Day 1 - morning] > sell wheat 10
✓ 出售成功: 10x wheat, 获得 80
货币: 170
物品: seed: 2, wheat: 5
```

---

### 终端2：Bob（厨师）

**连接到Bob**
```bash
python architecture2_rest/interactive_cli.py --port 5003
```

**游戏流程**
```
[Day 1 - morning] > create
名字: Bob
职业: chef
性别: male
性格: 热情的厨师

[Day 1 - morning] > info
体力: 100/100
货币: 100

# 注意：实际游戏中Bob应该从Alice购买小麦
# 但村民间交易暂未实现，所以从商人买（商人不卖小麦是设计）
# 为了演示，我们假设Bob找Alice买了小麦

[Day 1 - morning] > info
# 假设通过某种方式获得了小麦

[Day 1 - morning] > produce
# 需要3小麦才能制作2面包
```

---

### 终端3：Charlie（木工）

**连接到Charlie**
```bash
python architecture2_rest/interactive_cli.py --port 5004
```

**游戏流程**
```
[Day 1 - morning] > create
名字: Charlie
职业: carpenter
性别: male
性格: 细心的木工

[Day 1 - morning] > buy wood 20
✓ 购买成功: 20x wood, 花费 100
货币: 0
物品: wood: 20

[Day 1 - morning] > produce
✓ 生产成功: 1x house
体力: 70/100
货币: 0
物品: wood: 10, house: 1

[Day 1 - morning] > info
Charlie现在有自己的房子了！
```

---

### 推进时间（任意终端）

```
[Day 1 - morning] > advance
✓ 时间推进: Time advanced to Day 1 noon
当前时间: 1天 noon

[Day 1 - noon] > advance
✓ 时间推进: Time advanced to Day 1 evening
当前时间: 1天 evening
```

---

### 晚上睡觉

**Charlie（有房子）**
```
[Day 1 - evening] > sleep
✓ 睡眠成功，恢复体力 30
体力: 100/100
货币: 0  # 没有扣钱
```

**Alice（没房子）**
```
[Day 1 - evening] > sleep
Alice支付租金 10
✓ 睡眠成功，恢复体力 30
体力: 70/100
货币: 160  # 扣了10金币租金
```

---

### 新的一天

```
[Day 1 - evening] > advance
✓ 时间推进: Time advanced to Day 2 morning
当前时间: 2天 morning

[Day 2 - morning] > info
# 所有村民饥饿-10体力，行动点重置为3
体力: 60/100  # Charlie是90
行动点: 3/3
```

---

## 命令速查

### 创建角色
```
> create
```

### 查看信息
```
> info          # 村民状态
> time          # 当前时间
> prices        # 商人价格
> help          # 所有命令
```

### 交易
```
> buy seed 5        # 买5个种子
> buy wood 20       # 买20个木材
> sell wheat 10     # 卖10个小麦
> sell bread 3      # 卖3个面包
```

### 操作
```
> produce       # 生产（根据职业）
> sleep         # 睡觉恢复体力
> advance       # 推进时间
```

### 退出
```
> quit
```

---

## 职业生产规则

| 职业 | 输入 | 输出 | 体力消耗 |
|------|------|------|----------|
| 农夫 (farmer) | 1种子 | 5小麦 | 20 |
| 厨师 (chef) | 3小麦 | 2面包 | 15 |
| 木工 (carpenter) | 10木材 | 1住房 | 30 |

---

## 经济系统

### 商人价格

**出售（玩家购买）**
- 木材: 5金币
- 种子: 2金币

**收购（玩家出售）**
- 小麦: 8金币
- 面包: 15金币
- 住房: 150金币

### 其他费用
- 租房（没有自己房子时睡觉）: 10金币/次

---

## 游戏目标

在保持体力不归零的情况下，尽可能积累财富！

策略：
1. **农夫**: 种植小麦→出售→买种子→继续种植
2. **厨师**: 买小麦→做面包→出售（利润更高）
3. **木工**: 造房子→自己用省租金 或 卖给商人赚大钱

---

## 提示

- 每天3个行动点（早中晚）
- 生产消耗1行动点，交易不消耗
- 晚上必须睡觉恢复体力
- 没房子要付租金
- 不睡觉第二天额外扣20体力
- 每天因饥饿扣10体力

玩得愉快！🎮

