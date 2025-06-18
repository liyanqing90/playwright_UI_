# 网络操作插件

## 概述

网络操作插件提供了强大的网络请求监控、响应处理、API Mock等功能，帮助用户在自动化测试中更好地控制和监控网络行为。

## 功能特性

### 核心功能

- **请求监控** - 监控和拦截HTTP请求
- **响应处理** - 处理和修改HTTP响应
- **API Mock** - 模拟API响应
- **网络延迟** - 模拟网络延迟
- **缓存管理** - 管理网络数据缓存

### 扩展功能

- **规则引擎** - 灵活的网络规则配置
- **性能监控** - 网络性能指标收集
- **安全控制** - 域名白名单/黑名单
- **调试支持** - HAR文件导出

## 安装和配置

### 1. 插件安装

插件已集成在框架中，通过插件管理器自动加载：

```python
from src.automation.commands.plugin_manager import PluginManager

# 加载网络操作插件
plugin_manager = PluginManager()
plugin_manager.load_plugin('network_operations')
```

### 2. 配置文件

编辑 `plugins/network_operations/config.yaml` 文件：

```yaml
network_operations:
  enabled: true
  timeout: 30000
  mock_enabled: true
  intercept_enabled: true
```

## 使用指南

### 基础用法

#### 1. 监控请求

```yaml
# YAML测试用例
- action: MONITOR_REQUEST
  url_pattern: "**/api/users/**"
  action_type: "click"
  selector: "#submit-btn"
  variable_name: "user_request"
```

```python
# Python测试用例
from src.automation.commands.command_executor import CommandExecutor

executor = CommandExecutor()
executor.execute_command('MONITOR_REQUEST', {
    'url_pattern': '**/api/users/**',
    'action_type': 'click',
    'selector': '#submit-btn',
    'variable_name': 'user_request'
})
```

#### 2. 监控响应

```yaml
# YAML测试用例
- action: MONITOR_RESPONSE
  url_pattern: "**/api/login"
  action_type: "click"
  selector: "#login-btn"
  assert_params:
    status_code: 200
    response_contains: "success"
  variable_name: "login_response"
```

#### 3. 拦截请求

```yaml
# YAML测试用例
- action: INTERCEPT_REQUEST
  url_pattern: "**/api/sensitive/**"
  method: "POST"
  modify_request: true
  headers:
    Authorization: "Bearer fake-token"
```

#### 4. 模拟响应

```yaml
# YAML测试用例
- action: MOCK_RESPONSE
  url_pattern: "**/api/external/**"
  status_code: 200
  response_body:
    success: true
    data:
      id: 123
      name: "Mock User"
  headers:
    Content-Type: "application/json"
  delay: 1000
```

#### 5. 网络延迟

```yaml
# YAML测试用例
- action: NETWORK_DELAY
  url_pattern: "**/api/slow/**"
  delay_ms: 3000
  apply_to: "all"
```

#### 6. 清空缓存

```yaml
# YAML测试用例
- action: CLEAR_NETWORK_CACHE
  cache_type: "all"  # all, requests, responses, rules
```

### 高级用法

#### 1. 使用规则引擎

```python
from plugins.network_operations.plugin import NetworkRule, NetworkOperationsPlugin

# 创建网络规则
rule = NetworkRule(
    pattern="**/api/users/**",
    method="GET",
    headers={"X-Custom-Header": "test"},
    delay=500
)

# 添加规则
plugin = NetworkOperationsPlugin()
plugin.add_rule(rule)
```

#### 2. 动态配置

```python
# 更新插件配置
plugin.update_config({
    "mock_enabled": True,
    "timeout": 60000,
    "max_retries": 5
})
```

#### 3. 获取拦截数据

```python
# 获取所有拦截数据
all_data = plugin.get_intercepted_data()

# 只获取请求数据
requests = plugin.get_intercepted_data("requests")

# 只获取响应数据
responses = plugin.get_intercepted_data("responses")
```

## 配置参考

### 基础配置

