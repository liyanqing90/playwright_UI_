"""公共模块包

本包包含框架的公共组件，包括：
- 异常处理
- 配置管理
- 类型定义
- 常量定义
"""

from .exceptions import (
    AutomationError,
    ElementNotFoundError,
    CommandExecutionError,
    ConfigurationError,
    ValidationError,
    NetworkError,
    TimeoutError,
    BrowserError,
    DataError,
    AssertionError
)

from .config_manager import (
    ConfigManager,
    ConfigSchema,
    get_config_manager,
    get_config,
    get_config_value
)

from .types import (
    # 基础类型
    ElementSelector,
    VariableValue,
    StepDefinition,
    TestData,
    ConfigData,
    AssertionResult,
    
    # 枚举类型
    ActionType,
    BrowserType,
    AssertionType,
    LogLevel,
    
    # 数据类
    StepResult,
    TestCaseResult,
    PerformanceMetrics,
    ElementInfo,
    
    # 协议
    CommandProtocol,
    PageProtocol,
    AssertionProtocol,
    ConfigProtocol,
    LoggerProtocol,
    DataManagerProtocol,
    
    # 基类
    BaseCommand,
    BasePage,
    
    # 类型检查函数
    is_command,
    is_page,
    is_assertion,
    is_config_manager,
    is_logger
)

__all__ = [
    # 异常类
    'AutomationError',
    'ElementNotFoundError',
    'CommandExecutionError',
    'ConfigurationError',
    'ValidationError',
    'NetworkError',
    'TimeoutError',
    'BrowserError',
    'DataError',
    'AssertionError',
    
    # 配置管理
    'ConfigManager',
    'ConfigSchema',
    'get_config_manager',
    'get_config',
    'get_config_value',
    
    # 类型定义
    'ElementSelector',
    'VariableValue',
    'StepDefinition',
    'TestData',
    'ConfigData',
    'AssertionResult',
    'ActionType',
    'BrowserType',
    'AssertionType',
    'LogLevel',
    'StepResult',
    'TestCaseResult',
    'PerformanceMetrics',
    'ElementInfo',
    'CommandProtocol',
    'PageProtocol',
    'AssertionProtocol',
    'ConfigProtocol',
    'LoggerProtocol',
    'DataManagerProtocol',
    'BaseCommand',
    'BasePage',
    'is_command',
    'is_page',
    'is_assertion',
    'is_config_manager',
    'is_logger'
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'Playwright UI Framework Team'
__description__ = 'Common utilities and types for Playwright UI automation framework'