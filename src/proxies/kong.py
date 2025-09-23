import requests
import logging
from typing import Optional, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KongProxy:
    """Kong 代理管理类，提供添加和删除 HTTP 代理的功能"""

    def __init__(self, kong_admin_url: str = "http://127.0.0.1:8001"):
        """
        初始化 Kong 代理管理器

        Args:
            kong_admin_url: Kong Admin API 的基础 URL
        """
        self.kong_admin_url = kong_admin_url.rstrip('/')
        self.session = requests.Session()

    def add_http_proxy(self, name: str, host: str, port: int, domain: str, protocol: str = "http") -> bool:
        """
        添加 HTTP 代理

        Args:
            name: 服务和路由的名称
            host: 目标服务的主机地址
            port: 目标服务的端口
            domain: 路由的域名
            protocol: 协议类型，默认为 http

        Returns:
            bool: 操作是否成功
        """
        try:
            # 第一步：添加服务
            service_success = self._add_service(name, protocol, host, port)
            if not service_success:
                logger.error(f"添加服务 {name} 失败")
                return False

            # 第二步：添加路由
            route_success = self._add_route(name, domain)
            if not route_success:
                logger.error(f"添加路由 {name} 失败，开始清理服务")
                # 如果路由添加失败，清理已创建的服务
                self._delete_service(name)
                return False

            logger.info(f"成功添加 HTTP 代理: {name} -> {host}:{port} (域名: {domain})")
            return True

        except Exception as e:
            logger.error(f"添加 HTTP 代理时发生异常: {e}")
            return False

    def delete_http_proxy(self, name: str) -> bool:
        """
        删除 HTTP 代理

        Args:
            name: 要删除的服务和路由名称

        Returns:
            bool: 操作是否成功
        """
        try:
            # 第一步：删除路由
            route_success = self._delete_route(name)
            if not route_success:
                logger.warning(f"删除路由 {name} 失败或路由不存在")

            # 第二步：删除服务
            service_success = self._delete_service(name)
            if not service_success:
                logger.warning(f"删除服务 {name} 失败或服务不存在")

            # 只要有一个操作成功就认为删除操作有效
            if route_success or service_success:
                logger.info(f"成功删除 HTTP 代理: {name}")
                return True
            else:
                logger.error(f"删除 HTTP 代理 {name} 完全失败")
                return False

        except Exception as e:
            logger.error(f"删除 HTTP 代理时发生异常: {e}")
            return False

    def _add_service(self, name: str, protocol: str, host: str, port: int) -> bool:
        """添加服务"""
        url = f"{self.kong_admin_url}/services"
        data = {
            'name': f"http-{name}",
            'protocol': protocol,
            'host': host,
            'port': str(port)
        }

        try:
            response = self.session.post(url, data=data)
            if response.status_code == 201:
                logger.info(f"服务 http-{name} 添加成功")
                return True
            else:
                logger.error(f"添加服务失败: {response.status_code} - {response.text}")
                return False
        except requests.RequestException as e:
            logger.error(f"添加服务时网络请求失败: {e}")
            return False

    def _add_route(self, name: str, domain: str) -> bool:
        """添加路由"""
        url = f"{self.kong_admin_url}/services/http-{name}/routes"
        data = {
            'name': f"http-{name}",
            'protocols[]': 'http',
            'hosts[]': domain
        }

        try:
            response = self.session.post(url, data=data)
            if response.status_code == 201:
                logger.info(f"路由 http-{name} 添加成功")
                return True
            else:
                logger.error(f"添加路由失败: {response.status_code} - {response.text}")
                return False
        except requests.RequestException as e:
            logger.error(f"添加路由时网络请求失败: {e}")
            return False

    def _delete_route(self, name: str) -> bool:
        """删除路由"""
        url = f"{self.kong_admin_url}/routes/http-{name}"

        try:
            response = self.session.delete(url)
            if response.status_code == 204:
                logger.info(f"路由 http-{name} 删除成功")
                return True
            elif response.status_code == 404:
                logger.warning(f"路由 http-{name} 不存在")
                return False
            else:
                logger.error(f"删除路由失败: {response.status_code} - {response.text}")
                return False
        except requests.RequestException as e:
            logger.error(f"删除路由时网络请求失败: {e}")
            return False

    def _delete_service(self, name: str) -> bool:
        """删除服务"""
        url = f"{self.kong_admin_url}/services/http-{name}"

        try:
            response = self.session.delete(url)
            if response.status_code == 204:
                logger.info(f"服务 http-{name} 删除成功")
                return True
            elif response.status_code == 404:
                logger.warning(f"服务 http-{name} 不存在")
                return False
            else:
                logger.error(f"删除服务失败: {response.status_code} - {response.text}")
                return False
        except requests.RequestException as e:
            logger.error(f"删除服务时网络请求失败: {e}")
            return False

    def get_service_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取服务信息

        Args:
            name: 服务名称

        Returns:
            Dict: 服务信息，如果服务不存在返回 None
        """
        url = f"{self.kong_admin_url}/services/http-{name}"

        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"服务 http-{name} 不存在")
                return None
            else:
                logger.error(f"获取服务信息失败: {response.status_code} - {response.text}")
                return None
        except requests.RequestException as e:
            logger.error(f"获取服务信息时网络请求失败: {e}")
            return None

    def get_route_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取路由信息

        Args:
            name: 路由名称

        Returns:
            Dict: 路由信息，如果路由不存在返回 None
        """
        url = f"{self.kong_admin_url}/routes/http-{name}"

        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"路由 http-{name} 不存在")
                return None
            else:
                logger.error(f"获取路由信息失败: {response.status_code} - {response.text}")
                return None
        except requests.RequestException as e:
            logger.error(f"获取路由信息时网络请求失败: {e}")
            return None
