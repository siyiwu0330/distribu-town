"""
村民节点 - Architecture 2 (REST)
每个村民作为独立的REST服务节点
"""

from flask import Flask, request, jsonify
import requests
import sys
import os
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.models import (
    Villager, Occupation, Gender, Inventory,
    PRODUCTION_RECIPES, MERCHANT_PRICES,
    RENT_COST, SLEEP_STAMINA, NO_SLEEP_PENALTY
)

app = Flask(__name__)

# 全局状态
villager_state = {
    'node_id': None,
    'villager': None,
    'merchant_address': 'localhost:5001',
    'coordinator_address': 'localhost:5000'
}


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'villager',
        'node_id': villager_state['node_id'],
        'initialized': villager_state['villager'] is not None
    })


@app.route('/villager', methods=['POST'])
def create_villager():
    """创建/初始化村民"""
    try:
        data = request.json
        occupation = Occupation(data['occupation'])
        gender = Gender(data['gender'])
        
        villager = Villager(
            name=data['name'],
            occupation=occupation,
            gender=gender,
            personality=data['personality']
        )
        
        villager_state['villager'] = villager
        
        print(f"[Villager-{villager_state['node_id']}] 创建村民: {villager.name}")
        print(f"  职业: {villager.occupation.value}")
        print(f"  性别: {villager.gender.value}")
        print(f"  性格: {villager.personality}")
        print(f"  体力: {villager.stamina}/{villager.max_stamina}")
        print(f"  货币: {villager.inventory.money}")
        
        return jsonify({
            'success': True,
            'message': f'Villager {villager.name} created successfully',
            'villager': villager.to_dict()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to create villager: {str(e)}'
        }), 400


@app.route('/villager', methods=['GET'])
def get_villager_info():
    """获取村民信息"""
    if not villager_state['villager']:
        return jsonify({
            'success': False,
            'message': 'Villager not initialized'
        }), 400
    
    return jsonify(villager_state['villager'].to_dict())


@app.route('/action/submit', methods=['POST'])
def submit_action():
    """提交行动到协调器（同步屏障）"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    action = data.get('action', 'idle')  # work, sleep, idle
    
    # 提交到协调器
    try:
        coordinator_addr = villager_state['coordinator_address']
        response = requests.post(
            f"http://{coordinator_addr}/action/submit",
            json={
                'node_id': villager_state['node_id'],
                'action': action
            },
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('all_ready'):
                # 所有人都准备好了，时间已推进
                return jsonify({
                    'success': True,
                    'message': '所有村民已准备就绪，时间已推进！',
                    'all_ready': True,
                    'new_time': result.get('new_time'),
                    'villager': villager.to_dict()
                })
            else:
                # 还在等待其他人
                waiting_for = result.get('waiting_for', [])
                return jsonify({
                    'success': True,
                    'message': f"已提交行动，等待其他村民: {', '.join(waiting_for)}",
                    'all_ready': False,
                    'waiting_for': waiting_for,
                    'villager': villager.to_dict()
                })
        else:
            return jsonify({'success': False, 'message': '提交行动失败'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'提交失败: {str(e)}'}), 500


@app.route('/action/produce', methods=['POST'])
def produce():
    """执行生产"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    # 检查是否有行动点
    if villager.action_points <= 0:
        return jsonify({'success': False, 'message': '没有行动点了，请提交行动等待时间推进'}), 400
    
    # 获取生产配方
    recipe = PRODUCTION_RECIPES.get(villager.occupation)
    if not recipe:
        return jsonify({
            'success': False,
            'message': f'职业 {villager.occupation.value} 没有生产配方'
        }), 400
    
    # 检查是否有足够资源
    if not recipe.can_produce(villager.inventory, villager.stamina):
        missing_items = []
        for item, qty in recipe.input_items.items():
            if not villager.inventory.has_item(item, qty):
                have = villager.inventory.items.get(item, 0)
                missing_items.append(f"{item} (需要{qty}, 拥有{have})")
        
        if villager.stamina < recipe.stamina_cost:
            missing_items.append(f"体力不足 (需要{recipe.stamina_cost}, 剩余{villager.stamina})")
        
        return jsonify({
            'success': False,
            'message': f"资源不足: {', '.join(missing_items)}"
        }), 400
    
    # 消耗资源
    for item, quantity in recipe.input_items.items():
        villager.inventory.remove_item(item, quantity)
    
    villager.consume_stamina(recipe.stamina_cost)
    villager.consume_action_point()
    
    # 生产产出
    villager.inventory.add_item(recipe.output_item, recipe.output_quantity)
    
    print(f"[Villager-{villager_state['node_id']}] {villager.name} 生产了 {recipe.output_quantity}x {recipe.output_item}")
    print(f"  消耗体力: {recipe.stamina_cost}, 剩余: {villager.stamina}")
    print(f"  剩余行动点: {villager.action_points}")
    
    return jsonify({
        'success': True,
        'message': f"生产成功: {recipe.output_quantity}x {recipe.output_item}",
        'villager': villager.to_dict()
    })


