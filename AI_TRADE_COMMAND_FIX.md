# AI Agent交易命令格式修复

## 🐛 问题诊断

### 1. ✅ 交易命令格式错误

**问题**：AI Agent使用了错误的交易命令格式

**错误格式**：
```bash
# AI Agent生成的错误命令
trade Bob offer wheat 5 5
```

**正确格式**：
```bash
# 应该是这样的格式
trade node2 buy wheat 5 25  # 向node2购买5个小麦，总价25金币
trade node1 sell wheat 5 25 # 向node1出售5个小麦，总价25金币
```

**格式说明**：
- `trade <节点ID> <buy/sell> <物品> <数量> <总价>`
- 使用节点ID（node1, node2），不是村民名称
- 价格是总价，不是单价
- 动作是 `buy` 或 `sell`，不是 `offer`

---

### 2. ✅ 交易请求发送目标错误

**问题**：AI Agent发送交易请求到自己的节点，而不是目标节点

**错误逻辑**：
```python
# 发送到自己节点的trade/request端点
response = requests.post(f"{self.villager_url}/trade/request", ...)
```

**正确逻辑**：
```python
# 发送到目标节点的trade/request端点
response = requests.post(f"http://{target_node['address']}/trade/request", ...)
```

---

## 🔧 修复内容

### 1. 修复命令解析逻辑

**修复前**：
```python
elif action == "trade" and len(parts) >= 6:
    return {
        "action": "trade",
        "target": parts[1],           # 可能是名称
        "trade_action": parts[2],      # 可能是"offer"
        "item": parts[3],
        "quantity": int(parts[4]),
        "price": int(parts[5])         # 可能是单价
    }
```

**修复后**：
```python
elif action == "trade" and len(parts) >= 6:
    # 正确的格式: trade <节点ID> <buy/sell> <物品> <数量> <总价>
    trade_action = parts[2].lower()
    if trade_action not in ['buy', 'sell']:
        # 如果使用了错误的动作，尝试修正
        if trade_action in ['offer', 'purchase']:
            trade_action = 'buy'
        elif trade_action in ['sell_to', 'give']:
            trade_action = 'sell'
        else:
            trade_action = 'buy'  # 默认
    
    return {
        "action": "trade",
        "target": parts[1],           # 节点ID
        "trade_action": trade_action, # buy/sell
        "item": parts[3],
        "quantity": int(parts[4]),
        "price": int(parts[5])        # 总价
    }
```

### 2. 修复交易请求发送逻辑

**修复前**：
```python
# 发送到自己节点
response = requests.post(f"{self.villager_url}/trade/request", ...)
```

**修复后**：
```python
# 首先从协调器获取目标节点地址
coordinator_addr = villager_state.get('coordinator_address', 'localhost:5000')
nodes_response = requests.get(f"http://{coordinator_addr}/nodes", timeout=5)

if nodes_response.status_code != 200:
    print(f"[AI Agent] ✗ 获取节点列表失败: HTTP {nodes_response.status_code}")
    return False

nodes_data = nodes_response.json()
target_node = None

# 查找目标节点（支持节点ID和村民名称）
for node in nodes_data['nodes']:
    if node['node_id'] == target or node.get('name') == target:
        target_node = node
        break

if not target_node:
    print(f"[AI Agent] ✗ 找不到目标节点: {target}")
    return False

# 发送交易请求到目标节点
response = requests.post(f"http://{target_node['address']}/trade/request", ...)
```

### 3. 修复GPT提示词

**修复前**：
```python
6. TRADING EXAMPLES:
   - "trade bob sell wheat 5 80" → Offer to sell 5 wheat to Bob for 80 gold
   - "trade alice buy seed 2 15" → Offer to buy 2 seeds from Alice for 15 gold
```

**修复后**：
```python
6. TRADING EXAMPLES:
   - "trade node2 sell wheat 5 80" → Sell 5 wheat to node2 for 80 gold total
   - "trade node1 buy seed 2 15" → Buy 2 seeds from node1 for 15 gold total
   
   IMPORTANT: Use node IDs (node1, node2, etc.) not names for trading!
   IMPORTANT: Price is TOTAL price, not per-unit price!
```

