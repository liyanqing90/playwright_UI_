# API参考文档

## 概述

本文档提供了之家UI自动化测试框架的完整API参考，包括核心类、方法、配置选项和使用示例。开发者可以通过本文档了解如何扩展框架功能或集成到其他系统中。

## 1. 核心API

### 1.1 TestRunner

测试运行器是框架的入口点，负责协调整个测试执行流程。

```python
class TestRunner:
    """测试运行器主类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化测试运行器
        
        Args:
            config_path (str, optional): 配置文件路径
        """
        pass
    
    def run_test_suite(self, test_path: str, **kwargs) -> TestResult:
        """
        运行测试套件
        
        Args:
            test_path (str): 测试用例路径
            **kwargs: 额外的运行参数
                - browser (str): 浏览器类型
                - headless (bool): 是否无头模式
                - timeout (int): 超时时间
                - parallel (bool): 是否并行执行
                - max_workers (int): 最大工作线程数
        
        Returns:
            TestResult: 测试结果对象
        
        Raises:
            TestConfigError: 配置错误
            TestExecutionError: 执行错误
        """
        pass
    
    def run_single_test(self, test_case: str, **kwargs) -> TestCaseResult:
        """
        运行单个测试用例
        
        Args:
            test_case (str): 测试用例名称
            **kwargs: 运行参数
        
        Returns:
            TestCaseResult: 测试用例结果
        """
        pass
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """
        获取测试统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
                - total_tests: 总测试数
                - passed_tests: 通过测试数
                - failed_tests: 失败测试数
                - execution_time: 执行时间
                - success_rate: 成功率
        """
        pass
```

### 1.2 TestCaseExecutor

测试用例执行器负责执行单个测试用例。

```python
class TestCaseExecutor:
    """测试用例执行器"""
    
    def __init__(self, service_container: ServiceContainer):
        """
        初始化执行器
        
        Args:
            service_container (ServiceContainer): 服务容器
        """
        pass
    
    def execute(self, test_case: TestCase) -> TestCaseResult:
        """
        执行测试用例
        
        Args:
            test_case (TestCase): 测试用例对象
        
        Returns:
            TestCaseResult: 执行结果
        """
        pass
    
    def setup_test_case(self, test_case: TestCase) -> None:
        """
        测试用例前置操作
        
        Args:
            test_case (TestCase): 测试用例
        """
        pass
    
    def teardown_test_case(self, test_case: TestCase) -> None:
        """
        测试用例后置操作
        
        Args:
            test_case (TestCase): 测试用例
        """
        pass
```

### 1.3 StepExecutor

步骤执行器负责执行测试步骤。

```python
class StepExecutor:
    """步骤执行器"""
    
    def __init__(self, service_container: ServiceContainer):
        """
        初始化步骤执行器
        
        Args:
            service_container (ServiceContainer): 服务容器
        """
        pass
    
    def execute_step(self, step: TestStep, context: ExecutionContext) -> StepResult:
        """
        执行单个步骤
        
        Args:
            step (TestStep): 测试步骤
            context (ExecutionContext): 执行上下文
        
        Returns:
            StepResult: 步骤执行结果
        """
        pass
    
    def execute_conditional_step(self, step: ConditionalStep, context: ExecutionContext) -> StepResult:
        """
        执行条件步骤
        
        Args:
            step (ConditionalStep): 条件步骤
            context (ExecutionContext): 执行上下文
        
        Returns:
            StepResult: 执行结果
        """
        pass
    
    def execute_loop_step(self, step: LoopStep, context: ExecutionContext) -> List[StepResult]:
        """
        执行循环步骤
        
        Args:
            step (LoopStep): 循环步骤
            context (ExecutionContext): 执行上下文
        
        Returns:
            List[StepResult]: 循环执行结果列表
        """
        pass
```

## 2. 数据模型API

### 2.1 TestCase

测试用例数据模型。

