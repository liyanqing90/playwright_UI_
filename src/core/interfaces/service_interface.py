"""服务接口定义"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class ServiceInterface(ABC):
    """服务基础接口"""
    
    @abstractmethod
    def initialize(self) -> None:
        """初始化服务"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理服务资源"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取服务名称"""
        pass
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """检查服务是否已初始化"""
        pass


class ConfigurableService(ServiceInterface):
    """可配置服务接口"""
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """配置服务"""
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """获取服务配置"""
        pass


class LifecycleService(ServiceInterface):
    """生命周期服务接口"""
    
    @abstractmethod
    def start(self) -> None:
        """启动服务"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """停止服务"""
        pass
    
    @abstractmethod
    def restart(self) -> None:
        """重启服务"""
        pass
    
    @abstractmethod
    def get_status(self) -> str:
        """获取服务状态"""
        pass