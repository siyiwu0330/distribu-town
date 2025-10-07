# 交易系统增强：支持多项交易和状态标记

## 优化内容

本次更新针对用户反馈的两个重要问题进行了优化：

### 1. ✅ 防止重复接受交易

**问题**：接收方在accept后，`trades`列表中交易状态仍显示为pending，用户可能误以为未接受而重复操作。

**解决方案**：
- 在`trades`显示中明确标记已接受状态
- 在`accept`命令中检查交易是否已被接受，防止重复操作

**修复前**：
```bash
[Day 1 - noon] > accept trade_0
✓ 交易已接受！

[Day 1 - noon] > trades
[1] 交易ID: trade_0
    状态: accepted  # ❌ 没有明显提示
    操作: accept trade_0 或 reject trade_0  # ❌ 误导用户
```

**修复后**：
```bash
[Day 1 - noon] > accept trade_0
✓ 交易已接受！

[Day 1 - noon] > trades
[1] 交易ID: trade_0
    状态: ✓ 已接受（等待对方完成）  # ✓ 清晰标记
    操作: 等待对方confirm或reject trade_0 取消  # ✓ 明确指示

[Day 1 - noon] > accept trade_0
⚠️  交易 trade_0 已经被接受过了  # ✓ 防止重复
   等待对方完成交易...
```

---

### 2. ✅ 支持多项并发交易

**问题**：
- 只能跟踪一个发起的交易（`pending_trade`单变量）
- `confirm`和`cancel`命令无法指定交易ID
- 同时进行多项交易时会发生混乱

**解决方案**：
- 将`pending_trade`改为`pending_trades`字典
- `confirm`和`cancel`命令支持指定trade_id
- 自动检测机制支持多项交易

**修复前**：
```python
self.pending_trade = {...}  # 只能存一个交易

# 命令
confirm   # 无法指定哪个交易
cancel    # 无法指定哪个交易
```

**修复后**：
```python
self.pending_trades = {
    'trade_0': {...},
    'trade_1': {...},
    'trade_2': {...}
}

# 命令
confirm trade_0      # 指定交易ID
confirm              # 如果只有一个，自动选择
cancel trade_1       # 指定交易ID
```

---

## 详细实现

### 数据结构变更

#### 从单个交易到多个交易

```python
# 旧设计
class VillagerCLI:
    def __init__(self):
        self.pending_trade = None  # 单个交易

# 新设计
class VillagerCLI:
    def __init__(self):
        self.pending_trades = {}  # 多个交易，key为trade_id
```

#### 存储交易

```python
# 新设计
self.pending_trades[trade_id] = {
    'target': target_id,
    'target_address': target_address,
    'item': item,
    'quantity': quantity,
    'price': price,
    'type': offer_type,
    'trade_id': trade_id,
    'status': 'pending'
}
```

---

### 功能增强

#### 1. trades命令 - 状态可视化

```python
for i, trade in enumerate(trades, 1):
    status = trade.get('status', 'pending')
    print(f"\n[{i}] 交易ID: {trade['trade_id']}")
    print(f"    来自: {trade['from']}")
    # ...
    
    # 根据状态显示不同的提示
    if status == 'accepted':
        print(f"    状态: ✓ 已接受（等待对方完成）")
        print(f"    操作: 等待对方confirm或reject {trade['trade_id']} 取消")
    else:
        print(f"    状态: ⏳ 待处理")
        print(f"    操作: accept {trade['trade_id']} 或 reject {trade['trade_id']}")
```

#### 2. accept命令 - 防止重复

```python
def accept_trade_request(self, trade_id: str):
    # 先检查交易状态
    trades_response = requests.get(f"{self.villager_url}/trade/pending", timeout=5)
    if trades_response.status_code == 200:
        trades = trades_response.json().get('pending_trades', [])
        for trade in trades:
            if trade['trade_id'] == trade_id:
                if trade.get('status') == 'accepted':
                    print(f"\n⚠️  交易 {trade_id} 已经被接受过了")
                    print("   等待对方完成交易...")
                    return
                break
    
    # 继续接受流程...
```

#### 3. confirm命令 - 支持多项交易

```python
def complete_pending_trade(self, trade_id: str = None):
    """完成自己发起的交易（在对方accept后）"""
    if not self.pending_trades:
        print("\n✗ 没有待处理的交易")
        return
    
    # 如果没有指定trade_id，检查是否只有一个待处理交易
    if trade_id is None:
        if len(self.pending_trades) == 1:
            trade_id = list(self.pending_trades.keys())[0]
        else:
            print("\n✗ 有多个待处理的交易，请指定交易ID")
            print("   可用的交易:")
            for tid, t in self.pending_trades.items():
                status_text = "✓ 已接受" if t.get('status') == 'ready_to_confirm' else "⏳ 等待接受"
                print(f"   {tid}: {t['type']} {t['quantity']}x {t['item']} ({status_text})")
            print(f"\n   使用 'confirm <trade_id>' 完成指定交易")
            return
    
    # 处理指定的交易...
```

#### 4. 自动检查 - 支持多项交易

```python
def check_my_pending_trade_status(self):
    """检查自己发起的交易状态"""
    if not self.pending_trades:
        return
    
    for trade_id, trade in list(self.pending_trades.items()):
        # 如果已经提示过，就不再提示
        if trade.get('status') == 'ready_to_confirm':
            continue
        
        # 查询每个交易的状态...
        if remote_trade.get('status') == 'accepted':
            print(f"🎉 对方已接受你的交易请求！[{trade_id}]")
            print(f"💡 输入 'confirm {trade_id}' 完成交易")
```

