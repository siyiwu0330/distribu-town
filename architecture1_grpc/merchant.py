"""
MerchantNode - Architecture 1 (gRPC)
提供固定Price的Item买卖服务
"""

import grpc
from concurrent import futures
import sys
import os
import time

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))
import town_pb2
import town_pb2_grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.models import MERCHANT_PRICES


class MerchantNodeService(town_pb2_grpc.MerchantNodeServicer):
    """MerchantNode服务"""
    
    def __init__(self, node_id="merchant"):
        self.node_id = node_id
        self.prices = MERCHANT_PRICES
        # 中心化Trade管理
        self.trade_counter = 0
        self.active_trades = {}  # trade_id -> trade_data
        print(f"[Merchant] Merchant '{node_id}' Initialization complete")
        print(f"[Merchant] SellPrice: {self.prices['buy']}")
        print(f"[Merchant] 收购Price: {self.prices['sell']}")
    
    def BuyItem(self, request, context):
        """玩家从Merchant处BuyItem"""
        buyer_id = request.buyer_id
        item = request.item
        quantity = request.quantity
        
        # 检查Merchant是否Sell该Item
        if item not in self.prices['buy']:
            return town_pb2.Status(
                success=False,
                message=f"Merchant不Sell {item}"
            )
        
        price = self.prices['buy'][item]
        total_cost = price * quantity
        
        print(f"[Merchant] {buyer_id} Buy {quantity}x {item}, 总价: {total_cost}")
        
        return town_pb2.Status(
            success=True,
            message=f"Sell {quantity}x {item} 给 {buyer_id}, 收入 {total_cost}"
        )
    
    def SellItem(self, request, context):
        """玩家向MerchantSellItem"""
        seller_id = request.seller_id
        item = request.item
        quantity = request.quantity
        
        # 检查Merchant是否收购该Item
        if item not in self.prices['sell']:
            return town_pb2.Status(
                success=False,
                message=f"Merchant不收购 {item}"
            )
        
        price = self.prices['sell'][item]
        total_income = price * quantity
        
        print(f"[Merchant] 从 {seller_id} 收购 {quantity}x {item}, 支付: {total_income}")
        
        return town_pb2.Status(
            success=True,
            message=f"收购 {quantity}x {item} 从 {seller_id}, 支付 {total_income}"
        )
    
    def GetPrices(self, request, context):
        """获取Price表"""
        buy_prices = [
            town_pb2.PriceInfo(item=item, price=int(price))
            for item, price in self.prices['buy'].items()
        ]
        sell_prices = [
            town_pb2.PriceInfo(item=item, price=int(price))
            for item, price in self.prices['sell'].items()
        ]
        
        return town_pb2.PriceList(
            buy_prices=buy_prices,
            sell_prices=sell_prices
        )
    
    def OnTimeAdvance(self, request, context):
        """TimeAdvanceNotify"""
        new_time = request.new_time
        print(f"[Merchant] TimeAdvance: Day {new_time.day} {new_time.time_of_day}")
        
        return town_pb2.Status(success=True, message="Time updated")
    
    # ==================== 中心化Trade系统 ====================
    
    def CreateTrade(self, request, context):
        """CreateTrade（由发起方调用）"""
        self.trade_counter += 1
        trade_id = f"trade_{self.trade_counter}"
        
        # CreateTrade记录
        trade_data = {
            'trade_id': trade_id,
            'initiator_id': request.initiator_id,
            'initiator_address': request.initiator_address,
            'target_id': request.target_id,
            'target_address': request.target_address,
            'offer_type': request.offer_type,
            'item': request.item,
            'quantity': request.quantity,
            'price': request.price,
            'status': 'pending',
            'initiator_confirmed': False,
            'target_confirmed': False,
            'created_at': time.time()
        }
        
        self.active_trades[trade_id] = trade_data
        
        print(f"[Merchant-Trade] CreateTrade {trade_id}: {request.initiator_id} -> {request.target_id}")
        print(f"  类型: {request.offer_type}, Item: {request.item}x{request.quantity}, Price: {request.price}")
        
        return town_pb2.CreateTradeResponse(
            success=True,
            message=f"TradeCreateSuccess",
            trade_id=trade_id
        )
    
    def ListTrades(self, request, context):
        """列出Trade"""
        node_id = request.node_id
        trade_type = request.type
        
        trades = []
        for trade_id, trade_data in self.active_trades.items():
            # 根据类型筛选
            if trade_type == 'pending':
                # 待Handle的Trade（我是target且status为pending）
                if trade_data['target_id'] == node_id and trade_data['status'] == 'pending':
                    trades.append(self._convert_trade_to_proto(trade_data))
            elif trade_type == 'sent':
                # 我发起的Trade（我是initiator）
                if trade_data['initiator_id'] == node_id:
                    trades.append(self._convert_trade_to_proto(trade_data))
            elif trade_type == 'received':
                # 我收到的Trade（我是target）
                if trade_data['target_id'] == node_id:
                    trades.append(self._convert_trade_to_proto(trade_data))
            elif trade_type == 'all':
                # 所有相关Trade
                if trade_data['initiator_id'] == node_id or trade_data['target_id'] == node_id:
                    trades.append(self._convert_trade_to_proto(trade_data))
        
        return town_pb2.ListTradesResponse(trades=trades)
    
    def AcceptTrade(self, request, context):
        """AcceptTrade"""
        trade_id = request.trade_id
        node_id = request.node_id
        
        if trade_id not in self.active_trades:
            return town_pb2.Status(success=False, message="Trade不存在")
        
        trade = self.active_trades[trade_id]
        
        # 检查是否是目标方
        if trade['target_id'] != node_id:
            return town_pb2.Status(success=False, message="只有Trade目标方可以Accept")
        
        # 检查状态
        if trade['status'] != 'pending':
            return town_pb2.Status(success=False, message=f"Trade状态Error: {trade['status']}")
        
        # 检查目标方资源
        try:
            channel = grpc.insecure_channel(trade['target_address'])
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            info = stub.GetInfo(town_pb2.Empty())
            
            if trade['offer_type'] == 'buy':
                # 发起方想买，目标方需要有Item
                if info.inventory.items.get(trade['item'], 0) < trade['quantity']:
                    channel.close()
                    return town_pb2.Status(success=False, message=f"你没有足够的 {trade['item']}")
            elif trade['offer_type'] == 'sell':
                # 发起方想卖，目标方需要有钱
                if info.inventory.money < trade['price']:
                    channel.close()
                    return town_pb2.Status(success=False, message=f"你没有足够的Money")
            
            channel.close()
        except Exception as e:
            return town_pb2.Status(success=False, message=f"检查资源Failed: {str(e)}")
        
        # Update状态
        trade['status'] = 'accepted'
        
        print(f"[Merchant-Trade] Trade {trade_id} 被Accept")
        
        return town_pb2.Status(success=True, message="Trade已Accept，Waiting双方Confirm")
    
    def ConfirmTrade(self, request, context):
        """ConfirmTrade"""
        trade_id = request.trade_id
        node_id = request.node_id
        
        if trade_id not in self.active_trades:
            return town_pb2.Status(success=False, message="Trade不存在")
        
        trade = self.active_trades[trade_id]
        
        # 检查状态
        if trade['status'] != 'accepted':
            return town_pb2.Status(success=False, message=f"Trade状态Error: {trade['status']}")
        
        # 标记Confirm
        if trade['initiator_id'] == node_id:
            trade['initiator_confirmed'] = True
            print(f"[Merchant-Trade] {node_id} (发起方) ConfirmTrade {trade_id}")
        elif trade['target_id'] == node_id:
            trade['target_confirmed'] = True
            print(f"[Merchant-Trade] {node_id} (目标方) ConfirmTrade {trade_id}")
        else:
            return town_pb2.Status(success=False, message="你不是此Trade的参与方")
        
        # 如果双方都Confirm了，ExecuteTrade
        if trade['initiator_confirmed'] and trade['target_confirmed']:
            print(f"[Merchant-Trade] 双方已Confirm，ExecuteTrade {trade_id}")
            result = self._execute_trade(trade)
            if result['success']:
                # DeleteTrade记录
                del self.active_trades[trade_id]
                return town_pb2.Status(success=True, message="Trade完成")
            else:
                # 回滚Confirm状态
                trade['initiator_confirmed'] = False
                trade['target_confirmed'] = False
                trade['status'] = 'accepted'
                return town_pb2.Status(success=False, message=f"TradeExecuteFailed: {result['message']}")
        
        return town_pb2.Status(success=True, message="ConfirmSuccess，Waiting对方Confirm")
    
    def CancelTrade(self, request, context):
        """CancelTrade"""
        trade_id = request.trade_id
        node_id = request.node_id
        
        if trade_id not in self.active_trades:
            return town_pb2.Status(success=False, message="Trade不存在")
        
        trade = self.active_trades[trade_id]
        
        # 只有发起方可以Cancel
        if trade['initiator_id'] != node_id:
            return town_pb2.Status(success=False, message="只有发起方可以CancelTrade")
        
        # 只有pending状态可以Cancel
        if trade['status'] != 'pending':
            return town_pb2.Status(success=False, message=f"无法Cancel {trade['status']} 状态的Trade")
        
        del self.active_trades[trade_id]
        print(f"[Merchant-Trade] Trade {trade_id} 已被Cancel")
        
        return town_pb2.Status(success=True, message="Trade已Cancel")
    
    def RejectTrade(self, request, context):
        """RejectTrade"""
        trade_id = request.trade_id
        node_id = request.node_id
        
        if trade_id not in self.active_trades:
            return town_pb2.Status(success=False, message="Trade不存在")
        
        trade = self.active_trades[trade_id]
        
        # 只有目标方可以Reject
        if trade['target_id'] != node_id:
            return town_pb2.Status(success=False, message="只有目标方可以RejectTrade")
        
        # 只有pending状态可以Reject
        if trade['status'] != 'pending':
            return town_pb2.Status(success=False, message=f"无法Reject {trade['status']} 状态的Trade")
        
        trade['status'] = 'rejected'
        print(f"[Merchant-Trade] Trade {trade_id} 已被Reject")
        
        return town_pb2.Status(success=True, message="Trade已Reject")
    
    def _execute_trade(self, trade):
        """ExecuteTrade的原子操作"""
        trade_id = trade['trade_id']
        
        try:
            # 根据offer_type确定买卖双方
            if trade['offer_type'] == 'buy':
                # 发起方买，目标方卖
                buyer_id = trade['initiator_id']
                buyer_addr = trade['initiator_address']
                seller_id = trade['target_id']
                seller_addr = trade['target_address']
            else:  # sell
                # 发起方卖，目标方买
                seller_id = trade['initiator_id']
                seller_addr = trade['initiator_address']
                buyer_id = trade['target_id']
                buyer_addr = trade['target_address']
            
            item = trade['item']
            quantity = trade['quantity']
            price = trade['price']
            
            print(f"[Merchant-Trade] ExecuteTrade: {buyer_id} 买 {quantity}x{item} from {seller_id}, Price {price}")
            
            # Step 1: 买方支付
            channel = grpc.insecure_channel(buyer_addr)
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.TradeExecute(town_pb2.TradeExecuteRequest(
                action='pay',
                money=price
            ))
            channel.close()
            
            if not response.success:
                return {'success': False, 'message': f"买方支付Failed: {response.message}"}
            
            # Step 2: 卖方移除Item
            channel = grpc.insecure_channel(seller_addr)
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.TradeExecute(town_pb2.TradeExecuteRequest(
                action='remove_item',
                item=item,
                quantity=quantity
            ))
            
            if not response.success:
                # 回滚: 买方退款
                channel_buyer = grpc.insecure_channel(buyer_addr)
                stub_buyer = town_pb2_grpc.VillagerNodeStub(channel_buyer)
                stub_buyer.TradeExecute(town_pb2.TradeExecuteRequest(
                    action='refund',
                    money=price
                ))
                channel_buyer.close()
                channel.close()
                return {'success': False, 'message': f"卖方移除ItemFailed: {response.message}"}
            channel.close()
            
            # Step 3: 买方添加Item
            channel = grpc.insecure_channel(buyer_addr)
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.TradeExecute(town_pb2.TradeExecuteRequest(
                action='add_item',
                item=item,
                quantity=quantity
            ))
            
            if not response.success:
                # 回滚: 卖方添加Item，买方退款
                channel_seller = grpc.insecure_channel(seller_addr)
                stub_seller = town_pb2_grpc.VillagerNodeStub(channel_seller)
                stub_seller.TradeExecute(town_pb2.TradeExecuteRequest(
                    action='add_item',
                    item=item,
                    quantity=quantity
                ))
                channel_seller.close()
                
                channel_buyer = grpc.insecure_channel(buyer_addr)
                stub_buyer = town_pb2_grpc.VillagerNodeStub(channel_buyer)
                stub_buyer.TradeExecute(town_pb2.TradeExecuteRequest(
                    action='refund',
                    money=price
                ))
                channel_buyer.close()
                channel.close()
                return {'success': False, 'message': f"买方添加ItemFailed: {response.message}"}
            channel.close()
            
            # Step 4: 卖方收款
            channel = grpc.insecure_channel(seller_addr)
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.TradeExecute(town_pb2.TradeExecuteRequest(
                action='receive',
                money=price
            ))
            channel.close()
            
            if not response.success:
                print(f"[Merchant-Trade] Warning: 卖方收款Failed，但Trade已Execute")
            
            print(f"[Merchant-Trade] Trade {trade_id} ExecuteSuccess")
            return {'success': True, 'message': 'Trade完成'}
            
        except Exception as e:
            return {'success': False, 'message': f'ExecuteFailed: {str(e)}'}
    
    def _convert_trade_to_proto(self, trade_data):
        """将Trade数据转换为protoMessage"""
        return town_pb2.TradeInfo(
            trade_id=trade_data['trade_id'],
            initiator_id=trade_data['initiator_id'],
            initiator_address=trade_data['initiator_address'],
            target_id=trade_data['target_id'],
            target_address=trade_data['target_address'],
            offer_type=trade_data['offer_type'],
            item=trade_data['item'],
            quantity=trade_data['quantity'],
            price=trade_data['price'],
            status=trade_data['status'],
            initiator_confirmed=trade_data['initiator_confirmed'],
            target_confirmed=trade_data['target_confirmed']
        )


