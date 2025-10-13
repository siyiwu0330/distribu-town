#!/bin/bash

echo ""
echo "=================================================================="
echo "  Start Base Service Nodes (Coordinator + Merchant) - REST Version"
echo "=================================================================="
echo ""

cd "$(dirname "$0")"

# Clean up old processes
echo "1. Cleaning old processes..."
pkill -9 -f 'python.*(coordinator|merchant)\.py' 2>/dev/null
sleep 1

# Check and free occupied ports
for port in 5000 5001; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo "⚠ Port $port is in use, cleaning up..."
        PID=$(lsof -ti :$port)
        if [ ! -z "$PID" ]; then
            echo "   Found PID: $PID"
            kill -9 $PID 2>/dev/null
            sleep 1
            echo "✓ Port $port cleared"
        fi
    fi
done

# Start coordinator
echo "2. Starting Coordinator (port 5000)..."
python coordinator.py --port 5000 > /tmp/rest_coord.log 2>&1 &
COORD_PID=$!
sleep 2

# Start merchant
echo "3. Starting Merchant (port 5001)..."
python merchant.py --port 5001 --coordinator localhost:5000 > /tmp/rest_merch.log 2>&1 &
MERCH_PID=$!
sleep 2

echo ""
echo "✓ Base services started"
echo "  Coordinator: PID $COORD_PID (port 5000)"
echo "  Merchant:    PID $MERCH_PID (port 5001)"
echo ""

# Test connections
echo "4. Testing connections..."
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
        print(f'✓ Merchant: {len(data.get(\"buy_prices\", {}))} items')
    else:
        print('✗ Merchant: HTTP', response.status_code)
except Exception as e:
    print(f'✗ Merchant: {e}')
"

echo ""
echo "=================================================================="
echo "  Base Services Ready!"
echo "=================================================================="
echo ""
echo "You can now start villager nodes:"
echo "  ./start_villager.sh <port> <node_id>"
echo ""
echo "Examples:"
echo "  ./start_villager.sh 5002 node1"
echo "  ./start_villager.sh 5003 node2"
echo ""
echo "Stop base services: kill $COORD_PID $MERCH_PID"
echo ""
