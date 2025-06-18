# 存储命令插件 (Storage Commands Plugin)

## 概述

存储命令插件提供全面的数据存储和状态管理功能，支持变量管理、缓存机制、持久化存储等多种存储方式，是自动化测试框架中的核心数据管理组件。

## 核心特性

### 🔧 变量管理

- **多作用域支持**：global、session、test、step、temporary
- **TTL过期机制**：支持变量自动过期
- **类型检测**：自动检测和管理数据类型
- **变量监听**：支持变量变化监听和通知
- **表达式计算**：支持数学表达式计算和存储

### 💾 缓存机制

- **LRU淘汰策略**：最近最少使用算法
- **内存限制**：可配置的内存使用限制
- **自动清理**：定期清理过期缓存
- **统计信息**：缓存命中率、使用情况统计
- **压缩支持**：可选的数据压缩功能

### 🗄️ 持久化存储

- **SQLite数据库**：轻量级本地数据库
- **多种序列化格式**：JSON、Pickle、Binary、String
- **数据备份**：自动备份和恢复
- **数据迁移**：版本升级时的数据迁移
- **导入导出**：支持数据的导入和导出

### 🚀 批量操作

- **批量存储**：一次性存储多个变量
- **批量获取**：一次性获取多个变量
- **批量删除**：一次性删除多个变量
- **事务支持**：保证批量操作的原子性

### 🔍 监控和统计

- **实时统计**：存储使用情况实时监控
- **性能指标**：操作耗时、内存使用等
- **健康检查**：存储系统健康状态检查
- **告警机制**：异常情况自动告警

## 支持的命令

### 基础存储命令

#### store_variable

存储变量到指定作用域

```yaml
- action: store_variable
  params:
    name: "user_id"
    value: "12345"
    scope: "session"  # 可选：global, session, test, step, temporary
    ttl: 3600         # 可选：生存时间（秒）
    metadata:         # 可选：元数据
      source: "login_page"
      type: "user_data"
```

#### store_text

存储元素文本内容

```yaml
- action: store_text
  selector: "h1.title"
  params:
    variable_name: "page_title"
    scope: "test"
    ttl: 1800
```

#### store_attribute

存储元素属性值

```yaml
- action: store_attribute
  selector: "a.download-link"
  params:
    variable_name: "download_url"
    attribute: "href"
    scope: "session"
```

#### save_element_count

保存元素数量

```yaml
- action: save_element_count
  selector: ".product-item"
  params:
    variable_name: "product_count"
    scope: "test"
```

### 扩展存储命令

#### store_json

存储JSON数据

```yaml
- action: store_json
  params:
    variable_name: "config"
    json_data:
      api_url: "https://api.example.com"
      timeout: 30
      retries: 3
    scope: "global"
```

#### store_list

存储列表数据

```yaml
- action: store_list
  params:
    variable_name: "test_data"
    list_data: ["item1", "item2", "item3"]
    scope: "test"
```

#### store_expression

计算表达式并存储结果

```yaml
- action: store_expression
  params:
    variable_name: "total_price"
    expression: "${unit_price} * ${quantity} * (1 + ${tax_rate})"
    scope: "session"
```

#### get_variable

获取变量值

```yaml
- action: get_variable
  params:
    variable_name: "user_id"
    scope: "session"
    default: "guest"
    target_variable: "current_user_id"
```

#### delete_variable

删除变量

```yaml
- action: delete_variable
  params:
    variable_name: "temp_data"
    scope: "step"
```

#### list_variables

列出变量

```yaml
- action: list_variables
  params:
    scope: "session"  # 可选：为空则列出所有作用域
    target_variable: "session_vars"
```

#### clear_scope

清空作用域中的所有变量

```yaml
- action: clear_scope
  params:
    scope: "temporary"
```

### 缓存命令

#### set_cache

设置缓存

```yaml
- action: set_cache
  params:
    key: "api_response"
    value: "${response_data}"
    ttl: 300  # 5分钟
```

#### get_cache

获取缓存

```yaml
- action: get_cache
  params:
    key: "api_response"
    default: null
    target_variable: "cached_data"
```

#### delete_cache

删除缓存

```yaml
- action: delete_cache
  params:
    key: "old_data"
```

#### clear_cache