```python
@dataclass
class TestCase:
    """测试用例数据模型"""
    
    name: str                           # 测试用例名称
    description: str = ""               # 描述
    steps: List[TestStep] = field(default_factory=list)  # 测试步骤
    variables: Dict[str, Any] = field(default_factory=dict)  # 变量
    depends_on: List[str] = field(default_factory=list)  # 依赖的测试用例
    fixtures: List[str] = field(default_factory=list)   # 使用的夹具
    tags: List[str] = field(default_factory=list)       # 标签
    timeout: int = 30000                # 超时时间(毫秒)
    retry_count: int = 0                # 重试次数
    
    def add_step(self, step: TestStep) -> None:
        """
        添加测试步骤
        
        Args:
            step (TestStep): 测试步骤
        """
        pass
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        获取变量值
        
        Args:
            name (str): 变量名
            default (Any): 默认值
        
        Returns:
            Any: 变量值
        """
        pass
    
    def set_variable(self, name: str, value: Any) -> None:
        """
        设置变量值
        
        Args:
            name (str): 变量名
            value (Any): 变量值
        """
        pass
```

### 2.2 TestStep

测试步骤数据模型。

```python
@dataclass
class TestStep:
    """测试步骤数据模型"""
    
    action: StepAction                  # 步骤动作
    selector: str = ""                  # 元素选择器
    value: Any = None                   # 步骤值
    timeout: int = None                 # 超时时间
    retry_count: int = None             # 重试次数
    description: str = ""               # 描述
    screenshot: bool = False            # 是否截图
    
    # 条件执行
    condition: str = ""                 # 执行条件
    if_condition: str = ""              # if条件
    then_steps: List['TestStep'] = field(default_factory=list)  # then步骤
    else_steps: List['TestStep'] = field(default_factory=list)  # else步骤
    
    # 循环执行
    for_each: str = ""                  # 循环数据
    loop_steps: List['TestStep'] = field(default_factory=list)  # 循环步骤
    
    # 模块执行
    module_name: str = ""               # 模块名称
    module_params: Dict[str, Any] = field(default_factory=dict)  # 模块参数
    
    def is_conditional(self) -> bool:
        """
        判断是否为条件步骤
        
        Returns:
            bool: 是否为条件步骤
        """
        pass
    
    def is_loop(self) -> bool:
        """
        判断是否为循环步骤
        
        Returns:
            bool: 是否为循环步骤
        """
        pass
    
    def is_module(self) -> bool:
        """
        判断是否为模块步骤
        
        Returns:
            bool: 是否为模块步骤
        """
        pass
```

### 2.3 TestResult

测试结果数据模型。

```python
@dataclass
class TestResult:
    """测试结果数据模型"""
    
    test_suite_name: str                # 测试套件名称
    start_time: datetime                # 开始时间
    end_time: datetime                  # 结束时间
    total_tests: int                    # 总测试数
    passed_tests: int                   # 通过测试数
    failed_tests: int                   # 失败测试数
    skipped_tests: int                  # 跳过测试数
    test_case_results: List[TestCaseResult] = field(default_factory=list)  # 测试用例结果
    
    @property
    def execution_time(self) -> timedelta:
        """
        获取执行时间
        
        Returns:
            timedelta: 执行时间
        """
        pass
    
    @property
    def success_rate(self) -> float:
        """
        获取成功率
        
        Returns:
            float: 成功率(0.0-1.0)
        """
        pass
    
    def add_test_case_result(self, result: TestCaseResult) -> None:
        """
        添加测试用例结果
        
        Args:
            result (TestCaseResult): 测试用例结果
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 结果字典
        """
        pass
```

## 3. 服务容器API

### 3.1 ServiceContainer

依赖注入容器。

