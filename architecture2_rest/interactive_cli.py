"""
交互式CLI客户端 - 控制单个村民节点
可以连接到任何正在运行的村民节点进行交互
"""

import requests
import sys
import json
from typing import Optional


class VillagerCLI:
    """村民节点交互式CLI"""
    
    def __init__(self, villager_port: int, coordinator_port: int = 5000, merchant_port: int = 5001):
        self.villager_url = f"http://localhost:{villager_port}"
        self.coordinator_url = f"http://localhost:{coordinator_port}"
        self.merchant_url = f"http://localhost:{merchant_port}"
        self.villager_port = villager_port
    
    def check_connection(self) -> bool:
        """检查连接"""
        try:
            response = requests.get(f"{self.villager_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def get_villager_info(self) -> Optional[dict]:
        """获取村民信息"""
        try:
            response = requests.get(f"{self.villager_url}/villager", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"错误: {e}")
            return None
    
    def create_villager(self, name: str, occupation: str, gender: str, personality: str):
        """创建村民"""
        try:
            response = requests.post(
                f"{self.villager_url}/villager",
                json={
                    'name': name,
                    'occupation': occupation,
                    'gender': gender,
                    'personality': personality
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ 村民创建成功!")
                self.display_villager_info(data['villager'])
            else:
                print(f"\n✗ 创建失败: {response.json().get('message', '未知错误')}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def display_villager_info(self, info: dict = None):
        """显示村民信息"""
        if info is None:
            info = self.get_villager_info()
        
        if not info:
            print("\n村民未初始化")
            return
        
        # 根据行动点显示时段提示
        time_period_hint = ""
        if info['action_points'] == 3:
            time_period_hint = " [早晨 - 新时段开始]"
        elif info['action_points'] == 2:
            time_period_hint = " [已工作1次]"
        elif info['action_points'] == 1:
            time_period_hint = " [已工作2次]"
        elif info['action_points'] == 0:
            time_period_hint = " [⚠️ 行动点用完，建议推进时间]"
        
        print("\n" + "="*50)
        print(f"  {info['name']} - {info['occupation']}")
        print("="*50)
        print(f"性别: {info['gender']}")
        print(f"性格: {info['personality']}")
        print(f"⚡ 体力: {info['stamina']}/{info['max_stamina']}")
        print(f"🎯 行动点: {info['action_points']}/3{time_period_hint}")
        print(f"😴 已睡眠: {'是' if info['has_slept'] else '否'}")
        print(f"\n💰 货币: {info['inventory']['money']}")
        
        if info['inventory']['items']:
            print("📦 物品:")
            for item, quantity in info['inventory']['items'].items():
                print(f"   - {item}: {quantity}")
        else:
            print("📦 物品: 无")
        print("="*50)
    
    def produce(self):
        """生产"""
        try:
            response = requests.post(f"{self.villager_url}/action/produce", timeout=5)
            
            if response.status_code == 200:
                print(f"\n✓ {response.json()['message']}")
                villager_data = response.json()['villager']
                self.display_villager_info(villager_data)
                
                # 检查行动点
                if villager_data['action_points'] == 0:
                    print("\n⚠️  行动点已用完！")
                    print("   当前时段的工作已完成，你可以：")
                    print("   1. 进行不消耗行动点的操作（交易、睡眠）")
                    print("   2. 输入 'submit work' 提交本时段行动")
                else:
                    print(f"\n💡 提示: 剩余 {villager_data['action_points']} 个行动点")
                    print(f"   完成工作后使用 'submit work' 提交行动")
            else:
                print(f"\n✗ {response.json()['message']}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def trade(self, action: str, item: str, quantity: int):
        """交易"""
        try:
            response = requests.post(
                f"{self.villager_url}/action/trade",
                json={
                    'target': 'merchant',
                    'item': item,
                    'quantity': quantity,
                    'action': action
                },
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"\n✓ {response.json()['message']}")
                self.display_villager_info(response.json()['villager'])
            else:
                print(f"\n✗ {response.json()['message']}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def sleep(self):
        """睡眠"""
        try:
            response = requests.post(f"{self.villager_url}/action/sleep", timeout=5)
            
            if response.status_code == 200:
                print(f"\n✓ {response.json()['message']}")
                self.display_villager_info(response.json()['villager'])
            else:
                print(f"\n✗ {response.json()['message']}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def get_current_time(self):
        """获取当前时间"""
        try:
            response = requests.get(f"{self.coordinator_url}/time", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return f"Day {data['day']} - {data['time_of_day']}"
            return "无法获取时间"
        except:
            return "协调器未连接"
    
    def submit_action(self, action_type: str):
        """提交行动到协调器（同步屏障）"""
        try:
            response = requests.post(
                f"{self.villager_url}/action/submit",
                json={'action': action_type},
                timeout=10  # 延长超时，因为可能要等待其他人
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('all_ready'):
                    # 所有人都准备好了，时间已推进
                    print(f"\n✓ {data['message']}")
                    
                    # 显示新时间
                    new_time = data.get('new_time', {})
                    time_of_day = new_time.get('time_of_day', '')
                    
                    if time_of_day == 'morning':
                        print(f"\n🌅 新的一天开始！")
                        print("   - 所有村民行动点重置为3")
                        print("   - 每日饥饿扣除10体力")
                    elif time_of_day == 'noon':
                        print(f"\n☀️  已到中午")
                    elif time_of_day == 'evening':
                        print(f"\n🌙 已到晚上")
                        print("   - 可以睡眠恢复体力")
                    
                    # 显示更新后的村民状态
                    print("\n你的村民状态：")
                    self.display_villager_info()
                else:
                    # 还在等待其他人
                    waiting_for = data.get('waiting_for', [])
                    print(f"\n⏳ {data['message']}")
                    print(f"\n等待以下村民提交行动:")
                    for node_id in waiting_for:
                        print(f"   - {node_id}")
                    print("\n💡 提示: 你可以继续做其他操作（交易等），或者等待...")
            else:
                print(f"\n✗ 提交失败: {response.json().get('message', '未知错误')}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def check_action_status(self):
        """查看当前行动提交状态"""
        try:
            response = requests.get(f"{self.coordinator_url}/action/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                print("\n" + "="*50)
                print("  行动提交状态")
                print("="*50)
                print(f"\n总村民数: {data['total_villagers']}")
                print(f"已提交: {data['submitted']}/{data['total_villagers']}")
                
                if data['pending_actions']:
                    print(f"\n已提交的行动:")
                    for node_id, action in data['pending_actions'].items():
                        print(f"   {node_id}: {action}")
                
                if data['waiting_for']:
                    print(f"\n等待提交:")
                    for node_id in data['waiting_for']:
                        print(f"   - {node_id}")
                else:
                    print(f"\n✓ 所有村民已提交，时间即将推进")
                
                print("="*50)
            else:
                print("\n✗ 无法获取状态")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def get_merchant_prices(self):
        """获取商人价格表"""
        try:
            response = requests.get(f"{self.merchant_url}/prices", timeout=5)
            if response.status_code == 200:
                prices = response.json()
                print("\n" + "="*50)
                print("  商人价格表")
                print("="*50)
                print("\n📤 商人出售 (你购买):")
                for item, price in prices['buy'].items():
                    print(f"   {item}: {price}金币")
                
                print("\n📥 商人收购 (你出售):")
                for item, price in prices['sell'].items():
                    print(f"   {item}: {price}金币")
                print("="*50)
            else:
                print("\n✗ 无法获取价格表")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def show_help(self):
        """显示帮助"""
        print("\n" + "="*50)
        print("  命令列表")
        print("="*50)
        print("\n基本命令:")
        print("  info / i        - 查看村民状态")
        print("  time / t        - 查看当前时间")
        print("  status / s      - 查看所有村民的提交状态")
        print("  prices / p      - 查看商人价格")
        print("  help / h / ?    - 显示此帮助")
        print("  quit / q / exit - 退出")
        
        print("\n村民操作:")
        print("  create          - 创建新村民")
        print("  produce / work  - 执行生产（消耗1行动点）")
        print("  buy <物品> <数量>   - 从商人购买（不消耗行动点）")
        print("  sell <物品> <数量>  - 出售给商人（不消耗行动点）")
        print("  sleep / rest    - 睡眠恢复体力（不消耗行动点）")
        
        print("\n时间同步系统:")
        print("  submit work     - 提交'工作'行动（完成生产后）")
        print("  submit sleep    - 提交'睡眠'行动（睡眠后）")
        print("  submit idle     - 提交'空闲'行动（什么都不做）")
        print("  ")
        print("  ⚠️  只有所有村民都提交行动后，时间才会推进！")
        print("  这是一个分布式同步屏障（Barrier Synchronization）")
        
        print("\n示例工作流:")
        print("  buy seed 5      → 购买种子")
        print("  produce         → 生产小麦")
        print("  produce         → 再次生产")
        print("  produce         → 第三次生产")
        print("  submit work     → 提交行动，等待其他村民")
        print("  [等待...]       → 其他村民也提交后，时间自动推进")
        
        print("\n职业生产规则:")
        print("  farmer (农夫):     1种子 → 5小麦 (20体力, 1行动点)")
        print("  chef (厨师):       3小麦 → 2面包 (15体力, 1行动点)")
        print("  carpenter (木工):  10木材 → 1住房 (30体力, 1行动点)")
        print("="*50)
    
    def run(self):
        """运行交互式CLI"""
        print("\n" + "="*60)
        print("  分布式虚拟小镇 - 村民控制台")
        print("="*60)
        print(f"\n连接到村民节点: localhost:{self.villager_port}")
        
        # 检查连接
        if not self.check_connection():
            print("\n✗ 无法连接到村民节点，请确保节点正在运行")
            print(f"   命令: python villager.py --port {self.villager_port} --id <名称>")
            return
        
        print("✓ 连接成功!")
        print(f"当前时间: {self.get_current_time()}")
        
        # 检查村民是否已创建
        info = self.get_villager_info()
        if info:
            print(f"✓ 村民已就绪: {info['name']}")
            self.display_villager_info(info)
        else:
            print("\n! 村民未创建，请先创建村民")
            print("  输入 'create' 开始创建")
        
        print("\n输入 'help' 查看所有命令")
        
        # 主循环
        while True:
            try:
                cmd = input(f"\n[{self.get_current_time()}] > ").strip().lower()
                
                if not cmd:
                    continue
                
                parts = cmd.split()
                command = parts[0]
                
                # 退出命令
                if command in ['quit', 'q', 'exit']:
                    print("\n再见！")
                    break
                
                # 帮助命令
                elif command in ['help', 'h', '?']:
                    self.show_help()
                
                # 信息命令
                elif command in ['info', 'i']:
                    self.display_villager_info()
                
                # 时间命令
                elif command in ['time', 't']:
                    print(f"\n当前时间: {self.get_current_time()}")
                
                # 查看提交状态
                elif command in ['status', 's']:
                    self.check_action_status()
                
                # 提交行动
                elif command == 'submit' and len(parts) >= 2:
                    action_type = parts[1]
                    if action_type in ['work', 'sleep', 'idle']:
                        self.submit_action(action_type)
                    else:
                        print(f"\n✗ 无效的行动类型: {action_type}")
                        print("   有效选项: work, sleep, idle")
                
                # 价格表
                elif command in ['prices', 'p']:
                    self.get_merchant_prices()
                
                # 创建村民
                elif command == 'create':
                    print("\n=== 创建村民 ===")
                    name = input("名字: ").strip()
                    print("职业选项: farmer (农夫), chef (厨师), carpenter (木工)")
                    occupation = input("职业: ").strip()
                    print("性别选项: male (男), female (女)")
                    gender = input("性别: ").strip()
                    personality = input("性格: ").strip()
                    
                    if name and occupation and gender and personality:
                        self.create_villager(name, occupation, gender, personality)
                    else:
                        print("\n✗ 信息不完整")
                
                # 生产
                elif command in ['produce', 'work']:
                    self.produce()
                
                # 购买
                elif command == 'buy' and len(parts) >= 3:
                    item = parts[1]
                    try:
                        quantity = int(parts[2])
                        self.trade('buy', item, quantity)
                    except ValueError:
                        print("\n✗ 数量必须是整数")
                
                # 出售
                elif command == 'sell' and len(parts) >= 3:
                    item = parts[1]
                    try:
                        quantity = int(parts[2])
                        self.trade('sell', item, quantity)
                    except ValueError:
                        print("\n✗ 数量必须是整数")
                
                # 睡眠
                elif command in ['sleep', 'rest']:
                    self.sleep()
                
                # 未知命令
                else:
                    print(f"\n✗ 未知命令: {command}")
                    print("   输入 'help' 查看所有命令")
                
            except KeyboardInterrupt:
                print("\n\n使用 'quit' 退出")
            except Exception as e:
                print(f"\n✗ 错误: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='村民节点交互式CLI')
    parser.add_argument('--port', type=int, required=True, 
                       help='村民节点端口号')
    parser.add_argument('--coordinator', type=int, default=5000,
                       help='协调器端口 (默认: 5000)')
    parser.add_argument('--merchant', type=int, default=5001,
                       help='商人端口 (默认: 5001)')
    args = parser.parse_args()
    
    cli = VillagerCLI(args.port, args.coordinator, args.merchant)
    cli.run()


if __name__ == '__main__':
    main()

