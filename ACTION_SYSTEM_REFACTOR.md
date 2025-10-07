# 行动系统重构说明

## 问题分析

之前的设计存在逻辑冗余：
- 每个时段有1个行动点
- 做完工作需要手动提交
- 行动点在时间推进时刷新

**核心问题**：既然每个时段只能做一件事（工作/睡眠/空闲），那么"行动点"这个状态就是多余的！

---

## 新设计

### 核心逻辑

每个时段只能做以下**三件事之一**：
1. **工作** - `produce` → 自动提交 `work`
2. **睡眠** - `sleep` → 自动提交 `sleep`  
3. **空闲** - `idle` → 手动提交 `idle`（跳过当前时段）

### 状态管理

**移除**: `action_points: int`  
**新增**: `has_submitted_action: bool`

- `False` - 当前时段还没有提交行动，可以工作/睡眠/空闲
- `True` - 已提交行动，等待时间推进

---

## 实现细节

### 1. 数据模型（common/models.py）

```python
class Villager:
    has_submitted_action: bool = False  # 当前时段是否已提交行动
    
    def reset_time_period(self):
        """重置时段状态（每次时间推进时调用）"""
        self.has_submitted_action = False
    
    def reset_daily(self):
        """每日重置"""
        self.has_submitted_action = False
        self.has_slept = False
        # ... 其他重置逻辑
```

**移除的方法**：
- `consume_action_point()`
- `refresh_action_point()`

### 2. 村民节点（villager.py）

#### 新增内部函数

```python
def _submit_action_internal(action: str) -> dict:
    """内部函数：提交行动到协调器"""
    villager.has_submitted_action = True
    # 向协调器提交行动
    # 返回结果
```

#### produce端点

```python
@app.route('/action/produce', methods=['POST'])
def produce():
    # 检查是否已提交
    if villager.has_submitted_action:
        return error('当前时段已经提交过行动')
    
    # 执行生产
    # ...
    
    # 自动提交work行动
    submit_result = _submit_action_internal('work')
    
    return {
        'message': '生产成功',
        'submit_result': submit_result
    }
```

#### sleep端点

```python
@app.route('/action/sleep', methods=['POST'])
def sleep():
    # 检查是否已提交
    if villager.has_submitted_action:
        return error('当前时段已经提交过行动')
    
    # 执行睡眠
    # ...
    
    # 自动提交sleep行动
    submit_result = _submit_action_internal('sleep')
    
    return {
        'message': '睡眠成功',
        'submit_result': submit_result
    }
```

#### submit端点

```python
@app.route('/action/submit', methods=['POST'])
def submit_action():
    # 检查是否已提交
    if villager.has_submitted_action:
        return error('当前时段已经提交过行动')
    
    action = request.json.get('action', 'idle')
    result = _submit_action_internal(action)
    
    return result
```

**用途**: 现在主要用于手动提交`idle`行动，跳过当前时段。

#### 时间推进处理

```python
@app.route('/time/advance', methods=['POST'])
def on_time_advance():
    data = request.json
    
    if data['time_of_day'] == 'morning':
        villager.reset_daily()  # 重置has_submitted_action
    else:
        villager.reset_time_period()  # 重置has_submitted_action
    
    return {'success': True}
```

### 3. CLI（interactive_cli.py）

#### produce命令

```python
def produce(self):
    """生产（自动提交work）"""
    response = requests.post(f"{self.villager_url}/action/produce")
    
    # 显示提交结果
    submit_result = response.json().get('submit_result', {})
    if submit_result.get('all_ready'):
        print("🎉 所有村民已准备就绪，时间已推进！")
    else:
        print("⏳ 已自动提交'work'行动，等待其他村民")
```

#### sleep命令

```python
def sleep(self):
    """睡眠（自动提交sleep）"""
    response = requests.post(f"{self.villager_url}/action/sleep")
    
    # 显示提交结果（同上）
```

#### idle命令

```python
# 主循环中
elif command == 'idle':
    self.submit_action('idle')
```

---

## 用户体验改进

### 之前的工作流

```bash
早上:
> produce         # 生产
✓ 生产成功
  行动点: 0      # 需要记住还有没有行动点

> submit work     # 手动提交（容易忘记）
⏳ 等待其他村民...
```

### 现在的工作流

```bash
早上:
> produce         # 生产
✓ 生产成功
⏳ 已自动提交'work'行动，等待其他村民  # 自动提交，无需手动操作！
```

---

## 命令对比

### 移除的命令

- `submit work` - 不再需要，produce自动提交
- `submit sleep` - 不再需要，sleep自动提交

