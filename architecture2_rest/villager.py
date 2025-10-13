"""
VillagerNode - Architecture 2 (REST)
Each villager runs as an independent REST service node
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

# Global state
villager_state = {
    'node_id': None,
    'villager': None,
    'merchant_address': os.getenv('MERCHANT_HOST', 'localhost') + ':' + os.getenv('MERCHANT_PORT', '5001'),
    'coordinator_address': os.getenv('COORDINATOR_HOST', 'localhost') + ':' + os.getenv('COORDINATOR_PORT', '5000'),
    'messages': []  # store received messages
}


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'villager',
        'node_id': villager_state['node_id'],
        'initialized': villager_state['villager'] is not None
    })


@app.route('/villager', methods=['POST'])
def create_villager():
    """Create/initialize villager"""
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
        
        print(f"[Villager-{villager_state['node_id']}] Create villager: {villager.name}")
        print(f"  Occupation: {villager.occupation.value}")
        print(f"  Gender: {villager.gender.value}")
        print(f"  Personality: {villager.personality}")
        print(f"  Stamina: {villager.stamina}/{villager.max_stamina}")
        print(f"  Money: {villager.inventory.money}")
        
        # After creating the villager, re-register with the coordinator to update name and occupation
        coordinator_addr = villager_state.get('coordinator_address', f"{os.getenv('COORDINATOR_HOST', 'localhost')}:{os.getenv('COORDINATOR_PORT', '5000')}")
        port = villager_state.get('port')
        node_id = villager_state['node_id']
        
        if port:
            try:
                response = requests.post(
                    f"http://{coordinator_addr}/register",
                    json={
                        'node_id': node_id,
                        'node_type': 'villager',
                        'address': f"{os.getenv('VILLAGER_HOST', 'localhost')}:{port}",
                        'name': villager.name,
                        'occupation': villager.occupation.value
                    },
                    timeout=5
                )
                if response.status_code == 200:
                    print(f"[Villager-{node_id}] Updated coordinator: {villager.name} ({villager.occupation.value})")
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
    """Get villager information"""
    if not villager_state['villager']:
        return jsonify({
            'success': False,
            'message': 'Villager not initialized'
        }), 400
    
    # Return villager info including node_id
    villager_data = villager_state['villager'].to_dict()
    villager_data['node_id'] = villager_state['node_id']
    return jsonify(villager_data)


def _submit_action_internal(action: str) -> dict:
    """Internal function: submit action to coordinator (synchronization barrier)"""
    villager = villager_state['villager']
    
    if not villager:
        return {'success': False, 'message': 'Villager not initialized'}
    
    # Mark action as submitted
    villager.has_submitted_action = True
    
    # Submit to coordinator
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
                # Everyone is ready; time has advanced
                return {
                    'success': True,
                    'message': 'All villagers are ready, time has advanced!',
                    'all_ready': True,
                    'new_time': result.get('new_time')
                }
            else:
                # Still waiting for others
                waiting_for = result.get('waiting_for', [])
                return {
                    'success': True,
                    'message': f"Submitted '{action}' action, waiting for other villagers",
                    'all_ready': False,
                    'waiting_for': waiting_for
                }
        else:
            return {'success': False, 'message': f'Coordinator returned error: {response.status_code}'}
    
    except Exception as e:
        return {'success': False, 'message': f'Failed to submit: {str(e)}'}


@app.route('/action/submit', methods=['POST'])
def submit_action():
    """Submit action to coordinator (synchronization barrier)"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    # Check if already submitted
    if villager.has_submitted_action:
        return jsonify({'success': False, 'message': 'Action already submitted for the current time segment'}), 400
    
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
            # Still waiting for others
            waiting_for = result.get('waiting_for', [])
            return jsonify({
                'success': True,
                'message': result['message'],
                'all_ready': False,
                'waiting_for': waiting_for,
                'villager': villager.to_dict()
            })
    else:
        return jsonify({'success': False, 'message': result.get('message', 'Failed to submit action')}), 500