**增强的交易指导**：
```python
   - **ACTIVE TRADING**: Look for opportunities to trade with other villagers!
     * Use 'trade <node_id> buy/sell <item> <quantity> <total_price>' to initiate trades
     * Check 'villagers' to see who's online and their occupations
     * IMPORTANT: Use node IDs (node1, node2) not names!
```

---

## 🎯 修复效果

### 修复前的问题

```bash
# AI Agent生成的错误命令
[AI Agent] Alice 行动: trade Bob offer wheat 5 5
[AI Agent] 交易请求已发送: offer 5x wheat for 5 gold to Bob
# ❌ Bob没有收到任何交易请求
# ❌ 命令格式错误（offer不是有效动作）
# ❌ 发送到错误的目标
```

### 修复后的正确行为

```bash
# AI Agent生成正确的命令
[AI Agent] Alice 思考: I need wheat, let me buy from Bob the farmer
[AI Agent] Alice 行动: trade node2 buy wheat 5 25
[AI Agent] 交易请求已发送: buy 5x wheat for 25 gold to node2

# Bob的终端会显示：
[Villager-node2] 收到交易请求:
  Alice 想购买 5x wheat, 出价 25金币
```

---

## 📊 测试验证

### 测试场景：农夫向厨师出售小麦

#### 1. 农夫AI发起交易
```bash
[AI Agent Bob] 思考: I have wheat, let me sell to Alice the chef
[AI Agent Bob] 行动: trade node1 sell wheat 5 30
[AI Agent Bob] ✓ 交易请求已发送: sell 5x wheat for 30 gold to node1
```

#### 2. 厨师AI收到交易请求
```bash
[Villager-node1] 收到交易请求:
  Bob 想出售 5x wheat, 要价 30金币

[AI Agent Alice] 思考: Bob offers wheat at 30 gold, that's reasonable
[AI Agent Alice] 行动: accept trade_0
[AI Agent Alice] ✓ Alice 成功执行: accept
```

#### 3. 农夫AI确认交易
```bash
[AI Agent Bob] 思考: Alice accepted my trade, I should confirm it
[AI Agent Bob] 行动: confirm trade_0
[AI Agent Bob] ✓ Bob 成功执行: confirm
[Villager-node2] 交易完成: 出售 5x wheat 给 Alice, 获得 30金币
```

---

## 🔍 关键修复点

### 1. 命令格式标准化

| 组件 | 修复前 | 修复后 |
|------|--------|--------|
| **目标** | `Bob` (名称) | `node2` (节点ID) |
| **动作** | `offer` (无效) | `buy/sell` (有效) |
| **价格** | `5` (单价) | `25` (总价) |

### 2. 网络通信修复

| 步骤 | 修复前 | 修复后 |
|------|--------|--------|
| **目标查找** | ❌ 无 | ✅ 从协调器获取节点列表 |
| **地址解析** | ❌ 无 | ✅ 支持节点ID和名称查找 |
| **请求发送** | ❌ 发送到自己 | ✅ 发送到目标节点 |

### 3. GPT提示优化

| 方面 | 修复前 | 修复后 |
|------|--------|--------|
| **示例格式** | ❌ 使用名称 | ✅ 使用节点ID |
| **价格说明** | ❌ 单价 | ✅ 总价 |
| **动作说明** | ❌ offer | ✅ buy/sell |

---

## 🎉 总结

### ✅ 修复完成

1. **命令格式修复**：
   - ✅ 支持 `buy/sell` 动作（不是 `offer`）
   - ✅ 使用节点ID（不是村民名称）
   - ✅ 价格是总价（不是单价）

2. **网络通信修复**：
   - ✅ 正确发送到目标节点
   - ✅ 支持节点ID和名称查找
   - ✅ 完整的错误处理

3. **GPT提示优化**：
   - ✅ 更新了交易示例
   - ✅ 强调了格式要求
   - ✅ 提供了清晰的指导

### 🚀 预期效果

现在AI Agent应该能够：
- 🔄 生成正确格式的交易命令
- 📡 成功发送交易请求到目标节点
- 💰 使用总价而不是单价
- 🎯 使用节点ID而不是村民名称
- ✅ 完成完整的交易流程

这些修复解决了交易请求无法到达目标节点的问题！🎉

