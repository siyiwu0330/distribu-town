"""
VillagerNode - Architecture 1 (gRPC)
每个Villager作为独立的微服务Node
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
from common.models import (
    Villager, Occupation, Gender, Inventory,
    PRODUCTION_RECIPES, MERCHANT_PRICES,
    SLEEP_STAMINA, NO_SLEEP_PENALTY
)


class VillagerNodeService(town_pb2_grpc.VillagerNodeServicer):
    """VillagerNode服务"""
    
    def __init__(self, node_id):
        self.node_id = node_id
        self.villager = None
        self.merchant_address = 'localhost:50052'
        
        # Message系统 - 简单存储
        self.messages = []  # 存储Message
        self.message_counter = 0
        
        print(f"[Villager-{node_id}] Node初始化")
    
    def CreateVillager(self, request, context):
        """Create/初始化Villager"""
        try:
            occupation = Occupation(request.occupation)
            gender = Gender(request.gender)
            
            self.villager = Villager(
                name=request.name,
                occupation=occupation,
                gender=gender,
                personality=request.personality
            )
            
            print(f"[Villager-{self.node_id}] CreateVillager: {self.villager.name}")
            print(f"  职业: {self.villager.occupation.value}")
            print(f"  性别: {self.villager.gender.value}")
            print(f"  性格: {self.villager.personality}")
            print(f"  Stamina: {self.villager.stamina}/{self.villager.max_stamina}")
            print(f"  Money: {self.villager.inventory.money}")
            
            return town_pb2.Status(
                success=True,
                message=f"Villager {self.villager.name} created successfully"
            )
        except Exception as e:
            return town_pb2.Status(
                success=False,
                message=f"Failed to create villager: {str(e)}"
            )
    
    def GetInfo(self, request, context):
        """GetVillagerinformation"""
        if not self.villager:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details('Villager not initialized')
            return town_pb2.VillagerInfo()
        
        # 转换Inventory
        inventory = town_pb2.Inventory(
            money=self.villager.inventory.money,
            items=self.villager.inventory.items
        )
        
        return town_pb2.VillagerInfo(
            name=self.villager.name,
            occupation=self.villager.occupation.value,
            gender=self.villager.gender.value,
            personality=self.villager.personality,
            stamina=self.villager.stamina,
            max_stamina=self.villager.max_stamina,
            inventory=inventory,
            action_points=0,  # gRPC版本不使用action系统
            has_slept=self.villager.has_slept
        )
    
    def Produce(self, request, context):
        """ExecuteProduction"""
        if not self.villager:
            return town_pb2.Status(success=False, message="Villager not initialized")
        
        # 获取Production配方
        recipe = PRODUCTION_RECIPES.get(self.villager.occupation)
        if not recipe:
            return town_pb2.Status(
                success=False,
                message=f"职业 {self.villager.occupation.value} 没有Production配方"
            )
        
        # 检查是否有足够资源
        if not recipe.can_produce(self.villager.inventory, self.villager.stamina):
            missing_items = []
            for item, qty in recipe.input_items.items():
                if not self.villager.inventory.has_item(item, qty):
                    have = self.villager.inventory.items.get(item, 0)
                    missing_items.append(f"{item} (需要{qty}, 拥有{have})")
            
            if self.villager.stamina < recipe.stamina_cost:
                missing_items.append(f"Stamina不足 (需要{recipe.stamina_cost}, 剩余{self.villager.stamina})")
            
            return town_pb2.Status(
                success=False,
                message=f"资源不足: {', '.join(missing_items)}"
            )
        
        # 消耗资源
        for item, quantity in recipe.input_items.items():
            self.villager.inventory.remove_item(item, quantity)
        
        self.villager.consume_stamina(recipe.stamina_cost)
        
        # Production产出
        self.villager.inventory.add_item(recipe.output_item, recipe.output_quantity)
        
        print(f"[Villager-{self.node_id}] {self.villager.name} Production了 {recipe.output_quantity}x {recipe.output_item}")
        print(f"  消耗Stamina: {recipe.stamina_cost}, 剩余: {self.villager.stamina}")
        
        return town_pb2.Status(
            success=True,
            message=f"ProductionSuccess: {recipe.output_quantity}x {recipe.output_item}"
        )
    
    def Trade(self, request, context):
        """ExecuteTrade
        现在统一使用中心化Trade系统
        """
        if not self.villager:
            return town_pb2.Status(success=False, message="Villager not initialized")
        
        target_node = request.target_node
        item = request.item
        quantity = request.quantity
        price = request.price
        
        # 如果是与MerchantTrade（保持旧逻辑兼容）
        if target_node == 'merchant':
            # 判断是buy还是sell（price==0表示buy）
            action = 'buy' if price == 0 else 'sell'
            return self._trade_with_merchant(item, quantity, action, context)
        else:
            # Villager间Trade暂未实现（需要前端支持）
            return town_pb2.Status(
                success=False,
                message="Villager间Trade请使用交互式CLI或AI Agent"
            )
    
    def _trade_with_merchant(self, item, quantity, action, context):
        """与MerchantTrade
        action: 'buy' 或 'sell'
        """
        try:
            channel = grpc.insecure_channel(self.merchant_address)
            stub = town_pb2_grpc.MerchantNodeStub(channel)
            
            if action == 'buy':
                # 从Merchant处Buy
                if item not in MERCHANT_PRICES['buy']:
                    return town_pb2.Status(success=False, message=f"Merchant不Sell {item}")
                
                total_cost = MERCHANT_PRICES['buy'][item] * quantity
                
                if not self.villager.inventory.remove_money(total_cost):
                    return town_pb2.Status(
                        success=False,
                        message=f"Money不足 (需要{total_cost}, 拥有{self.villager.inventory.money})"
                    )
                
                # 调用Merchant服务
                response = stub.BuyItem(town_pb2.BuyFromMerchantRequest(
                    buyer_id=self.node_id,
                    item=item,
                    quantity=quantity
                ))
                
                if response.success:
                    self.villager.inventory.add_item(item, quantity)
                    print(f"[Villager-{self.node_id}] {self.villager.name} 从Merchant处Buy {quantity}x {item}, 花费 {total_cost}")
                    return town_pb2.Status(
                        success=True,
                        message=f"BuySuccess: {quantity}x {item}, 花费 {total_cost}"
                    )
                else:
                    # 退款
                    self.villager.inventory.add_money(total_cost)
                    return response
            
            elif action == 'sell':
                # Sell给Merchant
                if item not in MERCHANT_PRICES['sell']:
                    return town_pb2.Status(success=False, message=f"Merchant不收购 {item}")
                
                if not self.villager.inventory.has_item(item, quantity):
                    return town_pb2.Status(
                        success=False,
                        message=f"Item不足: {item} (需要{quantity})"
                    )
                
                total_income = MERCHANT_PRICES['sell'][item] * quantity
                
                # 调用Merchant服务
                response = stub.SellItem(town_pb2.SellToMerchantRequest(
                    seller_id=self.node_id,
                    item=item,
                    quantity=quantity
                ))
                
                if response.success:
                    self.villager.inventory.remove_item(item, quantity)
                    self.villager.inventory.add_money(total_income)
                    print(f"[Villager-{self.node_id}] {self.villager.name} 向MerchantSell {quantity}x {item}, 获得 {total_income}")
                    return town_pb2.Status(
                        success=True,
                        message=f"SellSuccess: {quantity}x {item}, 获得 {total_income}"
                    )
                else:
                    return response
            
            channel.close()
            
        except Exception as e:
            return town_pb2.Status(
                success=False,
                message=f"TradeFailed: {str(e)}"
            )
    
    def Sleep(self, request, context):
        """Sleep"""
        if not self.villager:
            return town_pb2.Status(success=False, message="Villager not initialized")
        
        if self.villager.has_slept:
            return town_pb2.Status(success=False, message="今天已经睡过了")
        
        # 检查是否有房子或临时Room voucher
        has_house = self.villager.inventory.has_item("house", 1)
        has_temp_room = self.villager.inventory.has_item("temp_room", 1)
        
        if not has_house and not has_temp_room:
            return town_pb2.Status(
                success=False,
                message="没有房子或临时Room voucher，无法Sleep。请从Merchant处Buy临时Room voucher或建造房子。"
            )
        
        # 预HandleSleep（恢复在这里Execute）
        sleep_message = ""
        if has_house:
            sleep_message = "在自己的房子里Sleep"
        else:  # has_temp_room
            sleep_message = "使用临时Room voucherSleep（将在每日结算时消耗）"
        
        # 恢复Stamina
        self.villager.restore_stamina(SLEEP_STAMINA)
        self.villager.has_slept = True
        
        print(f"[Villager-{self.node_id}] {self.villager.name} {sleep_message}，恢复Stamina {SLEEP_STAMINA}")
        print(f"  当前Stamina: {self.villager.stamina}/{self.villager.max_stamina}")
        
        return town_pb2.Status(
            success=True,
            message=f"SleepSuccess，恢复Stamina {SLEEP_STAMINA}。{sleep_message}。"
        )
    
    def OnTimeAdvance(self, request, context):
        """TimeAdvanceNotify"""
        if not self.villager:
            return town_pb2.Status(success=True, message="No villager")
        
        new_time = request.new_time
        print(f"[Villager-{self.node_id}] TimeAdvance: Day {new_time.day} {new_time.time_of_day}")
        
        # 如果是新的一天（早晨）
        if new_time.time_of_day == 'morning':
            # 如果前一天Evening没睡觉，额外扣除Stamina
            if not self.villager.has_slept:
                self.villager.consume_stamina(NO_SLEEP_PENALTY)
                print(f"[Villager-{self.node_id}] {self.villager.name} 昨晚没睡觉，额外消耗 {NO_SLEEP_PENALTY} Stamina")
            
            # 每日重置
            self.villager.reset_daily()
            print(f"[Villager-{self.node_id}] 新的一天！")
            print(f"  Stamina: {self.villager.stamina}/{self.villager.max_stamina}")
        
        return town_pb2.Status(success=True, message="Time updated")
    
    def TradeExecute(self, request, context):
        """TradeExecute（原子操作）"""
        if not self.villager:
            return town_pb2.Status(success=False, message="Villager not initialized")
        
        action = request.action
        
        try:
            if action == 'pay':
                # 支付Money
                money = request.money
                if not self.villager.inventory.remove_money(money):
                    return town_pb2.Status(success=False, message=f"Money不足")
                print(f"[Villager-{self.node_id}] 支付 {money} Money")
                return town_pb2.Status(success=True, message="Payment success")
            
            elif action == 'refund':
                # 退款
                money = request.money
                self.villager.inventory.add_money(money)
                print(f"[Villager-{self.node_id}] 退款 {money} Money")
                return town_pb2.Status(success=True, message="Refund success")
            
            elif action == 'add_item':
                # 添加Item
                item = request.item
                quantity = request.quantity
                self.villager.inventory.add_item(item, quantity)
                print(f"[Villager-{self.node_id}] 获得 {quantity}x {item}")
                return town_pb2.Status(success=True, message="Item added")
            
            elif action == 'remove_item':
                # 移除Item
                item = request.item
                quantity = request.quantity
                if not self.villager.inventory.has_item(item, quantity):
                    return town_pb2.Status(success=False, message=f"Item不足: {item}")
                self.villager.inventory.remove_item(item, quantity)
                print(f"[Villager-{self.node_id}] 移除 {quantity}x {item}")
                return town_pb2.Status(success=True, message="Item removed")
            
            elif action == 'receive':
                # 收款
                money = request.money
                self.villager.inventory.add_money(money)
                print(f"[Villager-{self.node_id}] 收到 {money} Money")
                return town_pb2.Status(success=True, message="Money received")
            
            else:
                return town_pb2.Status(success=False, message=f"Unknown action: {action}")
        
        except Exception as e:
            return town_pb2.Status(success=False, message=f"Execute failed: {str(e)}")
    
    def SendMessage(self, request, context):
        """SendMessage"""
        try:
            if not self.villager:
                return town_pb2.SendMessageResponse(
                    success=False, 
                    message="Villager未初始化"
                )
            
            import time
            self.message_counter += 1
            message_id = f"msg_{self.message_counter}"
            
            # 如果是BroadcastMessage
            if request.type == 'broadcast':
                # Send给所有在线VillagerNode
                sent_count = 0
                try:
                    import town_pb2_grpc
                    import grpc
                    
                    # Connecting tocoordinator获取所有在线Villager
                    coordinator_channel = grpc.insecure_channel('localhost:50051')
                    coordinator_stub = town_pb2_grpc.TimeCoordinatorStub(coordinator_channel)
                    
                    nodes_response = coordinator_stub.ListNodes(town_pb2.Empty())
                    coordinator_channel.close()
                    
                    # Send给所有VillagerNode
                    for node in nodes_response.nodes:
                        if node.node_type == 'villager' and node.node_id != self.node_id:
                            try:
                                # Connecting to目标VillagerNode
                                target_channel = grpc.insecure_channel(node.address)
                                target_stub = town_pb2_grpc.VillagerNodeStub(target_channel)
                                
                                # 调用目标Node的ReceiveMessage方法
                                receive_request = town_pb2.ReceiveMessageRequest(
                                    content=request.content,
                                    type='broadcast',
                                    timestamp=int(time.time())
                                )
                                # Setfrom字段（因为from是Python关键字）
                                setattr(receive_request, 'from', self.node_id)
                                response = target_stub.ReceiveMessage(receive_request)
                                
                                if response.success:
                                    sent_count += 1
                                
                                target_channel.close()
                            except Exception as e:
                                print(f"[Villager-{self.node_id}] SendBroadcastMessage到 {node.node_id} Failed: {e}")
                                continue
                    
                    print(f"[Villager-{self.node_id}] BroadcastMessageSend给 {sent_count} 个Node")
                    
                except Exception as e:
                    print(f"[Villager-{self.node_id}] 获取在线VillagerFailed: {e}")
                
            else:
                # P2PMessage，Send给指定目标
                try:
                    import town_pb2_grpc
                    import grpc
                    
                    # Connecting tocoordinator获取目标Villager地址
                    coordinator_channel = grpc.insecure_channel('localhost:50051')
                    coordinator_stub = town_pb2_grpc.TimeCoordinatorStub(coordinator_channel)
                    
                    nodes_response = coordinator_stub.ListNodes(town_pb2.Empty())
                    coordinator_channel.close()
                    
                    # 查找目标Villager
                    target_address = None
                    for node in nodes_response.nodes:
                        if node.node_id == request.target:
                            target_address = node.address
                            break
                    
                    if target_address:
                        # Send给目标Villager
                        try:
                            target_channel = grpc.insecure_channel(target_address)
                            target_stub = town_pb2_grpc.VillagerNodeStub(target_channel)
                            
                            # 调用目标Node的ReceiveMessage方法
                            receive_request = town_pb2.ReceiveMessageRequest(
                                content=request.content,
                                type='private',
                                timestamp=int(time.time())
                            )
                            # Setfrom字段（因为from是Python关键字）
                            setattr(receive_request, 'from', self.node_id)
                            response = target_stub.ReceiveMessage(receive_request)
                            
                            if response.success:
                                print(f"[Villager-{self.node_id}] P2PMessageSend给 {request.target}")
                            else:
                                return town_pb2.SendMessageResponse(
                                    success=False,
                                    message=f"SendFailed: {response.message}"
                                )
                            
                            target_channel.close()
                        except Exception as e:
                            return town_pb2.SendMessageResponse(
                                success=False,
                                message=f"SendFailed: {str(e)}"
                            )
                    else:
                        return town_pb2.SendMessageResponse(
                            success=False,
                            message=f"找不到目标Villager: {request.target}"
                        )
                        
                except Exception as e:
                    return town_pb2.SendMessageResponse(
                        success=False,
                        message=f"SendFailed: {str(e)}"
                    )
            
            return town_pb2.SendMessageResponse(
                success=True,
                message="MessageSendSuccess",
                message_id=message_id
            )
            
        except Exception as e:
            return town_pb2.SendMessageResponse(
                success=False,
                message=f"SendMessageFailed: {str(e)}"
            )
    
    def ReceiveMessage(self, request, context):
        """ReceiveMessage（由其他VillagerNode调用）"""
        try:
            if not self.villager:
                return town_pb2.ReceiveMessageResponse(
                    success=False, 
                    message="Villager未初始化"
                )
            
            import time
            self.message_counter += 1
            message_id = f"rcv_{self.message_counter}"
            
            # CreateReceive到的Message
            from_field = getattr(request, 'from', 'unknown')
            message = {
                'message_id': message_id,
                'from': from_field,
                'to': self.node_id,
                'content': request.content,
                'type': request.type,
                'timestamp': request.timestamp,
                'is_read': False
            }
            
            # 存储到Message列表
            self.messages.append(message)
            
            print(f"[Villager-{self.node_id}] 收到Message: {request.type} from {from_field}: {request.content}")
            
            return town_pb2.ReceiveMessageResponse(
                success=True,
                message="MessageReceiveSuccess"
            )
            
        except Exception as e:
            return town_pb2.ReceiveMessageResponse(
                success=False,
                message=f"ReceiveMessageFailed: {str(e)}"
            )
    
    def GetMessages(self, request, context):
        """获取Message列表"""
        try:
            if not self.villager:
                return town_pb2.GetMessagesResponse(messages=[])
            
            # 返回所有Message
            proto_messages = []
            for msg in self.messages:
                proto_msg = town_pb2.Message(
                    message_id=msg['message_id'],
                    to=msg['to'],
                    content=msg['content'],
                    type=msg['type'],
                    timestamp=msg['timestamp'],
                    is_read=msg['is_read']
                )
                # Setfrom字段（因为from是Python关键字）
                setattr(proto_msg, 'from', msg['from'])
                proto_messages.append(proto_msg)
            
            return town_pb2.GetMessagesResponse(messages=proto_messages)
            
        except Exception as e:
            return town_pb2.GetMessagesResponse(messages=[])
    


def serve(port, node_id, coordinator_addr='localhost:50051'):
    """启动Villager服务器"""
    # 启动gRPC服务器
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    villager_service = VillagerNodeService(node_id)
    town_pb2_grpc.add_VillagerNodeServicer_to_server(villager_service, server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"[Villager-{node_id}] VillagerNodestarting on port {port}")
    
    # Register to coordinator
    try:
        channel = grpc.insecure_channel(coordinator_addr)
        stub = town_pb2_grpc.TimeCoordinatorStub(channel)
        
        response = stub.RegisterNode(town_pb2.RegisterNodeRequest(
            node_id=node_id,
            node_type='villager',
            address=f'localhost:{port}'
        ))
        
        if response.success:
            print(f"[Villager-{node_id}] SuccessRegister to coordinator: {coordinator_addr}")
        else:
            print(f"[Villager-{node_id}] Registration failed: {response.message}")
        
        channel.close()
    except Exception as e:
        print(f"[Villager-{node_id}] 无法Connecting toCoordinator {coordinator_addr}: {e}")
    
    # 使用纯gRPCMessage系统
    print(f"[Villager-{node_id}] 使用纯gRPCMessage系统，无需HTTP服务器")
    
    print(f"[Villager-{node_id}] 使用 Ctrl+C 停止服务器")
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print(f"\n[Villager-{node_id}] 关闭服务器...")
        server.stop(0)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='VillagerNode服务')
    parser.add_argument('--port', type=int, required=True, help='监听端口')
    parser.add_argument('--id', type=str, required=True, help='NodeID')
    parser.add_argument('--coordinator', type=str, default='localhost:50051',
                       help='Coordinator地址')
    args = parser.parse_args()
    
    serve(args.port, args.id, args.coordinator)

