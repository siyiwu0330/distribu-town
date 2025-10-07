# 节点ID vs 村民名字 说明

## 🏷️ 命名系统

系统现在区分了两个概念：

### 1. 节点ID（Node ID）
- **用途**: 技术标识符，用于系统内部通信
- **设置时机**: 启动villager节点时指定
- **特点**: 
  - 不可改变
  - 用于节点间通信
  - 在系统日志中显示
- **示例**: `alice_node`, `node1`, `worker_1`

### 2. 村民名字（Villager Name）
- **用途**: 游戏内角色名字，显示给玩家
- **设置时机**: 在CLI中执行`create`命令时指定
- **特点**:
  - 可以是任何名字
  - 在交易请求中显示
  - 在游戏界面显示
- **示例**: `Alice`, `张三`, `小明`

---

## 📖 使用示例

### 启动节点

```bash
# 启动节点时只需指定node_id
python villager.py --port 5002 --id node1

# 输出:
# [Villager-node1] REST村民节点启动在端口 5002
# [Villager-node1] 节点ID: node1 (村民名字将在create时设置)
```

### 创建村民

```bash
# 在CLI中连接
python interactive_cli.py --port 5002

# 创建村民，指定真实的名字
> create
名字: Alice
职业: farmer
性别: female
性格: 勤劳的农夫

# 输出:
# [Villager-node1] 创建村民: Alice
# [Villager-node1] 已更新协调器中的名字: Alice
```

### 系统行为

**在协调器中：**
```
[Coordinator] 节点注册: node1 (villager) @ localhost:5002
[Coordinator] 节点注册: node1 (Alice, villager) @ localhost:5002  # 创建后更新
```

**在交易中：**
```
# node2的CLI
> trade node1 buy wheat 10 100

# node1的日志
[Villager-node1] 收到交易请求:
  Bob 想购买 10x wheat, 出价 100金币
  
# 注意: 显示的是"Bob"（村民名字），不是"node2"（节点ID）
```

---

## 🎯 最佳实践

### 推荐的节点ID命名

简短、技术性的标识符：
```bash
--id node1
--id node2
--id worker_a
--id farmer1
```

### 推荐的村民名字

有意义的角色名：
```
Alice
Bob
Charlie
张三
李四
小明
```

---

## 🔍 在不同场景中的使用

### 1. 启动节点时
使用**节点ID**：
```bash
python villager.py --port 5002 --id node1
python villager.py --port 5003 --id node2
```

### 2. 创建村民时
设置**村民名字**：
```bash
> create
名字: Alice  # 这是真正的名字
```

### 3. 发起交易时
使用**节点ID**（因为需要知道对方的地址）：
```bash
> trade node1 buy wheat 10 100
# 使用node_id，但对方会看到你的村民名字（Alice）
```

### 4. 查看可用节点
显示**节点ID**：
```bash
> status
...
可用的节点ID: node1, node2, node3
```

### 5. 交易请求中
显示**村民名字**：
```
收到交易请求:
  Alice 想购买 10x wheat  # 显示村民名字
```

---

## 💡 为什么这样设计？

### 优点

1. **灵活性**: 节点ID固定，但村民名字可以随意设置
2. **国际化**: 村民名字可以使用中文等任何字符
3. **可读性**: 交易中看到真实名字，更友好
4. **技术分离**: 系统通信用ID，用户界面用名字

### 示例场景

```bash
# 技术层面（系统日志）
[Coordinator] 节点注册: node1 (Alice, villager)
[Coordinator] node1 提交行动: work

# 用户层面（CLI显示）
收到交易请求:
  Alice 想购买 10x wheat
  
✓ 交易完成！
  你向 Alice 出售了 10x wheat
```

---

## 🎮 完整示例

### 终端1：启动node1

```bash
python villager.py --port 5002 --id node1

# 输出:
[Villager-node1] REST村民节点启动在端口 5002
[Villager-node1] 节点ID: node1 (村民名字将在create时设置)
```

### 终端2：为node1创建村民

```bash
python interactive_cli.py --port 5002

> create
名字: Alice
职业: farmer
...

[Villager-node1] 创建村民: Alice
[Villager-node1] 已更新协调器中的名字: Alice
```

### 终端3：启动node2

```bash
python villager.py --port 5003 --id node2
```

### 终端4：为node2创建村民

```bash
python interactive_cli.py --port 5003

> create
名字: Bob
职业: chef
...
```

### 终端2（Alice）：与Bob交易

```bash
# 使用节点ID发起交易
> trade node2 sell wheat 10 80

📤 向 node2 发送交易请求...
✓ 交易请求已发送
```

### 终端4（Bob）：看到请求

```bash
# Bob的节点日志
[Villager-node2] 收到交易请求:
  Alice 想出售 10x wheat, 要价 80金币
  
# Bob查看
> trades
来自: Alice  # 显示的是名字，不是node1
```

---

## 📋 快速参考

| 场景 | 使用什么 | 示例 |
|------|---------|------|
| 启动节点 | 节点ID | `--id node1` |
| 创建村民 | 村民名字 | 名字: Alice |
| 发起交易 | 节点ID | `trade node2 ...` |
| 交易显示 | 村民名字 | "Alice 想购买..." |
| 系统日志 | 节点ID | `[Villager-node1]` |
| 用户界面 | 村民名字 | "Alice - farmer" |

---

## 🔧 故障排查

### Q: 交易时找不到村民？
A: 使用节点ID，不是村民名字：
```bash
✗ 错误: trade Alice buy wheat 10 100
✓ 正确: trade node1 buy wheat 10 100
```

### Q: 如何查看可用的节点ID？
A: 使用status命令或查看启动脚本

### Q: 可以改村民名字吗？
A: 当前版本不支持，需要重新创建

---

这个设计让系统更加灵活和用户友好！🎉

