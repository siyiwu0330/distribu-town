#!/bin/bash

# 启动交互式多终端系统的基础设施

echo "======================================================"
echo "  启动分布式虚拟小镇 - 交互式模式"
echo "======================================================"
echo ""

# 激活conda环境
eval "$(conda shell.bash hook)"
conda activate distribu-town

cd architecture2_rest

echo "启动协调器..."
python coordinator.py --port 5000 > /tmp/coordinator.log 2>&1 &
COORD_PID=$!
sleep 2

echo "启动商人节点..."
python merchant.py --port 5001 --coordinator localhost:5000 > /tmp/merchant.log 2>&1 &
MERCHANT_PID=$!
sleep 2

echo "启动村民节点..."

echo "  - Alice (端口 5002)"
python villager.py --port 5002 --id alice --coordinator localhost:5000 > /tmp/alice.log 2>&1 &
ALICE_PID=$!
sleep 1

echo "  - Bob (端口 5003)"
python villager.py --port 5003 --id bob --coordinator localhost:5000 > /tmp/bob.log 2>&1 &
BOB_PID=$!
sleep 1

echo "  - Charlie (端口 5004)"
python villager.py --port 5004 --id charlie --coordinator localhost:5000 > /tmp/charlie.log 2>&1 &
CHARLIE_PID=$!
sleep 1

echo "  - Diana (端口 5005)"
python villager.py --port 5005 --id diana --coordinator localhost:5000 > /tmp/diana.log 2>&1 &
DIANA_PID=$!
sleep 2

echo ""
echo "======================================================"
echo "✓ 所有服务已启动！"
echo "======================================================"
echo ""
echo "基础设施:"
echo "  协调器:  http://localhost:5000"
echo "  商人:    http://localhost:5001"
echo ""
echo "村民节点:"
echo "  Alice:   http://localhost:5002 (farmer - 农夫)"
echo "  Bob:     http://localhost:5003 (chef - 厨师)"
echo "  Charlie: http://localhost:5004 (carpenter - 木工)"
echo "  Diana:   http://localhost:5005 (自定义)"
echo ""
echo "======================================================"
echo "开始游戏："
echo "======================================================"
echo ""
echo "在不同的终端窗口运行以下命令来控制不同的村民："
echo ""
echo "  # 控制Alice"
echo "  python architecture2_rest/interactive_cli.py --port 5002"
echo ""
echo "  # 控制Bob"
echo "  python architecture2_rest/interactive_cli.py --port 5003"
echo ""
echo "  # 控制Charlie"
echo "  python architecture2_rest/interactive_cli.py --port 5004"
echo ""
echo "  # 控制Diana"
echo "  python architecture2_rest/interactive_cli.py --port 5005"
echo ""
echo "======================================================"
echo "日志文件位置："
echo "  /tmp/coordinator.log"
echo "  /tmp/merchant.log"
echo "  /tmp/alice.log"
echo "  /tmp/bob.log"
echo "  /tmp/charlie.log"
echo "  /tmp/diana.log"
echo ""
echo "查看日志: tail -f /tmp/coordinator.log"
echo "======================================================"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 捕获Ctrl+C信号
trap "echo ''; echo '停止所有服务...'; kill $COORD_PID $MERCHANT_PID $ALICE_PID $BOB_PID $CHARLIE_PID $DIANA_PID 2>/dev/null; echo '✓ 所有服务已停止'; exit" INT

# 等待
wait

