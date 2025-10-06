#!/bin/bash

# 快速测试脚本 - 自动运行REST架构的完整测试

echo "======================================"
echo "  分布式虚拟小镇 - 快速测试"
echo "======================================"
echo ""

# 激活环境
eval "$(conda shell.bash hook)"
conda activate distribu-town

echo "步骤1：启动REST服务..."
cd architecture2_rest

# 启动所有服务
python coordinator.py --port 5000 > /tmp/coord.log 2>&1 &
COORD_PID=$!
sleep 2

python merchant.py --port 5001 --coordinator localhost:5000 > /tmp/merchant.log 2>&1 &
MERCHANT_PID=$!
sleep 1

python villager.py --port 5002 --id alice --coordinator localhost:5000 > /tmp/alice.log 2>&1 &
ALICE_PID=$!
sleep 1

python villager.py --port 5003 --id bob --coordinator localhost:5000 > /tmp/bob.log 2>&1 &
BOB_PID=$!
sleep 1

python villager.py --port 5004 --id charlie --coordinator localhost:5000 > /tmp/charlie.log 2>&1 &
CHARLIE_PID=$!
sleep 2

echo "✓ 服务启动成功！"
echo ""

echo "步骤2：运行测试场景..."
echo ""
python test_scenario.py

echo ""
echo "======================================"
echo "测试完成！"
echo "======================================"
echo ""
echo "提示："
echo "  - 查看日志: tail /tmp/coord.log /tmp/merchant.log /tmp/alice.log"
echo "  - 手动测试: curl http://localhost:5002/villager"
echo ""
echo "按Enter键关闭所有服务..."
read

# 关闭所有服务
echo "关闭服务..."
kill $COORD_PID $MERCHANT_PID $ALICE_PID $BOB_PID $CHARLIE_PID 2>/dev/null
sleep 1

echo "✓ 所有服务已关闭"
echo ""
echo "测试完成！查看上面的输出了解系统运行情况。"

