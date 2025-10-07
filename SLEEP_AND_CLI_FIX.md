# 睡眠逻辑和CLI提示修复

## 修复内容

### 1. ✅ 修复睡眠逻辑

**问题**：睡眠系统允许没有房子或临时房间券的村民通过支付租金来睡觉，这与游戏设计不符。

**设计要求**：
- 必须拥有 `house`（房子）或 `temp_room`（临时房间券）才能睡觉
- `temp_room` 从商人处购买，每天结算时消耗1个
- 鼓励玩家提前规划住房资源

**修复前的逻辑**：
```python
# 允许三种方式睡觉
if has_house:
    sleep_message = "在自己的房子里睡眠"
elif has_temp_room:
    sleep_message = "使用临时房间券睡眠"
else:
    # ❌ 可以临时租房
    villager.inventory.remove_money(RENT_COST)
    sleep_message = f"支付租金{RENT_COST}金币后睡眠"
```

**修复后的逻辑**：
```python
# 检查是否有房子或临时房间券
has_house = villager.inventory.has_item("house", 1)
has_temp_room = villager.inventory.has_item("temp_room", 1)

if not has_house and not has_temp_room:
    # ✓ 必须有房子或临时房间券
    return jsonify({
        'success': False,
        'message': '没有房子或临时房间券，无法睡眠。请从商人处购买临时房间券或建造房子。'
    }), 400

# 只有两种方式
if has_house:
    sleep_message = "在自己的房子里睡眠"
else:  # has_temp_room
    sleep_message = "使用临时房间券睡眠（将在每日结算时消耗）"
```

**效果**：

#### 场景1：有房子
```bash
[Day 1 - evening] > sleep
✓ 睡眠成功
  在自己的房子里睡眠，恢复体力 30
  当前体力: 100/100
```

#### 场景2：有临时房间券
```bash
[Day 1 - evening] > sleep
✓ 睡眠成功
  使用临时房间券睡眠（将在每日结算时消耗），恢复体力 30
  当前体力: 100/100

# 每日结算时自动消耗
[Day 2 - morning] > info
📦 物品:
   - temp_room: 0  # 已消耗
```

#### 场景3：没有房子和临时房间券
```bash
[Day 1 - evening] > sleep
✗ 错误: 没有房子或临时房间券，无法睡眠。请从商人处购买临时房间券或建造房子。

# 提示用户购买临时房间券
[Day 1 - evening] > buy temp_room 1
✓ 购买成功
  购买了 1x temp_room
  花费: 10金币

[Day 1 - evening] > sleep
✓ 睡眠成功
  使用临时房间券睡眠（将在每日结算时消耗），恢复体力 30
```

---

### 2. ✅ 优化CLI提示信息

**问题**：在有了`mytrades`命令后，一些提示信息仍然引导用户使用`trades`查看自己发起的交易，造成混淆。

**改进**：

#### 改进1：发起交易后的提示

**修复前**：
```bash
[Day 1] > trade node1 buy wheat 5 50
✓ 交易请求已发送
⏳ 等待 node1 接受或拒绝...
💡 提示: 对方需要在CLI中输入 'accept' 或 'reject' 命令
# ❌ 没有提示如何查看状态
```

**修复后**：
```bash
[Day 1] > trade node1 buy wheat 5 50
✓ 交易请求已发送
⏳ 等待 node1 接受或拒绝...
💡 提示: 对方需要在CLI中输入 'accept' 或 'reject' 命令
   使用 'mytrades' 查看此交易的状态  # ✓ 明确指引
```

#### 改进2：接受交易后的提示

**修复前**：
```bash
[Day 1] > accept trade_0
✓ 交易已接受！
  交易ID: trade_0
  等待 test2 完成交易...

💡 对方需要在他的终端执行 'confirm' 来完成交易
# ❌ 可能让用户误以为需要在trades中操作
```

