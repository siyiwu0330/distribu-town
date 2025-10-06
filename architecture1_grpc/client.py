"""
交互式客户端 - Architecture 1 (gRPC)
用于控制和测试分布式虚拟小镇系统
"""

import grpc
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from proto import town_pb2
from proto import town_pb2_grpc


class TownClient:
    """虚拟小镇客户端"""
    
    def __init__(self, coordinator_addr='localhost:50051'):
        self.coordinator_addr = coordinator_addr
        self.merchant_addr = 'localhost:50052'
        self.villager_nodes = {}  # {node_id: address}
    
    def connect_coordinator(self):
        """连接到协调器"""
        return grpc.insecure_channel(self.coordinator_addr)
    
    def connect_merchant(self):
        """连接到商人"""
        return grpc.insecure_channel(self.merchant_addr)
    
    def connect_villager(self, node_id):
        """连接到村民节点"""
        if node_id not in self.villager_nodes:
            print(f"错误: 未知的村民节点 {node_id}")
            return None
        return grpc.insecure_channel(self.villager_nodes[node_id])
    
    def refresh_nodes(self):
        """刷新节点列表"""
        try:
            channel = self.connect_coordinator()
            stub = town_pb2_grpc.TimeCoordinatorStub(channel)
            response = stub.ListNodes(town_pb2.Empty())
            
            self.villager_nodes = {}
            for node in response.nodes:
                if node.node_type == 'villager':
                    self.villager_nodes[node.node_id] = node.address
            
            channel.close()
            print(f"已刷新节点列表，找到 {len(self.villager_nodes)} 个村民节点")
            return True
        except Exception as e:
            print(f"刷新节点列表失败: {e}")
            return False
    
    def get_current_time(self):
        """获取当前游戏时间"""
        try:
            channel = self.connect_coordinator()
            stub = town_pb2_grpc.TimeCoordinatorStub(channel)
            time = stub.GetCurrentTime(town_pb2.Empty())
            channel.close()
            return f"Day {time.day} - {time.time_of_day}"
        except Exception as e:
            return f"错误: {e}"
    
    def advance_time(self):
        """推进时间"""
        try:
            channel = self.connect_coordinator()
            stub = town_pb2_grpc.TimeCoordinatorStub(channel)
            response = stub.AdvanceTime(town_pb2.Empty())
            channel.close()
            return response.message if response.success else f"失败: {response.message}"
        except Exception as e:
            return f"错误: {e}"
    
    def create_villager(self, node_id, name, occupation, gender, personality):
        """创建村民"""
        try:
            channel = self.connect_villager(node_id)
            if not channel:
                return
            
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.CreateVillager(town_pb2.CreateVillagerRequest(
                name=name,
                occupation=occupation,
                gender=gender,
                personality=personality
            ))
            channel.close()
            
            if response.success:
                print(f"✓ 村民创建成功: {name} ({occupation})")
            else:
                print(f"✗ 创建失败: {response.message}")
        except Exception as e:
            print(f"✗ 错误: {e}")
    
    def get_villager_info(self, node_id):
        """获取村民信息"""
        try:
            channel = self.connect_villager(node_id)
            if not channel:
                return
            
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            info = stub.GetInfo(town_pb2.Empty())
            channel.close()
            
            print(f"\n=== {info.name} ===")
            print(f"职业: {info.occupation}")
            print(f"性别: {info.gender}")
            print(f"性格: {info.personality}")
            print(f"体力: {info.stamina}/{info.max_stamina}")
            print(f"行动点: {info.action_points}")
            print(f"已睡眠: {'是' if info.has_slept else '否'}")
            print(f"货币: {info.inventory.money}")
            print(f"物品: {dict(info.inventory.items) if info.inventory.items else '无'}")
            print()
        except Exception as e:
            print(f"✗ 错误: {e}")
    
    def villager_produce(self, node_id):
        """村民生产"""
        try:
            channel = self.connect_villager(node_id)
            if not channel:
                return
            
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.Produce(town_pb2.ProduceRequest())
            channel.close()
            
            if response.success:
                print(f"✓ {response.message}")
            else:
                print(f"✗ {response.message}")
        except Exception as e:
            print(f"✗ 错误: {e}")
    
    def villager_trade(self, node_id, target, item, quantity, action):
        """村民交易
        action: 'buy' 或 'sell'
        """
        try:
            channel = self.connect_villager(node_id)
            if not channel:
                return
            
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.Trade(town_pb2.TradeRequest(
                target_node=target,
                item=item,
                quantity=quantity,
                price=0  # action字段通过item传递
            ))
            channel.close()
            
            # 实际上需要修改，这里简化处理
            # 正确的做法是修改proto或villager.py的Trade方法
            
            if response.success:
                print(f"✓ {response.message}")
            else:
                print(f"✗ {response.message}")
        except Exception as e:
            print(f"✗ 错误: {e}")
    
    def villager_sleep(self, node_id):
        """村民睡眠"""
        try:
            channel = self.connect_villager(node_id)
            if not channel:
                return
            
            stub = town_pb2_grpc.VillagerNodeStub(channel)
            response = stub.Sleep(town_pb2.SleepRequest())
            channel.close()
            
            if response.success:
                print(f"✓ {response.message}")
            else:
                print(f"✗ {response.message}")
        except Exception as e:
            print(f"✗ 错误: {e}")
    
    def get_merchant_prices(self):
        """获取商人价格表"""
        try:
            channel = self.connect_merchant()
            stub = town_pb2_grpc.MerchantNodeStub(channel)
            prices = stub.GetPrices(town_pb2.Empty())
            channel.close()
            
            print("\n=== 商人价格表 ===")
            print("\n出售（商人卖给你）:")
            for price_info in prices.buy_prices:
                print(f"  {price_info.item}: {price_info.price}金币")
            
            print("\n收购（你卖给商人）:")
            for price_info in prices.sell_prices:
                print(f"  {price_info.item}: {price_info.price}金币")
            print()
        except Exception as e:
            print(f"✗ 错误: {e}")
    
    def interactive_mode(self):
        """交互式模式"""
        print("\n=== 分布式虚拟小镇 - gRPC客户端 ===")
        print("连接到协调器:", self.coordinator_addr)
        
        if not self.refresh_nodes():
            print("警告: 无法连接到协调器，某些功能可能不可用")
        
        while True:
            print("\n--- 主菜单 ---")
            print("1. 查看当前时间")
            print("2. 推进时间")
            print("3. 刷新节点列表")
            print("4. 查看商人价格表")
            print("5. 村民操作")
            print("0. 退出")
            
            choice = input("\n请选择: ").strip()
            
            if choice == '1':
                print(f"当前时间: {self.get_current_time()}")
            
            elif choice == '2':
                result = self.advance_time()
                print(f"时间推进: {result}")
            
            elif choice == '3':
                self.refresh_nodes()
                if self.villager_nodes:
                    print("村民节点:")
                    for node_id in self.villager_nodes:
                        print(f"  - {node_id}")
            
            elif choice == '4':
                self.get_merchant_prices()
            
            elif choice == '5':
                self.villager_menu()
            
            elif choice == '0':
                print("再见！")
                break
            
            else:
                print("无效选择")
    
    def villager_menu(self):
        """村民操作菜单"""
        if not self.villager_nodes:
            print("没有可用的村民节点，请先刷新节点列表")
            return
        
        print("\n可用村民:")
        node_list = list(self.villager_nodes.keys())
        for i, node_id in enumerate(node_list, 1):
            print(f"{i}. {node_id}")
        
        try:
            idx = int(input("\n选择村民 (输入序号): ").strip()) - 1
            if idx < 0 or idx >= len(node_list):
                print("无效选择")
                return
            
            node_id = node_list[idx]
        except ValueError:
            print("无效输入")
            return
        
        while True:
            print(f"\n--- {node_id} 操作菜单 ---")
            print("1. 查看信息")
            print("2. 生产")
            print("3. 从商人购买")
            print("4. 出售给商人")
            print("5. 睡眠")
            print("0. 返回")
            
            choice = input("\n请选择: ").strip()
            
            if choice == '1':
                self.get_villager_info(node_id)
            
            elif choice == '2':
                self.villager_produce(node_id)
            
            elif choice == '3':
                item = input("物品名称: ").strip()
                quantity = int(input("数量: ").strip())
                # 使用特殊格式传递buy action
                channel = self.connect_villager(node_id)
                if channel:
                    stub = town_pb2_grpc.VillagerNodeStub(channel)
                    # 直接调用内部方法（需要修改villager.py）
                    from villager import VillagerNodeService
                    # 这里简化处理，实际应该修改proto
                    print("提示：交易功能需要进一步完善")
                    channel.close()
            
            elif choice == '4':
                item = input("物品名称: ").strip()
                quantity = int(input("数量: ").strip())
                print("提示：交易功能需要进一步完善")
            
            elif choice == '5':
                self.villager_sleep(node_id)
            
            elif choice == '0':
                break
            
            else:
                print("无效选择")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='虚拟小镇gRPC客户端')
    parser.add_argument('--coordinator', type=str, default='localhost:50051',
                       help='协调器地址')
    args = parser.parse_args()
    
    client = TownClient(args.coordinator)
    client.interactive_mode()


if __name__ == '__main__':
    main()