@app.route('/action/produce', methods=['POST'])
def produce():
    """Execute production (auto-submit 'work')"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    # Check if action already submitted for this time segment
    if villager.has_submitted_action:
        return jsonify({'success': False, 'message': 'Action already submitted for the current time segment; please wait for time to advance'}), 400
    
    # Get production recipe
    recipe = PRODUCTION_RECIPES.get(villager.occupation)
    if not recipe:
        return jsonify({
            'success': False,
            'message': f'No production recipe for occupation {villager.occupation.value}'
        }), 400
    
    # Check if there are enough resources
    if not recipe.can_produce(villager.inventory, villager.stamina):
        missing_items = []
        for item, qty in recipe.input_items.items():
            if not villager.inventory.has_item(item, qty):
                have = villager.inventory.items.get(item, 0)
                missing_items.append(f"{item} (requires {qty}, have {have})")
        
        if villager.stamina < recipe.stamina_cost:
            missing_items.append(f"Insufficient stamina (requires {recipe.stamina_cost}, remaining {villager.stamina})")
        
        return jsonify({
            'success': False,
            'message': f"Insufficient resources: {', '.join(missing_items)}"
        }), 400
    
    # Consume resources
    for item, quantity in recipe.input_items.items():
        villager.inventory.remove_item(item, quantity)
    
    villager.consume_stamina(recipe.stamina_cost)
    
    # Production output
    villager.inventory.add_item(recipe.output_item, recipe.output_quantity)
    
    print(f"[Villager-{villager_state['node_id']}] {villager.name} produced {recipe.output_quantity}x {recipe.output_item}")
    print(f"  Stamina used: {recipe.stamina_cost}, remaining: {villager.stamina}")
    
    # Auto-submit 'work' action
    submit_result = _submit_action_internal('work')
    
    return jsonify({
        'success': True,
        'message': f"Production success: {recipe.output_quantity}x {recipe.output_item}. {submit_result.get('message', '')}",
        'villager': villager.to_dict(),
        'submit_result': submit_result
    })


@app.route('/action/trade', methods=['POST'])
def trade():
    """Execute trade"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    target = data['target']  # 'merchant', 'self', or villager node_id
    item = data['item']
    quantity = data['quantity']
    action = data['action']  # 'buy', 'sell', 'buy_from_villager', 'sell_to_villager'
    
    # Trade with merchant
    if target == 'merchant':
        return trade_with_merchant(item, quantity, action)
    # Self-handling for P2P trade between villagers
    elif target == 'self':
        try:
            price = data.get('price', 0)
            
            if action == 'buy_from_villager':
                # Buying from another villager: deduct money, add item
                if not villager.inventory.remove_money(price):
                    return jsonify({
                        'success': False,
                        'message': f'Insufficient money (requires {price})'
                    }), 400
                villager.inventory.add_item(item, quantity)
                print(f"[Villager-{villager_state['node_id']}] Bought {quantity}x {item} from another villager, paid {price}")
                
            elif action == 'sell_to_villager':
                # Selling to another villager: deduct item, add money
                if not villager.inventory.remove_item(item, quantity):
                    return jsonify({
                        'success': False,
                        'message': f'Insufficient item(s)'
                    }), 400
                villager.inventory.add_money(price)
                print(f"[Villager-{villager_state['node_id']}] Sold {quantity}x {item} to another villager, received {price}")
            
            return jsonify({
                'success': True,
                'message': 'Trade completed',
                'villager': villager.to_dict()
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Trade failed: {str(e)}'
            }), 500
    else:
        return jsonify({
            'success': False,
            'message': 'Please use the trade command for villager-to-villager trades'
        }), 400


def trade_with_merchant(item, quantity, action):
    """Trade with merchant"""
    villager = villager_state['villager']
    merchant_addr = villager_state['merchant_address']
    
    try:
        if action == 'buy':
            # Buy from merchant
            if item not in MERCHANT_PRICES['buy']:
                return jsonify({'success': False, 'message': f'Merchant does not sell {item}'}), 400
            
            total_cost = MERCHANT_PRICES['buy'][item] * quantity
            
            if not villager.inventory.remove_money(total_cost):
                return jsonify({
                    'success': False,
                    'message': f'Insufficient money (requires {total_cost}, have {villager.inventory.money})'
                }), 400
            
            # Call merchant service
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
                print(f"[Villager-{villager_state['node_id']}] {villager.name} bought {quantity}x {item} from merchant, cost {total_cost}")
                return jsonify({
                    'success': True,
                    'message': f'Purchase successful: {quantity}x {item}, cost {total_cost}',
                    'villager': villager.to_dict()
                })
            else:
                # Refund
                villager.inventory.add_money(total_cost)
                return jsonify({
                    'success': False,
                    'message': f'Purchase failed: {response.json().get("message", "Unknown error")}'
                }), 400
        
        elif action == 'sell':
            # Sell to merchant
            if item not in MERCHANT_PRICES['sell']:
                return jsonify({'success': False, 'message': f'Merchant does not buy {item}'}), 400
            
            if not villager.inventory.has_item(item, quantity):
                return jsonify({
                    'success': False,
                    'message': f'Insufficient item(s): {item} (requires {quantity})'
                }), 400
            
            total_income = MERCHANT_PRICES['sell'][item] * quantity
            
            # Call merchant service
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
                print(f"[Villager-{villager_state['node_id']}] {villager.name} sold {quantity}x {item} to merchant, received {total_income}")
                return jsonify({
                    'success': True,
                    'message': f'Sale successful: {quantity}x {item}, received {total_income}',
                    'villager': villager.to_dict()
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Sale failed: {response.json().get("message", "Unknown error")}'
                }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Trade failed: {str(e)}'
        }), 500


@app.route('/action/sleep', methods=['POST'])
def sleep():
    """Sleep (auto-submit 'sleep' after completion)"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    # Check if action already submitted for this time segment
    if villager.has_submitted_action:
        return jsonify({'success': False, 'message': 'Action already submitted for the current time segment; please wait for time to advance'}), 400
    
    if villager.has_slept:
        return jsonify({'success': False, 'message': 'Already slept today'}), 400
    
    # Check for house or temporary room voucher
    has_house = villager.inventory.has_item("house", 1)
    has_temp_room = villager.inventory.has_item("temp_room", 1)
    
    if not has_house and not has_temp_room:
        return jsonify({
            'success': False,
            'message': 'No house or temporary room voucher, cannot sleep. Please buy a temporary room voucher from the merchant or build a house.'
        }), 400
    
    # Pre-handle sleep (restoration happens here)
    sleep_message = ""
    if has_house:
        sleep_message = "Slept in own house"
    else:  # has_temp_room
        sleep_message = "Used a temporary room voucher to sleep (will be consumed at daily settlement)"
    
    villager.restore_stamina(SLEEP_STAMINA)
    villager.has_slept = True
    
    print(f"[Villager-{villager_state['node_id']}] {villager.name} {sleep_message}, restored stamina {SLEEP_STAMINA}")
    print(f"  Current stamina: {villager.stamina}/{villager.max_stamina}")
    
    # Auto-submit sleep action
    submit_result = _submit_action_internal('sleep')
    
    return jsonify({
        'success': True,
        'message': f'Sleep successful, restored {SLEEP_STAMINA} stamina. {sleep_message}. {submit_result.get("message", "")}',
        'villager': villager.to_dict(),
        'submit_result': submit_result
    })


@app.route('/action/eat', methods=['POST'])
def eat_food():
    """Eat bread to restore stamina"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    if not villager.inventory.has_item("bread", 1):
        return jsonify({
            'success': False,
            'message': 'No bread available to eat'
        }), 400
    
    # Eat bread
    old_stamina = villager.stamina
    success = villager.eat_bread()
    
    if success:
        restored = villager.stamina - old_stamina
        print(f"[Villager-{villager_state['node_id']}] {villager.name} ate bread and restored {restored} stamina")
        print(f"  Current stamina: {villager.stamina}/{villager.max_stamina}")
        
        return jsonify({
            'success': True,
            'message': f'Ate bread and restored {restored} stamina',
            'villager': villager.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to eat bread'
        }), 400


