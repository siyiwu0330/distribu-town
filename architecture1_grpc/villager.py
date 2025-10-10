"""
村民节点 - Architecture 1 (gRPC)
每个村民作为独立的微服务节点
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
from common.models import (
    Villager, Occupation, Gender, Inventory,
    PRODUCTION_RECIPES, MERCHANT_PRICES,
    SLEEP_STAMINA, NO_SLEEP_PENALTY
)


class VillagerNodeService(town_pb2_grpc.VillagerNodeServicer):
    """村民节点服务"""
    
    def __init__(self, node_id):
        self.node_id = node_id
        self.villager = None
        self.merchant_address = 'localhost:50052'
        print(f"[Villager-{node_id}] 节点初始化")
    
    def CreateVillager(self, request, context):
        """创建/初始化村民"""
        try:
            occupation = Occupation(request.occupation)
            gender = Gender(request.gender)
            
            self.villager = Villager(
                name=request.name,
                occupation=occupation,
                gender=gender,
                personality=request.personality
            )
            
            print(f"[Villager-{self.node_id}] 创建村民: {self.villager.name}")
            print(f"  职业: {self.villager.occupation.value}")
            print(f"  性别: {self.villager.gender.value}")
            print(f"  性格: {self.villager.personality}")
            print(f"  体力: {self.villager.stamina}/{self.villager.max_stamina}")
            print(f"  货币: {self.villager.inventory.money}")
            
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
        """获取村民信息"""
        if not self.villager:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details('Villager not initialized')
            return town_pb2.VillagerInfo()
        
        # 转换库存
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
        """执行生产"""
        if not self.villager:
            return town_pb2.Status(success=False, message="Villager not initialized")
        
        # 获取生产配方
        recipe = PRODUCTION_RECIPES.get(self.villager.occupation)
        if not recipe:
            return town_pb2.Status(
                success=False,
                message=f"职业 {self.villager.occupation.value} 没有生产配方"
            )
        
        # 检查是否有足够资源
        if not recipe.can_produce(self.villager.inventory, self.villager.stamina):
            missing_items = []
            for item, qty in recipe.input_items.items():
                if not self.villager.inventory.has_item(item, qty):
                    have = self.villager.inventory.items.get(item, 0)
                    missing_items.append(f"{item} (需要{qty}, 拥有{have})")
            
            if self.villager.stamina < recipe.stamina_cost:
                missing_items.append(f"体力不足 (需要{recipe.stamina_cost}, 剩余{self.villager.stamina})")
            
            return town_pb2.Status(
                success=False,
                message=f"资源不足: {', '.join(missing_items)}"
            )
        
        # 消耗资源
        for item, quantity in recipe.input_items.items():
            self.villager.inventory.remove_item(item, quantity)
        
        self.villager.consume_stamina(recipe.stamina_cost)
        
        # 生产产出
        self.villager.inventory.add_item(recipe.output_item, recipe.output_quantity)
        
        print(f"[Villager-{self.node_id}] {self.villager.name} 生产了 {recipe.output_quantity}x {recipe.output_item}")
        print(f"  消耗体力: {recipe.stamina_cost}, 剩余: {self.villager.stamina}")
        
        return town_pb2.Status(
            success=True,
            message=f"生产成功: {recipe.output_quantity}x {recipe.output_item}"
        )
    
    def Trade(self, request, context):
        """执行交易
        现在统一使用中心化交易系统
        """
        if not self.villager:
            return town_pb2.Status(success=False, message="Villager not initialized")
        
        target_node = request.target_node
        item = request.item
        quantity = request.quantity
        price = request.price
        
        # 如果是与商人交易（保持旧逻辑兼容）
        if target_node == 'merchant':
            # 判断是buy还是sell（price==0表示buy）
            action = 'buy' if price == 0 else 'sell'
            return self._trade_with_merchant(item, quantity, action, context)
        else:
            # 村民间交易暂未实现（需要前端支持）
            return town_pb2.Status(
                success=False,
                message="村民间交易请使用交互式CLI或AI Agent"
            )
    
    def _trade_with_merchant(self, item, quantity, action, context):
        """与商人交易
        action: 'buy' 或 'sell'
        """
        try:
            channel = grpc.insecure_channel(self.merchant_address)
            stub = town_pb2_grpc.MerchantNodeStub(channel)
            
            if action == 'buy':
                # 从商人处购买
                if item not in MERCHANT_PRICES['buy']:
                    return town_pb2.Status(success=False, message=f"商人不出售 {item}")
                
                total_cost = MERCHANT_PRICES['buy'][item] * quantity
                
                if not self.villager.inventory.remove_money(total_cost):
                    return town_pb2.Status(
                        success=False,
                        message=f"货币不足 (需要{total_cost}, 拥有{self.villager.inventory.money})"
                    )
                
                # 调用商人服务
                response = stub.BuyItem(town_pb2.BuyFromMerchantRequest(
                    buyer_id=self.node_id,
                    item=item,
                    quantity=quantity
                ))
                
                if response.success:
                    self.villager.inventory.add_item(item, quantity)
                    print(f"[Villager-{self.node_id}] {self.villager.name} 从商人处购买 {quantity}x {item}, 花费 {total_cost}")
                    return town_pb2.Status(
                        success=True,
                        message=f"购买成功: {quantity}x {item}, 花费 {total_cost}"
                    )
                else:
                    # 退款
                    self.villager.inventory.add_money(total_cost)
                    return response
            
            elif action == 'sell':
                # 出售给商人
                if item not in MERCHANT_PRICES['sell']:
                    return town_pb2.Status(success=False, message=f"商人不收购 {item}")
                
                if not self.villager.inventory.has_item(item, quantity):
                    return town_pb2.Status(
                        success=False,
                        message=f"物品不足: {item} (需要{quantity})"
                    )
                
                total_income = MERCHANT_PRICES['sell'][item] * quantity
                
                # 调用商人服务
                response = stub.SellItem(town_pb2.SellToMerchantRequest(
                    seller_id=self.node_id,
                    item=item,
                    quantity=quantity
                ))
                
                if response.success:
                    self.villager.inventory.remove_item(item, quantity)
                    self.villager.inventory.add_money(total_income)
                    print(f"[Villager-{self.node_id}] {self.villager.name} 向商人出售 {quantity}x {item}, 获得 {total_income}")
                    return town_pb2.Status(
                        success=True,
                        message=f"出售成功: {quantity}x {item}, 获得 {total_income}"
                    )
                else:
                    return response
            
            channel.close()
            
        except Exception as e:
            return town_pb2.Status(
                success=False,
                message=f"交易失败: {str(e)}"
            )
    
    def Sleep(self, request, context):
        """睡眠"""
        if not self.villager:
            return town_pb2.Status(success=False, message="Villager not initialized")
        
        if self.villager.has_slept:
            return town_pb2.Status(success=False, message="今天已经睡过了")
        
        # 检查是否有房子或临时房间券
        has_house = self.villager.inventory.has_item("house", 1)
        has_temp_room = self.villager.inventory.has_item("temp_room", 1)
        
        if not has_house and not has_temp_room:
            return town_pb2.Status(
                success=False,
                message="没有房子或临时房间券，无法睡眠。请从商人处购买临时房间券或建造房子。"
            )
        
        # 预处理睡眠（恢复在这里执行）
        sleep_message = ""
        if has_house:
            sleep_message = "在自己的房子里睡眠"
        else:  # has_temp_room
            sleep_message = "使用临时房间券睡眠（将在每日结算时消耗）"
        
        # 恢复体力
        self.villager.restore_stamina(SLEEP_STAMINA)
        self.villager.has_slept = True
        
        print(f"[Villager-{self.node_id}] {self.villager.name} {sleep_message}，恢复体力 {SLEEP_STAMINA}")
        print(f"  当前体力: {self.villager.stamina}/{self.villager.max_stamina}")
        
        return town_pb2.Status(
            success=True,
            message=f"睡眠成功，恢复体力 {SLEEP_STAMINA}。{sleep_message}。"
        )
    
    def OnTimeAdvance(self, request, context):
        """时间推进通知"""
        if not self.villager:
            return town_pb2.Status(success=True, message="No villager")
        
        new_time = request.new_time
        print(f"[Villager-{self.node_id}] 时间推进: Day {new_time.day} {new_time.time_of_day}")
        
        # 如果是新的一天（早晨）
        if new_time.time_of_day == 'morning':
            # 如果前一天晚上没睡觉，额外扣除体力
            if not self.villager.has_slept:
                self.villager.consume_stamina(NO_SLEEP_PENALTY)
                print(f"[Villager-{self.node_id}] {self.villager.name} 昨晚没睡觉，额外消耗 {NO_SLEEP_PENALTY} 体力")
            
            # 每日重置
            self.villager.reset_daily()
            print(f"[Villager-{self.node_id}] 新的一天！")
            print(f"  体力: {self.villager.stamina}/{self.villager.max_stamina}")
        
        return town_pb2.Status(success=True, message="Time updated")
    
    def TradeExecute(self, request, context):
        """交易执行（原子操作）"""
        if not self.villager:
            return town_pb2.Status(success=False, message="Villager not initialized")
        
        action = request.action
        
        try:
            if action == 'pay':
                # 支付货币
                money = request.money
                if not self.villager.inventory.remove_money(money):
                    return town_pb2.Status(success=False, message=f"货币不足")
                print(f"[Villager-{self.node_id}] 支付 {money} 货币")
                return town_pb2.Status(success=True, message="Payment success")
            
            elif action == 'refund':
                # 退款
                money = request.money
                self.villager.inventory.add_money(money)
                print(f"[Villager-{self.node_id}] 退款 {money} 货币")
                return town_pb2.Status(success=True, message="Refund success")
            
            elif action == 'add_item':
                # 添加物品
                item = request.item
                quantity = request.quantity
                self.villager.inventory.add_item(item, quantity)
                print(f"[Villager-{self.node_id}] 获得 {quantity}x {item}")
                return town_pb2.Status(success=True, message="Item added")
            
            elif action == 'remove_item':
                # 移除物品
                item = request.item
                quantity = request.quantity
                if not self.villager.inventory.has_item(item, quantity):
                    return town_pb2.Status(success=False, message=f"物品不足: {item}")
                self.villager.inventory.remove_item(item, quantity)
                print(f"[Villager-{self.node_id}] 移除 {quantity}x {item}")
                return town_pb2.Status(success=True, message="Item removed")
            
            elif action == 'receive':
                # 收款
                money = request.money
                self.villager.inventory.add_money(money)
                print(f"[Villager-{self.node_id}] 收到 {money} 货币")
                return town_pb2.Status(success=True, message="Money received")
            
            else:
                return town_pb2.Status(success=False, message=f"Unknown action: {action}")
        
        except Exception as e:
            return town_pb2.Status(success=False, message=f"Execute failed: {str(e)}")


def serve(port, node_id, coordinator_addr='localhost:50051'):
    """启动村民服务器"""
    # 启动gRPC服务器
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    town_pb2_grpc.add_VillagerNodeServicer_to_server(
        VillagerNodeService(node_id), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"[Villager-{node_id}] 村民节点启动在端口 {port}")
    
    # 注册到协调器
    try:
        channel = grpc.insecure_channel(coordinator_addr)
        stub = town_pb2_grpc.TimeCoordinatorStub(channel)
        
        response = stub.RegisterNode(town_pb2.RegisterNodeRequest(
            node_id=node_id,
            node_type='villager',
            address=f'localhost:{port}'
        ))
        
        if response.success:
            print(f"[Villager-{node_id}] 成功注册到协调器: {coordinator_addr}")
        else:
            print(f"[Villager-{node_id}] 注册失败: {response.message}")
        
        channel.close()
    except Exception as e:
        print(f"[Villager-{node_id}] 无法连接到协调器 {coordinator_addr}: {e}")
    
    print(f"[Villager-{node_id}] 使用 Ctrl+C 停止服务器")
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print(f"\n[Villager-{node_id}] 关闭服务器...")
        server.stop(0)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='村民节点服务')
    parser.add_argument('--port', type=int, required=True, help='监听端口')
    parser.add_argument('--id', type=str, required=True, help='节点ID')
    parser.add_argument('--coordinator', type=str, default='localhost:50051',
                       help='协调器地址')
    args = parser.parse_args()
    
    serve(args.port, args.id, args.coordinator)

