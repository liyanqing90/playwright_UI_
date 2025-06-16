# 配置说明文档

## 概述

本文档详细介绍了之家UI自动化测试框架的各种配置选项，包括全局配置、环境配置、浏览器配置、性能配置等。通过合理的配置，可以优化测试执行效果和性能。

## 1. 配置文件结构

### 1.1 配置文件层次

```
config/
├── constants.py           # 常量定义
├── test_config.yaml      # 主配置文件
├── environments/         # 环境配置
│   ├── dev.yaml         # 开发环境
│   ├── staging.yaml     # 测试环境
│   └── prod.yaml        # 生产环境
├── browsers/            # 浏览器配置
│   ├── chrome.yaml      # Chrome配置
│   ├── firefox.yaml     # Firefox配置
│   └── safari.yaml      # Safari配置
└── plugins/             # 插件配置
    ├── network.yaml     # 网络插件配置
    └── performance.yaml # 性能插件配置
```

### 1.2 配置优先级

配置的加载优先级（从高到低）：

1. **命令行参数** - 最高优先级
2. **环境变量** - 覆盖配置文件
3. **项目配置文件** - `test_config.yaml`
4. **默认配置** - `constants.py`

## 2. 主配置文件 (test_config.yaml)

### 2.1 基础配置

```yaml
# 基础执行配置
basic:
  # 默认超时时间(毫秒)
  timeout: 30000
  
  # 输入延迟(毫秒) - 模拟真实用户输入
  type_delay: 100
  
  # 轮询间隔(毫秒) - 等待元素时的检查间隔
  polling_interval: 500
  
  # 页面加载超时(毫秒)
  page_load_timeout: 60000
  
  # 导航超时(毫秒)
  navigation_timeout: 30000
```

### 2.2 重试配置

```yaml
retry:
  # 最大重试次数
  max_attempts: 3
  
  # 重试延迟(毫秒)
  delay: 1000
  
  # 指数退避因子
  backoff_factor: 2.0
  
  # 最大重试延迟(毫秒)
  max_delay: 10000
  
  # 需要重试的异常类型
  retry_exceptions:
    - "TimeoutError"
    - "ElementNotFoundError"
    - "NetworkError"
  
  # 不需要重试的异常类型
  no_retry_exceptions:
    - "AssertionError"
    - "ValidationError"
```

### 2.3 截图配置

```yaml
screenshot:
  # 失败时自动截图
  on_failure: true
  
  # 成功时截图
  on_success: false
  
  # 每个步骤后截图
  on_step: false
  
  # 截图保存目录
  directory: "screenshots"
  
  # 截图质量 (1-100)
  quality: 80
  
  # 截图格式
  format: "png"  # png, jpeg
  
  # 全页面截图
  full_page: false
  
  # 截图文件命名模式
  naming_pattern: "{test_name}_{timestamp}_{status}"
  
  # 最大保留截图数量
  max_files: 100
  
  # 自动清理过期截图(天)
  cleanup_days: 7
```

### 2.4 日志配置

```yaml
logging:
  # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: "INFO"
  
  # 日志格式
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # 日志文件配置
  file:
    enabled: true
    path: "logs/test.log"
    max_size: "10MB"
    backup_count: 5
    rotation: "daily"  # daily, weekly, monthly
  
  # 控制台日志
  console:
    enabled: true
    colored: true
  
  # 特定模块日志级别
  loggers:
    "selenium": "WARNING"
    "urllib3": "WARNING"
    "requests": "INFO"
```

### 2.5 报告配置

```yaml
report:
  # 证据收集目录
  evidence_dir: "evidence"
  
  # Allure报告配置
  allure:
    results_dir: "allure-results"
    report_dir: "allure-report"
    
    # 自动生成报告
    auto_generate: true
    
    # 报告标题
    title: "UI自动化测试报告"
    
    # 环境信息
    environment:
      Browser: "Chrome"
      Platform: "macOS"
      Version: "1.0.0"
  
  # HTML报告配置
  html:
    enabled: true
    template: "default"  # default, custom
    include_screenshots: true
    include_logs: true
  
  # JUnit XML报告
  junit:
    enabled: true
    file_path: "reports/junit.xml"
```