@app.route('/action/trade', methods=['POST'])
def trade():
    """执行交易"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    target = data['target']  # 'merchant', 'self', or villager node_id
    item = data['item']
    quantity = data['quantity']
    action = data['action']  # 'buy', 'sell', 'buy_from_villager', 'sell_to_villager'
    
    # 如果是与商人交易
    if target == 'merchant':
        return trade_with_merchant(item, quantity, action)
    # 如果是村民间交易的自我处理
    elif target == 'self':
        try:
            price = data.get('price', 0)
            
            if action == 'buy_from_villager':
                # 从其他村民购买：扣钱，加物品
                if not villager.inventory.remove_money(price):
                    return jsonify({
                        'success': False,
                        'message': f'货币不足 (需要{price})'
                    }), 400
                villager.inventory.add_item(item, quantity)
                print(f"[Villager-{villager_state['node_id']}] 从其他村民购买 {quantity}x {item}, 支付 {price}")
                
            elif action == 'sell_to_villager':
                # 卖给其他村民：扣物品，加钱
                if not villager.inventory.remove_item(item, quantity):
                    return jsonify({
                        'success': False,
                        'message': f'物品不足'
                    }), 400
                villager.inventory.add_money(price)
                print(f"[Villager-{villager_state['node_id']}] 卖给其他村民 {quantity}x {item}, 获得 {price}")
            
            return jsonify({
                'success': True,
                'message': 'Trade completed',
                'villager': villager.to_dict()
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'交易失败: {str(e)}'
            }), 500
    else:
        return jsonify({
            'success': False,
            'message': '请使用 trade 命令进行村民间交易'
        }), 400


def trade_with_merchant(item, quantity, action):
    """与商人交易"""
    villager = villager_state['villager']
    merchant_addr = villager_state['merchant_address']
    
    try:
        if action == 'buy':
            # 从商人处购买
            if item not in MERCHANT_PRICES['buy']:
                return jsonify({'success': False, 'message': f'商人不出售 {item}'}), 400
            
            total_cost = MERCHANT_PRICES['buy'][item] * quantity
            
            if not villager.inventory.remove_money(total_cost):
                return jsonify({
                    'success': False,
                    'message': f'货币不足 (需要{total_cost}, 拥有{villager.inventory.money})'
                }), 400
            
            # 调用商人服务
            response = requests.post(
                f"http://{merchant_addr}/buy",
                json={
                    'buyer_id': villager_state['node_id'],
                    'item': item,
                    'quantity': quantity
                },
                timeout=5
            )
            
            if response.status_code == 200:
                villager.inventory.add_item(item, quantity)
                print(f"[Villager-{villager_state['node_id']}] {villager.name} 从商人处购买 {quantity}x {item}, 花费 {total_cost}")
                return jsonify({
                    'success': True,
                    'message': f'购买成功: {quantity}x {item}, 花费 {total_cost}',
                    'villager': villager.to_dict()
                })
            else:
                # 退款
                villager.inventory.add_money(total_cost)
                return jsonify({
                    'success': False,
                    'message': f'购买失败: {response.json().get("message", "Unknown error")}'
                }), 400
        
        elif action == 'sell':
            # 出售给商人
            if item not in MERCHANT_PRICES['sell']:
                return jsonify({'success': False, 'message': f'商人不收购 {item}'}), 400
            
            if not villager.inventory.has_item(item, quantity):
                return jsonify({
                    'success': False,
                    'message': f'物品不足: {item} (需要{quantity})'
                }), 400
            
            total_income = MERCHANT_PRICES['sell'][item] * quantity
            
            # 调用商人服务
            response = requests.post(
                f"http://{merchant_addr}/sell",
                json={
                    'seller_id': villager_state['node_id'],
                    'item': item,
                    'quantity': quantity
                },
                timeout=5
            )
            
            if response.status_code == 200:
                villager.inventory.remove_item(item, quantity)
                villager.inventory.add_money(total_income)
                print(f"[Villager-{villager_state['node_id']}] {villager.name} 向商人出售 {quantity}x {item}, 获得 {total_income}")
                return jsonify({
                    'success': True,
                    'message': f'出售成功: {quantity}x {item}, 获得 {total_income}',
                    'villager': villager.to_dict()
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'出售失败: {response.json().get("message", "Unknown error")}'
                }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'交易失败: {str(e)}'
        }), 500


@app.route('/action/sleep', methods=['POST'])
def sleep():
    """睡眠（准备睡眠，实际在时间推进时执行）"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    if villager.has_slept:
        return jsonify({'success': False, 'message': '今天已经睡过了'}), 400
    
    # 检查是否有房子或足够的钱租房
    has_house = villager.inventory.has_item("house", 1)
    
    if not has_house:
        if villager.inventory.money < RENT_COST:
            return jsonify({
                'success': False,
                'message': f'没有房子且货币不足支付租金 (需要{RENT_COST}，拥有{villager.inventory.money})'
            }), 400
    
    # 预处理睡眠（扣费和恢复在这里执行）
    if not has_house:
        villager.inventory.remove_money(RENT_COST)
        print(f"[Villager-{villager_state['node_id']}] {villager.name} 支付租金 {RENT_COST}")
    
    villager.restore_stamina(SLEEP_STAMINA)
    villager.has_slept = True
    
    print(f"[Villager-{villager_state['node_id']}] {villager.name} 睡眠，恢复体力 {SLEEP_STAMINA}")
    print(f"  当前体力: {villager.stamina}/{villager.max_stamina}")
    
    return jsonify({
        'success': True,
        'message': f'睡眠成功，恢复体力 {SLEEP_STAMINA}。请提交行动等待时间推进',
        'villager': villager.to_dict()
    })


