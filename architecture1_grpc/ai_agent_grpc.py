#!/usr/bin/env python3
"""
AI Agent启动器 - gRPC版本
完全复制REST版本的AI Agent功能，使用gRPC适配层
"""

import sys
import os
import argparse
import threading
import time
import json
import openai
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'architecture2_rest'))

# 导入gRPC适配层
from grpc_adapter import GRPCAdapter

# 导入REST版本的AI Agent（我们将monkey patch它的requests调用）
from ai_villager_agent import AIVillagerAgent


class GRPCAIAgent(AIVillagerAgent):
    """gRPC版本的AI Agent，继承REST版本的所有功能"""
    
    def __init__(self, villager_port: int, coordinator_port: int = 50051, merchant_port: int = 50052, 
                 api_key: str = None, model: str = "gpt-4", use_react: bool = False):
        # 初始化gRPC适配层
        self.grpc_adapter = GRPCAdapter(
            coordinator_port=coordinator_port,
            merchant_port=merchant_port,
            villager_port=villager_port
        )
        
        # 调用父类初始化，但使用gRPC适配层
        super().__init__(
            villager_port=villager_port,
            coordinator_port=coordinator_port,
            merchant_port=merchant_port,
            api_key=api_key,
            model=model,
            use_react=use_react
        )
        
        print("[gRPC AI Agent] 使用gRPC适配层")
        
        # Monkey patch所有HTTP请求为gRPC调用
        self._patch_requests()
    
    def _patch_requests(self):
        """将所有HTTP请求替换为gRPC调用"""
        # 保存原始方法（只保存存在的方法）
        self._original_get_villager_status = super().get_villager_status
        self._original_get_current_time = super().get_current_time
        self._original_get_action_status = super().get_action_status
        self._original_get_merchant_prices = super().get_merchant_prices
        self._original_get_online_villagers = super().get_online_villagers
        self._original_get_messages = super().get_messages
        self._original_get_trades_received = super().get_trades_received
        self._original_get_trades_sent = super().get_trades_sent
        self._original_execute_action = super().execute_action
        self._original_check_connection = super().check_connection
        self._original_create_villager = super().create_villager
        self._original_buy_from_merchant = super().buy_from_merchant
        self._original_sell_to_merchant = super().sell_to_merchant
        self._original_send_message = super().send_message
        self._original_create_trade_request = super().create_trade_request
        self._original_accept_trade_request = super().accept_trade_request
        self._original_reject_trade_request = super().reject_trade_request
        self._original_confirm_trade_request = super().confirm_trade_request
        self._original_cancel_trade_request = super().cancel_trade_request
    
    def check_connection(self) -> bool:
        """检查连接"""
        return self.grpc_adapter.check_villager_connection()
    
    def get_villager_status(self) -> dict:
        """获取村民状态"""
        return self.grpc_adapter.get_villager_status()
    
    def get_current_time(self) -> str:
        """获取当前时间"""
        return self.grpc_adapter.get_current_time()
    
    def get_action_status(self) -> dict:
        """获取行动提交状态"""
        return self.grpc_adapter.get_action_status()
    
    def get_merchant_prices(self) -> dict:
        """获取商人价格"""
        return self.grpc_adapter.get_merchant_prices()
    
    def get_online_villagers(self) -> list:
        """获取在线村民"""
        return self.grpc_adapter.get_online_villagers()
    
    def get_messages(self) -> list:
        """获取消息"""
        return self.grpc_adapter.get_messages()
    
    def get_trades_received(self) -> list:
        """获取收到的交易请求"""
        return self.grpc_adapter.get_trades_received()
    
    def get_trades_sent(self) -> list:
        """获取发送的交易请求"""
        return self.grpc_adapter.get_trades_sent()
    
    def execute_action(self, action: str, **kwargs) -> bool:
        """执行行动"""
        return self.grpc_adapter.execute_action(action, **kwargs)
    
    def create_villager(self, name: str, occupation: str, gender: str, personality: str) -> bool:
        """创建村民"""
        return self.grpc_adapter.create_villager(name, occupation, gender, personality)
    
    def submit_action(self, action: str, **kwargs) -> bool:
        """提交行动（gRPC版本直接执行）"""
        return self.execute_action(action, **kwargs)
    
    def buy_from_merchant(self, item: str, quantity: int) -> bool:
        """从商人购买"""
        return self.grpc_adapter.buy_from_merchant(item, quantity)
    
    def sell_to_merchant(self, item: str, quantity: int) -> bool:
        """向商人出售"""
        return self.grpc_adapter.sell_to_merchant(item, quantity)
    
    def send_message(self, target: str, content: str) -> bool:
        """发送消息"""
        return self.grpc_adapter.send_message(target, content)
    
    def create_trade_request(self, target: str, offer_type: str, item: str, quantity: int, price: int) -> bool:
        """创建交易请求"""
        return self.grpc_adapter.create_trade_request(target, offer_type, item, quantity, price)
    
    def accept_trade_request(self, trade_id: str) -> bool:
        """接受交易请求"""
        return self.grpc_adapter.accept_trade_request(trade_id)
    
    def reject_trade_request(self, trade_id: str) -> bool:
        """拒绝交易请求"""
        return self.grpc_adapter.reject_trade_request(trade_id)
    
    def confirm_trade_request(self, trade_id: str) -> bool:
        """确认交易请求"""
        return self.grpc_adapter.confirm_trade_request(trade_id)
    
    def cancel_trade_request(self, trade_id: str) -> bool:
        """取消交易请求"""
        return self.grpc_adapter.cancel_trade_request(trade_id)
    
    def start(self):
        """启动AI Agent（重写父类方法）"""
        if not self.api_key:
            print("⚠ 警告: 没有提供OpenAI API Key，AI Agent将以模拟模式运行")
            print("   设置环境变量: export OPENAI_API_KEY=your_key")
            print("   或使用参数: --api-key your_key")
            print("")
        
        self.running = True
        print(f"[gRPC AI Agent] 开始托管村民: {self.villager_name}")
        print("   按 Ctrl+C 停止")
        print("")
        
        # 使用父类的决策循环
        self.start_auto_decision_loop(interval=30)
    
    def stop(self):
        """停止AI Agent"""
        self.stop_auto_decision_loop()
        print("[gRPC AI Agent] 已停止")