## 3. 浏览器配置

### 3.1 通用浏览器配置

```yaml
browser:
  # 浏览器类型: chromium, firefox, webkit
  type: "chromium"
  
  # 无头模式
  headless: false
  
  # 慢动作模式(毫秒) - 用于调试
  slow_mo: 0
  
  # 视窗大小
  viewport:
    width: 1920
    height: 1080
  
  # 设备像素比
  device_scale_factor: 1.0
  
  # 用户代理
  user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
  
  # 语言设置
  locale: "zh-CN"
  
  # 时区
  timezone: "Asia/Shanghai"
  
  # 权限设置
  permissions:
    - "geolocation"
    - "notifications"
  
  # 忽略HTTPS错误
  ignore_https_errors: true
  
  # 启用JavaScript
  javascript_enabled: true
```

### 3.2 Chrome特定配置

```yaml
chrome:
  # Chrome可执行文件路径
  executable_path: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  
  # Chrome启动参数
  args:
    - "--no-sandbox"
    - "--disable-dev-shm-usage"
    - "--disable-gpu"
    - "--disable-web-security"
    - "--allow-running-insecure-content"
    - "--disable-features=TranslateUI"
    - "--disable-extensions"
    - "--disable-plugins"
    - "--disable-images"  # 禁用图片加载以提高速度
  
  # 实验性功能
  experimental_options:
    useAutomationExtension: false
    excludeSwitches: ["enable-automation"]
  
  # 下载配置
  download:
    directory: "downloads"
    auto_download: true
```

### 3.3 Firefox特定配置

```yaml
firefox:
  # Firefox可执行文件路径
  executable_path: "/Applications/Firefox.app/Contents/MacOS/firefox"
  
  # Firefox配置选项
  preferences:
    "dom.webnotifications.enabled": false
    "media.volume_scale": "0.0"
    "browser.download.folderList": 2
    "browser.download.dir": "downloads"
    "browser.helperApps.neverAsk.saveToDisk": "application/pdf"
  
  # 配置文件路径
  profile_path: null
```

## 4. 环境配置

### 4.1 开发环境 (environments/dev.yaml)

```yaml
environment: "development"

# 基础URL配置
base_urls:
  web: "https://dev.example.com"
  api: "https://api-dev.example.com"
  admin: "https://admin-dev.example.com"

# 数据库配置
database:
  host: "localhost"
  port: 5432
  name: "testdb_dev"
  username: "testuser"
  password: "testpass"

# API配置
api:
  timeout: 30
  retry_count: 3
  base_headers:
    "Content-Type": "application/json"
    "Accept": "application/json"

# 测试数据配置
test_data:
  users:
    admin:
      username: "admin_dev"
      password: "admin123"
    normal:
      username: "user_dev"
      password: "user123"

# 调试配置
debug:
  enabled: true
  verbose_logging: true
  save_page_source: true
  pause_on_failure: true
```

### 4.2 生产环境 (environments/prod.yaml)

```yaml
environment: "production"

# 基础URL配置
base_urls:
  web: "https://www.example.com"
  api: "https://api.example.com"
  admin: "https://admin.example.com"

# 安全配置
security:
  ssl_verify: true
  certificate_path: "/path/to/cert.pem"
  
# 性能配置
performance:
  parallel_execution: true
  max_workers: 4
  resource_monitoring: true

# 调试配置
debug:
  enabled: false
  verbose_logging: false
  save_page_source: false
  pause_on_failure: false
```

## 5. 性能配置

### 5.1 执行性能配置