@app.route('/trade/request', methods=['POST'])
def receive_trade_request():
    """Receive a trade request from another villager (new system: resource locking)"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    from_villager = data['from']
    item = data['item']
    quantity = data['quantity']
    price = data['price']
    offer_type = data['offer_type']  # 'buy' or 'sell'
    
    # Log the trade request
    if offer_type == 'buy':
        print(f"\n[Villager-{villager_state['node_id']}] Received trade request:")
        print(f"  {from_villager} wants to buy {quantity}x {item} for {price} gold")
    else:
        print(f"\n[Villager-{villager_state['node_id']}] Received trade request:")
        print(f"  {from_villager} wants to sell {quantity}x {item} for {price} gold")
    
    # Store pending trade request
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
        'status': 'pending',           # waiting for accept
        'locked_resources': False,     # whether resources are locked
        'initiator_confirmed': False,  # whether the initiator has confirmed
        'receiver_confirmed': False,   # whether the receiver has confirmed
        'created_at': time.time()
    })
    
    return jsonify({
        'success': True,
        'message': 'Trade request received',
        'trade_id': trade_id
    })


@app.route('/trade/pending', methods=['GET'])
def get_pending_trades():
    """Get pending trade requests"""
    if 'pending_trades' not in villager_state:
        villager_state['pending_trades'] = []
    
    return jsonify({
        'success': True,
        'pending_trades': villager_state['pending_trades']
    })


@app.route('/trade/accept', methods=['POST'])
def accept_trade():
    """Accept trade (new system: resource locking)"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    if not data or 'trade_id' not in data:
        return jsonify({'success': False, 'message': 'Missing trade_id in request'}), 400
    
    trade_id = data['trade_id']
    
    # Find pending trade
    if 'pending_trades' not in villager_state:
        return jsonify({'success': False, 'message': 'No pending trades'}), 400
    
    trade = None
    for t in villager_state['pending_trades']:
        if t['trade_id'] == trade_id and t.get('status') == 'pending':
            trade = t
            break
    
    if not trade:
        return jsonify({'success': False, 'message': 'Trade not found or not pending'}), 400
    
    # Check and lock resources
    if trade['offer_type'] == 'buy':
        # The other party wants to buy my item; I need to have the item
        if not villager.inventory.has_item(trade['item'], trade['quantity']):
            return jsonify({
                'success': False,
                'message': f"Insufficient items: {trade['item']} (requires {trade['quantity']})"
            }), 400
        
        # Lock item (temporarily remove from inventory)
        villager.inventory.remove_item(trade['item'], trade['quantity'])
        print(f"[Villager-{villager_state['node_id']}] Locked resources: {trade['quantity']}x {trade['item']}")
        
    else:
        # The other party wants to sell to me; I need to have enough money
        if villager.inventory.money < trade['price']:
            return jsonify({
                'success': False,
                'message': f"Insufficient money (requires {trade['price']}, have {villager.inventory.money})"
            }), 400
        
        # Lock money (temporarily remove from inventory)
        villager.inventory.remove_money(trade['price'])
        print(f"[Villager-{villager_state['node_id']}] Locked resources: {trade['price']} gold")
    
    # Update trade status
    trade['status'] = 'accepted'
    trade['locked_resources'] = True
    trade['accepted_at'] = time.time()
    
    print(f"[Villager-{villager_state['node_id']}] Trade accepted: request {trade_id} from {trade['from']}")
    print(f"[Villager-{villager_state['node_id']}] Waiting for both parties to confirm the trade...")
    
    # Notify initiator that the trade has been accepted (via HTTP to their node)
    try:
        # Send HTTP request to the initiator to update their sent_trades status
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
                print(f"[Villager-{villager_state['node_id']}] Notified {trade['from']}: Trade {trade_id} has been accepted")
            else:
                print(f"[Villager-{villager_state['node_id']}] Failed to notify initiator: HTTP {response.status_code}")
        else:
            print(f"[Villager-{villager_state['node_id']}] Unable to notify initiator: missing address info")
        
    except Exception as e:
        print(f"[Villager-{villager_state['node_id']}] Failed to notify initiator: {e}")
    
    return jsonify({
        'success': True,
        'message': 'Trade accepted and resources locked. Waiting for confirmation.',
        'trade': trade
    })


