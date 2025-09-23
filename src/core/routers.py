from fastapi import FastAPI, Path
from fastapi.middleware.cors import CORSMiddleware
from core.apis import GatewayClient, ServiceResponse
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 创建全局的网关客户端实例
gateway_client = GatewayClient(
    local_ip=os.getenv('LOCAL_IP', '127.0.0.1'),
    etcd_host=os.getenv('ETCD_HOST', 'localhost'),
    etcd_port=int(os.getenv('ETCD_PORT', '2379')),
    ssh_port_start=int(os.getenv('SSH_PORT_START', '40000')),
    ssh_port_end=int(os.getenv('SSH_PORT_END', '40099')),
    http_endpoint=os.getenv('HTTP_ENDPOINT', 'example.com'),
    ssh_endpoint=os.getenv('SSH_ENDPOINT', 'connect.example.com'),
    frp_host=os.getenv('FRP_HOST', 'localhost'),
    frp_port=int(os.getenv('FRP_PORT', '7400')),
    frp_username=os.getenv('FRP_USERNAME', 'admin'),
    frp_password=os.getenv('FRP_PASSWORD', '123456'),
    kong_admin_url=os.getenv('KONG_ADMIN_URL', 'http://127.0.0.1:8001')
)


# 创建 FastAPI 应用
app = FastAPI(
    title="Gateway Client API",
    description="网关客户端 API 服务",
    version="1.0.0"
)

# Add CORS middleware
if os.getenv("ENABLE_CORS", "0") == "1":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def startup_event():
    """应用启动时连接服务"""
    logger.info("🚀 启动网关客户端 API 服务...")
    if not gateway_client.connect():
        logger.error("❌ 服务连接失败")
    else:
        logger.info("✅ 网关客户端 API 服务已启动")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时断开连接"""
    logger.info("👋 关闭网关客户端 API 服务...")
    gateway_client.disconnect()


@app.get("/api/v1/gateway/http/{service_name}")
async def register_http_service(
    service_name: str = Path(..., description="服务名称")
) -> ServiceResponse:
    """
    注册 HTTP 服务并返回 HTTP 访问地址
    """
    logger.info(f"📝 请求注册 HTTP 服务: {service_name}")
    return gateway_client.register_http_service(service_name)


@app.delete("/api/v1/gateway/http/{service_name}")
async def unregister_http_service(
    service_name: str = Path(..., description="服务名称")
) -> ServiceResponse:
    """
    删除 HTTP 服务
    """
    logger.info(f"🗑️ 请求删除 HTTP 服务: {service_name}")
    return gateway_client.unregister_http_service(service_name)


@app.get("/api/v1/gateway/ssh/{service_name}")
async def register_ssh_service(
    service_name: str = Path(..., description="服务名称")
) -> ServiceResponse:
    """
    注册 SSH 服务并返回 SSH 访问地址
    """
    logger.info(f"📝 请求注册 SSH 服务: {service_name}")
    return gateway_client.register_ssh_service(service_name)


@app.delete("/api/v1/gateway/ssh/{service_name}")
async def unregister_ssh_service(
    service_name: str = Path(..., description="服务名称")
) -> ServiceResponse:
    """
    删除 SSH 服务
    """
    logger.info(f"🗑️ 请求删除 SSH 服务: {service_name}")
    return gateway_client.unregister_ssh_service(service_name)


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "gateway-client-api"}


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Gateway Client API",
        "version": "1.0.0",
        "endpoints": [
            "GET /api/v1/gateway/http/{service-name} - 注册HTTP服务",
            "DELETE /api/v1/gateway/http/{service-name} - 删除HTTP服务",
            "GET /api/v1/gateway/ssh/{service-name} - 注册SSH服务",
            "DELETE /api/v1/gateway/ssh/{service-name} - 删除SSH服务"
        ]
    }