```yaml
performance:
  # 并行执行
  parallel:
    enabled: true
    max_workers: 4
    worker_timeout: 300  # 秒
  
  # 浏览器池
  browser_pool:
    enabled: true
    pool_size: 3
    max_idle_time: 300  # 秒
    reuse_browser: true
  
  # 资源监控
  monitoring:
    enabled: true
    
    # CPU监控
    cpu:
      threshold: 80  # 百分比
      alert_enabled: true
    
    # 内存监控
    memory:
      threshold: 1024  # MB
      alert_enabled: true
    
    # 网络监控
    network:
      timeout_threshold: 10000  # 毫秒
      alert_enabled: true
  
  # 缓存配置
  cache:
    enabled: true
    
    # 元素缓存
    elements:
      enabled: true
      ttl: 300  # 秒
      max_size: 1000
    
    # 页面缓存
    pages:
      enabled: false
      ttl: 60  # 秒
```

### 5.2 网络优化配置

```yaml
network:
  # 请求拦截
  intercept:
    enabled: true
    
    # 阻止资源类型
    block_resources:
      - "image"
      - "font"
      - "media"
      - "stylesheet"  # 可选，可能影响元素定位
    
    # 阻止特定域名
    block_domains:
      - "google-analytics.com"
      - "facebook.com"
      - "doubleclick.net"
  
  # 请求超时
  timeouts:
    connect: 10000  # 毫秒
    read: 30000     # 毫秒
    write: 10000    # 毫秒
  
  # 重试配置
  retry:
    max_attempts: 3
    delay: 1000  # 毫秒
```

## 6. 插件配置

### 6.1 网络插件配置 (plugins/network.yaml)

```yaml
network_plugin:
  enabled: true
  
  # 请求监控
  monitoring:
    enabled: true
    log_requests: true
    log_responses: false
    
    # 性能阈值
    thresholds:
      response_time: 5000  # 毫秒
      payload_size: 10485760  # 10MB
  
  # 请求模拟
  mocking:
    enabled: false
    rules_file: "test_data/mock_rules.yaml"
    
    # 默认响应
    default_response:
      status: 200
      headers:
        "Content-Type": "application/json"
      body: '{"status": "success"}'
  
  # 网络条件模拟
  conditions:
    enabled: false
    
    # 网络延迟(毫秒)
    latency: 100
    
    # 下载速度(字节/秒)
    download_speed: 1000000  # 1MB/s
    
    # 上传速度(字节/秒)
    upload_speed: 500000     # 500KB/s
```

### 6.2 性能插件配置 (plugins/performance.yaml)

```yaml
performance_plugin:
  enabled: true
  
  # 性能指标收集
  metrics:
    enabled: true
    
    # 页面性能指标
    page_metrics:
      - "loadEventEnd"
      - "domContentLoadedEventEnd"
      - "firstPaint"
      - "firstContentfulPaint"
    
    # 自定义指标
    custom_metrics:
      - name: "api_response_time"
        selector: "[data-api-time]"
        attribute: "data-api-time"
  
  # 性能阈值
  thresholds:
    page_load_time: 5000      # 毫秒
    first_paint: 2000         # 毫秒
    first_contentful_paint: 3000  # 毫秒
    
  # 报告生成
  reporting:
    enabled: true
    format: "json"  # json, html, csv
    output_file: "performance_report.json"
```

## 7. 数据配置

### 7.1 测试数据配置

```yaml
test_data:
  # 数据源配置
  sources:
    # 文件数据源
    file:
      enabled: true
      formats: ["yaml", "json", "csv"]
      encoding: "utf-8"
    
    # 数据库数据源
    database:
      enabled: false
      connection_string: "postgresql://user:pass@localhost/testdb"
      query_timeout: 30
    
    # API数据源
    api:
      enabled: false
      base_url: "https://api.example.com"
      timeout: 30
      headers:
        "Authorization": "Bearer ${API_TOKEN}"
  
  # 数据生成
  generation:
    enabled: true
    
    # Faker配置
    faker:
      locale: "zh_CN"
      seed: 12345  # 固定种子确保可重现性
    
    # 自定义生成器
    custom_generators:
      phone_number: "1[3-9]\\d{9}"
      id_card: "\\d{17}[0-9X]"
```

