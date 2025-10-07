# 系统优化更新

## 概述

本次更新解决了三个重要问题，使游戏系统更加平衡和合理。

---

## 1. 行动点机制重构 ⚡

### 问题
之前的设计中，每天早上重置3个行动点，用完就没有了，直到第二天才能恢复。

### 解决方案
改为**每个时段1个行动点**，时间推进时自动刷新：

- **早上 (morning)**: 1个行动点
- **中午 (noon)**: 推进时刷新为1个行动点
- **晚上 (evening)**: 推进时刷新为1个行动点

### 实现细节

**models.py**:
```python
class Villager:
    action_points: int = 1  # 改为1点
    
    def refresh_action_point(self):
        """刷新行动点（每时段调用）"""
        self.action_points = 1
```

**villager.py**:
```python
@app.route('/time/advance', methods=['POST'])
def on_time_advance():
    if data['time_of_day'] == 'morning':
        # 每日重置
        villager.reset_daily()
    else:
        # 每个时段刷新行动点
        villager.refresh_action_point()
```

### 游戏流程示例

```
早上：
> produce        # 生产（消耗1行动点）
> submit work    # 提交，等待时间推进
[时间推进到中午，行动点刷新为1]

中午：
> produce        # 再次生产（消耗1行动点）
> submit work    # 提交
[时间推进到晚上，行动点刷新为1]

晚上：
> sleep          # 睡眠
> submit sleep   # 提交
[时间推进到第二天早上]
```

---

## 2. 体力恢复系统 🍞

### 问题
体力只会下降（饥饿、工作消耗），无法恢复，导致游戏无法持续进行。

### 解决方案
添加**吃面包**功能恢复体力。

### 新增内容

**物品**: `bread` (面包)
- 厨师生产：3小麦 → 2面包
- 商人出售：20金币/个
- 商人收购：15金币/个（厨师可出售）
- 食用效果：恢复30体力

**CLI命令**: `eat` 或 `e`
```bash
> eat
✓ 吃了面包，恢复 30 体力
```

### 实现细节

**models.py**:
```python
BREAD_RESTORE = 30      # 吃面包恢复体力

class Villager:
    def eat_bread(self) -> bool:
        """吃面包恢复体力"""
        if not self.inventory.has_item("bread", 1):
            return False
        self.inventory.remove_item("bread", 1)
        self.restore_stamina(30)
        return True
```

**villager.py**:
```python
@app.route('/action/eat', methods=['POST'])
def eat_food():
    """吃面包恢复体力"""
    success = villager.eat_bread()
    # 返回结果
```

**商人价格表**:
```python
MERCHANT_PRICES = {
    "buy": {
        "bread": 20,      # 玩家可购买
    },
    "sell": {
        "bread": 15,      # 厨师可出售
    }
}
```

---

## 3. 临时租房系统 🏠

### 问题
没有房子的村民必须每晚支付租金（10金币），但这是固定的现金流出，没有优化空间。

### 解决方案
添加**临时房间券**，可以提前购买储备。

### 新增内容

**物品**: `temp_room` (临时房间券)
- 商人出售：15金币/个
- 使用方式：拥有时可用于睡眠
- 消耗时机：每日早上结算时自动消耗1个

### 睡眠优先级

1. **有自己的房子** → 免费睡眠
2. **有临时房间券** → 使用房间券（每日结算时消耗）
3. **都没有但有钱** → 支付10金币租金
4. **什么都没有** → 无法睡眠

### 实现细节

**models.py**:
```python
class ItemType(Enum):
    TEMP_ROOM = "temp_room"  # 临时房间券

MERCHANT_PRICES = {
    "buy": {
        "temp_room": 15,  # 临时房间券
    }
}

class Villager:
    def reset_daily(self):
        """每日重置"""
        # 每日结算消耗临时房间券
        if self.inventory.has_item("temp_room", 1):
            self.inventory.remove_item("temp_room", 1)
```

**villager.py**:
```python
@app.route('/action/sleep', methods=['POST'])
def sleep():
    has_house = villager.inventory.has_item("house", 1)
    has_temp_room = villager.inventory.has_item("temp_room", 1)
    
    if has_house:
        sleep_message = "在自己的房子里睡眠"
    elif has_temp_room:
        sleep_message = "使用临时房间券睡眠（将在每日结算时消耗）"
    else:
        villager.inventory.remove_money(RENT_COST)
        sleep_message = f"支付租金{RENT_COST}金币后睡眠"
```

### 经济优势

- **临时租金**: 10金币/晚
- **临时房间券**: 15金币/次
- **自己的房子**: 0金币/晚（但需要150金币建造）

临时房间券更贵，但可以提前储备，避免现金流断裂。

---

## 使用指南

