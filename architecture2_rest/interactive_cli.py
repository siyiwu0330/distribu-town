"""
Interactive CLI client - control a single VillagerNode
Can connect to any running VillagerNode for interaction
"""

import requests
import sys
import json
import time
from typing import Optional


class VillagerCLI:
    """VillagerNode interactive CLI"""
    
    def __init__(self, villager_port: int, coordinator_port: int = 5000, merchant_port: int = 5001, 
                 coordinator_host: str = "localhost", merchant_host: str = "localhost"):
        self.villager_url = f"http://localhost:{villager_port}"
        self.coordinator_url = f"http://{coordinator_host}:{coordinator_port}"
        self.merchant_url = f"http://{merchant_host}:{merchant_port}"
        self.villager_port = villager_port
        self.pending_trades = {}  # Trades currently awaiting response; key is trade_id
    
    def check_connection(self) -> bool:
        """Check connection"""
        try:
            response = requests.get(f"{self.villager_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def get_villager_info(self) -> Optional[dict]:
        """Get Villager information"""
        try:
            response = requests.get(f"{self.villager_url}/villager", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def create_villager(self, name: str, occupation: str, gender: str, personality: str):
        """CreateVillager"""
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
                print(f"\n✓ VillagerCreateSuccess!")
                self.display_villager_info(data['villager'])
            else:
                print(f"\n✗ CreateFailed: {response.json().get('message', 'Unknown error')}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def display_villager_info(self, info: dict = None):
        """Display Villager Info"""
        if info is None:
            info = self.get_villager_info()
        
        if not info:
            print("\nVillager not initialized")
            return
        
        # Show prompt based on action status
        action_status = ""
        if info.get('has_submitted_action', False):
            action_status = " [Submitted, waiting for time to advance]"
        else:
            action_status = " [Available actions: work/sleep/idle]"
        
        print("\n" + "="*50)
        print(f"  {info['name']} - {info['occupation']}")
        print("="*50)
        print(f"Gender: {info['gender']}")
        print(f"Personality: {info['personality']}")
        print(f"⚡ Stamina: {info['stamina']}/{info['max_stamina']}")
        print(f"🎯 Action status: {'Submitted' if info.get('has_submitted_action', False) else 'Not submitted'}{action_status}")
        print(f"😴 Slept: {'Yes' if info['has_slept'] else 'No'}")
        print(f"\n💰 Money: {info['inventory']['money']}")
        
        if info['inventory']['items']:
            print("📦 Item:")
            for item, quantity in info['inventory']['items'].items():
                print(f"   - {item}: {quantity}")
        else:
            print("📦 Item: None")
        print("="*50)
    
    def produce(self):
        """Production (auto-submit work)"""
        try:
            response = requests.post(f"{self.villager_url}/action/produce", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ {data['message']}")
                
                # Show submit result
                submit_result = data.get('submit_result', {})
                if submit_result.get('all_ready'):
                    print("\n🎉 All villagers are ready; time has advanced!")
                    print(f"   New time: {submit_result.get('new_time', {})}")
                elif submit_result.get('waiting_for'):
                    waiting_for = submit_result.get('waiting_for', [])
                    print(f"\n⏳ Auto-submitted 'work' action, waiting for other villagers")
                    print(f"   Waiting: {len(waiting_for)} villager(s)")
                
                villager_data = data['villager']
                self.display_villager_info(villager_data)
            else:
                print(f"\n✗ {response.json()['message']}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def trade(self, action: str, item: str, quantity: int):
        """Trade"""
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
            print(f"\n✗ Error: {e}")
    
    def sleep(self):
        """Sleep (auto-submit sleep)"""
        try:
            response = requests.post(f"{self.villager_url}/action/sleep", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ {data['message']}")
                
                # Show submit result
                submit_result = data.get('submit_result', {})
                if submit_result.get('all_ready'):
                    print("\n🎉 All villagers are ready; time has advanced!")
                    print(f"   New time: {submit_result.get('new_time', {})}")
                elif submit_result.get('waiting_for'):
                    waiting_for = submit_result.get('waiting_for', [])
                    print(f"\n⏳ Auto-submitted 'sleep' action, waiting for other villagers")
                    print(f"   Waiting: {len(waiting_for)} villager(s)")
                
                villager_data = data['villager']
                self.display_villager_info(villager_data)
            else:
                print(f"\n✗ {response.json()['message']}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def eat(self):
        """Eat bread to restore stamina"""
        try:
            response = requests.post(f"{self.villager_url}/action/eat", timeout=5)
            
            if response.status_code == 200:
                print(f"\n✓ {response.json()['message']}")
                self.display_villager_info(response.json()['villager'])
            else:
                print(f"\n✗ {response.json()['message']}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def get_current_time(self):
        """Get current time"""
        try:
            response = requests.get(f"{self.coordinator_url}/time", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return f"Day {data['day']} - {data['time_of_day']}"
            return "Unable to get time"
        except:
            return "Coordinator not connected"
    
    def submit_action(self, action_type: str):
        """Submit action to Coordinator (synchronization barrier)"""
        try:
            response = requests.post(
                f"{self.villager_url}/action/submit",
                json={'action': action_type},
                timeout=10  # Extended timeout because we may wait for others
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('all_ready'):
                    # Everyone is ready; time has advanced
                    print(f"\n✓ {data['message']}")
                    
                    # Show new time
                    new_time = data.get('new_time', {})
                    time_of_day = new_time.get('time_of_day', '')
                    
                    if time_of_day == 'morning':
                        print(f"\n🌅 A new day begins!")
                        print("   - All villagers' action points reset to 3")
                        print("   - Daily hunger reduces 10 stamina")
                    elif time_of_day == 'noon':
                        print(f"\n☀️  It's now noon")
                    elif time_of_day == 'evening':
                        print(f"\n🌙 It's now evening")
                        print("   - You can sleep to restore stamina")
                    
                    # Show updated villager status
                    print("\nYour villager status:")
                    self.display_villager_info()
                else:
                    # Still waiting for others
                    waiting_for = data.get('waiting_for', [])
                    print(f"\n⏳ {data['message']}")
                    print(f"\nWaiting for the following villagers to submit actions:")
                    for node in waiting_for:
                        if isinstance(node, dict):
                            print(f"   - {node['display_name']}")
                        else:
                            print(f"   - {node}")
                    print("\n💡 Tip: You can continue doing other operations (trade, etc.), or wait...")
            else:
                print(f"\n✗ Failed to submit: {response.json().get('message', 'Unknown error')}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def get_all_villagers(self):
        """Get all Villager nodes"""
        try:
            response = requests.get(f"{self.coordinator_url}/nodes", timeout=5)
            if response.status_code == 200:
                data = response.json()
                villagers = {}
                for node in data['nodes']:
                    if node['node_type'] == 'villager':
                        # Build display name
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
        """Trade with other Villagers (via Merchant centralized management)"""
        try:
            # Get current villager information (including node_id)
            my_info = self.get_villager_info()
            if not my_info:
                print("\n✗ Please create a villager first")
                return
            
            my_node_id = my_info.get('node_id')
            
            # Check whether trading with yourself
            if target_node == my_node_id:
                print(f"\n✗ Cannot trade with yourself!")
                print("   Please choose another Villager node")
                return
            
            # Get all Villager nodes
            villagers = self.get_all_villagers()
            
            # Support lookup by node_id
            target_address = None
            target_id = None
            
            if target_node in villagers:
                target_info = villagers[target_node]
                target_address = target_info['address']
                target_id = target_node
            else:
                print(f"\n✗ Villager node not found: {target_node}")
                print(f"\nAvailable Villagers:")
                for nid, info in villagers.items():
                    if nid != my_node_id:  # do not show self
                        print(f"   {nid}: {info['display_name']}")
                print("\n💡 Tip: Use the NodeID")
                print("   e.g.: trade node1 buy wheat 10 100")
                return
            
            # Create trade via Merchant
            print(f"\n📤 Creating trade request (via Merchant node)...")
            
            response = requests.post(
                f"{self.merchant_url}/trade/create",
                json={
                    'initiator_id': my_node_id,
                    'initiator_address': f'localhost:{self.villager_port}',
                    'target_id': target_id,
                    'target_address': target_address,
                    'offer_type': offer_type,
                    'item': item,
                    'quantity': quantity,
                    'price': price
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                trade_id = data['trade_id']
                
                if offer_type == 'buy':
                    print(f"✓ Trade request created: {trade_id}")
                    print(f"  You want to buy {quantity}x {item} from {target_node}, offering {price} gold")
                else:
                    print(f"✓ Trade request created: {trade_id}")
                    print(f"  You want to sell {quantity}x {item} to {target_node}, asking {price} gold")
                
                print(f"\n⏳ Waiting for {target_node} to accept or reject...")
                print(f"💡 Tip: The other side needs to enter 'accept {trade_id}' and 'confirm {trade_id}'")
                print(f"   Use 'mytrades' to view the status of this trade")
            else:
                print(f"\n✗ Create trade request failed: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def get_node_id(self):
        """Get the node_id of the current node"""
        try:
            my_info = self.get_villager_info()
            if my_info:
                return my_info.get('node_id')
            return None
        except:
            return None
    
    def check_my_pending_trade_status(self):
        """Check the status of trades I initiated"""
        if not self.pending_trades:
            return
        
        for trade_id, trade in list(self.pending_trades.items()):
            # If we've already notified once, don't notify again
            if trade.get('status') == 'ready_to_confirm':
                continue
            
            try:
                # Query the trade status from the other side
                response = requests.get(
                    f"http://{trade['target_address']}/trade/pending",
                    timeout=2
                )
                
                if response.status_code == 200:
                    data = response.json()
                    trades_list = data.get('pending_trades', [])
                    
                    # Find our trade
                    for remote_trade in trades_list:
                        if remote_trade['trade_id'] == trade_id:
                            if remote_trade.get('status') == 'accepted':
                                # The other side accepted; prompt user to confirm
                                print("\n" + "="*60)
                                print(f"🎉 The other side has accepted your trade request! [{trade_id}]")
                                print("="*60)
                                print(f"Trade details:")
                                if trade['type'] == 'buy':
                                    print(f"  Buy {trade['quantity']}x {trade['item']}")
                                    print(f"  Pay {trade['price']} gold")
                                else:
                                    print(f"  Sell {trade['quantity']}x {trade['item']}")
                                    print(f"  Receive {trade['price']} gold")
                                print(f"\n💡 Enter 'confirm {trade_id}' to complete the trade")
                                print(f"   Or enter 'cancel {trade_id}' to cancel")
                                print("="*60 + "\n")
                                
                                # Mark as notified
                                self.pending_trades[trade_id]['status'] = 'ready_to_confirm'
                            break
            except:
                pass  # Fail silently
    
    def show_my_pending_trades(self):
        """View all my trades (sent and received)"""
        try:
            node_id = self.get_node_id()
            if not node_id:
                print("\n✗ Unable to get NodeID")
                return
            
            # Get sent trades
            sent_response = requests.get(
                f"{self.merchant_url}/trade/list",
                params={'node_id': node_id, 'type': 'sent'},
                timeout=5
            )
            
            # Get received trades
            received_response = requests.get(
                f"{self.merchant_url}/trade/list",
                params={'node_id': node_id, 'type': 'pending'},
                timeout=5
            )
            
            sent_trades = []
            received_trades = []
            
            if sent_response.status_code == 200:
                sent_data = sent_response.json()
                sent_trades = sent_data.get('trades', [])
            
            if received_response.status_code == 200:
                received_data = received_response.json()
                received_trades = received_data.get('trades', [])
            
            if not sent_trades and not received_trades:
                print("\nYou have no related trades\n")
                return
            
            print("\n" + "="*50)
            print("  My Trades")
            print("="*50)
            
            # Show sent trades
            if sent_trades:
                print("\n📤 Trades I initiated:")
                for trade in sent_trades:
                    print(f"\nTradeID: {trade['trade_id']}")
                    print(f"  Counterparty: {trade['target_id']}")
                    print(f"  Type: {trade['offer_type']}")
                    print(f"  Item: {trade['item']} x{trade['quantity']}")
                    print(f"  Price: {trade['price']}")
                    
                    status = trade.get('status', 'pending')
                    if status == 'accepted':
                        print(f"  Status: ✓ Accepted by counterparty (waiting for both to confirm)")
                        if not trade.get('initiator_confirmed', False):
                            print(f"  💡 Action: confirm {trade['trade_id']}")
                        elif not trade.get('target_confirmed', False):
                            print(f"  💡 Waiting: Counterparty confirming...")
                        else:
                            print(f"  💡 Status: Both confirmed; trade will complete automatically")
                    elif status == 'pending':
                        print(f"  Status: ⏳ Waiting for counterparty to accept")
                        print(f"  💡 Action: wait for response or cancel {trade['trade_id']}")
                    elif status == 'rejected':
                        print(f"  Status: ✗ Rejected")
                    elif status == 'completed':
                        print(f"  Status: ✓ Trade completed")
            
            # Show received trades
            if received_trades:
                print("\n📥 Trades I received:")
                for trade in received_trades:
                    print(f"\nTradeID: {trade['trade_id']}")
                    print(f"  Initiator: {trade['initiator_id']}")
                    print(f"  Type: {trade['offer_type']}")
                    print(f"  Item: {trade['item']} x{trade['quantity']}")
                    print(f"  Price: {trade['price']}")
                    
                    status = trade.get('status', 'pending')
                    if status == 'pending':
                        print(f"  Status: ⏳ Pending")
                        print(f"  💡 Action: accept {trade['trade_id']} or reject {trade['trade_id']}")
                    elif status == 'accepted':
                        print(f"  Status: ✓ Accepted (waiting for both to confirm)")
                        if not trade.get('target_confirmed', False):
                            print(f"  💡 Action: confirm {trade['trade_id']}")
                        elif not trade.get('initiator_confirmed', False):
                            print(f"  💡 Waiting: Initiator confirming...")
                        else:
                            print(f"  💡 Status: Both confirmed; trade will complete automatically")
                    elif status == 'rejected':
                        print(f"  Status: ✗ Rejected")
                    elif status == 'completed':
                        print(f"  Status: ✓ Trade completed")
            
            print("="*50 + "\n")
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def check_pending_trades(self):
        """View received trade requests (from Merchant query)"""
        try:
            node_id = self.get_node_id()
            if not node_id:
                print("\n✗ Unable to get NodeID")
                return
            
            response = requests.get(
                f"{self.merchant_url}/trade/list",
                params={'node_id': node_id, 'type': 'pending'},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                trades = data.get('trades', [])
                
                if not trades:
                    print("\nNo pending trade requests received")
                    return
                
                print("\n" + "="*60)
                print("  Received Trade Requests")
                print("="*60)
                
                for i, trade in enumerate(trades, 1):
                    status = trade.get('status', 'pending')
                    print(f"\n[{i}] TradeID: {trade['trade_id']}")
                    print(f"    From: {trade['initiator_id']}")
                    
                    if trade['offer_type'] == 'buy':
                        print(f"    Type: They want to BUY")
                        print(f"    Item: {trade['quantity']}x {trade['item']}")
                        print(f"    Offer: {trade['price']} gold")
                    else:
                        print(f"    Type: They want to SELL")
                        print(f"    Item: {trade['quantity']}x {trade['item']}")
                        print(f"    Asking: {trade['price']} gold")
                    
                    # Show different prompts based on status
                    if status == 'accepted':
                        print(f"    Status: ✓ Accepted (waiting for both to confirm)")
                        print(f"    Action: confirm {trade['trade_id']}")
                    else:
                        print(f"    Status: ⏳ Pending")
                        print(f"    Action: accept {trade['trade_id']} or reject {trade['trade_id']}")
                
                print("="*60)
            else:
                print("\n✗ Unable to fetch trade requests")
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def accept_trade_request(self, trade_id: str):
        """Accept trade request (via Merchant)"""
        try:
            node_id = self.get_node_id()
            if not node_id:
                print("\n✗ Unable to get NodeID")
                return
            
            response = requests.post(
                f"{self.merchant_url}/trade/accept",
                json={'trade_id': trade_id, 'node_id': node_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"\n✓ Trade accepted: {trade_id}")
                    print(f"  Waiting for both parties to confirm...")
                    print(f"  Use 'confirm {trade_id}' to confirm the trade")
                else:
                    print(f"\n✗ Accept trade failed: {data.get('message')}")
            else:
                print(f"\n✗ Accept trade failed: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def confirm_trade_request(self, trade_id: str):
        """Confirm trade (via Merchant)"""
        try:
            node_id = self.get_node_id()
            if not node_id:
                print("\n✗ Unable to get NodeID")
                return
            
            response = requests.post(
                f"{self.merchant_url}/trade/confirm",
                json={'trade_id': trade_id, 'node_id': node_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"\n✓ Trade confirmed: {trade_id}")
                    if 'completed successfully' in data.get('message', ''):
                        print(f"  🎉 Trade completed!")
                        # Fetch latest villager information
                        villager_info = self.get_villager_info()
                        if villager_info:
                            print(f"  Current status:")
                            print(f"    Money: {villager_info.get('inventory', {}).get('money', 0)}")
                            print(f"    Items: {villager_info.get('inventory', {}).get('items', {})}")
                    else:
                        print(f"  Waiting for the other side to confirm...")
                else:
                    print(f"\n✗ Confirm trade failed: {data.get('message')}")
            else:
                print(f"\n✗ Confirm trade failed: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def reject_trade_request(self, trade_id: str):
        """Reject trade request (via Merchant)"""
        try:
            node_id = self.get_node_id()
            if not node_id:
                print("\n✗ Unable to get NodeID")
                return
            
            response = requests.post(
                f"{self.merchant_url}/trade/reject",
                json={'trade_id': trade_id, 'node_id': node_id},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"\n✓ Trade rejected: {trade_id}")
                else:
                    print(f"\n✗ Reject trade failed: {data.get('message')}")
            else:
                print(f"\n✗ Reject trade failed: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def cancel_trade_request(self, trade_id: str):
        """Cancel trade request (via Merchant)"""
        try:
            node_id = self.get_node_id()
            if not node_id:
                print("\n✗ Unable to get NodeID")
                return
            
            response = requests.post(
                f"{self.merchant_url}/trade/cancel",
                json={'trade_id': trade_id, 'node_id': node_id},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"\n✓ Trade canceled: {trade_id}")
                else:
                    print(f"\n✗ Cancel trade failed: {data.get('message')}")
            else:
                print(f"\n✗ Cancel trade failed: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def prepare_trade_request(self, trade_id: str):
        """Prepare trade (two-phase commit - phase 1)"""
        try:
            response = requests.post(
                f"{self.villager_url}/trade/prepare",
                json={'trade_id': trade_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"\n✓ Trade preparation successful: {trade_id}")
                    print(f"  Waiting for the counterparty to submit the trade...")
                    return True
                else:
                    print(f"\n✗ Trade preparation failed: {data.get('message')}")
                    return False
            else:
                print(f"\n✗ Trade preparation failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"\n✗ Trade preparation exception: {e}")
            return False

    def commit_trade_request(self, trade_id: str):
        """Submit trade (two-phase commit - phase 2)"""
        try:
            response = requests.post(
                f"{self.villager_url}/trade/commit",
                json={'trade_id': trade_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"\n✓ Trade submitted successfully: {trade_id}")
                    villager = data.get('villager', {})
                    if villager:
                        print(f"  Current status:")
                        print(f"    Money: {villager.get('inventory', {}).get('money', 0)}")
                        print(f"    Items: {villager.get('inventory', {}).get('items', {})}")
                    return True
                else:
                    print(f"\n✗ Trade failed to submit: {data.get('message')}")
                    return False
            else:
                print(f"\n✗ Trade failed to submit: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"\n✗ Trade submit exception: {e}")
            return False

    def abort_trade_request(self, trade_id: str):
        """Abort trade (two-phase commit - rollback)"""
        try:
            response = requests.post(
                f"{self.villager_url}/trade/abort",
                json={'trade_id': trade_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"\n✓ Trade aborted successfully: {trade_id}")
                    return True
                else:
                    print(f"\n✗ Trade abort failed: {data.get('message')}")
                    return False
            else:
                print(f"\n✗ Trade abort failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"\n✗ Trade abort exception: {e}")
            return False
    
    def complete_pending_trade(self, trade_id: str = None):
        """Complete a trade I initiated (after the other side accepts)"""
        if not self.pending_trades:
            print("\n✗ No pending trades to handle")
            print("   Use 'trade <Villager> buy/sell ...' to initiate a trade")
            return
        
        # If trade_id not specified, check whether only one pending trade exists
        if trade_id is None:
            if len(self.pending_trades) == 1:
                trade_id = list(self.pending_trades.keys())[0]
            else:
                print("\n✗ Multiple pending trades; please specify a TradeID")
                print("   Available trades:")
                for tid, t in self.pending_trades.items():
                    status_text = "✓ Accepted" if t.get('status') == 'ready_to_confirm' else "⏳ Waiting for acceptance"
                    print(f"   {tid}: {t['type']} {t['quantity']}x {t['item']} ({status_text})")
                print(f"\n   Use 'confirm <trade_id>' to complete a specific trade")
                return
        
        if trade_id not in self.pending_trades:
            print(f"\n✗ Trade not found: {trade_id}")
            return
        
        try:
            trade = self.pending_trades[trade_id]
            
            # Check whether the other side has accepted the trade
            # Simplified: try to complete directly
            
            # First, check if I have sufficient resources
            my_info = self.get_villager_info()
            
            if trade['type'] == 'buy':
                # I'm buying: need enough money
                if my_info['inventory']['money'] < trade['price']:
                    print(f"\n✗ Insufficient money (need {trade['price']}, have {my_info['inventory']['money']})")
                    return
            else:
                # I'm selling: need enough items
                items = my_info['inventory'].get('items', {})
                if items.get(trade['item'], 0) < trade['quantity']:
                    print(f"\n✗ Insufficient items (need {trade['quantity']}x {trade['item']})")
                    return
            
            print(f"\nCompleting trade with {trade['target']}...")
            
            # Notify the counterparty to complete the trade
            response = requests.post(
                f"http://{trade['target_address']}/trade/complete",
                json={
                    'from': my_info['name'],
                    'item': trade['item'],
                    'quantity': trade['quantity'],
                    'price': trade['price'],
                    'type': trade['type'],  # Initiator's type: 'buy' means the counterparty sells to me; 'sell' means they buy from me
                    'trade_id': trade.get('trade_id')  # Pass TradeID for cleanup
                },
                timeout=5
            )
            
            if response.status_code == 200:
                # Update my own state
                if trade['type'] == 'buy':
                    # I buy: deduct money, add item
                    result = requests.post(
                        f"{self.villager_url}/action/trade",
                        json={
                            'target': 'self',  # mark as handled locally
                            'item': trade['item'],
                            'quantity': trade['quantity'],
                            'action': 'buy_from_villager',
                            'price': trade['price']
                        },
                        timeout=5
                    )
                else:
                    # I sell: add money, deduct item
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
                
                # Check whether my state update succeeded
                if result.status_code == 200:
                    print(f"\n✓ Trade completed!")
                    if trade['type'] == 'buy':
                        print(f"  You bought {trade['quantity']}x {trade['item']} from {trade['target']}")
                        print(f"  Paid: {trade['price']} gold")
                    else:
                        print(f"  You sold {trade['quantity']}x {trade['item']} to {trade['target']}")
                        print(f"  Received: {trade['price']} gold")
                    
                    self.display_villager_info()
                    del self.pending_trades[trade_id]  # Clean up the completed trade
                else:
                    result_data = result.json()
                    print(f"\n✗ Trade failed: {result_data.get('message', 'Unknown error')}")
                    print("   Trade has been canceled")
            else:
                error_msg = response.json().get('message', 'Unknown error')
                print(f"\n✗ Trade failed: {error_msg}")
                print("   Possible reasons:")
                print("   - The counterparty lacks sufficient resources")
                print("   - The counterparty has not accepted the trade yet")
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def check_action_status(self):
        """View current action submission status"""
        try:
            response = requests.get(f"{self.coordinator_url}/action/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                print("\n" + "="*50)
                print("  Action Submission Status")
                print("="*50)
                print(f"\nTotal Villagers: {data['total_villagers']}")
                print(f"Submitted: {data['submitted']}/{data['total_villagers']}")
                
                # Show submitted nodes
                if data.get('submitted_nodes'):
                    print(f"\nSubmitted:")
                    for node in data['submitted_nodes']:
                        if isinstance(node, dict):
                            display_name = node['display_name']
                            node_id = node['node_id']
                            action = data['pending_actions'].get(node['node_id'], 'Unknown')
                            print(f"   ✓ [{node_id}] {display_name}: {action}")
                        else:
                            print(f"   ✓ {node}")
                
                # Show nodes waiting to submit
                if data['waiting_for']:
                    print(f"\nWaiting to Submit:")
                    for node in data['waiting_for']:
                        if isinstance(node, dict):
                            node_id = node['node_id']
                            display_name = node['display_name']
                            print(f"   - [{node_id}] {display_name}")
                        else:
                            print(f"   - {node}")
                else:
                    if data['total_villagers'] > 0:
                        print(f"\n✓ All villagers have submitted; time will advance soon")
                
                print("="*50)
            else:
                print("\n✗ Unable to fetch status")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def get_merchant_prices(self):
        """Get merchant price table"""
        try:
            response = requests.get(f"{self.merchant_url}/prices", timeout=5)
            if response.status_code == 200:
                prices = response.json()
                print("\n" + "="*50)
                print("  Merchant Price Table")
                print("="*50)
                print("\n📤 Merchant sells (you buy):")
                for item, price in prices['buy'].items():
                    print(f"   {item}: {price} gold")
                
                print("\n📥 Merchant buys (you sell):")
                for item, price in prices['sell'].items():
                    print(f"   {item}: {price} gold")
                print("="*50)
            else:
                print("\n✗ Unable to fetch price table")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def get_messages(self):
        """Get message list"""
        try:
            response = requests.get(f"{self.villager_url}/messages", timeout=5)
            if response.status_code == 200:
                return response.json()['messages']
            else:
                return []
        except Exception as e:
            print(f"Failed to get messages: {e}")
            return []
    
    def send_message(self, target, content, message_type='private'):
        """Send message"""
        try:
            response = requests.post(
                f"{self.villager_url}/messages/send",
                json={
                    'target': target,
                    'content': content,
                    'type': message_type
                },
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    if message_type == 'broadcast':
                        print(f"✓ Broadcast message sent: {content}")
                    else:
                        print(f"✓ Private message sent to {target}: {content}")
                else:
                    print(f"✗ Send failed: {result.get('message', 'Unknown error')}")
            else:
                print(f"✗ Send failed: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"✗ Error when sending message: {e}")
    
    def display_messages(self):
        """Display message list"""
        messages = self.get_messages()
        
        if not messages:
            print("\n📭 No messages")
            return
        
        print("\n" + "="*60)
        print("  Message List")
        print("="*60)
        
        unread_count = 0
        for msg in messages:
            if not msg['read']:
                unread_count += 1
        
        if unread_count > 0:
            print(f"📬 Unread messages: {unread_count}")
        
        print()
        
        for msg in messages:
            status_icon = "📬" if not msg['read'] else "📭"
            type_icon = "📢" if msg['type'] == 'broadcast' else "💬"
            
            print(f"{status_icon} {type_icon} [{msg['id']}] From: {msg['from']}")
            print(f"   Content: {msg['content']}")
            if msg['type'] == 'private':
                print(f"   To: {msg['to']}")
            print()
        
        print("="*60)
    
    def mark_messages_read(self, message_id=None):
        """Mark messages as read"""
        try:
            data = {}
            if message_id:
                data['message_id'] = message_id
            
            response = requests.post(
                f"{self.villager_url}/messages/mark_read",
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                if message_id:
                    print(f"✓ Message {message_id} marked as read")
                else:
                    print("✓ All messages marked as read")
            else:
                print("✗ Failed to mark messages as read")
        
        except Exception as e:
            print(f"✗ Error when marking messages as read: {e}")
    
    def get_online_villagers(self):
        """Get list of online villagers"""
        try:
            response = requests.get(f"{self.coordinator_url}/nodes", timeout=5)
            if response.status_code == 200:
                nodes_data = response.json()
                villagers = []
                for node in nodes_data['nodes']:
                    if node['node_type'] == 'villager':
                        display_name = node.get('name', node['node_id'])
                        if node.get('occupation'):
                            display_name += f" ({node['occupation']})"
                        villagers.append({
                            'node_id': node['node_id'],
                            'name': node.get('name', node['node_id']),
                            'display_name': display_name
                        })
                return villagers
            else:
                return []
        except Exception as e:
            print(f"Failed to get villager list: {e}")
            return []

    def show_help(self):
        """Show help"""
        print("\n" + "="*50)
        print("  Command List")
        print("="*50)
        print("\nBasic commands:")
        print("  info / i        - View villager status")
        print("  time / t        - View current time")
        print("  status / s      - View submission status of all villagers")
        print("  prices / p      - View merchant prices")
        print("  help / h / ?    - Show this help")
        print("  quit / q / exit - Exit")
        
        print("\nVillager actions:")
        print("  create          - Create a new villager")
        print("  produce / work  - Execute production (auto-submit 'work')")
        print("  sleep / rest    - Sleep to restore stamina (auto-submit 'sleep')")
        print("  idle            - Skip current segment (submit 'idle')")
        print("  eat / e         - Eat bread to restore stamina (does not consume action, no submit)")
        print("  buy <Item> <Quantity>   - Buy from merchant")
        print("  sell <Item> <Quantity>  - Sell to merchant")
        
        print("\nP2P trading between villagers (does not go through Coordinator):")
        print("  trade <Villager> buy <Item> <Quantity> <Price>  - Buy from another villager")
        print("  trade <Villager> sell <Item> <Quantity> <Price> - Sell to another villager")
        print("  mytrades        - View all my trades (sent and received)")
        print("  accept <ID>     - Accept a specific trade request (lock resources)")
        print("  reject <ID>     - Reject a specific trade request")
        print("  confirm <ID>    - Confirm trade (completed after both confirm)")
        print("  cancel <ID>     - Cancel a trade you initiated (specify ID)")
        
        print("\nMessage system:")
        print("  messages / msgs - View all messages")
        print("  send <target> <content> - Send a private message")
        print("  broadcast <content> - Send a broadcast message")
        print("  villagers / list - View list of online villagers")
        print("  read [ID]       - Mark messages as read (optional ID)")
        
        print("\n  Example: send node2 Hi, need wheat?")
        print("           broadcast Selling wheat, discounted prices!")
        print("           messages   → View all messages")
        print("           read       → Mark all messages as read")
        
        print("\n  Example: trade bob buy wheat 10 100  → Initiate a buy request to bob")
        print("           trades                       → View received requests")
        print("           mytrades                     → View requests you initiated")
        print("           accept trade_0               → Accept trade (lock resources)")
        print("           confirm trade_0              → Confirm trade (both confirm)")
        
        print("\nTime synchronization system:")
        print("  ⚠️  Only one major action (work/sleep/idle) per time segment")
        print("  ⚠️  Time advances only after ALL villagers submit actions!")
        print("  This is a distributed synchronization barrier")
        print("  ")
        print("  💡 'produce' and 'sleep' will auto-submit the action")
        print("  💡 If you want to skip the current segment, use the 'idle' command")
        print("  💡 Trading and eating do not consume action and can be done anytime")
        
        print("\nExample workflow (Morning):")
        print("  buy seed 1      → Buy seed (does not consume action)")
        print("  produce         → Produce wheat (auto-submit 'work')")
        print("  [Waiting...]       → After others submit, time advances to Noon")
        print("  ")
        print("  Noon:")
        print("  eat             → Eat bread to restore stamina (does not consume action)")
        print("  produce         → Produce again (auto-submit 'work')")
        print("  [Waiting...]       → Time advances to Evening")
        print("  ")
        print("  Evening:")
        print("  sleep           → Sleep (auto-submit 'sleep')")
        print("  [Waiting...]       → Time advances to next day's Morning")
        
        print("\nProfession production rules:")
        print("  farmer (Farmer):        1 seed → 5 wheat (20 stamina, 1 action point)")
        print("  chef (Chef):            3 wheat → 2 bread (15 stamina, 1 action point)")
        print("  carpenter (Carpenter): 10 wood → 1 house (30 stamina, 1 action point)")
        
        print("\nNew items:")
        print("  bread (Bread)      - Buy from merchant (20 gold) or crafted by Chef")
        print("                       Eating restores 30 stamina")
        print("  temp_room (Temporary room voucher) - Buy from merchant (15 gold)")
        print("                       Can be used to sleep; 1 is consumed at daily settlement")
        print("="*50)
    
    def run(self):
        """Run interactive CLI"""
        print("\n" + "="*60)
        print("  Distributed Virtual Town - Villager Console")
        print("="*60)
        print(f"\nConnecting to Villager Node: localhost:{self.villager_port}")
        
        # Check connection
        if not self.check_connection():
            print("\n✗ Unable to connect to Villager Node. Please make sure the node is running")
            print(f"   Command: python villager.py --port {self.villager_port} --id <name>")
            return
        
        print("✓ Connected successfully!")
        print(f"Current time: {self.get_current_time()}")
        
        # Check if villager is created
        info = self.get_villager_info()
        if info:
            print(f"✓ Villager ready: {info['name']}")
            self.display_villager_info(info)
        else:
            print("\n! Villager not created. Please create a villager first")
            print("  Type 'create' to start")
        
        print("\nType 'help' to see all commands")
        print("💡 Use 'trades' to see received requests, 'mytrades' to see the ones you initiated")
        
        # Main loop
        while True:
            try:
                # Check whether my initiated trade has been accepted
                self.check_my_pending_trade_status()
                
                cmd = input(f"\n[{self.get_current_time()}] > ").strip().lower()
                
                if not cmd:
                    continue
                
                parts = cmd.split()
                command = parts[0]
                
                # Exit command
                if command in ['quit', 'q', 'exit']:
                    print("\nGoodbye!")
                    break
                
                # Help command
                elif command in ['help', 'h', '?']:
                    self.show_help()
                
                # Info command
                elif command in ['info', 'i']:
                    self.display_villager_info()
                
                # Time command
                elif command in ['time', 't']:
                    print(f"\nCurrent time: {self.get_current_time()}")
                
                # View submission status
                elif command in ['status', 's']:
                    self.check_action_status()
                
                # Submit idle action (skip current segment)
                elif command == 'idle' or (command == 'submit' and len(parts) >= 2 and parts[1] == 'idle'):
                    self.submit_action('idle')
                
                # Price table
                elif command in ['prices', 'p']:
                    self.get_merchant_prices()
                
                # Create villager
                elif command == 'create':
                    print("\n=== Create Villager ===")
                    name = input("Name: ").strip()
                    print("Occupation options: farmer (Farmer), chef (Chef), carpenter (Carpenter)")
                    occupation = input("Occupation: ").strip()
                    print("Gender options: male, female")
                    gender = input("Gender: ").strip()
                    personality = input("Personality: ").strip()
                    
                    if name and occupation and gender and personality:
                        self.create_villager(name, occupation, gender, personality)
                    else:
                        print("\n✗ Incomplete information")
                
                # Produce
                elif command in ['produce', 'work']:
                    self.produce()
                
                # Buy
                elif command == 'buy' and len(parts) >= 3:
                    item = parts[1]
                    try:
                        quantity = int(parts[2])
                        self.trade('buy', item, quantity)
                    except ValueError:
                        print("\n✗ Quantity must be an integer")
                
                # Sell
                elif command == 'sell' and len(parts) >= 3:
                    item = parts[1]
                    try:
                        quantity = int(parts[2])
                        self.trade('sell', item, quantity)
                    except ValueError:
                        print("\n✗ Quantity must be an integer")
                
                # Sleep
                elif command in ['sleep', 'rest']:
                    self.sleep()
                
                # Eat
                elif command in ['eat', 'e']:
                    self.eat()
                
                # P2P trade between villagers
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
                            print(f"\n✗ Invalid trade type: {action}")
                            print("   Use 'buy' or 'sell'")
                    except ValueError:
                        print("\n✗ Quantity and price must be integers")
                
                elif command == 'mytrades' or command == 'pending':
                    self.show_my_pending_trades()
                
                # Accept trade request
                elif command == 'accept' and len(parts) >= 2:
                    trade_id = parts[1]
                    self.accept_trade_request(trade_id)
                
                # Reject trade request
                elif command == 'reject' and len(parts) >= 2:
                    trade_id = parts[1]
                    self.reject_trade_request(trade_id)
                
                # Cancel trade request
                elif command == 'cancel' and len(parts) >= 2:
                    trade_id = parts[1]
                    self.cancel_trade_request(trade_id)
                
                # Confirm trade (new system: both must confirm)
                elif command == 'confirm' and len(parts) >= 2:
                    trade_id = parts[1]
                    self.confirm_trade_request(trade_id)
                
                # Abort trade (two-phase commit - rollback)
                elif command == 'abort' and len(parts) >= 2:
                    trade_id = parts[1]
                    self.abort_trade_request(trade_id)
                
                # Confirm a trade I initiated
                elif command == 'confirm':
                    if len(parts) >= 2:
                        trade_id = parts[1]
                        self.complete_pending_trade(trade_id)
                    else:
                        self.complete_pending_trade()  # No ID specified, auto-select
                
                # Cancel a trade I initiated
                elif command == 'cancel':
                    if len(parts) >= 2:
                        trade_id = parts[1]
                        if trade_id in self.pending_trades:
                            print(f"\n✓ Canceled trade {trade_id}")
                            del self.pending_trades[trade_id]
                        else:
                            print(f"\n✗ Trade not found: {trade_id}")
                    else:
                        if self.pending_trades:
                            # If there is only one trade, cancel it directly
                            if len(self.pending_trades) == 1:
                                trade_id = list(self.pending_trades.keys())[0]
                                print(f"\n✓ Canceled trade {trade_id}")
                                del self.pending_trades[trade_id]
                            else:
                                print("\n✗ Multiple pending trades; please specify a TradeID")
                                for tid in self.pending_trades.keys():
                                    print(f"   {tid}")
                        else:
                            print("\n✗ No pending trades to handle")
                
                # Message system commands
                elif command in ['messages', 'msgs']:
                    self.display_messages()
                
                # Send private message
                elif command == 'send' and len(parts) >= 3:
                    target = parts[1]
                    content = ' '.join(parts[2:])
                    self.send_message(target, content, 'private')
                
                # Send broadcast message
                elif command == 'broadcast' and len(parts) >= 2:
                    content = ' '.join(parts[1:])
                    self.send_message('all', content, 'broadcast')
                
                # View list of online villagers
                elif command in ['villagers', 'list']:
                    villagers = self.get_online_villagers()
                    if villagers:
                        print("\n" + "="*50)
                        print("  Online Villagers")
                        print("="*50)
                        for villager in villagers:
                            print(f"  • {villager['display_name']} (ID: {villager['node_id']})")
                        print("="*50)
                    else:
                        print("\n📭 No villagers online")
                
                # Mark messages as read
                elif command == 'read':
                    if len(parts) >= 2:
                        try:
                            message_id = int(parts[1])
                            self.mark_messages_read(message_id)
                        except ValueError:
                            print("\n✗ Message ID must be an integer")
                    else:
                        self.mark_messages_read()
                
                # Unknown command
                else:
                    print(f"\n✗ Unknown command: {command}")
                    print("   Type 'help' to see all commands")
                
            except KeyboardInterrupt:
                print("\n\nUse 'quit' to exit")
            except Exception as e:
                print(f"\n✗ Error: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='VillagerNode Interactive CLI')
    parser.add_argument('--port', type=int, required=True, 
                       help='Villager node port')
    parser.add_argument('--coordinator', type=int, default=5000,
                       help='Coordinator port (default: 5000)')
    parser.add_argument('--merchant', type=int, default=5001,
                       help='Merchant port (default: 5001)')
    parser.add_argument('--coordinator-host', type=str, default='localhost',
                       help='Coordinator host (default: localhost)')
    parser.add_argument('--merchant-host', type=str, default='localhost',
                       help='Merchant host (default: localhost)')
    args = parser.parse_args()
    
    cli = VillagerCLI(args.port, args.coordinator, args.merchant, 
                     args.coordinator_host, args.merchant_host)
    cli.run()


if __name__ == '__main__':
    main()


