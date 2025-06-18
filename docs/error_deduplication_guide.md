# 错误去重功能使用指南

## 概述

错误去重功能旨在解决自动化测试中相同错误重复记录的问题，通过智能去重机制避免日志文件被大量重复错误信息污染，提高错误分析效率。

## 主要特性

### 🎯 核心功能

- **智能去重**: 基于错误消息、类型和选择器生成唯一哈希，识别重复错误
- **时间窗口**: 在指定时间窗口内限制相同错误的记录次数
- **错误分类**: 支持不同错误类型的差异化处理策略
- **自动清理**: 定期清理过期的错误记录，避免内存泄漏
- **统计报告**: 提供详细的错误统计和去重效果分析

### 🔧 高级特性

- **自定义模式**: 支持正则表达式定义特殊错误处理规则
- **忽略规则**: 可配置需要完全忽略的错误模式
- **优先级配置**: 不同错误类型可设置不同的重要性级别
- **配置热加载**: 支持运行时修改配置文件

## 快速开始

### 1. 基本使用

```python
from src.core.mixins.error_deduplication import ErrorDeduplicationManager
from utils.logger import logger

# 创建错误去重管理器
error_manager = ErrorDeduplicationManager()

# 在记录错误前检查是否应该记录
error_message = "Timeout waiting for element '#submit-button' to be visible"
if error_manager.should_log_error(error_message, "TimeoutError", "#submit-button"):
    logger.error(error_message)
else:
    # 错误被抑制，不记录
    pass
```

### 2. 装饰器集成

错误去重功能已集成到 `handle_page_error` 装饰器中：

```python
from src.core.mixins.decorators import handle_page_error

@handle_page_error
def click_element(page, selector):
    """点击元素，自动应用错误去重"""
    page.click(selector)
```

## 配置说明

### 配置文件位置

配置文件位于 `config/error_deduplication.yaml`，如果文件不存在将使用默认配置。

### 主要配置项

#### 基础去重配置

```yaml
error_deduplication:
  enabled: true                    # 是否启用错误去重
  time_window: 300                 # 时间窗口（秒），默认5分钟
  max_same_error_count: 3          # 相同错误最大记录次数
  cleanup_interval: 600            # 清理间隔（秒），默认10分钟
  
  # 错误消息标准化规则
  normalize_patterns:
    - pattern: '\d+ms'             # 将时间数字标准化
      replacement: 'Xms'
    - pattern: 'line \d+'          # 将行号标准化
      replacement: 'line X'
```

#### 错误类型配置

```yaml
error_types:
  timeout_errors:
    max_count: 2                   # 超时错误最多记录2次
    special_handling: true         # 启用特殊处理
    
  element_not_found_errors:
    max_count: 3                   # 元素未找到错误最多记录3次
    special_handling: false
    
  assertion_errors:
    max_count: 5                   # 断言错误最多记录5次
    special_handling: true
```

#### 高级配置

```yaml
advanced:
  # 自定义错误模式
  custom_error_patterns:
    - pattern: 'network.*timeout'   # 网络超时相关错误
      max_count: 1                 # 只记录1次
      category: 'network'
      
    - pattern: 'database.*connection'
      max_count: 2
      category: 'database'
  
  # 错误忽略规则
  ignore_patterns:
    - 'debug.*info'                # 忽略调试信息
    - 'temporary.*warning'         # 忽略临时警告
  
  # 错误优先级
  error_priorities:
    critical: ['assertion', 'fatal']
    high: ['timeout', 'network']
    medium: ['element_not_found']
    low: ['warning', 'info']
```

## 错误报告

### 自动生成报告

测试结束后会自动生成错误去重报告：

```
错误去重报告 - 2024-06-13 15:44:51
=====================================

📊 总体统计:
- 总错误类型: 15
- 被抑制错误: 8
- 去重效果: 53.3%
- 活跃记录: 7

🔥 高频错误 (Top 5):
1. Timeout waiting for element (出现 12 次)
2. Element not found: #submit-btn (出现 8 次)
3. Assertion failed: Expected text (出现 6 次)
4. Network connection timeout (出现 4 次)
5. Page load timeout (出现 3 次)

📈 错误趋势:
- 最近1小时: 25个错误
- 最近6小时: 67个错误
- 最近24小时: 156个错误
```

### 手动生成报告

```python
from src.core.mixins.error_reporter import generate_final_error_report

# 生成详细报告
generate_final_error_report()
```

## 最佳实践

### 1. 配置建议

- **时间窗口**: 根据测试执行时间调整，通常设置为5-10分钟
- **最大计数**: 重要错误设置较高值（5-10次），一般错误设置较低值（2-3次）
- **清理间隔**: 设置为时间窗口的2倍，避免频繁清理

### 2. 错误分类

- **超时错误**: 通常是环境问题，可以设置较低的记录次数
- **断言错误**: 通常是功能问题，应该设置较高的记录次数
- **元素未找到**: 可能是页面加载问题，设置中等记录次数

### 3. 监控建议

- 定期检查错误报告，关注高频错误
- 根据去重效果调整配置参数
- 监控被抑制的错误，避免遗漏重要问题

## 故障排除

### 常见问题

#### 1. 配置文件加载失败

**问题**: 日志显示"配置文件加载失败"

**解决方案**:

- 检查配置文件路径是否正确
- 验证YAML语法是否正确
- 确保文件编码为UTF-8

#### 2. 错误仍然重复记录

**问题**: 相同错误仍然被多次记录

**解决方案**:

- 检查 `enabled` 配置是否为 `true`
- 验证错误消息是否完全相同
- 检查时间窗口设置是否合理

#### 3. 重要错误被抑制

**问题**: 重要错误被错误地抑制了

**解决方案**:

- 增加该错误类型的 `max_count` 值
- 检查是否有忽略规则误匹配
- 考虑为重要错误设置自定义模式

### 调试模式

启用调试日志查看详细信息：

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## API 参考

### ErrorDeduplicationManager

#### 构造函数

```python
ErrorDeduplicationManager(config_file: str = None)
```

- `config_file`: 配置文件路径，默认为 `config/error_deduplication.yaml`

#### 主要方法

##### should_log_error

```python
should_log_error(error_message: str, error_type: str = None, selector: str = None) -> bool
```

判断是否应该记录错误。

**参数**:

- `error_message`: 错误消息
- `error_type`: 错误类型（可选）
- `selector`: 元素选择器（可选）

**返回**: 是否应该记录错误

##### get_error_statistics

```python
get_error_statistics() -> Dict[str, Any]
```

获取错误统计信息。

**返回**: 包含统计信息的字典

##### reset

```python
reset()
```

重置错误记录，清空所有数据。

## 更新日志

### v1.0.0 (2024-06-13)

- 初始版本发布
- 支持基本错误去重功能
- 集成配置文件支持
- 添加错误报告功能
- 支持自定义错误模式

## 许可证

本功能遵循项目整体许可证。