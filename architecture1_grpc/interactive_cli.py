"""
交互式CLI客户端 - 控制单个村民节点 (gRPC版本)
完全复制REST版本的功能
"""

import grpc
import sys
import os
import time
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
from proto import town_pb2
from proto import town_pb2_grpc


class VillagerCLI:
    """村民节点交互式CLI"""
    
    def __init__(self, villager_port: int, coordinator_port: int = 50051, merchant_port: int = 50052):
        self.villager_address = f"localhost:{villager_port}"
        self.coordinator_address = f"localhost:{coordinator_port}"
        self.merchant_address = f"localhost:{merchant_port}"
        self.villager_port = villager_port
        self.node_id = None  # 将在首次获取信息时设置
        self.pending_trades = {}  # 当前等待响应的交易
    
    def _get_villager_stub(self):
        """获取villager stub"""
        channel = grpc.insecure_channel(self.villager_address)
        return channel, town_pb2_grpc.VillagerNodeStub(channel)
    
    def _get_coordinator_stub(self):
        """获取coordinator stub"""
        channel = grpc.insecure_channel(self.coordinator_address)
        return channel, town_pb2_grpc.TimeCoordinatorStub(channel)
    
    def _get_merchant_stub(self):
        """获取merchant stub"""
        channel = grpc.insecure_channel(self.merchant_address)
        return channel, town_pb2_grpc.MerchantNodeStub(channel)
    
    def check_connection(self) -> bool:
        """检查连接"""
        try:
            channel, stub = self._get_villager_stub()
            stub.GetInfo(town_pb2.Empty())
            channel.close()
            return True
        except:
            return False
    
    def get_villager_info(self) -> Optional[dict]:
        """获取村民信息"""
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
                'has_slept': info.has_slept,
                'inventory': {
                    'money': info.inventory.money,
                    'items': dict(info.inventory.items)
                }
            }
        except Exception as e:
            print(f"错误: {e}")
            return None
    
    def create_villager(self, name: str, occupation: str, gender: str, personality: str):
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
            
            if response.success:
                print(f"\n✓ 村民创建成功!")
                self.display_villager_info()
            else:
                print(f"\n✗ 创建失败: {response.message}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def display_villager_info(self, info: dict = None):
        """显示村民信息"""
        if info is None:
            info = self.get_villager_info()
        
        if not info:
            print("\n村民未初始化")
            return
        
        print("\n" + "="*50)
        print(f"  {info['name']} - {info['occupation']}")
        print("="*50)
        print(f"性别: {info['gender']}")
        print(f"性格: {info['personality']}")
        print(f"⚡ 体力: {info['stamina']}/{info['max_stamina']}")
        print(f"😴 已睡眠: {'是' if info['has_slept'] else '否'}")
        print(f"\n💰 货币: {info['inventory']['money']}")
        
        if info['inventory']['items']:
            print("📦 物品:")
            for item, quantity in info['inventory']['items'].items():
                print(f"   - {item}: {quantity}")
        else:
            print("📦 物品: 无")
        print("="*50)
    
    def produce(self):
        """执行生产"""
        try:
            channel, stub = self._get_villager_stub()
            response = stub.Produce(town_pb2.ProduceRequest())
            channel.close()
            
            if response.success:
                print(f"\n✓ {response.message}")
                self.display_villager_info()
            else:
                print(f"\n✗ {response.message}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def trade(self, action: str, item: str, quantity: int):
        """与商人交易"""
        try:
            channel, stub = self._get_villager_stub()
            # action: buy or sell
            price = 0 if action == 'buy' else 1  # 使用price字段传递action
            response = stub.Trade(town_pb2.TradeRequest(
                target_node='merchant',
                item=item,
                quantity=quantity,
                price=price
            ))
            channel.close()
            
            if response.success:
                print(f"\n✓ {response.message}")
                self.display_villager_info()
            else:
                print(f"\n✗ {response.message}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def sleep(self):
        """睡眠"""
        try:
            channel, stub = self._get_villager_stub()
            response = stub.Sleep(town_pb2.SleepRequest())
            channel.close()
            
            if response.success:
                print(f"\n✓ {response.message}")
                self.display_villager_info()
            else:
                print(f"\n✗ {response.message}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def get_current_time(self):
        """获取当前时间"""
        try:
            channel, stub = self._get_coordinator_stub()
            time_info = stub.GetCurrentTime(town_pb2.Empty())
            channel.close()
            print(f"\n当前时间: Day {time_info.day} - {time_info.time_of_day}\n")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def get_node_id(self):
        """获取本节点ID (从coordinator查询)"""
        if self.node_id:
            return self.node_id
        
        try:
            channel, stub = self._get_coordinator_stub()
            response = stub.ListNodes(town_pb2.Empty())
            channel.close()
            
            # 根据地址查找node_id
            for node in response.nodes:
                if node.address == self.villager_address:
                    self.node_id = node.node_id
                    return self.node_id
            
            # 如果找不到，使用端口号
            self.node_id = f"node{self.villager_port}"
            return self.node_id
        except:
            self.node_id = f"node{self.villager_port}"
            return self.node_id
    
    def get_all_villagers(self):
        """获取所有村民节点"""
        try:
            channel, stub = self._get_coordinator_stub()
            response = stub.ListNodes(town_pb2.Empty())
            channel.close()
            
            villagers = []
            for node in response.nodes:
                if node.node_type == 'villager':
                    villagers.append({
                        'node_id': node.node_id,
                        'address': node.address
                    })
            return villagers
        except Exception as e:
            print(f"✗ 获取村民列表失败: {e}")
            return []
    
    def get_online_villagers(self):
        """获取在线村民"""
        villagers = self.get_all_villagers()
        
        if not villagers:
            print("\n没有找到其他村民节点")
            return []
        
        print("\n" + "="*50)
        print("  在线村民")
        print("="*50)
        
        my_node_id = self.get_node_id()
        online_list = []
        
        for v in villagers:
            # 获取村民信息
            try:
                channel = grpc.insecure_channel(v['address'])
                stub = town_pb2_grpc.VillagerNodeStub(channel)
                info = stub.GetInfo(town_pb2.Empty())
                channel.close()
                
                is_me = v['node_id'] == my_node_id
                marker = " (我)" if is_me else ""
                print(f"{v['node_id']:15s} - {info.name:15s} ({info.occupation}){marker}")
                
                if not is_me:
                    online_list.append({
                        'node_id': v['node_id'],
                        'name': info.name,
                        'occupation': info.occupation,
                        'address': v['address']
                    })
            except:
                print(f"{v['node_id']:15s} - [离线]")
        
        print("="*50)
        return online_list
    
    def trade_with_villager(self, target_node: str, item: str, quantity: int, price: int, offer_type: str):
        """向村民发起交易"""
        try:
            # 获取目标地址
            villagers = self.get_all_villagers()
            target_address = None
            for v in villagers:
                if v['node_id'] == target_node:
                    target_address = v['address']
                    break
            
            if not target_address:
                print(f"\n✗ 找不到节点: {target_node}")
                return
            
            my_node_id = self.get_node_id()
            
            channel, stub = self._get_merchant_stub()
            response = stub.CreateTrade(town_pb2.CreateTradeRequest(
                initiator_id=my_node_id,
                initiator_address=self.villager_address,
                target_id=target_node,
                target_address=target_address,
                offer_type=offer_type,
                item=item,
                quantity=quantity,
                price=price
            ))
            channel.close()
            
            if response.success:
                print(f"\n✓ 交易请求已发送: {response.trade_id}")
                print(f"  对方: {target_node}")
                print(f"  内容: {offer_type} {quantity}x {item} @ {price}\n")
            else:
                print(f"\n✗ {response.message}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def show_my_pending_trades(self):
        """查看我发起的交易"""
        try:
            my_node_id = self.get_node_id()
            
            channel, stub = self._get_merchant_stub()
            response = stub.ListTrades(town_pb2.ListTradesRequest(
                node_id=my_node_id,
                type='sent'
            ))
            channel.close()
            
            if not response.trades:
                print("\n你没有发起的交易\n")
                return
            
            print("\n" + "="*50)
            print("  我发起的交易")
            print("="*50)
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
            print("="*50 + "\n")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def check_pending_trades(self):
        """查看待处理的交易"""
        try:
            my_node_id = self.get_node_id()
            
            channel, stub = self._get_merchant_stub()
            response = stub.ListTrades(town_pb2.ListTradesRequest(
                node_id=my_node_id,
                type='pending'
            ))
            channel.close()
            
            if not response.trades:
                print("\n没有待处理的交易请求\n")
                return
            
            print("\n" + "="*50)
            print("  待处理的交易请求")
            print("="*50)
            for trade in response.trades:
                print(f"\n交易ID: {trade.trade_id}")
                print(f"  发起方: {trade.initiator_id}")
                print(f"  类型: {trade.offer_type}")
                print(f"  物品: {trade.item} x{trade.quantity}")
                print(f"  价格: {trade.price}")
                print(f"  状态: {trade.status}")
            print("="*50 + "\n")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def accept_trade_request(self, trade_id: str):
        """接受交易"""
        try:
            my_node_id = self.get_node_id()
            
            channel, stub = self._get_merchant_stub()
            response = stub.AcceptTrade(town_pb2.AcceptTradeRequest(
                trade_id=trade_id,
                node_id=my_node_id
            ))
            channel.close()
            
            if response.success:
                print(f"\n✓ {response.message}\n")
            else:
                print(f"\n✗ {response.message}\n")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def confirm_trade_request(self, trade_id: str):
        """确认交易"""
        try:
            my_node_id = self.get_node_id()
            
            channel, stub = self._get_merchant_stub()
            response = stub.ConfirmTrade(town_pb2.ConfirmTradeRequest(
                trade_id=trade_id,
                node_id=my_node_id
            ))
            channel.close()
            
            if response.success:
                print(f"\n✓ {response.message}\n")
                self.display_villager_info()
            else:
                print(f"\n✗ {response.message}\n")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def reject_trade_request(self, trade_id: str):
        """拒绝交易"""
        try:
            my_node_id = self.get_node_id()
            
            channel, stub = self._get_merchant_stub()
            response = stub.RejectTrade(town_pb2.RejectTradeRequest(
                trade_id=trade_id,
                node_id=my_node_id
            ))
            channel.close()
            
            if response.success:
                print(f"\n✓ {response.message}\n")
            else:
                print(f"\n✗ {response.message}\n")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def cancel_trade_request(self, trade_id: str):
        """取消交易"""
        try:
            my_node_id = self.get_node_id()
            
            channel, stub = self._get_merchant_stub()
            response = stub.CancelTrade(town_pb2.CancelTradeRequest(
                trade_id=trade_id,
                node_id=my_node_id
            ))
            channel.close()
            
            if response.success:
                print(f"\n✓ {response.message}\n")
            else:
                print(f"\n✗ {response.message}\n")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def get_merchant_prices(self):
        """获取商人价格"""
        try:
            channel, stub = self._get_merchant_stub()
            prices = stub.GetPrices(town_pb2.Empty())
            channel.close()
            
            print("\n" + "="*50)
            print("  商人价格表")
            print("="*50)
            print("\n【商人出售】(你可以购买)")
            for price_info in prices.buy_prices:
                print(f"  {price_info.item:15s} : {price_info.price:4d} 金币")
            
            print("\n【商人收购】(你可以出售)")
            for price_info in prices.sell_prices:
                print(f"  {price_info.item:15s} : {price_info.price:4d} 金币")
            print("="*50 + "\n")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def show_help(self):
        """显示帮助"""
        print("\n" + "="*70)
        print("  可用命令")
        print("="*70)
        print("\n【村民管理】")
        print("  create          - 创建村民")
        print("  info            - 查看我的信息")
        print("")
        print("【生产与生活】")
        print("  produce         - 执行生产")
        print("  sleep           - 睡眠")
        print("")
        print("【商人交易】")
        print("  price           - 查看商人价格表")
        print("  buy <item> <qty>   - 从商人购买物品")
        print("  sell <item> <qty>  - 向商人出售物品")
        print("")
        print("【村民交易】")
        print("  nodes           - 查看在线村民")
        print("  trade <node_id> <buy/sell> <item> <qty> <price>")
        print("                  - 向村民发起交易")
        print("  trades          - 查看待处理的交易请求")
        print("  mytrades        - 查看我发起的交易")
        print("  accept <trade_id>  - 接受交易请求")
        print("  reject <trade_id>  - 拒绝交易请求")
        print("  confirm <trade_id> - 确认交易")
        print("  cancel <trade_id>  - 取消交易")
        print("")
        print("【时间管理】")
        print("  time            - 查看当前时间")
        print("  advance         - 推进时间(需要协调器)")
        print("")
        print("【其他】")
        print("  help            - 显示此帮助")
        print("  exit/quit       - 退出")
        print("="*70 + "\n")
    
    def run(self):
        """运行交互式循环"""
        print("\n" + "="*70)
        print("  村民节点交互式CLI (gRPC版本)")
        print("="*70)
        print(f"连接到: {self.villager_address}")
        print(f"协调器: {self.coordinator_address}")
        print(f"商人: {self.merchant_address}")
        print("="*70)
        
        # 检查连接
        if not self.check_connection():
            print("\n⚠ 警告: 无法连接到村民节点")
            print("请确保村民节点正在运行\n")
        
        self.show_help()
        
        while True:
            try:
                cmd = input("> ").strip()
                
                if not cmd:
                    continue
                
                parts = cmd.split()
                action = parts[0].lower()
                
                if action in ['exit', 'quit']:
                    print("再见！")
                    break
                
                elif action == 'help':
                    self.show_help()
                
                elif action == 'create':
                    print("\n创建村民")
                    name = input("名字: ").strip()
                    print("职业选择: farmer (农夫), carpenter (木匠), chef (厨师)")
                    occupation = input("职业: ").strip()
                    print("性别选择: male (男), female (女)")
                    gender = input("性别: ").strip()
                    personality = input("性格描述: ").strip()
                    self.create_villager(name, occupation, gender, personality)
                
                elif action == 'info':
                    self.display_villager_info()
                
                elif action == 'produce':
                    self.produce()
                
                elif action == 'sleep':
                    self.sleep()
                
                elif action == 'time':
                    self.get_current_time()
                
                elif action == 'advance':
                    try:
                        channel, stub = self._get_coordinator_stub()
                        response = stub.AdvanceTime(town_pb2.Empty())
                        channel.close()
                        if response.success:
                            print(f"\n✓ {response.message}\n")
                        else:
                            print(f"\n✗ {response.message}\n")
                    except Exception as e:
                        print(f"\n✗ 错误: {e}")
                
                elif action == 'price':
                    self.get_merchant_prices()
                
                elif action == 'buy':
                    if len(parts) < 3:
                        print("用法: buy <item> <quantity>")
                    else:
                        self.trade('buy', parts[1], int(parts[2]))
                
                elif action == 'sell':
                    if len(parts) < 3:
                        print("用法: sell <item> <quantity>")
                    else:
                        self.trade('sell', parts[1], int(parts[2]))
                
                elif action == 'nodes':
                    self.get_online_villagers()
                
                elif action == 'trade':
                    if len(parts) < 6:
                        print("用法: trade <node_id> <buy/sell> <item> <quantity> <price>")
                    else:
                        self.trade_with_villager(parts[1], parts[3], int(parts[4]), int(parts[5]), parts[2])
                
                elif action == 'trades':
                    self.check_pending_trades()
                
                elif action == 'mytrades':
                    self.show_my_pending_trades()
                
                elif action == 'accept':
                    if len(parts) < 2:
                        print("用法: accept <trade_id>")
                    else:
                        self.accept_trade_request(parts[1])
                
                elif action == 'reject':
                    if len(parts) < 2:
                        print("用法: reject <trade_id>")
                    else:
                        self.reject_trade_request(parts[1])
                
                elif action == 'confirm':
                    if len(parts) < 2:
                        print("用法: confirm <trade_id>")
                    else:
                        self.confirm_trade_request(parts[1])
                
                elif action == 'cancel':
                    if len(parts) < 2:
                        print("用法: cancel <trade_id>")
                    else:
                        self.cancel_trade_request(parts[1])
                
                else:
                    print(f"未知命令: {action}")
                    print("输入 'help' 查看可用命令")
            
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\n✗ 错误: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='村民节点交互式CLI (gRPC)')
    parser.add_argument('--port', type=int, required=True, help='村民节点端口')
    parser.add_argument('--coordinator', type=int, default=50051, help='协调器端口')
    parser.add_argument('--merchant', type=int, default=50052, help='商人端口')
    args = parser.parse_args()
    
    cli = VillagerCLI(args.port, args.coordinator, args.merchant)
    cli.run()


if __name__ == '__main__':
    main()