### 7.2 变量配置

```yaml
variables:
  # 全局变量
  global:
    app_name: "之家UI测试"
    version: "1.0.0"
    author: "测试团队"
  
  # 环境变量映射
  environment_mapping:
    TEST_ENV: "test_environment"
    BASE_URL: "base_url"
    API_TOKEN: "api_token"
  
  # 变量作用域配置
  scopes:
    global:
      storage: "memory"  # memory, file
      persistence: false
    
    test_case:
      storage: "memory"
      persistence: false
    
    module:
      storage: "file"
      persistence: true
      file_path: "vars/module_vars.yaml"
  
  # 变量替换配置
  replacement:
    enabled: true
    pattern: "\\$\\{([^}]+)\\}"  # ${variable_name}
    recursive: true
    max_depth: 10
```

## 8. 安全配置

### 8.1 认证配置

```yaml
authentication:
  # 基础认证
  basic_auth:
    enabled: false
    username: "${AUTH_USERNAME}"
    password: "${AUTH_PASSWORD}"
  
  # Token认证
  token_auth:
    enabled: false
    token: "${AUTH_TOKEN}"
    header_name: "Authorization"
    token_prefix: "Bearer "
  
  # 证书认证
  certificate_auth:
    enabled: false
    cert_file: "certs/client.crt"
    key_file: "certs/client.key"
    ca_file: "certs/ca.crt"
```

### 8.2 数据安全配置

```yaml
security:
  # 敏感数据处理
  sensitive_data:
    # 数据脱敏
    masking:
      enabled: true
      patterns:
        password: "****"
        credit_card: "****-****-****-{last4}"
        phone: "{first3}-****-{last4}"
    
    # 数据加密
    encryption:
      enabled: false
      algorithm: "AES-256"
      key_file: "keys/encryption.key"
  
  # 日志安全
  logging_security:
    # 过滤敏感信息
    filter_sensitive: true
    sensitive_fields:
      - "password"
      - "token"
      - "secret"
      - "key"
```

## 9. 配置使用示例

### 9.1 命令行配置覆盖

```bash
# 指定环境
pytest --env=staging test_data/demo/

# 覆盖浏览器配置
pytest --browser=firefox --headless test_data/demo/

# 覆盖超时配置
pytest --timeout=60000 test_data/demo/

# 启用调试模式
pytest --debug --slow-mo=1000 test_data/demo/

# 指定配置文件
pytest --config=config/custom_config.yaml test_data/demo/
```

### 9.2 环境变量配置

```bash
# 设置环境变量
export TEST_ENV=staging
export BASE_URL=https://staging.example.com
export BROWSER_HEADLESS=true
export LOG_LEVEL=DEBUG

# 运行测试
pytest test_data/demo/
```

### 9.3 代码中访问配置

```python
from src.core.config_manager import ConfigManager

# 获取配置管理器实例
config = ConfigManager.get_instance()

# 读取配置值
timeout = config.get('basic.timeout', 30000)
browser_type = config.get('browser.type', 'chromium')
headless = config.get('browser.headless', False)

# 设置配置值
config.set('browser.headless', True)
config.set('logging.level', 'DEBUG')

# 获取环境特定配置
base_url = config.get_env_config('base_urls.web')
api_url = config.get_env_config('base_urls.api')

# 验证配置
if config.validate():
    print("配置验证通过")
else:
    print("配置验证失败")
```

## 10. 配置最佳实践

### 10.1 配置组织