def serve(port=50052, coordinator_addr='localhost:50051'):
    """启动Merchant服务器"""
    node_id = "merchant"
    
    # 启动gRPC服务器
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    town_pb2_grpc.add_MerchantNodeServicer_to_server(
        MerchantNodeService(node_id), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"[Merchant] MerchantNodestarting on port {port}")
    
    # Register to coordinator
    try:
        channel = grpc.insecure_channel(coordinator_addr)
        stub = town_pb2_grpc.TimeCoordinatorStub(channel)
        
        response = stub.RegisterNode(town_pb2.RegisterNodeRequest(
            node_id=node_id,
            node_type='merchant',
            address=f'localhost:{port}'
        ))
        
        if response.success:
            print(f"[Merchant] SuccessRegister to coordinator: {coordinator_addr}")
        else:
            print(f"[Merchant] Registration failed: {response.message}")
        
        channel.close()
    except Exception as e:
        print(f"[Merchant] 无法Connecting toCoordinator {coordinator_addr}: {e}")
    
    print("[Merchant] 使用 Ctrl+C 停止服务器")
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print("\n[Merchant] 关闭服务器...")
        server.stop(0)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='MerchantNode服务')
    parser.add_argument('--port', type=int, default=50052, help='监听端口')
    parser.add_argument('--coordinator', type=str, default='localhost:50051', 
                       help='Coordinator地址')
    args = parser.parse_args()
    
    serve(args.port, args.coordinator)

