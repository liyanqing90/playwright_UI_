# 断言命令插件 (Assertion Commands Plugin)

增强的断言命令插件，为 Playwright UI 自动化测试框架提供全面的断言功能。

## 🚀 核心特性

### 断言类型
- **硬断言 (Hard Assertion)**: 失败时立即停止执行
- **软断言 (Soft Assertion)**: 失败时记录错误但继续执行
- **条件断言 (Conditional Assertion)**: 基于条件执行的断言
- **批量断言 (Batch Assertion)**: 一次执行多个断言
- **重试断言 (Retry Assertion)**: 失败时自动重试的断言
- **超时断言 (Timeout Assertion)**: 在指定时间内等待条件满足
- **自定义断言 (Custom Assertion)**: 使用自定义验证逻辑

### 断言操作符
- **相等性**: `equals`, `not_equals`
- **包含性**: `contains`, `not_contains`, `starts_with`, `ends_with`
- **正则匹配**: `matches`
- **数值比较**: `greater_than`, `less_than`, `greater_equal`, `less_equal`
- **集合操作**: `in`, `not_in`
- **空值检查**: `is_empty`, `is_not_empty`, `is_null`, `is_not_null`
- **布尔值**: `is_true`, `is_false`
- **长度检查**: `length_equals`, `length_greater`, `length_less`

### 高级功能
- **统计监控**: 实时跟踪断言执行统计
- **性能监控**: 监控断言执行时间和性能
- **报告生成**: 自动生成详细的断言报告
- **错误处理**: 完善的错误处理和日志记录
- **配置灵活**: 丰富的配置选项

## 📦 支持的命令

### 基础断言命令

#### 等于断言
```yaml
- action: assert_equals
  selector: "#username"
  expected_value: "admin"
  message: "用户名应该是admin"
```

#### 包含断言
```yaml
- action: assert_contains
  selector: ".message"
  expected_value: "成功"
  ignore_case: true
```

#### 正则匹配断言
```yaml
- action: assert_matches
  selector: "#email"
  expected_value: "^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"
  message: "邮箱格式不正确"
```

#### 数值比较断言
```yaml
- action: assert_greater_than
  selector: "#score"
  expected_value: 80
  message: "分数应该大于80"
```

#### 长度断言
```yaml
- action: assert_length
  selector: ".items"
  expected_length: 5
  length_operator: "equals"  # equals, greater, less
```

### 高级断言命令

#### 软断言
```yaml
- action: soft_assert
  selector: "#status"
  operator: "equals"
  expected_value: "active"
  message: "状态应该是active"
```

#### 重试断言
```yaml
- action: retry_assert
  selector: ".loading"
  operator: "not_contains"
  expected_value: "loading"
  retry_count: 5
  retry_interval: 2.0
```

#### 超时断言
```yaml
- action: timeout_assert
  selector: ".result"
  operator: "not_empty"
  timeout: 30.0
  message: "30秒内应该有结果"
```

#### 条件断言
```yaml
- action: conditional_assert
  condition: "user_type == 'admin'"
  selector: ".admin-panel"
  operator: "not_empty"
  message: "管理员应该能看到管理面板"
```

#### 批量断言
```yaml
- action: batch_assert
  assertions:
    - selector: "#title"
      operator: "equals"
      expected_value: "首页"
    - selector: "#nav"
      operator: "not_empty"
    - selector: ".footer"
      operator: "contains"
      expected_value: "版权所有"
```

#### 自定义断言
```yaml
- action: custom_assert
  selector: "#price"
  validator: "float(actual) > 0 and float(actual) < 1000"
  message: "价格应该在0到1000之间"
```

### 管理命令

#### 检查软断言
```yaml
- action: check_soft_assertions
  fail_on_soft_assertion: true
```

#### 获取统计信息
```yaml
- action: get_assertion_stats
  variable_name: "assertion_stats"
```

#### 重置统计信息
```yaml
- action: reset_assertion_stats
```

## ⚙️ 配置选项

### 基础配置
```yaml
settings:
  enabled: true
  log_level: "INFO"
  encoding: "utf-8"
  timezone: "Asia/Shanghai"
  language: "zh-CN"
```

### 断言配置
```yaml
assertion:
  default_type: "hard"
  default_operator: "equals"
  default_timeout: 30.0
  default_retry_count: 0
  default_retry_interval: 1.0
  default_ignore_case: false
  default_trim_whitespace: true
```

### 软断言配置
```yaml
soft_assertion:
  enabled: true
  auto_collect_failures: true
  failure_log_level: "WARNING"
  max_failures: 100
  continue_on_failure: true
```

### 重试断言配置
```yaml
retry_assertion:
  enabled: true
  max_retry_count: 5
  retry_interval: 1.0
  retry_backoff_factor: 1.5
  max_retry_interval: 10.0
```

### 性能配置
```yaml
performance:
  monitoring_enabled: true
  collection_interval: 10
  slow_assertion_threshold: 1000
  memory_limit: 512
  cache_size: 1000
```

### 安全配置
```yaml
security:
  enabled: true
  allowed_assertion_types: ["hard", "soft", "conditional", "batch", "retry", "timeout", "custom"]
  max_assertion_depth: 10
  max_string_length: 10000
  validate_input: true
```

## 🔧 错误处理

### 断言失败处理
- **硬断言失败**: 立即抛出 `AssertionError` 并停止执行
- **软断言失败**: 记录失败信息，继续执行后续步骤
- **重试断言失败**: 按配置进行重试，最终失败时根据断言类型处理
- **超时断言失败**: 超时后根据断言类型处理