@app.route('/trade/execute', methods=['POST'])
def execute_trade_action():
    """Execute trade operation (called by the Merchant)"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    trade_id = data['trade_id']
    action = data['action']
    
    try:
        if action == 'pay':
            # Deduct money
            amount = data['amount']
            if villager.inventory.money < amount:
                return jsonify({'success': False, 'message': 'Not enough money'}), 400
            villager.inventory.remove_money(amount)
            print(f"[Villager-{villager_state['node_id']}] Paid {amount} gold (Trade {trade_id})")
        
        elif action == 'refund':
            # Refund money
            amount = data['amount']
            villager.inventory.add_money(amount)
            print(f"[Villager-{villager_state['node_id']}] Refunded {amount} gold (Trade {trade_id})")
        
        elif action == 'remove_item':
            # Deduct item
            item = data['item']
            quantity = data['quantity']
            if not villager.inventory.has_item(item, quantity):
                return jsonify({'success': False, 'message': f'Not enough {item}'}), 400
            villager.inventory.remove_item(item, quantity)
            print(f"[Villager-{villager_state['node_id']}] Removed {quantity}x {item} (Trade {trade_id})")
        
        elif action == 'add_item':
            # Add item
            item = data['item']
            quantity = data['quantity']
            villager.inventory.add_item(item, quantity)
            print(f"[Villager-{villager_state['node_id']}] Received {quantity}x {item} (Trade {trade_id})")
        
        elif action == 'receive':
            # Receive money
            amount = data['amount']
            villager.inventory.add_money(amount)
            print(f"[Villager-{villager_state['node_id']}] Received {amount} gold (Trade {trade_id})")
        
        else:
            return jsonify({'success': False, 'message': f'Unknown action: {action}'}), 400
        
        return jsonify({'success': True, 'message': f'Action {action} executed successfully'})
    
    except Exception as e:
        print(f"[Villager-{villager_state['node_id']}] Failed to execute trade operation: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/trade/confirm_notify', methods=['POST'])
def receive_confirm_notification():
    """Receive confirmation notification (used to sync both parties' confirmation states)"""
    data = request.json
    if not data or 'trade_id' not in data:
        return jsonify({'success': False, 'message': 'Missing trade_id'}), 400
    
    trade_id = data['trade_id']
    initiator_confirmed = data.get('initiator_confirmed', False)
    receiver_confirmed = data.get('receiver_confirmed', False)
    
    print(f"[Villager-{villager_state.get('node_id', 'unknown')}] Received confirm notification: {trade_id}")
    
    # Update confirm state in sent_trades or pending_trades
    trade = None
    if 'sent_trades' in villager_state:
        for t in villager_state['sent_trades']:
            if t['trade_id'] == trade_id:
                if receiver_confirmed:
                    t['receiver_confirmed'] = True
                if initiator_confirmed:
                    t['initiator_confirmed'] = True
                trade = t
                print(f"[Villager-{villager_state['node_id']}] Updated confirmation state in sent_trades")
                break
    
    if not trade and 'pending_trades' in villager_state:
        for t in villager_state['pending_trades']:
            if t['trade_id'] == trade_id:
                if receiver_confirmed:
                    t['receiver_confirmed'] = True
                if initiator_confirmed:
                    t['initiator_confirmed'] = True
                trade = t
                print(f"[Villager-{villager_state['node_id']}] Updated confirmation state in pending_trades")
                break
    
    if not trade:
        return jsonify({'success': False, 'message': 'Trade not found'}), 400
    
    print(f"[Villager-{villager_state['node_id']}] DEBUG: confirm_notify confirmation state check")
    print(f"[Villager-{villager_state['node_id']}] DEBUG: initiator_confirmed = {trade.get('initiator_confirmed', False)}")
    print(f"[Villager-{villager_state['node_id']}] DEBUG: receiver_confirmed = {trade.get('receiver_confirmed', False)}")
    
    # If both parties confirmed, complete the trade
    if trade.get('initiator_confirmed') and trade.get('receiver_confirmed'):
        # Check if trade already completed (avoid double settlement)
        if trade.get('status') == 'completed':
            print(f"[Villager-{villager_state['node_id']}] Trade already completed (already settled), skipping")
            return jsonify({'success': True, 'message': 'Trade already completed'})
        
        print(f"[Villager-{villager_state['node_id']}] Both confirmed, executing trade settlement")
        
        villager = villager_state['villager']
        if not villager:
            return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
        
        # Get the other party’s name
        other_party = trade.get('target') or trade.get('from')
        is_initiator = 'target' in trade  # sent_trades has 'target' meaning we are initiator
        
        # Execute resource transfer (by role and trade type)
        if is_initiator:
            # I am the initiator
            if trade['offer_type'] == 'buy':
                # I initiated a buy; I should receive items
                villager.inventory.add_item(trade['item'], trade['quantity'])
                print(f"[Villager-{villager_state['node_id']}] Trade completed: bought {trade['quantity']}x {trade['item']} from {other_party}, paid {trade['price']} gold")
            else:
                # I initiated a sell; I should receive money
                villager.inventory.add_money(trade['price'])
                print(f"[Villager-{villager_state['node_id']}] Trade completed: sold {trade['quantity']}x {trade['item']} to {other_party}, received {trade['price']} gold")
        else:
            # I am the receiver
            if trade['offer_type'] == 'buy':
                # Counterparty buys my item; I should receive money
                villager.inventory.add_money(trade['price'])
                print(f"[Villager-{villager_state['node_id']}] Trade completed: sold {trade['quantity']}x {trade['item']} to {other_party}, received {trade['price']} gold")
            else:
                # Counterparty sells to me; I should receive items
                villager.inventory.add_item(trade['item'], trade['quantity'])
                print(f"[Villager-{villager_state['node_id']}] Trade completed: bought {trade['quantity']}x {trade['item']} from {other_party}, paid {trade['price']} gold")
        
        # Clean up trade records
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
    """Receive trade-completion notification (mark completed to avoid double settlement)"""
    data = request.json
    if not data or 'trade_id' not in data:
        return jsonify({'success': False, 'message': 'Missing trade_id'}), 400
    
    trade_id = data['trade_id']
    
    print(f"[Villager-{villager_state.get('node_id', 'unknown')}] Received trade completion notification: {trade_id}")
    
    # Mark as completed in sent_trades or pending_trades
    trade_found = False
    
    if 'sent_trades' in villager_state:
        for t in villager_state['sent_trades']:
            if t['trade_id'] == trade_id:
                t['status'] = 'completed'
                trade_found = True
                print(f"[Villager-{villager_state['node_id']}] Marked trade as completed in sent_trades")
                break
    
    if not trade_found and 'pending_trades' in villager_state:
        for t in villager_state['pending_trades']:
            if t['trade_id'] == trade_id:
                t['status'] = 'completed'
                trade_found = True
                print(f"[Villager-{villager_state['node_id']}] Marked trade as completed in pending_trades")
                break
    
    return jsonify({'success': True, 'message': 'Completion notification received'})


@app.route('/trade/status_update', methods=['POST'])
def update_trade_status():
    """Update trade status (used by initiator to update sent_trades)"""
    data = request.json
    if not data or 'trade_id' not in data or 'status' not in data:
        print(f"[Villager-{villager_state.get('node_id', 'unknown')}] Status update failed: missing params")
        return jsonify({'success': False, 'message': 'Missing trade_id or status'}), 400
    
    trade_id = data['trade_id']
    new_status = data['status']
    
    print(f"[Villager-{villager_state.get('node_id', 'unknown')}] Received status update: {trade_id} -> {new_status}")
    
    # Update status in sent_trades
    if 'sent_trades' in villager_state:
        print(f"[Villager-{villager_state.get('node_id', 'unknown')}] sent_trades content: {villager_state['sent_trades']}")
        for trade in villager_state['sent_trades']:
            if trade['trade_id'] == trade_id:
                trade['status'] = new_status
                # Sync confirmation flags
                if new_status == 'accepted':
                    trade['receiver_confirmed'] = True
                print(f"[Villager-{villager_state['node_id']}] Updated trade status: {trade_id} -> {new_status}")
                return jsonify({'success': True, 'message': 'Trade status updated'})
        
        print(f"[Villager-{villager_state.get('node_id', 'unknown')}] Trade not found: {trade_id}")
    else:
        print(f"[Villager-{villager_state.get('node_id', 'unknown')}] sent_trades does not exist")
    
    return jsonify({'success': False, 'message': 'Trade not found in sent_trades'}), 400


@app.route('/trade/confirm', methods=['POST'])
def confirm_trade():
    """Confirm trade (new system: both parties confirm)"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    if not data or 'trade_id' not in data:
        return jsonify({'success': False, 'message': 'Missing trade_id in request'}), 400
    
    trade_id = data['trade_id']
    
    # Find accepted trade (first look in pending_trades)
    trade = None
    if 'pending_trades' in villager_state:
        for t in villager_state['pending_trades']:
            if t['trade_id'] == trade_id and t.get('status') == 'accepted':
                trade = t
                break
    
    # If not found, maybe the initiator is confirming a trade they initiated
    if not trade and 'sent_trades' in villager_state:
        print(f"[Villager-{villager_state['node_id']}] DEBUG: Searching trade {trade_id} in sent_trades")
        print(f"[Villager-{villager_state['node_id']}] DEBUG: sent_trades content: {villager_state['sent_trades']}")
        for t in villager_state['sent_trades']:
            if t['trade_id'] == trade_id and t.get('status') == 'accepted':
                trade = t
                print(f"[Villager-{villager_state['node_id']}] DEBUG: Found trade {trade_id} in sent_trades")
                break
    
    if not trade:
        return jsonify({'success': False, 'message': 'Trade not found or not accepted'}), 400
    
    # Determine whether current villager is initiator or receiver
    # In sent_trades -> initiator; in pending_trades -> receiver
    is_initiator = 'target' in trade  # sent_trades has 'target' when current user is initiator
    
    # Update confirmation state
    if is_initiator:
        # Initiator confirms and must lock resources
        if trade['offer_type'] == 'buy':
            # I initiated a buy, need to lock gold
            if villager.inventory.money < trade['price']:
                return jsonify({
                    'success': False,
                    'message': f"Insufficient money (requires {trade['price']}, have {villager.inventory.money})"
                }), 400
            villager.inventory.remove_money(trade['price'])
            print(f"[Villager-{villager_state['node_id']}] Locked resources: {trade['price']} gold")
        else:
            # I initiated a sell, need to lock items
            if not villager.inventory.has_item(trade['item'], trade['quantity']):
                return jsonify({
                    'success': False,
                    'message': f"Insufficient items: {trade['item']} (requires {trade['quantity']})"
                }), 400
            villager.inventory.remove_item(trade['item'], trade['quantity'])
            print(f"[Villager-{villager_state['node_id']}] Locked resources: {trade['quantity']}x {trade['item']}")
        
        trade['initiator_confirmed'] = True
        trade['locked_resources'] = True
        print(f"[Villager-{villager_state['node_id']}] Initiator confirmed trade: {trade_id}")
        
        # Notify receiver that initiator has confirmed
        try:
            receiver_address = trade.get('target_address')  # sent_trades uses target_address
            if receiver_address:
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
                    print(f"[Villager-{villager_state['node_id']}] Notified receiver: initiator confirmed trade {trade_id}")
                else:
                    print(f"[Villager-{villager_state['node_id']}] Failed to notify receiver: HTTP {response.status_code}")
            else:
                print(f"[Villager-{villager_state['node_id']}] Warning: receiver address missing")
        except Exception as e:
            print(f"[Villager-{villager_state['node_id']}] Failed to notify receiver: {e}")
    else:
        trade['receiver_confirmed'] = True
        print(f"[Villager-{villager_state['node_id']}] Receiver confirmed trade: {trade_id}")
        
        # Notify initiator that receiver has confirmed
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
                    print(f"[Villager-{villager_state['node_id']}] Notified initiator: receiver confirmed trade {trade_id}")
        except Exception as e:
            print(f"[Villager-{villager_state['node_id']}] Failed to notify initiator: {e}")
    
    trade['confirmed_at'] = time.time()
    
    print(f"[Villager-{villager_state['node_id']}] DEBUG: Confirmation state check")
    print(f"[Villager-{villager_state['node_id']}] DEBUG: initiator_confirmed = {trade.get('initiator_confirmed', False)}")
    print(f"[Villager-{villager_state['node_id']}] DEBUG: receiver_confirmed = {trade.get('receiver_confirmed', False)}")
    
    # If both parties have confirmed
    if trade.get('initiator_confirmed', False) and trade.get('receiver_confirmed', False):
        # Both confirmed, but settlement is not done here.
        # Settlement happens in confirm_notify (triggered by the party who confirms second).
        # If already completed, just return.
        if trade.get('status') == 'completed':
            print(f"[Villager-{villager_state['node_id']}] Trade already completed (already settled): {trade_id}")
            return jsonify({
                'success': True,
                'message': 'Trade already completed.',
                'villager': villager.to_dict()
            })
        
        # Not completed yet -> this is the second confirmer, perform settlement
        print(f"[Villager-{villager_state['node_id']}] Both confirmed, completing trade: {trade_id}")
        
        # Other party’s name ('target' for sent_trades, 'from' for pending_trades)
        other_party = trade.get('target') or trade.get('from')
        is_initiator = 'target' in trade
        
        # Execute actual resource transfer
        if is_initiator:
            if trade['offer_type'] == 'buy':
                # I initiated buy; gold already locked on confirm; now receive items
                villager.inventory.add_item(trade['item'], trade['quantity'])
                print(f"[Villager-{villager_state['node_id']}] Trade completed: bought {trade['quantity']}x {trade['item']} from {other_party}, paid {trade['price']} gold")
            else:
                # I initiated sell; items already locked on confirm; now receive money
                villager.inventory.add_money(trade['price'])
                print(f"[Villager-{villager_state['node_id']}] Trade completed: sold {trade['quantity']}x {trade['item']} to {other_party}, received {trade['price']} gold")
        else:
            if trade['offer_type'] == 'buy':
                # Counterparty buys my item; items locked at accept; now receive money
                villager.inventory.add_money(trade['price'])
                print(f"[Villager-{villager_state['node_id']}] Trade completed: sold {trade['quantity']}x {trade['item']} to {other_party}, received {trade['price']} gold")
            else:
                # Counterparty sells to me; gold locked at accept; now receive items
                villager.inventory.add_item(trade['item'], trade['quantity'])
                print(f"[Villager-{villager_state['node_id']}] Trade completed: bought {trade['quantity']}x {trade['item']} from {other_party}, paid {trade['price']} gold")
        
        # Mark trade as completed
        trade['status'] = 'completed'
        trade['completed_at'] = time.time()
        
        # Clean up completed trade from pending_trades
        if 'pending_trades' in villager_state:
            villager_state['pending_trades'] = [
                t for t in villager_state['pending_trades']
                if t.get('trade_id') != trade_id
            ]
        
        # Clean up completed trade from sent_trades
        if 'sent_trades' in villager_state:
            villager_state['sent_trades'] = [
                t for t in villager_state['sent_trades']
                if t.get('trade_id') != trade_id
            ]
        
        # Notify counterparty that trade is completed (to avoid double settlement)
        try:
            if is_initiator:
                # I am initiator, notify receiver
                target_address = trade.get('target_address')
                if target_address:
                    requests.post(
                        f"http://{target_address}/trade/complete_notify",
                        json={'trade_id': trade_id},
                        timeout=5
                    )
                    print(f"[Villager-{villager_state['node_id']}] Notified counterparty: trade completed")
            else:
                # I am receiver, notify initiator
                from_address = trade.get('from_address')
                if from_address:
                    requests.post(
                        f"http://{from_address}/trade/complete_notify",
                        json={'trade_id': trade_id},
                        timeout=5
                    )
                    print(f"[Villager-{villager_state['node_id']}] Notified counterparty: trade completed")
        except Exception as e:
            print(f"[Villager-{villager_state['node_id']}] Failed to notify counterparty of completion: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Trade completed successfully.',
            'trade': trade,
            'villager': villager.to_dict()
        })
    else:
        # Waiting for the other party to confirm
        return jsonify({
            'success': True,
            'message': 'Confirmation recorded. Waiting for the other party to confirm.',
            'trade': trade
        })


@app.route('/trade/commit', methods=['POST'])
def commit_trade():
    """Commit Trade (Two-phase commit - Phase 2)"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    trade_id = data['trade_id']
    
    # Find prepared trade
    if 'pending_trades' not in villager_state:
        return jsonify({'success': False, 'message': 'No pending trades'}), 400
    
    trade = None
    for t in villager_state['pending_trades']:
        if t['trade_id'] == trade_id and t.get('status') == 'prepared':
            trade = t
            break
    
    if not trade:
        return jsonify({'success': False, 'message': 'Prepared trade not found'}), 400
    
    # Execute trade (transfer resources)
    try:
        if trade['offer_type'] == 'buy':
            # Counterparty wants to buy my item; I'm the seller
            if not villager.inventory.has_item(trade['item'], trade['quantity']):
                return jsonify({
                    'success': False,
                    'message': f'Insufficient item: {trade["item"]} (requires {trade["quantity"]})'
                }), 400
            
            # Transfer items and gold
            villager.inventory.remove_item(trade['item'], trade['quantity'])
            villager.inventory.add_money(trade['price'])
            
            print(f"[Villager-{villager_state['node_id']}] Trade completed: Sold {trade['quantity']}x {trade['item']} to {trade['from']}, gained {trade['price']} gold")
            
        else:  # offer_type == 'sell'
            # Counterparty wants to sell to me; I'm the buyer
            if not villager.inventory.remove_money(trade['price']):
                return jsonify({
                    'success': False,
                    'message': f'Insufficient money (requires {trade["price"]}, has {villager.inventory.money})'
                }), 400
            
            # Receive item
            villager.inventory.add_item(trade['item'], trade['quantity'])
            
            print(f"[Villager-{villager_state['node_id']}] Trade completed: Bought {trade['quantity']}x {trade['item']} from {trade['from']}, paid {trade['price']} gold")
        
        # Mark trade as completed
        trade['status'] = 'committed'
        trade['committed_at'] = time.time()
        
        # Clean up completed trade from pending_trades
        villager_state['pending_trades'] = [
            t for t in villager_state['pending_trades']
            if t.get('trade_id') != trade_id
        ]
        
        print(f"[Villager-{villager_state['node_id']}] Trade commit completed: request from {trade['from']} {trade_id}")
        
        return jsonify({
            'success': True,
            'message': 'Trade committed successfully.',
            'villager': villager.to_dict()
        })
        
    except Exception as e:
        print(f"[Villager-{villager_state['node_id']}] Trade commit exception: {e}")
        return jsonify({
            'success': False,
            'message': f'Trade commit failed: {str(e)}'
        }), 500


@app.route('/trade/abort', methods=['POST'])
def abort_trade():
    """Abort Trade (Two-phase commit - rollback)"""
    data = request.json
    trade_id = data['trade_id']
    
    # Find pending trade
    if 'pending_trades' not in villager_state:
        return jsonify({'success': False, 'message': 'No pending trades'}), 400
    
    trade = None
    for t in villager_state['pending_trades']:
        if t['trade_id'] == trade_id and t.get('status') in ['pending', 'prepared']:
            trade = t
            break
    
    if not trade:
        return jsonify({'success': False, 'message': 'Trade not found'}), 400
    
    # Mark trade as aborted
    trade['status'] = 'aborted'
    trade['aborted_at'] = time.time()
    
    # Clean up aborted trade from pending_trades
    villager_state['pending_trades'] = [
        t for t in villager_state['pending_trades']
        if t.get('trade_id') != trade_id
    ]
    
    print(f"[Villager-{villager_state['node_id']}] Trade aborted: {trade_id}")
    
    return jsonify({
        'success': True,
        'message': 'Trade aborted successfully.'
    })


@app.route('/trade/reject', methods=['POST'])
def reject_trade():
    """Reject Trade"""
    data = request.json
    trade_id = data['trade_id']
    
    if 'pending_trades' not in villager_state:
        return jsonify({'success': False, 'message': 'No pending trades'}), 400
    
    # Remove trade
    villager_state['pending_trades'] = [
        t for t in villager_state['pending_trades'] 
        if t['trade_id'] != trade_id
    ]
    
    print(f"[Villager-{villager_state['node_id']}] Trade rejected: {trade_id}")
    
    return jsonify({
        'success': True,
        'message': 'Trade rejected'
    })


@app.route('/trade/complete', methods=['POST'])
def complete_trade():
    """Complete trade (called by initiator)"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
    
    data = request.json
    from_node = data['from']
    item = data['item']
    quantity = data['quantity']
    price = data['price']
    trade_type = data['type']  # 'buy' or 'sell'
    trade_id = data.get('trade_id')  # Trade ID for cleanup
    
    try:
        if trade_type == 'buy':
            # Counterparty buys my item
            if not villager.inventory.has_item(item, quantity):
                return jsonify({
                    'success': False,
                    'message': f'Insufficient item: {item} (requires {quantity})'
                }), 400
            
            # Transfer items and gold
            villager.inventory.remove_item(item, quantity)
            villager.inventory.add_money(price)
            
            print(f"[Villager-{villager_state['node_id']}] Trade completed: Sold {quantity}x {item} to {from_node}, gained {price} gold")
            
        else:  # sell
            # Counterparty sells items to me
            if not villager.inventory.remove_money(price):
                return jsonify({
                    'success': False,
                    'message': f'Insufficient money (requires {price}, has {villager.inventory.money})'
                }), 400
            
            # Receive item
            villager.inventory.add_item(item, quantity)
            
            print(f"[Villager-{villager_state['node_id']}] Trade completed: Bought {quantity}x {item} from {from_node}, paid {price} gold")
        
        # Clean up completed trade in pending_trades
        if 'pending_trades' in villager_state and trade_id:
            villager_state['pending_trades'] = [
                t for t in villager_state['pending_trades']
                if t.get('trade_id') != trade_id
            ]
            print(f"[Villager-{villager_state['node_id']}] Cleared trade record: {trade_id}")
        
        return jsonify({
            'success': True,
            'message': 'Trade completed',
            'villager': villager.to_dict()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Trade failed: {str(e)}'
        }), 500


@app.route('/time/advance', methods=['POST'])
def on_time_advance():
    """Time advance notification"""
    villager = villager_state['villager']
    
    if not villager:
        return jsonify({'success': True, 'message': 'No villager'})
    
    data = request.json
    print(f"[Villager-{villager_state['node_id']}] Time advance: Day {data['day']} {data['time_of_day']}")
    
    # If it's a new day (morning)
    if data['time_of_day'] == 'morning':
        # If did not sleep last evening, deduct additional stamina
        if not villager.has_slept:
            villager.consume_stamina(NO_SLEEP_PENALTY)
            print(f"[Villager-{villager_state['node_id']}] {villager.name} did not sleep last night, extra {NO_SLEEP_PENALTY} stamina consumed")
        
        # Daily reset
        villager.reset_daily()
        print(f"[Villager-{villager_state['node_id']}] A new day!")
        print(f"  Stamina: {villager.stamina}/{villager.max_stamina}")
    else:
        # Reset action status for this time period
        villager.reset_time_period()
        print(f"[Villager-{villager_state['node_id']}] Entered a new time period")
        print(f"  Current time of day: {data['time_of_day']}")
    
    print(f"  You can start a new action (work/sleep/idle)")
    
    return jsonify({'success': True, 'message': 'Time updated'})


# ==================== Message System API ====================

@app.route('/messages', methods=['GET'])
def get_messages():
    """Get all messages"""
    return jsonify({
        'success': True,
        'messages': villager_state['messages']
    })


@app.route('/messages', methods=['POST'])
def receive_message():
    """Receive Message (called by other nodes or Coordinator)"""
    try:
        data = request.json
        message = {
            'id': len(villager_state['messages']) + 1,
            'from': data['from'],
            'to': data.get('to', 'all'),  # 'all' means broadcast message
            'type': data['type'],  # 'private' or 'broadcast'
            'content': data['content'],
            'timestamp': data.get('timestamp', ''),
            'read': False
        }
        
        villager_state['messages'].append(message)
        
        # Print message notification
        if message['type'] == 'broadcast':
            print(f"[Villager-{villager_state['node_id']}] 📢 Received broadcast message: {message['from']}: {message['content']}")
        else:
            print(f"[Villager-{villager_state['node_id']}] 💬 Received private message: {message['from']}: {message['content']}")
        
        return jsonify({'success': True, 'message': 'Message received'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/messages/send', methods=['POST'])
def send_message():
    """Send message"""
    try:
        data = request.json
        target = data['target']  # Target node ID or 'all' means broadcast
        content = data['content']
        message_type = data.get('type', 'private')  # 'private' or 'broadcast'
        
        villager = villager_state['villager']
        if not villager:
            return jsonify({'success': False, 'message': 'Villager not initialized'}), 400
        
        sender_name = villager.name
        
        if message_type == 'broadcast':
            # Send broadcast message via Coordinator
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
                print(f"[Villager-{villager_state['node_id']}] 📢 Sent broadcast message: {content}")
                return jsonify({'success': True, 'message': 'Broadcast message sent'})
            else:
                return jsonify({'success': False, 'message': 'Failed to send broadcast'}), 500
        
        else:
            # Send point-to-point message
            # First, get the target node address from the Coordinator
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
            
            # Send message to target node
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
                print(f"[Villager-{villager_state['node_id']}] 💬 Sent private message to {target}: {content}")
                return jsonify({'success': True, 'message': 'Private message sent'})
            else:
                return jsonify({'success': False, 'message': 'Failed to send private message'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/messages/mark_read', methods=['POST'])
def mark_message_read():
    """Mark messages as read"""
    try:
        data = request.json
        message_id = data.get('message_id')
        
        if message_id:
            # Mark a specific message as read
            for msg in villager_state['messages']:
                if msg['id'] == message_id:
                    msg['read'] = True
                    break
        else:
            # Mark all messages as read
            for msg in villager_state['messages']:
                msg['read'] = True
        
        return jsonify({'success': True, 'message': 'Messages marked as read'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/mytrades', methods=['GET'])
def get_my_trades():
    """Get sent trade requests"""
    try:
        # Return list of sent trade requests
        sent_trades = villager_state.get('sent_trades', [])
        return jsonify({
            'success': True,
            'trades': sent_trades
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/sent_trades/add', methods=['POST'])
def add_sent_trade():
    """Add sent trade record"""
    try:
        data = request.json
        
        # Initialize sent_trades list
        if 'sent_trades' not in villager_state:
            villager_state['sent_trades'] = []
        
        # Add trade record
        villager_state['sent_trades'].append(data)
        
        return jsonify({'success': True, 'message': 'Trade record added'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def register_to_coordinator(coordinator_addr, port, node_id):
    """Register to coordinator"""
    import time
    time.sleep(2)  # Wait for service to start
    
    try:
        # Get villager name (if already created)
        villager_name = None
        if villager_state.get('villager'):
            villager_name = villager_state['villager'].name
        
        response = requests.post(
            f"http://{coordinator_addr}/register",
            json={
                'node_id': node_id,
                'node_type': 'villager',
                'address': f"{os.getenv('VILLAGER_HOST', 'localhost')}:{port}",
                'name': villager_name or node_id
            },
            timeout=5
        )
        
        if response.status_code == 200:
            if villager_name:
                print(f"[Villager-{node_id}] ({villager_name}) Successfully registered to coordinator: {coordinator_addr}")
            else:
                print(f"[Villager-{node_id}] Successfully registered to coordinator: {coordinator_addr}")
        else:
            print(f"[Villager-{node_id}] Registration failed: {response.status_code}")
    
    except Exception as e:
        print(f"[Villager-{node_id}] Unable to connect to coordinator {coordinator_addr}: {e}")


def run_server(port, node_id, coordinator_addr=None):
    """Run server"""
    villager_state['node_id'] = node_id
    villager_state['coordinator_address'] = coordinator_addr
    villager_state['port'] = port
    
    print(f"[Villager-{node_id}] REST Villager Node starting on port {port}")
    print(f"[Villager-{node_id}] NodeID: {node_id} (Villager name will be set on create)")
    
    # Register to coordinator in a background thread
    threading.Thread(
        target=register_to_coordinator,
        args=(coordinator_addr, port, node_id),
        daemon=True
    ).start()
    
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='REST Villager Node service')
    parser.add_argument('--port', type=int, required=True, help='listen port')
    parser.add_argument('--id', type=str, required=True, help='NodeID')
    parser.add_argument('--coordinator', type=str, default=f"{os.getenv('COORDINATOR_HOST', 'localhost')}:{os.getenv('COORDINATOR_PORT', '5000')}",
                       help='Coordinator address')
    args = parser.parse_args()
    
    run_server(args.port, args.id, args.coordinator)


