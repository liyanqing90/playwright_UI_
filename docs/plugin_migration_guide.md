# 插件系统迁移指南

本文档描述了如何从旧的插件系统迁移到新的分层架构插件系统。

## 迁移概述

### 架构变化

1. **核心服务层**：基础服务（元素操作、导航、断言等）移至核心层
2. **插件层**：高级功能和扩展功能保留在插件层
3. **兼容性层**：提供向后兼容的接口适配器

### 主要改进

- 更清晰的职责划分
- 更好的依赖管理
- 统一的插件接口
- 增强的生命周期管理
- 更强的错误处理

## 迁移步骤

### 1. 导入路径更新

**旧的导入方式：**

```python
from src.automation.commands.plugin_manager import plugin_manager
from src.automation.commands.plugin_manager import PluginManager
```

**新的导入方式：**

```python
# 使用兼容性适配器（推荐用于渐进式迁移）
from src.core.plugin_compatibility import plugin_manager
from src.core.plugin_compatibility import PluginManager

# 或直接使用新的核心管理器（用于新开发）
from src.core.plugin_manager import PluginManager as CorePluginManager
from src.core.interfaces.plugin_interface import PluginInterface
```

### 2. 插件接口更新

**旧的插件结构：**

```python
# plugin.py
def plugin_init():
    """插件初始化函数"""
    pass

def plugin_cleanup():
    """插件清理函数"""
    pass

@CommandRegistry.register(["custom_action"])
class CustomActionCommand(Command):
    def execute(self, ui_helper, selector, value, step):
        # 实现逻辑
        pass
```

**新的插件结构：**

```python
# plugin.py
from src.core.interfaces.plugin_interface import (
    PluginInterface, PluginStatus, PluginPriority,
    ConfigurablePlugin, LifecyclePlugin
)
from typing import Dict, Any, List

class Plugin(PluginInterface, ConfigurablePlugin, LifecyclePlugin):
    """新的插件接口实现"""
    
    def __init__(self):
        self._status = PluginStatus.UNLOADED
        self._config = {}
    
    def get_name(self) -> str:
        return "custom_plugin"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_description(self) -> str:
        return "自定义插件"
    
    def get_author(self) -> str:
        return "Plugin Developer"
    
    def get_dependencies(self) -> List[str]:
        return []
    
    def initialize(self, service_container) -> bool:
        """初始化插件"""
        try:
            self._status = PluginStatus.INITIALIZING
            # 初始化逻辑
            self._status = PluginStatus.ACTIVE
            return True
        except Exception:
            self._status = PluginStatus.ERROR
            return False
    
    def cleanup(self) -> bool:
        """清理插件"""
        try:
            self._status = PluginStatus.STOPPING
            # 清理逻辑
            self._status = PluginStatus.STOPPED
            return True
        except Exception:
            self._status = PluginStatus.ERROR
            return False
    
    def get_commands(self) -> List[str]:
        return ["custom_action"]
    
    def is_enabled(self) -> bool:
        return True
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "timeout": {"type": "number", "default": 30}
            }
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        return "timeout" in config and isinstance(config["timeout"], (int, float))
    
    def get_plugin_priority(self) -> PluginPriority:
        return PluginPriority.NORMAL
    
    def get_plugin_status(self) -> PluginStatus:
        return self._status
    
    # ConfigurablePlugin 接口
    def configure(self, config: Dict[str, Any]) -> bool:
        if self.validate_config(config):
            self._config = config
            return True
        return False
    
    def get_configuration(self) -> Dict[str, Any]:
        return self._config.copy()
    
    # LifecyclePlugin 接口
    def start(self) -> bool:
        if self._status == PluginStatus.LOADED:
            self._status = PluginStatus.ACTIVE
            return True
        return False
    
    def stop(self) -> bool:
        if self._status == PluginStatus.ACTIVE:
            self._status = PluginStatus.STOPPED
            return True
        return False
    
    def restart(self) -> bool:
        return self.stop() and self.start()
```

### 3. 插件元数据更新

**旧的配置格式（JSON）：**

```json
{
  "name": "custom_plugin",
  "version": "1.0.0",
  "description": "自定义插件",
  "author": "Plugin Developer",
  "commands": ["custom_action"],
  "dependencies": [],
  "enabled": true,
  "entry_point": "plugin.py"
}
```

