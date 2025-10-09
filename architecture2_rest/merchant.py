"""
商人节点 - Architecture 2 (REST)
提供固定价格的物品买卖服务
+ 中心化交易管理系统
+ 价格波动机制
"""

from flask import Flask, request, jsonify
import requests
import sys
import os
import threading
import time
import uuid
import random
import copy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.models import MERCHANT_PRICES

app = Flask(__name__)

# 全局状态
node_id = "merchant"
prices = MERCHANT_PRICES

# 交易管理系统
trade_counter = 0
active_trades = {}  # trade_id -> trade_data


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


# ==================== 中心化交易系统 ====================

@app.route('/trade/create', methods=['POST'])
def create_trade():
    """创建交易（由发起方调用）"""
    global trade_counter
    
    data = request.json
    initiator_id = data['initiator_id']  # 发起方node_id
    initiator_address = data['initiator_address']  # 发起方地址
    target_id = data['target_id']  # 目标方node_id
    target_address = data['target_address']  # 目标方地址
    offer_type = data['offer_type']  # 'buy' or 'sell'
    item = data['item']
    quantity = data['quantity']
    price = data['price']
    
    # 生成全局唯一的交易ID
    trade_counter += 1
    trade_id = f"trade_{trade_counter}"
    
    # 创建交易记录
    trade_data = {
        'trade_id': trade_id,
        'initiator_id': initiator_id,
        'initiator_address': initiator_address,
        'target_id': target_id,
        'target_address': target_address,
        'offer_type': offer_type,
        'item': item,
        'quantity': quantity,
        'price': price,
        'status': 'pending',  # pending -> accepted -> confirmed -> completed
        'initiator_confirmed': False,
        'target_confirmed': False,
        'created_at': time.time()
    }
    
    active_trades[trade_id] = trade_data
    
    print(f"[Merchant-Trade] 创建交易 {trade_id}: {initiator_id} -> {target_id}")
    print(f"[Merchant-Trade]   {offer_type} {quantity}x {item} for {price} gold")
    
    return jsonify({
        'success': True,
        'trade_id': trade_id,
        'message': 'Trade created successfully'
    })


@app.route('/trade/list', methods=['GET'])
def list_trades():
    """查询交易列表"""
    node_id_param = request.args.get('node_id')
    trade_type = request.args.get('type', 'all')  # 'pending', 'sent', 'all'
    
    if not node_id_param:
        return jsonify({'success': False, 'message': 'Missing node_id parameter'}), 400
    
    result_trades = []
    
    for trade_id, trade in active_trades.items():
        if trade_type == 'pending' and trade['target_id'] == node_id_param:
            # 收到的待处理交易
            result_trades.append(trade)
        elif trade_type == 'sent' and trade['initiator_id'] == node_id_param:
            # 自己发起的交易
            result_trades.append(trade)
        elif trade_type == 'all' and (trade['initiator_id'] == node_id_param or trade['target_id'] == node_id_param):
            # 所有相关交易
            result_trades.append(trade)
    
    return jsonify({
        'success': True,
        'trades': result_trades
    })