```python
class ServiceContainer:
    """服务容器"""
    
    def __init__(self):
        """初始化服务容器"""
        pass
    
    def register(self, 
                 service_type: Type[T], 
                 implementation: Union[Type[T], Callable[[], T], T],
                 scope: ServiceScope = ServiceScope.TRANSIENT) -> None:
        """
        注册服务
        
        Args:
            service_type (Type[T]): 服务类型
            implementation (Union[Type[T], Callable[[], T], T]): 实现
            scope (ServiceScope): 服务作用域
        """
        pass
    
    def register_singleton(self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T], T]) -> None:
        """
        注册单例服务
        
        Args:
            service_type (Type[T]): 服务类型
            implementation (Union[Type[T], Callable[[], T], T]): 实现
        """
        pass
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """
        注册工厂服务
        
        Args:
            service_type (Type[T]): 服务类型
            factory (Callable[[], T]): 工厂函数
        """
        pass
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        解析服务
        
        Args:
            service_type (Type[T]): 服务类型
        
        Returns:
            T: 服务实例
        
        Raises:
            ServiceNotFoundError: 服务未找到
            CircularDependencyError: 循环依赖
        """
        pass
    
    def is_registered(self, service_type: Type) -> bool:
        """
        检查服务是否已注册
        
        Args:
            service_type (Type): 服务类型
        
        Returns:
            bool: 是否已注册
        """
        pass
```

## 4. 命令系统API

### 4.1 Command基类

所有命令的基类。

```python
class Command(ABC):
    """命令基类"""
    
    def __init__(self, ui_helper: UIHelper):
        """
        初始化命令
        
        Args:
            ui_helper (UIHelper): UI助手
        """
        pass
    
    @abstractmethod
    def execute(self, selector: str = None, value: Any = None, **kwargs) -> Any:
        """
        执行命令
        
        Args:
            selector (str, optional): 元素选择器
            value (Any, optional): 命令值
            **kwargs: 额外参数
        
        Returns:
            Any: 执行结果
        """
        pass
    
    def validate_arguments(self, selector: str = None, value: Any = None, **kwargs) -> None:
        """
        验证参数
        
        Args:
            selector (str, optional): 元素选择器
            value (Any, optional): 命令值
            **kwargs: 额外参数
        
        Raises:
            ArgumentValidationError: 参数验证错误
        """
        pass
    
    def before_execute(self, **kwargs) -> None:
        """
        执行前钩子
        
        Args:
            **kwargs: 参数
        """
        pass
    
    def after_execute(self, result: Any, **kwargs) -> None:
        """
        执行后钩子
        
        Args:
            result (Any): 执行结果
            **kwargs: 参数
        """
        pass
    
    def on_error(self, error: Exception, **kwargs) -> None:
        """
        错误处理钩子
        
        Args:
            error (Exception): 异常
            **kwargs: 参数
        """
        pass
```

### 4.2 CommandExecutor

命令执行器。

```python
class CommandExecutor:
    """命令执行器"""
    
    def __init__(self, service_container: ServiceContainer):
        """
        初始化命令执行器
        
        Args:
            service_container (ServiceContainer): 服务容器
        """
        pass
    
    def execute_command(self, action: StepAction, selector: str = None, value: Any = None, **kwargs) -> Any:
        """
        执行命令
        
        Args:
            action (StepAction): 步骤动作
            selector (str, optional): 元素选择器
            value (Any, optional): 命令值
            **kwargs: 额外参数
        
        Returns:
            Any: 执行结果
        
        Raises:
            CommandNotFoundError: 命令未找到
            CommandExecutionError: 命令执行错误
        """
        pass
    
    def register_command(self, action: StepAction, command_class: Type[Command]) -> None:
        """
        注册命令
        
        Args:
            action (StepAction): 步骤动作
            command_class (Type[Command]): 命令类
        """
        pass
    
    def get_command_statistics(self) -> Dict[str, Any]:
        """
        获取命令统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
```

## 5. 变量管理API

### 5.1 VariableManager

变量管理器。