| 参数                | 类型      | 默认值   | 说明         |
|-------------------|---------|-------|------------|
| enabled           | boolean | true  | 是否启用插件     |
| timeout           | number  | 30000 | 默认超时时间（毫秒） |
| max_retries       | integer | 3     | 最大重试次数     |
| mock_enabled      | boolean | false | 是否启用响应模拟   |
| intercept_enabled | boolean | true  | 是否启用请求拦截   |
| logging_enabled   | boolean | true  | 是否启用日志记录   |

### 高级配置

#### 拦截配置

- `max_requests`: 最大拦截请求数
- `auto_cleanup`: 自动清理过期数据
- `cleanup_interval`: 清理间隔（秒）

#### 模拟配置

- `default_delay`: 默认延迟（毫秒）
- `max_response_size`: 最大响应大小
- `cache_responses`: 是否缓存响应

#### 监控配置

- `track_headers`: 是否跟踪请求头
- `track_body`: 是否跟踪请求体
- `track_timing`: 是否跟踪时间信息

## API 参考

### 命令列表

| 命令                  | 说明   | 参数                                                |
|---------------------|------|---------------------------------------------------|
| MONITOR_REQUEST     | 监控请求 | url_pattern, action_type, selector, variable_name |
| MONITOR_RESPONSE    | 监控响应 | url_pattern, action_type, selector, assert_params |
| INTERCEPT_REQUEST   | 拦截请求 | url_pattern, method, headers, modify_request      |
| MOCK_RESPONSE       | 模拟响应 | url_pattern, status_code, response_body, headers  |
| NETWORK_DELAY       | 网络延迟 | url_pattern, delay_ms, apply_to                   |
| CLEAR_NETWORK_CACHE | 清空缓存 | cache_type                                        |

### 插件方法

#### NetworkOperationsPlugin

```python
class NetworkOperationsPlugin:
    def add_rule(self, rule: NetworkRule) -> None
    def remove_rule(self, pattern: str) -> None
    def clear_rules(self) -> None
    def get_intercepted_data(self, data_type: str = "all") -> List[Dict]
    def clear_intercepted_data(self) -> None
    def update_config(self, config: Dict[str, Any]) -> None
    def get_plugin_info(self) -> Dict[str, Any]
```

## 最佳实践

### 1. 性能优化

- 合理设置 `max_requests` 限制内存使用
- 启用 `auto_cleanup` 自动清理过期数据
- 对静态资源使用忽略规则

### 2. 安全考虑

- 配置域名白名单/黑名单
- 验证SSL证书
- 限制最大重定向次数

### 3. 调试技巧

- 启用详细日志记录
- 导出HAR文件分析网络行为
- 使用变量存储关键数据

### 4. 测试策略

- 分离网络测试和UI测试
- 使用Mock减少外部依赖
- 模拟各种网络条件

## 故障排除

### 常见问题

#### 1. 请求未被拦截

**问题**: 配置的URL模式没有匹配到请求

**解决方案**:

- 检查URL模式是否正确
- 使用通配符 `**` 匹配路径
- 启用详细日志查看实际请求URL

#### 2. 响应模拟不生效

**问题**: Mock响应没有返回预期数据

**解决方案**:

- 确认 `mock_enabled` 为 true
- 检查URL模式匹配
- 验证响应格式是否正确

#### 3. 性能问题

**问题**: 插件影响测试执行速度

**解决方案**:

- 减少监控的请求数量
- 启用自动清理
- 优化规则配置

### 日志分析

插件会输出详细的日志信息，包括：

```
[INFO] 网络操作插件已初始化: network_operations v1.0.0
[INFO] 已添加网络规则: **/api/users/**
[INFO] 已存储请求数据到变量 user_request
[INFO] 已设置模拟响应: **/api/mock/** -> 200
[INFO] 已清空网络缓存: all
```

## 版本历史

### v1.0.0

- 初始版本发布
- 支持基础的请求监控和响应处理
- 提供API Mock功能
- 实现网络延迟模拟
- 添加缓存管理功能

## 贡献指南

欢迎贡献代码和建议！请遵循以下步骤：

1. Fork 项目仓库
2. 创建功能分支
3. 提交代码更改
4. 创建 Pull Request

## 许可证

本插件遵循项目主许可证。