@app.route('/trade/request', methods=['POST'])
def receive_trade_request():
    """接收来自其他村民的交易请求"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    from_villager = data['from']
    item = data['item']
    quantity = data['quantity']
    price = data['price']
    offer_type = data['offer_type']  # 'buy' or 'sell'
    
    # 打印交易请求
    if offer_type == 'buy':
        print(f"\n[Villager-{villager_state['node_id']}] 收到交易请求:")
        print(f"  {from_villager} 想购买 {quantity}x {item}, 出价 {price}金币")
    else:
        print(f"\n[Villager-{villager_state['node_id']}] 收到交易请求:")
        print(f"  {from_villager} 想出售 {quantity}x {item}, 要价 {price}金币")
    
    # 存储待处理的交易请求
    if 'pending_trades' not in villager_state:
        villager_state['pending_trades'] = []
    
    trade_id = f"trade_{len(villager_state['pending_trades'])}"
    villager_state['pending_trades'].append({
        'trade_id': trade_id,
        'from': from_villager,
        'from_address': data['from_address'],
        'item': item,
        'quantity': quantity,
        'price': price,
        'offer_type': offer_type
    })
    
    return jsonify({
        'success': True,
        'message': 'Trade request received',
        'trade_id': trade_id
    })


@app.route('/trade/pending', methods=['GET'])
def get_pending_trades():
    """获取待处理的交易请求"""
    if 'pending_trades' not in villager_state:
        villager_state['pending_trades'] = []
    
    return jsonify({
        'success': True,
        'pending_trades': villager_state['pending_trades']
    })


@app.route('/trade/accept', methods=['POST'])
def accept_trade():
    """接受交易"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    trade_id = data['trade_id']
    
    # 查找交易
    if 'pending_trades' not in villager_state:
        return jsonify({'success': False, 'message': 'No pending trades'}), 400
    
    trade = None
    for t in villager_state['pending_trades']:
        if t['trade_id'] == trade_id:
            trade = t
            break
    
    if not trade:
        return jsonify({'success': False, 'message': 'Trade not found'}), 400
    
    # 检查是否有足够的资源
    if trade['offer_type'] == 'buy':
        # 对方想买我的东西，我需要有物品
        if not villager.inventory.has_item(trade['item'], trade['quantity']):
            return jsonify({
                'success': False,
                'message': f"物品不足: {trade['item']} (需要{trade['quantity']})"
            }), 400
    else:
        # 对方想卖给我，我需要有钱
        if villager.inventory.money < trade['price']:
            return jsonify({
                'success': False,
                'message': f"货币不足 (需要{trade['price']}, 拥有{villager.inventory.money})"
            }), 400
    
    # 标记交易为已接受
    trade['status'] = 'accepted'
    
    print(f"[Villager-{villager_state['node_id']}] 接受交易: {trade['from']} 的请求")
    
    return jsonify({
        'success': True,
        'message': 'Trade accepted. Waiting for initiator to complete.',
        'trade': trade
    })


