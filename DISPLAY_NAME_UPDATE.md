# 村民名字和职业显示更新

## 更新内容

现在系统在各个地方都能正确显示村民的名字和职业，而不是仅显示节点ID。

---

## 显示格式

**格式**: `Name (occupation)`

**示例**:
- `Alice (farmer)` - 农夫Alice
- `Bob (chef)` - 厨师Bob
- `Charlie (carpenter)` - 木工Charlie

---

## 更新的地方

### 1. **协调器注册日志**

创建村民前：
```
[Coordinator] 节点注册: node1 (villager) @ localhost:5002
```

创建村民后：
```
[Coordinator] 节点注册: node1 (Alice - farmer, villager) @ localhost:5002
```

### 2. **status命令 - 行动提交状态**

**之前**:
```
==================================================
  行动提交状态
==================================================

总村民数: 2
已提交: 0/2

等待提交:
   - node1
   - node2
==================================================
```

**现在**:
```
==================================================
  行动提交状态
==================================================

总村民数: 2
已提交: 1/2

已提交:
   ✓ Alice (farmer): work

等待提交:
   - Bob (chef)
==================================================
```

### 3. **submit命令 - 等待其他村民**

**之前**:
```
⏳ 等待其他村民提交...

等待以下村民提交行动:
   - node2
```

**现在**:
```
⏳ 等待其他村民提交...

等待以下村民提交行动:
   - Bob (chef)
```

### 4. **trade命令 - 查找村民**

**之前**:
```
✗ 找不到村民节点: xxx
可用的节点ID: node1, node2
```

**现在**:
```
✗ 找不到村民节点: xxx

可用的村民:
   node1: Alice (farmer)
   node2: Bob (chef)

💡 提示: 使用节点ID
   例如: trade node1 buy wheat 10 100
```

### 5. **村民节点日志**

创建时：
```
[Villager-node1] 创建村民: Alice
  职业: farmer
  性别: female
  性格: 勤劳的农夫
  体力: 100/100
  货币: 1000
[Villager-node1] 已更新协调器: Alice (farmer)
```

---

## 技术实现

### 协调器（coordinator.py）

1. 注册端点接受`name`和`occupation`字段
2. 存储在`registered_nodes`字典中
3. `/action/status`返回格式化的显示名称

```python
registered_nodes[node_id] = {
    'node_id': node_id,
    'node_type': node_type,
    'address': address,
    'name': name,
    'occupation': occupation
}
```

### 村民节点（villager.py）

创建村民后自动重新注册，更新名字和职业：

```python
response = requests.post(
    f"http://{coordinator_addr}/register",
    json={
        'node_id': node_id,
        'node_type': 'villager',
        'address': f'localhost:{port}',
        'name': villager.name,
        'occupation': villager.occupation.value
    },
    timeout=5
)
```

### CLI（interactive_cli.py）

所有显示函数都更新为使用`display_name`：

```python
# 构建显示名称
display_name = node['node_id']
if node.get('name') and node['name'] != node['node_id']:
    if node.get('occupation'):
        display_name = f"{node['name']} ({node['occupation']})"
    else:
        display_name = node['name']
```

---

## 使用示例

### 场景：两个村民的工作流

**终端1**: 启动Alice节点
```bash
python villager.py --port 5002 --id node1
```

**终端2**: 创建Alice
```bash
python interactive_cli.py --port 5002

> create
名字: Alice
职业: farmer
性别: female
性格: 勤劳的农夫
```

**终端3**: 启动Bob节点
```bash
python villager.py --port 5003 --id node2
```

**终端4**: 创建Bob
```bash
python interactive_cli.py --port 5003

> create
名字: Bob
职业: chef
性别: male
性格: 热情的厨师
```

### 查看状态

**任意终端**:
```bash
> status

==================================================
  行动提交状态
==================================================

总村民数: 2
已提交: 0/2

等待提交:
   - Alice (farmer)
   - Bob (chef)
==================================================
```

### 交易

**Alice的终端**:
```bash
> trade node2 sell wheat 10 80

📤 向 node2 发送交易请求...
✓ 交易请求已发送
  你想向 node2 出售 10x wheat, 要价 80金币
```

**Bob的终端**会看到:
```
[Villager-node2] 收到交易请求:
  Alice (farmer) 想出售 10x wheat, 要价 80金币
```

---

## 优势

1. ✅ **更友好的显示**: 看到真实名字而不是技术ID
2. ✅ **职业识别**: 一眼看出每个村民的职业
3. ✅ **国际化支持**: 名字可以使用中文等任何字符
4. ✅ **保持技术ID**: 底层通信仍使用稳定的节点ID
5. ✅ **一致性**: 所有界面都使用统一的显示格式

---

## 注意事项

⚠️ **交易时仍使用节点ID**

虽然显示用的是名字，但发起交易时必须使用节点ID：

```bash
✓ 正确: trade node1 buy wheat 10 100
✗ 错误: trade Alice buy wheat 10 100
```

这是因为节点ID是稳定的技术标识符，而名字可能重复或包含特殊字符。

---

现在系统更加用户友好了！🎉

