"""服务容器单例模块

提供全局唯一的服务容器实例，避免重复初始化。
"""

from typing import Optional

from utils.logger import logger
from .config import ConfigLoader, EnvironmentManager
from .container import ServiceContainer


class ServiceContainerSingleton:
    """服务容器单例

    确保整个应用只有一个服务容器实例，避免重复初始化带来的性能损耗。
    """

    _instance: Optional[ServiceContainer] = None
    _initialized: bool = False

    @classmethod
    def get_instance(
        cls,
        config_loader: Optional[ConfigLoader] = None,
        environment_manager: Optional[EnvironmentManager] = None,
        force_recreate: bool = False,
    ) -> ServiceContainer:
        """获取服务容器单例实例

        Args:
            config_loader: 配置加载器（仅在首次创建时使用）
            environment_manager: 环境管理器（仅在首次创建时使用）
            force_recreate: 是否强制重新创建实例

        Returns:
            ServiceContainer: 服务容器实例
        """
        if cls._instance is None or force_recreate:
            if force_recreate and cls._instance is not None:
                logger.info("强制重新创建服务容器实例")
            else:
                logger.info("首次创建服务容器单例实例")

            cls._instance = ServiceContainer(
                config_loader=config_loader, environment_manager=environment_manager
            )
            cls._initialized = True
            logger.info("服务容器单例已初始化")
        else:
            logger.debug("复用现有服务容器实例")

        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置单例实例（主要用于测试）"""
        if cls._instance is not None:
            logger.info("重置服务容器单例")
            cls._instance = None
            cls._initialized = False

    @classmethod
    def is_initialized(cls) -> bool:
        """检查是否已初始化"""
        return cls._initialized and cls._instance is not None
