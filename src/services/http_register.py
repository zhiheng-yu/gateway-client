import json
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
import etcd3
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class HttpServiceInfo:
    """HTTP服务信息"""
    service_name: str
    container_name: str
    http_port: int          # HTTP 端口
    http_endpoint: str      # 服务名.{http_endpoint}
    create_time: str        # 创建时间
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式用于存储到 etcd"""
        return asdict(self)

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class EtcdHttpServiceRegister:
    """基于 etcd 的HTTP服务注册客户端"""

    def __init__(self, etcd_host: str = 'localhost', etcd_port: int = 2379,
                 service_prefix: str = '/gateway-client/services/http/',
                 http_endpoint: str = 'example.com'):
        """
        初始化 etcd 服务注册客户端

        :param etcd_host: etcd 服务器地址
        :param etcd_port: etcd 服务器端口
        :param service_prefix: 服务键前缀
        :param http_endpoint: HTTP 访问端点
        """
        self.etcd_host = etcd_host
        self.etcd_port = etcd_port
        self.service_prefix = service_prefix
        self.http_endpoint = http_endpoint
        self.client = None

    def connect(self) -> bool:
        """连接到 etcd 服务器"""
        try:
            self.client = etcd3.client(host=self.etcd_host, port=self.etcd_port)
            # 测试连接
            self.client.status()
            logger.info(f"成功连接到 etcd 服务器: {self.etcd_host}:{self.etcd_port}")
            return True
        except Exception as e:
            logger.error(f"连接 etcd 服务器失败: {e}")
            return False

    def disconnect(self):
        """断开 etcd 连接"""
        if self.client:
            self.client.close()
            logger.info("已断开 etcd 连接")

    def register_service(self,
                         http_endpoint: str,
                         service_name: str,
                         container_name: str,
                         http_port: int) -> bool:
        """
        注册HTTP服务到 etcd

        :param service_name: 服务名称
        :param container_name: 容器名称
        :param http_port: HTTP 端口
        :return: 注册是否成功
        """
        if not self.client:
            logger.error("etcd 客户端未连接")
            return False

        try:
            # 生成服务信息
            service_info = HttpServiceInfo(
                service_name=service_name,
                container_name=container_name,
                http_port=http_port,
                http_endpoint=http_endpoint,
                create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            # 构建 etcd 键
            service_key = f"{self.service_prefix}{service_name}"

            # 写入 etcd
            self.client.put(service_key, service_info.to_json())

            logger.info(f"成功注册HTTP服务: {service_name}")
            logger.debug(f"  HTTP 端点: {service_info.http_endpoint}")
            logger.debug(f"  etcd 键: {service_key}")

            return True

        except Exception as e:
            logger.error(f"注册服务失败 {service_name}: {e}")
            return False

    def unregister_service(self, service_name: str) -> bool:
        """
        从 etcd 中删除HTTP服务

        :param service_name: 服务名称
        :return: 删除是否成功
        """
        if not self.client:
            logger.error("etcd 客户端未连接")
            return False

        try:
            # 构建 etcd 键
            service_key = f"{self.service_prefix}{service_name}"

            # 从 etcd 删除
            deleted = self.client.delete(service_key)
            if deleted:
                logger.info(f"成功删除服务: {service_name}")
            else:
                logger.warning(f"服务不存在: {service_name}")

            return deleted

        except Exception as e:
            logger.error(f"删除服务失败 {service_name}: {e}")
            return False

    def get_service(self, service_name: str) -> Optional[HttpServiceInfo]:
        """
        从 etcd 获取HTTP服务信息

        :param service_name: 服务名称
        :return: 服务信息，如果不存在则返回 None
        """
        if not self.client:
            logger.error("etcd 客户端未连接")
            return None

        try:
            service_key = f"{self.service_prefix}{service_name}"
            value, _ = self.client.get(service_key)

            if value:
                service_data = json.loads(value.decode('utf-8'))
                return HttpServiceInfo(**service_data)
            else:
                logger.debug(f"HTTP服务不存在: {service_name}")
                return None

        except Exception as e:
            logger.error(f"获取服务信息失败 {service_name}: {e}")
            return None

    def list_services(self) -> Dict[str, HttpServiceInfo]:
        """
        列出所有已注册的HTTP服务

        :return: 服务信息字典
        """
        if not self.client:
            logger.error("etcd 客户端未连接")
            return {}

        try:
            services = {}
            # 获取所有以服务前缀开头的键值对
            for value, metadata in self.client.get_prefix(self.service_prefix):
                if value:
                    key = metadata.key.decode('utf-8')
                    container_name = key.replace(self.service_prefix, '')

                    try:
                        service_data = json.loads(value.decode('utf-8'))
                        services[container_name] = HttpServiceInfo(**service_data)
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"解析HTTP服务数据失败 {container_name}: {e}")
                        continue

            return services

        except Exception as e:
            logger.error(f"获取服务列表失败: {e}")
            return {}

    def print_service_summary(self):
        """打印HTTP服务注册摘要"""
        services = self.list_services()

        print("\n" + "="*80)
        print("🌐 网关客户端HTTP服务注册摘要")
        print("="*80)

        if services:
            print(f"📊 已注册HTTP服务数量: {len(services)}")
            print("\nHTTP服务列表:")

            for service_name, service in services.items():
                print(f"\n📦 {service_name}")
                print(f"  🌐 HTTP: {service.http_endpoint}")
                print(f"  📅 创建时间: {service.create_time}")
        else:
            print("📭 暂无已注册的HTTP服务")

        print("="*80)
