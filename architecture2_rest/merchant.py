"""
商人节点 - Architecture 2 (REST)
提供固定价格的物品买卖服务
"""

from flask import Flask, request, jsonify
import requests
import sys
import os
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.models import MERCHANT_PRICES

app = Flask(__name__)

# 全局状态
node_id = "merchant"
prices = MERCHANT_PRICES


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'healthy', 'service': 'merchant', 'node_id': node_id})


@app.route('/prices', methods=['GET'])
def get_prices():
    """获取价格表"""
    return jsonify(prices)


@app.route('/buy', methods=['POST'])
def buy_item():
    """玩家从商人处购买物品"""
    data = request.json
    buyer_id = data['buyer_id']
    item = data['item']
    quantity = data['quantity']
    
    # 检查商人是否出售该物品
    if item not in prices['buy']:
        return jsonify({
            'success': False,
            'message': f'商人不出售 {item}'
        }), 400
    
    price = prices['buy'][item]
    total_cost = price * quantity
    
    print(f"[Merchant] {buyer_id} 购买 {quantity}x {item}, 总价: {total_cost}")
    
    return jsonify({
        'success': True,
        'message': f'出售 {quantity}x {item} 给 {buyer_id}',
        'total_cost': total_cost
    })


@app.route('/sell', methods=['POST'])
def sell_item():
    """玩家向商人出售物品"""
    data = request.json
    seller_id = data['seller_id']
    item = data['item']
    quantity = data['quantity']
    
    # 检查商人是否收购该物品
    if item not in prices['sell']:
        return jsonify({
            'success': False,
            'message': f'商人不收购 {item}'
        }), 400
    
    price = prices['sell'][item]
    total_income = price * quantity
    
    print(f"[Merchant] 从 {seller_id} 收购 {quantity}x {item}, 支付: {total_income}")
    
    return jsonify({
        'success': True,
        'message': f'收购 {quantity}x {item} 从 {seller_id}',
        'total_income': total_income
    })


@app.route('/time/advance', methods=['POST'])
def on_time_advance():
    """时间推进通知"""
    data = request.json
    print(f"[Merchant] 时间推进: Day {data['day']} {data['time_of_day']}")
    
    return jsonify({
        'success': True,
        'message': 'Time updated'
    })


def register_to_coordinator(coordinator_addr, port):
    """注册到协调器"""
    import time
    time.sleep(2)  # 等待服务启动
    
    try:
        response = requests.post(
            f"http://{coordinator_addr}/register",
            json={
                'node_id': node_id,
                'node_type': 'merchant',
                'address': f'localhost:{port}'
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"[Merchant] 成功注册到协调器: {coordinator_addr}")
        else:
            print(f"[Merchant] 注册失败: {response.status_code}")
    
    except Exception as e:
        print(f"[Merchant] 无法连接到协调器 {coordinator_addr}: {e}")


def run_server(port=5001, coordinator_addr='localhost:5000'):
    """运行服务器"""
    print(f"[Merchant] REST商人节点启动在端口 {port}")
    print(f"[Merchant] 出售价格: {prices['buy']}")
    print(f"[Merchant] 收购价格: {prices['sell']}")
    
    # 在后台线程注册到协调器
    threading.Thread(
        target=register_to_coordinator,
        args=(coordinator_addr, port),
        daemon=True
    ).start()
    
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='REST商人节点服务')
    parser.add_argument('--port', type=int, default=5001, help='监听端口')
    parser.add_argument('--coordinator', type=str, default='localhost:5000',
                       help='协调器地址')
    args = parser.parse_args()
    
    run_server(args.port, args.coordinator)

