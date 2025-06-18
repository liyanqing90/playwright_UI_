# 插件开发指南

## 概述

本指南将帮助开发者了解如何为本项目开发插件，包括插件的基本结构、开发流程、最佳实践和调试技巧。

## 快速开始

### 1. 创建插件目录结构

```
plugins/
└── my_plugin/
    ├── __init__.py
    ├── plugin.py          # 主插件文件
    ├── config.yaml        # 插件配置
    ├── requirements.txt   # 依赖声明
    └── README.md         # 插件说明
```

### 2. 实现基础插件

```python
# plugins/my_plugin/plugin.py
from src.core.plugin_system.base import PluginInterface
from src.core.service_container import ServiceContainer
from typing import Dict, Any

class MyPlugin(PluginInterface):
    """示例插件"""
    
    def __init__(self):
        self.name = "my_plugin"
        self.version = "1.0.0"
        self.container = None
        self.logger = None
    
    def get_name(self) -> str:
        return self.name
    
    def get_version(self) -> str:
        return self.version
    
    def initialize(self, container: ServiceContainer) -> None:
        """插件初始化"""
        self.container = container
        self.logger = container.resolve('Logger')
        self.logger.info(f"Plugin {self.name} initialized")
    
    def cleanup(self) -> None:
        """插件清理"""
        if self.logger:
            self.logger.info(f"Plugin {self.name} cleaned up")
```

### 3. 配置插件

```yaml
# plugins/my_plugin/config.yaml
plugin:
  name: my_plugin
  version: "1.0.0"
  description: "示例插件"
  author: "Your Name"
  
config:
  enabled: true
  priority: normal
  dependencies: []
  
settings:
  debug_mode: false
  cache_enabled: true
```

## 插件类型

### 1. 命令插件

用于扩展测试步骤命令的插件：

```python
from src.core.plugin_system.interfaces import CommandPlugin

class MyCommandPlugin(CommandPlugin):
    """命令插件示例"""
    
    def get_commands(self) -> List[str]:
        """返回插件提供的命令列表"""
        return ['my_command', 'my_advanced_command']
    
    def execute_command(self, command: str, **kwargs) -> Any:
        """执行命令"""
        if command == 'my_command':
            return self._execute_my_command(**kwargs)
        elif command == 'my_advanced_command':
            return self._execute_advanced_command(**kwargs)
        else:
            raise ValueError(f"Unknown command: {command}")
    
    def _execute_my_command(self, **kwargs):
        """执行自定义命令"""
        self.logger.info("Executing my command")
        # 命令实现逻辑
        return {"status": "success", "result": "Command executed"}
```

### 2. 生命周期插件

参与测试生命周期的插件：

```python
from src.core.plugin_system.interfaces import LifecyclePlugin

class MyLifecyclePlugin(LifecyclePlugin):
    """生命周期插件示例"""
    
    def __init__(self):
        super().__init__()
        self.is_started = False
    
    def start(self) -> bool:
        """启动插件"""
        try:
            # 启动逻辑
            self.logger.info("Plugin starting...")
            self.is_started = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to start plugin: {e}")
            return False
    
    def stop(self) -> bool:
        """停止插件"""
        try:
            # 停止逻辑
            self.logger.info("Plugin stopping...")
            self.is_started = False
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop plugin: {e}")
            return False
    
    def is_running(self) -> bool:
        """检查插件是否运行中"""
        return self.is_started
    
    def on_test_start(self, test_info: Dict[str, Any]):
        """测试开始时调用"""
        self.logger.info(f"Test started: {test_info.get('name')}")
    
    def on_test_end(self, test_info: Dict[str, Any]):
        """测试结束时调用"""
        self.logger.info(f"Test ended: {test_info.get('name')}")
```

### 3. 可配置插件

支持动态配置的插件：