@app.route('/trade/accept', methods=['POST'])
def accept_trade():
    """接受交易（由目标方调用）"""
    data = request.json
    trade_id = data['trade_id']
    node_id_param = data['node_id']
    
    if trade_id not in active_trades:
        return jsonify({'success': False, 'message': 'Trade not found'}), 404
    
    trade = active_trades[trade_id]
    
    # 验证是否是目标方
    if trade['target_id'] != node_id_param:
        return jsonify({'success': False, 'message': 'Only target can accept trade'}), 403
    
    # 检查状态
    if trade['status'] != 'pending':
        return jsonify({'success': False, 'message': f"Trade status is {trade['status']}, cannot accept"}), 400
    
    # 检查目标方的资源
    target_address = trade['target_address']
    try:
        # 获取目标方的村民信息
        response = requests.get(f"http://{target_address}/villager", timeout=5)
        if response.status_code != 200:
            return jsonify({'success': False, 'message': 'Cannot get target villager info'}), 400
        
        villager_data = response.json()
        inventory = villager_data.get('inventory', {})
        money = inventory.get('money', 0)
        items = inventory.get('items', {})
        
        # 检查资源是否足够
        if trade['offer_type'] == 'buy':
            # 发起方想买，目标方要卖，检查目标方是否有物品
            if trade['item'] not in items or items[trade['item']] < trade['quantity']:
                return jsonify({
                    'success': False,
                    'message': f"Target does not have enough {trade['item']}"
                }), 400
        else:
            # 发起方想卖，目标方要买，检查目标方是否有钱
            if money < trade['price']:
                return jsonify({
                    'success': False,
                    'message': f"Target does not have enough money"
                }), 400
        
        # 更新交易状态
        trade['status'] = 'accepted'
        trade['accepted_at'] = time.time()
        
        print(f"[Merchant-Trade] 交易 {trade_id} 被接受: {trade['target_id']}")
        
        return jsonify({
            'success': True,
            'message': 'Trade accepted',
            'trade': trade
        })
    
    except Exception as e:
        print(f"[Merchant-Trade] 接受交易失败: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/trade/confirm', methods=['POST'])
def confirm_trade():
    """确认交易（双方都需要调用）"""
    data = request.json
    trade_id = data['trade_id']
    node_id_param = data['node_id']
    
    if trade_id not in active_trades:
        return jsonify({'success': False, 'message': 'Trade not found'}), 404
    
    trade = active_trades[trade_id]
    
    # 检查状态
    if trade['status'] != 'accepted':
        return jsonify({'success': False, 'message': f"Trade status is {trade['status']}, must be accepted"}), 400
    
    # 确定是发起方还是目标方
    if node_id_param == trade['initiator_id']:
        trade['initiator_confirmed'] = True
        print(f"[Merchant-Trade] 发起方确认交易: {trade_id}")
    elif node_id_param == trade['target_id']:
        trade['target_confirmed'] = True
        print(f"[Merchant-Trade] 目标方确认交易: {trade_id}")
    else:
        return jsonify({'success': False, 'message': 'Invalid node_id for this trade'}), 403
    
    # 检查是否双方都确认
    if trade['initiator_confirmed'] and trade['target_confirmed']:
        # 执行交易
        print(f"[Merchant-Trade] 双方已确认，执行交易: {trade_id}")
        
        try:
            # 执行原子交易
            success = execute_trade(trade)
            
            if success:
                trade['status'] = 'completed'
                trade['completed_at'] = time.time()
                
                # 从活跃交易中移除
                del active_trades[trade_id]
                
                print(f"[Merchant-Trade] 交易完成: {trade_id}")
                
                return jsonify({
                    'success': True,
                    'message': 'Trade completed successfully',
                    'trade': trade
                })
            else:
                return jsonify({'success': False, 'message': 'Trade execution failed'}), 500
        
        except Exception as e:
            print(f"[Merchant-Trade] 交易执行失败: {e}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    else:
        # 等待另一方确认
        return jsonify({
            'success': True,
            'message': 'Confirmation recorded. Waiting for the other party.',
            'trade': trade
        })


def execute_trade(trade):
    """执行交易（原子操作）"""
    try:
        initiator_address = trade['initiator_address']
        target_address = trade['target_address']
        
        # 根据交易类型确定谁给什么
        if trade['offer_type'] == 'buy':
            # 发起方想买
            buyer_address = initiator_address
            seller_address = target_address
        else:
            # 发起方想卖
            buyer_address = target_address
            seller_address = initiator_address
        
        # 1. 买方扣钱
        response = requests.post(
            f"http://{buyer_address}/trade/execute",
            json={
                'trade_id': trade['trade_id'],
                'action': 'pay',
                'amount': trade['price']
            },
            timeout=5
        )
        if response.status_code != 200:
            print(f"[Merchant-Trade] 买方支付失败")
            return False
        
        # 2. 卖方扣物品
        response = requests.post(
            f"http://{seller_address}/trade/execute",
            json={
                'trade_id': trade['trade_id'],
                'action': 'remove_item',
                'item': trade['item'],
                'quantity': trade['quantity']
            },
            timeout=5
        )
        if response.status_code != 200:
            print(f"[Merchant-Trade] 卖方扣除物品失败")
            # 回滚买方的钱
            requests.post(
                f"http://{buyer_address}/trade/execute",
                json={
                    'trade_id': trade['trade_id'],
                    'action': 'refund',
                    'amount': trade['price']
                },
                timeout=5
            )
            return False
        
        # 3. 买方加物品
        response = requests.post(
            f"http://{buyer_address}/trade/execute",
            json={
                'trade_id': trade['trade_id'],
                'action': 'add_item',
                'item': trade['item'],
                'quantity': trade['quantity']
            },
            timeout=5
        )
        if response.status_code != 200:
            print(f"[Merchant-Trade] 买方接收物品失败")
            return False
        
        # 4. 卖方加钱
        response = requests.post(
            f"http://{seller_address}/trade/execute",
            json={
                'trade_id': trade['trade_id'],
                'action': 'receive',
                'amount': trade['price']
            },
            timeout=5
        )
        if response.status_code != 200:
            print(f"[Merchant-Trade] 卖方接收金钱失败")
            return False
        
        print(f"[Merchant-Trade] 交易执行成功: {trade['initiator_id']} <-> {trade['target_id']}")
        return True
    
    except Exception as e:
        print(f"[Merchant-Trade] 交易执行异常: {e}")
        return False


@app.route('/trade/reject', methods=['POST'])
def reject_trade():
    """拒绝交易（目标方拒绝）"""
    data = request.json
    trade_id = data['trade_id']
    node_id_param = data['node_id']
    
    if trade_id not in active_trades:
        return jsonify({'success': False, 'message': 'Trade not found'}), 404
    
    trade = active_trades[trade_id]
    
    # 只有目标方可以拒绝
    if trade['target_id'] != node_id_param:
        return jsonify({'success': False, 'message': 'Only target can reject trade'}), 403
    
    # 只有pending状态的交易可以拒绝
    if trade['status'] != 'pending':
        return jsonify({'success': False, 'message': f"Cannot reject trade with status {trade['status']}"}), 400
    
    del active_trades[trade_id]
    
    print(f"[Merchant-Trade] 交易已拒绝: {trade_id} by {node_id_param}")
    
    return jsonify({
        'success': True,
        'message': 'Trade rejected'
    })


@app.route('/trade/cancel', methods=['POST'])
def cancel_trade():
    """取消交易（发起方取消）"""
    data = request.json
    trade_id = data['trade_id']
    node_id_param = data['node_id']
    
    if trade_id not in active_trades:
        return jsonify({'success': False, 'message': 'Trade not found'}), 404
    
    trade = active_trades[trade_id]
    
    # 只有发起方可以取消
    if trade['initiator_id'] != node_id_param:
        return jsonify({'success': False, 'message': 'Only initiator can cancel trade'}), 403
    
    # 只有pending状态的交易可以取消
    if trade['status'] != 'pending':
        return jsonify({'success': False, 'message': f"Cannot cancel trade with status {trade['status']}"}), 400
    
    del active_trades[trade_id]
    
    print(f"[Merchant-Trade] 交易已取消: {trade_id}")
    
    return jsonify({
        'success': True,
        'message': 'Trade cancelled'
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

