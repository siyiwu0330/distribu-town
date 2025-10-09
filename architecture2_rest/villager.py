"""
村民节点 - Architecture 2 (REST)
每个村民作为独立的REST服务节点
"""

from flask import Flask, request, jsonify
import requests
import sys
import os
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.models import (
    Villager, Occupation, Gender, Inventory,
    PRODUCTION_RECIPES, MERCHANT_PRICES,
    SLEEP_STAMINA, NO_SLEEP_PENALTY
)

app = Flask(__name__)

# 全局状态
villager_state = {
    'node_id': None,
    'villager': None,
    'merchant_address': 'localhost:5001',
    'coordinator_address': 'localhost:5000',
    'messages': []  # 存储接收到的消息
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
        
        # 创建村民后，重新注册到协调器以更新名字和职业
        coordinator_addr = villager_state.get('coordinator_address', 'localhost:5000')
        port = villager_state.get('port')
        node_id = villager_state['node_id']
        
        if port:
            try:
                response = requests.post(
                    f"http://{coordinator_addr}/register",
                    json={
                        'node_id': node_id,
                        'node_type': 'villager',
                        'address': f'localhost:{port}',
                        'name': villager.name,
                        'occupation': villager.occupation.value
                    },
                    timeout=5
                )
                if response.status_code == 200:
                    print(f"[Villager-{node_id}] 已更新协调器: {villager.name} ({villager.occupation.value})")
            except:
                pass
        
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
    
    # 返回村民信息，包含节点ID
    villager_data = villager_state['villager'].to_dict()
    villager_data['node_id'] = villager_state['node_id']
    return jsonify(villager_data)


def _submit_action_internal(action: str) -> dict:
    """内部函数：提交行动到协调器（同步屏障）"""
    villager = villager_state['villager']
    
    if not villager:
        return {'success': False, 'message': 'Villager not initialized'}
    
    # 标记已提交行动
    villager.has_submitted_action = True
    
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
                return {
                    'success': True,
                    'message': '所有村民已准备就绪，时间已推进！',
                    'all_ready': True,
                    'new_time': result.get('new_time')
                }
            else:
                # 还在等待其他人
                waiting_for = result.get('waiting_for', [])
                return {
                    'success': True,
                    'message': f"已提交'{action}'行动，等待其他村民",
                    'all_ready': False,
                    'waiting_for': waiting_for
                }
        else:
            return {'success': False, 'message': f'协调器返回错误: {response.status_code}'}
    
    except Exception as e:
        return {'success': False, 'message': f'提交失败: {str(e)}'}


@app.route('/action/submit', methods=['POST'])
def submit_action():
    """提交行动到协调器（同步屏障）"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    # 检查是否已提交
    if villager.has_submitted_action:
        return jsonify({'success': False, 'message': '当前时段已经提交过行动'}), 400
    
    data = request.json
    action = data.get('action', 'idle')  # work, sleep, idle
    
    result = _submit_action_internal(action)
    
    if result['success']:
        if result.get('all_ready'):
            return jsonify({
                'success': True,
                'message': result['message'],
                'all_ready': True,
                'new_time': result.get('new_time'),
                'villager': villager.to_dict()
            })
        else:
            # 还在等待其他人
            waiting_for = result.get('waiting_for', [])
            return jsonify({
                'success': True,
                'message': result['message'],
                'all_ready': False,
                'waiting_for': waiting_for,
                'villager': villager.to_dict()
            })
    else:
        return jsonify({'success': False, 'message': result.get('message', '提交行动失败')}), 500


@app.route('/action/produce', methods=['POST'])
def produce():
    """执行生产（完成后自动提交work）"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    # 检查当前时段是否已提交行动
    if villager.has_submitted_action:
        return jsonify({'success': False, 'message': '当前时段已经提交过行动，请等待时间推进'}), 400
    
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
    
    # 生产产出
    villager.inventory.add_item(recipe.output_item, recipe.output_quantity)
    
    print(f"[Villager-{villager_state['node_id']}] {villager.name} 生产了 {recipe.output_quantity}x {recipe.output_item}")
    print(f"  消耗体力: {recipe.stamina_cost}, 剩余: {villager.stamina}")
    
    # 自动提交work行动
    submit_result = _submit_action_internal('work')
    
    return jsonify({
        'success': True,
        'message': f"生产成功: {recipe.output_quantity}x {recipe.output_item}。{submit_result.get('message', '')}",
        'villager': villager.to_dict(),
        'submit_result': submit_result
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
    """睡眠（完成后自动提交sleep）"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    # 检查当前时段是否已提交行动
    if villager.has_submitted_action:
        return jsonify({'success': False, 'message': '当前时段已经提交过行动，请等待时间推进'}), 400
    
    if villager.has_slept:
        return jsonify({'success': False, 'message': '今天已经睡过了'}), 400
    
    # 检查是否有房子或临时房间券
    has_house = villager.inventory.has_item("house", 1)
    has_temp_room = villager.inventory.has_item("temp_room", 1)
    
    if not has_house and not has_temp_room:
        return jsonify({
            'success': False,
            'message': '没有房子或临时房间券，无法睡眠。请从商人处购买临时房间券或建造房子。'
        }), 400
    
    # 预处理睡眠（恢复在这里执行）
    sleep_message = ""
    if has_house:
        sleep_message = "在自己的房子里睡眠"
    else:  # has_temp_room
        sleep_message = "使用临时房间券睡眠（将在每日结算时消耗）"
    
    villager.restore_stamina(SLEEP_STAMINA)
    villager.has_slept = True
    
    print(f"[Villager-{villager_state['node_id']}] {villager.name} {sleep_message}，恢复体力 {SLEEP_STAMINA}")
    print(f"  当前体力: {villager.stamina}/{villager.max_stamina}")
    
    # 自动提交sleep行动
    submit_result = _submit_action_internal('sleep')
    
    return jsonify({
        'success': True,
        'message': f'睡眠成功，恢复体力 {SLEEP_STAMINA}。{sleep_message}。{submit_result.get("message", "")}',
        'villager': villager.to_dict(),
        'submit_result': submit_result
    })


@app.route('/action/eat', methods=['POST'])
def eat_food():
    """吃面包恢复体力"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    if not villager.inventory.has_item("bread", 1):
        return jsonify({
            'success': False,
            'message': '没有面包可以吃'
        }), 400
    
    # 吃面包
    old_stamina = villager.stamina
    success = villager.eat_bread()
    
    if success:
        restored = villager.stamina - old_stamina
        print(f"[Villager-{villager_state['node_id']}] {villager.name} 吃了面包，恢复 {restored} 体力")
        print(f"  当前体力: {villager.stamina}/{villager.max_stamina}")
        
        return jsonify({
            'success': True,
            'message': f'吃了面包，恢复 {restored} 体力',
            'villager': villager.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'message': '吃面包失败'
        }), 400


@app.route('/trade/request', methods=['POST'])
def receive_trade_request():
    """接收来自其他村民的交易请求（新系统：资源锁定）"""
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
        'offer_type': offer_type,
        'status': 'pending',  # 等待接受
        'locked_resources': False,  # 资源是否已锁定
        'initiator_confirmed': False,  # 发起方是否已确认
        'receiver_confirmed': False,  # 接收方是否已确认
        'created_at': time.time()
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
    """接受交易（新系统：资源锁定）"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    if not data or 'trade_id' not in data:
        return jsonify({'success': False, 'message': 'Missing trade_id in request'}), 400
    
    trade_id = data['trade_id']
    
    # 查找待处理的交易
    if 'pending_trades' not in villager_state:
        return jsonify({'success': False, 'message': 'No pending trades'}), 400
    
    trade = None
    for t in villager_state['pending_trades']:
        if t['trade_id'] == trade_id and t.get('status') == 'pending':
            trade = t
            break
    
    if not trade:
        return jsonify({'success': False, 'message': 'Trade not found or not pending'}), 400
    
    # 检查并锁定资源
    if trade['offer_type'] == 'buy':
        # 对方想买我的东西，我需要有物品
        if not villager.inventory.has_item(trade['item'], trade['quantity']):
            return jsonify({
                'success': False,
                'message': f"物品不足: {trade['item']} (需要{trade['quantity']})"
            }), 400
        
        # 锁定物品（暂时从库存中移除）
        villager.inventory.remove_item(trade['item'], trade['quantity'])
        print(f"[Villager-{villager_state['node_id']}] 锁定资源: {trade['quantity']}x {trade['item']}")
        
    else:
        # 对方想卖给我，我需要有钱
        if villager.inventory.money < trade['price']:
            return jsonify({
                'success': False,
                'message': f"货币不足 (需要{trade['price']}, 拥有{villager.inventory.money})"
            }), 400
        
        # 锁定金币（暂时从库存中移除）
        villager.inventory.remove_money(trade['price'])
        print(f"[Villager-{villager_state['node_id']}] 锁定资源: {trade['price']}金币")
    
    # 更新交易状态
    trade['status'] = 'accepted'
    trade['locked_resources'] = True
    trade['accepted_at'] = time.time()
    
    print(f"[Villager-{villager_state['node_id']}] 交易已接受: {trade['from']} 的请求 {trade_id}")
    print(f"[Villager-{villager_state['node_id']}] 等待双方确认交易...")
    
    # 通知发起方交易已被接受（通过消息系统）
    try:
        # 发送HTTP请求给发起方，更新其sent_trades状态
        initiator_address = trade.get('from_address')
        if initiator_address:
            update_data = {
                'trade_id': trade_id,
                'status': 'accepted'
            }
            
            response = requests.post(
                f"http://{initiator_address}/trade/status_update",
                json=update_data,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"[Villager-{villager_state['node_id']}] 已通知 {trade['from']}: 交易 {trade_id} 已被接受")
            else:
                print(f"[Villager-{villager_state['node_id']}] 通知发起方失败: HTTP {response.status_code}")
        else:
            print(f"[Villager-{villager_state['node_id']}] 无法通知发起方: 缺少地址信息")
        
    except Exception as e:
        print(f"[Villager-{villager_state['node_id']}] 通知发起方失败: {e}")
    
    return jsonify({
        'success': True,
        'message': 'Trade accepted and resources locked. Waiting for confirmation.',
        'trade': trade
    })


@app.route('/trade/execute', methods=['POST'])
def execute_trade_action():
    """执行交易操作（由Merchant调用）"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    trade_id = data['trade_id']
    action = data['action']
    
    try:
        if action == 'pay':
            # 扣除金钱
            amount = data['amount']
            if villager.inventory.money < amount:
                return jsonify({'success': False, 'message': 'Not enough money'}), 400
            villager.inventory.remove_money(amount)
            print(f"[Villager-{villager_state['node_id']}] 支付 {amount} 金币 (交易 {trade_id})")
        
        elif action == 'refund':
            # 退款
            amount = data['amount']
            villager.inventory.add_money(amount)
            print(f"[Villager-{villager_state['node_id']}] 退款 {amount} 金币 (交易 {trade_id})")
        
        elif action == 'remove_item':
            # 扣除物品
            item = data['item']
            quantity = data['quantity']
            if not villager.inventory.has_item(item, quantity):
                return jsonify({'success': False, 'message': f'Not enough {item}'}), 400
            villager.inventory.remove_item(item, quantity)
            print(f"[Villager-{villager_state['node_id']}] 扣除 {quantity}x {item} (交易 {trade_id})")
        
        elif action == 'add_item':
            # 添加物品
            item = data['item']
            quantity = data['quantity']
            villager.inventory.add_item(item, quantity)
            print(f"[Villager-{villager_state['node_id']}] 获得 {quantity}x {item} (交易 {trade_id})")
        
        elif action == 'receive':
            # 接收金钱
            amount = data['amount']
            villager.inventory.add_money(amount)
            print(f"[Villager-{villager_state['node_id']}] 获得 {amount} 金币 (交易 {trade_id})")
        
        else:
            return jsonify({'success': False, 'message': f'Unknown action: {action}'}), 400
        
        return jsonify({'success': True, 'message': f'Action {action} executed successfully'})
    
    except Exception as e:
        print(f"[Villager-{villager_state['node_id']}] 执行交易操作失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/trade/confirm_notify', methods=['POST'])
def receive_confirm_notification():
    """接收确认通知（用于同步双方确认状态）"""
    data = request.json
    if not data or 'trade_id' not in data:
        return jsonify({'success': False, 'message': 'Missing trade_id'}), 400
    
    trade_id = data['trade_id']
    initiator_confirmed = data.get('initiator_confirmed', False)
    receiver_confirmed = data.get('receiver_confirmed', False)
    
    print(f"[Villager-{villager_state.get('node_id', 'unknown')}] 收到确认通知: {trade_id}")
    
    # 更新sent_trades或pending_trades中的确认状态
    trade = None
    if 'sent_trades' in villager_state:
        for t in villager_state['sent_trades']:
            if t['trade_id'] == trade_id:
                if receiver_confirmed:
                    t['receiver_confirmed'] = True
                if initiator_confirmed:
                    t['initiator_confirmed'] = True
                trade = t
                print(f"[Villager-{villager_state['node_id']}] 更新sent_trades中的确认状态")
                break
    
    if not trade and 'pending_trades' in villager_state:
        for t in villager_state['pending_trades']:
            if t['trade_id'] == trade_id:
                if receiver_confirmed:
                    t['receiver_confirmed'] = True
                if initiator_confirmed:
                    t['initiator_confirmed'] = True
                trade = t
                print(f"[Villager-{villager_state['node_id']}] 更新pending_trades中的确认状态")
                break
    
    if not trade:
        return jsonify({'success': False, 'message': 'Trade not found'}), 400
    
    print(f"[Villager-{villager_state['node_id']}] DEBUG: confirm_notify确认状态检查")
    print(f"[Villager-{villager_state['node_id']}] DEBUG: initiator_confirmed = {trade.get('initiator_confirmed', False)}")
    print(f"[Villager-{villager_state['node_id']}] DEBUG: receiver_confirmed = {trade.get('receiver_confirmed', False)}")
    
    # 检查是否双方都已确认，如果是则完成交易
    if trade.get('initiator_confirmed') and trade.get('receiver_confirmed'):
        # 检查交易是否已经完成（避免双重结算）
        if trade.get('status') == 'completed':
            print(f"[Villager-{villager_state['node_id']}] 交易已完成（已结算过），跳过")
            return jsonify({'success': True, 'message': 'Trade already completed'})
        
        print(f"[Villager-{villager_state['node_id']}] 双方已确认，执行交易结算")
        
        villager = villager_state['villager']
        if not villager:
            return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
        
        # 获取交易对方的名称
        other_party = trade.get('target') or trade.get('from')
        is_initiator = 'target' in trade  # sent_trades中有target字段，表示是发起方
        
        # 执行资源转移（根据角色和交易类型）
        if is_initiator:
            # 我是发起方
            if trade['offer_type'] == 'buy':
                # 我发起购买，我应该获得物品
                villager.inventory.add_item(trade['item'], trade['quantity'])
                print(f"[Villager-{villager_state['node_id']}] 交易完成: 从 {other_party} 购买 {trade['quantity']}x {trade['item']}, 支付 {trade['price']}金币")
            else:
                # 我发起出售，我应该获得金钱
                villager.inventory.add_money(trade['price'])
                print(f"[Villager-{villager_state['node_id']}] 交易完成: 出售 {trade['quantity']}x {trade['item']} 给 {other_party}, 获得 {trade['price']}金币")
        else:
            # 我是接收方
            if trade['offer_type'] == 'buy':
                # 对方想买我的东西，我是出售方，我应该获得金钱
                villager.inventory.add_money(trade['price'])
                print(f"[Villager-{villager_state['node_id']}] 交易完成: 出售 {trade['quantity']}x {trade['item']} 给 {other_party}, 获得 {trade['price']}金币")
            else:
                # 对方想卖给我，我是购买方，我应该获得物品
                villager.inventory.add_item(trade['item'], trade['quantity'])
                print(f"[Villager-{villager_state['node_id']}] 交易完成: 从 {other_party} 购买 {trade['quantity']}x {trade['item']}, 支付 {trade['price']}金币")
        
        # 清理交易记录
        if 'pending_trades' in villager_state:
            villager_state['pending_trades'] = [
                t for t in villager_state['pending_trades']
                if t.get('trade_id') != trade_id
            ]
        
        if 'sent_trades' in villager_state:
            villager_state['sent_trades'] = [
                t for t in villager_state['sent_trades']
                if t.get('trade_id') != trade_id
            ]
    
    return jsonify({'success': True, 'message': 'Confirmation received'})


@app.route('/trade/complete_notify', methods=['POST'])
def receive_complete_notification():
    """接收交易完成通知（标记交易为已完成，避免重复结算）"""
    data = request.json
    if not data or 'trade_id' not in data:
        return jsonify({'success': False, 'message': 'Missing trade_id'}), 400
    
    trade_id = data['trade_id']
    
    print(f"[Villager-{villager_state.get('node_id', 'unknown')}] 收到交易完成通知: {trade_id}")
    
    # 在sent_trades或pending_trades中标记为已完成
    trade_found = False
    
    if 'sent_trades' in villager_state:
        for t in villager_state['sent_trades']:
            if t['trade_id'] == trade_id:
                t['status'] = 'completed'
                trade_found = True
                print(f"[Villager-{villager_state['node_id']}] 标记sent_trades中的交易为已完成")
                break
    
    if not trade_found and 'pending_trades' in villager_state:
        for t in villager_state['pending_trades']:
            if t['trade_id'] == trade_id:
                t['status'] = 'completed'
                trade_found = True
                print(f"[Villager-{villager_state['node_id']}] 标记pending_trades中的交易为已完成")
                break
    
    return jsonify({'success': True, 'message': 'Completion notification received'})


@app.route('/trade/status_update', methods=['POST'])
def update_trade_status():
    """更新交易状态（用于发起方更新sent_trades）"""
    data = request.json
    if not data or 'trade_id' not in data or 'status' not in data:
        print(f"[Villager-{villager_state.get('node_id', 'unknown')}] 状态更新失败: 缺少参数")
        return jsonify({'success': False, 'message': 'Missing trade_id or status'}), 400
    
    trade_id = data['trade_id']
    new_status = data['status']
    
    print(f"[Villager-{villager_state.get('node_id', 'unknown')}] 收到状态更新请求: {trade_id} -> {new_status}")
    
    # 更新sent_trades中的状态
    if 'sent_trades' in villager_state:
        print(f"[Villager-{villager_state.get('node_id', 'unknown')}] sent_trades内容: {villager_state['sent_trades']}")
        for trade in villager_state['sent_trades']:
            if trade['trade_id'] == trade_id:
                trade['status'] = new_status
                # 同步确认状态字段
                if new_status == 'accepted':
                    trade['receiver_confirmed'] = True
                print(f"[Villager-{villager_state['node_id']}] 更新交易状态: {trade_id} -> {new_status}")
                return jsonify({'success': True, 'message': 'Trade status updated'})
        
        print(f"[Villager-{villager_state.get('node_id', 'unknown')}] 未找到交易: {trade_id}")
    else:
        print(f"[Villager-{villager_state.get('node_id', 'unknown')}] sent_trades不存在")
    
    return jsonify({'success': False, 'message': 'Trade not found in sent_trades'}), 400


@app.route('/trade/confirm', methods=['POST'])
def confirm_trade():
    """确认交易（新系统：双方确认）"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    if not data or 'trade_id' not in data:
        return jsonify({'success': False, 'message': 'Missing trade_id in request'}), 400
    
    trade_id = data['trade_id']
    
    # 查找已接受的交易（在pending_trades中查找）
    trade = None
    if 'pending_trades' in villager_state:
        for t in villager_state['pending_trades']:
            if t['trade_id'] == trade_id and t.get('status') == 'accepted':
                trade = t
                break
    
    # 如果没找到，可能是发起方在确认自己发起的交易
    if not trade and 'sent_trades' in villager_state:
        print(f"[Villager-{villager_state['node_id']}] DEBUG: 在sent_trades中查找交易 {trade_id}")
        print(f"[Villager-{villager_state['node_id']}] DEBUG: sent_trades内容: {villager_state['sent_trades']}")
        for t in villager_state['sent_trades']:
            if t['trade_id'] == trade_id and t.get('status') == 'accepted':
                trade = t
                print(f"[Villager-{villager_state['node_id']}] DEBUG: 在sent_trades中找到交易 {trade_id}")
                break
    
    if not trade:
        return jsonify({'success': False, 'message': 'Trade not found or not accepted'}), 400
    
    # 确定当前用户是发起方还是接收方
    # 如果交易在sent_trades中，当前用户是发起方
    # 如果交易在pending_trades中，当前用户是接收方
    is_initiator = 'target' in trade  # sent_trades中有target字段，表示当前用户是发起方
    
    # 更新确认状态
    if is_initiator:
        # 发起方确认交易，需要锁定资源
        if trade['offer_type'] == 'buy':
            # 我发起购买，需要锁定金币
            if villager.inventory.money < trade['price']:
                return jsonify({
                    'success': False,
                    'message': f"货币不足 (需要{trade['price']}, 拥有{villager.inventory.money})"
                }), 400
            villager.inventory.remove_money(trade['price'])
            print(f"[Villager-{villager_state['node_id']}] 锁定资源: {trade['price']}金币")
        else:
            # 我发起出售，需要锁定物品
            if not villager.inventory.has_item(trade['item'], trade['quantity']):
                return jsonify({
                    'success': False,
                    'message': f"物品不足: {trade['item']} (需要{trade['quantity']})"
                }), 400
            villager.inventory.remove_item(trade['item'], trade['quantity'])
            print(f"[Villager-{villager_state['node_id']}] 锁定资源: {trade['quantity']}x {trade['item']}")
        
        trade['initiator_confirmed'] = True
        trade['locked_resources'] = True
        print(f"[Villager-{villager_state['node_id']}] 发起方确认交易: {trade_id}")
        
        # 通知接收方：发起方已确认
        try:
            receiver_address = trade.get('target_address')  # sent_trades中使用target_address
            if receiver_address:
                # 发送确认通知给接收方
                confirm_data = {
                    'trade_id': trade_id,
                    'initiator_confirmed': True
                }
                response = requests.post(
                    f"http://{receiver_address}/trade/confirm_notify",
                    json=confirm_data,
                    timeout=5
                )
                if response.status_code == 200:
                    print(f"[Villager-{villager_state['node_id']}] 已通知接收方: 发起方已确认交易 {trade_id}")
                else:
                    print(f"[Villager-{villager_state['node_id']}] 通知接收方失败: HTTP {response.status_code}")
            else:
                print(f"[Villager-{villager_state['node_id']}] 警告: 无法获取接收方地址")
        except Exception as e:
            print(f"[Villager-{villager_state['node_id']}] 通知接收方失败: {e}")
    else:
        trade['receiver_confirmed'] = True
        print(f"[Villager-{villager_state['node_id']}] 接收方确认交易: {trade_id}")
        
        # 通知发起方：接收方已确认
        try:
            initiator_address = trade.get('from_address')
            if initiator_address:
                confirm_data = {
                    'trade_id': trade_id,
                    'receiver_confirmed': True
                }
                response = requests.post(
                    f"http://{initiator_address}/trade/confirm_notify",
                    json=confirm_data,
                    timeout=5
                )
                if response.status_code == 200:
                    print(f"[Villager-{villager_state['node_id']}] 已通知发起方: 接收方已确认交易 {trade_id}")
        except Exception as e:
            print(f"[Villager-{villager_state['node_id']}] 通知发起方失败: {e}")
    
    trade['confirmed_at'] = time.time()
    
    print(f"[Villager-{villager_state['node_id']}] DEBUG: 确认状态检查")
    print(f"[Villager-{villager_state['node_id']}] DEBUG: initiator_confirmed = {trade.get('initiator_confirmed', False)}")
    print(f"[Villager-{villager_state['node_id']}] DEBUG: receiver_confirmed = {trade.get('receiver_confirmed', False)}")
    
    # 检查是否双方都已确认
    if trade.get('initiator_confirmed', False) and trade.get('receiver_confirmed', False):
        # 双方已确认，但不在这里结算
        # 结算会在confirm_notify中执行（由后确认的一方收到通知后触发）
        # 这里只是检查状态，如果已完成则返回
        if trade.get('status') == 'completed':
            # 交易已经完成了，直接返回
            print(f"[Villager-{villager_state['node_id']}] 交易已完成（已结算过）: {trade_id}")
            return jsonify({
                'success': True,
                'message': 'Trade already completed.',
                'villager': villager.to_dict()
            })
        
        # 如果还没有完成，说明这是第二个确认的人，需要执行结算
        print(f"[Villager-{villager_state['node_id']}] 双方已确认，完成交易: {trade_id}")
        
        # 获取交易对方的名称（sent_trades用target，pending_trades用from）
        other_party = trade.get('target') or trade.get('from')
        is_initiator = 'target' in trade
        
        # 执行实际的资源转移（根据角色和交易类型）
        if is_initiator:
            # 我是发起方
            if trade['offer_type'] == 'buy':
                # 我发起购买，物品已经在confirm时锁定了金币，现在接收物品
                villager.inventory.add_item(trade['item'], trade['quantity'])
                print(f"[Villager-{villager_state['node_id']}] 交易完成: 从 {other_party} 购买 {trade['quantity']}x {trade['item']}, 支付 {trade['price']}金币")
            else:
                # 我发起出售，物品已经在confirm时锁定，现在接收金钱
                villager.inventory.add_money(trade['price'])
                print(f"[Villager-{villager_state['node_id']}] 交易完成: 出售 {trade['quantity']}x {trade['item']} 给 {other_party}, 获得 {trade['price']}金币")
        else:
            # 我是接收方
            if trade['offer_type'] == 'buy':
                # 对方想买我的东西，物品已经在accept时锁定，现在接收金钱
                villager.inventory.add_money(trade['price'])
                print(f"[Villager-{villager_state['node_id']}] 交易完成: 出售 {trade['quantity']}x {trade['item']} 给 {other_party}, 获得 {trade['price']}金币")
            else:
                # 对方想卖给我，金币已经在accept时锁定，现在接收物品
                villager.inventory.add_item(trade['item'], trade['quantity'])
                print(f"[Villager-{villager_state['node_id']}] 交易完成: 从 {other_party} 购买 {trade['quantity']}x {trade['item']}, 支付 {trade['price']}金币")
        
        # 标记交易为已完成
        trade['status'] = 'completed'
        trade['completed_at'] = time.time()
        
        # 清理pending_trades中的已完成交易
        if 'pending_trades' in villager_state:
            villager_state['pending_trades'] = [
                t for t in villager_state['pending_trades']
                if t.get('trade_id') != trade_id
            ]
        
        # 清理sent_trades中的已完成交易
        if 'sent_trades' in villager_state:
            villager_state['sent_trades'] = [
                t for t in villager_state['sent_trades']
                if t.get('trade_id') != trade_id
            ]
        
        # 通知对方交易已完成（避免对方重复结算）
        try:
            if is_initiator:
                # 我是发起方，通知接收方
                target_address = trade.get('target_address')
                if target_address:
                    requests.post(
                        f"http://{target_address}/trade/complete_notify",
                        json={'trade_id': trade_id},
                        timeout=5
                    )
                    print(f"[Villager-{villager_state['node_id']}] 已通知对方交易完成")
            else:
                # 我是接收方，通知发起方
                from_address = trade.get('from_address')
                if from_address:
                    requests.post(
                        f"http://{from_address}/trade/complete_notify",
                        json={'trade_id': trade_id},
                        timeout=5
                    )
                    print(f"[Villager-{villager_state['node_id']}] 已通知对方交易完成")
        except Exception as e:
            print(f"[Villager-{villager_state['node_id']}] 通知对方交易完成失败: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Trade completed successfully.',
            'trade': trade,
            'villager': villager.to_dict()
        })
    else:
        # 等待另一方确认
        return jsonify({
            'success': True,
            'message': 'Confirmation recorded. Waiting for the other party to confirm.',
            'trade': trade
        })


@app.route('/trade/commit', methods=['POST'])
def commit_trade():
    """提交交易（两阶段提交 - 阶段2）"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    trade_id = data['trade_id']
    
    # 查找已准备的交易
    if 'pending_trades' not in villager_state:
        return jsonify({'success': False, 'message': 'No pending trades'}), 400
    
    trade = None
    for t in villager_state['pending_trades']:
        if t['trade_id'] == trade_id and t.get('status') == 'prepared':
            trade = t
            break
    
    if not trade:
        return jsonify({'success': False, 'message': 'Prepared trade not found'}), 400
    
    # 执行交易（转移资源）
    try:
        if trade['offer_type'] == 'buy':
            # 对方想买我的物品，我是出售方
            if not villager.inventory.has_item(trade['item'], trade['quantity']):
                return jsonify({
                    'success': False,
                    'message': f'物品不足: {trade["item"]} (需要{trade["quantity"]})'
                }), 400
            
            # 转移物品和金币
            villager.inventory.remove_item(trade['item'], trade['quantity'])
            villager.inventory.add_money(trade['price'])
            
            print(f"[Villager-{villager_state['node_id']}] 交易完成: 出售 {trade['quantity']}x {trade['item']} 给 {trade['from']}, 获得 {trade['price']}金币")
            
        else:  # offer_type == 'sell'
            # 对方想卖给我，我是购买方
            if not villager.inventory.remove_money(trade['price']):
                return jsonify({
                    'success': False,
                    'message': f'货币不足 (需要{trade["price"]}, 拥有{villager.inventory.money})'
                }), 400
            
            # 接收物品
            villager.inventory.add_item(trade['item'], trade['quantity'])
            
            print(f"[Villager-{villager_state['node_id']}] 交易完成: 从 {trade['from']} 购买 {trade['quantity']}x {trade['item']}, 支付 {trade['price']}金币")
        
        # 标记交易为已完成
        trade['status'] = 'committed'
        trade['committed_at'] = time.time()
        
        # 清理pending_trades中的已完成交易
        villager_state['pending_trades'] = [
            t for t in villager_state['pending_trades']
            if t.get('trade_id') != trade_id
        ]
        
        print(f"[Villager-{villager_state['node_id']}] 交易提交完成: {trade['from']} 的请求 {trade_id}")
        
        return jsonify({
            'success': True,
            'message': 'Trade committed successfully.',
            'villager': villager.to_dict()
        })
        
    except Exception as e:
        print(f"[Villager-{villager_state['node_id']}] 交易提交异常: {e}")
        return jsonify({
            'success': False,
            'message': f'Trade commit failed: {str(e)}'
        }), 500


@app.route('/trade/abort', methods=['POST'])
def abort_trade():
    """中止交易（两阶段提交 - 回滚）"""
    data = request.json
    trade_id = data['trade_id']
    
    # 查找待处理的交易
    if 'pending_trades' not in villager_state:
        return jsonify({'success': False, 'message': 'No pending trades'}), 400
    
    trade = None
    for t in villager_state['pending_trades']:
        if t['trade_id'] == trade_id and t.get('status') in ['pending', 'prepared']:
            trade = t
            break
    
    if not trade:
        return jsonify({'success': False, 'message': 'Trade not found'}), 400
    
    # 标记交易为中止
    trade['status'] = 'aborted'
    trade['aborted_at'] = time.time()
    
    # 清理pending_trades中的已中止交易
    villager_state['pending_trades'] = [
        t for t in villager_state['pending_trades']
        if t.get('trade_id') != trade_id
    ]
    
    print(f"[Villager-{villager_state['node_id']}] 交易中止: {trade_id}")
    
    return jsonify({
        'success': True,
        'message': 'Trade aborted successfully.'
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
    trade_id = data.get('trade_id')  # 获取交易ID用于清理
    
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
        
        # 清理pending_trades中的已完成交易
        if 'pending_trades' in villager_state and trade_id:
            villager_state['pending_trades'] = [
                t for t in villager_state['pending_trades']
                if t.get('trade_id') != trade_id
            ]
            print(f"[Villager-{villager_state['node_id']}] 已清理交易记录: {trade_id}")
        
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
    else:
        # 每个时段重置行动状态
        villager.reset_time_period()
        print(f"[Villager-{villager_state['node_id']}] 进入新时段")
        print(f"  当前时段: {data['time_of_day']}")
    
    print(f"  可以开始新的行动（工作/睡眠/空闲）")
    
    return jsonify({'success': True, 'message': 'Time updated'})


# ==================== 消息系统 API ====================

@app.route('/messages', methods=['GET'])
def get_messages():
    """获取所有消息"""
    return jsonify({
        'success': True,
        'messages': villager_state['messages']
    })


@app.route('/messages', methods=['POST'])
def receive_message():
    """接收消息（由其他节点或协调器调用）"""
    try:
        data = request.json
        message = {
            'id': len(villager_state['messages']) + 1,
            'from': data['from'],
            'to': data.get('to', 'all'),  # 'all' 表示广播消息
            'type': data['type'],  # 'private' 或 'broadcast'
            'content': data['content'],
            'timestamp': data.get('timestamp', ''),
            'read': False
        }
        
        villager_state['messages'].append(message)
        
        # 打印消息通知
        if message['type'] == 'broadcast':
            print(f"[Villager-{villager_state['node_id']}] 📢 收到广播消息: {message['from']}: {message['content']}")
        else:
            print(f"[Villager-{villager_state['node_id']}] 💬 收到私聊消息: {message['from']}: {message['content']}")
        
        return jsonify({'success': True, 'message': 'Message received'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/messages/send', methods=['POST'])
def send_message():
    """发送消息"""
    try:
        data = request.json
        target = data['target']  # 目标节点ID或'all'表示广播
        content = data['content']
        message_type = data.get('type', 'private')  # 'private' 或 'broadcast'
        
        villager = villager_state['villager']
        if not villager:
            return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
        
        sender_name = villager.name
        
        if message_type == 'broadcast':
            # 通过协调器发送广播消息
            coordinator_addr = villager_state['coordinator_address']
            response = requests.post(
                f"http://{coordinator_addr}/messages/broadcast",
                json={
                    'from': villager_state['node_id'],
                    'from_name': sender_name,
                    'content': content
                },
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"[Villager-{villager_state['node_id']}] 📢 发送广播消息: {content}")
                return jsonify({'success': True, 'message': 'Broadcast message sent'})
            else:
                return jsonify({'success': False, 'message': 'Failed to send broadcast'}), 500
        
        else:
            # 发送点对点消息
            # 首先从协调器获取目标节点地址
            coordinator_addr = villager_state['coordinator_address']
            nodes_response = requests.get(f"http://{coordinator_addr}/nodes", timeout=5)
            
            if nodes_response.status_code != 200:
                return jsonify({'success': False, 'message': 'Failed to get node list'}), 500
            
            nodes_data = nodes_response.json()
            target_node = None
            
            for node in nodes_data['nodes']:
                if node['node_id'] == target or node.get('name') == target:
                    target_node = node
                    break
            
            if not target_node:
                return jsonify({'success': False, 'message': f'Target node not found: {target}'}), 404
            
            # 发送消息到目标节点
            target_response = requests.post(
                f"http://{target_node['address']}/messages",
                json={
                    'from': villager_state['node_id'],
                    'from_name': sender_name,
                    'to': target_node['node_id'],
                    'type': 'private',
                    'content': content,
                    'timestamp': ''
                },
                timeout=5
            )
            
            if target_response.status_code == 200:
                print(f"[Villager-{villager_state['node_id']}] 💬 发送私聊消息到 {target}: {content}")
                return jsonify({'success': True, 'message': 'Private message sent'})
            else:
                return jsonify({'success': False, 'message': 'Failed to send private message'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/messages/mark_read', methods=['POST'])
def mark_message_read():
    """标记消息为已读"""
    try:
        data = request.json
        message_id = data.get('message_id')
        
        if message_id:
            # 标记特定消息为已读
            for msg in villager_state['messages']:
                if msg['id'] == message_id:
                    msg['read'] = True
                    break
        else:
            # 标记所有消息为已读
            for msg in villager_state['messages']:
                msg['read'] = True
        
        return jsonify({'success': True, 'message': 'Messages marked as read'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/mytrades', methods=['GET'])
def get_my_trades():
    """获取发送的交易请求"""
    try:
        # 返回发送的交易请求列表
        sent_trades = villager_state.get('sent_trades', [])
        return jsonify({
            'success': True,
            'trades': sent_trades
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/sent_trades/add', methods=['POST'])
def add_sent_trade():
    """添加发送的交易记录"""
    try:
        data = request.json
        
        # 初始化 sent_trades 列表
        if 'sent_trades' not in villager_state:
            villager_state['sent_trades'] = []
        
        # 添加交易记录
        villager_state['sent_trades'].append(data)
        
        return jsonify({'success': True, 'message': 'Trade record added'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def register_to_coordinator(coordinator_addr, port, node_id):
    """注册到协调器"""
    import time
    time.sleep(2)  # 等待服务启动
    
    try:
        # 获取村民名字（如果已创建）
        villager_name = None
        if villager_state.get('villager'):
            villager_name = villager_state['villager'].name
        
        response = requests.post(
            f"http://{coordinator_addr}/register",
            json={
                'node_id': node_id,
                'node_type': 'villager',
                'address': f'localhost:{port}',
                'name': villager_name or node_id
            },
            timeout=5
        )
        
        if response.status_code == 200:
            if villager_name:
                print(f"[Villager-{node_id}] ({villager_name}) 成功注册到协调器: {coordinator_addr}")
            else:
                print(f"[Villager-{node_id}] 成功注册到协调器: {coordinator_addr}")
        else:
            print(f"[Villager-{node_id}] 注册失败: {response.status_code}")
    
    except Exception as e:
        print(f"[Villager-{node_id}] 无法连接到协调器 {coordinator_addr}: {e}")


def run_server(port, node_id, coordinator_addr='localhost:5000'):
    """运行服务器"""
    villager_state['node_id'] = node_id
    villager_state['coordinator_address'] = coordinator_addr
    villager_state['port'] = port
    
    print(f"[Villager-{node_id}] REST村民节点启动在端口 {port}")
    print(f"[Villager-{node_id}] 节点ID: {node_id} (村民名字将在create时设置)")
    
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