```python
from src.core.plugin_system.interfaces import ConfigurablePlugin

class MyConfigurablePlugin(ConfigurablePlugin):
    """可配置插件示例"""
    
    def __init__(self):
        super().__init__()
        self.config = {
            'timeout': 30,
            'retry_count': 3,
            'debug_mode': False
        }
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """配置插件"""
        try:
            # 验证配置
            if 'timeout' in config and config['timeout'] <= 0:
                raise ValueError("Timeout must be positive")
            
            # 更新配置
            self.config.update(config)
            self.logger.info(f"Plugin configured: {self.config}")
            return True
        except Exception as e:
            self.logger.error(f"Configuration failed: {e}")
            return False
    
    def get_configuration(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.copy()
```

## 服务依赖

### 使用核心服务

```python
class MyServiceDependentPlugin(PluginInterface):
    """依赖服务的插件"""

    def initialize(self, container: ServiceContainer) -> None:
        """初始化并获取依赖服务"""
        super().initialize(container)

        # 获取核心服务
        self.element_service = container.resolve('ElementService')
        self.navigation_service = container.resolve('NavigationService')
        self.assertion_service = container.resolve('AssertionService')
        self.config_loader = container.resolve('ConfigLoader')

        # 获取可选服务
        try:
            self.performance_monitor = container.resolve('PerformanceMonitor')
        except Exception:
            self.performance_monitor = None

    def execute_with_services(self, **kwargs):
        """使用服务执行操作"""
        # 使用元素服务
        element = self.element_service.find_element("#my-button")

        # 使用导航服务
        self.navigation_service.navigate_to("https://example.com")

        # 使用断言服务
        self.assertion_service.assert_element_visible(element)
```

### 注册自定义服务

```python
class MyServicePlugin(PluginInterface):
    """提供服务的插件"""
    
    def initialize(self, container: ServiceContainer) -> None:
        super().initialize(container)
        
        # 注册自定义服务
        container.register_singleton('MyCustomService', self._create_custom_service)
        
        # 注册工厂服务
        container.register_factory('MyFactoryService', self._create_factory_service)
    
    def _create_custom_service(self):
        """创建自定义服务"""
        return MyCustomService(self.logger)
    
    def _create_factory_service(self):
        """创建工厂服务"""
        return MyFactoryService()
```

## 事件处理

### 监听系统事件

```python
class MyEventPlugin(PluginInterface):
    """事件处理插件"""
    
    def initialize(self, container: ServiceContainer) -> None:
        super().initialize(container)
        
        # 获取事件系统
        self.event_system = container.resolve('EventSystem')
        
        # 注册事件监听器
        self.event_system.register_listener('test.started', self.on_test_started)
        self.event_system.register_listener('test.failed', self.on_test_failed)
        self.event_system.register_listener('step.executed', self.on_step_executed)
    
    def on_test_started(self, **kwargs):
        """测试开始事件处理"""
        test_name = kwargs.get('test_name')
        self.logger.info(f"Test started: {test_name}")
    
    def on_test_failed(self, **kwargs):
        """测试失败事件处理"""
        test_name = kwargs.get('test_name')
        error = kwargs.get('error')
        self.logger.error(f"Test failed: {test_name}, Error: {error}")
    
    def on_step_executed(self, **kwargs):
        """步骤执行事件处理"""
        step_name = kwargs.get('step_name')
        duration = kwargs.get('duration')
        self.logger.debug(f"Step executed: {step_name}, Duration: {duration}ms")
```

### 发送自定义事件

```python
class MyEventEmitterPlugin(PluginInterface):
    """事件发送插件"""
    
    def execute_with_events(self, **kwargs):
        """执行操作并发送事件"""
        # 发送开始事件
        self.event_system.emit_event('plugin.operation.started', 
                                    plugin_name=self.get_name(),
                                    operation='custom_operation')
        
        try:
            # 执行操作
            result = self._perform_operation(**kwargs)
            
            # 发送成功事件
            self.event_system.emit_event('plugin.operation.completed',
                                        plugin_name=self.get_name(),
                                        operation='custom_operation',
                                        result=result)
            return result
            
        except Exception as e:
            # 发送失败事件
            self.event_system.emit_event('plugin.operation.failed',
                                        plugin_name=self.get_name(),
                                        operation='custom_operation',
                                        error=str(e))
            raise
```