---

## 使用示例

### 场景1：单个交易

```bash
# Terminal 2 (发起方)
[Day 1 - noon] > trade node1 buy wheat 5 50
✓ 交易请求已发送
⏳ 等待 node1 接受或拒绝...

# Terminal 1 (接收方)
[Day 1 - noon] > trades
[1] 交易ID: trade_0
    状态: ⏳ 待处理
    操作: accept trade_0 或 reject trade_0

[Day 1 - noon] > accept trade_0
✓ 交易已接受！

# Terminal 2
🎉 对方已接受你的交易请求！[trade_0]
💡 输入 'confirm trade_0' 完成交易

[Day 1 - noon] > confirm trade_0  # 指定ID
✓ 交易完成！

# 或者
[Day 1 - noon] > confirm  # 只有一个交易时可以省略ID
✓ 交易完成！
```

---

### 场景2：多项并发交易

```bash
# Terminal 2 (发起方)
[Day 1 - noon] > trade node1 buy wheat 5 50
✓ 交易请求已发送 [trade_0]

[Day 1 - noon] > trade node3 buy bread 2 20
✓ 交易请求已发送 [trade_1]

[Day 1 - noon] > trade node1 sell seed 10 30
✓ 交易请求已发送 [trade_2]

# node1接受了trade_0和trade_2
🎉 对方已接受你的交易请求！[trade_0]
💡 输入 'confirm trade_0' 完成交易

🎉 对方已接受你的交易请求！[trade_2]
💡 输入 'confirm trade_2' 完成交易

[Day 1 - noon] > confirm  # 有多个交易时，必须指定ID
✗ 有多个待处理的交易，请指定交易ID
   可用的交易:
   trade_0: buy 5x wheat (✓ 已接受)
   trade_1: buy 2x bread (⏳ 等待接受)
   trade_2: sell 10x seed (✓ 已接受)

   使用 'confirm <trade_id>' 完成指定交易

[Day 1 - noon] > confirm trade_0  # ✓ 指定ID
✓ 交易完成！

[Day 1 - noon] > cancel trade_1  # 取消还未接受的交易
✓ 已取消交易 trade_1

[Day 1 - noon] > confirm trade_2
✓ 交易完成！
```

---

### 场景3：防止重复接受

```bash
# Terminal 1 (接收方)
[Day 1 - noon] > trades
[1] 交易ID: trade_0
    状态: ⏳ 待处理
    操作: accept trade_0 或 reject trade_0

[Day 1 - noon] > accept trade_0
✓ 交易已接受！
  等待 test2 完成交易...

[Day 1 - noon] > trades
[1] 交易ID: trade_0
    状态: ✓ 已接受（等待对方完成）  # ✓ 清晰标记
    操作: 等待对方confirm或reject trade_0 取消

[Day 1 - noon] > accept trade_0  # 尝试重复接受
⚠️  交易 trade_0 已经被接受过了  # ✓ 防止重复
   等待对方完成交易...
```

---

## 命令语法更新

### 旧语法
```bash
confirm         # 完成唯一的交易
cancel          # 取消唯一的交易
```

### 新语法
```bash
confirm [trade_id]    # 可选指定ID
confirm               # 只有一个交易时自动选择
confirm trade_0       # 指定特定交易

cancel [trade_id]     # 可选指定ID
cancel                # 只有一个交易时自动选择
cancel trade_1        # 指定特定交易
```

---

## 兼容性

### 向后兼容

对于单个交易场景，新系统完全兼容旧的使用习惯：

```bash
# 旧用法（仍然有效）
trade node1 buy wheat 5 50
confirm    # 只有一个交易时自动识别
```

### 新功能

只有在多项交易时才需要指定ID：

```bash
# 新用法（多项交易）
trade node1 buy wheat 5 50
trade node2 buy bread 2 20
confirm trade_0  # 必须指定ID
```

---

## 错误处理

### 1. 重复接受
```bash
accept trade_0
⚠️  交易 trade_0 已经被接受过了
   等待对方完成交易...
```

### 2. 多项交易未指定ID
```bash
confirm
✗ 有多个待处理的交易，请指定交易ID
   可用的交易:
   trade_0: buy 5x wheat (✓ 已接受)
   trade_1: buy 2x bread (⏳ 等待接受)
```

### 3. 交易ID不存在
```bash
confirm trade_999
✗ 找不到交易: trade_999
```

---

## 相关文件

- `architecture2_rest/interactive_cli.py`
  - `__init__()` - 改用`pending_trades`字典
  - `check_my_pending_trade_status()` - 支持多项交易检查
  - `check_pending_trades()` - 显示状态标记
  - `accept_trade_request()` - 防止重复接受
  - `complete_pending_trade()` - 支持指定trade_id
  - 命令解析 - 支持`confirm [id]`和`cancel [id]`

---

## 总结

✅ **防止重复操作**: 已接受的交易明确标记，避免用户困惑  
✅ **支持并发交易**: 可以同时发起多个交易，独立管理  
✅ **灵活的ID指定**: 单个交易时自动识别，多个交易时必须指定  
✅ **向后兼容**: 旧的使用习惯仍然有效  
✅ **清晰的错误提示**: 帮助用户正确使用命令  

现在的交易系统更加健壮和易用！🎉

