"""基础服务类

所有服务的基类，提供通用功能。
"""

from abc import ABC
from typing import Optional, Dict, Any

from playwright.sync_api import Page

from utils.logger import logger
from ..interfaces.service_interface import ConfigurableService


class BaseService(ConfigurableService, ABC):
    """所有服务的基类
    
    提供通用的服务功能，如日志记录、错误处理等。
    实现ServiceInterface和ConfigurableService接口。
    """
    
    def __init__(self, performance_manager=None):
        """初始化基础服务
        
        Args:
            performance_manager: 性能管理器实例（可选）
        """
        self.performance_manager = performance_manager
        self._service_name = self.__class__.__name__
        self._initialized = False
        self._config: Dict[str, Any] = {}
        logger.debug(f"创建服务: {self._service_name}")
    
    def get_name(self) -> str:
        """获取服务名称"""
        return self._service_name
    
    def initialize(self) -> None:
        """初始化服务"""
        if not self._initialized:
            self._do_initialize()
            self._initialized = True
            logger.debug(f"初始化服务: {self._service_name}")
    
    def cleanup(self) -> None:
        """清理服务资源"""
        if self._initialized:
            self._do_cleanup()
            self._initialized = False
            logger.debug(f"清理服务: {self._service_name}")
    
    def is_initialized(self) -> bool:
        """检查服务是否已初始化"""
        return self._initialized
    
    def configure(self, config: Dict[str, Any]) -> None:
        """配置服务"""
        self._config.update(config)
        logger.debug(f"配置服务 {self._service_name}: {config}")
    
    def get_configuration(self) -> Dict[str, Any]:
        """获取服务配置"""
        return self._config.copy()
    
    def get_config(self) -> Dict[str, Any]:
        """获取服务配置（接口实现）"""
        return self.get_configuration()
    
    def _do_initialize(self) -> None:
        """子类可重写的初始化方法"""
        pass
    
    def _do_cleanup(self) -> None:
        """子类可重写的清理方法"""
        pass
    
    def _record_operation(self, operation: str, duration: float = 0.0, success: bool = True):
        """记录操作性能
        
        Args:
            operation: 操作名称
            duration: 操作耗时（秒）
            success: 操作是否成功
        """
        if self.performance_manager:
            try:
                self.performance_manager.record_operation(
                    duration * 1000,  # 转换为毫秒
                    f"{self._service_name}.{operation}"
                )
            except Exception as e:
                logger.warning(f"记录性能数据失败: {e}")
    
    def _log_operation(self, operation: str, details: str = ""):
        """记录操作日志
        
        Args:
            operation: 操作名称
            details: 操作详情
        """
        log_msg = f"{self._service_name}.{operation}"
        if details:
            log_msg += f": {details}"
        logger.debug(log_msg)
    
    def _get_locator(self, page: Page, selector: str, timeout: Optional[int] = None):
        """获取元素定位器
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            Locator: Playwright定位器对象
        """
        locator = page.locator(selector)
        if timeout:
            locator = locator.first
        return locator