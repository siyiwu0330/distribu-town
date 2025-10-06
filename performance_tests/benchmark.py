"""
性能测试脚本
对比两种架构的吞吐量和延迟
"""

import time
import statistics
import sys
import os

# gRPC
import grpc
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'architecture1_grpc'))
from proto import town_pb2
from proto import town_pb2_grpc

# REST
import requests


def benchmark_grpc(num_requests=100):
    """测试gRPC架构的性能"""
    print("\n=== 测试架构1：gRPC微服务 ===")
    
    results = {
        'get_time': [],
        'get_villager_info': [],
        'produce': [],
        'trade': []
    }
    
    try:
        # 测试1：获取时间
        print(f"\n1. 测试GetCurrentTime ({num_requests}次请求)")
        channel = grpc.insecure_channel('localhost:50051')
        stub = town_pb2_grpc.TimeCoordinatorStub(channel)
        
        for i in range(num_requests):
            start = time.time()
            response = stub.GetCurrentTime(town_pb2.Empty())
            latency = (time.time() - start) * 1000  # ms
            results['get_time'].append(latency)
        
        channel.close()
        print(f"   平均延迟: {statistics.mean(results['get_time']):.2f}ms")
        print(f"   中位数: {statistics.median(results['get_time']):.2f}ms")
        print(f"   P95: {statistics.quantiles(results['get_time'], n=20)[18]:.2f}ms")
        print(f"   P99: {statistics.quantiles(results['get_time'], n=100)[98]:.2f}ms")
        
        # 测试2：获取村民信息
        print(f"\n2. 测试GetVillagerInfo ({num_requests}次请求)")
        channel = grpc.insecure_channel('localhost:50053')
        stub = town_pb2_grpc.VillagerNodeStub(channel)
        
        for i in range(num_requests):
            start = time.time()
            response = stub.GetInfo(town_pb2.Empty())
            latency = (time.time() - start) * 1000
            results['get_villager_info'].append(latency)
        
        channel.close()
        print(f"   平均延迟: {statistics.mean(results['get_villager_info']):.2f}ms")
        print(f"   中位数: {statistics.median(results['get_villager_info']):.2f}ms")
        print(f"   P95: {statistics.quantiles(results['get_villager_info'], n=20)[18]:.2f}ms")
        print(f"   P99: {statistics.quantiles(results['get_villager_info'], n=100)[98]:.2f}ms")
        
        # 测试3：吞吐量（连续请求）
        print(f"\n3. 测试吞吐量 ({num_requests*3}次混合请求)")
        start_time = time.time()
        
        coord_channel = grpc.insecure_channel('localhost:50051')
        coord_stub = town_pb2_grpc.TimeCoordinatorStub(coord_channel)
        
        villager_channel = grpc.insecure_channel('localhost:50053')
        villager_stub = town_pb2_grpc.VillagerNodeStub(villager_channel)
        
        merchant_channel = grpc.insecure_channel('localhost:50052')
        merchant_stub = town_pb2_grpc.MerchantNodeStub(merchant_channel)
        
        for i in range(num_requests):
            coord_stub.GetCurrentTime(town_pb2.Empty())
            villager_stub.GetInfo(town_pb2.Empty())
            merchant_stub.GetPrices(town_pb2.Empty())
        
        elapsed = time.time() - start_time
        throughput = (num_requests * 3) / elapsed
        
        coord_channel.close()
        villager_channel.close()
        merchant_channel.close()
        
        print(f"   总时间: {elapsed:.2f}秒")
        print(f"   吞吐量: {throughput:.2f} requests/sec")
        
        return results, throughput
    
    except Exception as e:
        print(f"   错误: {e}")
        print("   提示: 确保gRPC服务正在运行 (architecture1_grpc/start_demo.sh)")
        return None, None


def benchmark_rest(num_requests=100):
    """测试REST架构的性能"""
    print("\n=== 测试架构2：RESTful HTTP ===")
    
    results = {
        'get_time': [],
        'get_villager_info': [],
        'produce': [],
        'trade': []
    }
    
    try:
        # 测试1：获取时间
        print(f"\n1. 测试GET /time ({num_requests}次请求)")
        
        for i in range(num_requests):
            start = time.time()
            response = requests.get('http://localhost:5000/time', timeout=5)
            latency = (time.time() - start) * 1000  # ms
            results['get_time'].append(latency)
        
        print(f"   平均延迟: {statistics.mean(results['get_time']):.2f}ms")
        print(f"   中位数: {statistics.median(results['get_time']):.2f}ms")
        print(f"   P95: {statistics.quantiles(results['get_time'], n=20)[18]:.2f}ms")
        print(f"   P99: {statistics.quantiles(results['get_time'], n=100)[98]:.2f}ms")
        
        # 测试2：获取村民信息
        print(f"\n2. 测试GET /villager ({num_requests}次请求)")
        
        for i in range(num_requests):
            start = time.time()
            response = requests.get('http://localhost:5002/villager', timeout=5)
            latency = (time.time() - start) * 1000
            results['get_villager_info'].append(latency)
        
        print(f"   平均延迟: {statistics.mean(results['get_villager_info']):.2f}ms")
        print(f"   中位数: {statistics.median(results['get_villager_info']):.2f}ms")
        print(f"   P95: {statistics.quantiles(results['get_villager_info'], n=20)[18]:.2f}ms")
        print(f"   P99: {statistics.quantiles(results['get_villager_info'], n=100)[98]:.2f}ms")
        
        # 测试3：吞吐量（连续请求）
        print(f"\n3. 测试吞吐量 ({num_requests*3}次混合请求)")
        start_time = time.time()
        
        for i in range(num_requests):
            requests.get('http://localhost:5000/time', timeout=5)
            requests.get('http://localhost:5002/villager', timeout=5)
            requests.get('http://localhost:5001/prices', timeout=5)
        
        elapsed = time.time() - start_time
        throughput = (num_requests * 3) / elapsed
        
        print(f"   总时间: {elapsed:.2f}秒")
        print(f"   吞吐量: {throughput:.2f} requests/sec")
        
        return results, throughput
    
    except Exception as e:
        print(f"   错误: {e}")
        print("   提示: 确保REST服务正在运行 (architecture2_rest/start_demo.sh)")
        return None, None


