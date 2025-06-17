"""核心服务注册表

定义核心服务的注册信息和依赖关系。
这些服务是框架的基础设施，提供稳定、高频使用的功能。
"""

from typing import Dict, Any, List

from utils.logger import logger
from .assertion_service import AssertionService
from .element_service import ElementService
from .navigation_service import NavigationService
from .variable_service import VariableService
from .wait_service import WaitService
from ..container import ServiceContainer


class CoreServiceRegistry:
    """核心服务注册表

    负责注册框架的核心服务，确保服务的正确初始化和依赖注入。
    """

    @staticmethod
    def register_core_services(container: ServiceContainer) -> None:
        """注册所有核心服务

        Args:
            container: 服务容器实例
        """
        logger.info("开始注册核心服务")

        # 注册基础服务（无依赖）
        container.register_implementation(
            VariableService, VariableService, singleton=True
        )

        # 注册元素服务（依赖变量服务）
        container.register_factory(
            ElementService,
            lambda: ElementService(
                performance_manager=None,  # 性能管理器将通过插件提供
                variable_manager=(
                    container.resolve(VariableService)
                    if container.is_registered(VariableService)
                    else None
                ),
            ),
            singleton=True,
        )

        # 注册导航服务
        container.register_implementation(
            NavigationService, NavigationService, singleton=True
        )

        # 注册等待服务
        container.register_implementation(WaitService, WaitService, singleton=True)

        # 注册断言服务
        container.register_implementation(
            AssertionService, AssertionService, singleton=True
        )

        logger.info("核心服务注册完成")

    @staticmethod
    def get_service_dependencies() -> Dict[str, List[str]]:
        """获取服务依赖关系图

        Returns:
            Dict[str, List[str]]: 服务依赖关系映射
        """
        return {
            "VariableService": [],
            "ElementService": ["VariableService"],
            "NavigationService": [],
            "WaitService": [],
            "AssertionService": [],
        }

    @staticmethod
    def get_service_configs() -> Dict[str, Dict[str, Any]]:
        """获取服务默认配置

        Returns:
            Dict[str, Dict[str, Any]]: 服务配置映射
        """
        return {
            "ElementService": {
                "default_timeout": 30000,
                "retry_count": 3,
                "force_click": True,
            },
            "NavigationService": {
                "default_timeout": 30000,
                "wait_until": "networkidle",
            },
            "WaitService": {"default_timeout": 30000, "polling_interval": 100},
            "AssertionService": {"strict_mode": True, "timeout": 5000},
            "VariableService": {"auto_save": True, "case_sensitive": False},
        }

    @staticmethod
    def validate_service_health(container: ServiceContainer) -> Dict[str, bool]:
        """验证核心服务健康状态

        Args:
            container: 服务容器实例

        Returns:
            Dict[str, bool]: 服务健康状态映射
        """
        health_status = {}
        core_services = [
            ElementService,
            NavigationService,
            WaitService,
            AssertionService,
            VariableService,
        ]

        for service_class in core_services:
            service_name = service_class.__name__
            try:
                if container.is_registered(service_class):
                    service_instance = container.resolve(service_class)
                    health_status[service_name] = service_instance.is_initialized()
                else:
                    health_status[service_name] = False
            except Exception as e:
                logger.error(f"检查服务 {service_name} 健康状态失败: {e}")
                health_status[service_name] = False

        return health_status
