#!/bin/bash

echo ""
echo "=================================================================="
echo "  启动基础服务节点 (Coordinator + Merchant) - REST版本"
echo "=================================================================="
echo ""

cd "$(dirname "$0")"

# 清理旧进程
echo "1. 清理旧进程..."
pkill -9 -f 'python.*(coordinator|merchant)\.py' 2>/dev/null
sleep 1

# 检查并清理端口占用
for port in 5000 5001; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo "⚠ 端口 $port 已被占用，正在清理..."
        PID=$(lsof -ti :$port)
        if [ ! -z "$PID" ]; then
            echo "   发现进程 PID: $PID"
            kill -9 $PID 2>/dev/null
            sleep 1
            echo "✓ 端口 $port 已清理"
        fi
    fi
done

# 启动coordinator
echo "2. 启动Coordinator (端口5000)..."
python coordinator.py --port 5000 > /tmp/rest_coord.log 2>&1 &
COORD_PID=$!
sleep 2

# 启动merchant
echo "3. 启动Merchant (端口5001)..."
python merchant.py --port 5001 --coordinator localhost:5000 > /tmp/rest_merch.log 2>&1 &
MERCH_PID=$!
sleep 2

echo ""
echo "✓ 基础服务启动完成"
echo "  Coordinator: PID $COORD_PID (端口 5000)"
echo "  Merchant:    PID $MERCH_PID (端口 5001)"
echo ""

# 测试连接
echo "4. 测试连接..."
python -c "
import requests
import sys

try:
    response = requests.get('http://localhost:5000/time', timeout=2)
    if response.status_code == 200:
        data = response.json()
        print(f'✓ Coordinator: Day {data[\"day\"]} - {data[\"time_of_day\"]}')
    else:
        print('✗ Coordinator: HTTP', response.status_code)
except Exception as e:
    print(f'✗ Coordinator: {e}')

try:
    response = requests.get('http://localhost:5001/prices', timeout=2)
    if response.status_code == 200:
        data = response.json()
        print(f'✓ Merchant: {len(data.get(\"buy_prices\", {}))} 种商品')
    else:
        print('✗ Merchant: HTTP', response.status_code)
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
echo "  ./start_villager.sh 5002 node1"
echo "  ./start_villager.sh 5003 node2"
echo ""
echo "停止基础服务: kill $COORD_PID $MERCH_PID"
echo ""

