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

echo ""
echo "村民节点需要手动创建。"

echo ""
echo "======================================================"
echo "✓ 基础设施已启动！"
echo "======================================================"
echo ""
echo "基础设施:"
echo "  协调器:  http://localhost:5000"
echo "  商人:    http://localhost:5001"
echo ""
echo "======================================================"
echo "创建村民节点："
echo "======================================================"
echo ""
echo "在新终端中启动村民节点（每个村民一个终端）："
echo ""
echo "  # 终端A：启动Alice节点"
echo "  cd $(pwd) && conda activate distribu-town"
echo "  python architecture2_rest/villager.py --port 5002 --id alice"
echo ""
echo "  # 终端B：启动Bob节点"
echo "  python architecture2_rest/villager.py --port 5003 --id bob"
echo ""
echo "  # 终端C：启动Charlie节点"
echo "  python architecture2_rest/villager.py --port 5004 --id charlie"
echo ""
echo "======================================================"
echo "连接到村民节点："
echo "======================================================"
echo ""
echo "启动村民节点后，在另一个终端连接CLI控制："
echo ""
echo "  # 控制Alice（确保Alice节点已启动在5002端口）"
echo "  python architecture2_rest/interactive_cli.py --port 5002"
echo ""
echo "  # 控制Bob（确保Bob节点已启动在5003端口）"
echo "  python architecture2_rest/interactive_cli.py --port 5003"
echo ""
echo "提示："
echo "  1. 先启动村民节点 (villager.py)"
echo "  2. 再连接CLI控制台 (interactive_cli.py)"
echo "  3. 在CLI中使用 'create' 命令初始化村民"
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
trap "echo ''; echo '停止所有服务...'; kill $COORD_PID $MERCHANT_PID 2>/dev/null; echo '✓ 基础设施已停止'; echo '提示: 手动停止村民节点 (Ctrl+C)'; exit" INT

# 等待
wait