## 配置管理

### 读取配置

```python
class MyConfigurablePlugin(PluginInterface):
    """配置管理插件"""
    
    def initialize(self, container: ServiceContainer) -> None:
        super().initialize(container)
        
        # 获取配置加载器
        self.config_loader = container.resolve('ConfigLoader')
        
        # 加载插件配置
        self.plugin_config = self._load_plugin_config()
    
    def _load_plugin_config(self) -> Dict[str, Any]:
        """加载插件配置"""
        try:
            # 从配置文件加载
            config = self.config_loader.load_config(f'plugins/{self.get_name()}/config.yaml')
            
            # 合并默认配置
            default_config = self._get_default_config()
            merged_config = {**default_config, **config.get('config', {})}
            
            return merged_config
        except Exception as e:
            self.logger.warning(f"Failed to load plugin config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'enabled': True,
            'timeout': 30,
            'retry_count': 3,
            'debug_mode': False
        }
```

### 动态配置更新

```python
class MyDynamicConfigPlugin(ConfigurablePlugin):
    """动态配置插件"""
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """动态更新配置"""
        try:
            # 验证配置
            self._validate_config(config)
            
            # 备份当前配置
            old_config = self.config.copy()
            
            # 更新配置
            self.config.update(config)
            
            # 应用配置变更
            self._apply_config_changes(old_config, self.config)
            
            self.logger.info(f"Configuration updated: {config}")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration update failed: {e}")
            return False
    
    def _validate_config(self, config: Dict[str, Any]):
        """验证配置"""
        if 'timeout' in config and config['timeout'] <= 0:
            raise ValueError("Timeout must be positive")
        
        if 'retry_count' in config and config['retry_count'] < 0:
            raise ValueError("Retry count must be non-negative")
    
    def _apply_config_changes(self, old_config: Dict, new_config: Dict):
        """应用配置变更"""
        # 检查关键配置变更
        if old_config.get('timeout') != new_config.get('timeout'):
            self._update_timeout(new_config['timeout'])
        
        if old_config.get('debug_mode') != new_config.get('debug_mode'):
            self._toggle_debug_mode(new_config['debug_mode'])
```

## 错误处理

### 异常处理最佳实践

```python
class MyRobustPlugin(PluginInterface):
    """健壮的插件实现"""
    
    def execute_operation(self, **kwargs):
        """执行操作（带完整错误处理）"""
        operation_id = kwargs.get('operation_id', 'unknown')
        
        try:
            # 参数验证
            self._validate_parameters(**kwargs)
            
            # 执行前检查
            self._pre_execution_check()
            
            # 执行主要逻辑
            result = self._execute_main_logic(**kwargs)
            
            # 执行后验证
            self._post_execution_validation(result)
            
            return result
            
        except ValidationError as e:
            self.logger.error(f"Parameter validation failed for operation {operation_id}: {e}")
            raise PluginExecutionError(f"Invalid parameters: {e}")
            
        except ResourceNotAvailableError as e:
            self.logger.warning(f"Resource not available for operation {operation_id}: {e}")
            # 尝试恢复
            if self._try_recover_resource():
                return self.execute_operation(**kwargs)  # 重试
            raise
            
        except Exception as e:
            self.logger.error(f"Unexpected error in operation {operation_id}: {e}")
            # 清理资源
            self._cleanup_on_error()
            raise PluginExecutionError(f"Operation failed: {e}")
    
    def _validate_parameters(self, **kwargs):
        """参数验证"""
        required_params = ['param1', 'param2']
        for param in required_params:
            if param not in kwargs:
                raise ValidationError(f"Missing required parameter: {param}")
    
    def _try_recover_resource(self) -> bool:
        """尝试恢复资源"""
        try:
            # 资源恢复逻辑
            self.logger.info("Attempting resource recovery...")
            # ...
            return True
        except Exception:
            return False
    
    def _cleanup_on_error(self):
        """错误时清理"""
        try:
            # 清理逻辑
            pass
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
```

