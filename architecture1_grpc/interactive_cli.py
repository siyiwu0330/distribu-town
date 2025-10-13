"""
交互式CLI客户端 - 控制单个VillagerNode (gRPC版本)
完全复制REST版本的功能
"""

import grpc
import sys
import os
import time
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
import town_pb2
import town_pb2_grpc


class VillagerCLI:
    """VillagerNode交互式CLI"""
    
    def __init__(self, villager_port: int, coordinator_port: int = 50051, merchant_port: int = 50052):
        self.villager_address = f"localhost:{villager_port}"
        self.coordinator_address = f"localhost:{coordinator_port}"
        self.merchant_address = f"localhost:{merchant_port}"
        self.villager_port = villager_port
        self.node_id = None  # 将在首次Getinformation时Set
        self.pending_trades = {}  # 当前Waiting响应的Trade
        
        # Message系统
        self.received_messages = []
    
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
        """GetVillagerinformation"""
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
            print(f"Error: {e}")
            return None
    
    def create_villager(self, name: str, occupation: str, gender: str, personality: str):
        """CreateVillager"""
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
                print(f"\n✓ VillagerCreateSuccess!")
                self.display_villager_info()
            else:
                print(f"\n✗ CreateFailed: {response.message}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def display_villager_info(self, info: dict = None):
        """显示VillagerInfo"""
        if info is None:
            info = self.get_villager_info()
        
        if not info:
            print("\nVillager未初始化")
            return
        
        print("\n" + "="*50)
        print(f"  {info['name']} - {info['occupation']}")
        print("="*50)
        print(f"性别: {info['gender']}")
        print(f"性格: {info['personality']}")
        print(f"⚡ Stamina: {info['stamina']}/{info['max_stamina']}")
        print(f"😴 已Sleep: {'是' if info['has_slept'] else '否'}")
        print(f"\n💰 Money: {info['inventory']['money']}")
        
        if info['inventory']['items']:
            print("📦 Item:")
            for item, quantity in info['inventory']['items'].items():
                print(f"   - {item}: {quantity}")
        else:
            print("📦 Item: 无")
        print("="*50)
    
    def produce(self):
        """ExecuteProduction"""
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
            print(f"\n✗ Error: {e}")
    
    def trade(self, action: str, item: str, quantity: int):
        """与MerchantTrade"""
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
            print(f"\n✗ Error: {e}")
    
    def sleep(self):
        """Sleep"""
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
            print(f"\n✗ Error: {e}")
    
    def get_current_time(self):
        """获取当前Time"""
        try:
            channel, stub = self._get_coordinator_stub()
            time_info = stub.GetCurrentTime(town_pb2.Empty())
            channel.close()
            return f"Day {time_info.day} - {time_info.time_of_day}"
        except Exception as e:
            return "Unknown"
    
    def get_node_id(self):
        """获取本NodeID (从coordinatorQuery)"""
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
        """获取所有VillagerNode"""
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
            print(f"✗ 获取Villager列表Failed: {e}")
            return []
    
    def get_online_villagers(self):
        """获取在线Villager"""
        villagers = self.get_all_villagers()
        
        if not villagers:
            print("\n没有找到其他VillagerNode")
            return []
        
        print("\n" + "="*50)
        print("  在线Villager")
        print("="*50)
        
        my_node_id = self.get_node_id()
        online_list = []
        
        for v in villagers:
            # GetVillagerinformation
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
        """向Villager发起Trade"""
        try:
            # 获取目标地址
            villagers = self.get_all_villagers()
            target_address = None
            for v in villagers:
                if v['node_id'] == target_node:
                    target_address = v['address']
                    break
            
            if not target_address:
                print(f"\n✗ 找不到Node: {target_node}")
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
                print(f"\n✓ Trade请求已Send: {response.trade_id}")
                print(f"  对方: {target_node}")
                print(f"  内容: {offer_type} {quantity}x {item} @ {price}")
                print(f"\n⏳ Waiting {target_node} Accept或Reject...")
                print(f"💡 提示: 对方需要输入 'accept {response.trade_id}' 和 'confirm {response.trade_id}'")
                print(f"   使用 'mytrades' 查看此Trade的状态\n")
            else:
                print(f"\n✗ {response.message}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def show_my_pending_trades(self):
        """查看我的所有Trade（Send的和收到的）"""
        try:
            my_node_id = self.get_node_id()
            
            channel, stub = self._get_merchant_stub()
            response = stub.ListTrades(town_pb2.ListTradesRequest(
                node_id=my_node_id,
                type='all'
            ))
            channel.close()
            
            if not response.trades:
                print("\n你没有相关Trade\n")
                return
            
            print("\n" + "="*50)
            print("  我的Trade")
            print("="*50)
            
            # 分类显示
            sent_trades = []
            received_trades = []
            
            for trade in response.trades:
                if trade.initiator_id == my_node_id:
                    sent_trades.append(trade)
                else:
                    received_trades.append(trade)
            
            # 显示我发起的Trade
            if sent_trades:
                print("\n📤 我发起的Trade:")
                for trade in sent_trades:
                    print(f"\nTradeID: {trade.trade_id}")
                    print(f"  对方: {trade.target_id}")
                    print(f"  类型: {trade.offer_type}")
                    print(f"  Item: {trade.item} x{trade.quantity}")
                    print(f"  Price: {trade.price}")
                    
                    # 根据状态显示不同的提示
                    if trade.status == 'accepted':
                        print(f"  状态: ✓ 对方已Accept（Waiting双方Confirm）")
                        if not trade.initiator_confirmed:
                            print(f"  💡 操作: confirm {trade.trade_id}")
                        elif not trade.target_confirmed:
                            print(f"  💡 Waiting: 对方Confirm中...")
                        else:
                            print(f"  💡 状态: 双方已Confirm，Trade将自动完成")
                    elif trade.status == 'pending':
                        print(f"  状态: ⏳ Waiting对方Accept")
                        print(f"  💡 操作: Waiting对方响应或 cancel {trade.trade_id}")
                    elif trade.status == 'rejected':
                        print(f"  状态: ✗ 已被Reject")
                    elif trade.status == 'completed':
                        print(f"  状态: ✓ Trade完成")
            
            # 显示我收到的Trade
            if received_trades:
                print("\n📥 我收到的Trade:")
                for trade in received_trades:
                    print(f"\nTradeID: {trade.trade_id}")
                    print(f"  发起方: {trade.initiator_id}")
                    print(f"  类型: {trade.offer_type}")
                    print(f"  Item: {trade.item} x{trade.quantity}")
                    print(f"  Price: {trade.price}")
                    
                    # 根据状态显示不同的提示
                    if trade.status == 'pending':
                        print(f"  状态: ⏳ 待Handle")
                        print(f"  💡 操作: accept {trade.trade_id} 或 reject {trade.trade_id}")
                    elif trade.status == 'accepted':
                        print(f"  状态: ✓ 已Accept（Waiting双方Confirm）")
                        if not trade.target_confirmed:
                            print(f"  💡 操作: confirm {trade.trade_id}")
                        elif not trade.initiator_confirmed:
                            print(f"  💡 Waiting: 对方Confirm中...")
                        else:
                            print(f"  💡 状态: 双方已Confirm，Trade将自动完成")
                    elif trade.status == 'rejected':
                        print(f"  状态: ✗ 已Reject")
                    elif trade.status == 'completed':
                        print(f"  状态: ✓ Trade完成")
            
            print("="*50 + "\n")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def check_pending_trades(self):
        """查看待Handle的Trade"""
        try:
            my_node_id = self.get_node_id()
            
            channel, stub = self._get_merchant_stub()
            response = stub.ListTrades(town_pb2.ListTradesRequest(
                node_id=my_node_id,
                type='received'
            ))
            channel.close()
            
            if not response.trades:
                print("\n没有待Handle的Trade请求\n")
                return
            
            print("\n" + "="*50)
            print("  待Handle的Trade请求")
            print("="*50)
            for trade in response.trades:
                print(f"\nTradeID: {trade.trade_id}")
                print(f"  发起方: {trade.initiator_id}")
                print(f"  类型: {trade.offer_type}")
                print(f"  Item: {trade.item} x{trade.quantity}")
                print(f"  Price: {trade.price}")
                
                # 根据状态显示不同的提示
                if trade.status == 'pending':
                    print(f"  状态: ⏳ 待Handle")
                    print(f"  💡 操作: accept {trade.trade_id} 或 reject {trade.trade_id}")
                elif trade.status == 'accepted':
                    print(f"  状态: ✓ 已Accept（Waiting双方Confirm）")
                    if not trade.target_confirmed:
                        print(f"  💡 操作: confirm {trade.trade_id}")
                    elif not trade.initiator_confirmed:
                        print(f"  💡 Waiting: 对方Confirm中...")
                    else:
                        print(f"  💡 状态: 双方已Confirm，Trade将自动完成")
                elif trade.status == 'rejected':
                    print(f"  状态: ✗ 已Reject")
                elif trade.status == 'completed':
                    print(f"  状态: ✓ Trade完成")
            print("="*50 + "\n")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def accept_trade_request(self, trade_id: str):
        """AcceptTrade"""
        try:
            my_node_id = self.get_node_id()
            
            channel, stub = self._get_merchant_stub()
            response = stub.AcceptTrade(town_pb2.AcceptTradeRequest(
                trade_id=trade_id,
                node_id=my_node_id
            ))
            channel.close()
            
            if response.success:
                print(f"\n✓ {response.message}")
                print(f"💡 提示: Trade已Accept，现在需要双方Confirm")
                print(f"   使用 'confirm {trade_id}' ConfirmTrade")
                print(f"   或使用 'cancel {trade_id}' CancelTrade\n")
            else:
                print(f"\n✗ {response.message}\n")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def confirm_trade_request(self, trade_id: str):
        """ConfirmTrade"""
        try:
            my_node_id = self.get_node_id()
            
            channel, stub = self._get_merchant_stub()
            response = stub.ConfirmTrade(town_pb2.ConfirmTradeRequest(
                trade_id=trade_id,
                node_id=my_node_id
            ))
            channel.close()
            
            if response.success:
                print(f"\n✓ Trade已Confirm")
                print(f"   使用 'mytrades' 查看Trade状态\n")
            else:
                print(f"\n✗ {response.message}\n")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def reject_trade_request(self, trade_id: str):
        """RejectTrade"""
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
            print(f"\n✗ Error: {e}")
    
    def cancel_trade_request(self, trade_id: str):
        """CancelTrade"""
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
            print(f"\n✗ Error: {e}")
    
    def get_messages(self):
        """获取Message列表"""
        try:
            channel, stub = self._get_villager_stub()
            response = stub.GetMessages(town_pb2.GetMessagesRequest(
                node_id=self.node_id
            ))
            channel.close()
            
            messages = []
            for msg in response.messages:
                from_field = getattr(msg, 'from', 'unknown')
                messages.append({
                    'message_id': msg.message_id,
                    'from': from_field,
                    'to': msg.to,
                    'content': msg.content,
                    'type': msg.type,
                    'timestamp': msg.timestamp,
                    'is_read': msg.is_read
                })
            return messages
        except Exception as e:
            print(f"[CLI] 获取MessageFailed: {e}")
            return []
    
    def send_message(self, target, content, message_type='private'):
        """SendMessage"""
        try:
            channel, stub = self._get_villager_stub()
            response = stub.SendMessage(town_pb2.SendMessageRequest(
                target=target,
                content=content,
                type=message_type
            ))
            channel.close()
            
            if response.success:
                print(f"\n✓ {response.message}")
                if message_type == 'private':
                    print(f"  Send给: {target}")
                else:
                    print(f"  BroadcastMessage")
            else:
                print(f"\n✗ {response.message}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def display_messages(self):
        """显示Message列表"""
        messages = self.get_messages()
        
        if not messages:
            print("\n📭 没有Message")
            return
        
        print("\n" + "="*50)
        print("  Message列表")
        print("="*50)
        
        for msg in messages:
            status = "✓" if msg['is_read'] else "●"
            
            # 格式化Time戳
            import datetime
            timestamp = msg['timestamp']
            if timestamp:
                try:
                    # 将Time戳转换为可读格式
                    dt = datetime.datetime.fromtimestamp(timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = f"Time戳: {timestamp}"
            else:
                time_str = "未知Time"
            
            print(f"\n{status} [{msg['message_id']}] - {time_str}")
            print(f"  来自: {msg['from']}")
            print(f"  内容: {msg['content']}")
            if msg['type'] == 'private':
                print(f"  Send给: {msg['to']}")
            else:
                print(f"  类型: Broadcast")
            print()
        
        print("="*50)
    
    def mark_messages_read(self, message_id=None):
        """标记Message为已读"""
        try:
            my_node_id = self.get_node_id()
            
            channel, stub = self._get_villager_stub()
            response = stub.MarkMessagesRead(town_pb2.MarkMessagesReadRequest(
                node_id=my_node_id,
                message_id=message_id or ""
            ))
            channel.close()
            
            if response.success:
                print(f"\n✓ {response.message}")
            else:
                print(f"\n✗ {response.message}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
        """获取MerchantPrice"""
        try:
            channel, stub = self._get_merchant_stub()
            prices = stub.GetPrices(town_pb2.Empty())
            channel.close()
            
            print("\n" + "="*50)
            print("  MerchantPrice表")
            print("="*50)
            print("\n【MerchantSell】(你可以Buy)")
            for price_info in prices.buy_prices:
                print(f"  {price_info.item:15s} : {price_info.price:4d} 金币")
            
            print("\n【Merchant收购】(你可以Sell)")
            for price_info in prices.sell_prices:
                print(f"  {price_info.item:15s} : {price_info.price:4d} 金币")
            print("="*50 + "\n")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def show_help(self):
        """显示帮助"""
        print("\n" + "="*70)
        print("  可用命令")
        print("="*70)
        print("\n【Villager管理】")
        print("  create          - CreateVillager")
        print("  info            - 查看我的Info")
        print("")
        print("【Production与生活】")
        print("  produce         - ExecuteProduction")
        print("  sleep           - Sleep")
        print("")
        print("【MerchantTrade】")
        print("  price           - 查看MerchantPrice表")
        print("  buy <item> <qty>   - 从MerchantBuyItem")
        print("  sell <item> <qty>  - 向MerchantSellItem")
        print("")
        print("【VillagerTrade】")
        print("  nodes           - 查看在线Villager")
        print("  trade <node_id> <buy/sell> <item> <qty> <price>")
        print("                  - 向Villager发起Trade")
        print("  mytrades        - 查看我的所有Trade（Send的和收到的）")
        print("  accept <trade_id>  - AcceptTrade请求")
        print("  reject <trade_id>  - RejectTrade请求")
        print("  confirm <trade_id> - ConfirmTrade")
        print("  cancel <trade_id>  - CancelTrade")
        
        print("\nMessage系统:")
        print("  messages          - 查看Message列表")
        print("  send <node> <内容> - Send私聊Message")
        print("  broadcast <内容>   - SendBroadcastMessage")
        print("  read [msg_id]      - 标记Message为已读")
        
        print("\n【Time管理】")
        print("  time            - 查看当前Time")
        print("  advance         - AdvanceTime(需要Coordinator)")
        print("")
        print("【其他】")
        print("  help            - 显示此帮助")
        print("  exit/quit       - 退出")
        print("="*70 + "\n")
    
    def run(self):
        """运行交互式循环"""
        print("\n" + "="*70)
        print("  VillagerNode交互式CLI (gRPC版本)")
        print("="*70)
        print(f"Connecting to: {self.villager_address}")
        print(f"Coordinator: {self.coordinator_address}")
        print(f"Merchant: {self.merchant_address}")
        print("="*70)
        
        # 检查连接
        if not self.check_connection():
            print("\n⚠ Warning: 无法Connecting toVillagerNode")
            print("请确保VillagerNode正在运行\n")
        
        self.show_help()
        
        while True:
            try:
                cmd = input(f"[{self.get_current_time()}] > ").strip()
                
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
                    print("\nCreateVillager")
                    name = input("名字: ").strip()
                    print("职业选择: farmer (Farmer), carpenter (木匠), chef (Chef)")
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
                    print(f"\n当前Time: {self.get_current_time()}")
                
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
                        print(f"\n✗ Error: {e}")
                
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
                
                # Message系统命令
                elif action in ['messages', 'msgs']:
                    self.display_messages()
                
                # Send私聊Message
                elif action == 'send' and len(parts) >= 3:
                    target = parts[1]
                    content = ' '.join(parts[2:])
                    self.send_message(target, content, 'private')
                
                # SendBroadcastMessage
                elif action == 'broadcast' and len(parts) >= 2:
                    content = ' '.join(parts[1:])
                    self.send_message('', content, 'broadcast')
                
                # 标记Message为已读
                elif action == 'read':
                    if len(parts) >= 2:
                        self.mark_messages_read(parts[1])
                    else:
                        self.mark_messages_read()
                
                else:
                    print(f"未知命令: {action}")
                    print("输入 'help' 查看可用命令")
            
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\n✗ Error: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='VillagerNode交互式CLI (gRPC)')
    parser.add_argument('--port', type=int, required=True, help='VillagerNode端口')
    parser.add_argument('--coordinator', type=int, default=50051, help='Coordinator端口')
    parser.add_argument('--merchant', type=int, default=50052, help='Merchant端口')
    args = parser.parse_args()
    
    cli = VillagerCLI(args.port, args.coordinator, args.merchant)
    cli.run()


if __name__ == '__main__':
    main()
