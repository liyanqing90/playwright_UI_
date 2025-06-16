# 插件系统架构

## 概述

本项目采用分层架构与插件系统相结合的设计，实现了核心功能与扩展功能的清晰分离，提供了强大的可扩展性和模块化能力。

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (Application Layer)                │
├─────────────────────────────────────────────────────────────┤
│                    插件层 (Plugin Layer)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │ 数据生成插件 │ │ 网络操作插件 │ │ 报告处理插件 │ │   ...   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    服务层 (Service Layer)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │ 元素服务    │ │ 导航服务    │ │ 断言服务    │ │   ...   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    核心层 (Core Layer)                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │ 服务容器    │ │ 配置管理    │ │ 日志系统    │ │   ...   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 分层职责

### 核心层 (Core Layer)

**职责**：提供基础设施和底层服务

**组件**：
- **服务容器** (`ServiceContainer`) - 依赖注入和服务管理
- **配置管理** (`ConfigLoader`) - 配置文件加载和管理
- **日志系统** (`Logger`) - 统一的日志记录
- **异常处理** (`ExceptionHandler`) - 全局异常处理
- **性能监控** (`PerformanceMonitor`) - 基础性能指标收集

**特点**：
- 稳定性要求高，变更频率低
- 为上层提供基础设施支撑
- 不包含业务逻辑

### 服务层 (Service Layer)

**职责**：提供核心业务服务

**组件**：
- **元素服务** (`ElementService`) - 页面元素操作
- **导航服务** (`NavigationService`) - 页面导航功能
- **断言服务** (`AssertionService`) - 基础断言功能
- **等待服务** (`WaitService`) - 等待和同步功能
- **变量服务** (`VariableService`) - 变量管理

**特点**：
- 提供可复用的业务服务
- 通过依赖注入获取核心层服务
- 为插件层提供标准化接口

### 插件层 (Plugin Layer)

**职责**：实现扩展功能和高级特性

**组件**：
- **数据生成插件** - 测试数据生成
- **网络操作插件** - 网络请求监控
- **报告处理插件** - 测试报告生成
- **表达式计算插件** - 复杂表达式计算
- **通知插件** - 结果通知
- **文件操作插件** - 文件系统操作
- **性能管理插件** - 高级性能分析

**特点**：
- 可选加载，按需使用
- 独立开发和部署
- 可以依赖服务层提供的服务

## 插件系统设计

### 插件接口体系

```python
# 基础插件接口
class PluginInterface(ABC):
    @abstractmethod
    def get_name(self) -> str: ...
    
    @abstractmethod
    def get_version(self) -> str: ...
    
    @abstractmethod
    def initialize(self, container) -> None: ...

# 可配置插件接口
class ConfigurablePlugin(PluginInterface):
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> bool: ...
    
    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]: ...

# 生命周期插件接口
class LifecyclePlugin(PluginInterface):
    @abstractmethod
    def start(self) -> bool: ...
    
    @abstractmethod
    def stop(self) -> bool: ...
    
    @abstractmethod
    def is_running(self) -> bool: ...

# 命令插件接口
class CommandPlugin(PluginInterface):
    @abstractmethod
    def get_commands(self) -> List[str]: ...
    
    @abstractmethod
    def execute_command(self, command: str, **kwargs) -> Any: ...
```

### 插件管理器

```python
class PluginManager:
    """插件管理器 - 负责插件的生命周期管理"""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_configs: Dict[str, Dict] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
    
    def discover_plugins(self, plugin_dir: str) -> List[Dict]:
        """发现插件"""
        
    def load_plugin(self, plugin_path: str) -> bool:
        """加载插件"""
        
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        
    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        
    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
```

### 插件状态管理

```python
class PluginStatus(Enum):
    """插件状态枚举"""
    UNLOADED = "unloaded"      # 未加载
    LOADING = "loading"        # 加载中
    LOADED = "loaded"          # 已加载
    INITIALIZING = "initializing"  # 初始化中
    ACTIVE = "active"          # 活跃状态
    STOPPING = "stopping"      # 停止中
    STOPPED = "stopped"        # 已停止
    ERROR = "error"            # 错误状态

class PluginPriority(Enum):
    """插件优先级"""
    CRITICAL = 1    # 关键插件
    HIGH = 2        # 高优先级
    NORMAL = 3      # 普通优先级
    LOW = 4         # 低优先级
```

## 依赖注入集成

### 服务注册

```python
# 核心服务注册
container.register_singleton(ElementService)
container.register_singleton(NavigationService)
container.register_singleton(AssertionService)

# 插件服务注册
container.register_transient(DataGeneratorPlugin)
container.register_transient(NetworkOperationsPlugin)
```

### 插件依赖解析