**新的配置格式（YAML）：**

```yaml
# metadata.json 或 config.yaml
plugin:
  name: custom_plugin
  version: 1.0.0
  description: 自定义插件
  author: Plugin Developer
  dependencies: []
  enabled: true
  priority: normal  # critical, high, normal, low
  entry_point: plugin.py
  class_name: Plugin

commands:
  - name: custom_action
    description: 执行自定义动作
    parameters:
      - name: value
        type: string
        required: true

configuration:
  timeout: 30
  retry_count: 3
```

### 4. 服务容器集成

**新插件可以访问核心服务：**

```python
class Plugin(PluginInterface):
    def initialize(self, service_container) -> bool:
        # 获取核心服务
        self.element_service = service_container.get_service('ElementService')
        self.navigation_service = service_container.get_service('NavigationService')
        self.assertion_service = service_container.get_service('AssertionService')
        
        # 注册自己的服务
        service_container.register_service('CustomService', self.create_custom_service())
        
        return True
    
    def create_custom_service(self):
        """创建插件提供的服务"""
        return CustomService()
```

## 兼容性说明

### 向后兼容

1. **兼容性适配器**：`src.core.plugin_compatibility` 提供与旧接口完全兼容的适配器
2. **渐进式迁移**：可以逐步迁移插件，新旧插件可以共存
3. **配置兼容**：支持旧的JSON配置格式

### 迁移策略

1. **第一阶段**：更新导入路径，使用兼容性适配器
2. **第二阶段**：逐步更新插件接口，采用新的插件结构
3. **第三阶段**：完全迁移到新架构，移除兼容性层

## 最佳实践

### 1. 插件设计原则

- **单一职责**：每个插件专注于特定功能域
- **松耦合**：通过服务容器进行依赖注入
- **可配置**：支持运行时配置
- **可测试**：提供清晰的接口和模拟支持

### 2. 错误处理

```python
class Plugin(PluginInterface):
    def initialize(self, service_container) -> bool:
        try:
            # 初始化逻辑
            return True
        except Exception as e:
            self.logger.error(f"Plugin initialization failed: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """提供健康状态检查"""
        try:
            # 执行健康检查
            return {
                "status": "healthy",
                "message": "Plugin is running normally",
                "metrics": self.get_metrics()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {e}"
            }
```

### 3. 性能优化

- **延迟加载**：只在需要时加载插件
- **资源管理**：正确清理资源
- **缓存策略**：合理使用缓存

### 4. 测试策略

```python
import pytest
from src.core.container import ServiceContainer
from src.core.logger import Logger

class TestCustomPlugin:
    def setup_method(self):
        self.service_container = ServiceContainer()
        self.logger = Logger()
        self.plugin = Plugin()
    
    def test_plugin_initialization(self):
        assert self.plugin.initialize(self.service_container)
        assert self.plugin.get_plugin_status() == PluginStatus.ACTIVE
    
    def test_plugin_configuration(self):
        config = {"timeout": 60}
        assert self.plugin.configure(config)
        assert self.plugin.get_configuration()["timeout"] == 60
    
    def test_plugin_lifecycle(self):
        self.plugin.initialize(self.service_container)
        assert self.plugin.start()
        assert self.plugin.is_running()
        assert self.plugin.stop()
        assert not self.plugin.is_running()
```

## 故障排除

### 常见问题

1. **导入错误**：检查导入路径是否正确更新
2. **接口不兼容**：使用兼容性适配器进行过渡
3. **依赖问题**：确保所有依赖都已正确安装和配置
4. **配置错误**：验证插件配置格式和内容

### 调试技巧

1. **启用详细日志**：设置日志级别为DEBUG
2. **检查插件状态**：使用插件管理器的状态查询功能
3. **验证服务容器**：确保所需服务已注册
4. **单步调试**：逐步验证插件加载过程

## 总结

新的分层架构插件系统提供了更好的可维护性、可扩展性和可测试性。通过兼容性适配器，可以实现平滑的迁移过程，确保现有功能不受影响的同时，逐步采用新的架构优势。

建议采用渐进式迁移策略，先更新导入路径，然后逐步重构插件接口，最终完全迁移到新架构。