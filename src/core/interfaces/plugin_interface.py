"""插件接口定义"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional

from .service_interface import ServiceInterface


class PluginStatus(Enum):
    """插件状态枚举"""
    UNLOADED = "unloaded"          # 未加载
    LOADING = "loading"            # 加载中
    LOADED = "loaded"              # 已加载
    INITIALIZING = "initializing"  # 初始化中
    ACTIVE = "active"              # 活跃状态
    STOPPING = "stopping"          # 停止中
    STOPPED = "stopped"            # 已停止
    ERROR = "error"                # 错误状态

class PluginPriority(Enum):
    """插件优先级"""
    CRITICAL = 1    # 关键插件
    HIGH = 2        # 高优先级
    NORMAL = 3      # 普通优先级
    LOW = 4         # 低优先级


class PluginInterface(ABC):
    """插件基础接口"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """获取插件版本"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    @abstractmethod
    def get_author(self) -> str:
        """获取插件作者"""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """获取插件依赖的服务或其他插件"""
        pass
    
    @abstractmethod
    def initialize(self, container: 'ServiceContainer') -> None:
        """初始化插件
        
        Args:
            container: 服务容器，用于获取依赖的服务
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理插件资源"""
        pass
    
    @abstractmethod
    def get_commands(self) -> Dict[str, Any]:
        """获取插件提供的命令
        
        Returns:
            Dict[str, Any]: 命令名称到命令类的映射
        """
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """检查插件是否启用"""
        pass
    
    def get_config_schema(self) -> Optional[Dict[str, Any]]:
        """获取插件配置模式（可选）
        
        Returns:
            Optional[Dict[str, Any]]: JSON Schema格式的配置模式
        """
        return None
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证插件配置（可选）
        
        Args:
            config: 插件配置
            
        Returns:
            bool: 配置是否有效
        """
        return True
    
    def get_plugin_priority(self) -> PluginPriority:
        """获取插件优先级
        
        Returns:
            PluginPriority: 插件优先级，影响加载顺序
        """
        return PluginPriority.NORMAL
    
    def get_plugin_status(self) -> PluginStatus:
        """获取插件状态
        
        Returns:
            PluginStatus: 当前插件状态
        """
        return PluginStatus.UNLOADED
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取插件健康状态
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        return {
            "status": "healthy",
            "message": "Plugin is running normally"
        }


class CommandPlugin(PluginInterface):
    """命令插件接口"""
    
    @abstractmethod
    def register_commands(self, command_registry: 'CommandRegistry') -> None:
        """注册插件命令
        
        Args:
            command_registry: 命令注册器
        """
        pass
    
    @abstractmethod
    def unregister_commands(self, command_registry: 'CommandRegistry') -> None:
        """注销插件命令
        
        Args:
            command_registry: 命令注册器
        """
        pass


class ServicePlugin(PluginInterface):
    """服务插件接口"""
    
    @abstractmethod
    def get_services(self) -> Dict[str, ServiceInterface]:
        """获取插件提供的服务
        
        Returns:
            Dict[str, ServiceInterface]: 服务名称到服务实例的映射
        """
        pass
    
    @abstractmethod
    def register_services(self, container: 'ServiceContainer') -> None:
        """注册插件服务
        
        Args:
            container: 服务容器
        """
        pass


class EventPlugin(PluginInterface):
    """事件插件接口"""
    
    @abstractmethod
    def register_event_handlers(self, event_bus: 'EventBus') -> None:
        """注册事件处理器
        
        Args:
            event_bus: 事件总线
        """
        pass
    
    @abstractmethod
    def unregister_event_handlers(self, event_bus: 'EventBus') -> None:
        """注销事件处理器
        
        Args:
            event_bus: 事件总线
        """
        pass


class ConfigurablePlugin(ABC):
    """可配置插件接口
    
    为需要配置管理的插件提供标准接口。
    """
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> bool:
        """配置插件
        
        Args:
            config: 配置字典
            
        Returns:
            bool: 配置是否成功
        """
        pass
    
    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """获取当前配置
        
        Returns:
            Dict[str, Any]: 当前配置字典
        """
        pass
    
    def update_configuration(self, config: Dict[str, Any]) -> bool:
        """更新配置
        
        Args:
            config: 新的配置字典
            
        Returns:
            bool: 更新是否成功
        """
        current_config = self.get_configuration()
        current_config.update(config)
        return self.configure(current_config)

class LifecyclePlugin(ABC):
    """生命周期插件接口
    
    为需要生命周期管理的插件提供标准接口。
    """
    
    @abstractmethod
    def start(self) -> bool:
        """启动插件
        
        Returns:
            bool: 启动是否成功
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """停止插件
        
        Returns:
            bool: 停止是否成功
        """
        pass
    
    @abstractmethod
    def restart(self) -> bool:
        """重启插件
        
        Returns:
            bool: 重启是否成功
        """
        pass
    
    def is_running(self) -> bool:
        """检查插件是否正在运行
        
        Returns:
            bool: 插件是否正在运行
        """
        return self.get_plugin_status() == PluginStatus.ACTIVE

class PluginMetadata:
    """插件元数据"""
    
    def __init__(self, name: str, version: str, description: str, 
                 author: str, dependencies: List[str] = None,
                 enabled: bool = True, config: Dict[str, Any] = None,
                 priority: PluginPriority = PluginPriority.NORMAL,
                 entry_point: str = "plugin.py",
                 class_name: str = "Plugin"):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.dependencies = dependencies or []
        self.enabled = enabled
        self.config = config or {}
        self.priority = priority
        self.entry_point = entry_point
        self.class_name = class_name
        self.status = PluginStatus.UNLOADED
        self.load_time: Optional[float] = None
        self.error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'dependencies': self.dependencies,
            'enabled': self.enabled,
            'config': self.config,
            'priority': self.priority.value,
            'entry_point': self.entry_point,
            'class_name': self.class_name,
            'status': self.status.value,
            'load_time': self.load_time,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """从字典创建"""
        metadata = cls(
            name=data['name'],
            version=data['version'],
            description=data['description'],
            author=data['author'],
            dependencies=data.get('dependencies', []),
            enabled=data.get('enabled', True),
            config=data.get('config', {}),
            priority=PluginPriority(data.get('priority', PluginPriority.NORMAL.value)),
            entry_point=data.get('entry_point', 'plugin.py'),
            class_name=data.get('class_name', 'Plugin')
        )
        
        if 'status' in data:
            metadata.status = PluginStatus(data['status'])
        if 'load_time' in data:
            metadata.load_time = data['load_time']
        if 'error_message' in data:
            metadata.error_message = data['error_message']
            
        return metadata

# 插件异常类
class PluginException(Exception):
    """插件异常基类"""
    pass

class PluginLoadError(PluginException):
    """插件加载错误"""
    pass

class PluginInitializationError(PluginException):
    """插件初始化错误"""
    pass

class PluginConfigurationError(PluginException):
    """插件配置错误"""
    pass

class PluginDependencyError(PluginException):
    """插件依赖错误"""
    pass