### 异常类型
- `AssertionError`: 断言失败
- `TimeoutError`: 超时断言超时
- `ValidationError`: 输入验证失败
- `ConfigurationError`: 配置错误

### 日志记录
```python
# 断言成功
logger.info("断言成功: assert_equals - 期望 'admin' 等于 'admin'")

# 断言失败
logger.error("断言失败: assert_equals - 期望 'admin' 等于 'user'")

# 重试断言
logger.info("重试断言成功: assert_contains, 尝试次数: 3")

# 软断言失败
logger.warning("软断言失败: assert_not_empty - 期望 '' 不为空")
```

## 📊 性能考虑

### 性能优化
- **断言缓存**: 缓存断言结果以提高性能
- **批量执行**: 支持批量断言以减少开销
- **异步执行**: 支持异步断言执行
- **内存管理**: 自动清理过期的断言结果

### 性能监控
- **执行时间**: 监控每个断言的执行时间
- **内存使用**: 监控断言过程中的内存使用
- **慢断言检测**: 自动检测执行时间过长的断言
- **统计报告**: 生成性能统计报告

### 性能建议
1. **合理使用重试断言**: 避免过多的重试次数
2. **优化选择器**: 使用高效的元素选择器
3. **批量断言**: 对于多个相关断言，使用批量断言
4. **缓存配置**: 合理配置断言缓存大小
5. **监控阈值**: 设置合适的慢断言阈值

## 🔌 扩展开发

### 自定义断言操作符
```python
class CustomAssertionOperator(Enum):
    CUSTOM_OPERATION = "custom_operation"

def evaluate_custom_operation(actual, expected):
    # 自定义断言逻辑
    return actual.custom_method() == expected
```

### 自定义断言类型
```python
class CustomAssertionType(Enum):
    CUSTOM_TYPE = "custom_type"

def execute_custom_assertion(assertion_id, actual, expected, config):
    # 自定义断言执行逻辑
    pass
```

### 自定义验证器
```python
def custom_validator(actual, expected):
    """自定义验证器示例"""
    try:
        # 自定义验证逻辑
        if isinstance(actual, str) and isinstance(expected, str):
            return actual.lower().strip() == expected.lower().strip()
        return actual == expected
    except Exception:
        return False
```

## 📝 使用场景

### Web UI 测试
```yaml
# 登录页面断言
- action: assert_equals
  selector: "h1"
  expected_value: "用户登录"
  
- action: assert_not_empty
  selector: "#username"
  
- action: soft_assert
  selector: ".remember-me"
  operator: "is_true"
```

### API 响应断言
```yaml
# API 响应断言
- action: assert_equals
  actual_value: "${response.status_code}"
  expected_value: 200
  
- action: assert_contains
  actual_value: "${response.body}"
  expected_value: "success"
  
- action: custom_assert
  actual_value: "${response.json}"
  validator: "'data' in actual and len(actual['data']) > 0"
```

### 数据验证
```yaml
# 数据格式验证
- action: assert_matches
  actual_value: "${user.email}"
  expected_value: "^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"
  
- action: assert_greater_than
  actual_value: "${user.age}"
  expected_value: 0
  
- action: assert_in
  actual_value: "${user.role}"
  expected_value: ["admin", "user", "guest"]
```

### 性能测试断言
```yaml
# 性能断言
- action: timeout_assert
  selector: ".page-content"
  operator: "not_empty"
  timeout: 5.0
  message: "页面应在5秒内加载完成"
  
- action: assert_less_than
  actual_value: "${page_load_time}"
  expected_value: 3000
  message: "页面加载时间应小于3秒"
```

## 📋 注意事项

### 安全性
- **输入验证**: 所有输入都经过严格验证
- **代码注入防护**: 自定义验证器有安全限制
- **权限控制**: 支持断言类型和操作符的权限控制
- **日志安全**: 敏感信息不会记录到日志中

### 兼容性
- **Python 版本**: 支持 Python 3.8+
- **Playwright 版本**: 支持 Playwright 1.20.0+
- **框架版本**: 支持框架 1.0.0+
- **操作系统**: 支持 Windows、macOS、Linux

### 可维护性
- **模块化设计**: 清晰的模块结构
- **配置驱动**: 通过配置文件控制行为
- **文档完整**: 详细的代码文档和使用说明
- **测试覆盖**: 完整的单元测试和集成测试
- **版本管理**: 规范的版本管理和更新日志

## 📈 版本历史

### v1.0.0 (2024-01-15)
- ✨ 初始版本发布
- ✨ 支持基础断言命令（equals, contains, matches等）
- ✨ 支持软断言和硬断言
- ✨ 支持条件断言和批量断言
- ✨ 支持重试断言和超时断言
- ✨ 支持自定义断言
- ✨ 提供完整的统计和报告功能
- ✨ 支持多种配置选项
- ✨ 提供详细的使用示例和文档

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 支持

- **文档**: [插件文档](docs/)
- **示例**: [使用示例](examples/)
- **问题反馈**: [GitHub Issues](https://github.com/playwright-ui/assertion-commands/issues)
- **功能请求**: [GitHub Discussions](https://github.com/playwright-ui/assertion-commands/discussions)

## 🔗 相关链接

- [Playwright UI 框架](https://github.com/playwright-ui/framework)
- [插件开发指南](docs/plugin-development.md)
- [最佳实践](docs/best-practices.md)
- [故障排除](docs/troubleshooting.md)

---

**断言命令插件** - 让您的自动化测试更加可靠和高效！