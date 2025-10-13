# Distributed Virtual Town

A distributed multi-agent virtual town simulation system implementing two different system architectures and communication models. Supports multi-terminal interactive operations, where each villager runs as an independent node and can engage in production, trading, time synchronization, and other activities.

## Project Overview

This is a distributed system simulating a virtual town, where each villager runs as an independent node. Villagers have different occupations (farmer, chef, carpenter) and can engage in production, trading, and other activities. The system implements global time synchronization and resource management, supporting P2P inter-villager trading and trading with merchants.

## Five Core Features

1. **Villager Management** - Create and manage virtual villagers (character creation system)
2. **Production System** - Different occupations perform production activities (carpenter→house, farmer→wheat, chef→bread)
3. **Trading System** - Trading between villagers and with merchants, peer-to-peer villager trading
4. **Time Synchronization** - Global time management (three time periods: morning, noon, evening)
5. **Resource Management** - Manage stamina, currency, items (wood, wheat, bread, houses)

## Two System Architectures

### Architecture 1: Microservices + gRPC
- Location: `architecture1_grpc/`
- Features:
  - Each villager as an independent gRPC service
  - Central time coordinator manages global clock
  - Uses Protocol Buffers for message format
  - Efficient binary communication

### Architecture 2: RESTful Resource-Oriented + HTTP
- Location: `architecture2_rest/`
- Features:
  - Each villager exposes REST API endpoints
  - Uses HTTP JSON for communication
  - Resource-oriented design
  - Easy to test and debug

## Quick Start

### 1. Setup Environment

```bash
# Create conda environment
conda env create -f environment.yml
conda activate distribu-town

# Or install dependencies with pip
pip install flask requests grpcio protobuf numpy matplotlib openai
```

### 2. Start Base Services

```bash
cd architecture2_rest
bash start_services.sh
```

This will start:
- **Coordinator** (port 5000) - Time coordinator
- **Merchant** (port 5001) - Merchant service

### 3. Start Villager Nodes

```bash
# Start first villager node
./start_villager.sh 5002 node1

# Start second villager node (new terminal)
./start_villager.sh 5003 node2
```

### 4. Connect to Villager Nodes

#### Using Interactive CLI to Control Villagers:

```bash
# Connect to node1 (port 5002)
python interactive_cli.py --port 5002

# Connect to node2 (port 5003) - new terminal
python interactive_cli.py --port 5003
```

#### Using AI Agent to Automatically Control Villagers:

```bash
# AI controls node1
python ai_villager_agent.py --port 5002 --react

# AI controls node2 - new terminal  
python ai_villager_agent.py --port 5003 --react
```

## System Architecture

```
┌─────────────────┐
│ Time Coordinator│ (Synchronizes time across nodes)
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    │         │        │        │
┌───▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐
│Merchant│ │Farmer│ │ Chef │ │Carpenter│
└────────┘ └──────┘ └──────┘ └────────┘
```

## Villager Attributes

- **Stamina**: 0-100, decreases by 10 daily from hunger, consumed by work, restored by sleep
- **Occupation**: Carpenter, Farmer, Chef (Merchant is system NPC)
- **Gender**: Male/Female
- **Personality**: Customizable
- **Assets**: Currency and items (wood, wheat, bread, houses)

## Basic Operations

### Creating a Villager
In the CLI, enter `create`, then follow prompts to enter:
- Name
- Occupation (farmer/chef/carpenter)
- Gender (male/female)
- Personality description

### Common Commands
- `info` - View villager status
- `produce` - Produce items
- `buy <item> <quantity>` - Buy from merchant
- `sell <item> <quantity>` - Sell to merchant
- `sleep` - Sleep to restore stamina
- `eat` - Eat bread to restore stamina
- `prices` - View merchant prices
- `help` - View all commands

### Inter-Villager Trading
- `trade <node_id> buy <item> <quantity> <price>` - Buy from other villager
- `trade <node_id> sell <item> <quantity> <price>` - Sell to other villager
- `mytrades` - View all trades
- `accept <trade_id>` - Accept trade request
- `confirm <trade_id>` - Confirm trade

### Messaging System
- `send <node_id> <message>` - Send private message
- `broadcast <message>` - Send broadcast message
- `messages` - View message list