```python
class Plugin(PluginInterface):
    def __init__(self, container: ServiceContainer):
        # 插件可以依赖核心服务
        self.element_service = container.resolve(ElementService)
        self.config_loader = container.resolve(ConfigLoader)
        self.logger = container.resolve(Logger)
```

## 配置管理

### 插件配置结构

```yaml
# config/plugins.yaml
plugins:
  enabled:
    - data_generator
    - network_operations
    - report_handler
  
  disabled:
    - notification  # 可选禁用
  
  search_paths:
    - "plugins/core"
    - "plugins/commands"
    - "plugins/third_party"
  
  load_order:
    - data_generator    # 优先加载
    - expression_evaluator
    - network_operations
```

### 插件特定配置

```yaml
# plugins/data_generator/config.yaml
plugin:
  name: data_generator
  version: "1.0.0"
  description: "测试数据生成插件"
  
config:
  default_locale: "zh_CN"
  cache_size: 1000
  providers:
    - faker
    - custom
```

## 性能优化

### 延迟加载

```python
class LazyPluginLoader:
    """延迟加载插件"""
    
    def __init__(self):
        self._plugin_registry = {}
        self._loaded_plugins = {}
    
    def register_plugin(self, name: str, loader: Callable):
        """注册插件加载器"""
        self._plugin_registry[name] = loader
    
    def get_plugin(self, name: str) -> PluginInterface:
        """获取插件（按需加载）"""
        if name not in self._loaded_plugins:
            loader = self._plugin_registry.get(name)
            if loader:
                self._loaded_plugins[name] = loader()
        return self._loaded_plugins.get(name)
```

### 插件缓存

```python
class PluginCache:
    """插件缓存管理"""
    
    def __init__(self, max_size: int = 100):
        self.cache = LRUCache(max_size)
        self.hit_count = 0
        self.miss_count = 0
    
    def get_plugin_result(self, plugin_name: str, method: str, args: tuple):
        """获取缓存的插件执行结果"""
        cache_key = f"{plugin_name}:{method}:{hash(args)}"
        
        if cache_key in self.cache:
            self.hit_count += 1
            return self.cache[cache_key]
        
        self.miss_count += 1
        return None
```

## 错误处理和隔离

### 插件异常隔离

```python
class PluginExecutor:
    """插件执行器 - 提供异常隔离"""
    
    def execute_plugin_method(self, plugin: PluginInterface, 
                            method_name: str, *args, **kwargs):
        """安全执行插件方法"""
        try:
            method = getattr(plugin, method_name)
            return method(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Plugin {plugin.get_name()} method {method_name} failed: {e}")
            # 插件错误不影响核心功能
            return None
```

### 插件健康检查

```python
class PluginHealthChecker:
    """插件健康检查"""
    
    def check_plugin_health(self, plugin: PluginInterface) -> bool:
        """检查插件健康状态"""
        try:
            # 检查插件基本功能
            if not plugin.get_name():
                return False
            
            # 检查插件状态
            if hasattr(plugin, 'get_plugin_status'):
                status = plugin.get_plugin_status()
                return status in [PluginStatus.ACTIVE, PluginStatus.LOADED]
            
            return True
        except Exception:
            return False
```

## 扩展机制

### 事件系统

```python
class PluginEventSystem:
    """插件事件系统"""
    
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = defaultdict(list)
    
    def register_listener(self, event_type: str, listener: Callable):
        """注册事件监听器"""
        self.listeners[event_type].append(listener)
    
    def emit_event(self, event_type: str, **kwargs):
        """触发事件"""
        for listener in self.listeners[event_type]:
            try:
                listener(**kwargs)
            except Exception as e:
                self.logger.error(f"Event listener failed: {e}")
```

### 插件通信

```python
class PluginCommunicator:
    """插件间通信"""
    
    def __init__(self):
        self.message_bus = MessageBus()
    
    def send_message(self, from_plugin: str, to_plugin: str, message: Dict):
        """发送消息"""
        self.message_bus.publish(f"plugin.{to_plugin}", {
            'from': from_plugin,
            'data': message,
            'timestamp': time.time()
        })
    
    def subscribe_messages(self, plugin_name: str, handler: Callable):
        """订阅消息"""
        self.message_bus.subscribe(f"plugin.{plugin_name}", handler)
```

## 总结

插件系统架构的核心优势：

1. **清晰的职责分离** - 核心功能与扩展功能明确分离
2. **强大的扩展性** - 支持第三方插件开发
3. **高度的模块化** - 插件可独立开发、测试和部署
4. **良好的性能** - 延迟加载和缓存机制
5. **可靠的稳定性** - 插件异常隔离，不影响核心功能
6. **统一的接口** - 标准化的插件开发接口
7. **灵活的配置** - 支持插件的启用/禁用和配置管理

这种架构设计确保了系统的可维护性、可扩展性和稳定性，为项目的长期发展奠定了坚实的基础。