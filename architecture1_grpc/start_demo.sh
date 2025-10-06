#!/bin/bash

# 启动分布式虚拟小镇演示 - Architecture 1 (gRPC)

echo "=== 启动分布式虚拟小镇 ==="
echo ""

# 激活conda环境
eval "$(conda shell.bash hook)"
conda activate distribu-town

echo "1. 启动时间协调器..."
python coordinator.py --port 50051 &
COORD_PID=$!
sleep 2

echo "2. 启动商人节点..."
python merchant.py --port 50052 --coordinator localhost:50051 &
MERCHANT_PID=$!
sleep 2

echo "3. 启动村民节点..."
python villager.py --port 50053 --id alice --coordinator localhost:50051 &
VILLAGER1_PID=$!
sleep 1

python villager.py --port 50054 --id bob --coordinator localhost:50051 &
VILLAGER2_PID=$!
sleep 1

python villager.py --port 50055 --id charlie --coordinator localhost:50051 &
VILLAGER3_PID=$!
sleep 1

python villager.py --port 50056 --id diana --coordinator localhost:50051 &
VILLAGER4_PID=$!
sleep 1

echo ""
echo "=== 所有节点已启动 ==="
echo "协调器: localhost:50051 (PID: $COORD_PID)"
echo "商人: localhost:50052 (PID: $MERCHANT_PID)"
echo "村民Alice: localhost:50053 (PID: $VILLAGER1_PID)"
echo "村民Bob: localhost:50054 (PID: $VILLAGER2_PID)"
echo "村民Charlie: localhost:50055 (PID: $VILLAGER3_PID)"
echo "村民Diana: localhost:50056 (PID: $VILLAGER4_PID)"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获Ctrl+C信号
trap "echo ''; echo '停止所有服务...'; kill $COORD_PID $MERCHANT_PID $VILLAGER1_PID $VILLAGER2_PID $VILLAGER3_PID $VILLAGER4_PID 2>/dev/null; exit" INT

# 等待
wait