def main():
    parser = argparse.ArgumentParser(description='AI村民代理 (gRPC版本)')
    parser.add_argument('--port', type=int, required=True, help='村民节点端口')
    parser.add_argument('--name', type=str, required=True, help='村民名字')
    parser.add_argument('--occupation', type=str, required=True, help='村民职业')
    parser.add_argument('--gender', type=str, required=True, help='村民性别')
    parser.add_argument('--personality', type=str, required=True, help='村民性格')
    parser.add_argument('--api-key', type=str, help='OpenAI API Key')
    parser.add_argument('--model', type=str, default='gpt-4', help='OpenAI模型')
    parser.add_argument('--use-react', action='store_true', help='使用ReAct模式')
    
    args = parser.parse_args()
    
    # 获取API Key
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    
    print("="*70)
    print("  创建AI村民:", args.name)
    print("="*70)
    print()
    
    # 创建AI Agent
    agent = GRPCAIAgent(
        villager_port=args.port,
        api_key=api_key,
        model=args.model,
        use_react=args.use_react
    )
    
    # 检查连接
    if not agent.check_connection():
        print("✗ 无法连接到村民节点，请确保节点已启动")
        return
    
    # 创建村民
    if agent.create_villager(args.name, args.occupation, args.gender, args.personality):
        print("✓ 村民创建成功")
    else:
        print("✗ 村民创建失败")
        return
    
    # 获取村民信息
    villager_info = agent.get_villager_status()
    if villager_info:
        agent.villager_name = villager_info.get('name', args.name)
        agent.villager_occupation = villager_info.get('occupation', args.occupation)
        print(f"✓ 村民信息: {agent.villager_name} ({agent.villager_occupation})")
    
    print()
    print("="*70)
    print("  启动AI Agent托管")
    print("="*70)
    print()
    
    # 启动AI Agent
    try:
        agent.start()
        
        # 保持运行
        while agent.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[gRPC AI Agent] 收到停止信号...")
        agent.stop()
    except Exception as e:
        print(f"[gRPC AI Agent] 运行异常: {e}")
        agent.stop()


if __name__ == "__main__":
    main()