1. **分层配置**: 将不同类型的配置分别存储
2. **环境隔离**: 为不同环境创建独立的配置文件
3. **敏感信息**: 使用环境变量存储敏感信息
4. **版本控制**: 配置文件纳入版本控制，但排除敏感信息

### 10.2 配置验证

```yaml
# 配置验证规则
validation:
  rules:
    - field: "basic.timeout"
      type: "integer"
      min: 1000
      max: 300000
    
    - field: "browser.type"
      type: "string"
      choices: ["chromium", "firefox", "webkit"]
    
    - field: "retry.max_attempts"
      type: "integer"
      min: 1
      max: 10
```

### 10.3 配置文档化

```yaml
# 在配置文件中添加注释
basic:
  # 默认超时时间(毫秒)
  # 建议值: 30000 (30秒)
  # 最小值: 5000 (5秒)
  # 最大值: 300000 (5分钟)
  timeout: 30000
```

### 10.4 配置监控

```python
# 配置变更监控
class ConfigMonitor:
    def on_config_changed(self, key, old_value, new_value):
        logger.info(f"配置项 {key} 从 {old_value} 变更为 {new_value}")
        
        # 特殊配置项处理
        if key == 'browser.headless':
            self.restart_browser_pool()
        elif key.startswith('performance.'):
            self.update_performance_settings()
```

## 11. 故障排除

### 11.1 常见配置问题

#### 问题1: 配置文件找不到

```bash
# 错误信息
FileNotFoundError: config/test_config.yaml not found

# 解决方案
# 1. 检查文件路径
ls -la config/

# 2. 使用绝对路径
pytest --config=/absolute/path/to/config.yaml

# 3. 设置工作目录
cd /path/to/project && pytest
```

#### 问题2: 配置格式错误

```bash
# 错误信息
YAMLError: Invalid YAML syntax

# 解决方案
# 1. 验证YAML语法
python -c "import yaml; yaml.safe_load(open('config/test_config.yaml'))"

# 2. 使用在线YAML验证器
# 3. 检查缩进和特殊字符
```

#### 问题3: 环境变量未设置

```bash
# 错误信息
KeyError: 'BASE_URL' environment variable not set

# 解决方案
# 1. 设置环境变量
export BASE_URL=https://example.com

# 2. 使用.env文件
echo "BASE_URL=https://example.com" >> .env

# 3. 提供默认值
base_url = os.getenv('BASE_URL', 'https://localhost:8080')
```

### 11.2 配置调试

```python
# 配置调试工具
class ConfigDebugger:
    @staticmethod
    def dump_config():
        """输出当前配置"""
        config = ConfigManager.get_instance()
        print(json.dumps(config.to_dict(), indent=2))
    
    @staticmethod
    def validate_config():
        """验证配置完整性"""
        config = ConfigManager.get_instance()
        errors = config.validate()
        if errors:
            for error in errors:
                print(f"配置错误: {error}")
        else:
            print("配置验证通过")
    
    @staticmethod
    def trace_config_source(key):
        """追踪配置项来源"""
        config = ConfigManager.get_instance()
        source = config.get_source(key)
        print(f"配置项 {key} 来源: {source}")
```

## 12. 总结

通过本配置说明文档，您已经了解了：

1. ✅ **配置结构**: 理解框架的配置文件组织方式
2. ✅ **基础配置**: 掌握超时、重试、截图等基础配置
3. ✅ **浏览器配置**: 了解不同浏览器的配置选项
4. ✅ **环境配置**: 学会为不同环境创建配置
5. ✅ **性能配置**: 优化测试执行性能
6. ✅ **插件配置**: 配置网络和性能插件
7. ✅ **安全配置**: 处理敏感数据和认证
8. ✅ **最佳实践**: 遵循配置管理的最佳实践
9. ✅ **故障排除**: 解决常见的配置问题

合理的配置是高效自动化测试的基础，建议根据实际需求调整配置参数，并定期审查和优化配置设置。