def compare_results(grpc_results, grpc_throughput, rest_results, rest_throughput):
    """对比两种架构的结果"""
    print("\n" + "="*60)
    print("性能对比总结")
    print("="*60)
    
    if not grpc_results or not rest_results:
        print("无法进行对比 - 某些服务未运行")
        return
    
    print("\n延迟对比 (平均值):")
    print(f"{'操作':<20} {'gRPC (ms)':<15} {'REST (ms)':<15} {'差异':<15}")
    print("-" * 60)
    
    for key in ['get_time', 'get_villager_info']:
        grpc_avg = statistics.mean(grpc_results[key])
        rest_avg = statistics.mean(rest_results[key])
        diff = ((rest_avg - grpc_avg) / grpc_avg) * 100
        
        operation_names = {
            'get_time': '获取时间',
            'get_villager_info': '获取村民信息'
        }
        
        print(f"{operation_names[key]:<20} {grpc_avg:<15.2f} {rest_avg:<15.2f} {diff:+.1f}%")
    
    print("\n吞吐量对比:")
    print(f"  gRPC: {grpc_throughput:.2f} req/sec")
    print(f"  REST: {rest_throughput:.2f} req/sec")
    diff = ((rest_throughput - grpc_throughput) / grpc_throughput) * 100
    print(f"  差异: {diff:+.1f}%")
    
    print("\n结论:")
    if grpc_throughput > rest_throughput:
        print(f"  - gRPC在吞吐量上表现更好（高 {abs(diff):.1f}%）")
    else:
        print(f"  - REST在吞吐量上表现更好（高 {abs(diff):.1f}%）")
    
    grpc_avg_latency = statistics.mean([statistics.mean(grpc_results[k]) for k in ['get_time', 'get_villager_info']])
    rest_avg_latency = statistics.mean([statistics.mean(rest_results[k]) for k in ['get_time', 'get_villager_info']])
    
    if grpc_avg_latency < rest_avg_latency:
        diff_pct = ((rest_avg_latency - grpc_avg_latency) / grpc_avg_latency) * 100
        print(f"  - gRPC在延迟上表现更好（低 {diff_pct:.1f}%）")
    else:
        diff_pct = ((grpc_avg_latency - rest_avg_latency) / rest_avg_latency) * 100
        print(f"  - REST在延迟上表现更好（低 {diff_pct:.1f}%）")
    
    print("\n架构特点:")
    print("  gRPC:")
    print("    + 二进制协议，传输效率高")
    print("    + 强类型，编译时检查")
    print("    - 需要proto定义和代码生成")
    print("    - 调试相对困难")
    
    print("\n  REST:")
    print("    + JSON格式，易于调试")
    print("    + 广泛支持，易于集成")
    print("    - 文本协议，传输开销大")
    print("    - 弱类型，运行时检查")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='分布式虚拟小镇性能测试')
    parser.add_argument('--requests', type=int, default=100,
                       help='每个测试的请求数量 (默认: 100)')
    parser.add_argument('--arch', type=str, choices=['grpc', 'rest', 'both'], default='both',
                       help='要测试的架构 (默认: both)')
    args = parser.parse_args()
    
    print("="*60)
    print("分布式虚拟小镇 - 性能基准测试")
    print("="*60)
    print(f"\n每个测试将执行 {args.requests} 次请求")
    print("\n注意: 请确保相应的服务已经启动!")
    print("  - gRPC: cd architecture1_grpc && bash start_demo.sh")
    print("  - REST: cd architecture2_rest && bash start_demo.sh")
    
    input("\n按Enter开始测试...")
    
    grpc_results = None
    grpc_throughput = None
    rest_results = None
    rest_throughput = None
    
    if args.arch in ['grpc', 'both']:
        grpc_results, grpc_throughput = benchmark_grpc(args.requests)
    
    if args.arch in ['rest', 'both']:
        rest_results, rest_throughput = benchmark_rest(args.requests)
    
    if args.arch == 'both' and grpc_results and rest_results:
        compare_results(grpc_results, grpc_throughput, rest_results, rest_throughput)
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)


if __name__ == '__main__':
    main()