### 保留的命令

- `idle` / `submit idle` - 用于跳过当前时段

### 新增行为

- `produce` - 现在会自动提交work
- `sleep` - 现在会自动提交sleep

---

## 技术优势

### 1. 简化状态管理

**之前**:
```python
action_points: int = 1        # 需要维护
has_submitted_action: bool    # 隐式的，没有明确追踪
```

**现在**:
```python
has_submitted_action: bool = False  # 唯一的状态
```

### 2. 减少错误可能

**之前**:
- 可能produce后忘记submit
- 可能submit了但没有produce
- action_points和实际提交状态可能不同步

**现在**:
- produce必定提交
- sleep必定提交
- 状态一致性由系统保证

### 3. 更符合业务逻辑

**业务规则**: 每个时段做一件事  
**技术实现**: `has_submitted_action`布尔值

完美对应，不需要"点数"的概念。

---

## 完整示例

### 农夫的一天

```bash
# 早上（Day 1, morning）
> info
名字: Alice (farmer)
体力: 100/100
货币: 100
行动状态: 未提交

> buy seed 1
✓ 购买成功: 1x seed, 花费 2金币

> produce
✓ 生产成功: 5x wheat
  消耗体力: 20, 剩余: 80
⏳ 已自动提交'work'行动，等待其他村民
  等待中: 1 个村民

[等待Bob也提交...]
[Bob执行了produce并自动提交]

🎉 所有村民已准备就绪，时间已推进！
   新时间: {'day': 1, 'time_of_day': 'noon'}

# 中午（Day 1, noon）
> eat
✓ 吃了面包，恢复 30 体力
  当前体力: 100/100

> produce
✓ 生产成功: 5x wheat
⏳ 已自动提交'work'行动，等待其他村民

[等待...]

# 晚上（Day 1, evening）
> sell wheat 10
✓ 出售成功: 10x wheat, 获得 80金币

> sleep
✓ 睡眠成功，恢复体力 30。在自己的房子里睡眠
⏳ 已自动提交'sleep'行动，等待其他村民

[等待...]

# 第二天早上（Day 2, morning）
[自动扣除饥饿10体力]
[临时房间券如有将被消耗]

> info
名字: Alice (farmer)
体力: 90/100
货币: 178
行动状态: 未提交  # 已重置，可以开始新的行动
```

---

## 边缘情况处理

### 1. 重复提交

```bash
> produce
✓ 生产成功
⏳ 已自动提交'work'

> produce
✗ 当前时段已经提交过行动，请等待时间推进
```

### 2. 想跳过当前时段

```bash
> idle
✓ 已提交'idle'行动
⏳ 等待其他村民...
```

### 3. 混合操作

```bash
> buy seed 5      # OK，交易不消耗行动
> eat             # OK，吃饭不消耗行动
> produce         # OK，生产并自动提交
> buy wood 10     # OK，交易仍可以进行
> produce         # ERROR，已经提交过了
```

---

## 帮助信息更新

```
村民操作:
  produce / work  - 执行生产（自动提交work）
  sleep / rest    - 睡眠恢复体力（自动提交sleep）
  idle            - 跳过当前时段（提交idle）
  eat / e         - 吃面包恢复体力（不消耗行动，不提交）
  buy <物品> <数量>   - 从商人购买
  sell <物品> <数量>  - 出售给商人

时间同步系统:
  ⚠️  每个时段只能做一个主要行动（工作/睡眠/空闲）
  ⚠️  只有所有村民都提交行动后，时间才会推进！
  
  💡 produce和sleep会自动提交行动
  💡 如果想跳过当前时段，使用 'idle' 命令
  💡 交易和吃饭不消耗行动，可以随时进行

示例工作流（早上）:
  buy seed 1      → 购买种子（不消耗行动）
  produce         → 生产小麦（自动提交work）
  [等待...]       → 其他村民也提交后，时间推进到中午
```

---

## 总结

### 核心改进

1. ✅ **移除冗余状态** - 不再需要`action_points`
2. ✅ **自动化提交** - produce和sleep自动提交，减少手动操作
3. ✅ **逻辑清晰** - 每个时段只能做一件主要的事
4. ✅ **错误更少** - 系统保证状态一致性
5. ✅ **体验更好** - 减少步骤，更直观

### 技术债务清理

- 删除了`consume_action_point()`方法
- 删除了`refresh_action_point()`方法
- 简化了`reset_daily()`逻辑
- 统一了提交流程

---

这次重构让系统更加符合"每个时段做一件事"的核心设计理念！🎉

