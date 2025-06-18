# 文件操作插件 (File Operations Plugin)

## 概述

文件操作插件提供了完整的文件系统操作功能，支持文件和目录的创建、读取、写入、删除、复制、移动等操作。插件设计注重安全性、性能和易用性，支持多种文件格式和编码方式。

## 主要特性

### 🔧 核心功能

- **文件操作**: 读取、写入、删除、复制、移动文件
- **目录操作**: 创建、列出、搜索目录内容
- **文件信息**: 获取文件属性、检查文件存在性
- **备份恢复**: 自动备份、手动备份、文件恢复
- **压缩解压**: 支持ZIP、TAR等多种压缩格式
- **批量操作**: 支持批量文件处理

### 📁 支持格式

- **文本文件**: .txt, .log, .md, .rst, .ini, .cfg
- **JSON文件**: .json（支持格式化输出）
- **YAML文件**: .yaml, .yml（支持Unicode）
- **CSV文件**: .csv（支持自定义分隔符）
- **XML文件**: .xml
- **二进制文件**: .bin, .dat, .exe, .dll

### 🛡️ 安全特性

- **路径限制**: 可配置允许/禁止操作的路径
- **扩展名过滤**: 可配置允许/禁止的文件扩展名
- **大小限制**: 可配置最大文件大小限制
- **编码检测**: 自动检测文件编码

### ⚡ 性能优化

- **分块读写**: 大文件分块处理
- **并发控制**: 限制并发操作数量
- **内存管理**: 内存使用限制
- **超时控制**: 操作超时保护

## 支持的命令

### 基础文件操作

#### READ_FILE - 读取文件

```yaml
- action: read_file
  file_path: "./data/config.json"
  format: "json"
  encoding: "utf-8"
  variable_name: "config_data"
```

#### WRITE_FILE - 写入文件

```yaml
- action: write_file
  file_path: "./output/result.txt"
  content: "Hello, World!"
  encoding: "utf-8"
  mode: "w"  # w: 覆盖, a: 追加
  create_dirs: true
  backup: true
```

#### DELETE_FILE - 删除文件

```yaml
- action: delete_file
  file_path: "./temp/old_file.txt"
  backup: true
  force: false  # 强制删除目录
```

### 文件管理操作

#### COPY_FILE - 复制文件

```yaml
- action: copy_file
  source_path: "./source/file.txt"
  dest_path: "./backup/file.txt"
  overwrite: false
  preserve_metadata: true
```

#### MOVE_FILE - 移动文件

```yaml
- action: move_file
  source_path: "./temp/file.txt"
  dest_path: "./archive/file.txt"
  overwrite: false
```

### 目录操作

#### CREATE_DIRECTORY - 创建目录

```yaml
- action: create_directory
  dir_path: "./new_folder/subfolder"
  parents: true
  exist_ok: true
```

#### LIST_DIRECTORY - 列出目录

```yaml
- action: list_directory
  dir_path: "./data"
  pattern: "*.json"
  recursive: true
  include_hidden: false
  variable_name: "file_list"
```

### 文件信息

#### FILE_EXISTS - 检查文件存在

```yaml
- action: file_exists
  file_path: "./config/settings.yaml"
  variable_name: "config_exists"
```

#### GET_FILE_INFO - 获取文件信息

```yaml
- action: get_file_info
  file_path: "./data/large_file.dat"
  variable_name: "file_info"
```

### 备份和恢复

#### BACKUP_FILE - 备份文件

```yaml
- action: backup_file
  file_path: "./important/config.yaml"
  backup_dir: "./backups"
  variable_name: "backup_path"
```

#### RESTORE_FILE - 恢复文件

```yaml
- action: restore_file
  backup_path: "./backups/config.yaml.backup_20240613_143022"
  original_path: "./important/config.yaml"
  overwrite: true
```

### 压缩和解压

#### COMPRESS_FILE - 压缩文件

```yaml
- action: compress_file
  source_path: "./data/folder"
  archive_path: "./archives/data.zip"
  format: "zip"  # zip, tar, gztar, bztar, xztar
  variable_name: "archive_path"
```

#### EXTRACT_FILE - 解压文件

```yaml
- action: extract_file
  archive_path: "./archives/data.zip"
  extract_path: "./extracted"
  variable_name: "extract_path"
```

### 高级功能

#### SEARCH_FILES - 搜索文件

```yaml
- action: search_files
  search_path: "./logs"
  pattern: "*.log"
  content_pattern: "ERROR|FATAL"
  recursive: true
  case_sensitive: false
  variable_name: "error_logs"
```

#### BATCH_OPERATION - 批量操作

```yaml
- action: batch_operation
  operations:
    - type: "backup"
      params:
        file_path: "./config/app.yaml"
    - type: "copy"
      params:
        source_path: "./data/input.csv"
        dest_path: "./backup/input.csv"
    - type: "compress"
      params:
        source_path: "./logs"
        format: "gztar"
  continue_on_error: true
  variable_name: "batch_results"
```

## 参数说明

### 通用参数

