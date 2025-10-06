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
            town_pb2.PriceInfo(item=item, price=price)
            for item, price in self.prices['buy'].items()
        ]
        sell_prices = [
            town_pb2.PriceInfo(item=item, price=price)
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

