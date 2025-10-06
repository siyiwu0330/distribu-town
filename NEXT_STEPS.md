# 下一步操作指南

恭喜！你的分布式虚拟小镇系统已经准备就绪。以下是推荐的下一步操作：

## 🚀 立即开始

### 1. 快速测试（推荐首选）

最快速地看到系统运行效果：

```bash
# 确保在项目根目录
cd /home/siyi/projects/distribu-town

# 激活环境
conda activate distribu-town

# 测试架构2（REST - 更容易调试）
cd architecture2_rest
bash start_demo.sh
```

在另一个终端运行：
```bash
cd /home/siyi/projects/distribu-town/architecture2_rest
conda activate distribu-town
python test_scenario.py
```

### 2. 测试gRPC架构

```bash
cd /home/siyi/projects/distribu-town/architecture1_grpc
conda activate distribu-town
bash start_demo.sh
```

在另一个终端运行：
```bash
cd /home/siyi/projects/distribu-town/architecture1_grpc
conda activate distribu-town
python test_scenario.py
```

## 📊 性能对比测试

当你想对比两种架构的性能时：

```bash
# 终端1：启动gRPC
cd architecture1_grpc
bash start_demo.sh

# 终端2：启动REST  
cd architecture2_rest
bash start_demo.sh

# 终端3：运行性能测试
cd performance_tests
conda activate distribu-town
python benchmark.py --requests 100
```

## 🎮 交互式使用

### REST架构 - 使用curl

REST架构非常适合手动测试，你可以使用curl命令：

```bash
# 查看当前时间
curl http://localhost:5000/time

# 创建村民Alice（农夫）
curl -X POST http://localhost:5002/villager \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","occupation":"farmer","gender":"female","personality":"勤劳的农夫"}'

# 查看Alice的状态
curl http://localhost:5002/villager | python -m json.tool

# Alice从商人购买5个种子
curl -X POST http://localhost:5002/action/trade \
  -H "Content-Type: application/json" \
  -d '{"target":"merchant","item":"seed","quantity":5,"action":"buy"}'

# Alice进行生产（种植）
curl -X POST http://localhost:5002/action/produce

# 推进时间
curl -X POST http://localhost:5000/time/advance

# 查看商人价格表
curl http://localhost:5001/prices | python -m json.tool

# 查看所有注册的节点
curl http://localhost:5000/nodes | python -m json.tool
```

### gRPC架构 - 使用交互式客户端

```bash
cd architecture1_grpc
conda activate distribu-town
python client.py
```

然后按照菜单提示操作。

## 📝 准备报告和演示

### 1. 收集实验数据

运行性能测试并保存结果：
```bash
conda activate distribu-town
python performance_tests/benchmark.py --requests 100 > results.txt
```

### 2. 准备演示材料

你已经有以下文档可以直接使用：
- `README.md` - 完整的项目说明
- `PROJECT_SUMMARY.md` - 项目总结
- `QUICKSTART.md` - 快速开始指南

### 3. 准备演示

对于8分钟的演示，建议结构：
1. **0-1分钟**: 项目介绍和五个功能需求
2. **1-3分钟**: 演示架构1（gRPC）运行
3. **3-5分钟**: 演示架构2（REST）运行
4. **5-7分钟**: 性能对比结果
5. **7-8分钟**: AI工具使用总结和收获

## 🔧 常见任务

### 修改游戏参数

编辑 `common/models.py` 文件：

```python
# 修改商人价格
MERCHANT_PRICES = {
    "buy": {
        "wood": 3,      # 改为3（原来是5）
        "seed": 1,      # 改为1（原来是2）
    },
    # ...
}

# 修改体力恢复量
SLEEP_STAMINA = 50      # 改为50（原来是30）
```

### 添加新的村民节点

**gRPC**:
```bash
python villager.py --port 50057 --id emma --coordinator localhost:50051
```

**REST**:
```bash
python villager.py --port 5006 --id emma --coordinator localhost:5000
```

### 查看节点日志

如果使用启动脚本，日志会输出到终端。
如果想保存日志：
```bash
python coordinator.py --port 50051 > coordinator.log 2>&1 &
```

## 🐛 故障排查

### 端口被占用

```bash
# 查找占用端口的进程
lsof -i :50051
lsof -i :5000

# 终止进程
kill <PID>
```

### gRPC代码未生成

```bash
cd architecture1_grpc
conda activate distribu-town
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/town.proto
```

### 节点注册失败

确保：
1. 协调器先启动
2. 等待2-3秒后再启动其他节点
3. 地址和端口配置正确

## 📦 Docker部署（可选，如果需要）

虽然我们暂时跳过了Docker配置，但如果你需要，可以创建简单的Dockerfile：

```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "coordinator.py"]
```

## 🎯 扩展建议

如果你有额外时间，可以尝试：

1. **添加Web UI**
   - 使用Flask或React创建控制面板
   - 可视化村民状态和时间流逝

2. **实现持久化**
   - 将村民状态保存到SQLite数据库
   - 支持系统重启后恢复状态

3. **添加更多职业**
   - 矿工（挖掘矿石）
   - 铁匠（制作工具）
   - 商人（村民间交易中介）

4. **引入真正的AI Agent**
   - 使用简单的规则引擎让村民自动决策
   - 例如：体力低时自动睡觉，缺钱时自动生产

5. **实现村民间交易**
   - 扩展交易系统支持P2P交易
   - 实现简单的市场机制

## 📚 参考资料

- gRPC官方文档: https://grpc.io/docs/languages/python/
- Flask文档: https://flask.palletsprojects.com/
- REST API设计: https://restfulapi.net/

## ✅ 提交前检查清单

在提交作业前，确保：
- [ ] 运行 `python test_setup.py` 全部通过
- [ ] 两个架构都能成功启动
- [ ] 测试场景都能正常运行
- [ ] 性能测试能产生对比结果
- [ ] README.md完整且清晰
- [ ] 代码有适当的注释
- [ ] Git仓库包含所有必要文件

## 💡 演示技巧

1. **提前准备**: 在演示前先运行一遍确保没有问题
2. **分屏显示**: 使用tmux或多个终端窗口展示多个节点
3. **准备备份**: 录屏或截图作为备份
4. **时间控制**: 8分钟很短，每部分不要超时
5. **突出重点**: 重点展示两种架构的差异

## 🎉 完成后

项目完成后，你可以：
1. 将代码推送到GitHub/GitLab
2. 在README中添加演示GIF或视频
3. 写一篇技术博客分享经验
4. 继续扩展成为一个完整的游戏

---

祝你项目成功！如有问题，查看代码注释或重新运行 `python test_setup.py`。

