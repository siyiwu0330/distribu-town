#!/usr/bin/env python3
"""
AI Agent启动器 - gRPC版本
使用适配层桥接gRPC和REST API，从而复用REST版本的AI Agent代码
"""

import sys
import os
import argparse

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'architecture2_rest'))

# 导入gRPC适配层
from grpc_adapter import GRPCAdapter

# 导入REST版本的AI Agent（我们将monkey patch它的requests调用）
from ai_villager_agent import AIVillagerAgent


class GRPCAIAgent(AIVillagerAgent):
    """
    gRPC版本的AI Agent
    继承REST版本的AIVillagerAgent，但使用gRPC适配层替换requests调用
    """
    
    def __init__(self, villager_port: int, coordinator_port: int = 50051, merchant_port: int = 50052,
                 api_key: str = None, model: str = "gpt-4o-mini", use_react: bool = True):
        
        # 构造地址
        villager_address = f"localhost:{villager_port}"
        coordinator_address = f"localhost:{coordinator_port}"
        merchant_address = f"localhost:{merchant_port}"
        
        # 创建gRPC适配器
        self.grpc_adapter = GRPCAdapter(villager_address, coordinator_address, merchant_address)
        
        # 初始化父类（REST版本）
        # 注意：我们传入的端口会被转换为URL，但我们会拦截所有requests调用
        super().__init__(villager_port, coordinator_port, merchant_port, api_key, model, use_react)
        
        # 覆盖地址信息
        self.villager_address = villager_address
        self.coordinator_address = coordinator_address  
        self.merchant_address = merchant_address
        
        print(f"[gRPC AI Agent] 使用gRPC适配层")
    
    # ========== 覆盖REST API调用方法 ==========
    
    def check_connection(self) -> bool:
        """检查连接（使用gRPC）"""
        try:
            result = self.grpc_adapter.get_villager()
            return result['status_code'] == 200 or result['status_code'] == 400  # 400表示未初始化，但连接正常
        except:
            return False
    
    def get_villager_status(self):
        """获取村民状态（使用gRPC）"""
        try:
            result = self.grpc_adapter.get_villager()
            if result['status_code'] == 200:
                # 补充node_id
                villager_data = result['json']
                # 从coordinator获取node_id
                nodes_result = self.grpc_adapter.get_nodes()
                if nodes_result['status_code'] == 200:
                    for node in nodes_result['json']['nodes']:
                        if node['address'] == self.villager_address:
                            villager_data['node_id'] = node['node_id']
                            break
                if 'node_id' not in villager_data:
                    villager_data['node_id'] = f"node{self.villager_port}"
                return villager_data
            return None
        except Exception as e:
            print(f"[gRPC AI Agent] 获取村民状态失败: {e}")
            return None
    
    def get_current_time(self) -> str:
        """获取当前时间（使用gRPC）"""
        try:
            result = self.grpc_adapter.get_time()
            if result['status_code'] == 200:
                time_data = result['json']
                return f"Day {time_data['day']} - {time_data['time_of_day']}"
            return "Unknown"
        except Exception as e:
            print(f"[gRPC AI Agent] 获取时间失败: {e}")
            return "Unknown"
    
    def get_action_status(self):
        """获取行动状态（gRPC版本没有action系统，返回None）"""
        return None
    
    def get_merchant_prices(self):
        """获取商人价格（使用gRPC）"""
        try:
            result = self.grpc_adapter.get_prices()
            if result['status_code'] == 200:
                return result['json']
            return None
        except Exception as e:
            print(f"[gRPC AI Agent] 获取商人价格失败: {e}")
            return None
    
    def get_trades_received(self):
        """获取收到的交易请求（使用gRPC）"""
        try:
            villager_state = self.get_villager_status() or {}
            my_node_id = villager_state.get('node_id')
            
            if not my_node_id:
                return []
            
            result = self.grpc_adapter.list_trades(my_node_id, 'pending')
            if result['status_code'] == 200:
                return result['json'].get('trades', [])
            return []
        except Exception as e:
            print(f"[gRPC AI Agent] 获取交易请求失败: {e}")
            return []
    
    def get_trades_sent(self):
        """获取发送的交易请求（使用gRPC）"""
        try:
            villager_state = self.get_villager_status() or {}
            my_node_id = villager_state.get('node_id')
            
            if not my_node_id:
                return []
            
            result = self.grpc_adapter.list_trades(my_node_id, 'sent')
            if result['status_code'] == 200:
                return result['json'].get('trades', [])
            return []
        except Exception as e:
            print(f"[gRPC AI Agent] 获取发送交易失败: {e}")
            return []
    
    def get_messages(self):
        """获取消息列表（gRPC版本没有消息系统）"""
        return []
    
    def get_online_villagers(self):
        """获取在线村民列表（使用gRPC）"""
        try:
            result = self.grpc_adapter.get_nodes()
            if result['status_code'] != 200:
                return []
            
            villagers = []
            for node in result['json']['nodes']:
                if node['node_type'] == 'villager':
                    # 获取详细信息
                    try:
                        adapter = GRPCAdapter(node['address'], self.coordinator_address, self.merchant_address)
                        v_result = adapter.get_villager()
                        if v_result['status_code'] == 200:
                            v_data = v_result['json']
                            villagers.append({
                                'node_id': node['node_id'],
                                'name': v_data.get('name', node['node_id']),
                                'occupation': v_data.get('occupation', 'unknown'),
                                'has_submitted_action': False,
                                'stamina': v_data.get('stamina', 0),
                                'inventory': v_data.get('inventory', {}),
                                'address': node['address']
                            })
                        else:
                            villagers.append({
                                'node_id': node['node_id'],
                                'name': node['node_id'],
                                'occupation': 'unknown',
                                'has_submitted_action': False,
                                'stamina': 0,
                                'inventory': {},
                                'address': node['address']
                            })
                    except:
                        villagers.append({
                            'node_id': node['node_id'],
                            'name': node['node_id'],
                            'occupation': 'unknown',
                            'has_submitted_action': False,
                            'stamina': 0,
                            'inventory': {},
                            'address': node['address']
                        })
            
            return villagers
        except Exception as e:
            print(f"[gRPC AI Agent] 获取在线村民失败: {e}")
            return []
    
    # ========== 覆盖行动执行方法 ==========
    
    def execute_action(self, action_dict):
        """执行行动（覆盖以使用gRPC）"""
        action = action_dict.get('action')
        
        if action == 'produce':
            result = self.grpc_adapter.produce()
            return result['json'].get('success', False), result['json'].get('message', '')
        
        elif action == 'buy':
            result = self.grpc_adapter.trade_merchant('buy', action_dict['item'], action_dict['quantity'])
            return result['json'].get('success', False), result['json'].get('message', '')
        
        elif action == 'sell':
            result = self.grpc_adapter.trade_merchant('sell', action_dict['item'], action_dict['quantity'])
            return result['json'].get('success', False), result['json'].get('message', '')
        
        elif action == 'sleep':
            result = self.grpc_adapter.sleep()
            return result['json'].get('success', False), result['json'].get('message', '')
        
        elif action == 'trade':
            # 村民间交易
            my_state = self.get_villager_status()
            if not my_state:
                return False, "无法获取自己的状态"
            
            my_node_id = my_state.get('node_id')
            target_id = action_dict['target']
            
            # 获取目标地址
            nodes = self.grpc_adapter.get_nodes()
            target_address = None
            for node in nodes['json']['nodes']:
                if node['node_id'] == target_id:
                    target_address = node['address']
                    break
            
            if not target_address:
                return False, f"找不到目标节点: {target_id}"
            
            result = self.grpc_adapter.create_trade({
                'initiator_id': my_node_id,
                'initiator_address': self.villager_address,
                'target_id': target_id,
                'target_address': target_address,
                'offer_type': action_dict['offer_type'],
                'item': action_dict['item'],
                'quantity': action_dict['quantity'],
                'price': action_dict['price']
            })
            return result['json'].get('success', False), result['json'].get('message', '')
        
        elif action == 'accept_trade':
            my_state = self.get_villager_status()
            my_node_id = my_state.get('node_id') if my_state else None
            if not my_node_id:
                return False, "无法获取node_id"
            
            result = self.grpc_adapter.accept_trade(action_dict['trade_id'], my_node_id)
            return result['json'].get('success', False), result['json'].get('message', '')
        
        elif action == 'confirm_trade':
            my_state = self.get_villager_status()
            my_node_id = my_state.get('node_id') if my_state else None
            if not my_node_id:
                return False, "无法获取node_id"
            
            result = self.grpc_adapter.confirm_trade(action_dict['trade_id'], my_node_id)
            return result['json'].get('success', False), result['json'].get('message', '')
        
        elif action == 'reject_trade':
            my_state = self.get_villager_status()
            my_node_id = my_state.get('node_id') if my_state else None
            if not my_node_id:
                return False, "无法获取node_id"
            
            result = self.grpc_adapter.reject_trade(action_dict['trade_id'], my_node_id)
            return result['json'].get('success', False), result['json'].get('message', '')
        
        elif action == 'cancel_trade':
            my_state = self.get_villager_status()
            my_node_id = my_state.get('node_id') if my_state else None
            if not my_node_id:
                return False, "无法获取node_id"
            
            result = self.grpc_adapter.cancel_trade(action_dict['trade_id'], my_node_id)
            return result['json'].get('success', False), result['json'].get('message', '')
        
        elif action in ['send', 'idle', 'wait', 'eat']:
            # gRPC版本不支持这些action
            return True, f"Action {action} (not supported in gRPC, simulated)"
        
        else:
            return False, f"Unknown action: {action}"


