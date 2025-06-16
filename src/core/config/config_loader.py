# -*- coding: utf-8 -*-
"""
配置加载器

负责加载和解析服务配置文件，支持环境特定配置。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

import yaml

from utils.logger import logger


@dataclass
class ServiceConfig:
    """服务配置数据类"""
    name: str
    class_path: str
    interface_path: Optional[str] = None
    scope: str = "singleton"  # singleton, transient, scoped
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

@dataclass
class ServiceGroupConfig:
    """服务组配置数据类"""
    name: str
    services: List[str]
    description: Optional[str] = None

@dataclass
class GlobalConfig:
    """全局配置数据类"""
    container: Dict[str, Any] = field(default_factory=dict)
    logging: Dict[str, Any] = field(default_factory=dict)
    timeouts: Dict[str, int] = field(default_factory=dict)
    retry: Dict[str, Any] = field(default_factory=dict)

class ConfigLoader:
    """配置加载器
    
    负责加载YAML配置文件并提供配置访问接口。
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None, environment: str = "development"):
        """初始化配置加载器
        
        Args:
            config_path: 配置文件路径，默认为当前目录下的services.yaml
            environment: 环境名称，用于加载环境特定配置
        """
        self.environment = environment
        self._config_data: Dict[str, Any] = {}
        self._services: Dict[str, ServiceConfig] = {}
        self._service_groups: Dict[str, ServiceGroupConfig] = {}
        self._global_config: GlobalConfig = GlobalConfig()
        
        # 确定配置文件路径
        if config_path is None:
            config_path = Path(__file__).parent / "services.yaml"
        else:
            config_path = Path(config_path)
        
        self.config_path = config_path
        
        # 加载配置
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                logger.warning(f"配置文件不存在: {self.config_path}")
                self._load_default_config()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config_data = yaml.safe_load(file) or {}
            
            logger.info(f"成功加载配置文件: {self.config_path}")
            
            # 解析配置
            self._parse_services()
            self._parse_service_groups()
            self._parse_global_config()
            self._apply_environment_config()
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._load_default_config()
    
    def _load_default_config(self) -> None:
        """加载默认配置"""
        logger.info("使用默认配置")
        
        # 默认服务配置
        default_services = {
            "element_service": ServiceConfig(
                name="element_service",
                class_path="src.core.services.element_service.ElementService",
                interface_path="src.core.services.element_service.ElementOperations",
                config={"default_timeout": 30000}
            ),
            "navigation_service": ServiceConfig(
                name="navigation_service",
                class_path="src.core.services.navigation_service.NavigationService",
                interface_path="src.core.services.navigation_service.NavigationOperations",
                config={"default_timeout": 30000}
            ),
            "wait_service": ServiceConfig(
                name="wait_service",
                class_path="src.core.services.wait_service.WaitService",
                interface_path="src.core.services.wait_service.WaitOperations",
                config={"default_timeout": 30000}
            ),
            "assertion_service": ServiceConfig(
                name="assertion_service",
                class_path="src.core.services.assertion_service.AssertionService",
                interface_path="src.core.services.assertion_service.AssertionOperations",
                dependencies=["wait_service"],
                config={"default_timeout": 30000}
            ),
            "variable_service": ServiceConfig(
                name="variable_service",
                class_path="src.core.services.variable_service.VariableService",
                interface_path="src.core.services.variable_service.VariableOperations"
            )
        }
        
        self._services = default_services
        
        # 默认全局配置
        self._global_config = GlobalConfig(
            container={"auto_wire": True, "lazy_loading": True},
            timeouts={"default": 30000, "short": 5000, "long": 60000},
            retry={"default_count": 3, "default_delay": 1000}
        )
    
    def _parse_services(self) -> None:
        """解析服务配置"""
        services_data = self._config_data.get("services", {})
        
        for service_name, service_config in services_data.items():
            try:
                self._services[service_name] = ServiceConfig(
                    name=service_name,
                    class_path=service_config.get("class", ""),
                    interface_path=service_config.get("interface"),
                    scope=service_config.get("scope", "singleton"),
                    dependencies=service_config.get("dependencies", []),
                    config=service_config.get("config", {}),
                    enabled=service_config.get("enabled", True)
                )
            except Exception as e:
                logger.error(f"解析服务配置失败 {service_name}: {e}")
    
    def _parse_service_groups(self) -> None:
        """解析服务组配置"""
        groups_data = self._config_data.get("service_groups", {})
        
        for group_name, group_config in groups_data.items():
            try:
                self._service_groups[group_name] = ServiceGroupConfig(
                    name=group_name,
                    services=group_config.get("services", []),
                    description=group_config.get("description")
                )
            except Exception as e:
                logger.error(f"解析服务组配置失败 {group_name}: {e}")
    
    def _parse_global_config(self) -> None:
        """解析全局配置"""
        global_data = self._config_data.get("global", {})
        
        self._global_config = GlobalConfig(
            container=global_data.get("container", {}),
            logging=global_data.get("logging", {}),
            timeouts=global_data.get("timeouts", {}),
            retry=global_data.get("retry", {})
        )
    
    def _apply_environment_config(self) -> None:
        """应用环境特定配置"""
        env_data = self._config_data.get("environments", {}).get(self.environment, {})
        
        if not env_data:
            logger.info(f"未找到环境 {self.environment} 的特定配置")
            return
        
        # 应用环境特定的服务配置
        env_services = env_data.get("services", {})
        for service_name, env_config in env_services.items():
            if service_name in self._services:
                # 合并配置
                service = self._services[service_name]
                env_service_config = env_config.get("config", {})
                service.config.update(env_service_config)
                
                # 更新其他属性
                if "enabled" in env_config:
                    service.enabled = env_config["enabled"]
                if "scope" in env_config:
                    service.scope = env_config["scope"]
                
                logger.debug(f"应用环境配置到服务 {service_name}")
    
    def get_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """获取服务配置
        
        Args:
            service_name: 服务名称
            
        Returns:
            ServiceConfig: 服务配置对象，如果不存在则返回None
        """
        return self._services.get(service_name)
    
    def get_all_services(self) -> Dict[str, ServiceConfig]:
        """获取所有服务配置
        
        Returns:
            Dict[str, ServiceConfig]: 所有服务配置
        """
        return self._services.copy()
    
    def get_enabled_services(self) -> Dict[str, ServiceConfig]:
        """获取启用的服务配置
        
        Returns:
            Dict[str, ServiceConfig]: 启用的服务配置
        """
        return {name: config for name, config in self._services.items() if config.enabled}
    
    def get_service_group(self, group_name: str) -> Optional[ServiceGroupConfig]:
        """获取服务组配置
        
        Args:
            group_name: 服务组名称
            
        Returns:
            ServiceGroupConfig: 服务组配置对象，如果不存在则返回None
        """
        return self._service_groups.get(group_name)
    
    def get_services_by_group(self, group_name: str) -> List[ServiceConfig]:
        """根据服务组获取服务配置列表
        
        Args:
            group_name: 服务组名称
            
        Returns:
            List[ServiceConfig]: 服务配置列表
        """
        group = self.get_service_group(group_name)
        if not group:
            return []
        
        services = []
        for service_name in group.services:
            service_config = self.get_service_config(service_name)
            if service_config and service_config.enabled:
                services.append(service_config)
        
        return services
    
    def get_global_config(self) -> GlobalConfig:
        """获取全局配置
        
        Returns:
            GlobalConfig: 全局配置对象
        """
        return self._global_config
    
    def get_timeout(self, timeout_type: str = "default") -> int:
        """获取超时配置
        
        Args:
            timeout_type: 超时类型（default, short, long）
            
        Returns:
            int: 超时时间（毫秒）
        """
        return self._global_config.timeouts.get(timeout_type, 30000)
    
    def reload_config(self) -> None:
        """重新加载配置"""
        logger.info("重新加载配置文件")
        self._config_data.clear()
        self._services.clear()
        self._service_groups.clear()
        self._load_config()
    
    def validate_config(self) -> List[str]:
        """验证配置
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证服务配置
        for service_name, service_config in self._services.items():
            if not service_config.class_path:
                errors.append(f"服务 {service_name} 缺少class配置")
            
            # 验证依赖关系
            for dep in service_config.dependencies:
                if dep not in self._services:
                    errors.append(f"服务 {service_name} 的依赖 {dep} 不存在")
        
        # 检查循环依赖
        cycle_errors = self._check_circular_dependencies()
        errors.extend(cycle_errors)
        
        return errors
    
    def _check_circular_dependencies(self) -> List[str]:
        """检查循环依赖
        
        Returns:
            List[str]: 循环依赖错误列表
        """
        errors = []
        visited = set()
        rec_stack = set()
        
        def has_cycle(service_name: str, path: List[str]) -> bool:
            if service_name in rec_stack:
                cycle_path = path[path.index(service_name):] + [service_name]
                errors.append(f"检测到循环依赖: {' -> '.join(cycle_path)}")
                return True
            
            if service_name in visited:
                return False
            
            visited.add(service_name)
            rec_stack.add(service_name)
            
            service_config = self._services.get(service_name)
            if service_config:
                for dep in service_config.dependencies:
                    if has_cycle(dep, path + [service_name]):
                        return True
            
            rec_stack.remove(service_name)
            return False
        
        for service_name in self._services:
            if service_name not in visited:
                has_cycle(service_name, [])
        
        return errors