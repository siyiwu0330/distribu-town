"""
Time Coordinator - Architecture 2 (REST)
Manages global time and synchronizes all nodes
"""

from flask import Flask, request, jsonify
import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.models import GameState, TimeOfDay

app = Flask(__name__)

# Global state
game_state = GameState()
registered_nodes = {}  # {node_id: {node_type, address}}
pending_actions = {}   # {node_id: action_type}  - Pending action submissions
time_barrier_ready = False  # Whether all nodes are ready to advance time


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'service': 'coordinator'})


@app.route('/register', methods=['POST'])
def register_node():
    """Register node"""
    data = request.json
    node_id = data['node_id']
    node_type = data['node_type']
    address = data['address']
    name = data.get('name', node_id)  # Optional villager name
    occupation = data.get('occupation')  # Optional occupation
    
    registered_nodes[node_id] = {
        'node_id': node_id,
        'node_type': node_type,
        'address': address,
        'name': name,
        'occupation': occupation
    }
    
    if name != node_id and occupation:
        print(f"[Coordinator] Node registered: {node_id} ({name} - {occupation}, {node_type}) @ {address}")
    elif name != node_id:
        print(f"[Coordinator] Node registered: {node_id} ({name}, {node_type}) @ {address}")
    else:
        print(f"[Coordinator] Node registered: {node_id} ({node_type}) @ {address}")
    
    return jsonify({
        'success': True,
        'message': f'Node {node_id} registered successfully'
    })


@app.route('/time', methods=['GET'])
def get_current_time():
    """Get current time"""
    return jsonify(game_state.to_dict())


@app.route('/action/submit', methods=['POST'])
def submit_action():
    """Villager submits action for current time period"""
    global pending_actions, time_barrier_ready
    
    data = request.json
    node_id = data['node_id']
    action_type = data['action']  # 'work', 'sleep', 'idle'
    
    # Record action
    pending_actions[node_id] = action_type
    
    print(f"\n[Coordinator] {node_id} submitted action: {action_type}")
    print(f"[Coordinator] Submitted: {len(pending_actions)}/{len([n for n in registered_nodes.values() if n['node_type'] == 'villager'])}")
    
    # Check if all villager nodes have submitted
    villager_nodes = [nid for nid, info in registered_nodes.items() if info['node_type'] == 'villager']
    all_submitted = all(nid in pending_actions for nid in villager_nodes)
    
    if all_submitted and len(villager_nodes) > 0:
        print(f"[Coordinator] ✓ All villagers have submitted actions, ready to advance time")
        time_barrier_ready = True
        
        # Automatically advance time
        result = _advance_time_internal()
        
        return jsonify({
            'success': True,
            'message': 'Action submitted, time will advance',
            'all_ready': True,
            'time_advanced': True,
            'new_time': game_state.to_dict()
        })
    else:
        waiting_for = [nid for nid in villager_nodes if nid not in pending_actions]
        print(f"[Coordinator] Waiting for other villagers: {waiting_for}")
        
        return jsonify({
            'success': True,
            'message': f'Action submitted, waiting for others ({len(pending_actions)}/{len(villager_nodes)})',
            'all_ready': False,
            'waiting_for': waiting_for
        })


def _advance_time_internal():
    """Internal function: Actually advance time"""
    global game_state, pending_actions, time_barrier_ready
    
    old_time = f"Day {game_state.day} {game_state.time_of_day.value}"
    
    # Advance time
    game_state.advance_time()
    
    new_time = f"Day {game_state.day} {game_state.time_of_day.value}"
    print(f"\n[Coordinator] ⏰ Time advanced: {old_time} -> {new_time}")
    print(f"[Coordinator] Action log: {pending_actions}")
    
    # Clear action records
    pending_actions = {}
    time_barrier_ready = False
    
    # Notify all registered nodes
    notification = game_state.to_dict()
    
    for node_id, node_info in registered_nodes.items():
        if node_info['node_type'] == 'coordinator':
            continue
        
        try:
            address = node_info['address']
            response = requests.post(
                f"http://{address}/time/advance",
                json=notification,
                timeout=2
            )
            
            if response.status_code == 200:
                print(f"[Coordinator] Notified node: {node_id}")
            else:
                print(f"[Coordinator] Failed to notify node {node_id}: {response.status_code}")
        
        except Exception as e:
            print(f"[Coordinator] Failed to notify node {node_id}: {e}")
    
    return {
        'success': True,
        'message': f'Time advanced to {new_time}',
        'time': game_state.to_dict()
    }


