#!/bin/bash

# 完整演示脚本 - 展示两种架构的完整功能

echo "======================================================"
echo "  分布式虚拟小镇 - 完整功能演示"
echo "======================================================"
echo ""
echo "本演示将依次展示两种系统架构的功能："
echo "  1. 架构1：gRPC微服务架构"
echo "  2. 架构2：RESTful HTTP架构"
echo ""
echo "每个架构将自动运行一个完整的游戏场景测试"
echo ""

# 激活conda环境
eval "$(conda shell.bash hook)"
conda activate distribu-town

# ===== 架构1：gRPC =====
echo ""
echo "======================================================"
echo "第一部分：测试 gRPC 微服务架构"
echo "======================================================"
echo ""
echo "启动gRPC服务..."

cd architecture1_grpc

# 启动所有服务
python coordinator.py --port 50051 > /tmp/grpc_coord.log 2>&1 &
GRPC_COORD_PID=$!
sleep 2

python merchant.py --port 50052 --coordinator localhost:50051 > /tmp/grpc_merchant.log 2>&1 &
GRPC_MERCHANT_PID=$!
sleep 1

python villager.py --port 50053 --id alice --coordinator localhost:50051 > /tmp/grpc_alice.log 2>&1 &
GRPC_ALICE_PID=$!
sleep 1

python villager.py --port 50054 --id bob --coordinator localhost:50051 > /tmp/grpc_bob.log 2>&1 &
GRPC_BOB_PID=$!
sleep 1

python villager.py --port 50055 --id charlie --coordinator localhost:50051 > /tmp/grpc_charlie.log 2>&1 &
GRPC_CHARLIE_PID=$!
sleep 2

echo "✓ gRPC服务已启动"
echo ""
echo "运行测试场景..."
echo ""

# 运行测试
python test_scenario.py

echo ""
echo "按Enter继续到REST架构测试..."
read

# 关闭gRPC服务
echo "关闭gRPC服务..."
kill $GRPC_COORD_PID $GRPC_MERCHANT_PID $GRPC_ALICE_PID $GRPC_BOB_PID $GRPC_CHARLIE_PID 2>/dev/null
sleep 2

# ===== 架构2：REST =====
echo ""
echo "======================================================"
echo "第二部分：测试 RESTful HTTP 架构"
echo "======================================================"
echo ""
echo "启动REST服务..."

cd ../architecture2_rest

# 启动所有服务
python coordinator.py --port 5000 > /tmp/rest_coord.log 2>&1 &
REST_COORD_PID=$!
sleep 2

python merchant.py --port 5001 --coordinator localhost:5000 > /tmp/rest_merchant.log 2>&1 &
REST_MERCHANT_PID=$!
sleep 1

python villager.py --port 5002 --id alice --coordinator localhost:5000 > /tmp/rest_alice.log 2>&1 &
REST_ALICE_PID=$!
sleep 1

python villager.py --port 5003 --id bob --coordinator localhost:5000 > /tmp/rest_bob.log 2>&1 &
REST_BOB_PID=$!
sleep 1

python villager.py --port 5004 --id charlie --coordinator localhost:5000 > /tmp/rest_charlie.log 2>&1 &
REST_CHARLIE_PID=$!
sleep 2

echo "✓ REST服务已启动"
echo ""
echo "运行测试场景..."
echo ""

# 运行测试
python test_scenario.py

echo ""
echo "按Enter继续到性能对比测试..."
read

# ===== 性能对比 =====
echo ""
echo "======================================================"
echo "第三部分：性能对比测试"
echo "======================================================"
echo ""
echo "重新启动gRPC服务以进行对比测试..."

cd ../architecture1_grpc

python coordinator.py --port 50051 > /tmp/grpc_coord.log 2>&1 &
GRPC_COORD_PID=$!
sleep 2

python merchant.py --port 50052 --coordinator localhost:50051 > /tmp/grpc_merchant.log 2>&1 &
GRPC_MERCHANT_PID=$!
sleep 1

python villager.py --port 50053 --id alice --coordinator localhost:50051 > /tmp/grpc_alice.log 2>&1 &
GRPC_ALICE_PID=$!
sleep 2

# 创建gRPC测试用的村民
python -c "
import grpc
import sys
import os
sys.path.insert(0, '.')
from proto import town_pb2, town_pb2_grpc

channel = grpc.insecure_channel('localhost:50053')
stub = town_pb2_grpc.VillagerNodeStub(channel)
stub.CreateVillager(town_pb2.CreateVillagerRequest(
    name='Alice', occupation='farmer', gender='female', personality='勤劳'
))
channel.close()
" 2>/dev/null

# 创建REST测试用的村民
curl -X POST http://localhost:5002/villager \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","occupation":"farmer","gender":"female","personality":"勤劳"}' \
  > /dev/null 2>&1

sleep 1

echo "两个架构都已就绪，开始性能测试..."
echo ""

cd ../performance_tests
python benchmark.py --requests 50

echo ""
echo "======================================================"
echo "演示完成！"
echo "======================================================"
echo ""
echo "关闭所有服务..."

# 关闭所有服务
kill $GRPC_COORD_PID $GRPC_MERCHANT_PID $GRPC_ALICE_PID $GRPC_BOB_PID $GRPC_CHARLIE_PID 2>/dev/null
kill $REST_COORD_PID $REST_MERCHANT_PID $REST_ALICE_PID $REST_BOB_PID $REST_CHARLIE_PID 2>/dev/null

echo "✓ 所有服务已关闭"
echo ""
echo "日志文件位于 /tmp/grpc_*.log 和 /tmp/rest_*.log"
echo ""
echo "感谢使用分布式虚拟小镇系统！"

