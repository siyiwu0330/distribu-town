#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <port> <node_id>"
    echo ""
    echo "Examples:"
    echo "  $0 5002 node1"
    echo "  $0 5003 node2"
    echo "  $0 5004 node3"
    echo ""
    echo "Note: Please run ./start_services.sh to start the base services first"
    exit 1
fi

PORT=$1
NODE_ID=$2

echo ""
echo "=================================================================="
echo "  Start Villager Node: $NODE_ID (port $PORT) - REST Version"
echo "=================================================================="
echo ""

cd "$(dirname "$0")"

# Check whether base services are running
echo "1. Checking base services..."
python -c "
import requests
import sys

try:
    response = requests.get('http://localhost:5000/time', timeout=2)
    if response.status_code == 200:
        print('✓ Coordinator is running')
    else:
        print('✗ Coordinator is not running. Please run: ./start_services.sh')
        sys.exit(1)
except Exception as e:
    print('✗ Coordinator is not running. Please run: ./start_services.sh')
    sys.exit(1)

try:
    response = requests.get('http://localhost:5001/prices', timeout=2)
    if response.status_code == 200:
        print('✓ Merchant is running')
    else:
        print('✗ Merchant is not running. Please run: ./start_services.sh')
        sys.exit(1)
except Exception as e:
    print('✗ Merchant is not running. Please run: ./start_services.sh')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Check if the port is in use; if so, clean it up automatically
if lsof -i :$PORT >/dev/null 2>&1; then
    echo "⚠ Port $PORT is in use, cleaning up..."
    
    # Find the process occupying the port
    PID=$(lsof -ti :$PORT)
    if [ ! -z "$PID" ]; then
        echo "   Found PID: $PID"
        kill -9 $PID 2>/dev/null
        sleep 1
        
        # Check again
        if lsof -i :$PORT >/dev/null 2>&1; then
            echo "✗ Unable to free port $PORT, please handle manually"
            exit 1
        else:
            echo "✓ Port $PORT cleared"
        fi
    fi
fi

# Start villager node
echo ""
echo "2. Starting villager node..."
python villager.py --port $PORT --id $NODE_ID --coordinator localhost:5000 > /tmp/rest_villager_${NODE_ID}.log 2>&1 &
VILLAGER_PID=$!
sleep 3

# Check whether it started successfully
if kill -0 $VILLAGER_PID 2>/dev/null; then
    echo "✓ Villager node started successfully"
    echo "  PID: $VILLAGER_PID"
    echo "  Port: $PORT"
    echo "  Node ID: $NODE_ID"
else
    echo "✗ Failed to start villager node"
    echo "See logs: cat /tmp/rest_villager_${NODE_ID}.log"
    exit 1
fi

echo ""
echo "3. Verifying registration..."
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
                print(f'✓ Node $NODE_ID has registered with Coordinator')
                found = True
                break
        
        if not found:
            print('⚠ The node may still be registering, please wait a moment...')
    else:
        print('✗ Verification failed: HTTP', response.status_code)
except Exception as e:
    print(f'✗ Verification failed: {e}')
"

echo ""
echo "=================================================================="
echo "  Villager Node Ready!"
echo "=================================================================="
echo ""
echo "You can now connect to this node:"
echo ""
echo "[Using CLI]"
echo "  python interactive_cli.py --port $PORT"
echo ""
echo "[Using AI Agent]"
echo "  python ai_villager_agent.py --port $PORT --name Alice --occupation farmer --gender female --personality 'hardworking farmer'"
echo ""
echo "Stop node: kill $VILLAGER_PID"
echo "View logs: tail -f /tmp/rest_villager_${NODE_ID}.log"
echo ""
