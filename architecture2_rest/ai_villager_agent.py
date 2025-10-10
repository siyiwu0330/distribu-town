"""
AI村民代理 - 简化版（只支持ReAct模式）
"""

import requests
import openai
import time
import os
import sys
from datetime import datetime
from typing import Dict

class AIVillagerAgent:
    """AI村民代理（ReAct模式）"""
    
    def __init__(self, villager_port: int, coordinator_port: int = 5000, merchant_port: int = 5001, 
                 api_key: str = None, model: str = "gpt-4o"):
        self.villager_url = f"http://localhost:{villager_port}"
        self.coordinator_url = f"http://localhost:{coordinator_port}"
        self.merchant_url = f"http://localhost:{merchant_port}"
        self.villager_port = villager_port
        
        # OpenAI配置
        self.api_key = api_key
        self.model = model
        if api_key:
            openai.api_key = api_key
        
        # 村民信息
        self.villager_info = None
        self.villager_name = None
        self.villager_occupation = None
        
        # 运行状态
        self.running = False
        self.decision_thread = None
        
        # 决策历史
        self.decision_history = []
        
        # 交易跟踪
        self.sent_trades_tracker = {}  # 跟踪已发送的交易请求
        
        # 消息跟踪
        self.sent_messages_tracker = []  # 跟踪最近发送的消息
        
        print(f"[AI Agent] 初始化完成，连接到村民节点: {villager_port}")
    
    def check_connection(self) -> bool:
        """检查连接"""
        try:
            response = requests.get(f"{self.villager_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def create_villager(self, name: str, occupation: str, gender: str, personality: str = "neutral"):
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
                result = response.json()
                if result['success']:
                    self.villager_info = result['villager']
                    self.villager_name = name
                    self.villager_occupation = occupation
                    print(f"[AI Agent] ✓ 村民创建成功: {name} ({occupation})")
                    return True
                else:
                    print(f"[AI Agent] ✗ 村民创建失败: {result.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"[AI Agent] ✗ 村民创建失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[AI Agent] ✗ 村民创建异常: {e}")
            return False
    
    def get_villager_info(self):
        """获取村民信息"""
        try:
            response = requests.get(f"{self.villager_url}/villager", timeout=5)
            if response.status_code == 200:
                result = response.json()
                # REST API直接返回村民数据，不是包装在success/villager中
                return result
            return None
        except:
            return None
    
    def get_current_time(self):
        """获取当前时间"""
        try:
            response = requests.get(f"{self.coordinator_url}/time", timeout=5)
            if response.status_code == 200:
                result = response.json()
                return result.get('time', '')
            return ''
        except:
            return ''
    
    def get_action_status(self):
        """获取行动状态"""
        try:
            response = requests.get(f"{self.coordinator_url}/action_status", timeout=5)
            if response.status_code == 200:
                return response.json()
            return {}
        except:
            return {}
    
    def get_merchant_prices(self):
        """获取商人价格"""
        try:
            response = requests.get(f"{self.merchant_url}/prices", timeout=5)
            if response.status_code == 200:
                return response.json()
            return {}
        except:
            return {}
    
    def get_online_villagers(self):
        """获取在线村民"""
        try:
            response = requests.get(f"{self.coordinator_url}/nodes", timeout=5)
            if response.status_code == 200:
                result = response.json()
                return result.get('nodes', [])
            return []
        except:
            return []
    
    def get_messages(self):
        """获取消息"""
        try:
            response = requests.get(f"{self.villager_url}/messages", timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    return result['messages']
            return []
        except:
            return []
    
    def get_trades_received(self):
        """获取收到的交易请求"""
        try:
            response = requests.get(f"{self.merchant_url}/trades", params={'type': 'received', 'villager_id': self.villager_name}, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    return result['trades']
            return []
        except:
            return []
    
    def get_trades_sent(self):
        """获取发送的交易请求"""
        try:
            response = requests.get(f"{self.merchant_url}/trades", params={'type': 'sent', 'villager_id': self.villager_name}, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    return result['trades']
            return []
        except:
            return []
    
    def execute_action(self, action: str, **kwargs) -> bool:
        """执行行动"""
        try:
            if action == "buy":
                response = requests.post(
                    f"{self.merchant_url}/buy",
                    json={
                        'buyer_id': self.villager_name,
                        'item': kwargs['item'],
                        'quantity': kwargs['quantity']
                    },
                    timeout=5
                )
            elif action == "sell":
                response = requests.post(
                    f"{self.merchant_url}/sell",
                    json={
                        'seller_id': self.villager_name,
                        'item': kwargs['item'],
                        'quantity': kwargs['quantity']
                    },
                    timeout=5
                )
            elif action == "produce":
                response = requests.post(f"{self.villager_url}/produce", timeout=5)
            elif action == "sleep":
                response = requests.post(f"{self.villager_url}/sleep", timeout=5)
            elif action == "eat":
                response = requests.post(f"{self.villager_url}/eat", timeout=5)
            elif action == "idle":
                response = requests.post(f"{self.villager_url}/idle", timeout=5)
            elif action == "price":
                # price行动不需要调用API，直接返回成功
                return True
            elif action == "send_message":
                response = requests.post(
                    f"{self.villager_url}/messages/send",
                    json={
                        'target': kwargs['target'],
                        'content': kwargs['content'],
                        'type': kwargs.get('type', 'private')
                    },
                    timeout=5
                )
            elif action == "create_trade":
                response = requests.post(
                    f"{self.merchant_url}/trades",
                    json={
                        'from': self.villager_name,
                        'to': kwargs['target'],
                        'offer_type': kwargs['trade_action'],
                        'item': kwargs['item'],
                        'quantity': kwargs['quantity'],
                        'price': kwargs['price']
                    },
                    timeout=5
                )
            elif action == "accept_trade":
                response = requests.post(
                    f"{self.merchant_url}/trades/{kwargs['trade_id']}/accept",
                    json={'villager_id': self.villager_name},
                    timeout=5
                )
            elif action == "reject_trade":
                response = requests.post(
                    f"{self.merchant_url}/trades/{kwargs['trade_id']}/reject",
                    json={'villager_id': self.villager_name},
                    timeout=5
                )
            elif action == "confirm_trade":
                response = requests.post(
                    f"{self.merchant_url}/trades/{kwargs['trade_id']}/confirm",
                    json={'villager_id': self.villager_name},
                    timeout=5
                )
            elif action == "cancel_trade":
                response = requests.post(
                    f"{self.merchant_url}/trades/{kwargs['trade_id']}/cancel",
                    json={'villager_id': self.villager_name},
                    timeout=5
                )
            else:
                print(f"[AI Agent] ✗ 未知行动: {action}")
                return False
            
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
            else:
                print(f"[AI Agent] ✗ 行动失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[AI Agent] ✗ 执行行动异常: {e}")
            return False
    
    def generate_decision(self, context: Dict) -> Dict:
        """生成决策（ReAct模式）"""
        if not self.api_key:
            print("[AI Agent] ✗ 未配置API Key，无法使用GPT")
            return {"action": "idle", "reason": "No API key configured"}
        
        try:
            # 使用ReAct结构
            prompt = self._build_react_prompt(context)
            system_prompt = self._get_react_system_prompt()
            max_tokens = 800
            
            # 调试：打印GPT看到的状态
            print(f"[AI Agent DEBUG] GPT看到的状态:")
            print(f"  体力: {context.get('villager', {}).get('stamina')}/{context.get('villager', {}).get('max_stamina')}")
            print(f"  货币: {context.get('villager', {}).get('inventory', {}).get('money')}")
            print(f"  物品: {context.get('villager', {}).get('inventory', {}).get('items')}")
            print(f"  消息: {len(context.get('messages', []))} 条")
            print(f"  交易请求: {len(context.get('trades_received', []))} 条")
            print(f"  发送交易: {len(context.get('trades_sent', []))} 条")
            print(f"  已提交行动: {context.get('villager', {}).get('has_submitted_action', False)}")
            print(f"  其他村民状态: {[(v['name'], v.get('has_submitted_action', False)) for v in context.get('villagers', [])]}")
            
            # 显示详细的交易信息
            trades_received = context.get('trades_received', [])
            if trades_received:
                print(f"[AI Agent DEBUG] 收到的交易请求详情:")
                for trade in trades_received:
                    print(f"  {trade.get('trade_id', '')}: {trade.get('from', 'Unknown')} 想{trade.get('offer_type', '')} {trade.get('item', '')} x{trade.get('quantity', 0)} for {trade.get('price', 0)} gold")
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            decision_text = response.choices[0].message.content.strip()
            
            # 解析ReAct格式的响应
            decision = self._parse_react_decision(decision_text)
            
            # 记录决策历史
            self.decision_history.append({
                'timestamp': datetime.now().isoformat(),
                'context': context,
                'decision': decision,
                'raw_response': decision_text
            })
            
            return decision
            
        except Exception as e:
            print(f"[AI Agent] ✗ GPT决策生成失败: {e}")
            return {"action": "idle", "reason": f"GPT error: {str(e)}"}
    
    def _get_react_system_prompt(self) -> str:
        """获取ReAct系统提示词"""
        return """You are a **ReAct Villager Agent** in the *Distributed Virtual Town* simulation.

You must follow the ReAct (Reasoning + Acting) pattern:

**THOUGHT**: Analyze the current situation, consider your goals, and reason about what action to take.
**ACTION**: Execute exactly one command based on your reasoning.
**OBSERVATION**: The result of your action will be provided for the next cycle.

## Available Actions:
- `buy <item> <quantity>` - Buy from merchant (no action cost)
- `sell <item> <quantity>` - Sell to merchant (no action cost)  
- `eat` - Eat bread to restore stamina (no action cost)
- `produce` - Produce items (consumes action point + stamina)
- `sleep` - Sleep to restore stamina (consumes action point, evening only, REQUIRES HOUSE OR TEMP_ROOM!)
- `idle` - Skip current segment (consumes action point)
- `price` - Check merchant prices (no action cost)
- `mytrades` - Check all trade requests (sent and received) (no action cost) - **READ ONLY**
- `trade <node_id> <buy/sell> <item> <quantity> <total_price>` - **SEND trade request to villager** 
  **⚠️ IMPORTANT: Use node_id (like 'node1', 'node2') NOT villager names!**
- `accept <trade_id>` - Accept received trade request (receiver only)
- `reject <trade_id>` - Reject received trade request (receiver only)
- `cancel <trade_id>` - Cancel your own trade request (initiator only)
- `confirm <trade_id>` - Confirm trade (both parties must confirm to complete)
- `send <node_id> <message>` - Send message to another villager
  **⚠️ IMPORTANT: Use node_id (like 'node1', 'node2') NOT villager names!**

## Game Rules:
- Each time segment allows ONE main action (produce/sleep/idle)
- Trading and eating don't consume action points
- Stamina: 0-100, work consumes stamina, sleep restores stamina
- Hunger: -10 stamina daily, -20 extra if no sleep at night
- **CRITICAL: Sleep requires a HOUSE or TEMP_ROOM! Temp room costs 15 gold (affordable!) and lasts 1 day.**
- **IMPORTANT: Buy and produce are SEPARATE decisions! Buy resources first, then produce in the next decision.**
- **ACTION SUBMISSION STATUS: If you have already submitted your action for this time segment, you can still:**
  - Respond to trade requests (accept/reject)
  - Send and read messages
  - Eat bread to restore stamina
  - Check prices and trades
  - **Send new trade requests to other villagers**
  - **BUT CANNOT: produce, sleep, buy, sell, or idle (these consume action points)**
  - **IMPORTANT: Trading is ALWAYS allowed, even after submitting actions!**

## Priority Order (CRITICAL - Follow This Order):
1. **SURVIVAL**: 
   - Eat if stamina ≤ 35
   - ⚠️ **EVENING/NIGHT WITHOUT HOUSE**: Buy temp_room (15 gold) BEFORE sleeping!
   - Sleep if night and stamina ≤ 45 (requires house/temp_room)

2. **CONFIRM TRADES**: ⚠️ Check `mytrades` and `trades` for status="accepted" → USE `confirm <trade_id>`!

3. **CHECK PRICES** (if not checked recently):
   - Look at PREVIOUS OBSERVATIONS first
   - If last 2-3 decisions include "PRICE" action → prices already known, can skip
   - Recommended to check once before making economic decisions
   - Prices are stable within the same day

4. **ACQUIRE RESOURCES**: Buy materials from merchant if needed
   - Recommended to check prices first (Step 3) for informed decisions
   - Knowing prices helps optimize spending

5. **PRODUCTION**: Produce items if you have materials and stamina ≥ 20

6. **TRADING**: 
   - First: Handle received trade requests (accept/reject)
   - Then: Send P2P trade requests (recommended to use prices from step 3)
   - Format: `trade <node_id> <buy/sell> <item> <quantity> <price>`
   - Knowing current prices helps make fair offers

7. **COMMUNICATION**: For non-trade coordination when needed

8. **IDLE**: When no productive action is currently possible

💡 **Smart Strategy**: Check prices early in your decision cycle
- Helps you make informed buy/sell/trade decisions
- Allows you to compare merchant vs P2P options
- One price check can inform multiple subsequent decisions

## P2P Trading Strategy (HIGH PRIORITY):
- **Selling**: Try to sell products to villagers at better prices than merchant buy prices
- **Buying**: Try to buy materials from villagers at better prices than merchant sell prices
- **Smart Pricing**: Use prices between merchant buy/sell prices (e.g., merchant buys at 5, sells at 10 → use 7)
- **Targeting**: Farmers have wheat/seeds, Chefs have bread, Builders have wood
- **No Spam**: Don't send duplicate trade requests to the same villager
- **⚠️ DIRECT TRADING**: Send `trade` command DIRECTLY, NO negotiation messages!
- **Commands**: `trades`=view received, `mytrades`=view sent, `trade`=send new request
- **Fallback**: If no response after 2-3 decisions, trade with merchant instead
- **Examples (DO THIS - USE NODE_ID)**:
  - Farmer (node1) selling to Chef (node2): `trade node2 sell wheat 5 35` (5 wheat at 7 gold each)
  - Chef (node2) buying from Farmer (node1): `trade node1 buy wheat 3 21` (3 wheat at 7 gold each)

## Trading Workflow (Centralized System via Merchant):
1. **Initiate Phase**: Use `trade` command to create trade request (status: pending)
2. **Accept/Reject Phase**: Receiver uses `accept` or `reject` on the trade
   - After `accept`: status changes to "accepted"
3. **Confirm Phase**: ⚠️ BOTH parties must `confirm` to complete the trade!
   - Check `mytrades` or `trades` to see if status is "accepted"
   - If status is "accepted", use `confirm <trade_id>` to finalize
   - Trade completes only when BOTH parties confirm
4. **Cancel Phase**: Initiator can use `cancel` before receiver accepts

**TRADE FLOW EXAMPLE** (⚠️ USE NODE_ID, NOT NAME):
- Alice (node1): `trade node2 buy wheat 3 21` → Creates trade_1
- Bob (node2): `trades` → Sees trade_1 from Alice
- Bob: `accept trade_1` → Accepts the trade (resources checked)
- Bob: `confirm trade_1` → Bob confirms
- Alice: `confirm trade_1` → Alice confirms → Trade completes automatically!

**CRITICAL POINTS**:
- **INVENTORY CHECK**: System checks resources when accepting trade
- **ATOMIC COMPLETION**: Trade completes when BOTH parties confirm
- **UNIQUE IDs**: All trades have unique IDs managed by Merchant
- **STATUS TRACKING**: Use `trades` and `mytrades` to monitor trade status
- **TRADE ID CLARITY**: `trades` shows requests YOU received, `mytrades` shows requests YOU sent
- **REJECT vs CANCEL**: Receiver uses `reject`, initiator uses `cancel`
- **PRICE NEGOTIATION**: 
  * If you RECEIVE a trade with bad price → `reject <trade_id>` + optionally send message with counter-offer
  * If your SENT trade is rejected → check `mytrades` status, then send new trade with adjusted price
  * Don't negotiate before sending first trade - let the trade request itself be the first offer!
- **PRODUCTIVITY FOCUS**: Don't get stuck negotiating - move to actual trades quickly!
- **NO SPAM**: Don't send duplicate trade requests to the same villager

## Trading Decision Process (Recommended Flow):
1. **Check prices when needed** (but avoid repeating):
   - Check PREVIOUS OBSERVATIONS: If you see "PRICE" action recently → prices already known
   - Use `price` command if you haven't checked recently (within last 2-3 decisions)
   - Once you know prices, you can use them for multiple decisions
   - Example: If merchant sells wheat at 10g, you can offer 7-8g for P2P buy

2. **Direct trade requests work well**: Skip lengthy negotiations
   - Less effective: send node2 "Hi, interested in wheat?" then wait for reply
   - More effective: After knowing prices, directly send: `trade node2 buy wheat 3 21`
   - Trade request itself serves as your offer

3. **Smart pricing strategy**: Base your P2P prices on merchant prices
   - For buying: Offer slightly more than merchant's buy price (e.g., 7g if merchant buys at 5g)
   - For selling: Ask slightly less than merchant's sell price (e.g., 9g if merchant sells at 10g)
   - Win-win pricing encourages trades!

4. **Use node_id for trades**: Look at "Online Villagers" list to find node_id (e.g., node1, node2)

5. **Avoid spam**: Don't send duplicate messages or trade requests

## Output Format:
Always follow this exact format:

THOUGHT: [Your reasoning about the current situation and what action to take]

ACTION: [Single command to execute]

Example:
THOUGHT: I'm a farmer with 0 seeds and 100 stamina. I need seeds to produce wheat. I should buy 1-2 seeds first.

ACTION: buy seed 2

Remember: Only output THOUGHT and ACTION. The OBSERVATION will be provided in the next cycle."""

    def _build_react_prompt(self, context: Dict) -> str:
        """构建ReAct提示词"""
        villager = context.get('villager', {})
        time_info = context.get('time', '')
        action_status = context.get('action_status', {})
        prices = context.get('prices', {})
        messages = context.get('messages', [])
        villagers = context.get('villagers', [])
        
        # 获取物品信息
        inventory = villager.get('inventory', {})
        items = inventory.get('items', {})
        money = inventory.get('money', 0)
        
        # 分析当前状态
        stamina = villager.get('stamina', 0)
        max_stamina = villager.get('max_stamina', 100)
        occupation = villager.get('occupation', 'Unknown')
        has_submitted = villager.get('has_submitted_action', False)
        has_slept = villager.get('has_slept', False)
        
        # 分析资源需求
        resource_analysis = ""
        if occupation == 'farmer':
            seed_count = items.get('seed', 0)
            resource_analysis = f"Farmer needs seeds to produce wheat. Current seeds: {seed_count}"
            if seed_count == 0:
                resource_analysis += " ⚠️ No seeds! Need to buy first."
            elif seed_count >= 1:
                resource_analysis += " ✓ Ready to produce wheat!"
        elif occupation == 'chef':
            wheat_count = items.get('wheat', 0)
            resource_analysis = f"Chef needs wheat to produce bread. Current wheat: {wheat_count}"
            if wheat_count < 3:
                resource_analysis += " ⚠️ Not enough wheat, need at least 3!"
            else:
                resource_analysis += " ✓ Ready to produce bread!"
        elif occupation == 'carpenter':
            wood_count = items.get('wood', 0)
            resource_analysis = f"Carpenter needs wood to build house. Current wood: {wood_count}"
            if wood_count < 10:
                resource_analysis += " ⚠️ Not enough wood, need at least 10!"
            else:
                resource_analysis += " ✓ Ready to build house!"
        
        # 分析体力状况
        stamina_analysis = ""
        if stamina < 30:
            stamina_analysis = "⚠️ 体力严重不足，需要立即恢复！"
        elif stamina < 50:
            stamina_analysis = "⚠️ 体力较低，建议恢复"
        elif stamina >= 50:
            stamina_analysis = "✓ 体力充足"
        
        # 分析睡眠状况
        sleep_analysis = ""
        if has_slept:
            sleep_analysis = "✓ 今日已睡眠"
        else:
            sleep_analysis = "⚠️ 今日未睡眠"
        
        # 分析时间信息
        is_morning = 'morning' in time_info.lower()
        is_noon = 'noon' in time_info.lower()
        is_evening = 'evening' in time_info.lower()
        is_night = 'night' in time_info.lower()
        
        # 当前时段建议
        segment_advice = ""
        if is_morning or is_noon:
            segment_advice = "PRODUCTION TIME - Focus on buying resources and producing"
        elif is_evening:
            segment_advice = "EVENING TIME - Should sleep if not yet slept today"
        
        # 获取消息和交易信息
        messages = self.get_messages()
        trades_received = self.get_trades_received()
        trades_sent = self.get_trades_sent()
        
        prompt = f"""=== CURRENT STATE ANALYSIS ===

Time: {time_info} - {segment_advice}
Villager: {villager.get('name', 'Unknown')} ({occupation})
Stamina: {stamina}/{max_stamina} {stamina_analysis}
Money: {money} gold
Action Submitted: {has_submitted}
Sleep Status: {sleep_analysis}

=== INVENTORY ===
{chr(10).join([f"- {item}: {count}" for item, count in items.items()]) if items else "No items"}

=== RESOURCE ANALYSIS ===
{resource_analysis}

=== ACTION STATUS ===
Total Villagers: {action_status.get('total_villagers', 0)}
Submitted: {action_status.get('submitted', 0)}
Waiting: {action_status.get('waiting_for', [])}

=== MERCHANT PRICES ===
{chr(10).join([f"- {item}: {price} gold" for item, price in prices.get('prices', {}).items()]) if prices.get('prices') else "Cannot get prices"}

=== MESSAGES ===
Messages Received: {len(messages)}
{chr(10).join([f"- From {msg.get('from', 'Unknown')}: {msg.get('content', '')[:50]}..." for msg in messages[:3]]) if messages else "No messages"}

Recently Sent Messages: {len(self.sent_messages_tracker)}
{chr(10).join([f"- To {msg['target']}: {msg['content'][:50]}..." for msg in self.sent_messages_tracker[-3:]]) if self.sent_messages_tracker else "No sent messages"}
⚠️ IMPORTANT: You have already sent the above messages. Don't send duplicate messages!

=== TRADES ===
Trades Received: {len(trades_received)}
{chr(10).join([f"- Trade {trade.get('trade_id', '')}: {trade.get('from', 'Unknown')} wants to {trade.get('offer_type', '')} {trade.get('item', '')} x{trade.get('quantity', 0)} for {trade.get('price', 0)} gold total ({trade.get('price', 0)//trade.get('quantity', 1)} gold each)" for trade in trades_received[:3]]) if trades_received else "No trade requests"}

Trades Sent: {len(trades_sent)}
{chr(10).join([f"- Trade {trade.get('id', '')}: {trade.get('action', '')} {trade.get('item', '')} x{trade.get('quantity', 0)} for {trade.get('price', 0)} gold" for trade in trades_sent[:3]]) if trades_sent else "No sent trades"}

=== ONLINE VILLAGERS ===
Online Villagers: {len(villagers)}
{chr(10).join([f"- {v['name']} ({v['occupation']}) - Action: {'✓ Submitted' if v.get('has_submitted_action', False) else '⏳ Pending'}" for v in villagers])}

=== ACTION SUBMISSION STATUS ===
Total Villagers: {len(villagers)}
Submitted: {sum(1 for v in villagers if v.get('has_submitted_action', False))}/{len(villagers)}
Waiting: {[v['name'] for v in villagers if not v.get('has_submitted_action', False)]}

=== RECENT OBSERVATIONS ===
{self._get_recent_observations()}

=== REFLECTIONS ===
{self._get_reflections()}

Remember: You are operating in a distributed system. Make decisions that maximize your villager's survival, productivity, and economic efficiency. Focus on actions that provide immediate value while building toward long-term sustainability.

QUANTITY HEURISTIC:
- Farmer: Buy just enough seeds to cover this period's production, keep a buffer of 1-2 if money ≥ 2× seed price
- Chef: Ensure wheat ≥ 3 before producing; keep bread reserve 2-3 for stamina
- Carpenter: Accumulate toward 10 wood; don't starve other needs
- Choose quantities dynamically; buy the minimum needed to enable production now, plus a small buffer if affordable"""
        
        return prompt
    
    def _get_recent_observations(self) -> str:
        """获取最近的观察结果"""
        if not self.decision_history:
            return "No previous observations."
        
        recent = self.decision_history[-5:]  # 最近5次决策
        observations = []
        
        for entry in recent:
            timestamp = entry['timestamp'][:19]  # 去掉毫秒
            decision = entry['decision']
            action = decision.get('action', 'unknown')
            command = decision.get('command', '')
            reason = decision.get('reason', 'No reason')[:80]  # 限制理由长度
            success = decision.get('success', True)
            error_msg = decision.get('error_message', '')
            
            if success:
                observations.append(f"[{timestamp}] {action.upper()} - SUCCESS")
                observations.append(f"  → Command: {command}")
                observations.append(f"  → Reason: {reason}")
            else:
                observations.append(f"[{timestamp}] {action.upper()} - FAILED")
                observations.append(f"  → Command: {command}")
                observations.append(f"  → Reason: {reason}")
                if error_msg:
                    observations.append(f"  → Error: {error_msg}")
        
        return "\n".join(observations)
    
    def _get_reflections(self) -> str:
        """获取反思"""
        if not self.decision_history:
            return "No reflections available."
        
        reflections = []
        
        # 检查最近的决策模式
        recent_decisions = self.decision_history[-3:]
        if len(recent_decisions) >= 2:
            last_action = recent_decisions[-1]['decision'].get('action', '')
            prev_action = recent_decisions[-2]['decision'].get('action', '')
            
            # 模式1: 重复购买但没有生产
            if last_action == 'buy' and prev_action == 'buy':
                reflections.append("⚠️ PATTERN DETECTED: You've been buying repeatedly without producing!")
                reflections.append("   → SUGGESTED ACTION: Produce items with your resources")
            
            # 模式2: 查看交易但没有处理
            elif last_action in ['trades', 'mytrades']:
                reflections.append("⚠️ PATTERN DETECTED: You checked trades but didn't act on them!")
                reflections.append("   → SUGGESTED ACTION: Accept/confirm trades, or send new trade request")
        
        return "\n".join(reflections) if reflections else "No specific patterns detected."
    
    def _parse_react_decision(self, decision_text: str) -> Dict:
        """解析ReAct格式的决策"""
        try:
            lines = decision_text.strip().split('\n')
            thought = ""
            action = "idle"
            reason = "No reason provided"
            command = "idle"
            
            # 解析THOUGHT和ACTION
            for line in lines:
                line = line.strip()
                if line.startswith('THOUGHT:'):
                    thought = line[8:].strip()
                elif line.startswith('ACTION:'):
                    action_line = line[7:].strip()
                    command = action_line
                    
                    # 解析具体行动
                    parts = action_line.split()
                    if len(parts) >= 1:
                        action = parts[0]
                        
                        # 解析不同行动的参数
                        if action == "buy" and len(parts) >= 3:
                            try:
                                quantity = int(parts[2])
                                return {
                                    "action": "buy",
                                    "reason": thought,
                                    "command": action_line,
                                    "item": parts[1],
                                    "quantity": quantity
                                }
                            except ValueError:
                                pass
                        elif action == "sell" and len(parts) >= 3:
                            try:
                                quantity = int(parts[2])
                                return {
                                    "action": "sell",
                                    "reason": thought,
                                    "command": action_line,
                                    "item": parts[1],
                                    "quantity": quantity
                                }
                            except ValueError:
                                pass
                        elif action == "trade" and len(parts) >= 6:
                            try:
                                quantity = int(parts[3])
                                price = int(parts[4])
                                return {
                                    "action": "trade",
                                    "reason": thought,
                                    "command": action_line,
                                    "target": parts[1],
                                    "trade_action": parts[2],
                                    "item": parts[3],
                                    "quantity": quantity,
                                    "price": price
                                }
                            except ValueError:
                                pass
                        elif action == "send" and len(parts) >= 3:
                            target = parts[1]
                            content = " ".join(parts[2:])
                            return {
                                "action": "send",
                                "reason": thought,
                                "command": action_line,
                                "target": target,
                                "content": content
                            }
                        elif action == "accept" and len(parts) >= 2:
                            trade_id = parts[1]
                            if not trade_id.startswith('trade_'):
                                trade_id = f"trade_{trade_id}"
                            return {
                                "action": "accept",
                                "reason": thought,
                                "command": action_line,
                                "trade_id": trade_id
                            }
                        elif action == "reject" and len(parts) >= 2:
                            trade_id = parts[1]
                            if not trade_id.startswith('trade_'):
                                trade_id = f"trade_{trade_id}"
                            return {
                                "action": "reject",
                                "reason": thought,
                                "command": action_line,
                                "trade_id": trade_id
                            }
                        elif action == "confirm" and len(parts) >= 2:
                            trade_id = parts[1]
                            if not trade_id.startswith('trade_'):
                                trade_id = f"trade_{trade_id}"
                            return {
                                "action": "confirm",
                                "reason": thought,
                                "command": action_line,
                                "trade_id": trade_id
                            }
                        elif action == "cancel" and len(parts) >= 2:
                            trade_id = parts[1]
                            if not trade_id.startswith('trade_'):
                                trade_id = f"trade_{trade_id}"
                            return {
                                "action": "cancel",
                                "reason": thought,
                                "command": action_line,
                                "trade_id": trade_id
                            }
            
            return {
                "action": action,
                "reason": thought or reason,
                "command": command
            }
            
        except Exception as e:
            print(f"[AI Agent] ✗ ReAct解析失败: {e}")
            return {"action": "idle", "reason": f"Parse error: {str(e)}", "command": "idle"}
    
    def execute_decision(self, decision: Dict, context: Dict) -> bool:
        """执行决策"""
        action = decision.get('action', 'idle')
        reason = decision.get('reason', 'No reason')
        
        print(f"[AI Agent] {self.villager_name} 思考: {reason}")
        print(f"[AI Agent] {self.villager_name} 行动: {decision.get('command', action)}")
        print(f"[AI Agent] 决策详情: {decision}")
        
        # 检查是否已提交行动
        has_submitted = context.get('villager', {}).get('has_submitted_action', False)
        
        # 如果已经提交了行动，限制可执行的行动类型
        if has_submitted:
            print(f"[AI Agent] {self.villager_name} 已经提交了行动，只能执行非推进时间的行动...")
            
            # 定义不允许的行动（这些会推进时间）
            forbidden_actions = ['produce', 'sleep', 'idle']
            
            if action in forbidden_actions:
                print(f"[AI Agent] ⚠️ 已提交行动，不能执行 {action}，改为处理消息和交易")
                
                # 检查是否有待处理的交易请求
                trades_received = context.get('trades_received', [])
                if trades_received:
                    print(f"[AI Agent] {self.villager_name} 发现 {len(trades_received)} 个待处理的交易请求")
                    self._handle_pending_trades(trades_received, context)
                
                # 检查是否有需要确认的已发送交易
                trades_sent = context.get('trades_sent', [])
                if trades_sent:
                    print(f"[AI Agent] {self.villager_name} 发现 {len(trades_sent)} 个已发送的交易")
                    self._handle_sent_trades(trades_sent, context)
                
                # 检查消息
                messages = context.get('messages', [])
                unread_messages = [msg for msg in messages if not msg.get('read', False)]
                if unread_messages:
                    print(f"[AI Agent] {self.villager_name} 发现 {len(unread_messages)} 条未读消息")
                
                print(f"[AI Agent] {self.villager_name} 已完成消息和交易处理，等待时间推进...")
                return True
        
        # 执行行动
        success = False
        error_message = None
        
        if action == "buy":
            success = self.execute_action("buy",
                                        item=decision.get('item'),
                                        quantity=decision.get('quantity'))
        elif action == "sell":
            success = self.execute_action("sell",
                                        item=decision.get('item'),
                                        quantity=decision.get('quantity'))
        elif action == "produce":
            success = self.execute_action("produce")
        elif action == "sleep":
            success = self.execute_action("sleep")
        elif action == "eat":
            success = self.execute_action("eat")
        elif action == "idle":
            success = self.execute_action("idle")
        elif action == "price":
            success = self.execute_action("price")
            if success:
                # 获取价格信息并记录
                prices = self.get_merchant_prices()
                if prices and self.decision_history:
                    last_decision = self.decision_history[-1]
                    last_decision['decision']['prices'] = prices
        elif action == "mytrades":
            success = self.execute_action("mytrades")
            if success:
                # 获取发送交易信息并记录
                trades = self.get_trades_sent()
                if trades and self.decision_history:
                    last_decision = self.decision_history[-1]
                    last_decision['decision']['mytrades'] = trades
        elif action == "trade":
            success = self.execute_action("create_trade",
                                        target=decision.get('target'),
                                        trade_action=decision.get('trade_action', 'buy'),
                                        item=decision.get('item'),
                                        quantity=decision.get('quantity'),
                                        price=decision.get('price'))
        elif action == "send":
            success = self.execute_action("send_message",
                                        target=decision.get('target', 'all'),
                                        content=decision.get('content', 'Hello!'),
                                        type='private')
            if success:
                # 记录已发送的消息
                self.sent_messages_tracker.append({
                    'target': decision.get('target'),
                    'content': decision.get('content'),
                    'timestamp': time.time()
                })
                # 只保留最近10条消息
                if len(self.sent_messages_tracker) > 10:
                    self.sent_messages_tracker = self.sent_messages_tracker[-10:]
        elif action == "accept":
            trade_id = decision.get('trade_id')
            if trade_id:
                success = self.execute_action("accept_trade", trade_id=trade_id)
            else:
                success = False
                error_message = "Accept trade failed: No trade ID provided"
        elif action == "reject":
            trade_id = decision.get('trade_id')
            if trade_id:
                success = self.execute_action("reject_trade", trade_id=trade_id)
            else:
                success = False
                error_message = "Reject trade failed: No trade ID provided"
        elif action == "cancel":
            trade_id = decision.get('trade_id')
            if trade_id:
                success = self.execute_action("cancel_trade", trade_id=trade_id)
            else:
                success = False
                error_message = "Cancel trade failed: No trade ID provided"
        elif action == "confirm":
            trade_id = decision.get('trade_id')
            if trade_id:
                success = self.execute_action("confirm_trade", trade_id=trade_id)
            else:
                success = False
                error_message = "Confirm trade failed: No trade ID provided"
        else:
            print(f"[AI Agent] ✗ 未知行动: {action}")
            success = False
            error_message = f"Unknown action: {action}"
        
        if success:
            print(f"[AI Agent] ✓ 执行行动成功: {action}")
            print(f"[AI Agent] ✓ {self.villager_name} 成功执行: {action}")
        else:
            print(f"[AI Agent] ✗ {self.villager_name} 执行失败: {action}")
            if error_message:
                print(f"[AI Agent] 错误信息: {error_message}")
        
        # 更新决策历史，记录执行结果
        if self.decision_history:
            last_decision = self.decision_history[-1]
            last_decision['decision']['success'] = success
            if error_message:
                last_decision['decision']['error_message'] = error_message
        
        return success
    
    def _handle_pending_trades(self, trades_received: list, context: Dict):
        """处理待处理的交易请求"""
        for trade in trades_received:
            trade_id = trade.get('trade_id', '')
            from_villager = trade.get('from', 'Unknown')
            offer_type = trade.get('offer_type', '')
            item = trade.get('item', '')
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0)
            
            print(f"[AI Agent] {self.villager_name} 处理交易请求: {offer_type} {quantity}x {item} for {price} gold from {from_villager}")
            
            # 简单的交易决策逻辑
            should_accept = False
            reason = ""
            
            # 获取当前状态
            villager = context.get('villager', {})
            inventory = villager.get('inventory', {})
            money = inventory.get('money', 0)
            items = inventory.get('items', {})
            
            # 获取商人价格作为参考
            prices = context.get('prices', {})
            merchant_prices = prices.get('prices', {})
            
            if offer_type == 'buy':
                # 对方想买我的物品
                my_item_count = items.get(item, 0)
                if my_item_count >= quantity:
                    # 我有足够的物品
                    merchant_buy_price = merchant_prices.get(item, 0) * quantity
                    if price >= merchant_buy_price * 0.8:  # 至少是商人价格的80%
                        should_accept = True
                        reason = f"价格合理 ({price} >= {merchant_buy_price * 0.8})"
                    else:
                        reason = f"价格太低 ({price} < {merchant_buy_price * 0.8})"
                else:
                    reason = f"物品不足 ({my_item_count} < {quantity})"
            else:
                # 对方想卖给我物品
                merchant_sell_price = merchant_prices.get(item, 0) * quantity
                if money >= price:
                    if price <= merchant_sell_price * 1.2:  # 最多是商人价格的120%
                        should_accept = True
                        reason = f"价格合理 ({price} <= {merchant_sell_price * 1.2})"
                    else:
                        reason = f"价格太高 ({price} > {merchant_sell_price * 1.2})"
                else:
                    reason = f"货币不足 ({money} < {price})"
            
            # 执行交易决策
            if should_accept:
                print(f"[AI Agent] {self.villager_name} 接受交易: {reason}")
                try:
                    success = self.execute_action("accept_trade", trade_id=trade_id)
                    if success:
                        print(f"[AI Agent] ✓ 交易接受成功")
                        # 发送消息通知发起方交易已接受
                        message = f"交易 {trade_id} 已接受！请使用 'confirm {trade_id}' 来确认交易。"
                        self.execute_action("send_message", target=from_villager, content=message)
                        print(f"[AI Agent] {self.villager_name} 已通知 {from_villager} 交易已接受")
                    else:
                        print(f"[AI Agent] ✗ 交易接受失败")
                except Exception as e:
                    print(f"[AI Agent] ✗ 交易接受异常: {e}")
            else:
                print(f"[AI Agent] {self.villager_name} 拒绝交易: {reason}")
                try:
                    success = self.execute_action("reject_trade", trade_id=trade_id)
                    if success:
                        print(f"[AI Agent] ✓ 交易拒绝成功")
                    else:
                        print(f"[AI Agent] ✗ 交易拒绝失败")
                except Exception as e:
                    print(f"[AI Agent] ✗ 交易拒绝异常: {e}")
    
    def _handle_sent_trades(self, trades_sent: list, context: Dict):
        """处理已发送交易（两阶段提交）"""
        for trade in trades_sent:
            trade_id = trade.get('trade_id', '')
            status = trade.get('status', 'pending')
            
            if status == 'accepted':
                print(f"[AI Agent] {self.villager_name} 发现已接受的交易 {trade_id}，尝试确认...")
                try:
                    result = self.execute_action("confirm_trade", trade_id=trade_id)
                    if isinstance(result, tuple):
                        success, error_message = result
                    else:
                        success = result
                        error_message = None
                    
                    if success:
                        print(f"[AI Agent] ✓ {self.villager_name} 成功提交交易 {trade_id}")
                    else:
                        print(f"[AI Agent] ✗ {self.villager_name} 提交交易失败: {error_message}")
                except Exception as e:
                    print(f"[AI Agent] ✗ {self.villager_name} 提交交易异常: {e}")
    
    def make_decision(self):
        """做一次决策"""
        if not self.villager_info:
            print("[AI Agent] ✗ 村民未创建，请先创建村民")
            return False
        
        try:
            # 获取当前状态
            villager = self.get_villager_info()
            if not villager:
                print("[AI Agent] ✗ 无法获取村民信息")
                return False
            
            time_info = self.get_current_time()
            action_status = self.get_action_status()
            prices = self.get_merchant_prices()
            messages = self.get_messages()
            villagers = self.get_online_villagers()
            trades_received = self.get_trades_received()
            trades_sent = self.get_trades_sent()
            
            # 构建上下文
            context = {
                'villager': villager,
                'time': time_info,
                'action_status': action_status,
                'prices': prices,
                'messages': messages,
                'villagers': villagers,
                'trades_received': trades_received,
                'trades_sent': trades_sent
            }
            
            # 生成决策
            decision = self.generate_decision(context)
            
            # 执行决策
            success = self.execute_decision(decision, context)
            
            return success
            
        except Exception as e:
            print(f"[AI Agent] ✗ 决策异常: {e}")
            return False
    
    def run_interactive_mode(self):
        """运行交互模式"""
        print("[AI Agent] 启动交互模式")
        
        # 检查村民是否已创建
        villager = self.get_villager_info()
        if not villager:
            print("[AI Agent] 村民未创建，请先创建村民")
            name = input("村民名字: ")
            occupation = input("职业 (farmer/chef/carpenter): ")
            gender = input("性别 (male/female): ")
            personality = input("性格: ")
            
            if not self.create_villager(name, occupation, gender, personality):
                print("[AI Agent] ✗ 村民创建失败")
                return
        else:
            self.villager_info = villager
            self.villager_name = villager.get('name', 'Unknown')
            self.villager_occupation = villager.get('occupation', 'Unknown')
            print(f"[AI Agent] ✓ 村民 {self.villager_name} 准备就绪")
        
        print(f"[AI Agent] 输入命令:")
        print(f"  auto <间隔秒数> - 启动自动决策")
        print(f"  decision - 手动决策一次")
        print(f"  status - 查看状态")
        print(f"  history - 查看决策历史")
        print(f"  quit - 退出")
        
        while True:
            try:
                command = input(f"\n[AI Agent {self.villager_name}] > ").strip()
                
                if command == "quit":
                    print("[AI Agent] 退出")
                    break
                elif command == "decision":
                    print(f"[AI Agent] {self.villager_name} 正在思考...")
                    self.make_decision()
                elif command.startswith("auto"):
                    parts = command.split()
                    interval = int(parts[1]) if len(parts) > 1 else 30
                    print(f"[AI Agent] 启动自动决策，间隔 {interval} 秒")
                    self.start_auto_decision_loop(interval)
                elif command == "status":
                    self._show_status()
                elif command == "history":
                    self._show_history()
                else:
                    print("[AI Agent] 未知命令")
                    
            except KeyboardInterrupt:
                print("\n[AI Agent] 用户中断")
                break
            except Exception as e:
                print(f"[AI Agent] 命令执行异常: {e}")
    
    def start_auto_decision_loop(self, interval: int = 30):
        """启动自动决策循环"""
        if self.running:
            print("[AI Agent] 自动决策循环已在运行")
            return
        
        self.running = True
        print(f"[AI Agent] 启动自动决策循环，间隔 {interval} 秒")
        
        def decision_loop():
            while self.running:
                try:
                    print(f"[AI Agent] {self.villager_name} 正在思考...")
                    self.make_decision()
                    time.sleep(interval)
                except Exception as e:
                    print(f"[AI Agent] 自动决策异常: {e}")
                    time.sleep(interval)
        
        import threading
        self.decision_thread = threading.Thread(target=decision_loop, daemon=True)
        self.decision_thread.start()
    
    def stop_auto_decision_loop(self):
        """停止自动决策循环"""
        if not self.running:
            print("[AI Agent] 自动决策循环未运行")
            return
        
        self.running = False
        if self.decision_thread:
            self.decision_thread.join(timeout=5)
        print("[AI Agent] 自动决策循环已停止")
    
    def _show_status(self):
        """显示状态"""
        villager = self.get_villager_info()
        if not villager:
            print("无法获取村民信息")
            return
        
        print(f"\n=== {self.villager_name} 状态 ===")
        print(f"职业: {villager.get('occupation', 'Unknown')}")
        print(f"体力: {villager.get('stamina', 0)}/{villager.get('max_stamina', 100)}")
        print(f"货币: {villager.get('inventory', {}).get('money', 0)}")
        print(f"物品: {villager.get('inventory', {}).get('items', {})}")
        print(f"已提交行动: {villager.get('has_submitted_action', False)}")
        
        # 获取其他信息
        messages = self.get_messages()
        villagers = self.get_online_villagers()
        
        print(f"消息数: {len(messages)}")
        print(f"在线村民: {len(villagers)}")
    
    def _show_history(self):
        """显示决策历史"""
        if not self.decision_history:
            print("没有决策历史")
            return
        
        print(f"\n决策历史 (最近 {min(5, len(self.decision_history))} 条):")
        for i, record in enumerate(self.decision_history[-5:]):
            print(f"{i+1}. {record['timestamp']}")
            print(f"   行动: {record['decision'].get('action', 'unknown')}")
            print(f"   理由: {record['decision'].get('reason', 'No reason')[:100]}...")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AI村民代理')
    parser.add_argument('--port', type=int, required=True, help='村民节点端口号')
    parser.add_argument('--coordinator', type=int, default=5000, help='协调器端口')
    parser.add_argument('--merchant', type=int, default=5001, help='商人端口')
    parser.add_argument('--api-key', type=str, help='OpenAI API Key')
    parser.add_argument('--model', type=str, default='gpt-4o', help='GPT模型')
    parser.add_argument('--auto', type=int, help='自动模式间隔秒数')
    args = parser.parse_args()
    
    # 使用提供的API Key或环境变量
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    
    agent = AIVillagerAgent(
        villager_port=args.port,
        coordinator_port=args.coordinator,
        merchant_port=args.merchant,
        api_key=api_key,
        model=args.model
    )
    
    agent.run_interactive_mode()


if __name__ == '__main__':
    main()
