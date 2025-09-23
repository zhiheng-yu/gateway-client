import base64
import requests
import logging
from typing import Dict, Optional
from dataclasses import dataclass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class FrpProxy:
    """FRP 代理配置"""
    name: str
    type: str = "tcp"
    local_ip: str = "127.0.0.1"
    local_port: int = 22
    remote_port: int = 0

    def to_config_section(self) -> str:
        """转换为 FRP 配置段"""
        config = f"\n[[proxies]]\n"
        config += f"name = \"{self.name}\"\n"
        config += f"type = \"{self.type}\"\n"
        config += f"localIP = \"{self.local_ip}\"\n"
        config += f"localPort = {self.local_port}\n"
        config += f"remotePort = {self.remote_port}\n"
        return config


class FrpClient:
    """FRP 客户端 API 管理类"""

    def __init__(self,
                 frp_host: str = "localhost",
                 frp_port: int = 7400,
                 username: str = "admin",
                 password: str = "123456"):
        """
        初始化 FRP 客户端

        :param frp_host: FRP 客户端 Web 控制台地址
        :param frp_port: FRP 客户端 Web 控制台端口
        :param username: 控制台用户名
        :param password: 控制台密码
        """
        self.frp_host = frp_host
        self.frp_port = frp_port
        self.username = username
        self.password = password

        # 构建基础 URL 和认证头
        self.base_url = f"http://{frp_host}:{frp_port}/api"
        self.auth_header = self._create_auth_header()

        # 存储当前代理配置
        self.proxies: Dict[str, FrpProxy] = {}

    def _create_auth_header(self) -> str:
        """创建 Basic Auth 认证头"""
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"

    def _remove_proxy_sections(self, config: str) -> str:
        """截取第一个 [[proxies]] 之前的所有信息"""
        lines = config.split('\n')
        result_lines = []

        for line in lines:
            stripped_line = line.strip()

            # 检测到第一个 [[proxies]] 段落就停止
            if stripped_line.startswith('[[proxies]]'):
                break

            # 保留这一行
            result_lines.append(line)

        # 确保配置以换行符结尾
        config_without_proxies = '\n'.join(result_lines).rstrip()
        if config_without_proxies and not config_without_proxies.endswith('\n'):
            config_without_proxies += '\n'

        return config_without_proxies

    def _make_request(self, method: str, endpoint: str, data: str = None) -> requests.Response:
        """发送 HTTP 请求"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': self.auth_header
        }

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, data=data, timeout=10)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            logger.debug(f"{method} {url} -> {response.status_code}")
            return response

        except requests.RequestException as e:
            logger.error(f"请求失败 {method} {url}: {e}")
            raise

    def get_config(self) -> Optional[str]:
        """获取当前 FRP 配置"""
        try:
            response = self._make_request('GET', '/config')
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"获取配置失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"获取配置异常: {e}")
            return None

    def put_config(self, config: str) -> bool:
        """更新 FRP 配置"""
        try:
            response = self._make_request('PUT', '/config', data=config)
            if response.status_code == 200:
                logger.debug("成功更新 FRP 配置")
                return True
            else:
                logger.error(f"更新配置失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"更新配置异常: {e}")
            return False

    def reload_config(self) -> bool:
        """重载 FRP 配置"""
        try:
            response = self._make_request('GET', '/reload')
            if response.status_code == 200:
                logger.debug("成功重载 FRP 配置")
                return True
            else:
                logger.error(f"重载配置失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"重载配置异常: {e}")
            return False

    def deploy_proxies(self) -> bool:
        """部署代理配置（更新配置并重载）"""
        try:
            # 1. 获取当前配置作为基础
            current_config = self.get_config()
            if current_config is None:
                logger.error("无法获取当前配置")
                return False

            # 2. 移除现有的 [[proxies]] 段落，保留基础配置
            base_config = self._remove_proxy_sections(current_config)

            # 3. 添加所有代理配置
            for proxy in self.proxies.values():
                base_config += proxy.to_config_section()

            # 4. 更新配置
            if not self.put_config(base_config):
                return False

            # 5. 重载配置
            if not self.reload_config():
                return False

            logger.debug("✅ FRP 代理配置部署成功")
            return True

        except Exception as e:
            logger.error(f"部署代理配置失败: {e}")
            return False

    def add_tcp_proxy(self, name: str, local_ip: str, local_port: int, remote_port: int) -> bool:
        """
        添加 TCP 代理并立即部署

        :param name: 代理名称
        :param local_ip: 本地 IP 地址
        :param local_port: 本地端口
        :param remote_port: 远程端口
        :return: 是否成功
        """
        proxy = FrpProxy(
            name=name,
            type="tcp",
            local_ip=local_ip,
            local_port=local_port,
            remote_port=remote_port
        )

        self.proxies[name] = proxy
        logger.info(f"添加 TCP 代理: {name} ({local_ip}:{local_port} -> :{remote_port})")
        return self.deploy_proxies()

    def remove_proxy(self, name: str) -> bool:
        """
        移除代理并立即部署

        :param name: 代理名称
        :return: 是否成功
        """
        if name in self.proxies:
            self.proxies.pop(name)
            logger.info(f"移除代理: {name}")
            return self.deploy_proxies()
        else:
            logger.warning(f"代理不存在: {name}")
            return False

    def list_proxies(self) -> Dict[str, FrpProxy]:
        """列出所有代理"""
        return self.proxies.copy()

    def print_proxies(self):
        """打印当前所有代理"""
        if not self.proxies:
            print("📭 当前没有代理配置")
            return

        print(f"\n📊 当前代理配置 ({len(self.proxies)} 个):")
        print("-" * 50)
        for name, proxy in self.proxies.items():
            print(f"🔒 {name}: {proxy.local_ip}:{proxy.local_port} -> :{proxy.remote_port}")
        print("-" * 50)