```python
class VariableManager:
    """变量管理器(单例)"""
    
    @classmethod
    def get_instance(cls) -> 'VariableManager':
        """
        获取单例实例
        
        Returns:
            VariableManager: 变量管理器实例
        """
        pass
    
    def set_variable(self, name: str, value: Any, scope: VariableScope = VariableScope.TEST_CASE) -> None:
        """
        设置变量
        
        Args:
            name (str): 变量名
            value (Any): 变量值
            scope (VariableScope): 变量作用域
        """
        pass
    
    def get_variable(self, name: str, default: Any = None, scope: VariableScope = None) -> Any:
        """
        获取变量
        
        Args:
            name (str): 变量名
            default (Any): 默认值
            scope (VariableScope, optional): 变量作用域
        
        Returns:
            Any: 变量值
        """
        pass
    
    def replace_variables(self, text: str) -> str:
        """
        替换文本中的变量
        
        Args:
            text (str): 包含变量的文本
        
        Returns:
            str: 替换后的文本
        """
        pass
    
    def evaluate_expression(self, expression: str) -> Any:
        """
        计算表达式
        
        Args:
            expression (str): 表达式
        
        Returns:
            Any: 计算结果
        """
        pass
    
    def clear_scope(self, scope: VariableScope) -> None:
        """
        清空指定作用域的变量
        
        Args:
            scope (VariableScope): 变量作用域
        """
        pass
    
    def get_all_variables(self, scope: VariableScope = None) -> Dict[str, Any]:
        """
        获取所有变量
        
        Args:
            scope (VariableScope, optional): 变量作用域
        
        Returns:
            Dict[str, Any]: 变量字典
        """
        pass
```

## 6. 页面对象API

### 6.1 BasePage

页面对象基类。

```python
class BasePage:
    """页面对象基类"""
    
    def __init__(self, page: Page, ui_helper: UIHelper):
        """
        初始化页面对象
        
        Args:
            page (Page): Playwright页面对象
            ui_helper (UIHelper): UI助手
        """
        pass
    
    def wait_for_load(self, timeout: int = 30000) -> None:
        """
        等待页面加载完成
        
        Args:
            timeout (int): 超时时间(毫秒)
        """
        pass
    
    def get_element(self, selector: str, timeout: int = None) -> Locator:
        """
        获取元素
        
        Args:
            selector (str): 元素选择器
            timeout (int, optional): 超时时间
        
        Returns:
            Locator: 元素定位器
        """
        pass
    
    def click_element(self, selector: str, **kwargs) -> None:
        """
        点击元素
        
        Args:
            selector (str): 元素选择器
            **kwargs: 额外参数
        """
        pass
    
    def fill_element(self, selector: str, value: str, **kwargs) -> None:
        """
        填写元素
        
        Args:
            selector (str): 元素选择器
            value (str): 填写值
            **kwargs: 额外参数
        """
        pass
    
    def get_text(self, selector: str) -> str:
        """
        获取元素文本
        
        Args:
            selector (str): 元素选择器
        
        Returns:
            str: 元素文本
        """
        pass
    
    def is_visible(self, selector: str) -> bool:
        """
        检查元素是否可见
        
        Args:
            selector (str): 元素选择器
        
        Returns:
            bool: 是否可见
        """
        pass
    
    def screenshot(self, filename: str = None, **kwargs) -> str:
        """
        截图
        
        Args:
            filename (str, optional): 文件名
            **kwargs: 额外参数
        
        Returns:
            str: 截图文件路径
        """
        pass
```

## 7. 工具类API

### 7.1 UIHelper

UI操作助手。

```python
class UIHelper:
    """UI操作助手"""
    
    def __init__(self, page: Page, config: Dict[str, Any]):
        """
        初始化UI助手
        
        Args:
            page (Page): Playwright页面对象
            config (Dict[str, Any]): 配置
        """
        pass
    
    def wait_for_selector(self, selector: str, timeout: int = None, state: str = "visible") -> Locator:
        """
        等待元素
        
        Args:
            selector (str): 元素选择器
            timeout (int, optional): 超时时间
            state (str): 元素状态
        
        Returns:
            Locator: 元素定位器
        """
        pass
    
    def safe_click(self, selector: str, **kwargs) -> bool:
        """
        安全点击(带重试)
        
        Args:
            selector (str): 元素选择器
            **kwargs: 额外参数
        
        Returns:
            bool: 是否成功
        """
        pass
    
    def safe_fill(self, selector: str, value: str, **kwargs) -> bool:
        """
        安全填写(带重试)
        
        Args:
            selector (str): 元素选择器
            value (str): 填写值
            **kwargs: 额外参数
        
        Returns:
            bool: 是否成功
        """
        pass
    
    def get_element_info(self, selector: str) -> Dict[str, Any]:
        """
        获取元素信息
        
        Args:
            selector (str): 元素选择器
        
        Returns:
            Dict[str, Any]: 元素信息
        """
        pass
    
    def highlight_element(self, selector: str, duration: int = 2000) -> None:
        """
        高亮元素
        
        Args:
            selector (str): 元素选择器
            duration (int): 高亮持续时间(毫秒)
        """
        pass
```