@app.route('/trade/reject', methods=['POST'])
def reject_trade():
    """拒绝交易"""
    data = request.json
    trade_id = data['trade_id']
    
    if 'pending_trades' not in villager_state:
        return jsonify({'success': False, 'message': 'No pending trades'}), 400
    
    # 移除交易
    villager_state['pending_trades'] = [
        t for t in villager_state['pending_trades'] 
        if t['trade_id'] != trade_id
    ]
    
    print(f"[Villager-{villager_state['node_id']}] 拒绝交易: {trade_id}")
    
    return jsonify({
        'success': True,
        'message': 'Trade rejected'
    })


@app.route('/trade/complete', methods=['POST'])
def complete_trade():
    """完成交易（由发起方调用）"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    from_node = data['from']
    item = data['item']
    quantity = data['quantity']
    price = data['price']
    trade_type = data['type']  # 'buy' or 'sell'
    
    try:
        if trade_type == 'buy':
            # 对方购买我的物品
            if not villager.inventory.has_item(item, quantity):
                return jsonify({
                    'success': False,
                    'message': f'物品不足: {item} (需要{quantity})'
                }), 400
            
            # 转移物品和金币
            villager.inventory.remove_item(item, quantity)
            villager.inventory.add_money(price)
            
            print(f"[Villager-{villager_state['node_id']}] 交易完成: 出售 {quantity}x {item} 给 {from_node}, 获得 {price}金币")
            
        else:  # sell
            # 对方出售物品给我
            if not villager.inventory.remove_money(price):
                return jsonify({
                    'success': False,
                    'message': f'货币不足 (需要{price}, 拥有{villager.inventory.money})'
                }), 400
            
            # 接收物品
            villager.inventory.add_item(item, quantity)
            
            print(f"[Villager-{villager_state['node_id']}] 交易完成: 从 {from_node} 购买 {quantity}x {item}, 支付 {price}金币")
        
        return jsonify({
            'success': True,
            'message': 'Trade completed',
            'villager': villager.to_dict()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'交易失败: {str(e)}'
        }), 500


@app.route('/time/advance', methods=['POST'])
def on_time_advance():
    """时间推进通知"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': True, 'message': 'No villager'})
    
    data = request.json
    print(f"[Villager-{villager_state['node_id']}] 时间推进: Day {data['day']} {data['time_of_day']}")
    
    # 如果是新的一天（早晨）
    if data['time_of_day'] == 'morning':
        # 如果前一天晚上没睡觉，额外扣除体力
        if not villager.has_slept:
            villager.consume_stamina(NO_SLEEP_PENALTY)
            print(f"[Villager-{villager_state['node_id']}] {villager.name} 昨晚没睡觉，额外消耗 {NO_SLEEP_PENALTY} 体力")
        
        # 每日重置
        villager.reset_daily()
        print(f"[Villager-{villager_state['node_id']}] 新的一天！")
        print(f"  体力: {villager.stamina}/{villager.max_stamina}")
        print(f"  行动点: {villager.action_points}")
    
    return jsonify({'success': True, 'message': 'Time updated'})


def register_to_coordinator(coordinator_addr, port, node_id):
    """注册到协调器"""
    import time
    time.sleep(2)  # 等待服务启动
    
    try:
        response = requests.post(
            f"http://{coordinator_addr}/register",
            json={
                'node_id': node_id,
                'node_type': 'villager',
                'address': f'localhost:{port}'
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"[Villager-{node_id}] 成功注册到协调器: {coordinator_addr}")
        else:
            print(f"[Villager-{node_id}] 注册失败: {response.status_code}")
    
    except Exception as e:
        print(f"[Villager-{node_id}] 无法连接到协调器 {coordinator_addr}: {e}")


def run_server(port, node_id, coordinator_addr='localhost:5000'):
    """运行服务器"""
    villager_state['node_id'] = node_id
    villager_state['coordinator_address'] = coordinator_addr
    
    print(f"[Villager-{node_id}] REST村民节点启动在端口 {port}")
    
    # 在后台线程注册到协调器
    threading.Thread(
        target=register_to_coordinator,
        args=(coordinator_addr, port, node_id),
        daemon=True
    ).start()
    
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='REST村民节点服务')
    parser.add_argument('--port', type=int, required=True, help='监听端口')
    parser.add_argument('--id', type=str, required=True, help='节点ID')
    parser.add_argument('--coordinator', type=str, default='localhost:5000',
                       help='协调器地址')
    args = parser.parse_args()
    
    run_server(args.port, args.id, args.coordinator)

