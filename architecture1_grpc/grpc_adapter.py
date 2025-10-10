"""
gRPC适配层 - 将gRPC调用包装成类似REST API的接口
使得REST版本的AI Agent代码可以无缝运行在gRPC架构上
"""

import grpc
import sys
import os
import json
import time
from typing import Dict, List, Optional, Any

sys.path.insert(0, os.path.dirname(__file__))
from proto import town_pb2
from proto import town_pb2_grpc


class GRPCAdapter:
    """gRPC API适配器，提供类似REST的接口"""
    
    def __init__(self, villager_port: int, coordinator_port: int = 50051, merchant_port: int = 50052):
        self.villager_address = f"localhost:{villager_port}"
        self.coordinator_address = f"localhost:{coordinator_port}"
        self.merchant_address = f"localhost:{merchant_port}"
    
    def _get_villager_stub(self):
        channel = grpc.insecure_channel(self.villager_address)
        return channel, town_pb2_grpc.VillagerNodeStub(channel)
    
    def _get_coordinator_stub(self):
        channel = grpc.insecure_channel(self.coordinator_address)
        return channel, town_pb2_grpc.TimeCoordinatorStub(channel)
    
    def _get_merchant_stub(self):
        channel = grpc.insecure_channel(self.merchant_address)
        return channel, town_pb2_grpc.MerchantNodeStub(channel)
    
    # ========== 连接检查 ==========
    
    def check_villager_connection(self) -> bool:
        """检查村民节点连接"""
        try:
            channel, stub = self._get_villager_stub()
            stub.GetInfo(town_pb2.Empty())
            channel.close()
            return True
        except:
            return False
    
    # ========== 村民状态 ==========
    
    def get_villager_status(self) -> Dict:
        """获取村民状态"""
        try:
            channel, stub = self._get_villager_stub()
            info = stub.GetInfo(town_pb2.Empty())
            channel.close()
            
            return {
                'name': info.name,
                'occupation': info.occupation,
                'gender': info.gender,
                'personality': info.personality,
                'stamina': info.stamina,
                'max_stamina': info.max_stamina,
                'inventory': {
                    'money': info.inventory.money,
                    'items': dict(info.inventory.items)
                },
                'has_submitted_action': False,  # gRPC版本暂时不支持
                'action_points': info.action_points
            }
        except Exception as e:
            print(f"[gRPC Adapter] 获取村民状态失败: {e}")
            return {}
    
    def create_villager(self, name: str, occupation: str, gender: str, personality: str) -> bool:
        """创建村民"""
        try:
            channel, stub = self._get_villager_stub()
            response = stub.CreateVillager(town_pb2.CreateVillagerRequest(
                name=name,
                occupation=occupation,
                gender=gender,
                personality=personality
            ))
            channel.close()
            return response.success
        except Exception as e:
            print(f"[gRPC Adapter] 创建村民失败: {e}")
            return False
    
    # ========== 时间系统 ==========
    
    def get_current_time(self) -> str:
        """获取当前时间"""
        try:
            channel, stub = self._get_coordinator_stub()
            response = stub.GetTime(town_pb2.Empty())
            channel.close()
            return f"Day {response.day} - {response.time_of_day}"
        except Exception as e:
            print(f"[gRPC Adapter] 获取时间失败: {e}")
            return "Unknown"
    
    def get_action_status(self) -> Dict:
        """获取行动提交状态"""
        # gRPC版本暂时不支持行动提交状态
        return {
            'has_submitted_action': False,
            'submitted_action': None,
            'submitted_at': None
        }
    
    # ========== 商人系统 ==========
    
    def get_merchant_prices(self) -> Dict:
        """获取商人价格"""
        try:
            channel, stub = self._get_merchant_stub()
            response = stub.GetPrices(town_pb2.Empty())
            channel.close()
            
            buy_prices = {}
            sell_prices = {}
            
            for price_info in response.buy_prices:
                buy_prices[price_info.item] = price_info.price
            
            for price_info in response.sell_prices:
                sell_prices[price_info.item] = price_info.price
            
            return {
                'buy_prices': buy_prices,
                'sell_prices': sell_prices
            }
        except Exception as e:
            print(f"[gRPC Adapter] 获取商人价格失败: {e}")
            return {'buy_prices': {}, 'sell_prices': {}}
    
    def buy_from_merchant(self, item: str, quantity: int) -> bool:
        """从商人购买"""
        try:
            channel, stub = self._get_villager_stub()
            response = stub.Buy(town_pb2.BuyRequest(
                item=item,
                quantity=quantity
            ))
            channel.close()
            return response.success
        except Exception as e:
            print(f"[gRPC Adapter] 购买失败: {e}")
            return False
    
    def sell_to_merchant(self, item: str, quantity: int) -> bool:
        """向商人出售"""
        try:
            channel, stub = self._get_villager_stub()
            response = stub.Sell(town_pb2.SellRequest(
                item=item,
                quantity=quantity
            ))
            channel.close()
            return response.success
        except Exception as e:
            print(f"[gRPC Adapter] 出售失败: {e}")
            return False
    
    # ========== 村民系统 ==========
    
    def get_online_villagers(self) -> List[Dict]:
        """获取在线村民"""
        try:
            channel, stub = self._get_coordinator_stub()
            response = stub.ListNodes(town_pb2.Empty())
            channel.close()
            
            villagers = []
            for node in response.nodes:
                if node.node_type == 'villager':
                    villagers.append({
                        'node_id': node.node_id,
                        'name': node.node_id,  # gRPC版本暂时没有名字
                        'has_submitted_action': False  # gRPC版本暂时不支持
                    })
            return villagers
        except Exception as e:
            print(f"[gRPC Adapter] 获取在线村民失败: {e}")
            return []
    
    # ========== 消息系统 ==========
    
    def get_messages(self) -> List[Dict]:
        """获取消息"""
        try:
            channel, stub = self._get_villager_stub()
            response = stub.GetMessages(town_pb2.GetMessagesRequest(
                node_id=self.node_id
            ))
            channel.close()
            
            messages = []
            for msg in response.messages:
                messages.append({
                    'message_id': msg.message_id,
                    'from': msg.from_,
                    'to': msg.to,
                    'content': msg.content,
                    'type': msg.type,
                    'timestamp': msg.timestamp,
                    'is_read': msg.is_read
                })
            return messages
        except Exception as e:
            print(f"[gRPC Adapter] 获取消息失败: {e}")
            return []
    
    def send_message(self, target: str, content: str) -> bool:
        """发送消息"""
        try:
            channel, stub = self._get_villager_stub()
            response = stub.SendMessage(town_pb2.SendMessageRequest(
                target=target,
                content=content,
                type='private'
            ))
            channel.close()
            return response.success
        except Exception as e:
            print(f"[gRPC Adapter] 发送消息失败: {e}")
            return False
    
    # ========== 交易系统 ==========
    
    def get_trades_received(self) -> List[Dict]:
        """获取收到的交易请求"""
        try:
            # 获取当前村民的node_id
            villager_status = self.get_villager_status()
            if not villager_status:
                return []
            
            # 这里需要从某个地方获取node_id，暂时使用端口号
            node_id = f"node{self.villager_address.split(':')[-1]}"
            
            channel, stub = self._get_merchant_stub()
            response = stub.ListTrades(town_pb2.ListTradesRequest(
                node_id=node_id,
                type='received'
            ))
            channel.close()
            
            trades = []
            for trade in response.trades:
                trades.append({
                    'trade_id': trade.trade_id,
                    'from': trade.initiator_id,
                    'target_id': trade.target_id,
                    'offer_type': trade.offer_type,
                    'item': trade.item,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'status': trade.status,
                    'initiator_confirmed': trade.initiator_confirmed,
                    'target_confirmed': trade.target_confirmed
                })
            return trades
        except Exception as e:
            print(f"[gRPC Adapter] 获取收到交易失败: {e}")
            return []
    
    def get_trades_sent(self) -> List[Dict]:
        """获取发送的交易请求"""
        try:
            # 获取当前村民的node_id
            node_id = f"node{self.villager_address.split(':')[-1]}"
            
            channel, stub = self._get_merchant_stub()
            response = stub.ListTrades(town_pb2.ListTradesRequest(
                node_id=node_id,
                type='sent'
            ))
            channel.close()
            
            trades = []
            for trade in response.trades:
                trades.append({
                    'trade_id': trade.trade_id,
                    'initiator_id': trade.initiator_id,
                    'target_id': trade.target_id,
                    'offer_type': trade.offer_type,
                    'item': trade.item,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'status': trade.status,
                    'initiator_confirmed': trade.initiator_confirmed,
                    'target_confirmed': trade.target_confirmed
                })
            return trades
        except Exception as e:
            print(f"[gRPC Adapter] 获取发送交易失败: {e}")
            return []
    
    def create_trade_request(self, target: str, offer_type: str, item: str, quantity: int, price: int) -> bool:
        """创建交易请求"""
        try:
            node_id = f"node{self.villager_address.split(':')[-1]}"
            
            channel, stub = self._get_merchant_stub()
            response = stub.CreateTrade(town_pb2.CreateTradeRequest(
                initiator_id=node_id,
                initiator_address=self.villager_address,
                target_id=target,
                target_address=f"localhost:{target.replace('node', '5005')}",  # 假设端口映射
                offer_type=offer_type,
                item=item,
                quantity=quantity,
                price=price
            ))
            channel.close()
            return response.success
        except Exception as e:
            print(f"[gRPC Adapter] 创建交易失败: {e}")
            return False
    
    def accept_trade_request(self, trade_id: str) -> bool:
        """接受交易请求"""
        try:
            node_id = f"node{self.villager_address.split(':')[-1]}"
            
            channel, stub = self._get_merchant_stub()
            response = stub.AcceptTrade(town_pb2.AcceptTradeRequest(
                trade_id=trade_id,
                node_id=node_id
            ))
            channel.close()
            return response.success
        except Exception as e:
            print(f"[gRPC Adapter] 接受交易失败: {e}")
            return False
    
    def reject_trade_request(self, trade_id: str) -> bool:
        """拒绝交易请求"""
        try:
            node_id = f"node{self.villager_address.split(':')[-1]}"
            
            channel, stub = self._get_merchant_stub()
            response = stub.RejectTrade(town_pb2.RejectTradeRequest(
                trade_id=trade_id,
                node_id=node_id
            ))
            channel.close()
            return response.success
        except Exception as e:
            print(f"[gRPC Adapter] 拒绝交易失败: {e}")
            return False
    
    def confirm_trade_request(self, trade_id: str) -> bool:
        """确认交易请求"""
        try:
            node_id = f"node{self.villager_address.split(':')[-1]}"
            
            channel, stub = self._get_merchant_stub()
            response = stub.ConfirmTrade(town_pb2.ConfirmTradeRequest(
                trade_id=trade_id,
                node_id=node_id
            ))
            channel.close()
            return response.success
        except Exception as e:
            print(f"[gRPC Adapter] 确认交易失败: {e}")
            return False
    
    def cancel_trade_request(self, trade_id: str) -> bool:
        """取消交易请求"""
        try:
            node_id = f"node{self.villager_address.split(':')[-1]}"
            
            channel, stub = self._get_merchant_stub()
            response = stub.CancelTrade(town_pb2.CancelTradeRequest(
                trade_id=trade_id,
                node_id=node_id
            ))
            channel.close()
            return response.success
        except Exception as e:
            print(f"[gRPC Adapter] 取消交易失败: {e}")
            return False
    
    # ========== 行动系统 ==========
    
    def execute_action(self, action: str, **kwargs) -> bool:
        """执行行动"""
        try:
            channel, stub = self._get_villager_stub()
            
            if action == 'produce':
                response = stub.Produce(town_pb2.Empty())
            elif action == 'sleep':
                response = stub.Sleep(town_pb2.Empty())
            elif action == 'buy':
                item = kwargs.get('item', '')
                quantity = kwargs.get('quantity', 1)
                response = stub.Buy(town_pb2.BuyRequest(item=item, quantity=quantity))
            elif action == 'sell':
                item = kwargs.get('item', '')
                quantity = kwargs.get('quantity', 1)
                response = stub.Sell(town_pb2.SellRequest(item=item, quantity=quantity))
            elif action == 'idle':
                # gRPC版本不支持idle，返回成功
                return True
            else:
                print(f"[gRPC Adapter] 不支持的action: {action}")
                return False
            
            channel.close()
            return response.success
        except Exception as e:
            print(f"[gRPC Adapter] 执行行动失败: {e}")
            return False
    
    def submit_action(self, action: str, **kwargs) -> bool:
        """提交行动（gRPC版本直接执行）"""
        return self.execute_action(action, **kwargs)