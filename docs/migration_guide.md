# 架构迁移指南

本文档指导如何从旧的继承模式架构迁移到新的组合模式架构。

## 架构变化概述

### 旧架构（继承模式）
```python
# 旧的方式 - 通过Mixin继承
class BasePage(ElementOperationsMixin, NavigationOperationsMixin, WaitOperationsMixin):
    def __init__(self, page):
        self.page = page
        super().__init__()
```

### 新架构（组合模式）
```python
# 新的方式 - 通过服务组合
class BasePage:
    def __init__(self, page, container=None):
        self.page = page
        self.container = container or ServiceContainer()
        self.element_service = self.container.resolve(ElementService)
        self.navigation_service = self.container.resolve(NavigationService)
        # ...
```

## 主要优势

1. **降低耦合度**: 服务之间相互独立，易于测试和维护
2. **提高可扩展性**: 可以轻松添加新服务或替换现有服务
3. **支持依赖注入**: 便于单元测试和模拟
4. **更好的性能监控**: 每个服务都有独立的性能统计
5. **变量管理**: 统一的变量替换和管理机制

## 迁移步骤

### 1. 更新导入语句

**旧代码:**
```python
from src.core.base_page import BasePage
from src.core.mixins.element_operations_mixin import ElementOperationsMixin
```

**新代码:**
```python
from src.core import BasePage, ServiceContainer
from src.core.services import ElementService, NavigationService
```

### 2. 更新BasePage初始化

**旧代码:**
```python
class MyPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.page = page
```

**新代码:**
```python
class MyPage(BasePage):
    def __init__(self, page, **kwargs):
        super().__init__(page=page, **kwargs)
        # 页面特定的初始化
```

### 3. 更新方法调用

大部分方法调用保持不变，但现在通过服务实现：

**旧代码:**
```python
def test_login(self):
    self.click("#login-btn")
    self.fill("#username", "test@example.com")
    self.wait_for_element("#dashboard")
```

**新代码:**
```python
def test_login(self):
    self.click("#login-btn")  # 内部调用 self.element_service.click()
    self.fill("#username", "test@example.com")
    self.wait_for_element("#dashboard")
```

### 4. 使用变量管理

**新功能 - 变量替换:**
```python
# 设置变量
self.set_variable("username", "test@example.com")
self.set_variable("base_url", "https://example.com")

# 在选择器和URL中使用变量
self.goto("${base_url}/login")
self.fill("#username", "${username}")
```

### 5. 自定义服务注入

**新功能 - 依赖注入:**
```python
# 创建自定义容器
container = ServiceContainer()

# 注册自定义服务
container.register(ElementService, CustomElementService)

# 使用自定义容器
page = BasePage(playwright_page, container=container)
```

## 具体迁移示例

### 示例1: 简单页面对象

**旧代码:**
```python
from src.core.base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.username_input = "#username"
        self.password_input = "#password"
        self.login_button = "#login-btn"
    
    def login(self, username, password):
        self.fill(self.username_input, username)
        self.fill(self.password_input, password)
        self.click(self.login_button)
        self.wait_for_url_contains("/dashboard")
```

**新代码:**
```python
from src.core import BasePage

class LoginPage(BasePage):
    def __init__(self, page, **kwargs):
        super().__init__(page=page, **kwargs)
        self.selectors = {
            'username': "#username",
            'password': "#password",
            'login_btn': "#login-btn"
        }
    
    def login(self, username, password):
        # 使用变量管理
        self.set_variable("username", username)
        self.set_variable("password", password)
        
        self.fill(self.selectors['username'], "${username}")
        self.fill(self.selectors['password'], "${password}")
        self.click(self.selectors['login_btn'])
        self.wait_for_url("/dashboard")
```

### 示例2: 测试用例迁移

**旧代码:**
```python
import pytest
from src.core.base_page import BasePage

@pytest.fixture
def login_page(page):
    return BasePage(page)

def test_login_success(login_page):
    login_page.goto("https://example.com/login")
    login_page.fill("#username", "test@example.com")
    login_page.fill("#password", "password123")
    login_page.click("#login-btn")
    login_page.assert_url_contains("/dashboard")
```

**新代码:**
```python
import pytest
from src.core import BasePage

@pytest.fixture
def login_page(page):
    return BasePage(
        page=page,
        base_url="https://example.com"
    )

def test_login_success(login_page):
    # 使用变量管理
    login_page.set_variable("test_email", "test@example.com")
    login_page.set_variable("test_password", "password123")
    
    login_page.goto("/login")
    login_page.fill("#username", "${test_email}")
    login_page.fill("#password", "${test_password}")
    login_page.click("#login-btn")
    login_page.assert_url_contains("/dashboard")
```

## 性能监控

新架构提供了内置的性能监控功能：

```python
# 执行一些操作
page.goto("/complex-page")
page.wait_for_element(".loading", state="hidden")
page.click(".submit-btn")

# 获取性能指标
metrics = page.get_performance_metrics()
print(f"操作性能统计: {metrics}")
```

## 错误处理改进

新架构提供了更好的错误处理和日志记录：

```python
try:
    page.click("#non-existent-element")
except Exception as e:
    # 错误信息更详细，包含操作上下文
    print(f"操作失败: {e}")
    
    # 可以获取详细的操作历史
    metrics = page.get_performance_metrics()
    print(f"失败前的操作统计: {metrics}")
```

## 兼容性说明

1. **API兼容性**: 大部分公共API保持不变，现有测试代码只需要少量修改
2. **配置兼容性**: 现有的配置文件和环境变量继续有效
3. **插件兼容性**: 现有的pytest插件和fixtures需要适配新的初始化方式

## 迁移检查清单

- [ ] 更新所有导入语句
- [ ] 修改BasePage初始化调用
- [ ] 更新自定义页面对象类
- [ ] 适配测试fixtures
- [ ] 验证所有测试用例通过
- [ ] 更新CI/CD配置（如需要）
- [ ] 更新文档和示例代码

## 常见问题

### Q: 旧的Mixin类还能使用吗？
A: 建议迁移到新架构，但旧的Mixin类在过渡期间仍然可用。新架构提供了更好的可维护性和扩展性。

### Q: 如何处理自定义的操作方法？
A: 可以通过继承相应的服务类或创建新的服务来实现自定义操作。

### Q: 性能是否有影响？
A: 新架构通过服务复用和更好的资源管理，实际上可能提高性能。同时提供了详细的性能监控。

### Q: 如何调试服务调用？
A: 新架构提供了详细的日志记录，可以通过日志查看每个服务的调用情况。

## 获取帮助

如果在迁移过程中遇到问题，可以：

1. 查看 `examples/new_architecture_demo.py` 中的示例代码
2. 运行示例来了解新架构的使用方式
3. 查看各个服务的文档和测试用例
4. 在项目中创建issue报告问题

## 总结

新的组合模式架构提供了更好的可维护性、可测试性和可扩展性。虽然需要一些迁移工作，但长期来看会大大提高开发效率和代码质量。建议分阶段进行迁移，先迁移核心功能，再逐步迁移其他部分。