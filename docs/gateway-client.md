# Gateway Client 设计文档

## 概述

Gateway Client 是一个基于 FastAPI 的网关客户端服务，提供 HTTP 和 SSH 服务的动态注册与管理功能。通过与 etcd、Kong、FRP 等组件集成，实现服务的自动发现、代理配置和访问控制。

## 核心功能

### 1. HTTP 服务管理
- 自动发现容器化服务的 HTTP 端口 (80/tcp)
- 通过 Kong 配置 HTTP 反向代理
- 生成子域名访问地址 (`{service-name}.{http-endpoint}`)

### 2. SSH 服务管理
- 自动发现容器化服务的 SSH 端口 (22/tcp)
- 通过 FRP 配置 TCP 端口转发
- 动态分配外部访问端口 (40000-40099)

## API 接口

> **详细 API 接口文档请参见 [gateway-apis.md](gateway-apis.md)。**

## 数据模型

### ServiceResponse

通用 API 响应模型：

```python
class ServiceResponse(BaseModel):
    success: bool           # 操作是否成功
    message: str           # 响应消息
    data: Optional[Dict[str, Any]] = None  # 响应数据
```

### HttpServiceInfo

HTTP 服务信息模型：

```python
@dataclass
class HttpServiceInfo:
    service_name: str      # 服务名称
    container_name: str    # 容器名称
    http_port: int        # HTTP 端口
    http_endpoint: str    # HTTP 访问端点
    create_time: str      # 创建时间
    version: int = 1      # 版本号
```

### SshServiceInfo

SSH 服务信息模型：

```python
@dataclass
class SshServiceInfo:
    service_name: str     # 服务名称
    container_name: str   # 容器名称
    ssh_port: int        # SSH 端口
    ssh_endpoint: str    # SSH 访问端点
    create_time: str     # 创建时间
    version: int = 1     # 版本号
```

## 配置参数

### 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `LOCAL_IP` | `127.0.0.1` | 本地 IP 地址 |
| `ETCD_HOST` | `localhost` | etcd 服务器地址 |
| `ETCD_PORT` | `2379` | etcd 服务器端口 |
| `SSH_PORT_START` | `40000` | SSH 端口池起始端口 |
| `SSH_PORT_END` | `40099` | SSH 端口池结束端口 |
| `HTTP_ENDPOINT` | `example.com` | HTTP 访问端点域名 |
| `SSH_ENDPOINT` | `connect.example.com` | SSH 访问端点域名 |
| `FRP_HOST` | `localhost` | FRP 客户端地址 |
| `FRP_PORT` | `7400` | FRP 客户端端口 |
| `FRP_USERNAME` | `admin` | FRP 控制台用户名 |
| `FRP_PASSWORD` | `123456` | FRP 控制台密码 |
| `KONG_ADMIN_URL` | `http://127.0.0.1:8001` | Kong Admin API 地址 |
| `ENABLE_CORS` | `0` | 是否启用 CORS |

## 工作流程

### HTTP 服务注册流程

1. 从 etcd 服务发现获取容器服务信息
2. 检查服务是否已经注册
3. 提取容器的 HTTP 端口 (80/tcp)
4. 在 Kong 中创建反向代理规则
5. 将服务信息注册到 etcd
6. 返回生成的访问地址

### SSH 服务注册流程

1. 从 etcd 服务发现获取容器服务信息
2. 检查服务是否已经注册
3. 提取容器的 SSH 端口 (22/tcp)
4. 从端口池分配外部访问端口
5. 在 FRP 中创建 TCP 转发规则
6. 将服务信息注册到 etcd
7. 返回生成的访问地址

## 依赖服务

- **etcd**: 服务发现和注册信息存储
- **Kong**: HTTP 反向代理和 API 网关
- **FRP**: TCP 端口转发和内网穿透
- **Docker**: 容器化服务运行环境

## 启动方式

```bash
# 复制 .env.example 并对 .env 进行修改
cp .env.example .env

# Docker 容器运行
docker-compose up -d
```
