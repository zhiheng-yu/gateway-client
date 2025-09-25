from collections import deque


class PortPool:
    def __init__(self, exposed_start: int, exposed_end: int):
        """
        初始化端口池
        :param exposed_start: 暴露端口起始
        :param exposed_end: 暴露端口结束（包含）
        """
        self.free_ports = deque(range(exposed_start, exposed_end + 1))
        self.mapping = {}           # real_port -> exposed_port
        self.reverse_mapping = {}   # exposed_port -> real_port

    def assign(self, service_name: str) -> int:
        """
        为真实端口分配一个暴露端口
        :param service_name: 服务名
        :return: 暴露端口，如果池满则抛出异常
        """
        if service_name in self.mapping:
            return self.mapping[service_name]  # 已经分配过

        if not self.free_ports:
            raise RuntimeError("No free exposed ports available")

        exposed_port = self.free_ports.popleft()
        self.mapping[service_name] = exposed_port
        self.reverse_mapping[exposed_port] = service_name
        return exposed_port

    def release(self, service_name: str):
        """
        释放真实端口对应的暴露端口
        :param service_name: 服务名
        """
        if service_name not in self.mapping:
            return

        exposed_port = self.mapping.pop(service_name)
        self.reverse_mapping.pop(exposed_port, None)
        self.free_ports.append(exposed_port)

    def lookup_exposed(self, service_name: str) -> int | None:
        """
        根据真实端口查询暴露端口
        """
        return self.mapping.get(service_name)

    def lookup_real(self, exposed_port: int) -> int | None:
        """
        根据暴露端口查询真实端口
        """
        return self.reverse_mapping.get(exposed_port)

    def __repr__(self):
        return f"<PortPool mappings={self.mapping}>"