清空所有缓存

```yaml
- action: clear_cache
  params: {}
```

#### cache_stats

获取缓存统计信息

```yaml
- action: cache_stats
  params:
    target_variable: "cache_info"
```

### 持久化命令

#### save_persistent

保存持久化数据

```yaml
- action: save_persistent
  params:
    key: "user_settings"
    value: "${settings}"
    scope: "global"
    format: "json"  # json, pickle, binary, string
    ttl: 86400      # 24小时
    metadata:
      version: "1.0"
      created_by: "admin"
```

#### load_persistent

加载持久化数据

```yaml
- action: load_persistent
  params:
    key: "user_settings"
    scope: "global"
    default: {}
    target_variable: "loaded_settings"
```

#### delete_persistent

删除持久化数据

```yaml
- action: delete_persistent
  params:
    key: "temp_config"
    scope: "global"
```

#### export_data

导出数据到文件

```yaml
- action: export_data
  params:
    file_path: "backup/session_data.json"
    scope: "session"  # 可选：为空则导出所有数据
```

#### import_data

从文件导入数据

```yaml
- action: import_data
  params:
    file_path: "backup/session_data.json"
    target_variable: "import_count"
```

### 批量操作命令

#### batch_store

批量存储变量

```yaml
- action: batch_store
  params:
    variables:
      user_name: "admin"
      user_role: "administrator"
      login_time: "2024-01-15 10:30:00"
    scope: "session"
    ttl: 3600
```

#### batch_get

批量获取变量

```yaml
- action: batch_get
  params:
    variable_names: ["user_name", "user_role", "login_time"]
    scope: "session"
    target_variable: "user_info"
```

#### batch_delete

批量删除变量

```yaml
- action: batch_delete
  params:
    variable_names: ["temp1", "temp2", "temp3"]
    scope: "temporary"
```

### 管理命令

#### cleanup_storage

清理存储空间

```yaml
- action: cleanup_storage
  params:
    target_variable: "cleanup_result"
```

#### storage_stats

获取存储统计信息

```yaml
- action: storage_stats
  params:
    target_variable: "storage_info"
```

## 配置选项

### 基本配置

```yaml
general:
  data_directory: "data/storage"
  encoding: "utf-8"
  timezone: "Asia/Shanghai"
  language: "zh-CN"
```

### 变量管理配置

```yaml
variables:
  enabled: true
  default_scope: "global"
  scopes:
    global:
      max_variables: 1000
      default_ttl: null
    session:
      max_variables: 500
      default_ttl: 86400
  auto_cleanup:
    enabled: true
    interval: 300
```

### 缓存配置

```yaml
cache:
  enabled: true
  max_size: 1000
  default_ttl: 3600
  eviction_policy: "lru"
  auto_cleanup:
    enabled: true
    interval: 600
```

### 持久化配置

```yaml
persistence:
  enabled: true
  storage_path: "data/storage"
  database:
    type: "sqlite"
    file: "storage.db"
  serialization:
    default_format: "json"
  backup:
    enabled: true
    interval: 86400
    max_backups: 7
```

### 安全配置

```yaml
security:
  validation:
    enabled: true
    max_key_length: 255
    max_value_size: "10MB"
    forbidden_keys: ["password", "secret", "token"]
  encryption:
    enabled: false
    algorithm: "AES-256-GCM"
```

## 错误处理

### 常见错误类型

- **变量不存在**：尝试获取不存在的变量
- **作用域无效**：使用了不支持的作用域
- **数据过大**：存储的数据超过大小限制
- **序列化失败**：数据无法序列化
- **数据库错误**：持久化存储操作失败

### 错误处理策略

```yaml
# 在测试步骤中处理错误
- action: get_variable
  params:
    variable_name: "user_id"
    default: "guest"  # 提供默认值
  on_error: "continue"  # 错误时继续执行

# 使用条件判断
- action: conditional
  condition: "${user_id} != null"
  then:
    - action: store_variable
      params:
        name: "user_status"
        value: "logged_in"
  else:
    - action: store_variable
      params:
        name: "user_status"
        value: "guest"
```

## 性能考虑

### 内存优化

- 使用合适的TTL避免内存泄漏
- 定期清理过期数据
- 控制缓存大小
- 使用压缩减少内存占用

