"""
测试场景 - Architecture 1 (gRPC)
自动化测试虚拟小镇的各项功能
"""

import grpc
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))
from proto import town_pb2
from proto import town_pb2_grpc


def wait_for_service(address, max_retries=10):
    """等待服务启动"""
    for i in range(max_retries):
        try:
            channel = grpc.insecure_channel(address)
            grpc.channel_ready_future(channel).result(timeout=1)
            channel.close()
            return True
        except:
            time.sleep(1)
    return False


def run_test_scenario():
    """运行测试场景"""
    print("\n=== 分布式虚拟小镇测试场景 ===\n")
    
    # 等待服务启动
    print("等待服务启动...")
    if not wait_for_service('localhost:50051'):
        print("✗ 无法连接到协调器")
        return
    if not wait_for_service('localhost:50052'):
        print("✗ 无法连接到商人")
        return
    if not wait_for_service('localhost:50053'):
        print("✗ 无法连接到村民节点")
        return
    
    print("✓ 所有服务已就绪\n")
    
    # 创建村民
    print("=== 场景1: 创建村民 ===")
    
    villagers = [
        ('alice', 50053, 'Alice', 'farmer', 'female', '勤劳'),
        ('bob', 50054, 'Bob', 'chef', 'male', '热情'),
        ('charlie', 50055, 'Charlie', 'carpenter', 'male', '细心'),
    ]
    
    for node_id, port, name, occupation, gender, personality in villagers:
        channel = grpc.insecure_channel(f'localhost:{port}')
        stub = town_pb2_grpc.VillagerNodeStub(channel)
        response = stub.CreateVillager(town_pb2.CreateVillagerRequest(
            name=name,
            occupation=occupation,
            gender=gender,
            personality=personality
        ))
        print(f"✓ 创建村民 {name} ({occupation}): {response.message}")
        channel.close()
        time.sleep(0.5)
    
    print()
    
    # 查看初始状态
    print("=== 场景2: 查看初始状态 ===")
    for node_id, port, name, _, _, _ in villagers:
        channel = grpc.insecure_channel(f'localhost:{port}')
        stub = town_pb2_grpc.VillagerNodeStub(channel)
        info = stub.GetInfo(town_pb2.Empty())
        print(f"{info.name}: 体力{info.stamina}, 货币{info.inventory.money}, 物品{dict(info.inventory.items)}")
        channel.close()
    print()
    
    # Alice（农夫）购买种子并种植
    print("=== 场景3: Alice（农夫）购买种子并种植 ===")
    channel = grpc.insecure_channel('localhost:50053')
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    
    # 购买5个种子
    response = stub.Trade(town_pb2.TradeRequest(
        target_node='merchant',
        item='seed',
        quantity=5,
        price=0  # 0=buy
    ))
    print(f"购买种子: {response.message}")
    
    # 种植（生产小麦）
    for i in range(3):
        response = stub.Produce(town_pb2.ProduceRequest())
        print(f"生产第{i+1}次: {response.message}")
    
    # 查看状态
    info = stub.GetInfo(town_pb2.Empty())
    print(f"Alice当前状态: 体力{info.stamina}, 货币{info.inventory.money}, 物品{dict(info.inventory.items)}")
    channel.close()
    print()
    
    # Bob（厨师）向Alice购买小麦（简化：从商人处购买）
    print("=== 场景4: Bob（厨师）购买小麦并制作面包 ===")
    channel = grpc.insecure_channel('localhost:50054')
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    
    # 购买小麦（简化场景，从商人处购买）
    # 实际上应该从Alice购买，但村民间交易未实现
    # 先让Bob通过出售初始资产获得资金，然后制作面包
    
    # 暂时跳过，因为商人不出售小麦
    print("（村民间交易未实现，跳过此场景）")
    channel.close()
    print()
    
    # Charlie（木工）购买木材并建造房屋
    print("=== 场景5: Charlie（木工）购买木材并建造房屋 ===")
    channel = grpc.insecure_channel('localhost:50055')
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    
    # 购买木材
    response = stub.Trade(town_pb2.TradeRequest(
        target_node='merchant',
        item='wood',
        quantity=20,
        price=0  # 0=buy
    ))
    print(f"购买木材: {response.message}")
    
    # 建造房屋
    response = stub.Produce(town_pb2.ProduceRequest())
    print(f"建造房屋: {response.message}")
    
    # 查看状态
    info = stub.GetInfo(town_pb2.Empty())
    print(f"Charlie当前状态: 体力{info.stamina}, 货币{info.inventory.money}, 物品{dict(info.inventory.items)}")
    channel.close()
    print()
    
    # Alice出售小麦
    print("=== 场景6: Alice出售小麦给商人 ===")
    channel = grpc.insecure_channel('localhost:50053')
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    
    response = stub.Trade(town_pb2.TradeRequest(
        target_node='merchant',
        item='wheat',
        quantity=10,
        price=1  # 1=sell
    ))
    print(f"出售小麦: {response.message}")
    
    info = stub.GetInfo(town_pb2.Empty())
    print(f"Alice当前状态: 体力{info.stamina}, 货币{info.inventory.money}, 物品{dict(info.inventory.items)}")
    channel.close()
    print()
    
    # 推进到晚上并睡觉
    print("=== 场景7: 推进时间到晚上并睡觉 ===")
    coord_channel = grpc.insecure_channel('localhost:50051')
    coord_stub = town_pb2_grpc.TimeCoordinatorStub(coord_channel)
    
    # 推进到晚上
    for i in range(2):
        response = coord_stub.AdvanceTime(town_pb2.Empty())
        print(f"时间推进: {response.message}")
        time.sleep(1)
    
    # Alice睡觉（有房子的Charlie可以免费睡，Alice需要租房）
    print("\nCharlie睡觉（有自己的房子）:")
    channel = grpc.insecure_channel('localhost:50055')
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    response = stub.Sleep(town_pb2.SleepRequest())
    print(f"  {response.message}")
    channel.close()
    
    print("\nAlice睡觉（需要租房）:")
    channel = grpc.insecure_channel('localhost:50053')
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    response = stub.Sleep(town_pb2.SleepRequest())
    print(f"  {response.message}")
    channel.close()
    
    coord_channel.close()
    print()
    
    # 推进到新的一天
    print("=== 场景8: 推进到新的一天 ===")
    coord_channel = grpc.insecure_channel('localhost:50051')
    coord_stub = town_pb2_grpc.TimeCoordinatorStub(coord_channel)
    
    response = coord_stub.AdvanceTime(town_pb2.Empty())
    print(f"时间推进: {response.message}")
    time.sleep(1)
    
    # 查看新一天的状态
    print("\n新一天的村民状态:")
    for node_id, port, name, _, _, _ in villagers:
        channel = grpc.insecure_channel(f'localhost:{port}')
        stub = town_pb2_grpc.VillagerNodeStub(channel)
        info = stub.GetInfo(town_pb2.Empty())
        print(f"{info.name}: 体力{info.stamina}, 行动点{info.action_points}, 货币{info.inventory.money}")
        channel.close()
    
    coord_channel.close()
    print()
    
    print("=== 测试场景完成 ===\n")


if __name__ == '__main__':
    try:
        run_test_scenario()
    except KeyboardInterrupt:
        print("\n测试中断")
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()