## Occupation System

### Merchant
- System NPC with fixed prices
- Provides basic resources (seeds, wood)
- Purchases products (wheat, bread)

### Carpenter
- Consumes: Wood + Stamina
- Produces: Houses
- Income: Construction commission fees

### Farmer
- Consumes: Seeds + Stamina
- Produces: Wheat
- Income: Selling wheat

### Chef
- Consumes: Wheat + Stamina
- Produces: Bread
- Income: Selling bread

## Time System

Each day is divided into three periods:
- **Morning**: 1 action point
- **Noon**: 1 action point
- **Evening**: 1 action point

Rules:
- Production activities consume 1 action point and stamina
- Trading and eating don't consume action points
- Sleep restores stamina (requires house)
- Working at night without sleeping costs extra 20 stamina
- 10 stamina deducted at day end (hunger)

## Example Workflows

### A Typical Day
1. **Morning**: Buy seeds → Produce wheat
2. **Noon**: Eat bread to restore stamina → Continue production
3. **Evening**: Sleep to restore stamina

### Multi-Villager Cooperation
1. Farmer produces wheat
2. Chef buys wheat to make bread
3. Carpenter builds houses
4. Villagers engage in P2P trading for better prices

### Creating Villager Nodes

Start villager nodes in new terminals (one terminal per villager):

```bash
# Terminal A: Start node1
cd /path/to/distribu-town/architecture2_rest
conda activate distribu-town
python villager.py --port 5002 --id node1

# Terminal B: Start node2
python villager.py --port 5003 --id node2
```

### Connecting CLI Console

After starting villager nodes, connect CLI control in another terminal:

```bash
# Control node1 (ensure node1 is running on port 5002)
python interactive_cli.py --port 5002

# Control node2 (ensure node2 is running on port 5003)
python interactive_cli.py --port 5003
```

## Usage Guide

### CLI Command List

In the interactive CLI, you can use the following commands:

**Basic Commands:**
- `info` / `i` - View villager status
- `time` / `t` - View current time
- `status` / `s` - View all villagers' submission status
- `prices` / `p` - View merchant prices
- `help` / `h` / `?` - Show help
- `quit` / `q` / `exit` - Exit

