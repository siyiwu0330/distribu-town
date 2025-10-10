"""
交互式CLI - Architecture 1 (gRPC)
用于村民节点的交互式控制，支持中心化交易系统
"""

import grpc
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from proto import town_pb2
from proto import town_pb2_grpc


class InteractiveCLI:
    """交互式命令行界面"""
    
    def __init__(self, node_id, node_address, merchant_address='localhost:50052', coordinator_address='localhost:50051'):
        self.node_id = node_id
        self.node_address = node_address
        self.merchant_address = merchant_address
        self.coordinator_address = coordinator_address
        
        # 缓存其他节点信息
        self.nodes = {}  # {node_id: address}
        
        print(f"\n{'='*70}")
        print(f"  村民节点交互式CLI")
        print(f"{'='*70}")
        print(f"节点ID: {self.node_id}")
        print(f"节点地址: {self.node_address}")
        print(f"商人地址: {self.merchant_address}")
        print(f"{'='*70}\n")
    
    def refresh_nodes(self):
        """从协调器刷新节点列表"""
        try:
            channel = grpc.insecure_channel(self.coordinator_address)
            stub = town_pb2_grpc.TimeCoordinatorStub(channel)
            response = stub.ListNodes(town_pb2.Empty())
            
            self.nodes = {}
            for node in response.nodes:
                if node.node_type == 'villager':
                    self.nodes[node.node_id] = node.address
            
            channel.close()
            print(f"✓ 已刷新节点列表，找到 {len(self.nodes)} 个村民节点")
        except Exception as e:
            print(f"✗ 刷新节点列表失败: {e}")
    
    def show_help(self):
        """显示帮助信息"""
        print("\n" + "="*70)
        print("  可用命令")
        print("="*70)
        print("\n【基本操作】")
        print("  info              - 查看我的信息")
        print("  produce           - 执行生产")
        print("  sleep             - 睡眠")
        print("  time              - 查看当前时间")
        print("  advance           - 推进时间")
        print("")
        print("【商人交易】")
        print("  price             - 查看商人价格表")
        print("  buy <item> <qty>  - 从商人购买物品")
        print("  sell <item> <qty> - 向商人出售物品")
        print("")
        print("【村民交易】")
        print("  nodes             - 刷新并查看在线村民")
        print("  trade <node_id> <buy/sell> <item> <qty> <price>")
        print("                    - 向村民发起交易")
        print("  trades            - 查看待处理的交易请求")
        print("  mytrades          - 查看我发起的交易")
        print("  accept <trade_id> - 接受交易请求")
        print("  reject <trade_id> - 拒绝交易请求")
        print("  confirm <trade_id>- 确认交易")
        print("  cancel <trade_id> - 取消交易")
        print("")
        print("【其他】")
        print("  help              - 显示此帮助")
        print("  exit/quit         - 退出")
        print("="*70 + "\n")
    
    def get_my_info(self):
        """获取我的村民信息"""
        try:
            channel = grpc.insecure_channel(self.node_address)
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            info = stub.GetInfo(town_pb2.Empty())
            channel.close()
            
            print("\n" + "="*70)
            print(f"  {info.name} ({self.node_id})")
            print("="*70)
            print(f"职业: {info.occupation}")
            print(f"性别: {info.gender}")
            print(f"性格: {info.personality}")
            print(f"体力: {info.stamina}/{info.max_stamina}")
            print(f"行动点: {info.action_points}")
            print(f"已睡眠: {'是' if info.has_slept else '否'}")
            print(f"货币: {info.inventory.money}")
            if info.inventory.items:
                print(f"物品:")
                for item, qty in dict(info.inventory.items).items():
                    print(f"  - {item}: {qty}")
            else:
                print(f"物品: 无")
            print("="*70 + "\n")
        except Exception as e:
            print(f"✗ 获取信息失败: {e}")
    
    def do_produce(self):
        """执行生产"""
        try:
            channel = grpc.insecure_channel(self.node_address)
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.Produce(town_pb2.ProduceRequest())
            channel.close()
            
            if response.success:
                print(f"✓ {response.message}")
            else:
                print(f"✗ {response.message}")
        except Exception as e:
            print(f"✗ 生产失败: {e}")
    
    def do_sleep(self):
        """睡眠"""
        try:
            channel = grpc.insecure_channel(self.node_address)
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.Sleep(town_pb2.SleepRequest())
            channel.close()
            
            if response.success:
                print(f"✓ {response.message}")
            else:
                print(f"✗ {response.message}")
        except Exception as e:
            print(f"✗ 睡眠失败: {e}")
    
    def get_current_time(self):
        """获取当前时间"""
        try:
            channel = grpc.insecure_channel(self.coordinator_address)
            stub = town_pb2_grpc.TimeCoordinatorStub(channel)
            time = stub.GetCurrentTime(town_pb2.Empty())
            channel.close()
            print(f"\n当前时间: Day {time.day} - {time.time_of_day}\n")
        except Exception as e:
            print(f"✗ 获取时间失败: {e}")
    
    def advance_time(self):
        """推进时间"""
        try:
            channel = grpc.insecure_channel(self.coordinator_address)
            stub = town_pb2_grpc.TimeCoordinatorStub(channel)
            response = stub.AdvanceTime(town_pb2.Empty())
            channel.close()
            
            if response.success:
                print(f"✓ {response.message}")
            else:
                print(f"✗ {response.message}")
        except Exception as e:
            print(f"✗ 推进时间失败: {e}")
    
    def get_merchant_prices(self):
        """获取商人价格表"""
        try:
            channel = grpc.insecure_channel(self.merchant_address)
            stub = town_pb2_grpc.MerchantNodeStub(channel)
            prices = stub.GetPrices(town_pb2.Empty())
            channel.close()
            
            print("\n" + "="*70)
            print("  商人价格表")
            print("="*70)
            print("\n【商人出售】(你可以购买)")
            for price_info in prices.buy_prices:
                print(f"  {price_info.item:15s} : {price_info.price:4d} 金币")
            
            print("\n【商人收购】(你可以出售)")
            for price_info in prices.sell_prices:
                print(f"  {price_info.item:15s} : {price_info.price:4d} 金币")
            print("="*70 + "\n")
        except Exception as e:
            print(f"✗ 获取价格失败: {e}")
    
    def buy_from_merchant(self, item, quantity):
        """从商人购买"""
        try:
            channel = grpc.insecure_channel(self.node_address)
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.Trade(town_pb2.TradeRequest(
                target_node='merchant',
                item=item,
                quantity=quantity,
                price=0  # 0表示buy
            ))
            channel.close()
            
            if response.success:
                print(f"✓ {response.message}")
            else:
                print(f"✗ {response.message}")
        except Exception as e:
            print(f"✗ 购买失败: {e}")
    
    def sell_to_merchant(self, item, quantity):
        """向商人出售"""
        try:
            channel = grpc.insecure_channel(self.node_address)
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.Trade(town_pb2.TradeRequest(
                target_node='merchant',
                item=item,
                quantity=quantity,
                price=1  # 非0表示sell
            ))
            channel.close()
            
            if response.success:
                print(f"✓ {response.message}")
            else:
                print(f"✗ {response.message}")
        except Exception as e:
            print(f"✗ 出售失败: {e}")
    
    def create_trade(self, target_id, offer_type, item, quantity, price):
        """创建村民间交易"""
        if target_id not in self.nodes:
            print(f"✗ 未知的节点: {target_id}")
            print(f"提示: 使用 'nodes' 命令查看在线村民")
            return
        
        target_address = self.nodes[target_id]
        
        try:
            channel = grpc.insecure_channel(self.merchant_address)
            stub = town_pb2_grpc.MerchantNodeStub(channel)
            response = stub.CreateTrade(town_pb2.CreateTradeRequest(
                initiator_id=self.node_id,
                initiator_address=self.node_address,
                target_id=target_id,
                target_address=target_address,
                offer_type=offer_type,
                item=item,
                quantity=quantity,
                price=price
            ))
            channel.close()
            
            if response.success:
                print(f"✓ 交易请求已发送: {response.trade_id}")
                print(f"  对方: {target_id}")
                print(f"  内容: {offer_type} {quantity}x {item} @ {price}")
            else:
                print(f"✗ {response.message}")
        except Exception as e:
            print(f"✗ 创建交易失败: {e}")
    
    def list_pending_trades(self):
        """查看待处理的交易"""
        try:
            channel = grpc.insecure_channel(self.merchant_address)
            stub = town_pb2_grpc.MerchantNodeStub(channel)
            response = stub.ListTrades(town_pb2.ListTradesRequest(
                node_id=self.node_id,
                type='pending'
            ))
            channel.close()
            
            if not response.trades:
                print("\n没有待处理的交易请求\n")
                return
            
            print("\n" + "="*70)
            print("  待处理的交易请求")
            print("="*70)
            for trade in response.trades:
                print(f"\n交易ID: {trade.trade_id}")
                print(f"  发起方: {trade.initiator_id}")
                print(f"  类型: {trade.offer_type}")
                print(f"  物品: {trade.item} x{trade.quantity}")
                print(f"  价格: {trade.price}")
                print(f"  状态: {trade.status}")
            print("="*70 + "\n")
        except Exception as e:
            print(f"✗ 获取交易列表失败: {e}")
    
    def list_my_trades(self):
        """查看我发起的交易"""
        try:
            channel = grpc.insecure_channel(self.merchant_address)
            stub = town_pb2_grpc.MerchantNodeStub(channel)
            response = stub.ListTrades(town_pb2.ListTradesRequest(
                node_id=self.node_id,
                type='sent'
            ))
            channel.close()
            
            if not response.trades:
                print("\n你没有发起的交易\n")
                return
            
            print("\n" + "="*70)
            print("  我发起的交易")
            print("="*70)
            for trade in response.trades:
                print(f"\n交易ID: {trade.trade_id}")
                print(f"  对方: {trade.target_id}")
                print(f"  类型: {trade.offer_type}")
                print(f"  物品: {trade.item} x{trade.quantity}")
                print(f"  价格: {trade.price}")
                print(f"  状态: {trade.status}")
                if trade.status == 'accepted':
                    print(f"  我已确认: {'是' if trade.initiator_confirmed else '否'}")
                    print(f"  对方已确认: {'是' if trade.target_confirmed else '否'}")
            print("="*70 + "\n")
        except Exception as e:
            print(f"✗ 获取交易列表失败: {e}")
    
    def accept_trade(self, trade_id):
        """接受交易"""
        try:
            channel = grpc.insecure_channel(self.merchant_address)
            stub = town_pb2_grpc.MerchantNodeStub(channel)
            response = stub.AcceptTrade(town_pb2.AcceptTradeRequest(
                trade_id=trade_id,
                node_id=self.node_id
            ))
            channel.close()
            
            if response.success:
                print(f"✓ {response.message}")
            else:
                print(f"✗ {response.message}")
        except Exception as e:
            print(f"✗ 接受交易失败: {e}")
    
    def reject_trade(self, trade_id):
        """拒绝交易"""
        try:
            channel = grpc.insecure_channel(self.merchant_address)
            stub = town_pb2_grpc.MerchantNodeStub(channel)
            response = stub.RejectTrade(town_pb2.RejectTradeRequest(
                trade_id=trade_id,
                node_id=self.node_id
            ))
            channel.close()
            
            if response.success:
                print(f"✓ {response.message}")
            else:
                print(f"✗ {response.message}")
        except Exception as e:
            print(f"✗ 拒绝交易失败: {e}")
    
    def confirm_trade(self, trade_id):
        """确认交易"""
        try:
            channel = grpc.insecure_channel(self.merchant_address)
            stub = town_pb2_grpc.MerchantNodeStub(channel)
            response = stub.ConfirmTrade(town_pb2.ConfirmTradeRequest(
                trade_id=trade_id,
                node_id=self.node_id
            ))
            channel.close()
            
            if response.success:
                print(f"✓ {response.message}")
            else:
                print(f"✗ {response.message}")
        except Exception as e:
            print(f"✗ 确认交易失败: {e}")
    
    def cancel_trade(self, trade_id):
        """取消交易"""
        try:
            channel = grpc.insecure_channel(self.merchant_address)
            stub = town_pb2_grpc.MerchantNodeStub(channel)
            response = stub.CancelTrade(town_pb2.CancelTradeRequest(
                trade_id=trade_id,
                node_id=self.node_id
            ))
            channel.close()
            
            if response.success:
                print(f"✓ {response.message}")
            else:
                print(f"✗ {response.message}")
        except Exception as e:
            print(f"✗ 取消交易失败: {e}")
    
    def show_nodes(self):
        """显示在线节点"""
        self.refresh_nodes()
        
        if not self.nodes:
            print("\n没有找到其他村民节点\n")
            return
        
        print("\n" + "="*70)
        print("  在线村民节点")
        print("="*70)
        for node_id, address in self.nodes.items():
            if node_id == self.node_id:
                print(f"  {node_id:15s} @ {address:25s} (我)")
            else:
                print(f"  {node_id:15s} @ {address}")
        print("="*70 + "\n")
    
    def run(self):
        """运行交互式循环"""
        self.show_help()
        self.refresh_nodes()
        
        while True:
            try:
                cmd = input(f"[{self.node_id}]> ").strip()
                
                if not cmd:
                    continue
                
                parts = cmd.split()
                action = parts[0].lower()
                
                if action in ['exit', 'quit']:
                    print("再见！")
                    break
                
                elif action == 'help':
                    self.show_help()
                
                elif action == 'info':
                    self.get_my_info()
                
                elif action == 'produce':
                    self.do_produce()
                
                elif action == 'sleep':
                    self.do_sleep()
                
                elif action == 'time':
                    self.get_current_time()
                
                elif action == 'advance':
                    self.advance_time()
                
                elif action == 'price':
                    self.get_merchant_prices()
                
                elif action == 'buy':
                    if len(parts) < 3:
                        print("用法: buy <item> <quantity>")
                    else:
                        self.buy_from_merchant(parts[1], int(parts[2]))
                
                elif action == 'sell':
                    if len(parts) < 3:
                        print("用法: sell <item> <quantity>")
                    else:
                        self.sell_to_merchant(parts[1], int(parts[2]))
                
                elif action == 'nodes':
                    self.show_nodes()
                
                elif action == 'trade':
                    if len(parts) < 6:
                        print("用法: trade <node_id> <buy/sell> <item> <quantity> <price>")
                    else:
                        self.create_trade(parts[1], parts[2], parts[3], int(parts[4]), int(parts[5]))
                
                elif action == 'trades':
                    self.list_pending_trades()
                
                elif action == 'mytrades':
                    self.list_my_trades()
                
                elif action == 'accept':
                    if len(parts) < 2:
                        print("用法: accept <trade_id>")
                    else:
                        self.accept_trade(parts[1])
                
                elif action == 'reject':
                    if len(parts) < 2:
                        print("用法: reject <trade_id>")
                    else:
                        self.reject_trade(parts[1])
                
                elif action == 'confirm':
                    if len(parts) < 2:
                        print("用法: confirm <trade_id>")
                    else:
                        self.confirm_trade(parts[1])
                
                elif action == 'cancel':
                    if len(parts) < 2:
                        print("用法: cancel <trade_id>")
                    else:
                        self.cancel_trade(parts[1])
                
                else:
                    print(f"未知命令: {action}")
                    print("输入 'help' 查看可用命令")
            
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"✗ 错误: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='村民节点交互式CLI')
    parser.add_argument('--id', type=str, required=True, help='节点ID')
    parser.add_argument('--address', type=str, required=True, help='节点地址')
    parser.add_argument('--merchant', type=str, default='localhost:50052', help='商人地址')
    parser.add_argument('--coordinator', type=str, default='localhost:50051', help='协调器地址')
    args = parser.parse_args()
    
    cli = InteractiveCLI(args.id, args.address, args.merchant, args.coordinator)
    cli.run()


if __name__ == '__main__':
    main()

