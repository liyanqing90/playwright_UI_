# 配置管理器使用示例

本文档提供了配置管理器的使用示例，帮助您理解如何使用增强的配置管理功能。

## 基本用法

### 1. 获取项目配置

```python
from utils.config_manager import config_manager, Project

# 使用枚举获取项目配置
project_config = config_manager.get_project_config(Project.CRM_BACKEND)

# 使用字符串获取项目配置
project_config = config_manager.get_project_config("crm_backend")

# 访问项目配置属性
test_dir = project_config.test_dir
browser_config = project_config.browser_config
default_env = project_config.default_environment
```

### 2. 获取环境配置

```python
from utils.config_manager import config_manager, Project, Environment

# 获取指定环境的配置
env_config = config_manager.get_environment_config(Project.CRM_BACKEND, Environment.TEST)

# 获取默认环境的配置
env_config = config_manager.get_environment_config(Project.CRM_BACKEND)

# 访问环境配置属性
base_url = env_config.base_url
api_url = env_config.api_url
timeout_multiplier = env_config.timeout_multiplier
retry_count = env_config.retry_count
```

### 3. 获取浏览器配置

```python
from utils.config_manager import config_manager, Project

# 获取浏览器配置
browser_config = config_manager.get_browser_config(Project.CRM_BACKEND)

# 访问浏览器配置属性
viewport_width = browser_config.viewport_width
viewport_height = browser_config.viewport_height
default_timeout = browser_config.default_timeout
slow_mo = browser_config.slow_mo
```

### 4. 获取任意配置值

```python
from utils.config_manager import config_manager

# 获取任意配置值
base_url = config_manager.get_config_value("projects.crm_backend.environments.test.base_url")

# 提供默认值
api_url = config_manager.get_config_value("projects.crm_backend.environments.test.api_url",
                                          "http://default-api.example.com")
```

## 高级用法

### 1. 设置配置值

```python
from utils.config_manager import config_manager

# 设置配置值
config_manager.set_config_value("projects.crm_backend.environments.test.base_url", "https://new-test-url.example.com")

# 设置嵌套配置值
config_manager.set_config_value("projects.crm_backend.browser_config.viewport_width", 1600)
```

### 2. 保存配置

```python
from utils.config_manager import config_manager

# 修改配置后保存
config_manager.set_config_value("projects.crm_backend.environments.test.base_url", "https://new-test-url.example.com")
config_manager.save_config()
```

### 3. 重新加载配置

```python
from utils.config_manager import config_manager

# 重新加载配置
config_manager.reload_config()
```

### 4. 获取所有项目和环境

```python
from utils.config_manager import config_manager

# 获取所有项目
projects = config_manager.get_all_projects()
print(f"所有项目: {projects}")

# 获取项目的所有环境
environments = config_manager.get_all_environments("crm_backend")
print(f"CRM后台项目的所有环境: {environments}")
```

## 环境变量覆盖

配置管理器支持使用环境变量覆盖配置值。环境变量名称应以 `CONFIG_` 开头，后面跟着配置路径，使用双下划线 `__` 分隔路径部分。

例如，要覆盖 `projects.crm_backend.environments.test.base_url`，可以设置以下环境变量：

```bash
export CONFIG_PROJECTS__CRM_BACKEND__ENVIRONMENTS__TEST__BASE_URL="https://override-url.example.com"
```

环境变量的值会自动转换为适当的类型：

- `"true"` 和 `"false"` 会转换为布尔值
- 数字会转换为整数或浮点数
- 其他值保持为字符串

## 配置验证

配置管理器会自动验证配置的有效性，确保配置符合预期的结构和类型。如果配置无效，会抛出 `ValueError` 异常，并提供详细的错误信息。

例如，以下代码会触发验证错误：

```python
from utils.config_manager import config_manager

# 设置无效的视口宽度（必须是偶数）
try:
    config_manager.set_config_value("projects.crm_backend.browser_config.viewport_width", 1601)
except ValueError as e:
    print(f"验证错误: {str(e)}")
```

## 配置继承

配置管理器支持多级配置继承，按照以下顺序合并配置：

1. 基础配置 (`base_config.yaml`)
2. 环境配置 (`env_config.yaml`)
3. 本地配置 (`local_config.yaml`)
4. 环境变量覆盖

后面的配置会覆盖前面的配置，这样可以实现配置的层次化管理。