def main():
    parser = argparse.ArgumentParser(description='AI村民代理 (gRPC版本)')
    parser.add_argument('--port', type=int, required=True, help='村民节点端口')
    parser.add_argument('--name', type=str, required=True, help='村民名字')
    parser.add_argument('--occupation', type=str, required=True, help='职业 (farmer/carpenter/chef)')
    parser.add_argument('--gender', type=str, required=True, help='性别 (male/female)')
    parser.add_argument('--personality', type=str, required=True, help='性格描述')
    parser.add_argument('--api-key', type=str, help='OpenAI API Key')
    parser.add_argument('--model', type=str, default='gpt-4o-mini', help='GPT模型')
    parser.add_argument('--coordinator', type=int, default=50051, help='协调器端口')
    parser.add_argument('--merchant', type=int, default=50052, help='商人端口')
    
    args = parser.parse_args()
    
    # 创建AI Agent
    agent = GRPCAIAgent(
        villager_port=args.port,
        coordinator_port=args.coordinator,
        merchant_port=args.merchant,
        api_key=args.api_key or os.getenv('OPENAI_API_KEY'),
        model=args.model,
        use_react=True
    )
    
    # 创建村民
    print(f"\n{'='*70}")
    print(f"  创建AI村民: {args.name}")
    print(f"{'='*70}\n")
    
    result = agent.grpc_adapter.create_villager({
        'name': args.name,
        'occupation': args.occupation,
        'gender': args.gender,
        'personality': args.personality
    })
    
    if result['status_code'] != 200:
        print(f"✗ 创建村民失败: {result['json'].get('message')}")
        return
    
    print(f"✓ 村民创建成功")
    
    # 启动AI Agent
    print(f"\n{'='*70}")
    print(f"  启动AI Agent托管")
    print(f"{'='*70}\n")
    
    agent.start()
    
    # 保持运行
    try:
        while agent.running:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n停止AI Agent...")
        agent.stop()


if __name__ == '__main__':
    main()

