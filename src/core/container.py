# -*- coding: utf-8 -*-
"""
服务容器

实现依赖注入容器，管理服务的注册、解析和生命周期。
支持配置驱动的服务管理和自动装配。
"""

import importlib
import inspect
from enum import Enum
from typing import Type, TypeVar, Dict, Any, Callable, Optional, Union, List

from utils.logger import logger
from .config import ConfigLoader, ServiceConfig, EnvironmentManager
from .interfaces.service_interface import ServiceInterface, ConfigurableService, LifecycleService

T = TypeVar('T')
ServiceFactory = Callable[[], T]
ServiceInstance = Union[T, ServiceFactory[T]]

class ServiceScope(Enum):
    """服务作用域"""
    SINGLETON = "singleton"  # 单例
    TRANSIENT = "transient"  # 瞬态
    SCOPED = "scoped"        # 作用域

class ServiceContainer:
    """服务容器
    
    负责管理服务的注册、解析和生命周期。
    支持配置驱动的服务管理和自动装配。
    """
    
    def __init__(self, config_loader: Optional[ConfigLoader] = None, environment_manager: Optional[EnvironmentManager] = None):
        """初始化服务容器
        
        Args:
            config_loader: 配置加载器
            environment_manager: 环境管理器
        """
        self._services: Dict[str, Dict[str, Any]] = {}
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._service_configs: Dict[str, ServiceConfig] = {}
        self._dependency_graph: Dict[str, List[str]] = {}
        
        # 配置管理
        self._config_loader = config_loader or ConfigLoader()
        self._environment_manager = environment_manager or EnvironmentManager()
        
        # 自动装配设置
        global_config = self._config_loader.get_global_config()
        self._auto_wire = global_config.container.get('auto_wire', True)
        self._lazy_loading = global_config.container.get('lazy_loading', True)
        self._circular_dependency_detection = global_config.container.get('circular_dependency_detection', True)
        
        logger.debug("服务容器已初始化")
        
        # 如果启用自动装配，则加载配置中的服务
        if self._auto_wire:
            self._auto_register_services()
    
    def _auto_register_services(self) -> None:
        """自动注册配置中的服务"""
        try:
            services = self._config_loader.get_enabled_services()
            
            # 构建依赖图
            for service_name, service_config in services.items():
                self._dependency_graph[service_name] = service_config.dependencies
                self._service_configs[service_name] = service_config
            
            # 检查循环依赖
            if self._circular_dependency_detection:
                self._check_circular_dependencies()
            
            # 按依赖顺序注册服务
            registration_order = self._get_registration_order()
            
            for service_name in registration_order:
                if service_name in services:
                    self._register_from_config(services[service_name])
            
            logger.info(f"自动注册了 {len(registration_order)} 个服务")
            
        except Exception as e:
            logger.error(f"自动注册服务失败: {e}")
    
    def _register_from_config(self, service_config: ServiceConfig) -> None:
        """从配置注册服务
        
        Args:
            service_config: 服务配置
        """
        try:
            # 动态导入服务类
            service_class = self._import_class(service_config.class_path)
            
            # 获取接口类型
            interface_type = None
            if service_config.interface_path:
                interface_type = self._import_class(service_config.interface_path)
            else:
                # 如果没有指定接口，使用类本身作为接口
                interface_type = service_class
            
            # 注册服务
            scope = ServiceScope(service_config.scope)
            if scope == ServiceScope.SINGLETON:
                self.register_implementation(interface_type, service_class, singleton=True)
            elif scope == ServiceScope.TRANSIENT:
                self.register_implementation(interface_type, service_class, singleton=False)
            elif scope == ServiceScope.SCOPED:
                # 作用域服务暂时按单例处理
                self.register_implementation(interface_type, service_class, singleton=True)
            
            logger.debug(f"从配置注册服务: {service_config.name}")
            
        except Exception as e:
            logger.error(f"注册服务 {service_config.name} 失败: {e}")
            # 对于可选服务，记录警告但不中断整个系统
            if "performance" in service_config.name.lower() or "optimization" in service_config.name.lower():
                logger.warning(f"可选服务 {service_config.name} 注册失败，系统将继续运行")
                return
            raise
    
    def _import_class(self, class_path: str) -> Type:
        """动态导入类
        
        Args:
            class_path: 类路径，格式为 'module.path.ClassName'
            
        Returns:
            Type: 导入的类
        """
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except Exception as e:
            logger.error(f"导入类失败 {class_path}: {e}")
            # 对于可选服务，记录警告但不中断整个系统
            if "performance" in class_path.lower() or "optimization" in class_path.lower():
                logger.warning(f"可选服务 {class_path} 导入失败，系统将继续运行")
                return None
            raise
    
    def _get_registration_order(self) -> List[str]:
        """获取服务注册顺序（拓扑排序）
        
        Returns:
            List[str]: 按依赖顺序排列的服务名称列表
        """
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(service_name: str):
            if service_name in temp_visited:
                raise ValueError(f"检测到循环依赖: {service_name}")
            
            if service_name not in visited:
                temp_visited.add(service_name)
                
                # 先访问依赖
                for dependency in self._dependency_graph.get(service_name, []):
                    visit(dependency)
                
                temp_visited.remove(service_name)
                visited.add(service_name)
                result.append(service_name)
        
        # 访问所有服务
        for service_name in self._dependency_graph:
            if service_name not in visited:
                visit(service_name)
        
        return result
    
    def _check_circular_dependencies(self) -> None:
        """检查循环依赖"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(service_name: str, path: List[str]) -> bool:
            if service_name in rec_stack:
                cycle_path = path[path.index(service_name):] + [service_name]
                raise ValueError(f"检测到循环依赖: {' -> '.join(cycle_path)}")
            
            if service_name in visited:
                return False
            
            visited.add(service_name)
            rec_stack.add(service_name)
            
            for dependency in self._dependency_graph.get(service_name, []):
                if has_cycle(dependency, path + [service_name]):
                    return True
            
            rec_stack.remove(service_name)
            return False
        
        for service_name in self._dependency_graph:
            if service_name not in visited:
                has_cycle(service_name, [])
    
    def register(self, interface: Type[T], implementation: Type[T], singleton: bool = True) -> 'ServiceContainer':
        """注册服务实现（兼容性方法）
        
        Args:
            interface: 服务接口类型
            implementation: 服务实现类型
            singleton: 是否为单例模式
            
        Returns:
            ServiceContainer: 返回自身以支持链式调用
        """
        return self.register_implementation(interface, implementation, singleton)
    
    def register_implementation(self, interface: Type[T], implementation: Type[T], singleton: bool = True) -> 'ServiceContainer':
        """注册服务
        
        Args:
            interface: 服务接口类型
            implementation: 服务实现类型
            singleton: 是否为单例模式
            
        Returns:
            ServiceContainer: 返回自身以支持链式调用
        """
        service_name = self._get_service_name(interface)
        
        self._services[service_name] = {
            'interface': interface,
            'implementation': implementation,
            'singleton': singleton
        }
        
        logger.debug(f"已注册服务: {service_name} -> {implementation.__name__} (单例: {singleton})")
        return self
    
    def register_service_group(self, group_name: str) -> 'ServiceContainer':
        """注册服务组
        
        Args:
            group_name: 服务组名称
            
        Returns:
            ServiceContainer: 返回自身以支持链式调用
        """
        try:
            services = self._config_loader.get_services_by_group(group_name)
            
            for service_config in services:
                self._register_from_config(service_config)
            
            logger.info(f"注册服务组 {group_name}，包含 {len(services)} 个服务")
            
        except Exception as e:
            logger.error(f"注册服务组 {group_name} 失败: {e}")
        
        return self
    
    def get_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """获取服务配置
        
        Args:
            service_name: 服务名称
            
        Returns:
            ServiceConfig: 服务配置对象
        """
        return self._service_configs.get(service_name)
    
    def get_config_value(self, service_name: str, config_key: str, default: Any = None) -> Any:
        """获取服务配置值
        
        Args:
            service_name: 服务名称
            config_key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        service_config = self.get_service_config(service_name)
        if service_config:
            return service_config.config.get(config_key, default)
        return default
    
    def update_service_config(self, service_name: str, config_updates: Dict[str, Any]) -> None:
        """更新服务配置
        
        Args:
            service_name: 服务名称
            config_updates: 配置更新
        """
        service_config = self.get_service_config(service_name)
        if service_config:
            service_config.config.update(config_updates)
            logger.debug(f"更新服务 {service_name} 的配置")
        else:
            logger.warning(f"服务 {service_name} 不存在，无法更新配置")
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T], singleton: bool = True) -> 'ServiceContainer':
        """注册工厂函数
        
        Args:
            interface: 服务接口类型
            factory: 工厂函数
            singleton: 是否为单例模式
        """
        service_name = self._get_service_name(interface)
        
        self._factories[service_name] = factory
        self._services[service_name] = {
            'interface': interface,
            'implementation': None,
            'singleton': singleton,
            'factory': True
        }
        
        logger.debug(f"已注册工厂服务: {service_name} (单例: {singleton})")
        return self
    
    def register_instance(self, interface: Type[T], instance: T) -> 'ServiceContainer':
        """注册服务实例
        
        Args:
            interface: 服务接口类型
            instance: 服务实例
        """
        service_name = self._get_service_name(interface)
        
        self._instances[service_name] = instance
        self._services[service_name] = {
            'interface': interface,
            'implementation': type(instance),
            'singleton': True,
            'instance': True
        }
        
        logger.debug(f"已注册服务实例: {service_name} -> {type(instance).__name__}")
        return self
    
    def resolve(self, interface: Type[T]) -> T:
        """解析服务
        
        Args:
            interface: 服务接口类型
            
        Returns:
            T: 服务实例
            
        Raises:
            ValueError: 当服务未注册时
        """
        service_name = self._get_service_name(interface)
        
        if service_name not in self._services:
            raise ValueError(f"服务 {service_name} 未注册")
        
        service_config = self._services[service_name]
        
        # 如果是已注册的实例，直接返回
        if service_config.get('instance', False):
            return self._instances[service_name]
        
        # 单例模式检查
        if service_config['singleton']:
            if service_name in self._instances:
                return self._instances[service_name]
        
        # 创建新实例
        instance = self._create_instance(service_name, service_config)
        
        # 单例模式缓存
        if service_config['singleton']:
            self._instances[service_name] = instance
        
        return instance
    
    def _create_instance(self, service_name: str, service_config: Dict[str, Any]) -> Any:
        """创建服务实例"""
        try:
            # 使用工厂函数
            if service_config.get('factory', False):
                factory = self._factories[service_name]
                instance = factory()
            else:
                # 使用构造函数
                implementation = service_config['implementation']
                
                # 检查构造函数参数
                constructor = implementation.__init__
                sig = inspect.signature(constructor)
                
                # 自动注入依赖
                kwargs = {}
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    
                    if param.annotation != inspect.Parameter.empty:
                        try:
                            dependency = self.resolve(param.annotation)
                            kwargs[param_name] = dependency
                        except ValueError:
                            # 如果依赖未注册且有默认值，使用默认值
                            if param.default != inspect.Parameter.empty:
                                kwargs[param_name] = param.default
                            else:
                                logger.warning(f"无法解析依赖 {param_name}: {param.annotation}")
                
                instance = implementation(**kwargs)
            
            # 初始化服务（如果实现了ServiceInterface）
            if isinstance(instance, ServiceInterface):
                try:
                    # 配置服务（如果实现了ConfigurableService）
                    if isinstance(instance, ConfigurableService):
                        service_config_obj = self.get_service_config(service_name)
                        if service_config_obj and service_config_obj.config:
                            instance.configure(service_config_obj.config)
                    
                    # 初始化服务
                    instance.initialize()
                    
                    # 启动服务（如果实现了LifecycleService）
                    if isinstance(instance, LifecycleService):
                        instance.start()
                    
                    logger.debug(f"已初始化服务: {service_name}")
                except Exception as e:
                    logger.error(f"初始化服务 {service_name} 失败: {e}")
                    raise
            
            logger.debug(f"已创建服务实例: {service_name}")
            return instance
            
        except Exception as e:
            logger.error(f"创建服务实例失败 {service_name}: {e}")
            raise
    
    def _get_service_name(self, interface: Type) -> str:
        """获取服务名称"""
        return getattr(interface, '__name__', str(interface))
    
    def is_registered(self, interface: Type) -> bool:
        """检查服务是否已注册
        
        Args:
            interface: 服务接口类型
            
        Returns:
            bool: 是否已注册
        """
        service_name = self._get_service_name(interface)
        return service_name in self._services
    
    def shutdown_service(self, interface: Type[T]) -> None:
        """关闭指定服务
        
        Args:
            interface: 服务接口类型
        """
        service_name = self._get_service_name(interface)
        
        if service_name in self._instances:
            instance = self._instances[service_name]
            
            # 如果实现了LifecycleService，调用stop方法
            if isinstance(instance, LifecycleService):
                try:
                    instance.stop()
                    logger.debug(f"已停止服务: {service_name}")
                except Exception as e:
                    logger.error(f"停止服务 {service_name} 失败: {e}")
            
            # 如果实现了ServiceInterface，调用cleanup方法
            if isinstance(instance, ServiceInterface):
                try:
                    instance.cleanup()
                    logger.debug(f"已清理服务: {service_name}")
                except Exception as e:
                    logger.error(f"清理服务 {service_name} 失败: {e}")
            
            # 从实例缓存中移除
            del self._instances[service_name]
    
    def shutdown_all_services(self) -> None:
        """关闭所有服务"""
        # 按依赖关系逆序关闭服务
        shutdown_order = list(reversed(self._get_registration_order()))
        
        for service_name in shutdown_order:
            if service_name in self._instances:
                instance = self._instances[service_name]
                
                # 如果实现了LifecycleService，调用stop方法
                if isinstance(instance, LifecycleService):
                    try:
                        instance.stop()
                        logger.debug(f"已停止服务: {service_name}")
                    except Exception as e:
                        logger.error(f"停止服务 {service_name} 失败: {e}")
                
                # 如果实现了ServiceInterface，调用cleanup方法
                if isinstance(instance, ServiceInterface):
                    try:
                        instance.cleanup()
                        logger.debug(f"已清理服务: {service_name}")
                    except Exception as e:
                        logger.error(f"清理服务 {service_name} 失败: {e}")
        
        logger.info("所有服务已关闭")
    
    def restart_service(self, interface: Type[T]) -> T:
        """重启指定服务
        
        Args:
            interface: 服务接口类型
            
        Returns:
            T: 重启后的服务实例
        """
        service_name = self._get_service_name(interface)
        
        if service_name in self._instances:
            instance = self._instances[service_name]
            
            # 如果实现了LifecycleService，调用restart方法
            if isinstance(instance, LifecycleService):
                try:
                    instance.restart()
                    logger.debug(f"已重启服务: {service_name}")
                    return instance
                except Exception as e:
                    logger.error(f"重启服务 {service_name} 失败: {e}")
                    # 如果重启失败，尝试重新创建
        
        # 关闭现有服务并重新创建
        self.shutdown_service(interface)
        return self.resolve(interface)
    
    def get_service_status(self, interface: Type[T]) -> Dict[str, Any]:
        """获取服务状态
        
        Args:
            interface: 服务接口类型
            
        Returns:
            Dict[str, Any]: 服务状态信息
        """
        service_name = self._get_service_name(interface)
        status = {
            'name': service_name,
            'registered': service_name in self._services,
            'instantiated': service_name in self._instances,
            'initialized': False,
            'running': False
        }
        
        if service_name in self._instances:
            instance = self._instances[service_name]
            
            if isinstance(instance, ServiceInterface):
                status['initialized'] = instance.is_initialized()
            
            if isinstance(instance, LifecycleService):
                status['running'] = instance.get_status() == 'running'
        
        return status
    
    def clear(self) -> None:
        """清空所有注册的服务"""
        # 先关闭所有服务
        self.shutdown_all_services()
        
        # 清空注册信息
        self._services.clear()
        self._instances.clear()
        self._factories.clear()
        self._service_configs.clear()
        self._dependency_graph.clear()
        
        logger.debug("服务容器已清空")

# 全局容器实例
_container: Optional[ServiceContainer] = None

def get_container() -> ServiceContainer:
    """获取全局容器实例"""
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container

def reset_container():
    """重置全局容器（主要用于测试）"""
    global _container
    _container = None