### 7.2 DataLoader

数据加载器。

```python
class DataLoader:
    """数据加载器"""
    
    @staticmethod
    def load_yaml(file_path: str) -> Dict[str, Any]:
        """
        加载YAML文件
        
        Args:
            file_path (str): 文件路径
        
        Returns:
            Dict[str, Any]: 数据字典
        
        Raises:
            FileNotFoundError: 文件未找到
            YAMLError: YAML格式错误
        """
        pass
    
    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """
        加载JSON文件
        
        Args:
            file_path (str): 文件路径
        
        Returns:
            Dict[str, Any]: 数据字典
        """
        pass
    
    @staticmethod
    def load_csv(file_path: str) -> List[Dict[str, Any]]:
        """
        加载CSV文件
        
        Args:
            file_path (str): 文件路径
        
        Returns:
            List[Dict[str, Any]]: 数据列表
        """
        pass
    
    @staticmethod
    def save_yaml(data: Dict[str, Any], file_path: str) -> None:
        """
        保存为YAML文件
        
        Args:
            data (Dict[str, Any]): 数据
            file_path (str): 文件路径
        """
        pass
```

## 8. 插件API

### 8.1 Plugin基类

插件基类。

```python
class Plugin(ABC):
    """插件基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化插件
        
        Args:
            config (Dict[str, Any]): 插件配置
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取插件名称
        
        Returns:
            str: 插件名称
        """
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """
        获取插件版本
        
        Returns:
            str: 插件版本
        """
        pass
    
    def initialize(self) -> None:
        """
        初始化插件
        """
        pass
    
    def cleanup(self) -> None:
        """
        清理插件资源
        """
        pass
    
    def on_test_start(self, test_case: TestCase) -> None:
        """
        测试开始事件
        
        Args:
            test_case (TestCase): 测试用例
        """
        pass
    
    def on_test_end(self, test_case: TestCase, result: TestCaseResult) -> None:
        """
        测试结束事件
        
        Args:
            test_case (TestCase): 测试用例
            result (TestCaseResult): 测试结果
        """
        pass
    
    def on_step_start(self, step: TestStep) -> None:
        """
        步骤开始事件
        
        Args:
            step (TestStep): 测试步骤
        """
        pass
    
    def on_step_end(self, step: TestStep, result: StepResult) -> None:
        """
        步骤结束事件
        
        Args:
            step (TestStep): 测试步骤
            result (StepResult): 步骤结果
        """
        pass
```

### 8.2 PluginManager

插件管理器。

```python
class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        """初始化插件管理器"""
        pass
    
    def register_plugin(self, plugin: Plugin) -> None:
        """
        注册插件
        
        Args:
            plugin (Plugin): 插件实例
        """
        pass
    
    def unregister_plugin(self, plugin_name: str) -> None:
        """
        注销插件
        
        Args:
            plugin_name (str): 插件名称
        """
        pass
    
    def get_plugin(self, plugin_name: str) -> Plugin:
        """
        获取插件
        
        Args:
            plugin_name (str): 插件名称
        
        Returns:
            Plugin: 插件实例
        """
        pass
    
    def get_all_plugins(self) -> List[Plugin]:
        """
        获取所有插件
        
        Returns:
            List[Plugin]: 插件列表
        """
        pass
    
    def initialize_plugins(self) -> None:
        """
        初始化所有插件
        """
        pass
    
    def cleanup_plugins(self) -> None:
        """
        清理所有插件
        """
        pass
```

## 9. 异常API

### 9.1 框架异常

框架定义的异常类。