### 新命令

```bash
eat / e          # 吃面包恢复体力（消耗1个面包，恢复30体力）
```

### 更新的商人价格表

```bash
> prices

商人价格表:
出售物品（购买）:
  wood: 5 金币
  seed: 2 金币
  bread: 20 金币        # 新增
  temp_room: 15 金币    # 新增

收购物品（出售）:
  wheat: 8 金币
  bread: 15 金币        # 新增
  house: 150 金币
```

### 完整游戏循环示例

```bash
# 农夫角色示例
早上 (Day 1):
> buy seed 1          # 购买种子 (2金币)
> produce             # 生产小麦 (消耗1行动点, 20体力)
> submit work         # 提交工作
[等待其他村民...]
[时间推进到中午，行动点刷新为1]

中午:
> produce             # 再次生产 (消耗1行动点, 20体力)
> buy bread 1         # 购买面包备用 (20金币)
> submit work         # 提交
[时间推进到晚上，行动点刷新为1]

晚上:
> eat                 # 吃面包恢复30体力
> buy temp_room 2     # 购买2个临时房间券备用 (30金币)
> sleep               # 使用临时房间券睡眠
> submit sleep        # 提交
[时间推进到第二天早上]
[消耗1个临时房间券]
[饥饿扣除10体力]

Day 2 早上:
> sell wheat 5        # 出售小麦给商人 (获得40金币)
> produce             # 继续生产
> ...
```

---

## 系统平衡性

### 体力管理

**消耗**:
- 每日饥饿: -10体力
- 农夫生产: -20体力
- 厨师生产: -15体力
- 木工生产: -30体力
- 不睡觉惩罚: -20体力

**恢复**:
- 睡眠: +30体力
- 吃面包: +30体力

### 经济循环

**农夫**:
- 支出: 种子(2金币) + 可能的租金(10金币) + 面包(20金币)
- 收入: 小麦(8金币/个)
- 利润: 5小麦 = 40金币收入 - 32金币支出 = 8金币净利润/时段

**厨师**:
- 支出: 小麦(从农夫购买或商人) + 租金 + 面包
- 收入: 出售面包给商人(15金币/个)或玩家(价格自定)
- 利润: 取决于小麦采购价格和面包销售价格

**木工**:
- 支出: 木材(5金币/个) + 租金 + 面包
- 收入: 出售房子(150金币)
- 利润: 150 - 50(木材) - 费用 = ~100金币净利润

---

## 技术改进总结

### 文件修改

1. **common/models.py**
   - 添加`TEMP_ROOM`物品类型
   - 修改`action_points`初始值为1
   - 添加`refresh_action_point()`方法
   - 添加`eat_bread()`方法
   - 更新`MERCHANT_PRICES`
   - `reset_daily()`添加消耗临时房间券逻辑

2. **architecture2_rest/villager.py**
   - `on_time_advance()`添加每时段刷新行动点逻辑
   - 添加`/action/eat`端点
   - 修改`/action/sleep`支持临时房间券

3. **architecture2_rest/interactive_cli.py**
   - 添加`eat()`方法和`eat`命令
   - 更新`show_help()`帮助信息
   - 更新示例工作流

4. **architecture2_rest/merchant.py**
   - 无需修改（自动使用更新的`MERCHANT_PRICES`）

### 向后兼容性

⚠️ **重要**: 这些更改会影响现有的游戏状态：

- 旧的存档中的村民`action_points`可能是3，系统会在下次时间推进时重置为1
- 建议重新创建村民以获得最佳体验

---

## 测试建议

### 测试场景1: 行动点刷新
1. 创建农夫角色
2. 早上执行`produce`（消耗1行动点）
3. 执行`submit work`
4. 等待时间推进到中午
5. 验证行动点恢复为1
6. 再次执行`produce`

### 测试场景2: 体力恢复
1. 创建厨师角色
2. 从商人购买小麦和面包
3. 多次生产消耗体力
4. 执行`eat`恢复体力
5. 验证体力正确增加

### 测试场景3: 临时房间券
1. 创建任意角色（不建房子）
2. 从商人购买2个临时房间券
3. 晚上执行`sleep`，验证使用房间券
4. 等待到第二天早上
5. 检查库存，验证消耗了1个房间券
6. 第二天晚上再次睡眠，再次验证

---

## 后续优化建议

1. **饥饿机制**: 可以考虑增加饱食度，不吃饭会加速体力消耗
2. **季节系统**: 不同季节影响生产效率
3. **房屋升级**: 更好的房子提供额外恢复或存储空间
4. **料理系统**: 更多食物类型，不同恢复效果
5. **经济调整**: 根据测试数据平衡各职业收益

---

系统现在更加完善和平衡了！🎉

