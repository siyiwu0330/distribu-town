#!/bin/bash

# 测试交互式CLI系统

echo "======================================================"
echo "  测试交互式CLI系统"
echo "======================================================"
echo ""

# 激活环境
eval "$(conda shell.bash hook)"
conda activate distribu-town

cd architecture2_rest

# 启动服务
echo "1. 启动服务..."
python coordinator.py --port 5000 > /tmp/test_coord.log 2>&1 &
COORD_PID=$!
sleep 2

python merchant.py --port 5001 > /tmp/test_merchant.log 2>&1 &
MERCHANT_PID=$!
sleep 1

python villager.py --port 5002 --id alice > /tmp/test_alice.log 2>&1 &
ALICE_PID=$!
sleep 2

echo "✓ 服务已启动"
echo ""

# 测试基本连接
echo "2. 测试API连接..."

# 测试村民节点健康检查
HEALTH=$(curl -s http://localhost:5002/health | python -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
if [ "$HEALTH" = "healthy" ]; then
    echo "✓ 村民节点健康"
else
    echo "✗ 村民节点连接失败"
fi

# 创建村民
echo ""
echo "3. 创建村民Alice..."
curl -s -X POST http://localhost:5002/villager \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","occupation":"farmer","gender":"female","personality":"测试"}' \
  > /dev/null

# 查看村民信息
VILLAGER_NAME=$(curl -s http://localhost:5002/villager | python -c "import sys, json; print(json.load(sys.stdin)['name'])" 2>/dev/null)
if [ "$VILLAGER_NAME" = "Alice" ]; then
    echo "✓ 村民创建成功: $VILLAGER_NAME"
else
    echo "✗ 村民创建失败"
fi

# 测试购买
echo ""
echo "4. 测试购买功能..."
TRADE_RESULT=$(curl -s -X POST http://localhost:5002/action/trade \
  -H "Content-Type: application/json" \
  -d '{"target":"merchant","item":"seed","quantity":3,"action":"buy"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['success'])" 2>/dev/null)

if [ "$TRADE_RESULT" = "True" ]; then
    echo "✓ 购买功能正常"
else
    echo "✗ 购买功能失败"
fi

# 测试生产
echo ""
echo "5. 测试生产功能..."
PRODUCE_RESULT=$(curl -s -X POST http://localhost:5002/action/produce \
  | python -c "import sys, json; print(json.load(sys.stdin)['success'])" 2>/dev/null)

if [ "$PRODUCE_RESULT" = "True" ]; then
    echo "✓ 生产功能正常"
else
    echo "✗ 生产功能失败"
fi

# 测试时间推进
echo ""
echo "6. 测试时间推进..."
TIME_RESULT=$(curl -s -X POST http://localhost:5000/time/advance \
  | python -c "import sys, json; print(json.load(sys.stdin)['success'])" 2>/dev/null)

if [ "$TIME_RESULT" = "True" ]; then
    echo "✓ 时间推进正常"
else
    echo "✗ 时间推进失败"
fi

echo ""
echo "======================================================"
echo "测试完成！"
echo "======================================================"
echo ""
echo "交互式CLI准备就绪，可以使用："
echo "  python architecture2_rest/interactive_cli.py --port 5002"
echo ""
echo "按Enter键关闭测试服务..."
read

# 清理
echo "关闭服务..."
kill $COORD_PID $MERCHANT_PID $ALICE_PID 2>/dev/null
sleep 1
echo "✓ 测试完成"

