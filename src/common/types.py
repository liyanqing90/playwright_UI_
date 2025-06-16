"""统一类型定义模块

本模块定义了框架中使用的所有类型注解和协议，提供类型安全支持。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import (
    Protocol, TypeVar, Dict, Any, Optional, Union, List, Tuple,
    Callable, Awaitable, Type, runtime_checkable
)

try:
    from playwright.sync_api import Page, Locator, Browser, BrowserContext
except ImportError:
    # 如果 Playwright 未安装，定义占位符类型
    Page = Any
    Locator = Any
    Browser = Any
    BrowserContext = Any

# 基础类型别名
ElementSelector = str
VariableValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
StepDefinition = Dict[str, Any]
TestData = Dict[str, Any]
ConfigData = Dict[str, Any]
AssertionResult = Tuple[bool, str]  # (success, message)

# 类型变量
T = TypeVar('T')
CommandType = TypeVar('CommandType', bound='CommandProtocol')
PageType = TypeVar('PageType', bound='PageProtocol')

# 枚举类型
class ActionType(Enum):
    """操作类型枚举"""
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    NAVIGATE = "navigate"
    WAIT = "wait"
    ASSERT = "assert"
    SCRIPT = "script"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    SCREENSHOT = "screenshot"
    NETWORK = "network"
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    WINDOW = "window"
    STORAGE = "storage"
    PERFORMANCE = "performance"

class BrowserType(Enum):
    """浏览器类型枚举"""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"
    CHROME = "chrome"
    EDGE = "msedge"

class AssertionType(Enum):
    """断言类型枚举"""
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    VISIBLE = "visible"
    HIDDEN = "hidden"
    ENABLED = "enabled"
    DISABLED = "disabled"
    CHECKED = "checked"
    UNCHECKED = "unchecked"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    REGEX_MATCH = "regex_match"
    LENGTH = "length"
    EMPTY = "empty"
    NOT_EMPTY = "not_empty"

class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# 数据类
@dataclass
class StepResult:
    """步骤执行结果"""
    success: bool
    message: str
    data: Optional[Any] = None
    duration: Optional[float] = None
    screenshot_path: Optional[str] = None
    error: Optional[Exception] = None

@dataclass
class TestCaseResult:
    """测试用例执行结果"""
    case_name: str
    success: bool
    total_steps: int
    passed_steps: int
    failed_steps: int
    duration: float
    error_message: Optional[str] = None
    step_results: List[StepResult] = None

@dataclass
class PerformanceMetrics:
    """性能指标"""
    page_load_time: Optional[float] = None
    dom_content_loaded: Optional[float] = None
    first_paint: Optional[float] = None
    first_contentful_paint: Optional[float] = None
    largest_contentful_paint: Optional[float] = None
    memory_usage: Optional[Dict[str, float]] = None
    network_requests: Optional[List[Dict[str, Any]]] = None

@dataclass
class ElementInfo:
    """元素信息"""
    selector: str
    tag_name: Optional[str] = None
    text_content: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None
    bounding_box: Optional[Dict[str, float]] = None
    is_visible: Optional[bool] = None
    is_enabled: Optional[bool] = None

# 协议定义
@runtime_checkable
class CommandProtocol(Protocol):
    """命令协议
    
    定义所有命令类必须实现的接口。
    """
    
    def execute(
        self, 
        ui_helper: Any, 
        selector: str, 
        value: Any, 
        step: StepDefinition
    ) -> Any:
        """执行命令
        
        Args:
            ui_helper: UI 助手实例
            selector: 元素选择器
            value: 操作值
            step: 步骤定义
            
        Returns:
            执行结果
        """
        ...
    
    def validate_params(self, selector: str, value: Any, step: StepDefinition) -> bool:
        """验证参数
        
        Args:
            selector: 元素选择器
            value: 操作值
            step: 步骤定义
            
        Returns:
            参数是否有效
        """
        ...

@runtime_checkable
class PageProtocol(Protocol):
    """页面协议
    
    定义页面对象必须实现的接口。
    """
    
    page: Page
    
    def navigate(self, url: str) -> None:
        """导航到指定 URL"""
        ...
    
    def click(self, selector: str) -> None:
        """点击元素"""
        ...
    
    def fill(self, selector: str, value: str) -> None:
        """填充输入框"""
        ...
    
    def wait_for_element(self, selector: str, timeout: Optional[int] = None) -> Locator:
        """等待元素出现"""
        ...

@runtime_checkable
class AssertionProtocol(Protocol):
    """断言协议
    
    定义断言类必须实现的接口。
    """
    
    def assert_equal(self, actual: Any, expected: Any, message: Optional[str] = None) -> AssertionResult:
        """相等断言"""
        ...
    
    def assert_contains(self, container: Any, item: Any, message: Optional[str] = None) -> AssertionResult:
        """包含断言"""
        ...
    
    def assert_visible(self, selector: str, message: Optional[str] = None) -> AssertionResult:
        """可见性断言"""
        ...

@runtime_checkable
class ConfigProtocol(Protocol):
    """配置协议
    
    定义配置管理器必须实现的接口。
    """
    
    def get_config(self, config_type: str) -> ConfigData:
        """获取配置"""
        ...
    
    def get_value(self, config_type: str, key: str, default: Any = None) -> Any:
        """获取配置值"""
        ...
    
    def set_value(self, config_type: str, key: str, value: Any) -> None:
        """设置配置值"""
        ...

@runtime_checkable
class LoggerProtocol(Protocol):
    """日志协议
    
    定义日志记录器必须实现的接口。
    """
    
    def debug(self, message: str, **kwargs) -> None:
        """记录调试信息"""
        ...
    
    def info(self, message: str, **kwargs) -> None:
        """记录信息"""
        ...
    
    def warning(self, message: str, **kwargs) -> None:
        """记录警告"""
        ...
    
    def error(self, message: str, **kwargs) -> None:
        """记录错误"""
        ...
    
    def critical(self, message: str, **kwargs) -> None:
        """记录严重错误"""
        ...

@runtime_checkable
class DataManagerProtocol(Protocol):
    """数据管理协议
    
    定义数据管理器必须实现的接口。
    """
    
    def load_test_data(self, project: str, data_type: str) -> TestData:
        """加载测试数据"""
        ...
    
    def save_test_data(self, project: str, data_type: str, data: TestData) -> None:
        """保存测试数据"""
        ...
    
    def validate_data(self, data: TestData, schema: str) -> bool:
        """验证数据"""
        ...

# 抽象基类
class BaseCommand(ABC):
    """命令基类
    
    所有命令类的抽象基类。
    """
    
    @abstractmethod
    def execute(
        self, 
        ui_helper: Any, 
        selector: str, 
        value: Any, 
        step: StepDefinition
    ) -> Any:
        """执行命令"""
        pass
    
    def validate_params(self, selector: str, value: Any, step: StepDefinition) -> bool:
        """验证参数（默认实现）"""
        return True
    
    def get_command_name(self) -> str:
        """获取命令名称"""
        return self.__class__.__name__.replace('Command', '').lower()

# BasePage类已移至src.core.base_page模块，避免重复定义

# 函数类型别名
CommandExecutor = Callable[[Any, str, Any, StepDefinition], Any]
AssertionFunction = Callable[[Any, Any], AssertionResult]
ValidationFunction = Callable[[Any], bool]
TransformFunction = Callable[[Any], Any]
EventHandler = Callable[[str, Dict[str, Any]], None]
Middleware = Callable[[StepDefinition], StepDefinition]

# 异步类型别名
AsyncCommandExecutor = Callable[[Any, str, Any, StepDefinition], Awaitable[Any]]
AsyncAssertionFunction = Callable[[Any, Any], Awaitable[AssertionResult]]
AsyncValidationFunction = Callable[[Any], Awaitable[bool]]
AsyncEventHandler = Callable[[str, Dict[str, Any]], Awaitable[None]]

# 复合类型
CommandRegistry = Dict[str, Type[CommandProtocol]]
PageRegistry = Dict[str, Type[PageProtocol]]
AssertionRegistry = Dict[str, AssertionFunction]
MiddlewareStack = List[Middleware]
EventHandlerRegistry = Dict[str, List[EventHandler]]

# 配置相关类型
BrowserConfig = Dict[str, Union[str, bool, int, Dict[str, Any]]]
TestConfig = Dict[str, Union[str, bool, int, List[str]]]
PerformanceConfig = Dict[str, Union[bool, List[str], Dict[str, Any]]]
EnvironmentConfig = Dict[str, Union[str, bool, int, Dict[str, Any]]]

# 测试相关类型
TestSuite = List[StepDefinition]
TestModule = Dict[str, Union[str, List[StepDefinition], TestData]]
TestProject = Dict[str, Union[str, List[TestModule], ConfigData]]

# 网络相关类型
NetworkRequest = Dict[str, Union[str, int, Dict[str, str]]]
NetworkResponse = Dict[str, Union[str, int, Dict[str, str], bytes]]
NetworkInterception = Callable[[NetworkRequest], Optional[NetworkResponse]]

# 文件相关类型
FileUpload = Dict[str, Union[str, bytes]]
FileDownload = Dict[str, Union[str, int, bytes]]
ScreenshotOptions = Dict[str, Union[str, bool, int, Dict[str, int]]]

# 性能相关类型
TimingMetrics = Dict[str, float]
MemoryMetrics = Dict[str, Union[int, float]]
NetworkMetrics = Dict[str, Union[int, float, List[NetworkRequest]]]

# 工具函数类型检查
def is_command(obj: Any) -> bool:
    """检查对象是否为命令"""
    return isinstance(obj, CommandProtocol)

def is_page(obj: Any) -> bool:
    """检查对象是否为页面对象"""
    return isinstance(obj, PageProtocol)

def is_assertion(obj: Any) -> bool:
    """检查对象是否为断言对象"""
    return isinstance(obj, AssertionProtocol)

def is_config_manager(obj: Any) -> bool:
    """检查对象是否为配置管理器"""
    return isinstance(obj, ConfigProtocol)

def is_logger(obj: Any) -> bool:
    """检查对象是否为日志记录器"""
    return isinstance(obj, LoggerProtocol)