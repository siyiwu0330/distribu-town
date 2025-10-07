# 交易清理同步机制

## 问题描述

在之前的实现中，当交易完成后，接收方的 `pending_trades` 列表没有被清理，导致：

```bash
# Terminal 1 (接收方)
[Day 1 - morning] > accept trade_0
✓ 交易已接受！

# 发起方confirm后，交易已完成

[Day 1 - morning] > trades
# ❌ 问题：交易仍然显示在列表中
[1] 交易ID: trade_0
    来自: test2
    类型: 对方想购买
    物品: 5x wheat
    出价: 50金币
    状态: accepted  # ❌ 应该被清理
```

这会导致：
1. **用户困惑**：不知道交易是否完成
2. **状态不一致**：物品/货币已转移，但交易记录仍存在
3. **重复操作风险**：可能误以为交易未完成而重新操作

---

## 解决方案：双向同步清理机制

### 设计原理

采用 **双向ACK机制**：

1. **发起方发送请求** → 接收方保存到 `pending_trades`
2. **接收方accept** → 标记状态为 `accepted`
3. **发起方confirm** → 完成交易并通知接收方清理
4. **接收方收到complete** → 执行交易 + 清理 `pending_trades`

```
发起方                      接收方
  |                           |
  |---- trade request ------->|
  |                           | 保存到pending_trades
  |<----- trade_id ----------|
  |                           |
  |                           |
  |<------ accept ------------|
  |                           | 标记status='accepted'
  |                           |
confirm                       |
  |                           |
  |---- complete + trade_id ->|
  |                           | 1. 执行交易
  |                           | 2. 清理pending_trades ✓
  |<----- success ------------|
  |                           |
清理pending_trade             清理完成 ✓
```

---

## 实现细节

### 1. 发起方传递 `trade_id`

在 `complete_pending_trade()` 中，将 `trade_id` 发送给接收方：

```python
# architecture2_rest/interactive_cli.py
response = requests.post(
    f"http://{trade['target_address']}/trade/complete",
    json={
        'from': my_info['name'],
        'item': trade['item'],
        'quantity': trade['quantity'],
        'price': trade['price'],
        'type': trade['type'],
        'trade_id': trade.get('trade_id')  # ✓ 传递交易ID
    },
    timeout=5
)
```

### 2. 接收方清理 `pending_trades`

在 `/trade/complete` 端点中，根据 `trade_id` 清理记录：

```python
# architecture2_rest/villager.py
@app.route('/trade/complete', methods=['POST'])
def complete_trade():
    # ... 执行交易逻辑 ...
    
    # 清理pending_trades中的已完成交易
    if 'pending_trades' in villager_state and trade_id:
        villager_state['pending_trades'] = [
            t for t in villager_state['pending_trades']
            if t.get('trade_id') != trade_id
        ]
        print(f"[Villager-{node_id}] 已清理交易记录: {trade_id}")
    
    return jsonify({
        'success': True,
        'message': 'Trade completed',
        'villager': villager.to_dict()
    })
```

---

## 修复后的完整流程

### Terminal 2 (发起方 - test2)
```bash
[Day 1 - morning] > trade node1 buy wheat 5 50
📤 向 node1 发送交易请求...
✓ 交易请求已发送

# 等待对方accept...

============================================================
🎉 对方已接受你的交易请求！
============================================================
💡 输入 'confirm' 完成交易，或输入 'cancel' 取消
============================================================

[Day 1 - morning] > confirm

正在与 node1 完成交易...
✓ 交易完成！

[Day 1 - morning] > trades
没有待处理的交易请求  # ✓ 自己的pending_trade已清理
```

### Terminal 1 (接收方 - test1/node1)
```bash
[Day 1 - morning] > trades

[1] 交易ID: trade_0
    来自: test2
    类型: 对方想购买
    物品: 5x wheat
    出价: 50金币
    状态: pending

[Day 1 - morning] > accept trade_0
✓ 交易已接受！
  等待 test2 完成交易...

# 对方confirm后，自动执行交易并清理

[Day 1 - morning] > trades
没有待处理的交易请求  # ✓ pending_trades已自动清理

[Day 1 - morning] > info
==================================================
  test1 - farmer
==================================================
💰 货币: 130   # 80 + 50 ✓
📦 物品:
   - seed: 9
   - wheat: 0   # 5 - 5 ✓
==================================================
```

---

## 状态转换图

```
pending_trades 状态流转:

发起请求
   ↓
[pending]  ← 初始状态
   ↓
accept 命令
   ↓
[accepted] ← 等待confirm
   ↓
confirm 命令 (触发/trade/complete)
   ↓
[清理] ← 从列表中移除 ✓
```

---

## 边界情况处理

### 1. 交易被拒绝
```python
# /trade/reject
villager_state['pending_trades'] = [
    t for t in villager_state['pending_trades']
    if t['trade_id'] != trade_id
]
# ✓ 接收方主动清理
```

### 2. 交易被取消
```bash
# 发起方
[Day 1 - morning] > cancel
✓ 已取消交易
# ✓ 发起方清理pending_trade

# 接收方pending_trades仍保留（状态为pending）
# 可以手动reject清理
```

### 3. 网络错误
- 如果 `/trade/complete` 请求失败，接收方不会清理
- 发起方会收到错误提示
- 双方可以手动清理（reject/cancel）

---

## 一致性保证

### 双方状态一致性

| 时间点 | 发起方 | 接收方 | 一致性 |
|--------|--------|--------|--------|
| 发起请求后 | pending_trade存在 | pending_trades有记录 | ✓ |
| accept后 | pending_trade存在 | status='accepted' | ✓ |
| confirm后 | pending_trade清理 | pending_trades清理 | ✓ |

### 物品/货币一致性

```python
# 交易前
总wheat = 买家.wheat + 卖家.wheat = 0 + 5 = 5
总货币 = 买家.money + 卖家.money = 100 + 80 = 180

# 交易后
总wheat = 5 + 0 = 5 ✓ (守恒)
总货币 = 50 + 130 = 180 ✓ (守恒)
```

---

## 测试验证

### 测试用例：正常交易流程

```bash
# 1. 初始状态
node1: wheat=5, money=80
node2: wheat=0, money=100

# 2. 发起交易
node2: trade node1 buy wheat 5 50

# 3. 接受交易
node1: accept trade_0
node1: trades  # 显示1条accepted记录

# 4. 完成交易
node2: confirm

# 5. 验证清理
node1: trades  # ✓ 应该显示"没有待处理的交易请求"
node2: trades  # ✓ 应该显示"没有待处理的交易请求"

# 6. 验证结算
node1: info  # wheat=0, money=130 ✓
node2: info  # wheat=5, money=50 ✓
```

---

## 相关文件

- `architecture2_rest/villager.py`
  - `/trade/complete` - 添加清理逻辑
  
- `architecture2_rest/interactive_cli.py`
  - `complete_pending_trade()` - 传递trade_id

---

## 总结

✅ **同步清理机制**: 交易完成后，双方都会清理交易记录  
✅ **状态一致性**: 交易记录状态与实际物品/货币状态保持一致  
✅ **用户体验**: 用户可以通过 `trades` 命令准确了解当前待处理的交易  

现在的交易系统实现了完整的状态同步！🎉