```python
class TestFrameworkError(Exception):
    """测试框架基础异常"""
    pass

class TestConfigError(TestFrameworkError):
    """测试配置错误"""
    pass

class TestExecutionError(TestFrameworkError):
    """测试执行错误"""
    pass

class ElementNotFoundError(TestFrameworkError):
    """元素未找到错误"""
    pass

class TimeoutError(TestFrameworkError):
    """超时错误"""
    pass

class AssertionError(TestFrameworkError):
    """断言错误"""
    pass

class VariableNotFoundError(TestFrameworkError):
    """变量未找到错误"""
    pass

class ServiceNotFoundError(TestFrameworkError):
    """服务未找到错误"""
    pass

class CircularDependencyError(TestFrameworkError):
    """循环依赖错误"""
    pass

class CommandNotFoundError(TestFrameworkError):
    """命令未找到错误"""
    pass

class PluginError(TestFrameworkError):
    """插件错误"""
    pass
```

## 10. 枚举API

### 10.1 StepAction

步骤动作枚举。

```python
class StepAction(Enum):
    """步骤动作枚举"""
    
    # 基础操作
    GOTO = "goto"
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    HOVER = "hover"
    
    # 等待操作
    WAIT_FOR_SELECTOR = "wait_for_selector"
    WAIT_FOR_TEXT = "wait_for_text"
    WAIT_FOR_URL = "wait_for_url"
    WAIT_FOR_LOAD_STATE = "wait_for_load_state"
    
    # 断言操作
    ASSERT_TEXT = "assert_text"
    ASSERT_TEXT_CONTAINS = "assert_text_contains"
    ASSERT_VISIBLE = "assert_visible"
    ASSERT_NOT_EXISTS = "assert_not_exists"
    ASSERT_URL = "assert_url"
    ASSERT_TITLE = "assert_title"
    
    # 存储操作
    STORE_TEXT = "store_text"
    STORE_ATTRIBUTE = "store_attribute"
    STORE_VARIABLE = "store_variable"
    
    # 其他操作
    SCREENSHOT = "screenshot"
    SCROLL = "scroll"
    REFRESH = "refresh"
    NAVIGATE_BACK = "navigate_back"
    NAVIGATE_FORWARD = "navigate_forward"
```

### 10.2 VariableScope

变量作用域枚举。

```python
class VariableScope(Enum):
    """变量作用域枚举"""
    
    GLOBAL = "global"           # 全局作用域
    TEST_CASE = "test_case"     # 测试用例作用域
    MODULE = "module"           # 模块作用域
    STEP = "step"               # 步骤作用域
    TEMP = "temp"               # 临时作用域
```

### 10.3 ServiceScope

服务作用域枚举。

```python
class ServiceScope(Enum):
    """服务作用域枚举"""
    
    SINGLETON = "singleton"     # 单例
    TRANSIENT = "transient"     # 瞬态
    SCOPED = "scoped"           # 作用域
```

## 11. 配置API

### 11.1 ConfigManager

配置管理器。

```python
class ConfigManager:
    """配置管理器"""
    
    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """
        获取单例实例
        
        Returns:
            ConfigManager: 配置管理器实例
        """
        pass
    
    def load_config(self, config_path: str) -> None:
        """
        加载配置文件
        
        Args:
            config_path (str): 配置文件路径
        """
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key (str): 配置键(支持点号分隔)
            default (Any): 默认值
        
        Returns:
            Any: 配置值
        """
        pass
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key (str): 配置键
            value (Any): 配置值
        """
        pass
    
    def get_env_config(self, key: str, default: Any = None) -> Any:
        """
        获取环境特定配置
        
        Args:
            key (str): 配置键
            default (Any): 默认值
        
        Returns:
            Any: 配置值
        """
        pass
    
    def validate(self) -> List[str]:
        """
        验证配置
        
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        pass
```

## 12. 使用示例

### 12.1 基础使用

```python
from src.core.test_runner import TestRunner
from src.core.config_manager import ConfigManager

# 初始化配置
config = ConfigManager.get_instance()
config.load_config("config/test_config.yaml")

# 创建测试运行器
runner = TestRunner()

# 运行测试套件
result = runner.run_test_suite(
    test_path="test_data/demo/cases/demo.yaml",
    browser="chromium",
    headless=False
)

# 输出结果
print(f"测试结果: {result.success_rate:.2%}")
print(f"执行时间: {result.execution_time}")
```