- `file_path`: 文件路径（支持相对路径和绝对路径）
- `encoding`: 文件编码（默认: utf-8，支持auto自动检测）
- `format`: 文件格式（text/json/yaml/csv/binary）
- `variable_name`: 存储结果的变量名
- `scope`: 变量作用域（global/local，默认: global）

### 写入参数

- `content`: 要写入的内容
- `mode`: 写入模式（w: 覆盖，a: 追加）
- `create_dirs`: 是否自动创建目录（默认: true）
- `backup`: 是否创建备份（默认: true）

### 复制/移动参数

- `source_path`: 源文件路径
- `dest_path`: 目标文件路径
- `overwrite`: 是否覆盖已存在文件（默认: false）
- `preserve_metadata`: 是否保留文件元数据（默认: true）

### 搜索参数

- `pattern`: 文件名匹配模式（支持通配符）
- `content_pattern`: 内容搜索模式（支持正则表达式）
- `recursive`: 是否递归搜索（默认: true）
- `case_sensitive`: 是否大小写敏感（默认: false）
- `include_hidden`: 是否包含隐藏文件（默认: false）

### 压缩参数

- `format`: 压缩格式（zip/tar/gztar/bztar/xztar）
- `archive_path`: 压缩文件路径
- `extract_path`: 解压路径

## 配置选项

### 基础配置

```yaml
plugin:
  enabled: true
  encoding: "utf-8"
  backup_enabled: true
  max_file_size: 104857600  # 100MB
  auto_detect_encoding: true
  create_dirs: true
```

### 安全配置

```yaml
security:
  allowed_paths:
    - "./data"
    - "./temp"
    - "./uploads"
  forbidden_paths:
    - "/etc"
    - "/sys"
    - "C:\\Windows\\System32"
  allowed_extensions:
    - ".txt"
    - ".json"
    - ".yaml"
  forbidden_extensions:
    - ".exe"
    - ".bat"
    - ".cmd"
```

### 性能配置

```yaml
performance:
  chunk_size: 8192
  max_concurrent_operations: 5
  timeout: 30
  memory_limit: 536870912  # 512MB
```

### 备份配置

```yaml
backup:
  enabled: true
  directory: "backups"
  timestamp_format: "%Y%m%d_%H%M%S"
  max_backups: 10
  auto_cleanup: true
```

## 错误处理

插件提供完善的错误处理机制：

### 常见错误类型

- `FileNotFoundError`: 文件不存在
- `PermissionError`: 权限不足
- `ValueError`: 参数错误
- `OSError`: 系统错误
- `UnicodeError`: 编码错误

### 错误处理策略

- **自动重试**: 对于临时性错误进行重试
- **优雅降级**: 在可能的情况下提供替代方案
- **详细日志**: 记录详细的错误信息和上下文
- **用户友好**: 提供易于理解的错误消息

## 性能考虑

### 大文件处理

- 使用分块读写避免内存溢出
- 支持流式处理大文件
- 提供进度回调（计划中）

### 并发控制

- 限制同时进行的文件操作数量
- 避免资源竞争和死锁
- 支持异步操作（计划中）

### 内存管理

- 及时释放文件句柄
- 控制内存使用量
- 垃圾回收优化

## 扩展开发

### 添加新的文件格式支持

```python
class CustomFormatHandler:
    def read(self, file_path, encoding='utf-8'):
        # 实现自定义格式读取
        pass
    
    def write(self, file_path, content, encoding='utf-8'):
        # 实现自定义格式写入
        pass

# 注册新格式
plugin.register_format('custom', CustomFormatHandler())
```

### 添加新的操作命令

```python
@CommandFactory.register(StepAction.CUSTOM_OPERATION)
class CustomOperationCommand(Command):
    def execute(self, ui_helper, selector, value, step):
        # 实现自定义操作
        pass
```

## 使用场景

### 测试数据管理

- 读取测试配置文件
- 生成测试报告
- 管理测试数据文件
- 清理临时文件

### 配置文件操作

- 动态修改配置
- 备份重要配置
- 环境配置切换
- 配置验证

### 日志文件处理

- 搜索错误日志
- 归档旧日志
- 日志文件分析
- 日志清理

### 数据文件处理

- CSV数据导入导出
- JSON数据转换
- 批量数据处理
- 数据备份

## 注意事项

### 安全性

- 始终验证文件路径的安全性
- 避免路径遍历攻击
- 限制可操作的文件类型
- 定期清理临时文件

### 兼容性

- 注意不同操作系统的路径分隔符
- 处理文件编码差异
- 考虑文件权限问题
- 测试大文件处理

### 维护性

- 定期清理备份文件
- 监控磁盘空间使用
- 更新安全配置
- 优化性能参数

## 版本历史

### v1.0.0 (2024-06-13)

- 初始版本发布
- 支持基本文件操作
- 支持目录操作
- 支持文件备份和恢复
- 支持文件压缩和解压
- 支持批量操作
- 提供安全限制和性能优化

## 许可证

MIT License

## 支持

如有问题或建议，请联系开发团队或提交Issue。