#!/usr/bin/env python3
"""
消息系统测试脚本
测试点对点消息和广播消息功能
"""

import requests
import time
import json

def test_message_system():
    """测试消息系统功能"""
    print("="*60)
    print("  消息系统功能测试")
    print("="*60)
    
    # 测试配置
    coordinator_url = "http://localhost:5000"
    villager1_url = "http://localhost:5002"
    villager2_url = "http://localhost:5003"
    
    print("\n1. 检查服务状态...")
    
    # 检查协调器
    try:
        response = requests.get(f"{coordinator_url}/health", timeout=2)
        if response.status_code == 200:
            print("✓ 协调器运行正常")
        else:
            print("✗ 协调器状态异常")
            return
    except:
        print("✗ 无法连接到协调器")
        return
    
    # 检查村民节点
    try:
        response = requests.get(f"{villager1_url}/health", timeout=2)
        if response.status_code == 200:
            print("✓ 村民节点1 (5002) 运行正常")
        else:
            print("✗ 村民节点1状态异常")
    except:
        print("✗ 无法连接到村民节点1")
    
    try:
        response = requests.get(f"{villager2_url}/health", timeout=2)
        if response.status_code == 200:
            print("✓ 村民节点2 (5003) 运行正常")
        else:
            print("✗ 村民节点2状态异常")
    except:
        print("✗ 无法连接到村民节点2")
    
    print("\n2. 测试广播消息...")
    
    # 发送广播消息
    try:
        response = requests.post(
            f"{villager1_url}/messages/send",
            json={
                'target': 'all',
                'content': '大家好！我是test1，出售小麦，价格优惠！',
                'type': 'broadcast'
            },
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✓ 广播消息发送成功")
            else:
                print(f"✗ 广播消息发送失败: {result.get('message')}")
        else:
            print(f"✗ 广播消息发送失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ 广播消息发送异常: {e}")
    
    print("\n3. 测试点对点消息...")
    
    # 发送点对点消息
    try:
        response = requests.post(
            f"{villager1_url}/messages/send",
            json={
                'target': 'node2',
                'content': '你好node2，需要小麦吗？',
                'type': 'private'
            },
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✓ 点对点消息发送成功")
            else:
                print(f"✗ 点对点消息发送失败: {result.get('message')}")
        else:
            print(f"✗ 点对点消息发送失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ 点对点消息发送异常: {e}")
    
    print("\n4. 检查消息接收...")
    
    # 检查村民节点1的消息
    try:
        response = requests.get(f"{villager1_url}/messages", timeout=5)
        if response.status_code == 200:
            messages = response.json()['messages']
            print(f"✓ 村民节点1收到 {len(messages)} 条消息")
            for msg in messages:
                print(f"  - [{msg['id']}] {msg['type']}: {msg['content'][:50]}...")
        else:
            print("✗ 无法获取村民节点1的消息")
    except Exception as e:
        print(f"✗ 获取村民节点1消息异常: {e}")
    
    # 检查村民节点2的消息
    try:
        response = requests.get(f"{villager2_url}/messages", timeout=5)
        if response.status_code == 200:
            messages = response.json()['messages']
            print(f"✓ 村民节点2收到 {len(messages)} 条消息")
            for msg in messages:
                print(f"  - [{msg['id']}] {msg['type']}: {msg['content'][:50]}...")
        else:
            print("✗ 无法获取村民节点2的消息")
    except Exception as e:
        print(f"✗ 获取村民节点2消息异常: {e}")
    
    print("\n5. 测试消息标记为已读...")
    
    # 标记消息为已读
    try:
        response = requests.post(
            f"{villager1_url}/messages/mark_read",
            json={},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✓ 消息标记为已读成功")
            else:
                print(f"✗ 消息标记为已读失败: {result.get('message')}")
        else:
            print(f"✗ 消息标记为已读失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ 消息标记为已读异常: {e}")
    
    print("\n6. 测试在线村民列表...")
    
    # 获取在线村民列表
    try:
        response = requests.get(f"{coordinator_url}/nodes", timeout=5)
        if response.status_code == 200:
            nodes_data = response.json()
            villagers = [node for node in nodes_data['nodes'] if node['node_type'] == 'villager']
            print(f"✓ 发现 {len(villagers)} 个在线村民:")
            for villager in villagers:
                print(f"  - {villager.get('name', villager['node_id'])} ({villager['node_id']})")
        else:
            print("✗ 无法获取在线村民列表")
    except Exception as e:
        print(f"✗ 获取在线村民列表异常: {e}")
    
    print("\n" + "="*60)
    print("  消息系统测试完成")
    print("="*60)
    print("\n💡 提示:")
    print("  1. 启动两个村民节点:")
    print("     python architecture2_rest/villager.py --port 5002 --id node1")
    print("     python architecture2_rest/villager.py --port 5003 --id node2")
    print("  2. 在CLI中测试消息功能:")
    print("     messages  - 查看消息")
    print("     send node2 你好 - 发送私聊")
    print("     broadcast 出售小麦 - 发送广播")
    print("     villagers - 查看在线村民")


if __name__ == '__main__':
    test_message_system()
