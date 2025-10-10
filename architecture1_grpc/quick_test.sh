#!/bin/bash

echo ""
echo "=================================================================="
echo "  gRPC版本基础测试脚本"
echo "=================================================================="
echo ""

cd "$(dirname "$0")"

# 清理旧进程
echo "1. 清理旧进程..."
pkill -9 -f 'python.*(coordinator|merchant|villager)\.py' 2>/dev/null
sleep 1

# 启动节点
echo "2. 启动节点..."
python coordinator.py --port 50051 > /tmp/coord.log 2>&1 &
COORD_PID=$!
sleep 2

python merchant.py --port 50052 > /tmp/merch.log 2>&1 &
MERCH_PID=$!
sleep 2

python villager.py --port 50053 --id node1 > /tmp/v1.log 2>&1 &
V1_PID=$!
sleep 1

python villager.py --port 50054 --id node2 > /tmp/v2.log 2>&1 &
V2_PID=$!
sleep 3

echo "   节点启动完成"
echo ""

# 检查节点状态
echo "3. 检查节点状态..."
ps aux | grep -E "($COORD_PID|$MERCH_PID|$V1_PID|$V2_PID)" | grep python | grep -v grep

echo ""
echo "4. 测试连接..."
python -c "
import grpc
import sys
sys.path.insert(0, '.')
from proto import town_pb2, town_pb2_grpc

try:
    channel = grpc.insecure_channel('localhost:50051')
    stub = town_pb2_grpc.TimeCoordinatorStub(channel)
    response = stub.ListNodes(town_pb2.Empty())
    print(f'✓ Coordinator: 找到 {len(response.nodes)} 个节点')
    for node in response.nodes:
        print(f'  - {node.node_id} ({node.node_type})')
    channel.close()
except Exception as e:
    print(f'✗ Coordinator: {e}')

try:
    channel = grpc.insecure_channel('localhost:50052')
    stub = town_pb2_grpc.MerchantNodeStub(channel)
    prices = stub.GetPrices(town_pb2.Empty())
    print(f'✓ Merchant: {len(prices.buy_prices)} 种商品')
    channel.close()
except Exception as e:
    print(f'✗ Merchant: {e}')
"

echo ""
echo "=================================================================="
echo "  基础环境就绪！"
echo "=================================================================="
echo ""
echo "现在可以开始测试："
echo ""
echo "【测试1】 创建村民"
echo "  python interactive_cli.py --port 50053"
echo "  > create"
echo "  > info"
echo ""
echo "【测试2】 商人交易"
echo "  > price"
echo "  > buy seed 2"
echo "  > info"
echo ""
echo "【测试3】 村民交易"
echo "  # 在另一个终端"
echo "  python interactive_cli.py --port 50054"
echo "  > create"
echo "  # 回到第一个终端"
echo "  > trade node2 sell wheat 3 50"
echo ""
echo "停止节点: kill $COORD_PID $MERCH_PID $V1_PID $V2_PID"
echo ""