@app.route('/time/advance', methods=['POST'])
def advance_time():
    """Manually advance time (admin feature, for debugging)"""
    result = _advance_time_internal()
    return jsonify(result)


@app.route('/action/status', methods=['GET'])
def action_status():
    """Query current action submission status"""
    villager_nodes = {nid: info for nid, info in registered_nodes.items() if info['node_type'] == 'villager'}
    
    submitted = []
    waiting = []
    
    for nid, info in villager_nodes.items():
        # Build display name: Name (occupation)
        display_name = nid
        if info.get('name') and info['name'] != nid:
            if info.get('occupation'):
                display_name = f"{info['name']} ({info['occupation']})"
            else:
                display_name = info['name']
        
        if nid in pending_actions:
            submitted.append({'node_id': nid, 'display_name': display_name})
        else:
            waiting.append({'node_id': nid, 'display_name': display_name})
    
    return jsonify({
        'total_villagers': len(villager_nodes),
        'submitted': len(submitted),
        'submitted_nodes': submitted,
        'pending_actions': pending_actions,
        'waiting_for': waiting,
        'ready_to_advance': time_barrier_ready
    })


@app.route('/nodes', methods=['GET'])
def list_nodes():
    """List all registered nodes"""
    return jsonify({
        'nodes': list(registered_nodes.values())
    })


@app.route('/messages/broadcast', methods=['POST'])
def broadcast_message():
    """Broadcast message to all villager nodes"""
    try:
        data = request.json
        sender_id = data['from']
        sender_name = data['from_name']
        content = data['content']
        
        # Get all villager nodes
        villager_nodes = [node for node in registered_nodes.values() if node['node_type'] == 'villager']
        
        if not villager_nodes:
            return jsonify({'success': False, 'message': 'No villager nodes found'}), 404
        
        # Send broadcast message to each villager node
        success_count = 0
        failed_nodes = []
        
        for node in villager_nodes:
            try:
                response = requests.post(
                    f"http://{node['address']}/messages",
                    json={
                        'from': sender_id,
                        'from_name': sender_name,
                        'to': 'all',
                        'type': 'broadcast',
                        'content': content,
                        'timestamp': ''
                    },
                    timeout=3
                )
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    failed_nodes.append(node['node_id'])
                    
            except Exception as e:
                failed_nodes.append(node['node_id'])
                print(f"[Coordinator] Failed to send broadcast message to {node['node_id']}: {e}")
        
        print(f"[Coordinator] 📢 Broadcast message: {sender_name}: {content}")
        print(f"[Coordinator] Successfully sent to {success_count}/{len(villager_nodes)} nodes")
        
        if failed_nodes:
            print(f"[Coordinator] Failed nodes: {failed_nodes}")
        
        return jsonify({
            'success': True,
            'message': f'Broadcast sent to {success_count}/{len(villager_nodes)} nodes',
            'success_count': success_count,
            'total_nodes': len(villager_nodes),
            'failed_nodes': failed_nodes
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def run_server(port=5000):
    """Run server"""
    print(f"[Coordinator] REST Time Coordinator starting on port {port}")
    print("[Coordinator] Waiting for node registration...")
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='REST Time Coordinator Service')
    parser.add_argument('--port', type=int, default=5000, help='Listen port')
    args = parser.parse_args()
    
    run_server(args.port)