### 自定义异常

```python
# plugins/my_plugin/exceptions.py
class PluginError(Exception):
    """插件基础异常"""
    pass

class PluginInitializationError(PluginError):
    """插件初始化异常"""
    pass

class PluginExecutionError(PluginError):
    """插件执行异常"""
    pass

class ValidationError(PluginError):
    """参数验证异常"""
    pass

class ResourceNotAvailableError(PluginError):
    """资源不可用异常"""
    pass
```

## 测试

### 单元测试

```python
# tests/test_my_plugin.py
import unittest
from unittest.mock import Mock, patch
from plugins.my_plugin.plugin import MyPlugin
from src.core.service_container import ServiceContainer

class TestMyPlugin(unittest.TestCase):
    """插件单元测试"""
    
    def setUp(self):
        """测试设置"""
        self.container = Mock(spec=ServiceContainer)
        self.logger = Mock()
        self.container.resolve.return_value = self.logger
        
        self.plugin = MyPlugin()
        self.plugin.initialize(self.container)
    
    def test_plugin_initialization(self):
        """测试插件初始化"""
        self.assertEqual(self.plugin.get_name(), "my_plugin")
        self.assertEqual(self.plugin.get_version(), "1.0.0")
        self.assertIsNotNone(self.plugin.logger)
    
    def test_plugin_execution(self):
        """测试插件执行"""
        # 准备测试数据
        test_params = {'param1': 'value1', 'param2': 'value2'}
        
        # 执行测试
        result = self.plugin.execute_operation(**test_params)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'success')
    
    def test_plugin_error_handling(self):
        """测试错误处理"""
        # 测试参数验证错误
        with self.assertRaises(ValidationError):
            self.plugin.execute_operation()
    
    @patch('plugins.my_plugin.plugin.external_service')
    def test_plugin_with_external_dependency(self, mock_service):
        """测试外部依赖"""
        # 模拟外部服务
        mock_service.call_api.return_value = {'data': 'test'}
        
        # 执行测试
        result = self.plugin.call_external_service()
        
        # 验证调用
        mock_service.call_api.assert_called_once()
        self.assertEqual(result['data'], 'test')
```

### 集成测试

```python
# tests/integration/test_plugin_integration.py
import unittest
from src.core.service_container import ServiceContainer
from src.core.plugin_system.manager import PluginManager
from plugins.my_plugin.plugin import MyPlugin

class TestPluginIntegration(unittest.TestCase):
    """插件集成测试"""
    
    def setUp(self):
        """集成测试设置"""
        self.container = ServiceContainer()
        self.plugin_manager = PluginManager(self.container)
        
        # 注册必要的服务
        self._register_core_services()
    
    def _register_core_services(self):
        """注册核心服务"""
        from src.core.services.logger import Logger
        from src.core.services.config_loader import ConfigLoader
        
        self.container.register_singleton('Logger', Logger)
        self.container.register_singleton('ConfigLoader', ConfigLoader)
    
    def test_plugin_loading_and_execution(self):
        """测试插件加载和执行"""
        # 加载插件
        success = self.plugin_manager.load_plugin('plugins/my_plugin')
        self.assertTrue(success)
        
        # 获取插件
        plugin = self.plugin_manager.get_plugin('my_plugin')
        self.assertIsNotNone(plugin)
        
        # 执行插件功能
        result = plugin.execute_operation(param1='test', param2='value')
        self.assertIsNotNone(result)
    
    def test_plugin_service_integration(self):
        """测试插件与服务的集成"""
        # 加载插件
        self.plugin_manager.load_plugin('plugins/my_plugin')
        plugin = self.plugin_manager.get_plugin('my_plugin')
        
        # 测试服务依赖
        self.assertIsNotNone(plugin.logger)
        self.assertIsNotNone(plugin.container)
```

