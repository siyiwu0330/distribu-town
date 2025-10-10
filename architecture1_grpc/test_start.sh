#!/bin/bash

cd "$(dirname "$0")"

echo "启动gRPC节点..."

# 清理旧进程
pkill -9 -f 'python.*(coordinator|merchant|villager)\.py' 2>/dev/null
sleep 1

# 启动coordinator
echo "Starting coordinator..."
python coordinator.py --port 50051 > /tmp/grpc_coord.log 2>&1 &
COORD_PID=$!
sleep 2

# 启动merchant
echo "Starting merchant..."
python merchant.py --port 50052 > /tmp/grpc_merch.log 2>&1 &
MERCH_PID=$!
sleep 2

# 启动villager1
echo "Starting villager node1..."
python villager.py --port 50053 --id node1 > /tmp/grpc_v1.log 2>&1 &
V1_PID=$!
sleep 1

# 启动villager2
echo "Starting villager node2..."
python villager.py --port 50054 --id node2 > /tmp/grpc_v2.log 2>&1 &
V2_PID=$!
sleep 2

echo ""
echo "节点启动完成:"
echo "  Coordinator: PID $COORD_PID"
echo "  Merchant:    PID $MERCH_PID"
echo "  Villager 1:  PID $V1_PID"
echo "  Villager 2:  PID $V2_PID"
echo ""

# 检查进程
ps aux | grep -E "($COORD_PID|$MERCH_PID|$V1_PID|$V2_PID)" | grep python | grep -v grep

echo ""
echo "日志位置: /tmp/grpc_*.log"
echo ""
echo "测试连接..."
python -c "
import grpc
import sys
sys.path.insert(0, '.')
from proto import town_pb2, town_pb2_grpc

try:
    channel = grpc.insecure_channel('localhost:50051')
    stub = town_pb2_grpc.TimeCoordinatorStub(channel)
    response = stub.ListNodes(town_pb2.Empty())
    print(f'✓ 找到 {len(response.nodes)} 个节点')
    channel.close()
except Exception as e:
    print(f'✗ 连接失败: {e}')
"

echo ""
echo "停止节点: kill $COORD_PID $MERCH_PID $V1_PID $V2_PID"