### 性能优化

- 批量操作减少I/O次数
- 使用缓存避免重复计算
- 异步清理任务
- 数据库连接池

### 最佳实践

```yaml
# 1. 使用合适的作用域
- action: store_variable
  params:
    name: "temp_result"
    value: "${calculation}"
    scope: "step"  # 临时数据使用step作用域
    ttl: 300       # 设置较短的TTL

# 2. 批量操作提高效率
- action: batch_store
  params:
    variables:
      var1: "value1"
      var2: "value2"
      var3: "value3"

# 3. 使用缓存避免重复计算
- action: get_cache
  params:
    key: "expensive_calculation"
    target_variable: "result"
- action: conditional
  condition: "${result} == null"
  then:
    - action: store_expression
      params:
        variable_name: "result"
        expression: "complex_calculation()"
    - action: set_cache
      params:
        key: "expensive_calculation"
        value: "${result}"
        ttl: 1800
```

## 扩展开发

### 自定义存储后端

```python
class CustomStorageBackend:
    def __init__(self, config):
        self.config = config
    
    def save(self, key, value, metadata=None):
        # 实现自定义保存逻辑
        pass
    
    def load(self, key, default=None):
        # 实现自定义加载逻辑
        pass
    
    def delete(self, key):
        # 实现自定义删除逻辑
        pass
```

### 自定义序列化器

```python
class CustomSerializer:
    def serialize(self, data):
        # 实现自定义序列化
        return serialized_data
    
    def deserialize(self, data):
        # 实现自定义反序列化
        return deserialized_data
```

### 自定义监听器

```python
def variable_change_listener(action, key, value, scope):
    """变量变化监听器"""
    if action == 'set':
        logger.info(f"变量设置: {key}={value} (scope={scope.value})")
    elif action == 'delete':
        logger.info(f"变量删除: {key} (scope={scope.value})")

# 注册监听器
plugin.variable_manager.add_listener(variable_change_listener)
```

## 使用场景

### 测试数据管理

```yaml
# 存储测试配置
- action: store_json
  params:
    variable_name: "test_config"
    json_data:
      base_url: "https://test.example.com"
      timeout: 30
      retries: 3
    scope: "global"

# 存储用户凭据
- action: store_variable
  params:
    name: "access_token"
    value: "${login_response.token}"
    scope: "session"
    ttl: 3600
```

### 状态管理

```yaml
# 记录测试进度
- action: store_variable
  params:
    name: "current_step"
    value: "login_completed"
    scope: "test"

# 累计计数器
- action: store_expression
  params:
    variable_name: "error_count"
    expression: "${error_count:0} + 1"
    scope: "test"
```

### 数据共享

```yaml
# 在步骤间共享数据
- action: store_variable
  params:
    name: "order_id"
    value: "${create_order_response.id}"
    scope: "test"

# 在测试间共享数据
- action: save_persistent
  params:
    key: "user_profile"
    value: "${profile_data}"
    scope: "global"
```

### 性能优化

```yaml
# 缓存API响应
- action: set_cache
  params:
    key: "user_list"
    value: "${api_response}"
    ttl: 600

# 预计算结果
- action: store_expression
  params:
    variable_name: "total_amount"
    expression: "sum(${order_items}, 'price')"
    scope: "session"
```

## 注意事项

### 安全性

- 避免存储敏感信息（密码、密钥等）
- 使用加密存储敏感数据
- 设置合适的访问权限
- 定期清理过期数据

### 兼容性

- 支持Python 3.10+
- 兼容主流操作系统
- 向后兼容旧版本配置
- 支持数据迁移

### 可维护性

- 使用描述性的变量名
- 添加适当的元数据
- 定期备份重要数据
- 监控存储使用情况

## 版本历史

### v1.0.0 (2024-01-15)

- 初始版本发布
- 支持基本变量存储和管理
- 支持缓存功能
- 支持持久化存储
- 支持批量操作
- 支持多种作用域
- 支持TTL过期机制
- 支持数据序列化
- 支持自动清理
- 支持统计和监控

## 许可证

MIT License

## 支持

如有问题或建议，请联系开发团队或提交Issue。

---

**存储命令插件** - 让数据管理更简单、更高效！