**Villager Operations:**
- `create` - Create new villager
- `produce` / `work` - Perform production (auto-submit work)
- `sleep` / `rest` - Sleep to restore stamina (auto-submit sleep)
- `idle` - Skip current period (submit idle)
- `eat` / `e` - Eat bread to restore stamina (doesn't consume action, no submit)
- `buy <item> <quantity>` - Buy from merchant
- `sell <item> <quantity>` - Sell to merchant

**Inter-Villager Trading (P2P):**
- `trade <villager> buy <item> <quantity> <price>` - Buy from other villager
- `trade <villager> sell <item> <quantity> <price>` - Sell to other villager
- `trades` - View received trade requests
- `mytrades` - View your initiated trade requests
- `accept <ID>` - Accept specified trade request
- `reject <ID>` - Reject specified trade request
- `confirm <ID>` - Confirm and complete your initiated trade
- `cancel <ID>` - Cancel your initiated trade

### Typical Workflows

**Morning Period:**
```bash
create                    # Create villager (if not created)
buy seed 10              # Buy seeds (doesn't consume action)
produce                   # Produce wheat (auto-submit work)
# Wait for other villagers to submit actions...
```

**Noon Period:**
```bash
eat                      # Eat bread to restore stamina (doesn't consume action)
produce                  # Produce again (auto-submit work)
# Wait for other villagers to submit actions...
```

**Evening Period:**
```bash
sleep                    # Sleep (auto-submit sleep)
# Wait for other villagers to submit actions...
```

**Inter-Villager Trading:**
```bash
# Villager A initiates trade
trade node2 buy wheat 5 10
mytrades                  # View sent requests

# Villager B reviews and accepts
trades                    # View received requests
accept trade_0            # Accept trade

# Villager A completes trade
mytrades                  # Check if trade request was accepted
confirm trade_0           # Complete trade
```

## System Features

### Distributed Time Synchronization
- Uses Barrier Synchronization mechanism
- Time progresses only after all villagers submit actions
- Supports management of three time periods (morning, noon, evening)

### P2P Trading System
- Direct trading between villagers, not through coordinator
- Supports asynchronous trade requests and responses
- Real-time trade status synchronization

### Occupation Production System
- **Farmer**: 1 seed → 5 wheat (consumes 20 stamina)
- **Chef**: 3 wheat → 2 bread (consumes 15 stamina)  
- **Carpenter**: 10 wood → 1 house (consumes 30 stamina)

### Items and Resources
- **Basic Items**: seed, wheat, bread, wood, house
- **Special Items**: temp_room (temporary room voucher) - used for sleeping
- **Stamina System**: 0-100, consumed by work, restored by sleep

## API Examples

### REST API Calls

```bash
# Create villager
curl -X POST http://localhost:5002/villager \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","occupation":"farmer","gender":"female","personality":"hardworking"}'

# Query villager status
curl http://localhost:5002/villager

# Execute production
curl -X POST http://localhost:5002/action/produce

# Trade with merchant
curl -X POST http://localhost:5002/action/trade \
  -H "Content-Type: application/json" \
  -d '{"target":"merchant","item":"seed","quantity":10}'

# Inter-villager trade
curl -X POST http://localhost:5002/trade/request \
  -H "Content-Type: application/json" \
  -d '{"target":"node2","item":"wheat","quantity":5,"price":10}'
```

## Project Structure

```
distribu-town/
├── architecture1_grpc/          # Architecture 1: Microservices+gRPC
│   ├── proto/                   # Protocol Buffer definitions
│   ├── coordinator.py           # Time coordinator
│   ├── merchant.py              # Merchant node
│   ├── villager.py              # Villager node
│   ├── client.py                # Test client
│   ├── Dockerfile
│   └── docker-compose.yml
├── architecture2_rest/          # Architecture 2: RESTful+HTTP (Recommended)
│   ├── coordinator.py           # Time coordinator
│   ├── merchant.py              # Merchant node
│   ├── villager.py              # Villager node
│   ├── interactive_cli.py       # Interactive CLI client
│   ├── start_demo.sh            # Demo script
│   ├── test_scenario.py         # Test scenarios
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile
│   └── docker-compose.yml
├── common/                      # Common code
│   └── models.py                # Data models
├── performance_tests/           # Performance tests
│   ├── test_grpc.py
│   ├── test_rest.py
│   └── compare_results.py
├── environment.yml              # Conda environment configuration
├── start_interactive.sh         # Interactive startup script
├── demo_interactive.md          # Interactive demo instructions
├── BARRIER_SYNC_GUIDE.md        # Barrier synchronization mechanism guide
└── README.md
```

## Logging and Monitoring

The system generates the following log files during runtime:
- `/tmp/coordinator.log` - Coordinator log
- `/tmp/merchant.log` - Merchant log  
- `/tmp/alice.log` - Alice villager log
- `/tmp/bob.log` - Bob villager log
- `/tmp/charlie.log` - Charlie villager log

View real-time logs:
```bash
tail -f /tmp/coordinator.log
tail -f /tmp/merchant.log
```

## Troubleshooting

### Common Issues

**1. Villager node fails to start**
```bash
# Check if port is occupied
lsof -i :5002

# Check conda environment
conda activate distribu-town
```

**2. CLI connection failed**
```bash
# Ensure villager node is running
curl http://localhost:5002/health

# Check node status
python interactive_cli.py --port 5002
```

**3. Trade cannot be completed**
- Ensure both villager nodes are online
- Check if trade ID is correct
- Review log files to troubleshoot

**4. Time doesn't progress**
- Use `status` command to check if all villagers have submitted actions
- Ensure all villager nodes are connected to coordinator

### Debugging Tips

```bash
# View coordinator status
curl http://localhost:5000/status

# View merchant prices
curl http://localhost:5001/prices

# View villager info
curl http://localhost:5002/villager
```

## Development Log

Developed with AI tool assistance (Claude/Cursor):
- Distributed system architecture design
- REST API and gRPC implementation
- Barrier synchronization mechanism
- P2P trading system
- Interactive CLI interface
- Docker configuration optimization
