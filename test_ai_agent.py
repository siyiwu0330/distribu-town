#!/usr/bin/env python3
"""
AI Agent测试脚本
测试AI村民代理的功能
"""

import requests
import time
import json
import subprocess
import threading
import os
from ai_villager_agent import AIVillagerAgent

def test_ai_agent():
    """测试AI Agent功能"""
    print("="*60)
    print("  AI Agent功能测试")
    print("="*60)
    
    # 测试配置
    villager_port = 5002
    coordinator_port = 5000
    merchant_port = 5001
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("✗ 未设置 OPENAI_API_KEY 环境变量")
        print("请设置API Key: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    print("\n1. 检查服务状态...")
    
    # 检查协调器
    try:
        response = requests.get(f"http://localhost:{coordinator_port}/health", timeout=2)
        if response.status_code == 200:
            print("✓ 协调器运行正常")
        else:
            print("✗ 协调器状态异常")
            return
    except:
        print("✗ 无法连接到协调器")
        return
    
    # 检查商人
    try:
        response = requests.get(f"http://localhost:{merchant_port}/health", timeout=2)
        if response.status_code == 200:
            print("✓ 商人运行正常")
        else:
            print("✗ 商人状态异常")
    except:
        print("✗ 无法连接到商人")
    
    # 检查村民节点
    try:
        response = requests.get(f"http://localhost:{villager_port}/health", timeout=2)
        if response.status_code == 200:
            print("✓ 村民节点运行正常")
        else:
            print("✗ 村民节点状态异常")
    except:
        print("✗ 无法连接到村民节点")
    
    print("\n2. 创建AI Agent...")
    
    # 创建AI Agent
    agent = AIVillagerAgent(
        villager_port=villager_port,
        coordinator_port=coordinator_port,
        merchant_port=merchant_port,
        api_key=api_key,
        model="gpt-3.5-turbo"
    )
    
    print("✓ AI Agent创建成功")
    
    print("\n3. 测试连接...")
    
    # 测试连接
    if agent.check_connection():
        print("✓ AI Agent连接正常")
    else:
        print("✗ AI Agent连接失败")
        return
    
    print("\n4. 测试状态获取...")
    
    # 测试状态获取
    villager_status = agent.get_villager_status()
    if villager_status:
        print("✓ 村民状态获取成功")
        print(f"  村民: {villager_status.get('name', 'Unknown')}")
        print(f"  职业: {villager_status.get('occupation', 'Unknown')}")
        print(f"  体力: {villager_status.get('stamina', 0)}/{villager_status.get('max_stamina', 100)}")
    else:
        print("✗ 村民状态获取失败")
    
    # 测试时间获取
    current_time = agent.get_current_time()
    print(f"✓ 当前时间: {current_time}")
    
    # 测试行动状态获取
    action_status = agent.get_action_status()
    if action_status:
        print("✓ 行动状态获取成功")
        print(f"  总村民数: {action_status.get('total_villagers', 0)}")
        print(f"  已提交: {action_status.get('submitted', 0)}")
    else:
        print("✗ 行动状态获取失败")
    
    # 测试商人价格获取
    prices = agent.get_merchant_prices()
    if prices:
        print("✓ 商人价格获取成功")
        print(f"  价格项目: {len(prices.get('prices', {}))}")
    else:
        print("✗ 商人价格获取失败")
    
    print("\n5. 测试GPT决策生成...")
    
    # 测试GPT决策生成
    context = {
        'villager': villager_status or {},
        'time': current_time,
        'action_status': action_status or {},
        'prices': prices or {},
        'messages': [],
        'villagers': []
    }
    
    print("正在生成决策...")
    decision = agent.generate_decision(context)
    
    if decision:
        print("✓ GPT决策生成成功")
        print(f"  行动: {decision.get('action', 'unknown')}")
        print(f"  理由: {decision.get('reason', 'No reason')[:100]}...")
    else:
        print("✗ GPT决策生成失败")
    
    print("\n6. 测试决策执行...")
    
    # 测试决策执行（如果村民未提交行动）
    if villager_status and not villager_status.get('has_submitted_action', False):
        print("村民未提交行动，测试决策执行...")
        agent.make_decision_and_act()
    else:
        print("村民已提交行动，跳过决策执行测试")
    
    print("\n7. 测试消息功能...")
    
    # 测试发送消息
    success = agent.execute_action("send_message", 
                                 target="all", 
                                 content="大家好！我是AI Agent，很高兴认识大家！", 
                                 type="broadcast")
    if success:
        print("✓ 广播消息发送成功")
    else:
        print("✗ 广播消息发送失败")
    
    print("\n8. 测试决策历史...")
    
    # 显示决策历史
    if agent.decision_history:
        print(f"✓ 决策历史记录: {len(agent.decision_history)} 条")
        for i, record in enumerate(agent.decision_history[-3:]):
            print(f"  {i+1}. {record['decision'].get('action', 'unknown')} - {record['timestamp']}")
    else:
        print("✗ 没有决策历史")
    
    print("\n" + "="*60)
    print("  AI Agent功能测试完成")
    print("="*60)
    print("\n💡 提示:")
    print("  1. 启动村民节点:")
    print("     python architecture2_rest/villager.py --port 5002 --id node1")
    print("  2. 启动AI Agent:")
    print("     python architecture2_rest/ai_villager_agent.py --port 5002")
    print("  3. 或使用启动脚本:")
    print("     ./start_ai_agent.sh --port 5002")
    print("  4. AI Agent命令:")
    print("     auto 30    - 启动自动决策（30秒间隔）")
    print("     decision   - 手动决策一次")
    print("     status     - 查看状态")
    print("     history    - 查看决策历史")
    print("     quit       - 退出")


def test_ai_agent_with_villager():
    """测试AI Agent与村民节点的交互"""
    print("\n" + "="*60)
    print("  AI Agent与村民节点交互测试")
    print("="*60)
    
    # 启动村民节点（如果未运行）
    villager_port = 5002
    
    try:
        response = requests.get(f"http://localhost:{villager_port}/health", timeout=2)
        if response.status_code != 200:
            print("启动村民节点...")
            # 这里可以添加启动村民节点的代码
            print("请手动启动村民节点:")
            print(f"python architecture2_rest/villager.py --port {villager_port} --id node1")
            return
    except:
        print("请手动启动村民节点:")
        print(f"python architecture2_rest/villager.py --port {villager_port} --id node1")
        return
    
    # 创建AI Agent
    agent = AIVillagerAgent(
        villager_port=villager_port,
        api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # 检查村民是否已创建
    villager_status = agent.get_villager_status()
    if not villager_status:
        print("创建村民...")
        success = agent.create_villager("AI_Farmer", "farmer", "male", "intelligent and strategic")
        if success:
            print("✓ 村民创建成功")
        else:
            print("✗ 村民创建失败")
            return
    
    print("✓ AI Agent准备就绪")
    print("开始自动决策测试...")
    
    # 启动自动决策
    agent.start_auto_decision_loop(interval=60)  # 60秒间隔
    
    try:
        # 运行5分钟
        time.sleep(300)
    except KeyboardInterrupt:
        print("\n停止测试...")
    
    agent.stop_auto_decision_loop()
    
    # 显示决策历史
    print(f"\n决策历史 ({len(agent.decision_history)} 条):")
    for i, record in enumerate(agent.decision_history):
        print(f"{i+1}. {record['timestamp']}")
        print(f"   行动: {record['decision'].get('action', 'unknown')}")
        print(f"   理由: {record['decision'].get('reason', 'No reason')[:100]}...")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        test_ai_agent_with_villager()
    else:
        test_ai_agent()
