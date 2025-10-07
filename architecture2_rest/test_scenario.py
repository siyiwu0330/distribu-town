"""
测试场景 - Architecture 2 (REST)
自动化测试虚拟小镇的各项功能
"""

import requests
import time


def wait_for_service(url, max_retries=10):
    """等待服务启动"""
    for i in range(max_retries):
        try:
            response = requests.get(f"{url}/health", timeout=1)
            if response.status_code == 200:
                return True
        except:
            time.sleep(1)
    return False


def run_test_scenario():
    """运行测试场景"""
    print("\n=== 分布式虚拟小镇测试场景 (REST) ===\n")
    
    # 等待服务启动
    print("等待服务启动...")
    if not wait_for_service('http://localhost:5000'):
        print("✗ 无法连接到协调器")
        return
    if not wait_for_service('http://localhost:5001'):
        print("✗ 无法连接到商人")
        return
    if not wait_for_service('http://localhost:5002'):
        print("✗ 无法连接到村民节点")
        return
    
    print("✓ 所有服务已就绪\n")
    
    # 创建村民
    print("=== 场景1: 创建村民 ===")
    
    villagers = [
        (5002, 'alice', 'Alice', 'farmer', 'female', '勤劳'),
        (5003, 'bob', 'Bob', 'chef', 'male', '热情'),
        (5004, 'charlie', 'Charlie', 'carpenter', 'male', '细心'),
    ]
    
    for port, node_id, name, occupation, gender, personality in villagers:
        response = requests.post(
            f'http://localhost:{port}/villager',
            json={
                'name': name,
                'occupation': occupation,
                'gender': gender,
                'personality': personality
            }
        )
        if response.status_code == 200:
            print(f"✓ 创建村民 {name} ({occupation})")
        else:
            print(f"✗ 创建村民 {name} 失败: {response.json()}")
        time.sleep(0.3)
    
    print()
    
    # 查看初始状态
    print("=== 场景2: 查看初始状态 ===")
    for port, node_id, name, _, _, _ in villagers:
        response = requests.get(f'http://localhost:{port}/villager')
        if response.status_code == 200:
            data = response.json()
            print(f"{data['name']}: 体力{data['stamina']}, 货币{data['inventory']['money']}, 物品{data['inventory']['items']}")
    print()
    
    # Alice（农夫）购买种子并种植
    print("=== 场景3: Alice（农夫）购买种子并种植 ===")
    
    # 购买5个种子
    response = requests.post(
        'http://localhost:5002/action/trade',
        json={
            'target': 'merchant',
            'item': 'seed',
            'quantity': 5,
            'action': 'buy'
        }
    )
    print(f"购买种子: {response.json()['message']}")
    
    # 种植（生产小麦）3次
    for i in range(3):
        response = requests.post('http://localhost:5002/action/produce')
        if response.status_code == 200:
            print(f"生产第{i+1}次: {response.json()['message']}")
        else:
            print(f"生产第{i+1}次失败: {response.json()['message']}")
    
    # 查看状态
    response = requests.get('http://localhost:5002/villager')
    data = response.json()
    print(f"Alice当前状态: 体力{data['stamina']}, 货币{data['inventory']['money']}, 物品{data['inventory']['items']}")
    print()
    
    # Charlie（木工）购买木材并建造房屋
    print("=== 场景4: Charlie（木工）购买木材并建造房屋 ===")
    
    # 购买木材
    response = requests.post(
        'http://localhost:5004/action/trade',
        json={
            'target': 'merchant',
            'item': 'wood',
            'quantity': 20,
            'action': 'buy'
        }
    )
    print(f"购买木材: {response.json()['message']}")
    
    # 建造房屋
    response = requests.post('http://localhost:5004/action/produce')
    if response.status_code == 200:
        print(f"建造房屋: {response.json()['message']}")
    else:
        print(f"建造失败: {response.json()['message']}")
    
    # 查看状态
    response = requests.get('http://localhost:5004/villager')
    data = response.json()
    print(f"Charlie当前状态: 体力{data['stamina']}, 货币{data['inventory']['money']}, 物品{data['inventory']['items']}")
    print()
    
    # Alice出售小麦
    print("=== 场景5: Alice出售小麦给商人 ===")
    
    response = requests.post(
        'http://localhost:5002/action/trade',
        json={
            'target': 'merchant',
            'item': 'wheat',
            'quantity': 10,
            'action': 'sell'
        }
    )
    print(f"出售小麦: {response.json()['message']}")
    
    response = requests.get('http://localhost:5002/villager')
    data = response.json()
    print(f"Alice当前状态: 体力{data['stamina']}, 货币{data['inventory']['money']}, 物品{data['inventory']['items']}")
    print()
    
    # 推进到晚上并睡觉
    print("=== 场景6: 推进时间到晚上并睡觉 ===")
    
    # 推进到晚上
    for i in range(2):
        response = requests.post('http://localhost:5000/time/advance')
        if response.status_code == 200:
            data = response.json()
            print(f"时间推进: {data['message']}")
            time.sleep(1)
    
    # Charlie睡觉（有自己的房子）
    print("\nCharlie睡觉（有自己的房子）:")
    response = requests.post('http://localhost:5004/action/sleep')
    print(f"  {response.json()['message']}")
    
    # Alice睡觉（需要租房）
    print("\nAlice睡觉（需要租房）:")
    response = requests.post('http://localhost:5002/action/sleep')
    print(f"  {response.json()['message']}")
    print()
    
    # 推进到新的一天
    print("=== 场景7: 推进到新的一天 ===")
    response = requests.post('http://localhost:5000/time/advance')
    if response.status_code == 200:
        data = response.json()
        print(f"时间推进: {data['message']}")
        time.sleep(1)
    
    # 查看新一天的状态
    print("\n新一天的村民状态:")
    for port, node_id, name, _, _, _ in villagers:
        response = requests.get(f'http://localhost:{port}/villager')
        if response.status_code == 200:
            data = response.json()
            action_status = "已提交" if data.get('has_submitted_action', False) else "未提交"
            print(f"{data['name']}: 体力{data['stamina']}, 行动{action_status}, 货币{data['inventory']['money']}")
    print()
    
    # 获取商人价格表
    print("=== 场景8: 查看商人价格表 ===")
    response = requests.get('http://localhost:5001/prices')
    if response.status_code == 200:
        prices = response.json()
        print("\n商人出售价格:")
        for item, price in prices['buy'].items():
            print(f"  {item}: {price}金币")
        print("\n商人收购价格:")
        for item, price in prices['sell'].items():
            print(f"  {item}: {price}金币")
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

