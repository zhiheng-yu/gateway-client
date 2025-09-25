"""
Gateway Client API 启动脚本
使用 Uvicorn 启动 FastAPI 应用
"""

import uvicorn
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """启动 FastAPI 应用"""
    logger.info("🚀 启动 Gateway Client API 服务...")

    # 使用 uvicorn 启动 FastAPI 应用
    uvicorn.run(
        "core.routers:app",
        host="0.0.0.0",
        port=2381,
        reload=False,  # 开发模式下自动重载
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
