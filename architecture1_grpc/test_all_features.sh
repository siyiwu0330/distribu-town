#!/bin/bash

cd "$(dirname "$0")"

echo ""
echo "=================================================================="
echo "  测试gRPC版本所有功能"
echo "=================================================================="
echo ""

# 测试1: CLI创建村民并测试基本命令
echo "【测试 1】 使用CLI创建村民并测试基本命令"
echo "------------------------------------------------------------------"

timeout 10 python interactive_cli.py --port 50053 <<EOF
create
Alice
farmer
female
勤劳的农夫
info
produce
info
price
buy seed 2
info
exit
EOF

echo ""
echo "✓ CLI测试完成"
echo ""

# 测试2: 测试村民间交易
echo "【测试 2】 村民间交易"
echo "------------------------------------------------------------------"

# 在node2创建Bob
timeout 10 python interactive_cli.py --port 50054 <<EOF
create
Bob
carpenter
male
强壮的木匠
info
buy wood 5
info
exit
EOF

echo "✓ Bob created"
sleep 2

# 在node1查看在线村民
timeout 5 python interactive_cli.py --port 50053 <<EOF
nodes
exit
EOF

echo ""

# Alice向Bob发起交易
timeout 10 python interactive_cli.py --port 50053 <<EOF
trade node2 sell wheat 3 30
mytrades
exit
EOF

echo ""
echo "✓ 交易测试完成"
echo ""

# 测试3: 时间推进
echo "【测试 3】 时间推进"
echo "------------------------------------------------------------------"

timeout 5 python interactive_cli.py --port 50053 <<EOF
time
advance
time
exit
EOF

echo ""
echo "✓ 时间推进测试完成"
echo ""

echo "=================================================================="
echo "  ✅ 所有功能测试完成！"
echo "=================================================================="
echo ""
echo "节点仍在运行，可以手动测试："
echo "  python interactive_cli.py --port 50053"
echo "  python interactive_cli.py --port 50054"
echo ""

