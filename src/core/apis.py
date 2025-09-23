"""
Gateway Client FastAPI Application
基于 FastAPI 的网关客户端 API 服务
"""

import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
from services.discovery import EtcdServiceDiscovery
from services.http_register import EtcdHttpServiceRegister
from services.ssh_register import EtcdSshServiceRegister
from utils.port_pool import PortPool
from proxies.frp import FrpClient
from proxies.kong import KongProxy

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServiceResponse(BaseModel):
    """服务响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class GatewayClient:
    """网关客户端主类"""

    def __init__(self,
                 local_ip: str = '127.0.0.1',
                 etcd_host: str = 'localhost',
                 etcd_port: int = 2379,
                 ssh_port_start: int = 40000,
                 ssh_port_end: int = 40099,
                 http_endpoint: str = 'example.com',
                 ssh_endpoint: str = 'connect.example.com',
                 frp_host: str = 'localhost',
                 frp_port: int = 7400,
                 frp_username: str = 'admin',
                 frp_password: str = '123456',
                 kong_admin_url: str = 'http://127.0.0.1:8001'):
        """
        初始化网关客户端

        :param local_ip: 本地 IP 地址
        :param etcd_host: etcd 服务器地址
        :param etcd_port: etcd 服务器端口
        :param ssh_port_start: SSH 端口池起始端口
        :param ssh_port_end: SSH 端口池结束端口
        :param http_endpoint: HTTP 访问端点域名
        :param ssh_endpoint: SSH 访问端点域名
        :param frp_host: FRP 客户端地址
        :param frp_port: FRP 客户端端口
        :param frp_username: FRP 控制台用户名
        :param frp_password: FRP 控制台密码
        :param kong_admin_url: Kong Admin API 地址
        """
        self.local_ip = local_ip
        self.etcd_host = etcd_host
        self.etcd_port = etcd_port
        self.http_endpoint = http_endpoint
        self.ssh_endpoint = ssh_endpoint

        # 初始化服务发现
        self.discovery = EtcdServiceDiscovery(
            etcd_host=etcd_host,
            etcd_port=etcd_port,
            service_prefix='/gpu-docker-api/apis/v1/containers/'
        )

        # 初始化HTTP服务注册
        self.http_register = EtcdHttpServiceRegister(
            etcd_host=etcd_host,
            etcd_port=etcd_port,
            service_prefix='/gateway-client/services/http/',
            http_endpoint=http_endpoint
        )

        # 初始化SSH服务注册
        self.ssh_register = EtcdSshServiceRegister(
            etcd_host=etcd_host,
            etcd_port=etcd_port,
            service_prefix='/gateway-client/services/ssh/',
            ssh_endpoint=ssh_endpoint
        )

        # 初始化端口池
        self.port_pool = PortPool(ssh_port_start, ssh_port_end)

        # 初始化 FRP 客户端
        self.frp_client = FrpClient(
            frp_host=frp_host,
            frp_port=frp_port,
            username=frp_username,
            password=frp_password
        )

        # 初始化 Kong 代理
        self.kong_proxy = KongProxy(kong_admin_url=kong_admin_url)

        # 连接状态
        self._connected = False

    def connect(self) -> bool:
        """连接所有服务"""
        if self._connected:
            return True

        # 连接服务发现
        if not self.discovery.connect():
            logger.error("❌ 无法连接到服务发现")
            return False

        # 连接HTTP服务注册
        if not self.http_register.connect():
            logger.error("❌ 无法连接到HTTP服务注册")
            return False

        # 连接SSH服务注册
        if not self.ssh_register.connect():
            logger.error("❌ 无法连接到SSH服务注册")
            return False

        self._connected = True
        logger.info("✅ 所有服务连接成功")
        return True

    def disconnect(self):
        """断开所有服务连接"""
        if self._connected:
            self.discovery.disconnect()
            self.http_register.disconnect()
            self.ssh_register.disconnect()
            self._connected = False
            logger.info("🔌 已断开所有服务连接")

    def register_http_service(self, service_name: str) -> ServiceResponse:
        """
        注册 HTTP 服务

        :param service_name: 服务名称
        :return: 服务响应
        """
        if not self._connected:
            if not self.connect():
                return ServiceResponse(
                    success=False,
                    message="无法连接到 etcd 服务"
                )

        try:
            # 从服务发现获取服务信息
            service = self.discovery.get_service(service_name)
            if not service:
                return ServiceResponse(
                    success=False,
                    message=f"服务 {service_name} 不存在"
                )

            # 检查HTTP服务是否已经注册
            existing_service = self.http_register.get_service(service_name)
            if existing_service and existing_service.container_name == service.container_name:
                logger.info(
                    f"✅ HTTP 服务已注册: {service_name}:{existing_service.http_port} "
                    f"-> {existing_service.http_endpoint}"
                )

                return ServiceResponse(
                    success=True,
                    message=f"服务 {service_name} 已注册",
                    data={
                        "http_endpoint": existing_service.http_endpoint,
                        "service_name": service_name,
                        "container_name": existing_service.container_name
                    }
                )

            # 提取端口信息
            port_map = service.get_service_ports()

            # 获取 HTTP 端口 (80/tcp)
            http_port = None
            for port_key, host_port in port_map.items():
                if port_key.startswith('80/'):
                    http_port = int(host_port)
                    break

            if http_port is None:
                return ServiceResponse(
                    success=False,
                    message=f"服务 {service_name} 没有 HTTP 端口 (80/tcp)"
                )

            # 先添加 Kong HTTP 代理
            http_endpoint = f"{service_name}.{self.http_endpoint}"
            kong_success = self.kong_proxy.add_http_proxy(
                name=service_name,
                host=self.local_ip,
                port=http_port,
                domain=http_endpoint
            )

            if not kong_success:
                return ServiceResponse(
                    success=False,
                    message=f"Kong HTTP 代理添加失败"
                )

            # 注册HTTP服务
            success = self.http_register.register_service(
                service_name=service_name,
                container_name=service.container_name,
                http_port=http_port
            )

            if success:
                logger.info(f"✅ HTTP 服务注册成功: {service_name}:{http_port} -> {http_endpoint}")

                return ServiceResponse(
                    success=True,
                    message=f"HTTP 服务注册成功",
                    data={
                        "http_endpoint": http_endpoint,
                        "service_name": service_name,
                        "container_name": service.container_name,
                        "http_port": http_port
                    }
                )
            else:
                # 注册失败，清理 Kong 代理
                self.kong_proxy.delete_http_proxy(service_name)
                return ServiceResponse(
                    success=False,
                    message=f"服务注册失败"
                )

        except Exception as e:
            logger.error(f"注册 HTTP 服务失败 {service_name}: {e}")
            return ServiceResponse(
                success=False,
                message=f"注册服务时发生错误: {str(e)}"
            )

    def unregister_http_service(self, service_name: str) -> ServiceResponse:
        """
        删除 HTTP 服务

        :param service_name: 服务名称
        :return: 服务响应
        """
        if not self._connected:
            if not self.connect():
                return ServiceResponse(
                    success=False,
                    message="无法连接到 etcd 服务"
                )

        try:
            # 检查HTTP服务是否存在
            existing_service = self.http_register.get_service(service_name)
            if not existing_service:
                return ServiceResponse(
                    success=False,
                    message=f"服务 {service_name} 不存在"
                )

            # 从 etcd 删除HTTP服务
            success = self.http_register.unregister_service(service_name)

            if success:
                # 删除对应的 Kong HTTP 代理
                kong_success = self.kong_proxy.delete_http_proxy(service_name)

                if not kong_success:
                    logger.warning(f"⚠️ Kong HTTP 代理删除失败: {service_name}")
                else:
                    logger.info(f"✅ Kong HTTP 代理删除成功: {service_name}")

                logger.info(f"✅ HTTP 服务删除成功: {service_name}")

                return ServiceResponse(
                    success=True,
                    message=f"HTTP 服务删除成功",
                    data={"service_name": service_name}
                )
            else:
                return ServiceResponse(
                    success=False,
                    message=f"服务删除失败"
                )

        except Exception as e:
            logger.error(f"删除 HTTP 服务失败 {service_name}: {e}")
            return ServiceResponse(
                success=False,
                message=f"删除服务时发生错误: {str(e)}"
            )

    def register_ssh_service(self, service_name: str) -> ServiceResponse:
        """
        注册 SSH 服务

        :param service_name: 服务名称
        :return: 服务响应
        """
        if not self._connected:
            if not self.connect():
                return ServiceResponse(
                    success=False,
                    message="无法连接到 etcd 服务"
                )

        try:
            # 从服务发现获取服务信息
            service = self.discovery.get_service(service_name)
            if not service:
                return ServiceResponse(
                    success=False,
                    message=f"服务 {service_name} 不存在"
                )

            # 检查SSH服务是否已经注册
            existing_service = self.ssh_register.get_service(service_name)
            if existing_service and existing_service.container_name == service.container_name:
                logger.info(
                    f"✅ SSH 服务已注册: {service_name}:{existing_service.ssh_port} -> "
                    f"{existing_service.ssh_endpoint}"
                )

                return ServiceResponse(
                    success=True,
                    message=f"服务 {service_name} 已注册",
                    data={
                        "ssh_endpoint": existing_service.ssh_endpoint,
                        "service_name": service_name,
                        "container_name": existing_service.container_name
                    }
                )

            # 提取端口信息
            port_map = service.get_service_ports()

            # 获取 SSH 端口 (22/tcp)
            src_ssh_port = None
            for port_key, host_port in port_map.items():
                if port_key.startswith('22/'):
                    src_ssh_port = int(host_port)
                    break

            if src_ssh_port is None:
                return ServiceResponse(
                    success=False,
                    message=f"服务 {service_name} 没有 SSH 端口 (22/tcp)"
                )

            # 从端口池分配目标 SSH 端口
            try:
                dst_ssh_port = self.port_pool.assign(service_name)
            except RuntimeError as e:
                return ServiceResponse(
                    success=False,
                    message=f"端口池分配失败: {str(e)}"
                )

            # 先添加 FRP TCP 代理
            frp_proxy_name = f"ssh-{service_name}"
            frp_success = self.frp_client.add_tcp_proxy(
                name=frp_proxy_name,
                local_ip=self.local_ip,
                local_port=src_ssh_port,
                remote_port=dst_ssh_port
            )

            if not frp_success:
                # FRP 代理添加失败，释放端口
                self.port_pool.release(service_name)
                return ServiceResponse(
                    success=False,
                    message=f"FRP 代理添加失败"
                )

            # 注册SSH服务
            success = self.ssh_register.register_service(
                service_name=service_name,
                container_name=service.container_name,
                src_ssh_port=src_ssh_port,
                dst_ssh_port=dst_ssh_port
            )

            if success:
                ssh_endpoint = f"{self.ssh_endpoint}:{dst_ssh_port}"
                logger.info(f"✅ SSH 服务注册成功: {service_name}:{src_ssh_port} -> {ssh_endpoint}")

                return ServiceResponse(
                    success=True,
                    message=f"SSH 服务注册成功",
                    data={
                        "ssh_endpoint": ssh_endpoint,
                        "service_name": service_name,
                        "container_name": service.container_name,
                        "ssh_port": dst_ssh_port
                    }
                )
            else:
                # 注册失败，清理 FRP 代理和释放端口
                self.frp_client.remove_proxy(frp_proxy_name)
                self.port_pool.release(service_name)
                return ServiceResponse(
                    success=False,
                    message=f"服务注册失败"
                )

        except Exception as e:
            logger.error(f"注册 SSH 服务失败 {service_name}: {e}")
            return ServiceResponse(
                success=False,
                message=f"注册服务时发生错误: {str(e)}"
            )

    def unregister_ssh_service(self, service_name: str) -> ServiceResponse:
        """
        删除 SSH 服务

        :param service_name: 服务名称
        :return: 服务响应
        """
        if not self._connected:
            if not self.connect():
                return ServiceResponse(
                    success=False,
                    message="无法连接到 etcd 服务"
                )

        try:
            # 检查SSH服务是否存在
            existing_service = self.ssh_register.get_service(service_name)
            if not existing_service:
                return ServiceResponse(
                    success=False,
                    message=f"服务 {service_name} 不存在"
                )

            # 从 etcd 删除SSH服务
            success = self.ssh_register.unregister_service(service_name)

            if success:
                # 删除对应的 FRP 代理
                frp_proxy_name = f"ssh-{service_name}"
                frp_success = self.frp_client.remove_proxy(frp_proxy_name)

                if not frp_success:
                    logger.warning(f"⚠️ FRP 代理删除失败: {frp_proxy_name}")
                else:
                    logger.info(f"✅ FRP 代理删除成功: {frp_proxy_name}")

                # 释放端口
                self.port_pool.release(service_name)
                logger.info(f"✅ SSH 服务删除成功: {service_name}")

                return ServiceResponse(
                    success=True,
                    message=f"SSH 服务删除成功",
                    data={"service_name": service_name}
                )
            else:
                return ServiceResponse(
                    success=False,
                    message=f"服务删除失败"
                )

        except Exception as e:
            logger.error(f"删除 SSH 服务失败 {service_name}: {e}")
            return ServiceResponse(
                success=False,
                message=f"删除服务时发生错误: {str(e)}"
            )