## 性能优化

### 缓存机制

```python
from functools import lru_cache
from typing import Any, Dict

class MyOptimizedPlugin(PluginInterface):
    """性能优化的插件"""
    
    def __init__(self):
        super().__init__()
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    @lru_cache(maxsize=128)
    def expensive_operation(self, param: str) -> Any:
        """昂贵操作（带缓存）"""
        self.logger.debug(f"Performing expensive operation for: {param}")
        # 模拟昂贵操作
        import time
        time.sleep(0.1)
        return f"result_for_{param}"
    
    def cached_operation(self, key: str, **kwargs) -> Any:
        """自定义缓存操作"""
        if key in self.cache:
            self.cache_hits += 1
            return self.cache[key]
        
        self.cache_misses += 1
        result = self._perform_operation(**kwargs)
        self.cache[key] = result
        return result
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': round(hit_rate, 2)
        }
```

### 异步操作

```python
import asyncio
from typing import Awaitable

class MyAsyncPlugin(PluginInterface):
    """异步插件"""
    
    def __init__(self):
        super().__init__()
        self.loop = None
    
    def initialize(self, container: ServiceContainer) -> None:
        super().initialize(container)
        # 获取或创建事件循环
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
    
    async def async_operation(self, **kwargs) -> Any:
        """异步操作"""
        self.logger.info("Starting async operation")
        
        # 并发执行多个任务
        tasks = [
            self._async_task_1(**kwargs),
            self._async_task_2(**kwargs),
            self._async_task_3(**kwargs)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        successful_results = [r for r in results if not isinstance(r, Exception)]
        errors = [r for r in results if isinstance(r, Exception)]
        
        if errors:
            self.logger.warning(f"Some async tasks failed: {errors}")
        
        return successful_results
    
    def sync_wrapper(self, **kwargs) -> Any:
        """同步包装器"""
        if self.loop.is_running():
            # 如果循环正在运行，创建任务
            future = asyncio.ensure_future(self.async_operation(**kwargs))
            return future
        else:
            # 如果循环未运行，直接运行
            return self.loop.run_until_complete(self.async_operation(**kwargs))
    
    async def _async_task_1(self, **kwargs):
        """异步任务1"""
        await asyncio.sleep(0.1)  # 模拟异步操作
        return "task1_result"
    
    async def _async_task_2(self, **kwargs):
        """异步任务2"""
        await asyncio.sleep(0.2)  # 模拟异步操作
        return "task2_result"
    
    async def _async_task_3(self, **kwargs):
        """异步任务3"""
        await asyncio.sleep(0.15)  # 模拟异步操作
        return "task3_result"
```

## 调试和监控

### 调试支持

```python
class MyDebuggablePlugin(PluginInterface):
    """可调试的插件"""
    
    def __init__(self):
        super().__init__()
        self.debug_mode = False
        self.execution_trace = []
    
    def enable_debug(self, enabled: bool = True):
        """启用/禁用调试模式"""
        self.debug_mode = enabled
        if enabled:
            self.logger.setLevel('DEBUG')
        else:
            self.logger.setLevel('INFO')
    
    def execute_with_debug(self, **kwargs):
        """带调试信息的执行"""
        if self.debug_mode:
            self._trace_execution('start', kwargs)
        
        try:
            result = self._execute_main_logic(**kwargs)
            
            if self.debug_mode:
                self._trace_execution('success', {'result': result})
            
            return result
            
        except Exception as e:
            if self.debug_mode:
                self._trace_execution('error', {'error': str(e)})
            raise
    
    def _trace_execution(self, event: str, data: Dict[str, Any]):
        """记录执行轨迹"""
        import time
        trace_entry = {
            'timestamp': time.time(),
            'event': event,
            'data': data
        }
        self.execution_trace.append(trace_entry)
        self.logger.debug(f"Trace: {trace_entry}")
    
    def get_execution_trace(self) -> List[Dict[str, Any]]:
        """获取执行轨迹"""
        return self.execution_trace.copy()
    
    def clear_execution_trace(self):
        """清除执行轨迹"""
        self.execution_trace.clear()
```

