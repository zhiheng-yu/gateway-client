import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import etcd3

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ContainerService:
    """容器服务信息"""
    service_name: str
    container_name: str
    image: str
    create_time: str
    version: int
    exposed_ports: Dict[str, Any]
    port_bindings: Dict[str, List[Dict[str, str]]]
    hostname: str = ""
    environment: List[str] = None

    def __post_init__(self):
        if self.environment is None:
            self.environment = []

    def get_service_ports(self) -> Dict[str, str]:
        """获取服务端口映射 (内部端口 -> 主机端口)"""
        port_map = {}
        for internal_port, bindings in self.port_bindings.items():
            if bindings and len(bindings) > 0:
                host_port = bindings[0].get('HostPort', '')
                if host_port:
                    port_map[internal_port] = host_port
        return port_map

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'service_name': self.service_name,
            'container_name': self.container_name,
            'image': self.image,
            'create_time': self.create_time,
            'version': self.version,
            'exposed_ports': self.exposed_ports,
            'port_bindings': self.port_bindings,
            'hostname': self.hostname,
            'environment': self.environment,
            'service_ports': self.get_service_ports()
        }


class EtcdServiceDiscovery:
    """基于 etcd 的服务发现客户端"""

    def __init__(self, etcd_host: str = 'localhost', etcd_port: int = 2379,
                 service_prefix: str = '/gpu-docker-api/apis/v1/containers/'):
        """
        初始化 etcd 服务发现客户端

        :param etcd_host: etcd 服务器地址
        :param etcd_port: etcd 服务器端口
        :param service_prefix: 服务键前缀
        """
        self.etcd_host = etcd_host
        self.etcd_port = etcd_port
        self.service_prefix = service_prefix
        self.client = None
        self.services: Dict[str, ContainerService] = {}

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

    def parse_container_data(self, service_name: str, data: str) -> Optional[ContainerService]:
        """解析容器数据"""
        try:
            container_info = json.loads(data)

            config = container_info.get('config', {})
            host_config = container_info.get('hostConfig', {})

            service = ContainerService(
                service_name=service_name,
                container_name=container_info.get('containerName', ''),
                image=config.get('Image', ''),
                create_time=container_info.get('createTime', ''),
                version=container_info.get('version', 1),
                exposed_ports=config.get('ExposedPorts', {}),
                port_bindings=host_config.get('PortBindings', {}),
                hostname=config.get('Hostname', ''),
                environment=config.get('Env', [])
            )

            return service
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"解析容器数据失败: {e}")
            return None

    def print_service_details(self, service: ContainerService, action: str = "发现"):
        """打印服务详情"""
        logger.debug("")
        logger.debug("" + "="*80)
        logger.debug(f"🔍 {action}新服务: {service.container_name}")
        logger.debug("="*80)

        logger.debug(f"📦 容器名称: {service.container_name}")
        logger.debug(f"🐳 镜像: {service.image}")
        logger.debug(f"📅 创建时间: {service.create_time}")
        logger.debug(f"🔢 版本: {service.version}")
        logger.debug(f"🏠 主机名: {service.hostname or '未设置'}")

        # 打印端口映射
        port_map = service.get_service_ports()
        if port_map:
            logger.debug("")
            logger.debug("端口映射:")
            for internal_port, host_port in port_map.items():
                service_type = internal_port.split('/')[0]
                protocol = internal_port.split('/')[1] if '/' in internal_port else 'tcp'
                logger.debug(f"  • {service_type}/{protocol} -> 主机端口 {host_port}")

        # 打印暴露的端口
        if service.exposed_ports:
            logger.debug(f"")
            logger.debug(f"📡 暴露端口: {', '.join(service.exposed_ports.keys())}")

        # 打印环境变量
        if service.environment:
            logger.debug(f"")
            logger.debug(f"🔧 环境变量 ({len(service.environment)} 个):")
            for env in service.environment[:5]:  # 只显示前5个
                logger.debug(f"  • {env}")
            if len(service.environment) > 5:
                logger.debug(f"  ... 还有 {len(service.environment) - 5} 个环境变量")

        logger.debug("="*80)

    def get_all_services(self) -> Dict[str, ContainerService]:
        """获取所有现有服务"""
        if not self.client:
            logger.error("etcd 客户端未连接")
            return {}

        try:
            services = {}
            # 获取所有以服务前缀开头的键值对
            for value, metadata in self.client.get_prefix(self.service_prefix):
                if value:
                    key = metadata.key.decode('utf-8')
                    service_name = key.replace(self.service_prefix, '')

                    service = self.parse_container_data(service_name, value.decode('utf-8'))
                    if service:
                        services[service_name] = service
                        logger.info(f"发现现有服务: {service_name}")

            return services
        except Exception as e:
            logger.error(f"获取服务列表失败: {e}")
            return {}

    def get_service(self, service_name: str) -> Optional[ContainerService]:
        """获取特定服务信息"""
        if not self.client:
            logger.error("etcd 客户端未连接")
            return None

        try:
            # 直接从etcd获取服务信息
            key = f"{self.service_prefix}{service_name}"
            value, _ = self.client.get(key)

            if value:
                service = self.parse_container_data(service_name, value.decode('utf-8'))
                if service:
                    logger.info(f"获取到服务信息: {service_name}")
                    return service
            else:
                logger.info(f"服务不存在: {service_name}")
                return None

        except Exception as e:
            logger.error(f"获取服务信息失败: {e}")
            return None

    def list_services(self) -> List[str]:
        """列出所有服务名称"""
        return list(self.services.keys())
