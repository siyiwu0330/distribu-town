#!/usr/bin/env python3
"""
测试gRPC消息系统
"""
import requests
import grpc
from proto import town_pb2
from proto import town_pb2_grpc

def test_http_server(port):
    """测试HTTP服务器是否工作"""
    try:
        print(f"\n测试HTTP服务器（端口 {port}）...")
        response = requests.get(f"http://localhost:{port}/test", timeout=2)
        print(f"✓ HTTP服务器响应: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ HTTP服务器测试失败: {e}")
        return False

def test_message_receive(port, message):
    """测试消息接收端点"""
    try:
        print(f"\n测试消息接收端点（端口 {port}）...")
        response = requests.post(
            f"http://localhost:{port}/messages/receive",
            json=message,
            timeout=2
        )
        print(f"✓ 消息接收响应: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ 消息接收测试失败: {e}")
        return False

def test_grpc_get_messages(grpc_port, node_id):
    """测试gRPC获取消息"""
    try:
        print(f"\n测试gRPC获取消息（端口 {grpc_port}，节点 {node_id}）...")
        channel = grpc.insecure_channel(f'localhost:{grpc_port}')
        stub = town_pb2_grpc.VillagerNodeStub(channel)
        
        response = stub.GetMessages(town_pb2.GetMessagesRequest(node_id=node_id))
        print(f"✓ 获取到 {len(response.messages)} 条消息")
        
        for msg in response.messages:
            print(f"  - {msg.message_id}: {msg.from_} -> {msg.to}: {msg.content}")
        
        channel.close()
        return True
    except Exception as e:
        print(f"✗ gRPC获取消息失败: {e}")
        return False

def test_grpc_send_message(grpc_port, target, content):
    """测试gRPC发送消息"""
    try:
        print(f"\n测试gRPC发送消息（端口 {grpc_port}，目标 {target}）...")
        channel = grpc.insecure_channel(f'localhost:{grpc_port}')
        stub = town_pb2_grpc.VillagerNodeStub(channel)
        
        response = stub.SendMessage(town_pb2.SendMessageRequest(
            target=target,
            content=content,
            type='private'
        ))
        
        if response.success:
            print(f"✓ 消息发送成功: {response.message}")
        else:
            print(f"✗ 消息发送失败: {response.message}")
        
        channel.close()
        return response.success
    except Exception as e:
        print(f"✗ gRPC发送消息失败: {e}")
        return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='测试gRPC消息系统')
    parser.add_argument('--grpc-port', type=int, default=50053, help='gRPC端口')
    parser.add_argument('--node-id', type=str, default='node1', help='节点ID')
    args = parser.parse_args()
    
    grpc_port = args.grpc_port
    http_port = grpc_port + 1000
    node_id = args.node_id
    
    print("="*60)
    print(f"测试节点: {node_id}")
    print(f"gRPC端口: {grpc_port}")
    print(f"HTTP端口: {http_port}")
    print("="*60)
    
    # 测试1: HTTP服务器是否工作
    if not test_http_server(http_port):
        print("\n⚠️ HTTP服务器未运行，消息系统无法工作")
        print(f"请确保villager节点已启动: python villager.py --port {grpc_port} --id {node_id}")
        exit(1)
    
    # 测试2: 消息接收端点
    test_message = {
        'message_id': 'test_msg_1',
        'from': 'test_sender',
        'to': node_id,
        'content': 'Test message',
        'type': 'private',
        'timestamp': 1234567890,
        'is_read': False
    }
    test_message_receive(http_port, test_message)
    
    # 测试3: gRPC获取消息
    test_grpc_get_messages(grpc_port, node_id)
    
    # 测试4: gRPC发送消息
    test_grpc_send_message(grpc_port, 'node2', 'Test message from script')
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

