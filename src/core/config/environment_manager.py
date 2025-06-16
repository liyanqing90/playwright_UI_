# -*- coding: utf-8 -*-
"""
环境管理器

负责管理不同环境的配置和切换。
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List

from utils.logger import logger


class Environment(Enum):
    """环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"

@dataclass
class EnvironmentInfo:
    """环境信息"""
    name: str
    description: str
    config_overrides: Dict[str, Any]
    is_debug: bool = False
    log_level: str = "INFO"

class EnvironmentManager:
    """环境管理器
    
    负责环境检测、配置覆盖和环境特定的行为管理。
    """
    
    def __init__(self, default_environment: str = Environment.DEVELOPMENT.value):
        """初始化环境管理器
        
        Args:
            default_environment: 默认环境名称
        """
        self._current_environment = self._detect_environment(default_environment)
        self._environment_configs = self._load_environment_configs()
        
        logger.info(f"当前环境: {self._current_environment}")
    
    def _detect_environment(self, default: str) -> str:
        """检测当前环境
        
        Args:
            default: 默认环境
            
        Returns:
            str: 检测到的环境名称
        """
        # 优先级：命令行参数 > 环境变量 > 配置文件 > 默认值
        
        # 1. 检查环境变量
        env_from_var = os.getenv('PLAYWRIGHT_ENV', os.getenv('ENV', os.getenv('ENVIRONMENT')))
        if env_from_var:
            logger.info(f"从环境变量检测到环境: {env_from_var}")
            return env_from_var.lower()
        
        # 2. 检查是否在CI环境中
        if os.getenv('CI') or os.getenv('GITHUB_ACTIONS') or os.getenv('JENKINS_URL'):
            logger.info("检测到CI环境，使用testing环境")
            return Environment.TESTING.value
        
        # 3. 检查是否在Docker容器中
        if os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER'):
            logger.info("检测到Docker环境")
            return os.getenv('DOCKER_ENV', Environment.PRODUCTION.value)
        
        # 4. 检查开发环境标识
        if os.getenv('DEBUG') == 'true' or os.path.exists('.env.development'):
            logger.info("检测到开发环境标识")
            return Environment.DEVELOPMENT.value
        
        # 5. 使用默认环境
        logger.info(f"使用默认环境: {default}")
        return default
    
    def _load_environment_configs(self) -> Dict[str, EnvironmentInfo]:
        """加载环境配置
        
        Returns:
            Dict[str, EnvironmentInfo]: 环境配置字典
        """
        return {
            Environment.DEVELOPMENT.value: EnvironmentInfo(
                name=Environment.DEVELOPMENT.value,
                description="开发环境",
                is_debug=True,
                log_level="DEBUG",
                config_overrides={
                    "timeouts": {
                        "default": 10000,
                        "short": 3000,
                        "long": 30000
                    },
                    "retry": {
                        "default_count": 1,
                        "default_delay": 500
                    },
                    "performance": {
                        "enable_monitoring": False,
                        "metrics_collection": False
                    },
                    "logging": {
                        "level": "DEBUG",
                        "enable_service_logs": True
                    }
                }
            ),
            
            Environment.TESTING.value: EnvironmentInfo(
                name=Environment.TESTING.value,
                description="测试环境",
                is_debug=True,
                log_level="INFO",
                config_overrides={
                    "timeouts": {
                        "default": 15000,
                        "short": 5000,
                        "long": 45000
                    },
                    "retry": {
                        "default_count": 2,
                        "default_delay": 1000
                    },
                    "assertion": {
                        "strict_mode": False
                    },
                    "logging": {
                        "level": "INFO",
                        "enable_service_logs": True
                    }
                }
            ),
            
            Environment.STAGING.value: EnvironmentInfo(
                name=Environment.STAGING.value,
                description="预发布环境",
                is_debug=False,
                log_level="INFO",
                config_overrides={
                    "timeouts": {
                        "default": 25000,
                        "short": 8000,
                        "long": 60000
                    },
                    "retry": {
                        "default_count": 3,
                        "default_delay": 1500
                    },
                    "performance": {
                        "enable_monitoring": True,
                        "metrics_collection": True
                    },
                    "logging": {
                        "level": "INFO",
                        "enable_service_logs": False
                    }
                }
            ),
            
            Environment.PRODUCTION.value: EnvironmentInfo(
                name=Environment.PRODUCTION.value,
                description="生产环境",
                is_debug=False,
                log_level="WARNING",
                config_overrides={
                    "timeouts": {
                        "default": 30000,
                        "short": 10000,
                        "long": 90000
                    },
                    "retry": {
                        "default_count": 3,
                        "default_delay": 2000,
                        "exponential_backoff": True
                    },
                    "performance": {
                        "enable_monitoring": True,
                        "metrics_collection": True,
                        "baseline_threshold": 2000
                    },
                    "assertion": {
                        "strict_mode": True
                    },
                    "logging": {
                        "level": "WARNING",
                        "enable_service_logs": False
                    }
                }
            ),
            
            Environment.LOCAL.value: EnvironmentInfo(
                name=Environment.LOCAL.value,
                description="本地环境",
                is_debug=True,
                log_level="DEBUG",
                config_overrides={
                    "timeouts": {
                        "default": 5000,
                        "short": 2000,
                        "long": 15000
                    },
                    "retry": {
                        "default_count": 1,
                        "default_delay": 200
                    },
                    "performance": {
                        "enable_monitoring": False
                    },
                    "logging": {
                        "level": "DEBUG",
                        "enable_service_logs": True
                    }
                }
            )
        }
    
    def get_current_environment(self) -> str:
        """获取当前环境名称
        
        Returns:
            str: 当前环境名称
        """
        return self._current_environment
    
    def get_environment_info(self, environment: Optional[str] = None) -> Optional[EnvironmentInfo]:
        """获取环境信息
        
        Args:
            environment: 环境名称，如果为None则返回当前环境信息
            
        Returns:
            EnvironmentInfo: 环境信息对象
        """
        env_name = environment or self._current_environment
        return self._environment_configs.get(env_name)
    
    def is_development(self) -> bool:
        """是否为开发环境
        
        Returns:
            bool: 是否为开发环境
        """
        return self._current_environment == Environment.DEVELOPMENT.value
    
    def is_testing(self) -> bool:
        """是否为测试环境
        
        Returns:
            bool: 是否为测试环境
        """
        return self._current_environment == Environment.TESTING.value
    
    def is_production(self) -> bool:
        """是否为生产环境
        
        Returns:
            bool: 是否为生产环境
        """
        return self._current_environment == Environment.PRODUCTION.value
    
    def is_debug_enabled(self) -> bool:
        """是否启用调试模式
        
        Returns:
            bool: 是否启用调试模式
        """
        env_info = self.get_environment_info()
        return env_info.is_debug if env_info else False
    
    def get_log_level(self) -> str:
        """获取日志级别
        
        Returns:
            str: 日志级别
        """
        env_info = self.get_environment_info()
        return env_info.log_level if env_info else "INFO"
    
    def get_config_overrides(self) -> Dict[str, Any]:
        """获取配置覆盖
        
        Returns:
            Dict[str, Any]: 配置覆盖字典
        """
        env_info = self.get_environment_info()
        return env_info.config_overrides if env_info else {}
    
    def switch_environment(self, environment: str) -> None:
        """切换环境
        
        Args:
            environment: 目标环境名称
        """
        if environment not in self._environment_configs:
            raise ValueError(f"未知的环境: {environment}")
        
        old_env = self._current_environment
        self._current_environment = environment
        
        logger.info(f"环境已从 {old_env} 切换到 {environment}")
    
    def get_available_environments(self) -> List[str]:
        """获取可用环境列表
        
        Returns:
            List[str]: 可用环境名称列表
        """
        return list(self._environment_configs.keys())
    
    def validate_environment(self, environment: str) -> bool:
        """验证环境是否有效
        
        Args:
            environment: 环境名称
            
        Returns:
            bool: 环境是否有效
        """
        return environment in self._environment_configs
    
    def get_environment_variables(self) -> Dict[str, str]:
        """获取环境相关的环境变量
        
        Returns:
            Dict[str, str]: 环境变量字典
        """
        env_vars = {}
        
        # 添加当前环境信息
        env_vars['CURRENT_ENV'] = self._current_environment
        env_vars['IS_DEBUG'] = str(self.is_debug_enabled()).lower()
        env_vars['LOG_LEVEL'] = self.get_log_level()
        
        # 添加环境特定的变量
        env_info = self.get_environment_info()
        if env_info:
            env_vars['ENV_DESCRIPTION'] = env_info.description
        
        return env_vars
    
    def apply_environment_config(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """应用环境配置覆盖
        
        Args:
            base_config: 基础配置
            
        Returns:
            Dict[str, Any]: 应用环境覆盖后的配置
        """
        config = base_config.copy()
        overrides = self.get_config_overrides()
        
        # 深度合并配置
        def deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value
        
        deep_merge(config, overrides)
        
        logger.debug(f"应用了环境 {self._current_environment} 的配置覆盖")
        return config
    
    def __str__(self) -> str:
        """字符串表示"""
        env_info = self.get_environment_info()
        if env_info:
            return f"EnvironmentManager(current={self._current_environment}, debug={env_info.is_debug})"
        return f"EnvironmentManager(current={self._current_environment})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()