#!/bin/bash

echo ""
echo "=================================================================="
echo "  启动基础服务节点 (Coordinator + Merchant)"
echo "=================================================================="
echo ""

cd "$(dirname "$0")"

# 清理旧进程
echo "1. 清理旧进程..."
pkill -9 -f 'python.*(coordinator|merchant)\.py' 2>/dev/null
sleep 1

# 启动coordinator
echo "2. 启动Coordinator (端口50051)..."
python coordinator.py --port 50051 > /tmp/grpc_coord.log 2>&1 &
COORD_PID=$!
sleep 2

# 启动merchant
echo "3. 启动Merchant (端口50052)..."
python merchant.py --port 50052 > /tmp/grpc_merch.log 2>&1 &
MERCH_PID=$!
sleep 2

echo ""
echo "✓ 基础服务启动完成"
echo "  Coordinator: PID $COORD_PID (端口 50051)"
echo "  Merchant:    PID $MERCH_PID (端口 50052)"
echo ""

# 测试连接
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
echo "  基础服务就绪！"
echo "=================================================================="
echo ""
echo "现在可以启动村民节点："
echo "  ./start_villager.sh <port> <node_id>"
echo ""
echo "例如："
echo "  ./start_villager.sh 50053 node1"
echo "  ./start_villager.sh 50054 node2"
echo ""
echo "停止基础服务: kill $COORD_PID $MERCH_PID"
echo ""