**修复后**：
```bash
[Day 1] > accept trade_0
✓ 交易已接受！
  交易ID: trade_0
  等待 test2 完成交易...

💡 对方会在他的终端看到提醒并执行 'confirm' 来完成交易
# ✓ 更清晰的说明
```

---

## 临时房间券机制

### 购买
```bash
[Day 1] > buy temp_room 3
✓ 购买成功
  购买了 3x temp_room
  花费: 30金币  # 假设每个10金币
```

### 使用
```bash
[Day 1 - evening] > sleep
✓ 睡眠成功
  使用临时房间券睡眠（将在每日结算时消耗），恢复体力 30
  
# temp_room暂时不减少，等待每日结算
[Day 1 - evening] > info
📦 物品:
   - temp_room: 3  # 还有3个
```

### 每日结算（自动）
```python
# 在 Villager.reset_daily() 中
def reset_daily(self):
    # 消耗临时房间券
    if self.inventory.has_item("temp_room", 1):
        self.inventory.remove_item("temp_room", 1)
    
    # 重置其他状态...
    self.has_slept = False
    self.stamina = max(0, self.stamina - DAILY_HUNGER)
```

```bash
# 时间推进到新的一天
[Day 2 - morning] > info
📦 物品:
   - temp_room: 2  # ✓ 自动消耗了1个
```

---

## 游戏策略影响

### 资源规划

玩家现在需要提前规划住房：

1. **短期策略**：购买临时房间券
   - 成本：10金币/晚（商人价格）
   - 优点：灵活，按需购买
   - 缺点：持续成本

2. **长期策略**：建造房子
   - 成本：需要木材和木工服务（一次性）
   - 优点：永久使用，无持续成本
   - 缺点：初期投入大

### 社交互动

鼓励玩家与木工互动：
```bash
# 场景：找木工建房子
[Day 3] > trade carpenter1 buy house 1 100
📤 向 carpenter1 发送交易请求...

# 木工需要有木材和体力
# 建造后出售房子给你
```

---

## 错误处理

### 没有住房无法睡觉
```bash
[Day 1 - evening] > sleep
✗ 错误: 没有房子或临时房间券，无法睡眠。请从商人处购买临时房间券或建造房子。

# 清晰的错误信息，指导用户下一步操作
```

### 临时房间券用完
```bash
[Day 5 - evening] > info
📦 物品: 无  # temp_room已用完

[Day 5 - evening] > sleep
✗ 错误: 没有房子或临时房间券，无法睡眠。请从商人处购买临时房间券或建造房子。

# 提醒用户需要购买
[Day 5 - evening] > buy temp_room 5
✓ 购买成功
```

---

## 相关文件

- `architecture2_rest/villager.py`
  - `sleep()` - 修复睡眠逻辑，移除临时租房
  
- `architecture2_rest/interactive_cli.py`
  - `trade_with_villager()` - 添加mytrades提示
  - `accept_trade_request()` - 优化accept后的提示

- `common/models.py`
  - `Villager.reset_daily()` - 每日消耗temp_room

---

## 测试场景

### 测试1：无住房尝试睡觉
```bash
# 初始状态：无房子，无临时房间券
create
# ... 工作赚钱 ...
sleep
# 预期：失败，提示购买临时房间券或建造房子
```

### 测试2：购买并使用临时房间券
```bash
buy temp_room 2
sleep  # 成功
info   # 查看：temp_room: 2
# 推进到下一天
info   # 查看：temp_room: 1（自动消耗）
```

### 测试3：拥有房子后睡觉
```bash
# 通过交易获得房子
info   # 查看：house: 1
sleep  # 成功，使用房子
# 推进到下一天
info   # 查看：house: 1（不消耗）
```

---

## 总结

✅ **睡眠逻辑修复**: 必须有house或temp_room才能睡觉  
✅ **temp_room机制**: 从商人购买，每日自动消耗  
✅ **CLI提示优化**: 明确引导用户使用mytrades查看状态  
✅ **游戏深度**: 鼓励资源规划和社交互动  

这些修复使游戏机制更加合理，增加了策略深度！🎉

