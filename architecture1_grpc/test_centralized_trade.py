#!/usr/bin/env python3
"""
测试中心化交易系统 - gRPC版本
"""

import grpc
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))
from proto import town_pb2
from proto import town_pb2_grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.models import Occupation, Gender


def test_centralized_trading():
    """测试中心化交易系统"""
    
    print("\n" + "="*70)
    print("  测试中心化交易系统 (gRPC)")
    print("="*70 + "\n")
    
    # 连接信息
    coordinator_addr = 'localhost:50051'
    merchant_addr = 'localhost:50052'
    node1_addr = 'localhost:50053'
    node2_addr = 'localhost:50054'
    node1_id = 'node1'
    node2_id = 'node2'
    
    # Step 1: 创建两个村民
    print("Step 1: 创建村民...")
    
    # 创建Alice (farmer)
    channel = grpc.insecure_channel(node1_addr)
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    response = stub.CreateVillager(town_pb2.CreateVillagerRequest(
        name='Alice',
        occupation='farmer',
        gender='female',
        personality='勤劳的农民'
    ))
    channel.close()
    
    if not response.success:
        print(f"✗ 创建Alice失败: {response.message}")
        return
    print(f"✓ 创建Alice成功")
    
    # 创建Bob (miner)
    channel = grpc.insecure_channel(node2_addr)
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    response = stub.CreateVillager(town_pb2.CreateVillagerRequest(
        name='Bob',
        occupation='miner',
        gender='male',
        personality='强壮的矿工'
    ))
    channel.close()
    
    if not response.success:
        print(f"✗ 创建Bob失败: {response.message}")
        return
    print(f"✓ 创建Bob成功")
    
    # Step 2: Alice生产wheat
    print("\nStep 2: Alice生产wheat...")
    
    channel = grpc.insecure_channel(node1_addr)
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    response = stub.Produce(town_pb2.ProduceRequest())
    channel.close()
    
    if not response.success:
        print(f"✗ 生产失败: {response.message}")
        return
    print(f"✓ {response.message}")
    
    # Step 3: Bob从商人购买基础资源
    print("\nStep 3: Bob从商人购买stone...")
    
    channel = grpc.insecure_channel(node2_addr)
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    response = stub.Trade(town_pb2.TradeRequest(
        target_node='merchant',
        item='stone',
        quantity=2,
        price=0  # 0表示buy
    ))
    channel.close()
    
    if not response.success:
        print(f"✗ 购买失败: {response.message}")
        return
    print(f"✓ {response.message}")
    
    # 查看初始状态
    print("\n" + "="*70)
    print("  初始状态")
    print("="*70)
    
    channel = grpc.insecure_channel(node1_addr)
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    alice = stub.GetInfo(town_pb2.Empty())
    channel.close()
    
    print(f"\nAlice ({node1_id}):")
    print(f"  货币: {alice.inventory.money}")
    print(f"  物品: {dict(alice.inventory.items)}")
    
    channel = grpc.insecure_channel(node2_addr)
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    bob = stub.GetInfo(town_pb2.Empty())
    channel.close()
    
    print(f"\nBob ({node2_id}):")
    print(f"  货币: {bob.inventory.money}")
    print(f"  物品: {dict(bob.inventory.items)}")
    
    # Step 4: Alice向Bob发起交易（出售wheat）
    print("\n" + "="*70)
    print("  Step 4: Alice向Bob发起交易")
    print("="*70)
    print("Alice想要出售5个wheat给Bob，价格50")
    
    channel = grpc.insecure_channel(merchant_addr)
    stub = town_pb2_grpc.MerchantNodeStub(channel)
    response = stub.CreateTrade(town_pb2.CreateTradeRequest(
        initiator_id=node1_id,
        initiator_address=node1_addr,
        target_id=node2_id,
        target_address=node2_addr,
        offer_type='sell',
        item='wheat',
        quantity=5,
        price=50
    ))
    channel.close()
    
    if not response.success:
        print(f"✗ 创建交易失败: {response.message}")
        return
    
    trade_id = response.trade_id
    print(f"✓ 交易创建成功: {trade_id}")
    
    # Step 5: 查看待处理的交易
    print("\nStep 5: Bob查看待处理的交易...")
    
    channel = grpc.insecure_channel(merchant_addr)
    stub = town_pb2_grpc.MerchantNodeStub(channel)
    response = stub.ListTrades(town_pb2.ListTradesRequest(
        node_id=node2_id,
        type='pending'
    ))
    channel.close()
    
    if not response.trades:
        print("✗ 没有找到待处理的交易")
        return
    
    print(f"✓ 找到 {len(response.trades)} 个待处理的交易")
    for trade in response.trades:
        print(f"\n  交易ID: {trade.trade_id}")
        print(f"  发起方: {trade.initiator_id}")
        print(f"  类型: {trade.offer_type}")
        print(f"  物品: {trade.item} x{trade.quantity}")
        print(f"  价格: {trade.price}")
    
    # Step 6: Bob接受交易
    print("\nStep 6: Bob接受交易...")
    
    channel = grpc.insecure_channel(merchant_addr)
    stub = town_pb2_grpc.MerchantNodeStub(channel)
    response = stub.AcceptTrade(town_pb2.AcceptTradeRequest(
        trade_id=trade_id,
        node_id=node2_id
    ))
    channel.close()
    
    if not response.success:
        print(f"✗ 接受失败: {response.message}")
        return
    print(f"✓ {response.message}")
    
    # Step 7: 双方确认交易
    print("\nStep 7: 双方确认交易...")
    
    # Alice确认
    print("  Alice确认...")
    channel = grpc.insecure_channel(merchant_addr)
    stub = town_pb2_grpc.MerchantNodeStub(channel)
    response = stub.ConfirmTrade(town_pb2.ConfirmTradeRequest(
        trade_id=trade_id,
        node_id=node1_id
    ))
    channel.close()
    
    if not response.success:
        print(f"✗ Alice确认失败: {response.message}")
        return
    print(f"  ✓ Alice: {response.message}")
    
    # Bob确认
    print("  Bob确认...")
    channel = grpc.insecure_channel(merchant_addr)
    stub = town_pb2_grpc.MerchantNodeStub(channel)
    response = stub.ConfirmTrade(town_pb2.ConfirmTradeRequest(
        trade_id=trade_id,
        node_id=node2_id
    ))
    channel.close()
    
    if not response.success:
        print(f"✗ Bob确认失败: {response.message}")
        return
    print(f"  ✓ Bob: {response.message}")
    
    # Step 8: 查看最终状态
    print("\n" + "="*70)
    print("  最终状态")
    print("="*70)
    
    channel = grpc.insecure_channel(node1_addr)
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    alice = stub.GetInfo(town_pb2.Empty())
    channel.close()
    
    print(f"\nAlice ({node1_id}):")
    print(f"  货币: {alice.inventory.money} (应该 +50)")
    print(f"  物品: {dict(alice.inventory.items)} (wheat应该 -5)")
    
    channel = grpc.insecure_channel(node2_addr)
    stub = town_pb2_grpc.VillagerNodeStub(channel)
    bob = stub.GetInfo(town_pb2.Empty())
    channel.close()
    
    print(f"\nBob ({node2_id}):")
    print(f"  货币: {bob.inventory.money} (应该 -50)")
    print(f"  物品: {dict(bob.inventory.items)} (应该有5个wheat)")
    
    # 验证结果
    print("\n" + "="*70)
    print("  测试验证")
    print("="*70)
    
    success = True
    
    # 验证Alice
    if alice.inventory.money == 150:  # 100 + 50
        print("✓ Alice货币正确 (+50)")
    else:
        print(f"✗ Alice货币错误，期望150，实际{alice.inventory.money}")
        success = False
    
    alice_wheat = dict(alice.inventory.items).get('wheat', 0)
    if alice_wheat == 5:  # 10 - 5
        print("✓ Alice wheat正确 (-5)")
    else:
        print(f"✗ Alice wheat错误，期望5，实际{alice_wheat}")
        success = False
    
    # 验证Bob
    if bob.inventory.money == 50:  # 100 - 50
        print("✓ Bob货币正确 (-50)")
    else:
        print(f"✗ Bob货币错误，期望50，实际{bob.inventory.money}")
        success = False
    
    bob_wheat = dict(bob.inventory.items).get('wheat', 0)
    if bob_wheat == 5:  # 0 + 5
        print("✓ Bob wheat正确 (+5)")
    else:
        print(f"✗ Bob wheat错误，期望5，实际{bob_wheat}")
        success = False
    
    # 最终结果
    print("\n" + "="*70)
    if success:
        print("  ✅ 所有测试通过！")
    else:
        print("  ❌ 部分测试失败")
    print("="*70 + "\n")


if __name__ == '__main__':
    print("\n请确保以下节点已启动：")
    print("  - Coordinator (localhost:50051)")
    print("  - Merchant (localhost:50052)")
    print("  - Villager node1 (localhost:50053)")
    print("  - Villager node2 (localhost:50054)")
    
    input("\n按Enter开始测试...")
    
    try:
        test_centralized_trading()
    except grpc.RpcError as e:
        print(f"\n✗ gRPC错误: {e.code()}")
        print(f"  详情: {e.details()}")
        print("\n请检查所有节点是否正常运行")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

