#!/bin/bash

# AI Agent村民启动脚本
# 用于启动基于GPT的智能村民代理

echo "======================================================"
echo "  启动AI Agent村民 - 基于GPT的智能村民代理"
echo "======================================================"
echo ""

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "✗ Python未安装"
    exit 1
fi

# 检查必要的Python包
echo "检查依赖包..."
python -c "import openai, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装必要的依赖包..."
    pip install openai requests
fi

# 默认配置
DEFAULT_PORT=5002
DEFAULT_COORDINATOR=5000
DEFAULT_MERCHANT=5001
DEFAULT_MODEL="gpt-4o"
API_KEY="${OPENAI_API_KEY}"

# 解析命令行参数
PORT=$DEFAULT_PORT
COORDINATOR=$DEFAULT_COORDINATOR
MERCHANT=$DEFAULT_MERCHANT
MODEL=$DEFAULT_MODEL
AUTO_MODE=false
INTERVAL=30
REACT_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --coordinator)
            COORDINATOR="$2"
            shift 2
            ;;
        --merchant)
            MERCHANT="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --auto)
            AUTO_MODE=true
            INTERVAL="$2"
            shift 2
            ;;
        --react)
            REACT_MODE=true
            shift
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --port PORT          村民节点端口 (默认: $DEFAULT_PORT)"
            echo "  --coordinator PORT   协调器端口 (默认: $DEFAULT_COORDINATOR)"
            echo "  --merchant PORT      商人端口 (默认: $DEFAULT_MERCHANT)"
            echo "  --model MODEL        GPT模型 (默认: $DEFAULT_MODEL)"
            echo "  --auto INTERVAL      自动模式，指定决策间隔秒数"
            echo "  --react              启用ReAct推理模式"
            echo "  --help               显示此帮助"
            echo ""
            echo "示例:"
            echo "  $0 --port 5002                    # 连接到端口5002的村民节点"
            echo "  $0 --port 5003 --auto 60          # 自动模式，60秒决策一次"
            echo "  $0 --model gpt-4                   # 使用GPT-4模型"
            echo "  $0 --react                         # 启用ReAct推理模式"
            echo ""
            echo "环境变量:"
            echo "  OPENAI_API_KEY       OpenAI API Key (必需)"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

echo "配置信息:"
echo "  村民节点端口: $PORT"
echo "  协调器端口: $COORDINATOR"
echo "  商人端口: $MERCHANT"
echo "  GPT模型: $MODEL"
if [ -n "$API_KEY" ]; then
    echo "  API Key: ${API_KEY:0:20}..."
else
    echo "  API Key: 未设置 (请设置 OPENAI_API_KEY 环境变量)"
fi
echo ""

# 检查村民节点是否运行
echo "检查村民节点连接..."
if ! curl -s "http://localhost:$PORT/health" > /dev/null; then
    echo "✗ 无法连接到村民节点 (端口 $PORT)"
    echo "请确保村民节点正在运行:"
    echo "  python architecture2_rest/villager.py --port $PORT --id node1"
    exit 1
fi
echo "✓ 村民节点连接正常"

# 检查协调器
echo "检查协调器连接..."
if ! curl -s "http://localhost:$COORDINATOR/health" > /dev/null; then
    echo "✗ 无法连接到协调器 (端口 $COORDINATOR)"
    echo "请确保协调器正在运行:"
    echo "  python architecture2_rest/coordinator.py --port $COORDINATOR"
    exit 1
fi
echo "✓ 协调器连接正常"

# 检查商人
echo "检查商人连接..."
if ! curl -s "http://localhost:$MERCHANT/health" > /dev/null; then
    echo "✗ 无法连接到商人 (端口 $MERCHANT)"
    echo "请确保商人正在运行:"
    echo "  python architecture2_rest/merchant.py --port $MERCHANT --coordinator localhost:$COORDINATOR"
    exit 1
fi
echo "✓ 商人连接正常"

echo ""
echo "======================================================"
echo "✓ 所有服务连接正常，启动AI Agent"
echo "======================================================"
echo ""

# 检查API Key
if [ -z "$API_KEY" ]; then
    echo "✗ 未设置 OPENAI_API_KEY 环境变量"
    echo "请设置API Key:"
    echo "  export OPENAI_API_KEY='your-api-key-here'"
    echo "或使用 --api-key 参数"
    exit 1
fi

# 启动AI Agent
if [ "$AUTO_MODE" = true ]; then
    echo "启动自动模式 (间隔: ${INTERVAL}秒)"
    REACT_FLAG=""
    if [ "$REACT_MODE" = true ]; then
        REACT_FLAG="--react"
        echo "启用ReAct推理模式"
    fi
    python architecture2_rest/ai_villager_agent.py \
        --port $PORT \
        --coordinator $COORDINATOR \
        --merchant $MERCHANT \
        --api-key "$API_KEY" \
        --model "$MODEL" \
        $REACT_FLAG \
        --auto $INTERVAL
else
    echo "启动交互模式"
    REACT_FLAG=""
    if [ "$REACT_MODE" = true ]; then
        REACT_FLAG="--react"
        echo "启用ReAct推理模式"
    fi
    python architecture2_rest/ai_villager_agent.py \
        --port $PORT \
        --coordinator $COORDINATOR \
        --merchant $MERCHANT \
        --api-key "$API_KEY" \
        --model "$MODEL" \
        $REACT_FLAG
fi
