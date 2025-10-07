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
        self.pending_trades = {}  # 当前等待响应的交易，key为trade_id
    
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
        
        # 根据行动状态显示提示
        action_status = ""
        if info.get('has_submitted_action', False):
            action_status = " [已提交，等待时间推进]"
        else:
            action_status = " [可以行动：工作/睡眠/空闲]"
        
        print("\n" + "="*50)
        print(f"  {info['name']} - {info['occupation']}")
        print("="*50)
        print(f"性别: {info['gender']}")
        print(f"性格: {info['personality']}")
        print(f"⚡ 体力: {info['stamina']}/{info['max_stamina']}")
        print(f"🎯 行动状态: {'已提交' if info.get('has_submitted_action', False) else '未提交'}{action_status}")
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
        """生产（自动提交work）"""
        try:
            response = requests.post(f"{self.villager_url}/action/produce", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ {data['message']}")
                
                # 显示提交结果
                submit_result = data.get('submit_result', {})
                if submit_result.get('all_ready'):
                    print("\n🎉 所有村民已准备就绪，时间已推进！")
                    print(f"   新时间: {submit_result.get('new_time', {})}")
                elif submit_result.get('waiting_for'):
                    waiting_for = submit_result.get('waiting_for', [])
                    print(f"\n⏳ 已自动提交'work'行动，等待其他村民")
                    print(f"   等待中: {len(waiting_for)} 个村民")
                
                villager_data = data['villager']
                self.display_villager_info(villager_data)
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
        """睡眠（自动提交sleep）"""
        try:
            response = requests.post(f"{self.villager_url}/action/sleep", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ {data['message']}")
                
                # 显示提交结果
                submit_result = data.get('submit_result', {})
                if submit_result.get('all_ready'):
                    print("\n🎉 所有村民已准备就绪，时间已推进！")
                    print(f"   新时间: {submit_result.get('new_time', {})}")
                elif submit_result.get('waiting_for'):
                    waiting_for = submit_result.get('waiting_for', [])
                    print(f"\n⏳ 已自动提交'sleep'行动，等待其他村民")
                    print(f"   等待中: {len(waiting_for)} 个村民")
                
                villager_data = data['villager']
                self.display_villager_info(villager_data)
            else:
                print(f"\n✗ {response.json()['message']}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def eat(self):
        """吃面包恢复体力"""
        try:
            response = requests.post(f"{self.villager_url}/action/eat", timeout=5)
            
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
                    for node in waiting_for:
                        if isinstance(node, dict):
                            print(f"   - {node['display_name']}")
                        else:
                            print(f"   - {node}")
                    print("\n💡 提示: 你可以继续做其他操作（交易等），或者等待...")
            else:
                print(f"\n✗ 提交失败: {response.json().get('message', '未知错误')}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def get_all_villagers(self):
        """获取所有村民节点"""
        try:
            response = requests.get(f"{self.coordinator_url}/nodes", timeout=5)
            if response.status_code == 200:
                data = response.json()
                villagers = {}
                for node in data['nodes']:
                    if node['node_type'] == 'villager':
                        # 构建显示名称
                        display_name = node['node_id']
                        if node.get('name') and node['name'] != node['node_id']:
                            if node.get('occupation'):
                                display_name = f"{node['name']} ({node['occupation']})"
                            else:
                                display_name = node['name']
                        
                        villagers[node['node_id']] = {
                            'address': node['address'],
                            'display_name': display_name
                        }
                return villagers
            return {}
        except:
            return {}
    
    def trade_with_villager(self, target_node: str, item: str, quantity: int, price: int, offer_type: str):
        """与其他村民交易（点对点）"""
        try:
            # 获取当前村民信息（包含node_id）
            my_info = self.get_villager_info()
            if not my_info:
                print("\n✗ 请先创建村民")
                return
            
            my_node_id = my_info.get('node_id')
            
            # 检查是否与自己交易
            if target_node == my_node_id:
                print(f"\n✗ 不能与自己交易！")
                print("   请选择其他村民节点")
                return
            
            # 获取所有村民节点
            villagers = self.get_all_villagers()
            
            # 支持通过node_id查找
            target_address = None
            target_id = None
            
            if target_node in villagers:
                target_info = villagers[target_node]
                target_address = target_info['address']
                target_id = target_node
            else:
                print(f"\n✗ 找不到村民节点: {target_node}")
                print(f"\n可用的村民:")
                for nid, info in villagers.items():
                    if nid != my_node_id:  # 不显示自己
                        print(f"   {nid}: {info['display_name']}")
                print("\n💡 提示: 使用节点ID")
                print("   例如: trade node1 buy wheat 10 100")
                return
            
            # 获取当前村民名称（my_info已在前面获取）
            my_name = my_info['name']
            
            # 发送交易请求
            print(f"\n📤 向 {target_node} 发送交易请求...")
            
            response = requests.post(
                f"http://{target_address}/trade/request",
                json={
                    'from': my_name,
                    'from_address': f'localhost:{self.villager_port}',
                    'item': item,
                    'quantity': quantity,
                    'price': price,
                    'offer_type': offer_type
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                trade_id = data['trade_id']
                
                if offer_type == 'buy':
                    print(f"✓ 交易请求已发送")
                    print(f"  你想从 {target_node} 购买 {quantity}x {item}, 出价 {price}金币")
                else:
                    print(f"✓ 交易请求已发送")
                    print(f"  你想向 {target_node} 出售 {quantity}x {item}, 要价 {price}金币")
                
                print(f"\n⏳ 等待 {target_node} 接受或拒绝...")
                print(f"💡 提示: 对方需要在CLI中输入 'accept' 或 'reject' 命令")
                
                # 保存交易信息到字典中
                self.pending_trades[trade_id] = {
                    'target': target_id,
                    'target_address': target_address,
                    'item': item,
                    'quantity': quantity,
                    'price': price,
                    'type': offer_type,
                    'trade_id': trade_id,
                    'status': 'pending'  # 标记状态
                }
            else:
                print(f"\n✗ 发送交易请求失败")
        
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def check_my_pending_trade_status(self):
        """检查自己发起的交易状态"""
        if not self.pending_trades:
            return
        
        for trade_id, trade in list(self.pending_trades.items()):
            # 如果已经提示过，就不再提示
            if trade.get('status') == 'ready_to_confirm':
                continue
            
            try:
                # 向对方查询交易状态
                response = requests.get(
                    f"http://{trade['target_address']}/trade/pending",
                    timeout=2
                )
                
                if response.status_code == 200:
                    data = response.json()
                    trades_list = data.get('pending_trades', [])
                    
                    # 查找我们的交易
                    for remote_trade in trades_list:
                        if remote_trade['trade_id'] == trade_id:
                            if remote_trade.get('status') == 'accepted':
                                # 对方已经接受，提示用户confirm
                                print("\n" + "="*60)
                                print(f"🎉 对方已接受你的交易请求！[{trade_id}]")
                                print("="*60)
                                print(f"交易详情:")
                                if trade['type'] == 'buy':
                                    print(f"  购买 {trade['quantity']}x {trade['item']}")
                                    print(f"  支付 {trade['price']}金币")
                                else:
                                    print(f"  出售 {trade['quantity']}x {trade['item']}")
                                    print(f"  获得 {trade['price']}金币")
                                print(f"\n💡 输入 'confirm {trade_id}' 完成交易")
                                print(f"   或输入 'cancel {trade_id}' 取消")
                                print("="*60 + "\n")
                                
                                # 标记为已提示
                                self.pending_trades[trade_id]['status'] = 'ready_to_confirm'
                            break
            except:
                pass  # 静默失败
    
    def show_my_pending_trades(self):
        """查看自己发起的待处理交易"""
        if not self.pending_trades:
            print("\n你没有发起任何待处理的交易")
            return
        
        print("\n" + "="*60)
        print("  你发起的交易请求")
        print("="*60)
        
        for i, (trade_id, trade) in enumerate(self.pending_trades.items(), 1):
            status = trade.get('status', 'pending')
            print(f"\n[{i}] 交易ID: {trade_id}")
            print(f"    对象: {trade['target']}")
            
            if trade['type'] == 'buy':
                print(f"    类型: 你想购买")
                print(f"    物品: {trade['quantity']}x {trade['item']}")
                print(f"    出价: {trade['price']}金币")
            else:
                print(f"    类型: 你想出售")
                print(f"    物品: {trade['quantity']}x {trade['item']}")
                print(f"    要价: {trade['price']}金币")
            
            # 根据状态显示不同的提示
            if status == 'ready_to_confirm':
                print(f"    状态: ✓ 对方已接受")
                print(f"    操作: confirm {trade_id} 完成交易")
            else:
                print(f"    状态: ⏳ 等待对方接受")
                print(f"    操作: 等待对方响应或 cancel {trade_id} 取消")
        
        print("="*60)
    
    def check_pending_trades(self):
        """查看收到的交易请求"""
        try:
            response = requests.get(f"{self.villager_url}/trade/pending", timeout=5)
            if response.status_code == 200:
                data = response.json()
                trades = data.get('pending_trades', [])
                
                if not trades:
                    print("\n没有收到待处理的交易请求")
                    return
                
                print("\n" + "="*60)
                print("  收到的交易请求")
                print("="*60)
                
                for i, trade in enumerate(trades, 1):
                    status = trade.get('status', 'pending')
                    print(f"\n[{i}] 交易ID: {trade['trade_id']}")
                    print(f"    来自: {trade['from']}")
                    
                    if trade['offer_type'] == 'buy':
                        print(f"    类型: 对方想购买")
                        print(f"    物品: {trade['quantity']}x {trade['item']}")
                        print(f"    出价: {trade['price']}金币")
                    else:
                        print(f"    类型: 对方想出售")
                        print(f"    物品: {trade['quantity']}x {trade['item']}")
                        print(f"    要价: {trade['price']}金币")
                    
                    # 根据状态显示不同的提示
                    if status == 'accepted':
                        print(f"    状态: ✓ 已接受（等待对方完成）")
                        print(f"    操作: 等待对方confirm或reject {trade['trade_id']} 取消")
                    else:
                        print(f"    状态: ⏳ 待处理")
                        print(f"    操作: accept {trade['trade_id']} 或 reject {trade['trade_id']}")
                
                print("="*60)
            else:
                print("\n✗ 无法获取交易请求")
        
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def accept_trade_request(self, trade_id: str):
        """接受交易请求"""
        try:
            # 先检查交易状态
            trades_response = requests.get(f"{self.villager_url}/trade/pending", timeout=5)
            if trades_response.status_code == 200:
                trades = trades_response.json().get('pending_trades', [])
                for trade in trades:
                    if trade['trade_id'] == trade_id:
                        if trade.get('status') == 'accepted':
                            print(f"\n⚠️  交易 {trade_id} 已经被接受过了")
                            print("   等待对方完成交易...")
                            return
                        break
            
            response = requests.post(
                f"{self.villager_url}/trade/accept",
                json={'trade_id': trade_id},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                trade = data.get('trade', {})
                
                print(f"\n✓ 交易已接受！")
                print(f"  交易ID: {trade_id}")
                print(f"  等待 {trade.get('from', '对方')} 完成交易...")
                print("\n💡 对方需要在他的终端执行 'confirm' 来完成交易")
            else:
                print(f"\n✗ 接受交易失败: {response.json().get('message', '未知错误')}")
        
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def reject_trade_request(self, trade_id: str):
        """拒绝交易请求"""
        try:
            response = requests.post(
                f"{self.villager_url}/trade/reject",
                json={'trade_id': trade_id},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"\n✓ 交易已拒绝: {trade_id}")
            else:
                print(f"\n✗ 拒绝交易失败")
        
        except Exception as e:
            print(f"\n✗ 错误: {e}")
    
    def complete_pending_trade(self, trade_id: str = None):
        """完成自己发起的交易（在对方accept后）"""
        if not self.pending_trades:
            print("\n✗ 没有待处理的交易")
            print("   使用 'trade <村民> buy/sell ...' 发起交易")
            return
        
        # 如果没有指定trade_id，检查是否只有一个待处理交易
        if trade_id is None:
            if len(self.pending_trades) == 1:
                trade_id = list(self.pending_trades.keys())[0]
            else:
                print("\n✗ 有多个待处理的交易，请指定交易ID")
                print("   可用的交易:")
                for tid, t in self.pending_trades.items():
                    status_text = "✓ 已接受" if t.get('status') == 'ready_to_confirm' else "⏳ 等待接受"
                    print(f"   {tid}: {t['type']} {t['quantity']}x {t['item']} ({status_text})")
                print(f"\n   使用 'confirm <trade_id>' 完成指定交易")
                return
        
        if trade_id not in self.pending_trades:
            print(f"\n✗ 找不到交易: {trade_id}")
            return
        
        try:
            trade = self.pending_trades[trade_id]
            
            # 检查对方是否接受了交易
            # 简化版：直接尝试完成
            
            # 先检查自己是否有足够的资源
            my_info = self.get_villager_info()
            
            if trade['type'] == 'buy':
                # 我要买，需要有足够的钱
                if my_info['inventory']['money'] < trade['price']:
                    print(f"\n✗ 货币不足 (需要{trade['price']}, 拥有{my_info['inventory']['money']})")
                    return
            else:
                # 我要卖，需要有足够的物品
                items = my_info['inventory'].get('items', {})
                if items.get(trade['item'], 0) < trade['quantity']:
                    print(f"\n✗ 物品不足 (需要{trade['quantity']}x {trade['item']})")
                    return
            
            print(f"\n正在与 {trade['target']} 完成交易...")
            
            # 通知对方完成交易
            response = requests.post(
                f"http://{trade['target_address']}/trade/complete",
                json={
                    'from': my_info['name'],
                    'item': trade['item'],
                    'quantity': trade['quantity'],
                    'price': trade['price'],
                    'type': trade['type'],  # 发起方的type：buy表示对方要卖给我，sell表示对方要买我的
                    'trade_id': trade.get('trade_id')  # 传递交易ID用于清理
                },
                timeout=5
            )
            
            if response.status_code == 200:
                # 更新自己的状态
                if trade['type'] == 'buy':
                    # 我购买：扣钱，加物品
                    result = requests.post(
                        f"{self.villager_url}/action/trade",
                        json={
                            'target': 'self',  # 标记为自己处理
                            'item': trade['item'],
                            'quantity': trade['quantity'],
                            'action': 'buy_from_villager',
                            'price': trade['price']
                        },
                        timeout=5
                    )
                else:
                    # 我出售：加钱，扣物品
                    result = requests.post(
                        f"{self.villager_url}/action/trade",
                        json={
                            'target': 'self',
                            'item': trade['item'],
                            'quantity': trade['quantity'],
                            'action': 'sell_to_villager',
                            'price': trade['price']
                        },
                        timeout=5
                    )
                
                # 检查自己的状态更新是否成功
                if result.status_code == 200:
                    print(f"\n✓ 交易完成！")
                    if trade['type'] == 'buy':
                        print(f"  你从 {trade['target']} 购买了 {trade['quantity']}x {trade['item']}")
                        print(f"  支付: {trade['price']}金币")
                    else:
                        print(f"  你向 {trade['target']} 出售了 {trade['quantity']}x {trade['item']}")
                        print(f"  获得: {trade['price']}金币")
                    
                    self.display_villager_info()
                    del self.pending_trades[trade_id]  # 清理已完成的交易
                else:
                    result_data = result.json()
                    print(f"\n✗ 交易失败: {result_data.get('message', '未知错误')}")
                    print("   交易已取消")
            else:
                error_msg = response.json().get('message', '未知错误')
                print(f"\n✗ 交易失败: {error_msg}")
                print("   可能的原因:")
                print("   - 对方没有足够的资源")
                print("   - 对方还没有接受交易")
        
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
                
                # 显示已提交的节点
                if data.get('submitted_nodes'):
                    print(f"\n已提交:")
                    for node in data['submitted_nodes']:
                        if isinstance(node, dict):
                            display_name = node['display_name']
                            node_id = node['node_id']
                            action = data['pending_actions'].get(node['node_id'], '未知')
                            print(f"   ✓ [{node_id}] {display_name}: {action}")
                        else:
                            print(f"   ✓ {node}")
                
                # 显示等待提交的节点
                if data['waiting_for']:
                    print(f"\n等待提交:")
                    for node in data['waiting_for']:
                        if isinstance(node, dict):
                            node_id = node['node_id']
                            display_name = node['display_name']
                            print(f"   - [{node_id}] {display_name}")
                        else:
                            print(f"   - {node}")
                else:
                    if data['total_villagers'] > 0:
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
        print("  produce / work  - 执行生产（自动提交work）")
        print("  sleep / rest    - 睡眠恢复体力（自动提交sleep）")
        print("  idle            - 跳过当前时段（提交idle）")
        print("  eat / e         - 吃面包恢复体力（不消耗行动，不提交）")
        print("  buy <物品> <数量>   - 从商人购买")
        print("  sell <物品> <数量>  - 出售给商人")
        
        print("\n村民间交易（P2P，不经过协调器）:")
        print("  trade <村民> buy <物品> <数量> <价格>  - 向其他村民购买")
        print("  trade <村民> sell <物品> <数量> <价格> - 向其他村民出售")
        print("  trades          - 查看收到的交易请求")
        print("  mytrades        - 查看自己发起的交易请求")
        print("  accept <ID>     - 接受指定的交易请求")
        print("  reject <ID>     - 拒绝指定的交易请求")
        print("  confirm [ID]    - 确认并完成自己发起的交易（可选指定ID）")
        print("  cancel [ID]     - 取消自己发起的交易（可选指定ID）")
        print("  ")
        print("  示例: trade bob buy wheat 10 100  → 向bob发起购买请求")
        print("        trades                       → 查看收到的请求")
        print("        mytrades                     → 查看自己发起的请求")
        print("        accept trade_0               → 接受交易")
        print("        confirm trade_0              → 发起方完成交易（指定ID）")
        
        print("\n时间同步系统:")
        print("  ⚠️  每个时段只能做一个主要行动（工作/睡眠/空闲）")
        print("  ⚠️  只有所有村民都提交行动后，时间才会推进！")
        print("  这是一个分布式同步屏障（Barrier Synchronization）")
        print("  ")
        print("  💡 produce和sleep会自动提交行动")
        print("  💡 如果想跳过当前时段，使用 'idle' 命令")
        print("  💡 交易和吃饭不消耗行动，可以随时进行")
        
        print("\n示例工作流（早上）:")
        print("  buy seed 1      → 购买种子（不消耗行动）")
        print("  produce         → 生产小麦（自动提交work）")
        print("  [等待...]       → 其他村民也提交后，时间推进到中午")
        print("  ")
        print("  中午:")
        print("  eat             → 吃面包恢复体力（不消耗行动）")
        print("  produce         → 再次生产（自动提交work）")
        print("  [等待...]       → 时间推进到晚上")
        print("  ")
        print("  晚上:")
        print("  sleep           → 睡眠（自动提交sleep）")
        print("  [等待...]       → 时间推进到第二天早上")
        
        print("\n职业生产规则:")
        print("  farmer (农夫):     1种子 → 5小麦 (20体力, 1行动点)")
        print("  chef (厨师):       3小麦 → 2面包 (15体力, 1行动点)")
        print("  carpenter (木工):  10木材 → 1住房 (30体力, 1行动点)")
        
        print("\n新增物品:")
        print("  bread (面包)      - 可从商人购买(20金币)或厨师制作")
        print("                      吃掉恢复30体力")
        print("  temp_room (临时房间券) - 从商人购买(15金币)")
        print("                      可用于睡眠，每日结算时消耗1个")
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
        print("💡 使用 'trades' 查看收到的请求，'mytrades' 查看自己发起的请求")
        
        # 主循环
        while True:
            try:
                # 检查自己发起的交易是否被接受
                self.check_my_pending_trade_status()
                
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
                
                # 提交空闲行动（跳过当前时段）
                elif command == 'idle' or (command == 'submit' and len(parts) >= 2 and parts[1] == 'idle'):
                    self.submit_action('idle')
                
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
                
                # 吃饭
                elif command in ['eat', 'e']:
                    self.eat()
                
                # 村民间交易
                elif command == 'trade' and len(parts) >= 5:
                    target = parts[1]
                    action = parts[2]  # buy or sell
                    item = parts[3]
                    try:
                        quantity = int(parts[4])
                        price = int(parts[5]) if len(parts) > 5 else quantity * 10
                        
                        if action in ['buy', 'sell']:
                            self.trade_with_villager(target, item, quantity, price, action)
                        else:
                            print(f"\n✗ 无效的交易类型: {action}")
                            print("   使用 'buy' 或 'sell'")
                    except ValueError:
                        print("\n✗ 数量和价格必须是整数")
                
                # 查看收到的交易请求
                elif command == 'trades':
                    self.check_pending_trades()
                
                # 查看自己发起的交易请求
                elif command == 'mytrades' or command == 'pending':
                    self.show_my_pending_trades()
                
                # 接受交易请求
                elif command == 'accept' and len(parts) >= 2:
                    trade_id = parts[1]
                    self.accept_trade_request(trade_id)
                
                # 拒绝交易请求
                elif command == 'reject' and len(parts) >= 2:
                    trade_id = parts[1]
                    self.reject_trade_request(trade_id)
                
                # 确认自己发起的交易
                elif command == 'confirm':
                    if len(parts) >= 2:
                        trade_id = parts[1]
                        self.complete_pending_trade(trade_id)
                    else:
                        self.complete_pending_trade()  # 不指定ID，自动选择
                
                # 取消自己发起的交易
                elif command == 'cancel':
                    if len(parts) >= 2:
                        trade_id = parts[1]
                        if trade_id in self.pending_trades:
                            print(f"\n✓ 已取消交易 {trade_id}")
                            del self.pending_trades[trade_id]
                        else:
                            print(f"\n✗ 找不到交易: {trade_id}")
                    else:
                        if self.pending_trades:
                            # 如果只有一个交易，直接取消
                            if len(self.pending_trades) == 1:
                                trade_id = list(self.pending_trades.keys())[0]
                                print(f"\n✓ 已取消交易 {trade_id}")
                                del self.pending_trades[trade_id]
                            else:
                                print("\n✗ 有多个待处理的交易，请指定交易ID")
                                for tid in self.pending_trades.keys():
                                    print(f"   {tid}")
                        else:
                            print("\n✗ 没有待处理的交易")
                
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

