#!/bin/bash

# 启动分布式虚拟小镇演示 - Architecture 2 (REST)

echo "=== 启动分布式虚拟小镇 (REST架构) ==="
echo ""

# 激活conda环境
eval "$(conda shell.bash hook)"
conda activate distribu-town

echo "1. 启动时间协调器..."
python coordinator.py --port 5000 &
COORD_PID=$!
sleep 2

echo "2. 启动商人节点..."
python merchant.py --port 5001 --coordinator localhost:5000 &
MERCHANT_PID=$!
sleep 2

echo "3. 启动村民节点..."
python villager.py --port 5002 --id alice --coordinator localhost:5000 &
VILLAGER1_PID=$!
sleep 1

python villager.py --port 5003 --id bob --coordinator localhost:5000 &
VILLAGER2_PID=$!
sleep 1

python villager.py --port 5004 --id charlie --coordinator localhost:5000 &
VILLAGER3_PID=$!
sleep 1

python villager.py --port 5005 --id diana --coordinator localhost:5000 &
VILLAGER4_PID=$!
sleep 1

echo ""
echo "=== 所有节点已启动 ==="
echo "协调器: http://localhost:5000 (PID: $COORD_PID)"
echo "商人: http://localhost:5001 (PID: $MERCHANT_PID)"
echo "村民Alice: http://localhost:5002 (PID: $VILLAGER1_PID)"
echo "村民Bob: http://localhost:5003 (PID: $VILLAGER2_PID)"
echo "村民Charlie: http://localhost:5004 (PID: $VILLAGER3_PID)"
echo "村民Diana: http://localhost:5005 (PID: $VILLAGER4_PID)"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获Ctrl+C信号
trap "echo ''; echo '停止所有服务...'; kill $COORD_PID $MERCHANT_PID $VILLAGER1_PID $VILLAGER2_PID $VILLAGER3_PID $VILLAGER4_PID 2>/dev/null; exit" INT

# 等待
wait