### 性能监控

```python
import time
from contextlib import contextmanager

class MyMonitoredPlugin(PluginInterface):
    """带性能监控的插件"""
    
    def __init__(self):
        super().__init__()
        self.performance_stats = {
            'total_executions': 0,
            'total_time': 0,
            'average_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'error_count': 0
        }
    
    @contextmanager
    def performance_monitor(self, operation_name: str):
        """性能监控上下文管理器"""
        start_time = time.time()
        try:
            yield
            # 成功执行
            execution_time = time.time() - start_time
            self._update_performance_stats(execution_time)
            self.logger.debug(f"Operation {operation_name} completed in {execution_time:.3f}s")
            
        except Exception as e:
            # 执行失败
            execution_time = time.time() - start_time
            self.performance_stats['error_count'] += 1
            self.logger.error(f"Operation {operation_name} failed after {execution_time:.3f}s: {e}")
            raise
    
    def _update_performance_stats(self, execution_time: float):
        """更新性能统计"""
        stats = self.performance_stats
        stats['total_executions'] += 1
        stats['total_time'] += execution_time
        stats['average_time'] = stats['total_time'] / stats['total_executions']
        stats['min_time'] = min(stats['min_time'], execution_time)
        stats['max_time'] = max(stats['max_time'], execution_time)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = self.performance_stats.copy()
        if stats['min_time'] == float('inf'):
            stats['min_time'] = 0
        return stats
    
    def execute_monitored_operation(self, **kwargs):
        """带监控的操作执行"""
        with self.performance_monitor('main_operation'):
            return self._execute_main_logic(**kwargs)
```

## 最佳实践

### 1. 插件设计原则

- **单一职责**：每个插件应该专注于一个特定的功能领域
- **松耦合**：插件之间应该尽量减少直接依赖
- **高内聚**：插件内部的组件应该紧密协作
- **可配置性**：提供灵活的配置选项
- **错误隔离**：插件错误不应影响核心功能

### 2. 代码质量

- **文档完整**：提供详细的API文档和使用示例
- **测试覆盖**：确保充分的单元测试和集成测试
- **代码规范**：遵循项目的代码风格指南
- **性能考虑**：避免不必要的资源消耗
- **安全性**：验证输入参数，防止安全漏洞

### 3. 部署和维护

- **版本管理**：使用语义化版本号
- **向后兼容**：尽量保持API的向后兼容性
- **渐进式更新**：支持插件的热更新
- **监控告警**：提供运行状态监控
- **文档更新**：及时更新文档和变更日志

## 故障排除

### 常见问题

1. **插件加载失败**
    - 检查插件目录结构
    - 验证配置文件格式
    - 查看依赖是否满足

2. **服务依赖问题**
    - 确认服务已注册
    - 检查服务名称拼写
    - 验证服务初始化顺序

3. **配置问题**
    - 验证配置文件语法
    - 检查配置参数类型
    - 确认配置文件路径

4. **性能问题**
    - 使用性能监控工具
    - 检查缓存策略
    - 优化算法复杂度

### 调试技巧

1. **启用详细日志**
2. **使用调试模式**
3. **添加性能监控**
4. **单步调试插件代码**
5. **检查插件状态和配置**

通过遵循本指南，您可以开发出高质量、可维护的插件，为项目提供强大的扩展能力。