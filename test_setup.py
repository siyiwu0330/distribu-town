"""
环境验证脚本
检查所有依赖是否正确安装
"""

import sys

def test_imports():
    """测试所有必要的导入"""
    print("检查依赖包...")
    
    try:
        import grpc
        print("  ✓ grpc")
    except ImportError:
        print("  ✗ grpc - 请运行: pip install grpcio")
        return False
    
    try:
        import grpc_tools
        print("  ✓ grpc_tools")
    except ImportError:
        print("  ✗ grpc_tools - 请运行: pip install grpcio-tools")
        return False
    
    try:
        import flask
        print("  ✓ flask")
    except ImportError:
        print("  ✗ flask - 请运行: pip install flask")
        return False
    
    try:
        import requests
        print("  ✓ requests")
    except ImportError:
        print("  ✗ requests - 请运行: pip install requests")
        return False
    
    try:
        import numpy
        print("  ✓ numpy")
    except ImportError:
        print("  ✗ numpy - 请运行: pip install numpy")
        return False
    
    try:
        import matplotlib
        print("  ✓ matplotlib")
    except ImportError:
        print("  ✗ matplotlib - 请运行: pip install matplotlib")
        return False
    
    return True


def test_common_models():
    """测试公共模型"""
    print("\n检查公共模型...")
    
    try:
        sys.path.insert(0, '.')
        from common.models import (
            Villager, Occupation, Gender, Inventory,
            PRODUCTION_RECIPES, MERCHANT_PRICES
        )
        print("  ✓ 公共模型导入成功")
        
        # 测试创建村民
        villager = Villager(
            name="测试村民",
            occupation=Occupation.FARMER,
            gender=Gender.MALE,
            personality="测试"
        )
        print(f"  ✓ 创建村民成功: {villager.name}")
        
        return True
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def test_grpc_proto():
    """测试gRPC proto文件"""
    print("\n检查gRPC proto文件...")
    
    import os
    proto_file = 'architecture1_grpc/proto/town.proto'
    
    if not os.path.exists(proto_file):
        print(f"  ✗ proto文件不存在: {proto_file}")
        return False
    
    print(f"  ✓ proto文件存在")
    
    # 检查生成的Python文件
    pb2_file = 'architecture1_grpc/proto/town_pb2.py'
    grpc_file = 'architecture1_grpc/proto/town_pb2_grpc.py'
    
    if not os.path.exists(pb2_file):
        print(f"  ✗ {pb2_file} 未生成")
        print("     请运行: cd architecture1_grpc && python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/town.proto")
        return False
    
    if not os.path.exists(grpc_file):
        print(f"  ✗ {grpc_file} 未生成")
        print("     请运行: cd architecture1_grpc && python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/town.proto")
        return False
    
    print("  ✓ gRPC代码已生成")
    
    try:
        sys.path.insert(0, 'architecture1_grpc')
        from proto import town_pb2, town_pb2_grpc
        print("  ✓ gRPC模块导入成功")
        return True
    except Exception as e:
        print(f"  ✗ 导入错误: {e}")
        return False


def test_file_structure():
    """测试文件结构"""
    print("\n检查文件结构...")
    
    import os
    
    required_files = [
        'README.md',
        'QUICKSTART.md',
        'common/models.py',
        'architecture1_grpc/coordinator.py',
        'architecture1_grpc/merchant.py',
        'architecture1_grpc/villager.py',
        'architecture1_grpc/client.py',
        'architecture1_grpc/test_scenario.py',
        'architecture2_rest/coordinator.py',
        'architecture2_rest/merchant.py',
        'architecture2_rest/villager.py',
        'architecture2_rest/test_scenario.py',
        'performance_tests/benchmark.py',
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} 不存在")
            all_exist = False
    
    return all_exist


def main():
    print("="*60)
    print("分布式虚拟小镇 - 环境验证")
    print("="*60)
    print()
    
    results = []
    
    results.append(("依赖包", test_imports()))
    results.append(("公共模型", test_common_models()))
    results.append(("gRPC代码", test_grpc_proto()))
    results.append(("文件结构", test_file_structure()))
    
    print("\n" + "="*60)
    print("验证结果")
    print("="*60)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:<20} {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✓ 所有检查通过！系统已准备就绪。")
        print("\n下一步:")
        print("  1. 查看 QUICKSTART.md 了解如何启动系统")
        print("  2. 运行 bash demo_complete.sh 查看完整演示")
        print("  3. 或者分别测试两个架构:")
        print("     - cd architecture1_grpc && bash start_demo.sh")
        print("     - cd architecture2_rest && bash start_demo.sh")
        return 0
    else:
        print("\n✗ 某些检查未通过，请解决上述问题。")
        return 1


if __name__ == '__main__':
    sys.exit(main())