### 12.2 自定义命令

```python
from src.automation.commands.base_command import Command
from src.automation.action_types import StepAction

class CustomCommand(Command):
    """自定义命令"""
    
    def execute(self, selector: str = None, value: Any = None, **kwargs) -> Any:
        # 实现自定义逻辑
        print(f"执行自定义命令: {value}")
        return True
    
    def validate_arguments(self, selector: str = None, value: Any = None, **kwargs) -> None:
        if not value:
            raise ArgumentValidationError("value参数不能为空")

# 注册自定义命令
from src.automation.commands.command_executor import CommandExecutor

executor = CommandExecutor(service_container)
executor.register_command(StepAction.CUSTOM_ACTION, CustomCommand)
```

### 12.3 自定义插件

```python
from src.plugins.base_plugin import Plugin

class CustomPlugin(Plugin):
    """自定义插件"""
    
    def get_name(self) -> str:
        return "CustomPlugin"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def on_test_start(self, test_case: TestCase) -> None:
        print(f"开始执行测试: {test_case.name}")
    
    def on_test_end(self, test_case: TestCase, result: TestCaseResult) -> None:
        print(f"测试完成: {test_case.name}, 结果: {result.status}")

# 注册插件
from src.plugins.plugin_manager import PluginManager

plugin_manager = PluginManager()
plugin_manager.register_plugin(CustomPlugin({}))
```

### 12.4 服务注册

```python
from src.core.container import ServiceContainer

# 创建服务容器
container = ServiceContainer()

# 注册服务
container.register_singleton(ConfigManager, ConfigManager.get_instance)
container.register(UIHelper, UIHelper)
container.register_factory(DatabaseConnection, lambda: create_db_connection())

# 解析服务
config = container.resolve(ConfigManager)
ui_helper = container.resolve(UIHelper)
```

## 13. 扩展指南

### 13.1 添加新的步骤动作

1. 在 `StepAction` 枚举中添加新动作
2. 创建对应的命令类
3. 注册命令到命令执行器
4. 更新文档和测试

### 13.2 创建自定义页面对象

```python
from src.core.base_page import BasePage

class LoginPage(BasePage):
    """登录页面"""
    
    # 元素选择器
    USERNAME_INPUT = "#username"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "#login-btn"
    
    def login(self, username: str, password: str) -> None:
        """登录操作"""
        self.fill_element(self.USERNAME_INPUT, username)
        self.fill_element(self.PASSWORD_INPUT, password)
        self.click_element(self.LOGIN_BUTTON)
        self.wait_for_load()
```

### 13.3 集成外部系统

```python
from src.integrations.base_integration import BaseIntegration

class JiraIntegration(BaseIntegration):
    """Jira集成"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.jira_client = self._create_jira_client()
    
    def report_test_result(self, test_case: TestCase, result: TestCaseResult) -> None:
        """上报测试结果到Jira"""
        # 实现Jira集成逻辑
        pass
```

## 14. 总结

本API参考文档涵盖了框架的所有核心API，包括：

1. ✅ **核心API**: TestRunner、TestCaseExecutor、StepExecutor
2. ✅ **数据模型**: TestCase、TestStep、TestResult
3. ✅ **服务容器**: 依赖注入和服务管理
4. ✅ **命令系统**: 命令基类和执行器
5. ✅ **变量管理**: 多作用域变量管理
6. ✅ **页面对象**: 页面操作基类
7. ✅ **工具类**: UI助手和数据加载器
8. ✅ **插件系统**: 插件基类和管理器
9. ✅ **异常处理**: 框架异常定义
10. ✅ **配置管理**: 配置加载和管理
11. ✅ **使用示例**: 实际使用代码示例
12. ✅ **扩展指南**: 框架扩展方法

通过本文档，开发者可以：
- 理解框架的API设计
- 扩展框架功能
- 集成到其他系统
- 创建自定义组件
- 优化测试流程

建议开发者在使用API时参考具体的实现代码和单元测试，以获得更详细的使用方法和最佳实践。