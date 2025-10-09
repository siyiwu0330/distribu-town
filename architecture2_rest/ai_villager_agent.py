#!/usr/bin/env python3
"""
AI Agent村民 - 基于GPT的智能村民代理
可以自动读取状态并决定在当前时段做什么
"""

import requests
import json
import time
import threading
import os
import sys
from typing import Dict, List, Optional, Any
import openai
from datetime import datetime

class AIVillagerAgent:
    """AI村民代理"""
    
    def __init__(self, villager_port: int, coordinator_port: int = 5000, merchant_port: int = 5001, 
                 api_key: str = None, model: str = "gpt-4.1", use_react: bool = False):
        self.villager_url = f"http://localhost:{villager_port}"
        self.coordinator_url = f"http://localhost:{coordinator_port}"
        self.merchant_url = f"http://localhost:{merchant_port}"
        self.villager_port = villager_port
        
        # OpenAI配置
        self.api_key = api_key
        self.model = model
        self.use_react = use_react
        if api_key:
            openai.api_key = api_key
        
        # 村民信息
        self.villager_info = None
        self.villager_name = None
        self.villager_occupation = None
        
        # 运行状态
        self.running = False
        self.decision_thread = None
        
        # 决策历史
        self.decision_history = []
        
        # 交易跟踪
        self.sent_trades_tracker = {}  # 跟踪已发送的交易请求
        
        print(f"[AI Agent] 初始化完成，连接到村民节点: {villager_port}")
    
    def check_connection(self) -> bool:
        """检查连接"""
        try:
            response = requests.get(f"{self.villager_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def get_villager_status(self) -> Optional[Dict]:
        """获取村民状态"""
        try:
            response = requests.get(f"{self.villager_url}/villager", timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[AI Agent] 获取村民状态失败: {e}")
            return None
    
    def get_current_time(self) -> str:
        """获取当前时间"""
        try:
            response = requests.get(f"{self.coordinator_url}/time", timeout=5)
            if response.status_code == 200:
                time_data = response.json()
                return f"Day {time_data['day']} - {time_data['time_of_day']}"
            return "Unknown"
        except Exception as e:
            print(f"[AI Agent] 获取时间失败: {e}")
            return "Unknown"
    
    def get_action_status(self) -> Optional[Dict]:
        """获取行动提交状态"""
        try:
            response = requests.get(f"{self.coordinator_url}/action/status", timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[AI Agent] 获取行动状态失败: {e}")
            return None
    
    def get_merchant_prices(self) -> Optional[Dict]:
        """获取商人价格"""
        try:
            response = requests.get(f"{self.merchant_url}/prices", timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[AI Agent] 获取商人价格失败: {e}")
            return None
    
    def get_trades_received(self) -> List[Dict]:
        """获取收到的交易请求"""
        try:
            response = requests.get(f"{self.villager_url}/trade/pending", timeout=5)
            if response.status_code == 200:
                return response.json().get('pending_trades', [])
            return []
        except Exception as e:
            print(f"[AI Agent] 获取交易请求失败: {e}")
            return []
    
    def get_trades_sent(self) -> List[Dict]:
        """获取发送的交易请求"""
        try:
            response = requests.get(f"{self.villager_url}/mytrades", timeout=5)
            if response.status_code == 200:
                return response.json().get('trades', [])
            return []
        except Exception as e:
            print(f"[AI Agent] 获取发送交易失败: {e}")
            return []

    def get_messages(self) -> List[Dict]:
        """获取消息列表"""
        try:
            response = requests.get(f"{self.villager_url}/messages", timeout=5)
            if response.status_code == 200:
                return response.json().get('messages', [])
            return []
        except Exception as e:
            print(f"[AI Agent] 获取消息失败: {e}")
            return []
    
    def get_online_villagers(self) -> List[Dict]:
        """获取在线村民列表（包含提交状态）"""
        try:
            response = requests.get(f"{self.coordinator_url}/nodes", timeout=5)
            if response.status_code == 200:
                nodes_data = response.json()
                villagers = []
                for node in nodes_data['nodes']:
                    if node['node_type'] == 'villager':
                        # 获取村民的详细状态
                        try:
                            villager_response = requests.get(f"http://{node['address']}/villager", timeout=3)
                            if villager_response.status_code == 200:
                                villager_data = villager_response.json()
                                villagers.append({
                                    'node_id': node['node_id'],
                                    'name': villager_data.get('name', node['node_id']),
                                    'occupation': villager_data.get('occupation', 'unknown'),
                                    'has_submitted_action': villager_data.get('has_submitted_action', False),
                                    'stamina': villager_data.get('stamina', 0),
                                    'inventory': villager_data.get('inventory', {}),
                                    'address': node['address']
                                })
                            else:
                                # 如果无法获取详细状态，使用基本信息
                                villagers.append({
                                    'node_id': node['node_id'],
                                    'name': node.get('name', node['node_id']),
                                    'occupation': node.get('occupation', 'unknown'),
                                    'has_submitted_action': False,
                                    'stamina': 0,
                                    'inventory': {},
                                    'address': node['address']
                                })
                        except Exception as e:
                            # 如果获取详细状态失败，使用基本信息
                            villagers.append({
                                'node_id': node['node_id'],
                                'name': node.get('name', node['node_id']),
                                'occupation': node.get('occupation', 'unknown'),
                                'has_submitted_action': False,
                                'stamina': 0,
                                'inventory': {},
                                'address': node['address']
                            })
                return villagers
            return []
        except Exception as e:
            print(f"[AI Agent] 获取在线村民失败: {e}")
            return []
    
    def analyze_p2p_opportunities(self, context: Dict) -> Dict:
        """分析P2P交易机会"""
        opportunities = {
            'sell_opportunities': [],
            'buy_opportunities': [],
            'recommendations': []
        }
        
        villager = context.get('villager', {})
        occupation = villager.get('occupation')
        inventory = villager.get('inventory', {})
        villagers = context.get('villagers', [])
        prices = context.get('prices', {})
        
        # 分析出售机会
        if occupation == 'farmer' and inventory.get('wheat', 0) > 0:
            # 农夫出售小麦给厨师
            for other_villager in villagers:
                if other_villager.get('occupation') == 'chef':
                    other_inventory = other_villager.get('inventory', {})
                    if other_inventory.get('wheat', 0) < 3:  # 厨师需要小麦
                        quantity = min(inventory['wheat'], 3 - other_inventory.get('wheat', 0))
                        if quantity > 0:
                            target_node_id = other_villager['node_id']
                            suggested_price = 7
                            total_price = suggested_price * quantity
                            
                            # 检查是否已经发送过相同的交易请求
                            if not self.has_sent_trade_request(target_node_id, 'wheat', quantity, total_price):
                                opportunities['sell_opportunities'].append({
                                    'target': target_node_id,
                                    'target_name': other_villager.get('name', 'Unknown'),
                                    'item': 'wheat',
                                    'quantity': quantity,
                                    'suggested_price': suggested_price,
                                    'total_price': total_price,
                                    'merchant_buy_price': prices.get('sell', {}).get('wheat', 5),
                                    'merchant_sell_price': prices.get('buy', {}).get('wheat', 10),
                                    'negotiation_message': f"Hi! I have {quantity}x wheat to sell for {total_price} gold total ({suggested_price} gold each). This is better than the merchant's buy price of 5 gold each. Would you like to buy?"
                                })
        
        elif occupation == 'chef' and inventory.get('bread', 0) > 2:  # 保留2个面包自用
            # 厨师出售面包给其他村民
            for other_villager in villagers:
                if other_villager.get('node_id') != villager.get('node_id'):
                    other_inventory = other_villager.get('inventory', {})
                    if other_inventory.get('bread', 0) < 2:  # 其他村民需要面包
                        quantity = min(inventory['bread'] - 2, 2 - other_inventory.get('bread', 0))
                        if quantity > 0:
                            opportunities['sell_opportunities'].append({
                                'target': other_villager['node_id'],
                                'target_name': other_villager.get('name', 'Unknown'),
                                'item': 'bread',
                                'quantity': quantity,
                                'suggested_price': 35,  # 介于22.5(merchant buy)和45(merchant sell)之间
                                'total_price': 35 * quantity,
                                'merchant_buy_price': prices.get('sell', {}).get('bread', 22.5),
                                'merchant_sell_price': prices.get('buy', {}).get('bread', 45)
                            })
        
        elif occupation == 'carpenter' and inventory.get('house', 0) > 0:
            # 木工出售房子给没有房子的村民
            for other_villager in villagers:
                if other_villager.get('node_id') != villager.get('node_id'):
                    other_inventory = other_villager.get('inventory', {})
                    if other_inventory.get('house', 0) == 0:  # 没有房子
                        opportunities['sell_opportunities'].append({
                            'target': other_villager['node_id'],
                            'target_name': other_villager.get('name', 'Unknown'),
                            'item': 'house',
                            'quantity': 1,
                            'suggested_price': 180,  # 介于130(merchant buy)和260(merchant sell)之间
                            'total_price': 180,
                            'merchant_buy_price': prices.get('sell', {}).get('house', 130),
                            'merchant_sell_price': prices.get('buy', {}).get('house', 260)
                        })
        
        # 分析购买机会
        if occupation == 'chef' and inventory.get('wheat', 0) < 3:
            # 厨师从农夫购买小麦
            for other_villager in villagers:
                if other_villager.get('occupation') == 'farmer':
                    other_inventory = other_villager.get('inventory', {})
                    if other_inventory.get('wheat', 0) > 0:
                        quantity = min(3 - inventory.get('wheat', 0), other_inventory['wheat'])
                        if quantity > 0:
                            target_node_id = other_villager['node_id']
                            suggested_price = 7
                            total_price = suggested_price * quantity
                            
                            # 检查是否已经发送过相同的交易请求
                            if not self.has_sent_trade_request(target_node_id, 'wheat', quantity, total_price):
                                opportunities['buy_opportunities'].append({
                                    'target': target_node_id,
                                    'target_name': other_villager.get('name', 'Unknown'),
                                    'item': 'wheat',
                                    'quantity': quantity,
                                    'suggested_price': suggested_price,
                                    'total_price': total_price,
                                    'merchant_buy_price': prices.get('sell', {}).get('wheat', 5),
                                    'merchant_sell_price': prices.get('buy', {}).get('wheat', 10),
                                    'negotiation_message': f"Hi! I'd like to buy {quantity}x wheat from you for {total_price} gold total ({suggested_price} gold each). This is better than the merchant's price of 10 gold each. Are you interested?"
                                })
        
        elif occupation == 'carpenter' and inventory.get('wood', 0) < 10:
            # 木工从其他村民购买木材（如果有的话）
            for other_villager in villagers:
                if other_villager.get('node_id') != villager.get('node_id'):
                    other_inventory = other_villager.get('inventory', {})
                    if other_inventory.get('wood', 0) > 0:
                        quantity = min(10 - inventory.get('wood', 0), other_inventory['wood'])
                        if quantity > 0:
                            opportunities['buy_opportunities'].append({
                                'target': other_villager['node_id'],
                                'target_name': other_villager.get('name', 'Unknown'),
                                'item': 'wood',
                                'quantity': quantity,
                                'suggested_price': 7,  # 介于5(merchant buy)和10(merchant sell)之间
                                'total_price': 7 * quantity,
                                'merchant_buy_price': prices.get('sell', {}).get('wood', 5),
                                'merchant_sell_price': prices.get('buy', {}).get('wood', 10)
                            })
        
        return opportunities
    
    def _format_p2p_opportunities(self, opportunities: Dict) -> str:
        """格式化P2P交易机会显示"""
        if not opportunities:
            return "No P2P opportunities available"
        
        result = []
        
        # 出售机会
        sell_ops = opportunities.get('sell_opportunities', [])
        if sell_ops:
            result.append("🎯 SELL OPPORTUNITIES:")
            for op in sell_ops:
                profit_per_item = op['suggested_price'] - op['merchant_buy_price']
                result.append(f"  → Sell {op['quantity']}x {op['item']} to {op['target_name']} ({op['target']})")
                result.append(f"    Command: trade {op['target']} sell {op['item']} {op['quantity']} {op['total_price']}")
                result.append(f"    Negotiation: send {op['target']} \"{op.get('negotiation_message', '')}\"")
                result.append(f"    Price: {op['suggested_price']} gold each (vs merchant {op['merchant_buy_price']} gold)")
                result.append(f"    Extra profit: +{profit_per_item * op['quantity']} gold")
                result.append(f"    ⚠️ IMPORTANT: Use node ID '{op['target']}' not name '{op['target_name']}'")
                result.append("")
        
        # 购买机会
        buy_ops = opportunities.get('buy_opportunities', [])
        if buy_ops:
            result.append("💰 BUY OPPORTUNITIES:")
            for op in buy_ops:
                savings_per_item = op['merchant_sell_price'] - op['suggested_price']
                result.append(f"  → Buy {op['quantity']}x {op['item']} from {op['target_name']} ({op['target']})")
                result.append(f"    Command: trade {op['target']} buy {op['item']} {op['quantity']} {op['total_price']}")
                result.append(f"    Negotiation: send {op['target']} \"{op.get('negotiation_message', '')}\"")
                result.append(f"    Price: {op['suggested_price']} gold each (vs merchant {op['merchant_sell_price']} gold)")
                result.append(f"    Savings: -{savings_per_item * op['quantity']} gold")
                result.append(f"    ⚠️ IMPORTANT: Use node ID '{op['target']}' not name '{op['target_name']}'")
                result.append("")
        
        if not sell_ops and not buy_ops:
            return "No P2P opportunities available"
        
        return "\n".join(result)
    
    def check_villager_status(self, node_id: str) -> Dict:
        """检查指定村民的状态"""
        try:
            # 从协调器获取节点信息
            response = requests.get(f"{self.coordinator_url}/nodes", timeout=5)
            if response.status_code != 200:
                return {"error": "Cannot get nodes list"}
            
            nodes_data = response.json()
            target_node = None
            
            # 查找目标节点
            for node in nodes_data['nodes']:
                if node['node_id'] == node_id:
                    target_node = node
                    break
            
            if not target_node:
                return {"error": f"Node {node_id} not found"}
            
            # 获取目标村民的详细状态
            villager_response = requests.get(f"http://{target_node['address']}/villager", timeout=5)
            if villager_response.status_code != 200:
                return {"error": f"Cannot get villager status for {node_id}"}
            
            villager_data = villager_response.json()
            
            # 检查是否可以交易
            can_trade = True
            reason = ""
            
            # 只有体力不足时才无法交易，已提交行动不影响交易
            if villager_data.get('stamina', 0) < 20:
                can_trade = False
                reason = "目标村民体力不足，无法交易"
            elif villager_data.get('has_submitted_action', False):
                # 已提交行动但仍可交易，只是提醒状态
                can_trade = True
                reason = "目标村民已提交行动，但可以交易"
            
            return {
                "node_id": node_id,
                "name": villager_data.get('name', 'Unknown'),
                "occupation": villager_data.get('occupation', 'Unknown'),
                "stamina": villager_data.get('stamina', 0),
                "has_submitted_action": villager_data.get('has_submitted_action', False),
                "can_trade": can_trade,
                "reason": reason,
                "inventory": villager_data.get('inventory', {})
            }
            
        except Exception as e:
            return {"error": f"Error checking villager status: {e}"}
    
    def send_negotiation_message(self, target: str, item: str, quantity: int, price: int, trade_type: str) -> bool:
        """发送谈判消息"""
        try:
            # 构建谈判消息
            if trade_type == 'buy':
                message = f"Hi! I'd like to buy {quantity}x {item} from you for {price} gold total ({price//quantity} gold each). This is better than the merchant's price of {price//quantity + 3} gold each. Are you interested?"
            else:  # sell
                message = f"Hi! I have {quantity}x {item} to sell for {price} gold total ({price//quantity} gold each). This is better than the merchant's buy price of {price//quantity - 2} gold each. Would you like to buy?"
            
            # 发送消息
            response = requests.post(f"{self.villager_url}/messages/send",
                                   json={
                                       'target': target,
                                       'content': message,
                                       'type': 'private'
                                   }, timeout=10)
            
            if response.status_code == 200:
                print(f"[AI Agent] 谈判消息已发送给 {target}: {message}")
                return True
            else:
                print(f"[AI Agent] ✗ 发送谈判消息失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[AI Agent] ✗ 发送谈判消息异常: {e}")
            return False
    
    def has_sent_trade_request(self, target: str, item: str, quantity: int, price: int) -> bool:
        """检查是否已经发送过相同的交易请求"""
        trade_key = f"{target}_{item}_{quantity}_{price}"
        return trade_key in self.sent_trades_tracker
    
    def mark_trade_request_sent(self, target: str, item: str, quantity: int, price: int):
        """标记交易请求已发送"""
        trade_key = f"{target}_{item}_{quantity}_{price}"
        self.sent_trades_tracker[trade_key] = {
            "target": target,
            "item": item,
            "quantity": quantity,
            "price": price,
            "timestamp": time.time()
        }
    
    def clear_old_trade_requests(self):
        """清理旧的交易请求记录（超过5分钟的）"""
        current_time = time.time()
        old_keys = []
        for key, trade_info in self.sent_trades_tracker.items():
            if current_time - trade_info["timestamp"] > 300:  # 5分钟
                old_keys.append(key)
        
        for key in old_keys:
            del self.sent_trades_tracker[key]
    
    def _handle_pending_trades(self, trades_received: List[Dict], context: Dict):
        """处理待处理的交易请求"""
        villager = context.get('villager', {})
        inventory = villager.get('inventory', {}).get('items', {})
        money = villager.get('inventory', {}).get('money', 0)
        occupation = villager.get('occupation', '')
        
        for trade in trades_received:
            trade_id = trade.get('trade_id', '')
            item = trade.get('item', '')
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0)
            offer_type = trade.get('offer_type', '')
            from_villager = trade.get('from', '')
            
            print(f"[AI Agent] {self.villager_name} 处理交易请求: {offer_type} {quantity}x {item} for {price} gold from {from_villager}")
            
            # 简单的交易决策逻辑
            should_accept = False
            reason = ""
            
            if offer_type == 'buy':
                # 对方想买我的物品
                if inventory.get(item, 0) >= quantity:
                    # 检查价格是否合理
                    merchant_prices = context.get('prices', {}).get('prices', {})
                    merchant_buy_price = merchant_prices.get(item, 0) * quantity
                    
                    if price >= merchant_buy_price * 0.8:  # 至少是商人价格的80%
                        should_accept = True
                        reason = f"价格合理 ({price} >= {merchant_buy_price * 0.8})"
                    else:
                        reason = f"价格太低 ({price} < {merchant_buy_price * 0.8})"
                else:
                    reason = f"物品不足 ({inventory.get(item, 0)} < {quantity})"
            
            elif offer_type == 'sell':
                # 对方想卖物品给我
                if money >= price:
                    # 检查价格是否合理
                    merchant_prices = context.get('prices', {}).get('prices', {})
                    merchant_sell_price = merchant_prices.get(item, 0) * quantity
                    
                    if price <= merchant_sell_price * 1.2:  # 最多是商人价格的120%
                        should_accept = True
                        reason = f"价格合理 ({price} <= {merchant_sell_price * 1.2})"
                    else:
                        reason = f"价格太高 ({price} > {merchant_sell_price * 1.2})"
                else:
                    reason = f"货币不足 ({money} < {price})"
            
            # 执行交易决策
            if should_accept:
                print(f"[AI Agent] {self.villager_name} 接受交易: {reason}")
                try:
                    success = self.execute_action("accept_trade", trade_id=trade_id)
                    if success:
                        print(f"[AI Agent] ✓ 交易接受成功")
                    else:
                        print(f"[AI Agent] ✗ 交易接受失败")
                except Exception as e:
                    print(f"[AI Agent] ✗ 交易接受异常: {e}")
            else:
                print(f"[AI Agent] {self.villager_name} 拒绝交易: {reason}")
                try:
                    success = self.execute_action("reject_trade", trade_id=trade_id)
                    if success:
                        print(f"[AI Agent] ✓ 交易拒绝成功")
                    else:
                        print(f"[AI Agent] ✗ 交易拒绝失败")
                except Exception as e:
                    print(f"[AI Agent] ✗ 交易拒绝异常: {e}")
    
    def create_villager(self, name: str, occupation: str, gender: str, personality: str) -> bool:
        """创建村民"""
        try:
            response = requests.post(
                f"{self.villager_url}/villager",
                json={
                    'name': name,
                    'occupation': occupation,
                    'gender': gender,
                    'personality': personality
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    self.villager_info = result['villager']
                    self.villager_name = name
                    self.villager_occupation = occupation
                    print(f"[AI Agent] ✓ 村民创建成功: {name} ({occupation})")
                    return True
                else:
                    print(f"[AI Agent] ✗ 村民创建失败: {result.get('message')}")
                    return False
            else:
                print(f"[AI Agent] ✗ 村民创建失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"[AI Agent] ✗ 村民创建异常: {e}")
            return False
    
    def _can_produce_now(self, villager: Dict) -> bool:
        """检查是否可以立即生产"""
        occ = villager.get('occupation', '').lower()
        items = villager.get('inventory', {}).get('items', {}) or {}
        stamina = villager.get('stamina', 0)
        if occ == 'farmer':
            return items.get('seed', 0) >= 1 and stamina >= 20
        if occ == 'chef':
            return items.get('wheat', 0) >= 3 and stamina >= 15
        if occ == 'carpenter':
            return items.get('wood', 0) >= 10 and stamina >= 30
        return False

    def execute_action(self, action: str, **kwargs) -> bool:
        """执行行动"""
        try:
            if action == "produce":
                response = requests.post(f"{self.villager_url}/action/produce", timeout=10)
            elif action == "sleep":
                response = requests.post(f"{self.villager_url}/action/sleep", timeout=10)
            elif action == "idle":
                response = requests.post(f"{self.villager_url}/action/submit", 
                                       json={'action': 'idle'}, timeout=10)
            elif action == "buy":
                item = kwargs.get('item')
                quantity = kwargs.get('quantity')
                response = requests.post(f"{self.villager_url}/action/trade",
                                       json={'action': 'buy', 'target': 'merchant', 'item': item, 'quantity': quantity}, timeout=10)
            elif action == "sell":
                item = kwargs.get('item')
                quantity = kwargs.get('quantity')
                response = requests.post(f"{self.villager_url}/action/trade",
                                       json={'action': 'sell', 'target': 'merchant', 'item': item, 'quantity': quantity}, timeout=10)
            elif action == "eat":
                response = requests.post(f"{self.villager_url}/action/eat", timeout=10)
            elif action == "price":
                response = requests.get(f"{self.merchant_url}/prices", timeout=10)
                if response.status_code == 200:
                    prices_data = response.json()
                    print(f"[AI Agent] 商人价格: {prices_data}")
                    return True
                else:
                    print(f"[AI Agent] ✗ 获取价格失败: HTTP {response.status_code}")
                    return False
            elif action == "trades":
                response = requests.get(f"{self.villager_url}/trade/pending", timeout=10)
                if response.status_code == 200:
                    trades_data = response.json()
                    print(f"[AI Agent] 收到的交易请求: {trades_data}")
                    return True
                else:
                    print(f"[AI Agent] ✗ 获取交易请求失败: HTTP {response.status_code}")
                    return False
            elif action == "mytrades":
                response = requests.get(f"{self.villager_url}/mytrades", timeout=10)
                if response.status_code == 200:
                    trades_data = response.json()
                    print(f"[AI Agent] 发送的交易请求: {trades_data}")
                    return True
                else:
                    print(f"[AI Agent] ✗ 获取发送交易失败: HTTP {response.status_code}")
                    return False
            elif action == "trade":
                target = kwargs.get('target')
                trade_action = kwargs.get('trade_action', 'buy')
                item = kwargs.get('item')
                quantity = kwargs.get('quantity')
                price = kwargs.get('price')
                
                # 检查是否已经发送过相同的交易请求
                if self.has_sent_trade_request(target, item, quantity, price):
                    print(f"[AI Agent] ⚠️ 已经发送过相同的交易请求: {trade_action} {quantity}x {item} to {target} for {price} gold")
                    return False
                
                # 检查目标村民状态
                target_status = self.check_villager_status(target)
                if 'error' in target_status:
                    print(f"[AI Agent] ✗ 无法检查目标村民状态: {target_status['error']}")
                    return False
                
                if not target_status.get('can_trade', True):
                    print(f"[AI Agent] ⚠️ 目标村民无法交易: {target_status.get('reason', 'Unknown reason')}")
                    return False
                
                # 首先从协调器获取目标节点地址
                villager_state = self.get_villager_status() or {}
                coordinator_addr = villager_state.get('coordinator_address', 'localhost:5000')
                nodes_response = requests.get(f"http://{coordinator_addr}/nodes", timeout=5)
                
                if nodes_response.status_code != 200:
                    print(f"[AI Agent] ✗ 获取节点列表失败: HTTP {nodes_response.status_code}")
                    return False
                
                nodes_data = nodes_response.json()
                target_node = None
                
                # 查找目标节点（支持节点ID和村民名称）
                for node in nodes_data['nodes']:
                    if node['node_id'] == target or node.get('name') == target:
                        target_node = node
                        break
                
                if not target_node:
                    print(f"[AI Agent] ✗ 找不到目标节点: {target}")
                    return False
                
                # 发送交易请求到目标节点
                response = requests.post(f"http://{target_node['address']}/trade/request", 
                                        json={
                                            'from': self.villager_name,
                                            'from_address': f'localhost:{self.villager_port}',
                                            'item': item,
                                            'quantity': quantity,
                                            'price': price,
                                            'offer_type': trade_action
                                        }, timeout=10)
                if response.status_code == 200:
                    trade_data = response.json()
                    print(f"[AI Agent] 交易请求已发送: {trade_action} {quantity}x {item} for {price} gold to {target}")
                    # 标记交易请求已发送
                    self.mark_trade_request_sent(target, item, quantity, price)
                    
                    # 将交易记录添加到 villager 节点的 sent_trades 中
                    try:
                        sent_trade_record = {
                            'trade_id': trade_data.get('trade_id', f"trade_{int(time.time())}"),
                            'target': target,
                            'target_name': target_status.get('name', target),
                            'item': item,
                            'quantity': quantity,
                            'price': price,
                            'action': trade_action,
                            'timestamp': time.time(),
                            'status': 'pending'
                        }
                        
                        # 发送到 villager 节点记录
                        requests.post(f"{self.villager_url}/sent_trades/add",
                                   json=sent_trade_record, timeout=5)
                    except Exception as e:
                        print(f"[AI Agent] 记录发送交易失败: {e}")
                    
                    return True
                else:
                    print(f"[AI Agent] ✗ 发送交易请求失败: HTTP {response.status_code}")
                    return False
            elif action == "send_message":
                target = kwargs.get('target')
                content = kwargs.get('content')
                message_type = kwargs.get('type', 'private')
                response = requests.post(f"{self.villager_url}/messages/send",
                                       json={'target': target, 'content': content, 'type': message_type}, timeout=10)
            elif action == "accept_trade":
                trade_id = kwargs.get('trade_id')
                response = requests.post(f"{self.villager_url}/trade/accept",
                                       json={'trade_id': trade_id}, timeout=10)
            elif action == "reject_trade":
                trade_id = kwargs.get('trade_id')
                response = requests.post(f"{self.villager_url}/trade/reject",
                                       json={'trade_id': trade_id}, timeout=10)
            elif action == "confirm_trade":
                trade_id = kwargs.get('trade_id')
                response = requests.post(f"{self.villager_url}/trade/confirm",
                                       json={'trade_id': trade_id}, timeout=10)
            else:
                print(f"[AI Agent] ✗ 未知行动: {action}")
                return False
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', True):
                    print(f"[AI Agent] ✓ 执行行动成功: {action}")
                    return True
                else:
                    print(f"[AI Agent] ✗ 执行行动失败: {result.get('message')}")
                    return False
            else:
                print(f"[AI Agent] ✗ 执行行动失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"[AI Agent] ✗ 执行行动异常: {e}")
            return False
    
    def generate_decision(self, context: Dict) -> Dict:
        """生成决策（支持ReAct和传统模式）"""
        if not self.api_key:
            print("[AI Agent] ✗ 未配置API Key，无法使用GPT")
            return {"action": "idle", "reason": "No API key configured"}
        
        try:
            if self.use_react:
                # 使用ReAct结构
                prompt = self._build_react_prompt(context)
                system_prompt = self._get_react_system_prompt()
                max_tokens = 800
            else:
                # 使用传统JSON模式
                prompt = self._build_prompt(context)
                system_prompt = self._get_system_prompt()
                max_tokens = 500
            
            # 调试：打印GPT看到的状态
            print(f"[AI Agent DEBUG] GPT看到的状态:")
            print(f"  体力: {context.get('villager', {}).get('stamina')}/{context.get('villager', {}).get('max_stamina')}")
            print(f"  货币: {context.get('villager', {}).get('inventory', {}).get('money')}")
            print(f"  物品: {context.get('villager', {}).get('inventory', {}).get('items')}")
            print(f"  消息: {len(context.get('messages', []))} 条")
            print(f"  交易请求: {len(context.get('trades_received', []))} 条")
            print(f"  发送交易: {len(context.get('trades_sent', []))} 条")
            print(f"  已提交行动: {context.get('villager', {}).get('has_submitted_action', False)}")
            print(f"  其他村民状态: {[(v['name'], v.get('has_submitted_action', False)) for v in context.get('villagers', [])]}")
            
            # 调用GPT API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            decision_text = response.choices[0].message.content.strip()
            
            # 根据模式解析决策
            if self.use_react:
                decision = self._parse_react_decision(decision_text)
            else:
                decision = self._parse_decision(decision_text)
            
            # 记录决策历史
            self.decision_history.append({
                'timestamp': datetime.now().isoformat(),
                'context': context,
                'decision': decision,
                'raw_response': decision_text
            })
            
            return decision
            
        except Exception as e:
            print(f"[AI Agent] ✗ GPT决策生成失败: {e}")
            return {"action": "idle", "reason": f"GPT error: {str(e)}"}
    
    def _get_react_system_prompt(self) -> str:
        """获取ReAct系统提示词"""
        return """You are a **ReAct Villager Agent** in the *Distributed Virtual Town* simulation.

You must follow the ReAct (Reasoning + Acting) pattern:

**THOUGHT**: Analyze the current situation, consider your goals, and reason about what action to take.
**ACTION**: Execute exactly one command based on your reasoning.
**OBSERVATION**: The result of your action will be provided for the next cycle.

## Available Actions:
- `buy <item> <quantity>` - Buy from merchant (no action cost)
- `sell <item> <quantity>` - Sell to merchant (no action cost)  
- `eat` - Eat bread to restore stamina (no action cost)
- `produce` - Produce items (consumes action point + stamina)
- `sleep` - Sleep to restore stamina (consumes action point, evening only, REQUIRES HOUSE!)
- `idle` - Skip current segment (consumes action point)
- `price` - Check merchant prices (no action cost)
- `trades` - Check received trade requests (no action cost) - **READ ONLY**
- `mytrades` - Check sent trade requests (no action cost) - **READ ONLY**
- `trade <node_id> <buy/sell> <item> <quantity> <total_price>` - **SEND trade request to villager**
- `send <target> <message>` - Send message to another villager
- `accept <trade_id>` - Accept a trade request
- `reject <trade_id>` - Reject a trade request

## Game Rules:
- Each time segment allows ONE main action (produce/sleep/idle)
- Trading and eating don't consume action points
- Stamina: 0-100, work consumes stamina, sleep restores stamina
- Hunger: -10 stamina daily, -20 extra if no sleep at night
- **CRITICAL: Sleep requires a HOUSE! You cannot sleep without a house.**
- **IMPORTANT: Buy and produce are SEPARATE decisions! Buy resources first, then produce in the next decision.**
- **ACTION SUBMISSION STATUS: If you have already submitted your action for this time segment, you can still:**
  - Respond to trade requests (accept/reject)
  - Send and read messages
  - Eat bread to restore stamina
  - Check prices and trades
  - **Send new trade requests to other villagers**
  - **BUT CANNOT: produce, sleep, buy, sell, or idle (these consume action points)**
  - **IMPORTANT: Trading is ALWAYS allowed, even after submitting actions!**

## P2P Trading Strategy (HIGHEST PRIORITY):
- **Selling**: Always try to sell products to villagers at better prices than merchant buy prices
- **Buying**: Always try to buy materials from villagers at better prices than merchant sell prices
- **Smart Pricing**: Use prices between merchant buy/sell prices for maximum profit
- **Targeting**: Use villager occupation and inventory to identify trade partners
- **Status Check**: Before trading, check if target villager can trade (not waiting/submitted action)
- **No Spam**: Don't send duplicate trade requests to the same villager
- **Negotiation First**: Always send a negotiation message before sending trade request
- **CRITICAL**: After negotiation, ALWAYS send the actual trade request using `trade` command
- **IMPORTANT**: `trades` command only shows received requests - use `trade` command to SEND requests
- **Fallback**: If P2P trading fails, fall back to merchant trading
- **Examples**:
  - Farmer: `send node2 "Hi! I have 3x wheat to sell for 21 gold total (7 gold each). This is better than the merchant's buy price of 5 gold each. Would you like to buy?"`
  - Chef: `send node1 "Hi! I'd like to buy 3x wheat from you for 21 gold total (7 gold each). This is better than the merchant's price of 10 gold each. Are you interested?"`
  - After negotiation: `trade node2 sell wheat 3 21` or `trade node1 buy wheat 3 21`

## Trading Workflow:
1. **Negotiation Phase**: Send message to discuss price and terms
2. **Action Phase**: Send actual trade request using `trade` command
3. **Response Phase**: Use `accept` or `reject` for received requests
4. **Confirmation Phase**: Use `confirm` to complete accepted trades

**CRITICAL**: Don't just negotiate - always follow up with actual trade requests!
**REMEMBER**: `trades` shows what you received, `trade` sends what you want to offer!
**IMPORTANT**: When you see trade requests in `trades`, decide whether to accept or reject them!

## Output Format:
Always follow this exact format:

THOUGHT: [Your reasoning about the current situation and what action to take]

ACTION: [Single command to execute]

Example:
THOUGHT: I'm a farmer with 0 seeds and 100 stamina. I need seeds to produce wheat. I should buy 1-2 seeds first.

ACTION: buy seed 2

Remember: Only output THOUGHT and ACTION. The OBSERVATION will be provided in the next cycle."""

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """You are a **single villager node** agent in the *Distributed Virtual Town* simulation.
Your task is to keep your villager alive, productive, and economically efficient in a distributed world of villagers, merchants, and a time coordinator.
You operate autonomously, following the game's rules, using REST/CLI actions to interact with the world.

---

## 1. World and Objectives

* The world includes a **Time Coordinator**, a **Merchant**, and multiple **Villagers** (each an independent node).
* Time is divided into **Morning**, **Noon**, and **Night**.
* The world advances only when all villagers have submitted their action for the current period.
* Each villager has attributes: **occupation**, **stamina (0–100)**, **money**, and **inventory** (`seed`, `wheat`, `bread`, `wood`, `house`, `temp_room`).

**Your goals:**
1. Stay alive (don't let stamina reach 0).
2. Grow wealth and asset value.
3. Use stamina and time efficiently to maximize long-term productivity.

---

## 2. Core Rules

* **Three time periods per day:** Morning, Noon, Night.
* Each period allows **one submitted action** (e.g., `produce`, `sleep`, or `idle`).
* **Production actions** cost **1 action point** and **stamina**.
* **Trading** and **eating** do **not** consume an action point.
* **Stamina mechanics:**
  * Base range: 0–100
  * Hunger: -10 stamina per day
  * Working costs stamina (per occupation)
  * Skipping sleep at night: -20 stamina
  * Eating bread restores stamina
  * Sleeping restores stamina but requires a `house` or `temp_room`

**Occupation recipes and stamina cost:**
* Farmer: `1 seed → 5 wheat` (costs 20 stamina)
* Chef: `3 wheat → 2 bread` (costs 15 stamina)
* Carpenter: `10 wood → 1 house` (costs 30 stamina)

---

## 3. Available Actions

**Basic actions**
* `eat` → consume bread to restore stamina (no action cost)
* `sleep` → restore stamina; requires house/temp_room; consumes action point

**Production (consumes action point + stamina)**
* `produce` or `work` → perform occupation-specific production

**Merchant trading (no action cost)**
* `buy <item> <quantity>`
* `sell <item> <quantity>`

**Idle (submit empty action)**
* `idle` → submit no production or sleep action (to let time advance)

---

## 4. Decision Loop (Every Time Period)

1. **Survival first:**
   * If stamina ≤ 35 → `eat` (if bread available).
   * If it's Night and stamina ≤ 45 → `sleep` (if housing available).

2. **P2P Trading logic (highest priority for profit):**
   * **Selling**: If you have products, try to sell to villagers at better prices than merchant.
   * **Buying**: If you need materials, try to buy from villagers at better prices than merchant.
   * **Targeting**: Use villager occupation and inventory to identify potential trade partners.

3. **Production logic:**
   * If stamina and materials are sufficient → `produce`.
   * If missing inputs → `buy` from merchant (only if no P2P options).
   * If unproductive → `idle`.

4. **Night strategy:**
   * Prefer sleeping to recover stamina; avoid overwork unless safe.

---

## 5. Occupation Strategies

**Farmer**
* Focus on turning seeds → wheat efficiently.
* Keep enough seeds for future cycles.
* **P2P Strategy**: Sell wheat to chefs at 6-8 gold each (vs merchant 5 gold buy, 10 gold sell).
* **Buyer Targeting**: Look for chefs with low wheat inventory.

**Chef**
* Convert wheat → bread for both self-use and sales.
* Always keep 2–3 bread for stamina recovery.
* **P2P Strategy**: 
  - Buy wheat from farmers at 6-8 gold each (vs merchant 10 gold sell).
  - Sell bread to villagers at 30-40 gold each (vs merchant 22.5 gold buy, 45 gold sell).
* **Targeting**: Look for farmers selling wheat, villagers needing bread.

**Carpenter**
* Convert wood → house for high profit but large stamina cost.
* Ensure own housing before selling houses.
* **P2P Strategy**: Sell houses at 150-200 gold (vs merchant 130 gold buy, 260 gold sell).
* **Buyer Targeting**: Look for villagers without houses who have money.

---

## 6. Output Policy

* Always output **one actionable command** or **a short explanation + one command**.
* Example formats:
  ```
  # Low stamina, eating bread
  eat
  ```
  or just
  ```
  produce
  ```
* You may explain reasoning briefly with a `#` comment above the command.
* Avoid verbose analysis or internal reasoning. Output must be short and actionable.

---

## 7. Critical Rules

* **DO NOT use compound commands** like "buy seed 5 && produce" or "buy seed 5; produce"
* **Only ONE command per decision**
* **After buying resources, ALWAYS produce in the same segment**
* **Buy/sell/eat don't consume action points - can be done before main action**

Return decision in JSON format:
{
    "command": "single_cli_command",
    "reason": "brief explanation"
}

EXAMPLES:
- Buy seeds: {"command": "buy seed 1", "reason": "Need seeds for wheat production"}
- Produce wheat: {"command": "produce", "reason": "Have seeds, producing wheat"}
- Sleep: {"command": "sleep", "reason": "Low stamina, need rest"}
- Eat bread: {"command": "eat", "reason": "Low stamina, need to restore energy"}
- Idle: {"command": "idle", "reason": "No immediate action needed"}

QUANTITY HEURISTIC:
- Farmer: Buy just enough seeds to cover this period's production, keep a buffer of 1-2 if money ≥ 2× seed price
- Chef: Ensure wheat ≥ 3 before producing; keep bread reserve 2-3 for stamina
- Carpenter: Accumulate toward 10 wood; don't starve other needs
- Choose quantities dynamically; buy the minimum needed to enable production now, plus a small buffer if affordable"""
    
    def _build_react_prompt(self, context: Dict) -> str:
        """构建ReAct提示词"""
        villager = context.get('villager', {})
        time_info = context.get('time', '')
        action_status = context.get('action_status', {})
        prices = context.get('prices', {})
        messages = self.get_messages()
        trades_received = self.get_trades_received()
        trades_sent = self.get_trades_sent()
        villagers = context.get('villagers', [])
        
        # 获取物品信息
        inventory = villager.get('inventory', {})
        items = inventory.get('items', {})
        money = inventory.get('money', 0)
        
        # 分析当前状态
        stamina = villager.get('stamina', 0)
        max_stamina = villager.get('max_stamina', 100)
        occupation = villager.get('occupation', 'Unknown')
        has_submitted = villager.get('has_submitted_action', False)
        has_slept = villager.get('has_slept', False)
        
        # 判断当前时段
        is_evening = 'evening' in time_info.lower() or 'night' in time_info.lower()
        
        prompt = f"""=== CURRENT STATE ===

Time: {time_info}
Villager: {villager.get('name', 'Unknown')} ({occupation})
Stamina: {stamina}/{max_stamina}
Money: {money} gold
Action Submitted: {has_submitted}
Sleep Status: {"Already slept today" if has_slept else "Not slept yet" + (" - Should sleep!" if is_evening else "")}

Inventory: {items if items else "Empty"}

Merchant Prices: {prices.get('prices', {}) if prices.get('prices') else "Use 'price' command to check"}

Messages: {len(messages)} received
{chr(10).join([f"- From {msg.get('from', 'Unknown')}: {msg.get('content', '')[:50]}..." for msg in messages[:3]]) if messages else "No messages"}

Trades: {len(trades_received)} received, {len(trades_sent)} sent
{chr(10).join([f"- Trade {trade.get('trade_id', '')}: {trade.get('from', 'Unknown')} wants to {trade.get('offer_type', '')} {trade.get('item', '')} x{trade.get('quantity', 0)} for {trade.get('price', 0)} gold total ({trade.get('price', 0)//trade.get('quantity', 1)} gold each)" for trade in trades_received[:3]]) if trades_received else "No trade requests"}

Online Villagers: {len(villagers)}
{chr(10).join([f"- {v['name']} ({v['occupation']}) - Action: {'✓ Submitted' if v.get('has_submitted_action', False) else '⏳ Pending'}" for v in villagers])}

=== ACTION SUBMISSION STATUS ===
Total Villagers: {len(villagers)}
Submitted: {sum(1 for v in villagers if v.get('has_submitted_action', False))}/{len(villagers)}
Waiting: {[v['name'] for v in villagers if not v.get('has_submitted_action', False)]}

=== PREVIOUS OBSERVATIONS ===
{self._get_recent_observations()}

=== IMPORTANT GAME RULES ===
- Sleep requires a HOUSE! You cannot sleep without a house.
- To get a house: Carpenter produces houses (10 wood → 1 house), or trade with other villagers
- Farmer: 1 seed → 5 wheat (costs 20 stamina)
- Chef: 3 wheat → 2 bread (costs 15 stamina) 
- Carpenter: 10 wood → 1 house (costs 30 stamina)
- Use 'price' command to check merchant prices (don't send messages to merchant)
- **CRITICAL: Buy and produce are SEPARATE decisions! Buy resources first, then produce in the next decision.**

Now follow the ReAct pattern:"""
        
        return prompt

    def _get_recent_observations(self) -> str:
        """获取最近的观察结果"""
        if not self.decision_history:
            return "No previous observations."
        
        recent = self.decision_history[-3:]  # 最近3次决策
        observations = []
        
        for entry in recent:
            timestamp = entry['timestamp'][:19]  # 去掉毫秒
            decision = entry['decision']
            action = decision.get('action', 'unknown')
            reason = decision.get('reason', 'No reason')
            success = decision.get('success', True)
            error_msg = decision.get('error_message', '')
            
            if success:
                observations.append(f"[{timestamp}] ACTION: {action} - SUCCESS - {reason}")
                # 如果是价格查询，显示价格信息
                if action == "price" and 'prices' in decision:
                    prices = decision.get('prices', {})
                    if prices:
                        observations.append(f"  PRICES: {prices}")
                # 如果是交易查询，显示交易信息
                elif action == "trades" and 'trades' in decision:
                    trades = decision.get('trades', [])
                    if trades:
                        observations.append(f"  RECEIVED TRADES: {len(trades)} requests")
                        for trade in trades[:2]:  # 显示前2个交易
                            observations.append(f"    - {trade.get('action', '')} {trade.get('item', '')} x{trade.get('quantity', 0)} for {trade.get('price', 0)} gold")
                elif action == "mytrades" and 'mytrades' in decision:
                    trades = decision.get('mytrades', [])
                    if trades:
                        observations.append(f"  SENT TRADES: {len(trades)} requests")
                        for trade in trades[:2]:  # 显示前2个交易
                            observations.append(f"    - {trade.get('action', '')} {trade.get('item', '')} x{trade.get('quantity', 0)} for {trade.get('price', 0)} gold")
            else:
                observations.append(f"[{timestamp}] ACTION: {action} - FAILED - {reason}")
                if error_msg:
                    observations.append(f"  ERROR: {error_msg}")
        
        return "\n".join(observations)

    def _build_prompt(self, context: Dict) -> str:
        """构建提示词"""
        villager = context.get('villager', {})
        time_info = context.get('time', '')
        action_status = context.get('action_status', {})
        prices = context.get('prices', {})
        messages = context.get('messages', [])
        villagers = context.get('villagers', [])
        
        # 获取物品信息
        inventory = villager.get('inventory', {})
        items = inventory.get('items', {})
        money = inventory.get('money', 0)
        
        # 分析当前状态
        stamina = villager.get('stamina', 0)
        max_stamina = villager.get('max_stamina', 100)
        occupation = villager.get('occupation', 'Unknown')
        has_submitted = villager.get('has_submitted_action', False)
        has_slept = villager.get('has_slept', False)
        
        # 分析资源需求
        resource_analysis = ""
        if occupation == 'farmer':
            seed_count = items.get('seed', 0)
            resource_analysis = f"Farmer needs seeds to produce wheat. Current seeds: {seed_count}"
            if seed_count == 0:
                resource_analysis += " ⚠️ No seeds! Need to buy first."
            elif seed_count >= 1:
                resource_analysis += " ✓ Ready to produce wheat!"
        elif occupation == 'chef':
            wheat_count = items.get('wheat', 0)
            resource_analysis = f"Chef needs wheat to produce bread. Current wheat: {wheat_count}"
            if wheat_count < 3:
                resource_analysis += " ⚠️ Not enough wheat, need at least 3!"
            else:
                resource_analysis += " ✓ Ready to produce bread!"
        elif occupation == 'carpenter':
            wood_count = items.get('wood', 0)
            resource_analysis = f"Carpenter needs wood to build house. Current wood: {wood_count}"
            if wood_count < 10:
                resource_analysis += " ⚠️ Not enough wood, need at least 10!"
            else:
                resource_analysis += " ✓ Ready to build house!"
        
        # 分析体力状况
        stamina_analysis = ""
        if stamina < 30:
            stamina_analysis = "⚠️ 体力严重不足，需要立即恢复！"
        elif stamina < 50:
            stamina_analysis = "⚠️ 体力较低，建议考虑恢复体力"
        else:
            stamina_analysis = "✓ 体力充足"
        
        # 分析睡眠需求
        sleep_analysis = ""
        if not has_slept and 'evening' in time_info.lower():
            sleep_analysis = "⚠️ Evening - Should sleep to avoid penalty"
        elif not has_slept:
            sleep_analysis = "Not slept yet (will sleep in evening)"
        else:
            sleep_analysis = "✓ Already slept today"
        
        # 判断当前时段
        is_morning = 'morning' in time_info.lower()
        is_noon = 'noon' in time_info.lower() or 'afternoon' in time_info.lower()
        is_evening = 'evening' in time_info.lower()
        
        # 当前时段建议
        segment_advice = ""
        if is_morning or is_noon:
            segment_advice = "PRODUCTION TIME - Focus on buying resources and producing"
        elif is_evening:
            segment_advice = "EVENING TIME - Should sleep if not yet slept today"
        
        # 获取消息和交易信息
        messages = self.get_messages()
        trades_received = self.get_trades_received()
        trades_sent = self.get_trades_sent()
        
        prompt = f"""=== CURRENT STATE ANALYSIS ===

Time: {time_info} - {segment_advice}
Villager: {villager.get('name', 'Unknown')} ({occupation})
Stamina: {stamina}/{max_stamina} {stamina_analysis}
Money: {money} gold
Action Submitted: {has_submitted}
Sleep Status: {sleep_analysis}

=== INVENTORY ===
{chr(10).join([f"- {item}: {count}" for item, count in items.items()]) if items else "No items"}

=== RESOURCE ANALYSIS ===
{resource_analysis}

=== ACTION STATUS ===
Total Villagers: {action_status.get('total_villagers', 0)}
Submitted: {action_status.get('submitted', 0)}
Waiting: {action_status.get('waiting_for', [])}

=== MERCHANT PRICES ===
{chr(10).join([f"- {item}: {price} gold" for item, price in prices.get('prices', {}).items()]) if prices.get('prices') else "Cannot get prices"}

=== MESSAGES ===
Messages Received: {len(messages)}
{chr(10).join([f"- From {msg.get('from', 'Unknown')}: {msg.get('content', '')[:50]}..." for msg in messages[:3]]) if messages else "No messages"}

=== TRADES ===
Trades Received: {len(trades_received)}
{chr(10).join([f"- Trade {trade.get('trade_id', '')}: {trade.get('from', 'Unknown')} wants to {trade.get('offer_type', '')} {trade.get('item', '')} x{trade.get('quantity', 0)} for {trade.get('price', 0)} gold total ({trade.get('price', 0)//trade.get('quantity', 1)} gold each)" for trade in trades_received[:3]]) if trades_received else "No trade requests"}

Trades Sent: {len(trades_sent)}
{chr(10).join([f"- Trade {trade.get('id', '')}: {trade.get('action', '')} {trade.get('item', '')} x{trade.get('quantity', 0)} for {trade.get('price', 0)} gold" for trade in trades_sent[:3]]) if trades_sent else "No sent trades"}

=== ONLINE VILLAGERS ===
Online Villagers: {len(villagers)}
{chr(10).join([f"- {v['name']} ({v['occupation']}) - Action: {'✓ Submitted' if v.get('has_submitted_action', False) else '⏳ Pending'}" for v in villagers])}

=== ACTION SUBMISSION STATUS ===
Total Villagers: {len(villagers)}
Submitted: {sum(1 for v in villagers if v.get('has_submitted_action', False))}/{len(villagers)}
Waiting: {[v['name'] for v in villagers if not v.get('has_submitted_action', False)]}

=== P2P TRADING OPPORTUNITIES ===
{self._format_p2p_opportunities(context.get('p2p_opportunities', {}))}

=== DECISION GUIDELINES ===
Make smart decisions based on the above information:

1. CHECK STAMINA FIRST:
   - If stamina >= 50: You have sufficient stamina, focus on work
   - If stamina < 30: Urgent! Buy bread or sleep
   - Sleep is ONLY needed in evening segment to avoid penalty

2. PRODUCTION WORKFLOW (if stamina is good):
   - Step 1: Buy necessary resources (buy seed 1-2)
   - Step 2: Immediately produce (produce) - SAME SEGMENT!
   - Farmer: buy seed → produce wheat
   - Chef: buy wheat → produce bread
   - Carpenter: buy wood → produce house

3. P2P TRADING STRATEGY (HIGHEST PRIORITY):
   - **ALWAYS check P2P opportunities first** before buying from merchant!
   - **Selling**: If you have products, try to sell to villagers at better prices than merchant
   - **Buying**: If you need materials, try to buy from villagers at better prices than merchant
   - **Smart Pricing**: Use prices between merchant buy/sell prices for maximum profit
   - **Status Check**: Check if target villager can trade (not waiting/submitted action)
   - **No Spam**: Don't send duplicate trade requests to the same villager
   - **Negotiation First**: Always send a negotiation message before sending trade request
   - **Fallback**: If P2P trading fails, fall back to merchant trading
   - **Examples**:
     * Farmer: `send node2 "Hi! I have 3x wheat to sell for 21 gold total (7 gold each). This is better than the merchant's buy price of 5 gold each. Would you like to buy?"`
     * Chef: `send node1 "Hi! I'd like to buy 3x wheat from you for 21 gold total (7 gold each). This is better than the merchant's price of 10 gold each. Are you interested?"`
     * After negotiation: `trade node2 sell wheat 3 21` or `trade node1 buy wheat 3 21`
   - Use 'send <node_id> "<message>"' for negotiation, then 'trade <node_id> buy/sell <item> <quantity> <total_price>' for actual trade
   - IMPORTANT: Use node IDs (node1, node2) not names!

4. PRODUCTION WORKFLOW (if no P2P opportunities):
   - Buy resources from merchant FIRST, then produce immediately
   - Don't keep buying without producing!
   - Sell excess products to merchant for profit

5. TRADING OPPORTUNITIES:
   - **Farmer**: Sell wheat to chefs, buy seeds from other farmers
   - **Chef**: Sell bread to everyone, buy wheat from farmers  
   - **Carpenter**: Sell houses to everyone, buy wood from other carpenters
   - **Smart trading**: Offer competitive prices (slightly below merchant prices)
   - **Check trades**: Use 'trades' to see incoming requests, 'mytrades' for sent requests
   - **Respond to trades**: Use 'accept <trade_id>' or 'reject <trade_id>'
   - **Complete trades**: Use 'confirm <trade_id>' after other party accepts

5. TIME MANAGEMENT:
   - Morning/Afternoon: Buy resources → Produce → Trade opportunities
   - Evening: Consider sleeping if not yet slept today
   - Only idle if no better options

6. TRADING EXAMPLES:
   - "trade node2 sell wheat 5 80" → Sell 5 wheat to node2 for 80 gold total
   - "trade node1 buy seed 2 15" → Buy 2 seeds from node1 for 15 gold total
   - "trades" → Check incoming trade requests
   - "accept trade_0" → Accept a trade request
   - "confirm trade_0" → Complete a trade after acceptance
   
   IMPORTANT: Use node IDs (node1, node2, etc.) not names for trading!
   IMPORTANT: Price is TOTAL price, not per-unit price!

CRITICAL: After buying resources, ALWAYS produce in the same segment!
CRITICAL: Look for trading opportunities with other villagers!
CRITICAL: Always provide complete CLI command with all parameters!

Return JSON decision format."""
        
        return prompt
    
    def _parse_react_decision(self, decision_text: str) -> Dict:
        """解析ReAct决策"""
        try:
            lines = decision_text.strip().split('\n')
            thought = ""
            action = "idle"
            reason = "No reasoning provided"
            
            # 解析THOUGHT和ACTION
            for line in lines:
                line = line.strip()
                if line.startswith('THOUGHT:'):
                    thought = line[8:].strip()
                    reason = thought
                elif line.startswith('ACTION:'):
                    action_line = line[7:].strip()
                    # 解析动作
                    parts = action_line.split()
                    if parts:
                        action = parts[0].lower()
                        if action == "buy" and len(parts) >= 3:
                            try:
                                quantity = int(parts[2])
                                return {
                                    "action": "buy",
                                    "reason": reason,
                                    "command": action_line,
                                    "item": parts[1],
                                    "quantity": quantity
                                }
                            except ValueError:
                                pass
                        elif action == "sell" and len(parts) >= 3:
                            try:
                                quantity = int(parts[2])
                                return {
                                    "action": "sell", 
                                    "reason": reason,
                                    "command": action_line,
                                    "item": parts[1],
                                    "quantity": quantity
                                }
                            except ValueError:
                                pass
                        elif action == "send" and len(parts) >= 3:
                            target = parts[1]
                            content = " ".join(parts[2:])
                            return {
                                "action": "send",
                                "reason": reason,
                                "command": action_line,
                                "target": target,
                                "content": content
                            }
                        elif action == "price":
                            return {
                                "action": "price",
                                "reason": reason,
                                "command": action_line
                            }
                        elif action == "trades":
                            return {
                                "action": "trades",
                                "reason": reason,
                                "command": action_line
                            }
                        elif action == "mytrades":
                            return {
                                "action": "mytrades",
                                "reason": reason,
                                "command": action_line
                            }
                        elif action == "accept" and len(parts) >= 2:
                            # 格式: accept trade_1 或 accept 1
                            trade_id = parts[1]
                            if not trade_id.startswith('trade_'):
                                trade_id = f"trade_{trade_id}"
                            return {
                                "action": "accept",
                                "reason": reason,
                                "command": action_line,
                                "trade_id": trade_id
                            }
                        elif action == "reject" and len(parts) >= 2:
                            # 格式: reject trade_1 或 reject 1
                            trade_id = parts[1]
                            if not trade_id.startswith('trade_'):
                                trade_id = f"trade_{trade_id}"
                            return {
                                "action": "reject",
                                "reason": reason,
                                "command": action_line,
                                "trade_id": trade_id
                            }
                        elif action == "trade" and len(parts) >= 6:
                            # 正确的格式: trade <节点ID> <buy/sell> <物品> <数量> <总价>
                            trade_action = parts[2].lower()
                            if trade_action not in ['buy', 'sell']:
                                # 如果使用了错误的动作，尝试修正
                                if trade_action in ['offer', 'purchase']:
                                    trade_action = 'buy'
                                elif trade_action in ['sell_to', 'give']:
                                    trade_action = 'sell'
                                else:
                                    trade_action = 'buy'  # 默认
                            
                            return {
                                "action": "trade",
                                "reason": reason,
                                "command": action_line,
                                "target": parts[1],
                                "trade_action": trade_action,
                                "item": parts[3],
                                "quantity": int(parts[4]),
                                "price": int(parts[5])  # 总价
                            }
                        else:
                            return {
                                "action": action,
                                "reason": reason,
                                "command": action_line
                            }
            
            return {"action": "idle", "reason": reason, "command": "idle"}
            
        except Exception as e:
            print(f"[AI Agent] ✗ ReAct解析失败: {e}")
            return {"action": "idle", "reason": f"Parse error: {str(e)}", "command": "idle"}

    def _parse_decision(self, decision_text: str) -> Dict:
        """解析GPT返回的决策"""
        try:
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{.*\}', decision_text, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                command = decision.get('command', 'idle')
                reason = decision.get('reason', 'No reason provided')
                
                # 处理复合命令（如 "buy seed 5 && produce" 或 "buy seed 5; produce"）
                if '&&' in command or ';' in command:
                    separator = '&&' if '&&' in command else ';'
                    commands = [cmd.strip() for cmd in command.split(separator)]
                    # 只执行第一个命令
                    command = commands[0]
                    print(f"[AI Agent] 检测到复合命令，只执行第一个: {command}")
                
                # 验证命令格式
                parts = command.split()
                if not parts:
                    return {"action": "idle", "reason": "Empty command", "command": "idle"}
                
                action = parts[0].lower()
                
                # 构建返回结果
                result = {"action": action, "reason": reason, "command": command}
                
                # 添加特定参数
                if action == "buy" and len(parts) >= 3:
                    try:
                        result["item"] = parts[1]
                        result["quantity"] = int(parts[2])
                    except ValueError:
                        result["reason"] = f"Invalid quantity: {parts[2]}"
                elif action == "sell" and len(parts) >= 3:
                    try:
                        result["item"] = parts[1]
                        result["quantity"] = int(parts[2])
                    except ValueError:
                        result["reason"] = f"Invalid quantity: {parts[2]}"
                elif action == "produce" and len(parts) >= 2:
                    result["item"] = parts[1]
                elif action == "send" and len(parts) >= 3:
                    result["target"] = parts[1]
                    result["content"] = " ".join(parts[2:]).strip('"')
                
                return result
            else:
                # 如果没有找到JSON，尝试简单解析
                lines = decision_text.split('\n')
                action = "idle"
                reason = decision_text
                
                for line in lines:
                    if 'action' in line.lower():
                        if 'produce' in line.lower():
                            action = "produce"
                        elif 'sleep' in line.lower():
                            action = "sleep"
                        elif 'buy' in line.lower():
                            action = "buy"
                        elif 'sell' in line.lower():
                            action = "sell"
                        elif 'eat' in line.lower():
                            action = "eat"
                        elif 'idle' in line.lower():
                            action = "idle"
                
                return {"action": action, "reason": reason, "command": action}
        except Exception as e:
            print(f"[AI Agent] ✗ 解析决策失败: {e}")
            return {"action": "idle", "reason": f"Parse error: {str(e)}", "command": "idle"}
    
    def make_decision_and_act(self):
        """做出决策并执行行动"""
        # 收集上下文信息
        context = {
            'villager': self.get_villager_status() or {},
            'time': self.get_current_time(),
            'action_status': self.get_action_status() or {},
            'prices': self.get_merchant_prices() or {},
            'messages': self.get_messages(),
            'trades_received': self.get_trades_received(),
            'trades_sent': self.get_trades_sent(),
            'villagers': self.get_online_villagers()
        }
        
        # 清理旧的交易请求记录
        self.clear_old_trade_requests()
        
        # 分析P2P交易机会
        context['p2p_opportunities'] = self.analyze_p2p_opportunities(context)
        
        # 检查是否已经提交了行动
        villager = context['villager']
        has_submitted = villager.get('has_submitted_action', False)
        
        # 生成决策
        print(f"[AI Agent] {self.villager_name} 正在思考...")
        decision = self.generate_decision(context)
        
        action = decision.get('action', 'idle')
        reason = decision.get('reason', 'No reason provided')
        command = decision.get('command', action)
        
        print(f"[AI Agent] {self.villager_name} 思考: {reason}")
        print(f"[AI Agent] {self.villager_name} 行动: {command}")
        print(f"[AI Agent] 决策详情: {decision}")
        
        # 如果已经提交了行动，限制可执行的行动类型
        if has_submitted:
            print(f"[AI Agent] {self.villager_name} 已经提交了行动，只能执行非推进时间的行动...")
            
            # 定义不允许的行动（这些会推进时间）
            forbidden_actions = ['produce', 'sleep', 'idle', 'buy', 'sell']
            
            if action in forbidden_actions:
                print(f"[AI Agent] ⚠️ 已提交行动，不能执行 {action}，改为处理消息和交易")
                
                # 检查是否有待处理的交易请求
                trades_received = context.get('trades_received', [])
                if trades_received:
                    print(f"[AI Agent] {self.villager_name} 发现 {len(trades_received)} 个待处理的交易请求")
                    self._handle_pending_trades(trades_received, context)
                
                # 检查是否有新消息
                messages = context.get('messages', [])
                unread_messages = [msg for msg in messages if not msg.get('read', False)]
                if unread_messages:
                    print(f"[AI Agent] {self.villager_name} 发现 {len(unread_messages)} 条未读消息")
                    # 标记消息为已读
                    for msg in unread_messages:
                        try:
                            requests.post(f"{self.villager_url}/messages/mark_read",
                                       json={'message_id': msg.get('id')}, timeout=5)
                        except:
                            pass
                
                print(f"[AI Agent] {self.villager_name} 已完成消息和交易处理，等待时间推进...")
                return
            
            # 如果行动是允许的（如eat, trades, mytrades, trade, send等），继续执行
            print(f"[AI Agent] {self.villager_name} 执行允许的行动: {action}")
        
        # 执行行动
        success = False
        error_message = None
        
        if action == "buy":
            success = self.execute_action("buy", 
                                        item=decision.get('item', 'seed'), 
                                        quantity=decision.get('quantity', 1))
            # 购买不消耗行动点，但也不自动生产
            # 让AI在下一轮决策中决定是否生产
        elif action == "sell":
            success = self.execute_action("sell", 
                                        item=decision.get('item', 'wheat'), 
                                        quantity=decision.get('quantity', 1))
        elif action == "produce":
            success = self.execute_action("produce")
        elif action == "sleep":
            success = self.execute_action("sleep")
            if not success:
                error_message = "Sleep failed: You need a house to sleep! Build a house first or buy one from other villagers."
        elif action == "idle":
            success = self.execute_action("idle")
        elif action == "eat":
            success = self.execute_action("eat")
        elif action == "price":
            success = self.execute_action("price")
            if success:
                # 获取价格信息并记录
                prices = self.get_merchant_prices()
                if prices and self.decision_history:
                    last_decision = self.decision_history[-1]
                    last_decision['decision']['prices'] = prices
        elif action == "trades":
            success = self.execute_action("trades")
            if success:
                # 获取交易信息并记录
                trades = self.get_trades_received()
                if trades and self.decision_history:
                    last_decision = self.decision_history[-1]
                    last_decision['decision']['trades'] = trades
        elif action == "mytrades":
            success = self.execute_action("mytrades")
            if success:
                # 获取发送交易信息并记录
                trades = self.get_trades_sent()
                if trades and self.decision_history:
                    last_decision = self.decision_history[-1]
                    last_decision['decision']['mytrades'] = trades
        elif action == "trade":
            success = self.execute_action("trade",
                                        target=decision.get('target'),
                                        trade_action=decision.get('trade_action', 'buy'),
                                        item=decision.get('item'),
                                        quantity=decision.get('quantity'),
                                        price=decision.get('price'))
        elif action == "send":
            success = self.execute_action("send_message",
                                        target=decision.get('target', 'all'),
                                        content=decision.get('content', 'Hello!'),
                                        type='private')
        elif action == "accept":
            trade_id = decision.get('trade_id')
            if trade_id:
                success = self.execute_action("accept_trade", trade_id=trade_id)
            else:
                error_message = "Accept trade failed: No trade ID provided"
        elif action == "reject":
            trade_id = decision.get('trade_id')
            if trade_id:
                success = self.execute_action("reject_trade", trade_id=trade_id)
            else:
                error_message = "Reject trade failed: No trade ID provided"
        elif action == "confirm":
            trade_id = decision.get('trade_id')
            if trade_id:
                success = self.execute_action("confirm_trade", trade_id=trade_id)
            else:
                error_message = "Confirm trade failed: No trade ID provided"
        else:
            print(f"[AI Agent] ✗ 未知行动: {action}")
            success = False
            error_message = f"Unknown action: {action}"
        
        if success:
            print(f"[AI Agent] ✓ {self.villager_name} 成功执行: {action}")
        else:
            print(f"[AI Agent] ✗ {self.villager_name} 执行失败: {action}")
            if error_message:
                print(f"[AI Agent] 错误信息: {error_message}")
        
        # 更新决策历史，记录执行结果
        if self.decision_history:
            last_decision = self.decision_history[-1]
            last_decision['decision']['success'] = success
            if error_message:
                last_decision['decision']['error_message'] = error_message
        
        return success
    
    def start_auto_decision_loop(self, interval: int = 30):
        """启动自动决策循环"""
        if self.running:
            print("[AI Agent] 自动决策循环已在运行")
            return
        
        self.running = True
        self.decision_thread = threading.Thread(target=self._decision_loop, args=(interval,), daemon=True)
        self.decision_thread.start()
        print(f"[AI Agent] 启动自动决策循环，间隔 {interval} 秒")
    
    def stop_auto_decision_loop(self):
        """停止自动决策循环"""
        self.running = False
        if self.decision_thread:
            self.decision_thread.join()
        print("[AI Agent] 自动决策循环已停止")
    
    def _decision_loop(self, interval: int):
        """决策循环"""
        while self.running:
            try:
                self.make_decision_and_act()
                time.sleep(interval)
            except Exception as e:
                print(f"[AI Agent] 决策循环异常: {e}")
                time.sleep(interval)
    
    def run_interactive_mode(self):
        """运行交互模式"""
        print(f"[AI Agent] 启动交互模式")
        
        # 检查连接
        if not self.check_connection():
            print("[AI Agent] ✗ 无法连接到村民节点")
            return
        
        # 检查村民是否已创建
        villager_status = self.get_villager_status()
        if not villager_status:
            print("[AI Agent] 村民未创建，请先创建村民")
            name = input("村民名字: ").strip()
            occupation = input("职业 (farmer/chef/carpenter): ").strip()
            gender = input("性别 (male/female): ").strip()
            personality = input("性格: ").strip()
            
            if not self.create_villager(name, occupation, gender, personality):
                print("[AI Agent] ✗ 村民创建失败")
                return
        
        print(f"[AI Agent] ✓ 村民 {self.villager_name} 准备就绪")
        print("[AI Agent] 输入命令:")
        print("  auto <间隔秒数> - 启动自动决策")
        print("  decision - 手动决策一次")
        print("  status - 查看状态")
        print("  history - 查看决策历史")
        print("  quit - 退出")
        
        while True:
            try:
                cmd = input(f"\n[AI Agent {self.villager_name}] > ").strip().lower()
                
                if cmd == "quit":
                    self.stop_auto_decision_loop()
                    break
                elif cmd.startswith("auto"):
                    parts = cmd.split()
                    interval = int(parts[1]) if len(parts) > 1 else 30
                    self.start_auto_decision_loop(interval)
                elif cmd == "decision":
                    self.make_decision_and_act()
                elif cmd == "status":
                    self._show_status()
                elif cmd == "history":
                    self._show_history()
                else:
                    print("未知命令")
            except KeyboardInterrupt:
                print("\n[AI Agent] 退出中...")
                self.stop_auto_decision_loop()
                break
            except Exception as e:
                print(f"[AI Agent] 错误: {e}")
    
    def _show_status(self):
        """显示状态"""
        context = {
            'villager': self.get_villager_status() or {},
            'time': self.get_current_time(),
            'action_status': self.get_action_status() or {},
            'prices': self.get_merchant_prices() or {},
            'messages': self.get_messages(),
            'villagers': self.get_online_villagers()
        }
        
        print(f"\n当前状态:")
        print(f"时间: {context['time']}")
        print(f"村民: {context['villager'].get('name', 'Unknown')}")
        print(f"体力: {context['villager'].get('stamina', 0)}/{context['villager'].get('max_stamina', 100)}")
        print(f"货币: {context['villager'].get('inventory', {}).get('money', 0)}")
        print(f"物品: {context['villager'].get('inventory', {}).get('items', {})}")
        print(f"已提交行动: {context['villager'].get('has_submitted_action', False)}")
        print(f"消息数: {len(context['messages'])}")
        print(f"在线村民: {len(context['villagers'])}")
    
    def _show_history(self):
        """显示决策历史"""
        if not self.decision_history:
            print("没有决策历史")
            return
        
        print(f"\n决策历史 (最近 {min(5, len(self.decision_history))} 条):")
        for i, record in enumerate(self.decision_history[-5:]):
            print(f"{i+1}. {record['timestamp']}")
            print(f"   行动: {record['decision'].get('action', 'unknown')}")
            print(f"   理由: {record['decision'].get('reason', 'No reason')[:100]}...")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AI村民代理')
    parser.add_argument('--port', type=int, required=True, help='村民节点端口号')
    parser.add_argument('--coordinator', type=int, default=5000, help='协调器端口')
    parser.add_argument('--merchant', type=int, default=5001, help='商人端口')
    parser.add_argument('--api-key', type=str, help='OpenAI API Key')
    parser.add_argument('--model', type=str, default='gpt-4o', help='GPT模型')
    parser.add_argument('--react', action='store_true', help='使用ReAct推理模式')
    parser.add_argument('--auto', type=int, help='自动模式间隔秒数')
    args = parser.parse_args()
    
    # 使用提供的API Key或环境变量
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("错误: 未提供OpenAI API Key")
        print("请使用 --api-key 参数或设置 OPENAI_API_KEY 环境变量")
        sys.exit(1)
    
    agent = AIVillagerAgent(
        villager_port=args.port,
        coordinator_port=args.coordinator,
        merchant_port=args.merchant,
        api_key=api_key,
        model=args.model,
        use_react=args.react
    )
    
    agent.run_interactive_mode()


if __name__ == '__main__':
    main()
