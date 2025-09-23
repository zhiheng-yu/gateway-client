"""
Gateway Client API 测试脚本
演示如何使用新的 FastAPI 接口
"""

import requests
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API 基础地址
BASE_URL = "http://localhost:2381"


def test_api_endpoints():
    """测试 API 端点"""

    # 测试服务名称
    test_service = "newfoo"

    print("🧪 测试 Gateway Client API")
    print("=" * 50)

    # 1. 测试根路径
    print("\n1️⃣ 测试根路径...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    # 2. 测试健康检查
    print("\n2️⃣ 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    # 3. 测试注册 HTTP 服务
    print(f"\n3️⃣ 测试注册 HTTP 服务 ({test_service})...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/gateway/http/{test_service}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    try:
        response = requests.get(f"{BASE_URL}/api/v1/gateway/http/{test_service}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    # 4. 测试注册 SSH 服务
    print(f"\n4️⃣ 测试注册 SSH 服务 ({test_service})...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/gateway/ssh/{test_service}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    try:
        response = requests.get(f"{BASE_URL}/api/v1/gateway/ssh/{test_service}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    input("按 Enter 键测试删除服务...")

    # 5. 测试删除 HTTP 服务
    print(f"\n5️⃣ 测试删除 HTTP 服务 ({test_service})...")
    try:
        response = requests.delete(f"{BASE_URL}/api/v1/gateway/http/{test_service}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    # 6. 测试删除 SSH 服务
    print(f"\n6️⃣ 测试删除 SSH 服务 ({test_service})...")
    try:
        response = requests.delete(f"{BASE_URL}/api/v1/gateway/ssh/{test_service}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    print("\n" + "=" * 50)
    print("✅ API 测试完成")


if __name__ == "__main__":
    print("📝 请确保 API 服务已启动 (python start_api.py)")
    input("按 Enter 键开始测试...")
    test_api_endpoints()
