"""
TimeCoordinator - Architecture 1 (gRPC)
负责管理全局Time和同步所有Node
"""

import grpc
from concurrent import futures
import time
import sys
import os

# 添加路径以导入生成的proto文件
sys.path.insert(0, os.path.dirname(__file__))

import town_pb2
import town_pb2_grpc

# 添加common模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.models import GameState, TimeOfDay


class TimeCoordinatorService(town_pb2_grpc.TimeCoordinatorServicer):
    """TimeCoordinator服务"""
    
    def __init__(self):
        self.game_state = GameState()
        self.registered_nodes = {}  # {node_id: NodeInfo}
        print(f"[Coordinator] Initialization complete - Day {self.game_state.day}, {self.game_state.time_of_day.value}")
    
    def RegisterNode(self, request, context):
        """注册新Node"""
        node_id = request.node_id
        self.registered_nodes[node_id] = {
            'node_id': node_id,
            'node_type': request.node_type,
            'address': request.address
        }
        print(f"[Coordinator] Node注册: {node_id} ({request.node_type}) @ {request.address}")
        return town_pb2.Status(
            success=True,
            message=f"Node {node_id} registered successfully"
        )
    
    def GetCurrentTime(self, request, context):
        """获取当前Time"""
        return town_pb2.GameTime(
            day=self.game_state.day,
            time_of_day=self.game_state.time_of_day.value
        )
    
    def AdvanceTime(self, request, context):
        """AdvanceTime"""
        old_time = f"Day {self.game_state.day} {self.game_state.time_of_day.value}"
        
        # 如果是Evening到Morning的转换，需要重置所有Node
        is_new_day = self.game_state.time_of_day == TimeOfDay.EVENING
        
        # AdvanceTime
        self.game_state.advance_time()
        
        new_time = f"Day {self.game_state.day} {self.game_state.time_of_day.value}"
        print(f"\n[Coordinator] TimeAdvance: {old_time} -> {new_time}")
        
        # Notify所有注册的Node
        notification = town_pb2.TimeAdvanceNotification(
            new_time=town_pb2.GameTime(
                day=self.game_state.day,
                time_of_day=self.game_state.time_of_day.value
            )
        )
        
        for node_id, node_info in self.registered_nodes.items():
            try:
                if node_info['node_type'] == 'coordinator':
                    continue
                
                # Connecting toNode并Notify
                channel = grpc.insecure_channel(node_info['address'])
                
                if node_info['node_type'] == 'merchant':
                    stub = town_pb2_grpc.MerchantNodeStub(channel)
                    stub.OnTimeAdvance(notification)
                elif node_info['node_type'] == 'villager':
                    stub = town_pb2_grpc.VillagerNodeStub(channel)
                    stub.OnTimeAdvance(notification)
                
                channel.close()
                print(f"[Coordinator] NotifyNode: {node_id}")
            except Exception as e:
                print(f"[Coordinator] NotifyNode {node_id} Failed: {e}")
        
        return town_pb2.Status(
            success=True,
            message=f"Time advanced to {new_time}"
        )
    
    def ListNodes(self, request, context):
        """列出所有注册的Node"""
        nodes = []
        for node_info in self.registered_nodes.values():
            nodes.append(town_pb2.NodeInfo(
                node_id=node_info['node_id'],
                node_type=node_info['node_type'],
                address=node_info['address']
            ))
        return town_pb2.NodeList(nodes=nodes)


def serve(port=50051):
    """启动Coordinator服务器"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    town_pb2_grpc.add_TimeCoordinatorServicer_to_server(
        TimeCoordinatorService(), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"[Coordinator] TimeCoordinatorstarting on port {port}")
    print("[Coordinator] WaitingNode注册...")
    print("[Coordinator] 使用 Ctrl+C 停止服务器")
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print("\n[Coordinator] 关闭服务器...")
        server.stop(0)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='TimeCoordinator服务')
    parser.add_argument('--port', type=int, default=50051, help='监听端口')
    args = parser.parse_args()
    
    serve(args.port)

