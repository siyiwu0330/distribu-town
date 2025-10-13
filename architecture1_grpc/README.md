# Architecture 1: gRPC Distributed Architecture

## Overview

This is a gRPC-based implementation of the distributed virtual town, demonstrating an architecture using Protocol Buffers and gRPC for microservice communication.

## Latest Updates ✨

### Centralized Trading System
- ✅ Implemented centralized trade management same as REST version
- ✅ Merchant node acts as trade coordinator
- ✅ Supports complete trade workflow: Create → Accept → Confirm → Execute
- ✅ Atomic operations and rollback mechanism
- ✅ Interactive CLI supports all trading commands

For details, see [README_TRADING.md](README_TRADING.md)

## Architecture Features

### gRPC Communication
- Service interfaces defined using Protocol Buffers
- HTTP/2 binary protocol, high performance
- Strong type checking
- Auto-generated client code

### Node Types
1. **Coordinator** - Time coordinator
   - Manages global time
   - Synchronizes all nodes
   - Node registration and discovery

2. **Merchant** - Merchant node
   - Provides item buying/selling services
   - **Centralized trade management** (new)
   - Trade ID generation and state management
   - Atomic trade execution

3. **Villager** - Villager node
   - Villager information management
   - Production, trading, sleeping
   - **Atomic trade execution** (new)

## Directory Structure

```
architecture1_grpc/
├── proto/                      # Protocol Buffers definitions
│   ├── town.proto             # Service and message definitions
│   ├── town_pb2.py            # Generated message classes
│   └── town_pb2_grpc.py       # Generated service classes
├── coordinator.py              # Coordinator implementation
├── merchant.py                 # Merchant node implementation
├── villager.py                 # Villager node implementation
├── interactive_cli.py          # Interactive CLI (new)
├── test_centralized_trade.py  # Trading system tests (new)
├── start_test_nodes.sh         # Quick start script (new)
├── README.md                   # This file
└── README_TRADING.md           # Detailed trading system guide (new)
```

## Quick Start

### 1. Install Dependencies

```bash
cd architecture1_grpc
pip install -r requirements.txt
```

### 2. Compile Proto Files (if modified)

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/town.proto
```

### 3. Start Nodes

#### Method 1: Using Startup Script (Recommended)
```bash
./start_test_nodes.sh
```

#### Method 2: Manual Start
```bash
# Terminal 1: Coordinator
python coordinator.py --port 50051

# Terminal 2: Merchant
python merchant.py --port 50052

# Terminal 3: Villager 1
python villager.py --port 50053 --id node1

# Terminal 4: Villager 2
python villager.py --port 50054 --id node2
```

### 4. Test Trading System

```bash
# Run automated tests
python test_centralized_trade.py

# Or use interactive CLI
python interactive_cli.py --id node1 --address localhost:50053
```

## Usage Examples

### Interactive CLI

```bash
# Start CLI
python interactive_cli.py --id node1 --address localhost:50053

# In CLI
> info                              # View my information
> nodes                             # View online villagers
> trade node2 sell wheat 5 50      # Initiate trade with node2
> mytrades                          # View my trades
> confirm trade_1                   # Confirm trade
```

### Programming Interface

```python
import grpc
from proto import town_pb2, town_pb2_grpc

# Connect to merchant node
channel = grpc.insecure_channel('localhost:50052')
stub = town_pb2_grpc.MerchantNodeStub(channel)

# Create trade
response = stub.CreateTrade(town_pb2.CreateTradeRequest(
    initiator_id='node1',
    initiator_address='localhost:50053',
    target_id='node2',
    target_address='localhost:50054',
    offer_type='sell',
    item='wheat',
    quantity=5,
    price=50
))

print(f"Trade ID: {response.trade_id}")
channel.close()
```

## Comparison with REST Version

| Feature | gRPC Version | REST Version |
|---------|-------------|--------------|
| Communication Protocol | gRPC (HTTP/2) | HTTP/JSON |
| Type System | Protobuf strong types | JSON dynamic types |
| Performance | Higher (binary) | Lower (text) |
| Debugging Difficulty | Higher | Lower |
| Cross-language Support | Excellent | Excellent |
| Browser Support | Needs grpc-web | Native |
| Use Case | Internal microservices | Public APIs |

## Development Guide

### Modifying Proto Definitions

1. Edit `proto/town.proto`
2. Recompile:
   ```bash
   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/town.proto
   ```
3. Update service implementations

### Adding New Features

1. Define new messages and RPCs in proto file
2. Recompile proto
3. Implement server-side logic
4. Update client code

### Debugging Tips

1. **View Logs**: After starting with `start_test_nodes.sh`, logs are in `logs/` directory
2. **gRPC Errors**: Check `e.code()` and `e.details()`
3. **Connection Issues**: Confirm ports are not occupied, use `lsof -i :50051`

## Testing

### Unit Tests
```bash
python test_centralized_trade.py
```

### Load Testing
```bash
# TODO: Add concurrent trade tests
```

## Known Limitations

1. **AI Agent**: gRPC version doesn't include AI Agent implementation
   - Recommend using REST version (architecture2_rest) for AI experiments
   - gRPC version mainly demonstrates architectural differences

2. **Error Recovery**: Trade state may be lost after node crashes
   - Production environment needs persistent storage

3. **Concurrency Control**: Current implementation uses simple locking
   - Needs optimization for high concurrency scenarios

## FAQ

### Q: Proto compilation failed
A: Ensure `grpcio-tools` is installed:
```bash
pip install grpcio-tools
```

### Q: Connection failed
A: Check if nodes started properly:
```bash
# Check processes
ps aux | grep python

# Check ports
lsof -i :50051-50054
```

### Q: Trade failed
A: See detailed documentation [README_TRADING.md](README_TRADING.md)

## Next Steps

- [ ] Add AI Agent support (optional)
- [ ] Implement trade history persistence
- [ ] Add more test cases
- [ ] Performance benchmarks
- [ ] Docker containerization

## Reference Resources

- [gRPC Python Documentation](https://grpc.io/docs/languages/python/)
- [Protocol Buffers Guide](https://developers.google.com/protocol-buffers)
- [REST Version Comparison](../architecture2_rest/README.md)

## Contributing

Issues and Pull Requests are welcome!

## License

MIT License
