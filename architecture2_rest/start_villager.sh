#!/bin/bash

if [ $# -ne 2 ]; then
    echo "用法: $0 <port> <node_id>"
    echo ""
    echo "示例:"
    echo "  $0 5002 node1"
    echo "  $0 5003 node2"
    echo "  $0 5004 node3"
    echo ""
    echo "注意: 请先运行 ./start_services.sh 启动基础服务"
    exit 1
fi

PORT=$1
NODE_ID=$2

echo ""
echo "=================================================================="
echo "  启动村民节点: $NODE_ID (端口 $PORT) - REST版本"
echo "=================================================================="
echo ""

cd "$(dirname "$0")"

# 检查基础服务是否运行
echo "1. 检查基础服务..."
python -c "
import requests
import sys

try:
    response = requests.get('http://localhost:5000/time', timeout=2)
    if response.status_code == 200:
        print('✓ Coordinator 运行正常')
    else:
        print('✗ Coordinator 未运行，请先执行: ./start_services.sh')
        sys.exit(1)
except Exception as e:
    print('✗ Coordinator 未运行，请先执行: ./start_services.sh')
    sys.exit(1)

try:
    response = requests.get('http://localhost:5001/prices', timeout=2)
    if response.status_code == 200:
        print('✓ Merchant 运行正常')
    else:
        print('✗ Merchant 未运行，请先执行: ./start_services.sh')
        sys.exit(1)
except Exception as e:
    print('✗ Merchant 未运行，请先执行: ./start_services.sh')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# 检查端口是否被占用，如果被占用则自动清理
if lsof -i :$PORT >/dev/null 2>&1; then
    echo "⚠ 端口 $PORT 已被占用，正在清理..."
    
    # 查找占用端口的进程
    PID=$(lsof -ti :$PORT)
    if [ ! -z "$PID" ]; then
        echo "   发现进程 PID: $PID"
        kill -9 $PID 2>/dev/null
        sleep 1
        
        # 再次检查
        if lsof -i :$PORT >/dev/null 2>&1; then
            echo "✗ 无法清理端口 $PORT，请手动处理"
            exit 1
        else
            echo "✓ 端口 $PORT 已清理"
        fi
    fi
fi

# 启动村民节点
echo ""
echo "2. 启动村民节点..."
python villager.py --port $PORT --id $NODE_ID --coordinator localhost:5000 > /tmp/rest_villager_${NODE_ID}.log 2>&1 &
VILLAGER_PID=$!
sleep 3

# 检查是否启动成功
if kill -0 $VILLAGER_PID 2>/dev/null; then
    echo "✓ 村民节点启动成功"
    echo "  PID: $VILLAGER_PID"
    echo "  端口: $PORT"
    echo "  节点ID: $NODE_ID"
else
    echo "✗ 村民节点启动失败"
    echo "查看日志: cat /tmp/rest_villager_${NODE_ID}.log"
    exit 1
fi

echo ""
echo "3. 验证注册..."
python -c "
import requests
import sys

try:
    response = requests.get('http://localhost:5000/nodes', timeout=2)
    if response.status_code == 200:
        data = response.json()
        nodes = data.get('nodes', [])
        
        found = False
        for node in nodes:
            if node.get('node_id') == '$NODE_ID':
                print(f'✓ 节点 $NODE_ID 已注册到Coordinator')
                found = True
                break
        
        if not found:
            print('⚠ 节点可能还在注册中，请稍等...')
    else:
        print('✗ 验证失败: HTTP', response.status_code)
except Exception as e:
    print(f'✗ 验证失败: {e}')
"

echo ""
echo "=================================================================="
echo "  村民节点就绪！"
echo "=================================================================="
echo ""
echo "现在可以连接到此节点："
echo ""
echo "【使用CLI】"
echo "  python interactive_cli.py --port $PORT"
echo ""
echo "【使用AI Agent】"
echo "  python ai_villager_agent.py --port $PORT --name Alice --occupation farmer --gender female --personality '勤劳的农夫'"
echo ""
echo "停止节点: kill $VILLAGER_PID"
echo "查看日志: tail -f /tmp/rest_villager_${NODE_ID}.log"
echo ""

