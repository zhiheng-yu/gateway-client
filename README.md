# Gateway Client

一个基于 FastAPI 的网关客户端服务，提供容器化服务的 HTTP 和 SSH 访问代理管理。

## 功能特性

- 🌐 **HTTP 服务代理**: 通过 Kong 自动配置 HTTP 反向代理，支持子域名访问
- 🔒 **SSH 服务转发**: 通过 FRP 配置 TCP 端口转发，提供安全的 SSH 访问
- 🔍 **服务发现**: 基于 etcd 的自动服务发现和注册
- 📊 **动态端口管理**: 智能端口池分配和释放
- 🚀 **RESTful API**: 简洁的 REST API 接口，易于集成

## 核心组件

- **FastAPI**: Web 框架和 API 服务
- **etcd**: 服务发现和配置存储
- **Kong**: HTTP 反向代理和 API 网关
- **FRP**: TCP 端口转发和内网穿透
- **Docker**: 容器化部署

## 快速开始

### 环境要求

- Python 3.8+
- Docker & Docker Compose
- etcd 服务
- Kong 网关
- FRP 服务

### 安装部署

1. **克隆项目**
   ```bash
   git clone https://github.com/zhiheng-yu/gateway-client.git
   cd gateway-client
   git checkout dev-python
   ```

2. **环境配置**
   ```bash
   # 复制环境变量模板
   cp .env.example .env
   # 根据实际环境修改配置
   vim .env
   ```

3. **Docker 部署**
   ```bash
   # 启动所有服务
   docker-compose up -d
   ```

4. **本地开发**
   ```bash
   # 安装依赖
   pip install -r requirements.txt
   # 启动服务
   python src/start_api.py
   ```

## 配置说明

主要环境变量：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ETCD_HOST` | `localhost` | etcd 服务地址 |
| `HTTP_ENDPOINT` | `example.com` | HTTP 访问域名 |
| `SSH_ENDPOINT` | `connect.example.com` | SSH 访问域名 |
| `KONG_ADMIN_URL` | `http://127.0.0.1:8001` | Kong 管理 API |
| `SSH_PORT_START` | `40000` | SSH 端口池起始 |
| `SSH_PORT_END` | `40099` | SSH 端口池结束 |

## 项目结构

```
gateway-client/
├── src/
│   ├── core/           # 核心模块
│   ├── services/       # 服务注册模块
│   ├── proxies/        # 代理客户端
│   └── utils/          # 工具模块
├── docs/               # 文档
├── docker-compose.yml  # Docker 编排
└── README.md           # 项目说明
```

## 开发指南

### 本地开发环境

1. 启动依赖服务（etcd、Kong、FRP）
2. 设置环境变量
3. 运行 `python src/start_api.py`
4. 访问 `http://localhost:2381`

### 文档

- Swagger UI: `http://localhost:2381/docs`
- ReDoc: `http://localhost:2381/redoc`
- 详细设计文档: [Gateway Client 设计文档](docs/gateway-client.md)

## 🙏 特别鸣谢

> [!TIP]
> 排名不分先后

* [XShengTech/gpu-docker-api](https://github.com/XShengTech/gpu-docker-api): 提供容器操作代码和思路
* [Kong/kong](https://github.com/Kong/kong): 提供 HTTP 代理
* [fatedier/frp](https://github.com/fatedier/frp): 提供 SSH 隧道代理
