"""
时间协调器 - Architecture 2 (REST)
负责管理全局时间和同步所有节点
"""

from flask import Flask, request, jsonify
import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.models import GameState, TimeOfDay

app = Flask(__name__)

# 全局状态
game_state = GameState()
registered_nodes = {}  # {node_id: {node_type, address}}
pending_actions = {}   # {node_id: action_type}  - 等待提交的行动
time_barrier_ready = False  # 是否所有节点都准备好推进时间


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'healthy', 'service': 'coordinator'})


@app.route('/register', methods=['POST'])
def register_node():
    """注册节点"""
    data = request.json
    node_id = data['node_id']
    node_type = data['node_type']
    address = data['address']
    name = data.get('name', node_id)  # 可选的村民名字
    occupation = data.get('occupation')  # 可选的职业
    
    registered_nodes[node_id] = {
        'node_id': node_id,
        'node_type': node_type,
        'address': address,
        'name': name,
        'occupation': occupation
    }
    
    if name != node_id and occupation:
        print(f"[Coordinator] 节点注册: {node_id} ({name} - {occupation}, {node_type}) @ {address}")
    elif name != node_id:
        print(f"[Coordinator] 节点注册: {node_id} ({name}, {node_type}) @ {address}")
    else:
        print(f"[Coordinator] 节点注册: {node_id} ({node_type}) @ {address}")
    
    return jsonify({
        'success': True,
        'message': f'Node {node_id} registered successfully'
    })


@app.route('/time', methods=['GET'])
def get_current_time():
    """获取当前时间"""
    return jsonify(game_state.to_dict())


@app.route('/action/submit', methods=['POST'])
def submit_action():
    """村民提交当前时段的行动"""
    global pending_actions, time_barrier_ready
    
    data = request.json
    node_id = data['node_id']
    action_type = data['action']  # 'work', 'sleep', 'idle'
    
    # 记录行动
    pending_actions[node_id] = action_type
    
    print(f"\n[Coordinator] {node_id} 提交行动: {action_type}")
    print(f"[Coordinator] 已提交: {len(pending_actions)}/{len([n for n in registered_nodes.values() if n['node_type'] == 'villager'])}")
    
    # 检查是否所有村民节点都已提交
    villager_nodes = [nid for nid, info in registered_nodes.items() if info['node_type'] == 'villager']
    all_submitted = all(nid in pending_actions for nid in villager_nodes)
    
    if all_submitted and len(villager_nodes) > 0:
        print(f"[Coordinator] ✓ 所有村民已提交行动，准备推进时间")
        time_barrier_ready = True
        
        # 自动推进时间
        result = _advance_time_internal()
        
        return jsonify({
            'success': True,
            'message': '行动已提交，时间即将推进',
            'all_ready': True,
            'time_advanced': True,
            'new_time': game_state.to_dict()
        })
    else:
        waiting_for = [nid for nid in villager_nodes if nid not in pending_actions]
        print(f"[Coordinator] 等待其他村民: {waiting_for}")
        
        return jsonify({
            'success': True,
            'message': f'行动已提交，等待其他村民 ({len(pending_actions)}/{len(villager_nodes)})',
            'all_ready': False,
            'waiting_for': waiting_for
        })


def _advance_time_internal():
    """内部函数：实际推进时间"""
    global game_state, pending_actions, time_barrier_ready
    
    old_time = f"Day {game_state.day} {game_state.time_of_day.value}"
    
    # 推进时间
    game_state.advance_time()
    
    new_time = f"Day {game_state.day} {game_state.time_of_day.value}"
    print(f"\n[Coordinator] ⏰ 时间推进: {old_time} -> {new_time}")
    print(f"[Coordinator] 行动记录: {pending_actions}")
    
    # 清空行动记录
    pending_actions = {}
    time_barrier_ready = False
    
    # 通知所有注册的节点
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
                print(f"[Coordinator] 通知节点: {node_id}")
            else:
                print(f"[Coordinator] 通知节点 {node_id} 失败: {response.status_code}")
        
        except Exception as e:
            print(f"[Coordinator] 通知节点 {node_id} 失败: {e}")
    
    return {
        'success': True,
        'message': f'Time advanced to {new_time}',
        'time': game_state.to_dict()
    }


@app.route('/time/advance', methods=['POST'])
def advance_time():
    """手动推进时间（管理员功能，调试用）"""
    result = _advance_time_internal()
    return jsonify(result)


@app.route('/action/status', methods=['GET'])
def action_status():
    """查询当前行动提交状态"""
    villager_nodes = {nid: info for nid, info in registered_nodes.items() if info['node_type'] == 'villager'}
    
    submitted = []
    waiting = []
    
    for nid, info in villager_nodes.items():
        # 构建显示名称：Name (occupation)
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
    """列出所有注册的节点"""
    return jsonify({
        'nodes': list(registered_nodes.values())
    })


def run_server(port=5000):
    """运行服务器"""
    print(f"[Coordinator] REST时间协调器启动在端口 {port}")
    print("[Coordinator] 等待节点注册...")
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='REST时间协调器服务')
    parser.add_argument('--port', type=int, default=5000, help='监听端口')
    args = parser.parse_args()
    
    run_server(args.port)

