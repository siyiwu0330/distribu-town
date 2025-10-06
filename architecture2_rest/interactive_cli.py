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
        
        print("\n" + "="*50)
        print(f"  {info['name']} - {info['occupation']}")
        print("="*50)
        print(f"性别: {info['gender']}")
        print(f"性格: {info['personality']}")
        print(f"体力: {info['stamina']}/{info['max_stamina']}")
        print(f"行动点: {info['action_points']}/3")
        print(f"已睡眠: {'是' if info['has_slept'] else '否'}")
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
                self.display_villager_info(response.json()['villager'])
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
    
    def advance_time(self):
        """推进时间（需要管理员权限）"""
        try:
            response = requests.post(f"{self.coordinator_url}/time/advance", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ {data['message']}")
                print(f"当前时间: {data['time']['day']}天 {data['time']['time_of_day']}")
            else:
                print("\n✗ 时间推进失败")
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
        print("  advance / a     - 推进时间")
        print("  prices / p      - 查看商人价格")
        print("  help / h / ?    - 显示此帮助")
        print("  quit / q / exit - 退出")
        
        print("\n村民操作:")
        print("  create          - 创建新村民")
        print("  produce / work  - 执行生产")
        print("  buy <物品> <数量>   - 从商人购买")
        print("  sell <物品> <数量>  - 出售给商人")
        print("  sleep / rest    - 睡眠恢复体力")
        
        print("\n示例:")
        print("  buy seed 5      - 购买5个种子")
        print("  sell wheat 10   - 出售10个小麦")
        print("  produce         - 进行生产")
        
        print("\n职业生产规则:")
        print("  farmer (农夫):     1种子 → 5小麦 (消耗20体力)")
        print("  chef (厨师):       3小麦 → 2面包 (消耗15体力)")
        print("  carpenter (木工):  10木材 → 1住房 (消耗30体力)")
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
                
                # 推进时间
                elif command in ['advance', 'a']:
                    self.advance_time()
                
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

