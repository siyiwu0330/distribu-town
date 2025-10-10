"""
gRPC适配层 - 将gRPC调用包装成类似REST API的接口
使得REST版本的AI Agent代码可以无缝运行在gRPC架构上
"""

import grpc
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from proto import town_pb2
from proto import town_pb2_grpc


class GRPCAdapter:
    """gRPC API适配器，提供类似REST的接口"""
    
    def __init__(self, villager_address: str, coordinator_address: str, merchant_address: str):
        self.villager_address = villager_address
        self.coordinator_address = coordinator_address
        self.merchant_address = merchant_address
    
    def _get_villager_stub(self):
        channel = grpc.insecure_channel(self.villager_address)
        return channel, town_pb2_grpc.VillagerNodeStub(channel)
    
    def _get_coordinator_stub(self):
        channel = grpc.insecure_channel(self.coordinator_address)
        return channel, town_pb2_grpc.TimeCoordinatorStub(channel)
    
    def _get_merchant_stub(self):
        channel = grpc.insecure_channel(self.merchant_address)
        return channel, town_pb2_grpc.MerchantNodeStub(channel)
    
    # ========== Villager API适配 ==========
    
    def get_villager(self):
        """GET /villager"""
        try:
            channel, stub = self._get_villager_stub()
            info = stub.GetInfo(town_pb2.Empty())
            channel.close()
            
            return {
                'status_code': 200,
                'json': {
                    'name': info.name,
                    'occupation': info.occupation,
                    'gender': info.gender,
                    'personality': info.personality,
                    'stamina': info.stamina,
                    'max_stamina': info.max_stamina,
                    'has_slept': info.has_slept,
                    'inventory': {
                        'money': info.inventory.money,
                        'items': dict(info.inventory.items)
                    },
                    'has_submitted_action': False,  # gRPC版本没有action系统
                    'node_id': None  # 需要从coordinator获取
                }
            }
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.FAILED_PRECONDITION:
                return {'status_code': 400, 'json': {'message': 'Villager not initialized'}}
            return {'status_code': 500, 'json': {'message': str(e)}}
    
    def create_villager(self, data):
        """POST /villager"""
        try:
            channel, stub = self._get_villager_stub()
            response = stub.CreateVillager(town_pb2.CreateVillagerRequest(
                name=data['name'],
                occupation=data['occupation'],
                gender=data['gender'],
                personality=data['personality']
            ))
            channel.close()
            
            if response.success:
                return {'status_code': 200, 'json': {'message': response.message}}
            return {'status_code': 400, 'json': {'message': response.message}}
        except Exception as e:
            return {'status_code': 500, 'json': {'message': str(e)}}
    
    def produce(self):
        """POST /action/produce"""
        try:
            channel, stub = self._get_villager_stub()
            response = stub.Produce(town_pb2.ProduceRequest())
            channel.close()
            
            if response.success:
                return {'status_code': 200, 'json': {'success': True, 'message': response.message}}
            return {'status_code': 400, 'json': {'success': False, 'message': response.message}}
        except Exception as e:
            return {'status_code': 500, 'json': {'success': False, 'message': str(e)}}
    
    def sleep(self):
        """POST /action/sleep"""
        try:
            channel, stub = self._get_villager_stub()
            response = stub.Sleep(town_pb2.SleepRequest())
            channel.close()
            
            if response.success:
                return {'status_code': 200, 'json': {'success': True, 'message': response.message}}
            return {'status_code': 400, 'json': {'success': False, 'message': response.message}}
        except Exception as e:
            return {'status_code': 500, 'json': {'success': False, 'message': str(e)}}
    
    def trade_merchant(self, action, item, quantity):
        """POST /action/trade"""
        try:
            channel, stub = self._get_villager_stub()
            price = 0 if action == 'buy' else 1
            response = stub.Trade(town_pb2.TradeRequest(
                target_node='merchant',
                item=item,
                quantity=quantity,
                price=price
            ))
            channel.close()
            
            if response.success:
                return {'status_code': 200, 'json': {'success': True, 'message': response.message}}
            return {'status_code': 400, 'json': {'success': False, 'message': response.message}}
        except Exception as e:
            return {'status_code': 500, 'json': {'success': False, 'message': str(e)}}
    
    # ========== Coordinator API适配 ==========
    
    def get_time(self):
        """GET /time"""
        try:
            channel, stub = self._get_coordinator_stub()
            time_info = stub.GetCurrentTime(town_pb2.Empty())
            channel.close()
            
            return {
                'status_code': 200,
                'json': {
                    'day': time_info.day,
                    'time_of_day': time_info.time_of_day
                }
            }
        except Exception as e:
            return {'status_code': 500, 'json': {}}
    
    def get_nodes(self):
        """GET /nodes"""
        try:
            channel, stub = self._get_coordinator_stub()
            response = stub.ListNodes(town_pb2.Empty())
            channel.close()
            
            nodes = []
            for node in response.nodes:
                nodes.append({
                    'node_id': node.node_id,
                    'node_type': node.node_type,
                    'address': node.address
                })
            
            return {'status_code': 200, 'json': {'nodes': nodes}}
        except Exception as e:
            return {'status_code': 500, 'json': {'nodes': []}}
    
    # ========== Merchant API适配 ==========
    
    def get_prices(self):
        """GET /prices"""
        try:
            channel, stub = self._get_merchant_stub()
            prices = stub.GetPrices(town_pb2.Empty())
            channel.close()
            
            buy_prices = {p.item: p.price for p in prices.buy_prices}
            sell_prices = {p.item: p.price for p in prices.sell_prices}
            
            return {
                'status_code': 200,
                'json': {
                    'buy': buy_prices,
                    'sell': sell_prices
                }
            }
        except Exception as e:
            return {'status_code': 500, 'json': {'buy': {}, 'sell': {}}}
    
    def create_trade(self, data):
        """POST /trade/create"""
        try:
            channel, stub = self._get_merchant_stub()
            response = stub.CreateTrade(town_pb2.CreateTradeRequest(
                initiator_id=data['initiator_id'],
                initiator_address=data['initiator_address'],
                target_id=data['target_id'],
                target_address=data['target_address'],
                offer_type=data['offer_type'],
                item=data['item'],
                quantity=data['quantity'],
                price=data['price']
            ))
            channel.close()
            
            if response.success:
                return {'status_code': 200, 'json': {'success': True, 'trade_id': response.trade_id, 'message': response.message}}
            return {'status_code': 400, 'json': {'success': False, 'message': response.message}}
        except Exception as e:
            return {'status_code': 500, 'json': {'success': False, 'message': str(e)}}
    
    def list_trades(self, node_id, trade_type):
        """GET /trade/list"""
        try:
            channel, stub = self._get_merchant_stub()
            response = stub.ListTrades(town_pb2.ListTradesRequest(
                node_id=node_id,
                type=trade_type
            ))
            channel.close()
            
            trades = []
            for t in response.trades:
                trades.append({
                    'trade_id': t.trade_id,
                    'initiator_id': t.initiator_id,
                    'initiator_address': t.initiator_address,
                    'target_id': t.target_id,
                    'target_address': t.target_address,
                    'offer_type': t.offer_type,
                    'item': t.item,
                    'quantity': t.quantity,
                    'price': t.price,
                    'status': t.status,
                    'initiator_confirmed': t.initiator_confirmed,
                    'target_confirmed': t.target_confirmed
                })
            
            return {'status_code': 200, 'json': {'trades': trades}}
        except Exception as e:
            return {'status_code': 500, 'json': {'trades': []}}
    
    def accept_trade(self, trade_id, node_id):
        """POST /trade/accept"""
        try:
            channel, stub = self._get_merchant_stub()
            response = stub.AcceptTrade(town_pb2.AcceptTradeRequest(
                trade_id=trade_id,
                node_id=node_id
            ))
            channel.close()
            
            if response.success:
                return {'status_code': 200, 'json': {'success': True, 'message': response.message}}
            return {'status_code': 400, 'json': {'success': False, 'message': response.message}}
        except Exception as e:
            return {'status_code': 500, 'json': {'success': False, 'message': str(e)}}
    
    def confirm_trade(self, trade_id, node_id):
        """POST /trade/confirm"""
        try:
            channel, stub = self._get_merchant_stub()
            response = stub.ConfirmTrade(town_pb2.ConfirmTradeRequest(
                trade_id=trade_id,
                node_id=node_id
            ))
            channel.close()
            
            if response.success:
                return {'status_code': 200, 'json': {'success': True, 'message': response.message}}
            return {'status_code': 400, 'json': {'success': False, 'message': response.message}}
        except Exception as e:
            return {'status_code': 500, 'json': {'success': False, 'message': str(e)}}
    
    def cancel_trade(self, trade_id, node_id):
        """POST /trade/cancel"""
        try:
            channel, stub = self._get_merchant_stub()
            response = stub.CancelTrade(town_pb2.CancelTradeRequest(
                trade_id=trade_id,
                node_id=node_id
            ))
            channel.close()
            
            if response.success:
                return {'status_code': 200, 'json': {'success': True, 'message': response.message}}
            return {'status_code': 400, 'json': {'success': False, 'message': response.message}}
        except Exception as e:
            return {'status_code': 500, 'json': {'success': False, 'message': str(e)}}
    
    def reject_trade(self, trade_id, node_id):
        """POST /trade/reject"""
        try:
            channel, stub = self._get_merchant_stub()
            response = stub.RejectTrade(town_pb2.RejectTradeRequest(
                trade_id=trade_id,
                node_id=node_id
            ))
            channel.close()
            
            if response.success:
                return {'status_code': 200, 'json': {'success': True, 'message': response.message}}
            return {'status_code': 400, 'json': {'success': False, 'message': response.message}}
        except Exception as e:
            return {'status_code': 500, 'json': {'success': False, 'message': str(e)}}

