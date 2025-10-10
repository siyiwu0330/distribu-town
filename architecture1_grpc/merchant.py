"""
商人节点 - Architecture 1 (gRPC)
提供固定价格的物品买卖服务
"""

import grpc
from concurrent import futures
import sys
import os
import time

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))
from proto import town_pb2
from proto import town_pb2_grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.models import MERCHANT_PRICES


class MerchantNodeService(town_pb2_grpc.MerchantNodeServicer):
    """商人节点服务"""
    
    def __init__(self, node_id="merchant"):
        self.node_id = node_id
        self.prices = MERCHANT_PRICES
        # 中心化交易管理
        self.trade_counter = 0
        self.active_trades = {}  # trade_id -> trade_data
        print(f"[Merchant] 商人 '{node_id}' 初始化完成")
        print(f"[Merchant] 出售价格: {self.prices['buy']}")
        print(f"[Merchant] 收购价格: {self.prices['sell']}")
    
    def BuyItem(self, request, context):
        """玩家从商人处购买物品"""
        buyer_id = request.buyer_id
        item = request.item
        quantity = request.quantity
        
        # 检查商人是否出售该物品
        if item not in self.prices['buy']:
            return town_pb2.Status(
                success=False,
                message=f"商人不出售 {item}"
            )
        
        price = self.prices['buy'][item]
        total_cost = price * quantity
        
        print(f"[Merchant] {buyer_id} 购买 {quantity}x {item}, 总价: {total_cost}")
        
        return town_pb2.Status(
            success=True,
            message=f"出售 {quantity}x {item} 给 {buyer_id}, 收入 {total_cost}"
        )
    
    def SellItem(self, request, context):
        """玩家向商人出售物品"""
        seller_id = request.seller_id
        item = request.item
        quantity = request.quantity
        
        # 检查商人是否收购该物品
        if item not in self.prices['sell']:
            return town_pb2.Status(
                success=False,
                message=f"商人不收购 {item}"
            )
        
        price = self.prices['sell'][item]
        total_income = price * quantity
        
        print(f"[Merchant] 从 {seller_id} 收购 {quantity}x {item}, 支付: {total_income}")
        
        return town_pb2.Status(
            success=True,
            message=f"收购 {quantity}x {item} 从 {seller_id}, 支付 {total_income}"
        )
    
    def GetPrices(self, request, context):
        """获取价格表"""
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
        """时间推进通知"""
        new_time = request.new_time
        print(f"[Merchant] 时间推进: Day {new_time.day} {new_time.time_of_day}")
        
        return town_pb2.Status(success=True, message="Time updated")
    
    # ==================== 中心化交易系统 ====================
    
    def CreateTrade(self, request, context):
        """创建交易（由发起方调用）"""
        self.trade_counter += 1
        trade_id = f"trade_{self.trade_counter}"
        
        # 创建交易记录
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
        
        print(f"[Merchant-Trade] 创建交易 {trade_id}: {request.initiator_id} -> {request.target_id}")
        print(f"  类型: {request.offer_type}, 物品: {request.item}x{request.quantity}, 价格: {request.price}")
        
        return town_pb2.CreateTradeResponse(
            success=True,
            message=f"交易创建成功",
            trade_id=trade_id
        )
    
    def ListTrades(self, request, context):
        """列出交易"""
        node_id = request.node_id
        trade_type = request.type
        
        trades = []
        for trade_id, trade_data in self.active_trades.items():
            # 根据类型筛选
            if trade_type == 'pending':
                # 待处理的交易（我是target且status为pending）
                if trade_data['target_id'] == node_id and trade_data['status'] == 'pending':
                    trades.append(self._convert_trade_to_proto(trade_data))
            elif trade_type == 'sent':
                # 我发起的交易（我是initiator）
                if trade_data['initiator_id'] == node_id:
                    trades.append(self._convert_trade_to_proto(trade_data))
            elif trade_type == 'received':
                # 我收到的交易（我是target）
                if trade_data['target_id'] == node_id:
                    trades.append(self._convert_trade_to_proto(trade_data))
            elif trade_type == 'all':
                # 所有相关交易
                if trade_data['initiator_id'] == node_id or trade_data['target_id'] == node_id:
                    trades.append(self._convert_trade_to_proto(trade_data))
        
        return town_pb2.ListTradesResponse(trades=trades)
    
    def AcceptTrade(self, request, context):
        """接受交易"""
        trade_id = request.trade_id
        node_id = request.node_id
        
        if trade_id not in self.active_trades:
            return town_pb2.Status(success=False, message="交易不存在")
        
        trade = self.active_trades[trade_id]
        
        # 检查是否是目标方
        if trade['target_id'] != node_id:
            return town_pb2.Status(success=False, message="只有交易目标方可以接受")
        
        # 检查状态
        if trade['status'] != 'pending':
            return town_pb2.Status(success=False, message=f"交易状态错误: {trade['status']}")
        
        # 检查目标方资源
        try:
            channel = grpc.insecure_channel(trade['target_address'])
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            info = stub.GetInfo(town_pb2.Empty())
            
            if trade['offer_type'] == 'buy':
                # 发起方想买，目标方需要有物品
                if info.inventory.items.get(trade['item'], 0) < trade['quantity']:
                    channel.close()
                    return town_pb2.Status(success=False, message=f"你没有足够的 {trade['item']}")
            elif trade['offer_type'] == 'sell':
                # 发起方想卖，目标方需要有钱
                if info.inventory.money < trade['price']:
                    channel.close()
                    return town_pb2.Status(success=False, message=f"你没有足够的货币")
            
            channel.close()
        except Exception as e:
            return town_pb2.Status(success=False, message=f"检查资源失败: {str(e)}")
        
        # 更新状态
        trade['status'] = 'accepted'
        
        print(f"[Merchant-Trade] 交易 {trade_id} 被接受")
        
        return town_pb2.Status(success=True, message="交易已接受，等待双方确认")
    
    def ConfirmTrade(self, request, context):
        """确认交易"""
        trade_id = request.trade_id
        node_id = request.node_id
        
        if trade_id not in self.active_trades:
            return town_pb2.Status(success=False, message="交易不存在")
        
        trade = self.active_trades[trade_id]
        
        # 检查状态
        if trade['status'] != 'accepted':
            return town_pb2.Status(success=False, message=f"交易状态错误: {trade['status']}")
        
        # 标记确认
        if trade['initiator_id'] == node_id:
            trade['initiator_confirmed'] = True
            print(f"[Merchant-Trade] {node_id} (发起方) 确认交易 {trade_id}")
        elif trade['target_id'] == node_id:
            trade['target_confirmed'] = True
            print(f"[Merchant-Trade] {node_id} (目标方) 确认交易 {trade_id}")
        else:
            return town_pb2.Status(success=False, message="你不是此交易的参与方")
        
        # 如果双方都确认了，执行交易
        if trade['initiator_confirmed'] and trade['target_confirmed']:
            print(f"[Merchant-Trade] 双方已确认，执行交易 {trade_id}")
            result = self._execute_trade(trade)
            if result['success']:
                # 删除交易记录
                del self.active_trades[trade_id]
                return town_pb2.Status(success=True, message="交易完成")
            else:
                # 回滚确认状态
                trade['initiator_confirmed'] = False
                trade['target_confirmed'] = False
                trade['status'] = 'accepted'
                return town_pb2.Status(success=False, message=f"交易执行失败: {result['message']}")
        
        return town_pb2.Status(success=True, message="确认成功，等待对方确认")
    
    def CancelTrade(self, request, context):
        """取消交易"""
        trade_id = request.trade_id
        node_id = request.node_id
        
        if trade_id not in self.active_trades:
            return town_pb2.Status(success=False, message="交易不存在")
        
        trade = self.active_trades[trade_id]
        
        # 只有发起方可以取消
        if trade['initiator_id'] != node_id:
            return town_pb2.Status(success=False, message="只有发起方可以取消交易")
        
        # 只有pending状态可以取消
        if trade['status'] != 'pending':
            return town_pb2.Status(success=False, message=f"无法取消 {trade['status']} 状态的交易")
        
        del self.active_trades[trade_id]
        print(f"[Merchant-Trade] 交易 {trade_id} 已被取消")
        
        return town_pb2.Status(success=True, message="交易已取消")
    
    def RejectTrade(self, request, context):
        """拒绝交易"""
        trade_id = request.trade_id
        node_id = request.node_id
        
        if trade_id not in self.active_trades:
            return town_pb2.Status(success=False, message="交易不存在")
        
        trade = self.active_trades[trade_id]
        
        # 只有目标方可以拒绝
        if trade['target_id'] != node_id:
            return town_pb2.Status(success=False, message="只有目标方可以拒绝交易")
        
        # 只有pending状态可以拒绝
        if trade['status'] != 'pending':
            return town_pb2.Status(success=False, message=f"无法拒绝 {trade['status']} 状态的交易")
        
        trade['status'] = 'rejected'
        print(f"[Merchant-Trade] 交易 {trade_id} 已被拒绝")
        
        return town_pb2.Status(success=True, message="交易已拒绝")
    
    def _execute_trade(self, trade):
        """执行交易的原子操作"""
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
            
            print(f"[Merchant-Trade] 执行交易: {buyer_id} 买 {quantity}x{item} from {seller_id}, 价格 {price}")
            
            # Step 1: 买方支付
            channel = grpc.insecure_channel(buyer_addr)
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.TradeExecute(town_pb2.TradeExecuteRequest(
                action='pay',
                money=price
            ))
            channel.close()
            
            if not response.success:
                return {'success': False, 'message': f"买方支付失败: {response.message}"}
            
            # Step 2: 卖方移除物品
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
                return {'success': False, 'message': f"卖方移除物品失败: {response.message}"}
            channel.close()
            
            # Step 3: 买方添加物品
            channel = grpc.insecure_channel(buyer_addr)
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.TradeExecute(town_pb2.TradeExecuteRequest(
                action='add_item',
                item=item,
                quantity=quantity
            ))
            
            if not response.success:
                # 回滚: 卖方添加物品，买方退款
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
                return {'success': False, 'message': f"买方添加物品失败: {response.message}"}
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
                print(f"[Merchant-Trade] 警告: 卖方收款失败，但交易已执行")
            
            print(f"[Merchant-Trade] 交易 {trade_id} 执行成功")
            return {'success': True, 'message': '交易完成'}
            
        except Exception as e:
            return {'success': False, 'message': f'执行失败: {str(e)}'}
    
    def _convert_trade_to_proto(self, trade_data):
        """将交易数据转换为proto消息"""
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
    """启动商人服务器"""
    node_id = "merchant"
    
    # 启动gRPC服务器
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    town_pb2_grpc.add_MerchantNodeServicer_to_server(
        MerchantNodeService(node_id), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"[Merchant] 商人节点启动在端口 {port}")
    
    # 注册到协调器
    try:
        channel = grpc.insecure_channel(coordinator_addr)
        stub = town_pb2_grpc.TimeCoordinatorStub(channel)
        
        response = stub.RegisterNode(town_pb2.RegisterNodeRequest(
            node_id=node_id,
            node_type='merchant',
            address=f'localhost:{port}'
        ))
        
        if response.success:
            print(f"[Merchant] 成功注册到协调器: {coordinator_addr}")
        else:
            print(f"[Merchant] 注册失败: {response.message}")
        
        channel.close()
    except Exception as e:
        print(f"[Merchant] 无法连接到协调器 {coordinator_addr}: {e}")
    
    print("[Merchant] 使用 Ctrl+C 停止服务器")
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print("\n[Merchant] 关闭服务器...")
        server.stop(0)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='商人节点服务')
    parser.add_argument('--port', type=int, default=50052, help='监听端口')
    parser.add_argument('--coordinator', type=str, default='localhost:50051', 
                       help='协调器地址')
    args = parser.parse_args()
    
    serve(args.port, args.coordinator)

