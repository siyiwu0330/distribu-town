#!/usr/bin/env python3
"""
AI Agent村民 - 基于GPT的智能村民代理
可以自动读取状态并决定在当前时段做什么
"""

import requests
import json
import time
import threading
import os
import sys
from typing import Dict, List, Optional, Any
import openai
from datetime import datetime

class AIVillagerAgent:
    """AI村民代理"""
    
    def __init__(self, villager_port: int, coordinator_port: int = 5000, merchant_port: int = 5001, 
                 api_key: str = None, model: str = "gpt-4.1", use_react: bool = False):
        self.villager_url = f"http://localhost:{villager_port}"
        self.coordinator_url = f"http://localhost:{coordinator_port}"
        self.merchant_url = f"http://localhost:{merchant_port}"
        self.villager_port = villager_port
        
        # OpenAI配置
        self.api_key = api_key
        self.model = model
        self.use_react = use_react
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
        
        print(f"[AI Agent] 初始化完成，连接到村民节点: {villager_port}")
    
    def check_connection(self) -> bool:
        """检查连接"""
        try:
            response = requests.get(f"{self.villager_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def get_villager_status(self) -> Optional[Dict]:
        """获取村民状态"""
        try:
            response = requests.get(f"{self.villager_url}/villager", timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[AI Agent] 获取村民状态失败: {e}")
            return None
    
    def get_current_time(self) -> str:
        """获取当前时间"""
        try:
            response = requests.get(f"{self.coordinator_url}/time", timeout=5)
            if response.status_code == 200:
                time_data = response.json()
                return f"Day {time_data['day']} - {time_data['time_of_day']}"
            return "Unknown"
        except Exception as e:
            print(f"[AI Agent] 获取时间失败: {e}")
            return "Unknown"
    
    def get_action_status(self) -> Optional[Dict]:
        """获取行动提交状态"""
        try:
            response = requests.get(f"{self.coordinator_url}/action/status", timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[AI Agent] 获取行动状态失败: {e}")
            return None
    
    def get_merchant_prices(self) -> Optional[Dict]:
        """获取商人价格"""
        try:
            response = requests.get(f"{self.merchant_url}/prices", timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[AI Agent] 获取商人价格失败: {e}")
            return None
    
    def get_trades_received(self) -> List[Dict]:
        """获取收到的交易请求"""
        try:
            response = requests.get(f"{self.villager_url}/trade/pending", timeout=5)
            if response.status_code == 200:
                return response.json().get('pending_trades', [])
            return []
        except Exception as e:
            print(f"[AI Agent] 获取交易请求失败: {e}")
            return []
    
    def get_trades_sent(self) -> List[Dict]:
        """获取发送的交易请求"""
        try:
            response = requests.get(f"{self.villager_url}/mytrades", timeout=5)
            if response.status_code == 200:
                return response.json().get('trades', [])
            return []
        except Exception as e:
            print(f"[AI Agent] 获取发送交易失败: {e}")
            return []

    def get_messages(self) -> List[Dict]:
        """获取消息列表"""
        try:
            response = requests.get(f"{self.villager_url}/messages", timeout=5)
            if response.status_code == 200:
                return response.json().get('messages', [])
            return []
        except Exception as e:
            print(f"[AI Agent] 获取消息失败: {e}")
            return []
    
    def get_online_villagers(self) -> List[Dict]:
        """获取在线村民列表"""
        try:
            response = requests.get(f"{self.coordinator_url}/nodes", timeout=5)
            if response.status_code == 200:
                nodes_data = response.json()
                villagers = []
                for node in nodes_data['nodes']:
                    if node['node_type'] == 'villager':
                        villagers.append({
                            'node_id': node['node_id'],
                            'name': node.get('name', node['node_id']),
                            'occupation': node.get('occupation', 'unknown')
                        })
                return villagers
            return []
        except Exception as e:
            print(f"[AI Agent] 获取在线村民失败: {e}")
            return []
    
    def create_villager(self, name: str, occupation: str, gender: str, personality: str) -> bool:
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
                timeout=10
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
                    print(f"[AI Agent] ✗ 村民创建失败: {result.get('message')}")
                    return False
            else:
                print(f"[AI Agent] ✗ 村民创建失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"[AI Agent] ✗ 村民创建异常: {e}")
            return False
    
    def _can_produce_now(self, villager: Dict) -> bool:
        """检查是否可以立即生产"""
        occ = villager.get('occupation', '').lower()
        items = villager.get('inventory', {}).get('items', {}) or {}
        stamina = villager.get('stamina', 0)
        if occ == 'farmer':
            return items.get('seed', 0) >= 1 and stamina >= 20
        if occ == 'chef':
            return items.get('wheat', 0) >= 3 and stamina >= 15
        if occ == 'carpenter':
            return items.get('wood', 0) >= 10 and stamina >= 30
        return False

    def execute_action(self, action: str, **kwargs) -> bool:
        """执行行动"""
        try:
            if action == "produce":
                response = requests.post(f"{self.villager_url}/action/produce", timeout=10)
            elif action == "sleep":
                response = requests.post(f"{self.villager_url}/action/sleep", timeout=10)
            elif action == "idle":
                response = requests.post(f"{self.villager_url}/action/submit", 
                                       json={'action': 'idle'}, timeout=10)
            elif action == "buy":
                item = kwargs.get('item')
                quantity = kwargs.get('quantity')
                response = requests.post(f"{self.villager_url}/action/trade",
                                       json={'action': 'buy', 'target': 'merchant', 'item': item, 'quantity': quantity}, timeout=10)
            elif action == "sell":
                item = kwargs.get('item')
                quantity = kwargs.get('quantity')
                response = requests.post(f"{self.villager_url}/action/trade",
                                       json={'action': 'sell', 'target': 'merchant', 'item': item, 'quantity': quantity}, timeout=10)
            elif action == "eat":
                response = requests.post(f"{self.villager_url}/action/eat", timeout=10)
            elif action == "price":
                response = requests.get(f"{self.merchant_url}/prices", timeout=10)
                if response.status_code == 200:
                    prices_data = response.json()
                    print(f"[AI Agent] 商人价格: {prices_data}")
                    return True
                else:
                    print(f"[AI Agent] ✗ 获取价格失败: HTTP {response.status_code}")
                    return False
            elif action == "trades":
                response = requests.get(f"{self.villager_url}/trades", timeout=10)
                if response.status_code == 200:
                    trades_data = response.json()
                    print(f"[AI Agent] 收到的交易请求: {trades_data}")
                    return True
                else:
                    print(f"[AI Agent] ✗ 获取交易请求失败: HTTP {response.status_code}")
                    return False
            elif action == "mytrades":
                response = requests.get(f"{self.villager_url}/mytrades", timeout=10)
                if response.status_code == 200:
                    trades_data = response.json()
                    print(f"[AI Agent] 发送的交易请求: {trades_data}")
                    return True
                else:
                    print(f"[AI Agent] ✗ 获取发送交易失败: HTTP {response.status_code}")
                    return False
            elif action == "trade":
                target = kwargs.get('target')
                trade_action = kwargs.get('trade_action', 'buy')
                item = kwargs.get('item')
                quantity = kwargs.get('quantity')
                price = kwargs.get('price')
                
                # 首先从协调器获取目标节点地址
                coordinator_addr = villager_state.get('coordinator_address', 'localhost:5000')
                nodes_response = requests.get(f"http://{coordinator_addr}/nodes", timeout=5)
                
                if nodes_response.status_code != 200:
                    print(f"[AI Agent] ✗ 获取节点列表失败: HTTP {nodes_response.status_code}")
                    return False
                
                nodes_data = nodes_response.json()
                target_node = None
                
                # 查找目标节点（支持节点ID和村民名称）
                for node in nodes_data['nodes']:
                    if node['node_id'] == target or node.get('name') == target:
                        target_node = node
                        break
                
                if not target_node:
                    print(f"[AI Agent] ✗ 找不到目标节点: {target}")
                    return False
                
                # 发送交易请求到目标节点
                response = requests.post(f"http://{target_node['address']}/trade/request", 
                                        json={
                                            'from': self.villager_name,
                                            'from_address': f'localhost:{self.villager_port}',
                                            'item': item,
                                            'quantity': quantity,
                                            'price': price,
                                            'offer_type': trade_action
                                        }, timeout=10)
                if response.status_code == 200:
                    trade_data = response.json()
                    print(f"[AI Agent] 交易请求已发送: {trade_action} {quantity}x {item} for {price} gold to {target}")
                    return True
                else:
                    print(f"[AI Agent] ✗ 发送交易请求失败: HTTP {response.status_code}")
                    return False
            elif action == "send_message":
                target = kwargs.get('target')
                content = kwargs.get('content')
                message_type = kwargs.get('type', 'private')
                response = requests.post(f"{self.villager_url}/messages/send",
                                       json={'target': target, 'content': content, 'type': message_type}, timeout=10)
            elif action == "accept_trade":
                trade_id = kwargs.get('trade_id')
                response = requests.post(f"{self.villager_url}/trade/accept",
                                       json={'trade_id': trade_id}, timeout=10)
            elif action == "reject_trade":
                trade_id = kwargs.get('trade_id')
                response = requests.post(f"{self.villager_url}/trade/reject",
                                       json={'trade_id': trade_id}, timeout=10)
            elif action == "confirm_trade":
                trade_id = kwargs.get('trade_id')
                response = requests.post(f"{self.villager_url}/trade/confirm",
                                       json={'trade_id': trade_id}, timeout=10)
            else:
                print(f"[AI Agent] ✗ 未知行动: {action}")
                return False
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', True):
                    print(f"[AI Agent] ✓ 执行行动成功: {action}")
                    return True
                else:
                    print(f"[AI Agent] ✗ 执行行动失败: {result.get('message')}")
                    return False
            else:
                print(f"[AI Agent] ✗ 执行行动失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"[AI Agent] ✗ 执行行动异常: {e}")
            return False
    
    def generate_decision(self, context: Dict) -> Dict:
        """生成决策（支持ReAct和传统模式）"""
        if not self.api_key:
            print("[AI Agent] ✗ 未配置API Key，无法使用GPT")
            return {"action": "idle", "reason": "No API key configured"}
        
        try:
            if self.use_react:
                # 使用ReAct结构
                prompt = self._build_react_prompt(context)
                system_prompt = self._get_react_system_prompt()
                max_tokens = 800
            else:
                # 使用传统JSON模式
                prompt = self._build_prompt(context)
                system_prompt = self._get_system_prompt()
                max_tokens = 500
            
            # 调试：打印GPT看到的状态
            print(f"[AI Agent DEBUG] GPT看到的状态:")
            print(f"  体力: {context.get('villager', {}).get('stamina')}/{context.get('villager', {}).get('max_stamina')}")
            print(f"  货币: {context.get('villager', {}).get('inventory', {}).get('money')}")
            print(f"  物品: {context.get('villager', {}).get('inventory', {}).get('items')}")
            print(f"  消息: {len(context.get('messages', []))} 条")
            print(f"  交易请求: {len(context.get('trades_received', []))} 条")
            print(f"  发送交易: {len(context.get('trades_sent', []))} 条")
            
            # 调用GPT API
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
            
            # 根据模式解析决策
            if self.use_react:
                decision = self._parse_react_decision(decision_text)
            else:
                decision = self._parse_decision(decision_text)
            
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
- `sleep` - Sleep to restore stamina (consumes action point, evening only, REQUIRES HOUSE!)
- `idle` - Skip current segment (consumes action point)
- `price` - Check merchant prices (no action cost)
- `trades` - Check received trade requests (no action cost)
- `mytrades` - Check sent trade requests (no action cost)
- `trade <target> <action> <item> <quantity> <price>` - Send trade request to villager
- `send <target> <message>` - Send message to another villager
- `accept <trade_id>` - Accept a trade request
- `reject <trade_id>` - Reject a trade request

## Game Rules:
- Each time segment allows ONE main action (produce/sleep/idle)
- Trading and eating don't consume action points
- Stamina: 0-100, work consumes stamina, sleep restores stamina
- Hunger: -10 stamina daily, -20 extra if no sleep at night
- **CRITICAL: Sleep requires a HOUSE! You cannot sleep without a house.**
- **IMPORTANT: Buy and produce are SEPARATE decisions! Buy resources first, then produce in the next decision.**

## Occupation Recipes:
- Farmer: 1 seed → 5 wheat (costs 20 stamina)
- Chef: 3 wheat → 2 bread (costs 15 stamina)
- Carpenter: 10 wood → 1 house (costs 30 stamina)

## Output Format:
Always follow this exact format:

THOUGHT: [Your reasoning about the current situation and what action to take]

ACTION: [Single command to execute]

Example:
THOUGHT: I'm a farmer with 0 seeds and 100 stamina. I need seeds to produce wheat. I should buy 1-2 seeds first.

ACTION: buy seed 2

Remember: Only output THOUGHT and ACTION. The OBSERVATION will be provided in the next cycle."""

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """You are a **single villager node** agent in the *Distributed Virtual Town* simulation.
Your task is to keep your villager alive, productive, and economically efficient in a distributed world of villagers, merchants, and a time coordinator.
You operate autonomously, following the game's rules, using REST/CLI actions to interact with the world.

---

## 1. World and Objectives

* The world includes a **Time Coordinator**, a **Merchant**, and multiple **Villagers** (each an independent node).
* Time is divided into **Morning**, **Noon**, and **Night**.
* The world advances only when all villagers have submitted their action for the current period.
* Each villager has attributes: **occupation**, **stamina (0–100)**, **money**, and **inventory** (`seed`, `wheat`, `bread`, `wood`, `house`, `temp_room`).

**Your goals:**
1. Stay alive (don't let stamina reach 0).
2. Grow wealth and asset value.
3. Use stamina and time efficiently to maximize long-term productivity.

---

## 2. Core Rules

* **Three time periods per day:** Morning, Noon, Night.
* Each period allows **one submitted action** (e.g., `produce`, `sleep`, or `idle`).
* **Production actions** cost **1 action point** and **stamina**.
* **Trading** and **eating** do **not** consume an action point.
* **Stamina mechanics:**
  * Base range: 0–100
  * Hunger: -10 stamina per day
  * Working costs stamina (per occupation)
  * Skipping sleep at night: -20 stamina
  * Eating bread restores stamina
  * Sleeping restores stamina but requires a `house` or `temp_room`

**Occupation recipes and stamina cost:**
* Farmer: `1 seed → 5 wheat` (costs 20 stamina)
* Chef: `3 wheat → 2 bread` (costs 15 stamina)
* Carpenter: `10 wood → 1 house` (costs 30 stamina)

---

## 3. Available Actions

**Basic actions**
* `eat` → consume bread to restore stamina (no action cost)
* `sleep` → restore stamina; requires house/temp_room; consumes action point

**Production (consumes action point + stamina)**
* `produce` or `work` → perform occupation-specific production

**Merchant trading (no action cost)**
* `buy <item> <quantity>`
* `sell <item> <quantity>`

**Idle (submit empty action)**
* `idle` → submit no production or sleep action (to let time advance)

---

## 4. Decision Loop (Every Time Period)

1. **Survival first:**
   * If stamina ≤ 35 → `eat` (if bread available).
   * If it's Night and stamina ≤ 45 → `sleep` (if housing available).

2. **Production logic:**
   * If stamina and materials are sufficient → `produce`.
   * If missing inputs → `buy` from merchant.
   * If unproductive → `idle`.

3. **Trading strategy:**
   * Keep essential items (bread, seeds, temp_room) for survival.

4. **Night strategy:**
   * Prefer sleeping to recover stamina; avoid overwork unless safe.

---

## 5. Occupation Strategies

**Farmer**
* Focus on turning seeds → wheat efficiently.
* Keep enough seeds for future cycles.
* Sell wheat to chefs or merchant when price favorable.

**Chef**
* Convert wheat → bread for both self-use and sales.
* Always keep 2–3 bread for stamina recovery.
* Buy wheat at low price; sell bread at profit.

**Carpenter**
* Convert wood → house for high profit but large stamina cost.
* Ensure own housing before selling houses.
* Rest more frequently due to high stamina cost.

---

## 6. Output Policy

* Always output **one actionable command** or **a short explanation + one command**.
* Example formats:
  ```
  # Low stamina, eating bread
  eat
  ```
  or just
  ```
  produce
  ```
* You may explain reasoning briefly with a `#` comment above the command.
* Avoid verbose analysis or internal reasoning. Output must be short and actionable.

---

## 7. Critical Rules

* **DO NOT use compound commands** like "buy seed 5 && produce" or "buy seed 5; produce"
* **Only ONE command per decision**
* **After buying resources, ALWAYS produce in the same segment**
* **Buy/sell/eat don't consume action points - can be done before main action**

Return decision in JSON format:
{
    "command": "single_cli_command",
    "reason": "brief explanation"
}

EXAMPLES:
- Buy seeds: {"command": "buy seed 1", "reason": "Need seeds for wheat production"}
- Produce wheat: {"command": "produce", "reason": "Have seeds, producing wheat"}
- Sleep: {"command": "sleep", "reason": "Low stamina, need rest"}
- Eat bread: {"command": "eat", "reason": "Low stamina, need to restore energy"}
- Idle: {"command": "idle", "reason": "No immediate action needed"}

QUANTITY HEURISTIC:
- Farmer: Buy just enough seeds to cover this period's production, keep a buffer of 1-2 if money ≥ 2× seed price
- Chef: Ensure wheat ≥ 3 before producing; keep bread reserve 2-3 for stamina
- Carpenter: Accumulate toward 10 wood; don't starve other needs
- Choose quantities dynamically; buy the minimum needed to enable production now, plus a small buffer if affordable"""
    
    def _build_react_prompt(self, context: Dict) -> str:
        """构建ReAct提示词"""
        villager = context.get('villager', {})
        time_info = context.get('time', '')
        action_status = context.get('action_status', {})
        prices = context.get('prices', {})
        messages = self.get_messages()
        trades_received = self.get_trades_received()
        trades_sent = self.get_trades_sent()
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
        
        # 判断当前时段
        is_evening = 'evening' in time_info.lower() or 'night' in time_info.lower()
        
        prompt = f"""=== CURRENT STATE ===

Time: {time_info}
Villager: {villager.get('name', 'Unknown')} ({occupation})
Stamina: {stamina}/{max_stamina}
Money: {money} gold
Action Submitted: {has_submitted}
Sleep Status: {"Already slept today" if has_slept else "Not slept yet" + (" - Should sleep!" if is_evening else "")}

Inventory: {items if items else "Empty"}

Merchant Prices: {prices.get('prices', {}) if prices.get('prices') else "Use 'price' command to check"}

Messages: {len(messages)} received
{chr(10).join([f"- From {msg.get('from', 'Unknown')}: {msg.get('content', '')[:50]}..." for msg in messages[:3]]) if messages else "No messages"}

Trades: {len(trades_received)} received, {len(trades_sent)} sent
{chr(10).join([f"- Trade {trade.get('id', '')}: {trade.get('action', '')} {trade.get('item', '')} x{trade.get('quantity', 0)} for {trade.get('price', 0)} gold" for trade in trades_received[:3]]) if trades_received else "No trade requests"}

Online Villagers: {len(villagers)}
{chr(10).join([f"- {v['name']} ({v['occupation']})" for v in villagers])}

=== PREVIOUS OBSERVATIONS ===
{self._get_recent_observations()}

=== IMPORTANT GAME RULES ===
- Sleep requires a HOUSE! You cannot sleep without a house.
- To get a house: Carpenter produces houses (10 wood → 1 house), or trade with other villagers
- Farmer: 1 seed → 5 wheat (costs 20 stamina)
- Chef: 3 wheat → 2 bread (costs 15 stamina) 
- Carpenter: 10 wood → 1 house (costs 30 stamina)
- Use 'price' command to check merchant prices (don't send messages to merchant)
- **CRITICAL: Buy and produce are SEPARATE decisions! Buy resources first, then produce in the next decision.**

Now follow the ReAct pattern:"""
        
        return prompt

    def _get_recent_observations(self) -> str:
        """获取最近的观察结果"""
        if not self.decision_history:
            return "No previous observations."
        
        recent = self.decision_history[-3:]  # 最近3次决策
        observations = []
        
        for entry in recent:
            timestamp = entry['timestamp'][:19]  # 去掉毫秒
            decision = entry['decision']
            action = decision.get('action', 'unknown')
            reason = decision.get('reason', 'No reason')
            success = decision.get('success', True)
            error_msg = decision.get('error_message', '')
            
            if success:
                observations.append(f"[{timestamp}] ACTION: {action} - SUCCESS - {reason}")
                # 如果是价格查询，显示价格信息
                if action == "price" and 'prices' in decision:
                    prices = decision.get('prices', {})
                    if prices:
                        observations.append(f"  PRICES: {prices}")
                # 如果是交易查询，显示交易信息
                elif action == "trades" and 'trades' in decision:
                    trades = decision.get('trades', [])
                    if trades:
                        observations.append(f"  RECEIVED TRADES: {len(trades)} requests")
                        for trade in trades[:2]:  # 显示前2个交易
                            observations.append(f"    - {trade.get('action', '')} {trade.get('item', '')} x{trade.get('quantity', 0)} for {trade.get('price', 0)} gold")
                elif action == "mytrades" and 'mytrades' in decision:
                    trades = decision.get('mytrades', [])
                    if trades:
                        observations.append(f"  SENT TRADES: {len(trades)} requests")
                        for trade in trades[:2]:  # 显示前2个交易
                            observations.append(f"    - {trade.get('action', '')} {trade.get('item', '')} x{trade.get('quantity', 0)} for {trade.get('price', 0)} gold")
            else:
                observations.append(f"[{timestamp}] ACTION: {action} - FAILED - {reason}")
                if error_msg:
                    observations.append(f"  ERROR: {error_msg}")
        
        return "\n".join(observations)

    def _build_prompt(self, context: Dict) -> str:
        """构建提示词"""
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
            stamina_analysis = "⚠️ 体力较低，建议考虑恢复体力"
        else:
            stamina_analysis = "✓ 体力充足"
        
        # 分析睡眠需求
        sleep_analysis = ""
        if not has_slept and 'evening' in time_info.lower():
            sleep_analysis = "⚠️ Evening - Should sleep to avoid penalty"
        elif not has_slept:
            sleep_analysis = "Not slept yet (will sleep in evening)"
        else:
            sleep_analysis = "✓ Already slept today"
        
        # 判断当前时段
        is_morning = 'morning' in time_info.lower()
        is_noon = 'noon' in time_info.lower() or 'afternoon' in time_info.lower()
        is_evening = 'evening' in time_info.lower()
        
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

=== TRADES ===
Trades Received: {len(trades_received)}
{chr(10).join([f"- Trade {trade.get('id', '')}: {trade.get('action', '')} {trade.get('item', '')} x{trade.get('quantity', 0)} for {trade.get('price', 0)} gold" for trade in trades_received[:3]]) if trades_received else "No trade requests"}

Trades Sent: {len(trades_sent)}
{chr(10).join([f"- Trade {trade.get('id', '')}: {trade.get('action', '')} {trade.get('item', '')} x{trade.get('quantity', 0)} for {trade.get('price', 0)} gold" for trade in trades_sent[:3]]) if trades_sent else "No sent trades"}

=== ONLINE VILLAGERS ===
Online Villagers: {len(villagers)}
{chr(10).join([f"- {v['name']} ({v['occupation']})" for v in villagers])}

=== DECISION GUIDELINES ===
Make smart decisions based on the above information:

1. CHECK STAMINA FIRST:
   - If stamina >= 50: You have sufficient stamina, focus on work
   - If stamina < 30: Urgent! Buy bread or sleep
   - Sleep is ONLY needed in evening segment to avoid penalty

2. PRODUCTION WORKFLOW (if stamina is good):
   - Step 1: Buy necessary resources (buy seed 1-2)
   - Step 2: Immediately produce (produce) - SAME SEGMENT!
   - Farmer: buy seed → produce wheat
   - Chef: buy wheat → produce bread
   - Carpenter: buy wood → produce house

3. ECONOMIC STRATEGY:
   - Buy resources FIRST, then produce immediately
   - Don't keep buying without producing!
   - Sell excess products for profit
   - **ACTIVE TRADING**: Look for opportunities to trade with other villagers!
     * If you have excess items, offer them for sale to other villagers
     * If you need resources, try buying from other villagers (may be cheaper than merchant)
     * Use 'trade <node_id> buy/sell <item> <quantity> <total_price>' to initiate trades
     * Check 'villagers' to see who's online and their occupations
     * IMPORTANT: Use node IDs (node1, node2) not names!

4. TRADING OPPORTUNITIES:
   - **Farmer**: Sell wheat to chefs, buy seeds from other farmers
   - **Chef**: Sell bread to everyone, buy wheat from farmers  
   - **Carpenter**: Sell houses to everyone, buy wood from other carpenters
   - **Smart trading**: Offer competitive prices (slightly below merchant prices)
   - **Check trades**: Use 'trades' to see incoming requests, 'mytrades' for sent requests
   - **Respond to trades**: Use 'accept <trade_id>' or 'reject <trade_id>'
   - **Complete trades**: Use 'confirm <trade_id>' after other party accepts

5. TIME MANAGEMENT:
   - Morning/Afternoon: Buy resources → Produce → Trade opportunities
   - Evening: Consider sleeping if not yet slept today
   - Only idle if no better options

6. TRADING EXAMPLES:
   - "trade node2 sell wheat 5 80" → Sell 5 wheat to node2 for 80 gold total
   - "trade node1 buy seed 2 15" → Buy 2 seeds from node1 for 15 gold total
   - "trades" → Check incoming trade requests
   - "accept trade_0" → Accept a trade request
   - "confirm trade_0" → Complete a trade after acceptance
   
   IMPORTANT: Use node IDs (node1, node2, etc.) not names for trading!
   IMPORTANT: Price is TOTAL price, not per-unit price!

CRITICAL: After buying resources, ALWAYS produce in the same segment!
CRITICAL: Look for trading opportunities with other villagers!
CRITICAL: Always provide complete CLI command with all parameters!

Return JSON decision format."""
        
        return prompt
    
    def _parse_react_decision(self, decision_text: str) -> Dict:
        """解析ReAct决策"""
        try:
            lines = decision_text.strip().split('\n')
            thought = ""
            action = "idle"
            reason = "No reasoning provided"
            
            # 解析THOUGHT和ACTION
            for line in lines:
                line = line.strip()
                if line.startswith('THOUGHT:'):
                    thought = line[8:].strip()
                    reason = thought
                elif line.startswith('ACTION:'):
                    action_line = line[7:].strip()
                    # 解析动作
                    parts = action_line.split()
                    if parts:
                        action = parts[0].lower()
                        if action == "buy" and len(parts) >= 3:
                            try:
                                quantity = int(parts[2])
                                return {
                                    "action": "buy",
                                    "reason": reason,
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
                                    "reason": reason,
                                    "command": action_line,
                                    "item": parts[1],
                                    "quantity": quantity
                                }
                            except ValueError:
                                pass
                        elif action == "send" and len(parts) >= 3:
                            target = parts[1]
                            content = " ".join(parts[2:])
                            return {
                                "action": "send",
                                "reason": reason,
                                "command": action_line,
                                "target": target,
                                "content": content
                            }
                        elif action == "price":
                            return {
                                "action": "price",
                                "reason": reason,
                                "command": action_line
                            }
                        elif action == "trades":
                            return {
                                "action": "trades",
                                "reason": reason,
                                "command": action_line
                            }
                        elif action == "mytrades":
                            return {
                                "action": "mytrades",
                                "reason": reason,
                                "command": action_line
                            }
                        elif action == "trade" and len(parts) >= 6:
                            # 正确的格式: trade <节点ID> <buy/sell> <物品> <数量> <总价>
                            trade_action = parts[2].lower()
                            if trade_action not in ['buy', 'sell']:
                                # 如果使用了错误的动作，尝试修正
                                if trade_action in ['offer', 'purchase']:
                                    trade_action = 'buy'
                                elif trade_action in ['sell_to', 'give']:
                                    trade_action = 'sell'
                                else:
                                    trade_action = 'buy'  # 默认
                            
                            return {
                                "action": "trade",
                                "reason": reason,
                                "command": action_line,
                                "target": parts[1],
                                "trade_action": trade_action,
                                "item": parts[3],
                                "quantity": int(parts[4]),
                                "price": int(parts[5])  # 总价
                            }
                        else:
                            return {
                                "action": action,
                                "reason": reason,
                                "command": action_line
                            }
            
            return {"action": "idle", "reason": reason, "command": "idle"}
            
        except Exception as e:
            print(f"[AI Agent] ✗ ReAct解析失败: {e}")
            return {"action": "idle", "reason": f"Parse error: {str(e)}", "command": "idle"}

    def _parse_decision(self, decision_text: str) -> Dict:
        """解析GPT返回的决策"""
        try:
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{.*\}', decision_text, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                command = decision.get('command', 'idle')
                reason = decision.get('reason', 'No reason provided')
                
                # 处理复合命令（如 "buy seed 5 && produce" 或 "buy seed 5; produce"）
                if '&&' in command or ';' in command:
                    separator = '&&' if '&&' in command else ';'
                    commands = [cmd.strip() for cmd in command.split(separator)]
                    # 只执行第一个命令
                    command = commands[0]
                    print(f"[AI Agent] 检测到复合命令，只执行第一个: {command}")
                
                # 验证命令格式
                parts = command.split()
                if not parts:
                    return {"action": "idle", "reason": "Empty command", "command": "idle"}
                
                action = parts[0].lower()
                
                # 构建返回结果
                result = {"action": action, "reason": reason, "command": command}
                
                # 添加特定参数
                if action == "buy" and len(parts) >= 3:
                    try:
                        result["item"] = parts[1]
                        result["quantity"] = int(parts[2])
                    except ValueError:
                        result["reason"] = f"Invalid quantity: {parts[2]}"
                elif action == "sell" and len(parts) >= 3:
                    try:
                        result["item"] = parts[1]
                        result["quantity"] = int(parts[2])
                    except ValueError:
                        result["reason"] = f"Invalid quantity: {parts[2]}"
                elif action == "produce" and len(parts) >= 2:
                    result["item"] = parts[1]
                elif action == "send" and len(parts) >= 3:
                    result["target"] = parts[1]
                    result["content"] = " ".join(parts[2:]).strip('"')
                
                return result
            else:
                # 如果没有找到JSON，尝试简单解析
                lines = decision_text.split('\n')
                action = "idle"
                reason = decision_text
                
                for line in lines:
                    if 'action' in line.lower():
                        if 'produce' in line.lower():
                            action = "produce"
                        elif 'sleep' in line.lower():
                            action = "sleep"
                        elif 'buy' in line.lower():
                            action = "buy"
                        elif 'sell' in line.lower():
                            action = "sell"
                        elif 'eat' in line.lower():
                            action = "eat"
                        elif 'idle' in line.lower():
                            action = "idle"
                
                return {"action": action, "reason": reason, "command": action}
        except Exception as e:
            print(f"[AI Agent] ✗ 解析决策失败: {e}")
            return {"action": "idle", "reason": f"Parse error: {str(e)}", "command": "idle"}
    
    def make_decision_and_act(self):
        """做出决策并执行行动"""
        # 收集上下文信息
        context = {
            'villager': self.get_villager_status() or {},
            'time': self.get_current_time(),
            'action_status': self.get_action_status() or {},
            'prices': self.get_merchant_prices() or {},
            'messages': self.get_messages(),
            'trades_received': self.get_trades_received(),
            'trades_sent': self.get_trades_sent(),
            'villagers': self.get_online_villagers()
        }
        
        # 检查是否已经提交了行动
        villager = context['villager']
        if villager.get('has_submitted_action', False):
            print(f"[AI Agent] {self.villager_name} 已经提交了行动，等待时间推进...")
            return
        
        # 生成决策
        print(f"[AI Agent] {self.villager_name} 正在思考...")
        decision = self.generate_decision(context)
        
        action = decision.get('action', 'idle')
        reason = decision.get('reason', 'No reason provided')
        command = decision.get('command', action)
        
        print(f"[AI Agent] {self.villager_name} 思考: {reason}")
        print(f"[AI Agent] {self.villager_name} 行动: {command}")
        print(f"[AI Agent] 决策详情: {decision}")
        
        # 执行行动
        success = False
        error_message = None
        
        if action == "buy":
            success = self.execute_action("buy", 
                                        item=decision.get('item', 'seed'), 
                                        quantity=decision.get('quantity', 1))
            # 购买不消耗行动点，但也不自动生产
            # 让AI在下一轮决策中决定是否生产
        elif action == "sell":
            success = self.execute_action("sell", 
                                        item=decision.get('item', 'wheat'), 
                                        quantity=decision.get('quantity', 1))
        elif action == "produce":
            success = self.execute_action("produce")
        elif action == "sleep":
            success = self.execute_action("sleep")
            if not success:
                error_message = "Sleep failed: You need a house to sleep! Build a house first or buy one from other villagers."
        elif action == "idle":
            success = self.execute_action("idle")
        elif action == "eat":
            success = self.execute_action("eat")
        elif action == "price":
            success = self.execute_action("price")
            if success:
                # 获取价格信息并记录
                prices = self.get_merchant_prices()
                if prices and self.decision_history:
                    last_decision = self.decision_history[-1]
                    last_decision['decision']['prices'] = prices
        elif action == "trades":
            success = self.execute_action("trades")
            if success:
                # 获取交易信息并记录
                trades = self.get_trades_received()
                if trades and self.decision_history:
                    last_decision = self.decision_history[-1]
                    last_decision['decision']['trades'] = trades
        elif action == "mytrades":
            success = self.execute_action("mytrades")
            if success:
                # 获取发送交易信息并记录
                trades = self.get_trades_sent()
                if trades and self.decision_history:
                    last_decision = self.decision_history[-1]
                    last_decision['decision']['mytrades'] = trades
        elif action == "trade":
            success = self.execute_action("trade",
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
        elif action == "accept":
            trade_id = decision.get('trade_id')
            if trade_id:
                success = self.execute_action("accept_trade", trade_id=trade_id)
            else:
                error_message = "Accept trade failed: No trade ID provided"
        elif action == "reject":
            trade_id = decision.get('trade_id')
            if trade_id:
                success = self.execute_action("reject_trade", trade_id=trade_id)
            else:
                error_message = "Reject trade failed: No trade ID provided"
        elif action == "confirm":
            trade_id = decision.get('trade_id')
            if trade_id:
                success = self.execute_action("confirm_trade", trade_id=trade_id)
            else:
                error_message = "Confirm trade failed: No trade ID provided"
        else:
            print(f"[AI Agent] ✗ 未知行动: {action}")
            success = False
            error_message = f"Unknown action: {action}"
        
        if success:
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
    
    def start_auto_decision_loop(self, interval: int = 30):
        """启动自动决策循环"""
        if self.running:
            print("[AI Agent] 自动决策循环已在运行")
            return
        
        self.running = True
        self.decision_thread = threading.Thread(target=self._decision_loop, args=(interval,), daemon=True)
        self.decision_thread.start()
        print(f"[AI Agent] 启动自动决策循环，间隔 {interval} 秒")
    
    def stop_auto_decision_loop(self):
        """停止自动决策循环"""
        self.running = False
        if self.decision_thread:
            self.decision_thread.join()
        print("[AI Agent] 自动决策循环已停止")
    
    def _decision_loop(self, interval: int):
        """决策循环"""
        while self.running:
            try:
                self.make_decision_and_act()
                time.sleep(interval)
            except Exception as e:
                print(f"[AI Agent] 决策循环异常: {e}")
                time.sleep(interval)
    
    def run_interactive_mode(self):
        """运行交互模式"""
        print(f"[AI Agent] 启动交互模式")
        
        # 检查连接
        if not self.check_connection():
            print("[AI Agent] ✗ 无法连接到村民节点")
            return
        
        # 检查村民是否已创建
        villager_status = self.get_villager_status()
        if not villager_status:
            print("[AI Agent] 村民未创建，请先创建村民")
            name = input("村民名字: ").strip()
            occupation = input("职业 (farmer/chef/carpenter): ").strip()
            gender = input("性别 (male/female): ").strip()
            personality = input("性格: ").strip()
            
            if not self.create_villager(name, occupation, gender, personality):
                print("[AI Agent] ✗ 村民创建失败")
                return
        
        print(f"[AI Agent] ✓ 村民 {self.villager_name} 准备就绪")
        print("[AI Agent] 输入命令:")
        print("  auto <间隔秒数> - 启动自动决策")
        print("  decision - 手动决策一次")
        print("  status - 查看状态")
        print("  history - 查看决策历史")
        print("  quit - 退出")
        
        while True:
            try:
                cmd = input(f"\n[AI Agent {self.villager_name}] > ").strip().lower()
                
                if cmd == "quit":
                    self.stop_auto_decision_loop()
                    break
                elif cmd.startswith("auto"):
                    parts = cmd.split()
                    interval = int(parts[1]) if len(parts) > 1 else 30
                    self.start_auto_decision_loop(interval)
                elif cmd == "decision":
                    self.make_decision_and_act()
                elif cmd == "status":
                    self._show_status()
                elif cmd == "history":
                    self._show_history()
                else:
                    print("未知命令")
            except KeyboardInterrupt:
                print("\n[AI Agent] 退出中...")
                self.stop_auto_decision_loop()
                break
            except Exception as e:
                print(f"[AI Agent] 错误: {e}")
    
    def _show_status(self):
        """显示状态"""
        context = {
            'villager': self.get_villager_status() or {},
            'time': self.get_current_time(),
            'action_status': self.get_action_status() or {},
            'prices': self.get_merchant_prices() or {},
            'messages': self.get_messages(),
            'villagers': self.get_online_villagers()
        }
        
        print(f"\n当前状态:")
        print(f"时间: {context['time']}")
        print(f"村民: {context['villager'].get('name', 'Unknown')}")
        print(f"体力: {context['villager'].get('stamina', 0)}/{context['villager'].get('max_stamina', 100)}")
        print(f"货币: {context['villager'].get('inventory', {}).get('money', 0)}")
        print(f"物品: {context['villager'].get('inventory', {}).get('items', {})}")
        print(f"已提交行动: {context['villager'].get('has_submitted_action', False)}")
        print(f"消息数: {len(context['messages'])}")
        print(f"在线村民: {len(context['villagers'])}")
    
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
    parser.add_argument('--react', action='store_true', help='使用ReAct推理模式')
    parser.add_argument('--auto', type=int, help='自动模式间隔秒数')
    args = parser.parse_args()
    
    # 使用提供的API Key或环境变量
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("错误: 未提供OpenAI API Key")
        print("请使用 --api-key 参数或设置 OPENAI_API_KEY 环境变量")
        sys.exit(1)
    
    agent = AIVillagerAgent(
        villager_port=args.port,
        coordinator_port=args.coordinator,
        merchant_port=args.merchant,
        api_key=api_key,
        model=args.model,
        use_react=args.react
    )
    
    agent.run_interactive_mode()


if __name__ == '__main__':
    main()
