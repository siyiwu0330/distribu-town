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
    
    registered_nodes[node_id] = {
        'node_id': node_id,
        'node_type': node_type,
        'address': address
    }
    
    print(f"[Coordinator] 节点注册: {node_id} ({node_type}) @ {address}")
    
    return jsonify({
        'success': True,
        'message': f'Node {node_id} registered successfully'
    })


@app.route('/time', methods=['GET'])
def get_current_time():
    """获取当前时间"""
    return jsonify(game_state.to_dict())


@app.route('/time/advance', methods=['POST'])
def advance_time():
    """推进时间"""
    global game_state
    
    old_time = f"Day {game_state.day} {game_state.time_of_day.value}"
    
    # 推进时间
    game_state.advance_time()
    
    new_time = f"Day {game_state.day} {game_state.time_of_day.value}"
    print(f"\n[Coordinator] 时间推进: {old_time} -> {new_time}")
    
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
    
    return jsonify({
        'success': True,
        'message': f'Time advanced to {new_time}',
        'time': game_state.to_dict()
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

