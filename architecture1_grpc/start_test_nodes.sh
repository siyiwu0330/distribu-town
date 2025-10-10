#!/bin/bash
# 启动测试节点的脚本

echo "启动gRPC测试节点..."
echo ""

# 检查是否在正确的目录
if [ ! -f "coordinator.py" ]; then
    echo "错误: 请在architecture1_grpc目录下运行此脚本"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 启动协调器
echo "启动Coordinator (端口50051)..."
python coordinator.py --port 50051 > logs/coordinator.log 2>&1 &
COORD_PID=$!
sleep 1

# 启动商人
echo "启动Merchant (端口50052)..."
python merchant.py --port 50052 > logs/merchant.log 2>&1 &
MERCHANT_PID=$!
sleep 1

# 启动村民节点1
echo "启动Villager node1 (端口50053)..."
python villager.py --port 50053 --id node1 > logs/node1.log 2>&1 &
NODE1_PID=$!
sleep 1

# 启动村民节点2
echo "启动Villager node2 (端口50054)..."
python villager.py --port 50054 --id node2 > logs/node2.log 2>&1 &
NODE2_PID=$!
sleep 1

echo ""
echo "所有节点已启动："
echo "  Coordinator: PID $COORD_PID (端口 50051)"
echo "  Merchant:    PID $MERCHANT_PID (端口 50052)"
echo "  Node1:       PID $NODE1_PID (端口 50053)"
echo "  Node2:       PID $NODE2_PID (端口 50054)"
echo ""
echo "日志文件位于 logs/ 目录"
echo ""
echo "要停止所有节点，请运行:"
echo "  kill $COORD_PID $MERCHANT_PID $NODE1_PID $NODE2_PID"
echo ""
echo "或使用:"
echo "  pkill -f 'python.*coordinator.py|python.*merchant.py|python.*villager.py'"
echo ""
echo "现在可以运行测试："
echo "  python test_centralized_trade.py"
echo ""
echo "或使用交互式CLI："
echo "  python interactive_cli.py --id node1 --address localhost:50053"
echo ""

