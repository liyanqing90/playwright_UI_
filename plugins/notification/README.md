# 通知插件 (Notification Plugin)

通知插件提供了多渠道、统一的通知发送功能，支持钉钉、邮件、Webhook、Slack等多种通知方式，适用于自动化测试结果通知、系统告警、状态报告等场景。

## 核心特性

### 🚀 多渠道支持

- **钉钉通知**: 支持文本和Markdown格式，@功能
- **邮件通知**: 支持HTML和纯文本格式，附件功能
- **Webhook通知**: 灵活的HTTP回调通知
- **Slack通知**: 支持频道消息和私聊
- **企业微信**: 企业微信群机器人通知
- **短信通知**: 支持多家短信服务商
- **自定义提供者**: 可扩展的提供者架构

### 📋 模板系统

- **预定义模板**: 测试报告、错误告警、成功通知等
- **变量替换**: 支持动态内容生成
- **多格式支持**: 文本、Markdown、HTML、JSON
- **自定义模板**: 灵活的模板定义和管理

### 🔄 高级功能

- **批量通知**: 一次发送多条通知
- **条件通知**: 基于条件的智能通知
- **重试机制**: 自动重试失败的通知
- **限流控制**: 防止通知频率过高
- **优先级管理**: 支持不同优先级的通知

### 📊 监控统计

- **发送历史**: 完整的通知发送记录
- **成功率统计**: 各提供者的成功率分析
- **性能监控**: 响应时间和错误率监控
- **健康检查**: 提供者可用性检查

### 🔒 安全特性

- **访问控制**: IP白名单和API密钥验证
- **内容加密**: 敏感信息加密传输
- **审计日志**: 完整的操作审计记录
- **内容验证**: 防止恶意内容注入

## 支持的命令

### 基础通知命令

#### send_notification

发送通用通知消息

```yaml
- action: send_notification
  title: "测试完成通知"
  content: "自动化测试已完成，请查看结果"
  providers: ["dingtalk", "email"]
  priority: "normal"
  type: "markdown"
  recipients: ["user@example.com"]
  target_variable: "notification_results"
```

#### send_template_notification

使用模板发送通知

```yaml
- action: send_template_notification
  template_name: "test_report"
  variables:
    project_name: "Web自动化测试"
    environment: "测试环境"
    result: "成功"
    total_cases: 100
    passed_cases: 95
    failed_cases: 5
    success_rate: 95
  title: "测试报告"
  providers: ["dingtalk"]
  target_variable: "report_result"
```

### 特定提供者命令

#### send_dingtalk

发送钉钉通知

```yaml
- action: send_dingtalk
  title: "紧急告警"
  content: |
    ## 系统异常告警
    
    **时间**: 2024-01-15 14:30:00
    **级别**: 严重
    **描述**: 数据库连接超时
    
    请立即处理！
  at_mobiles: ["13800138000"]
  is_markdown: true
  target_variable: "dingtalk_result"
```

#### send_email

发送邮件通知

```yaml
- action: send_email
  title: "自动化测试报告"
  content: |
    <h2>测试报告</h2>
    <p>测试已完成，详细结果如下：</p>
    <ul>
      <li>总用例数: 100</li>
      <li>通过数: 95</li>
      <li>失败数: 5</li>
    </ul>
  recipients: ["team@example.com", "manager@example.com"]
  is_html: true
  target_variable: "email_result"
```

#### send_webhook

发送Webhook通知

```yaml
- action: send_webhook
  title: "API测试完成"
  content: "所有API测试用例执行完成"
  metadata:
    test_suite: "api_tests"
    environment: "staging"
    duration: "5m30s"
  target_variable: "webhook_result"
```

#### send_slack

发送Slack通知

```yaml
- action: send_slack
  title: "部署完成"
  content: |
    :white_check_mark: **部署成功**
    
    **版本**: v1.2.3
    **环境**: 生产环境
    **耗时**: 3分钟
  channel: "#deployments"
  is_markdown: true
  target_variable: "slack_result"
```

### 批量和条件通知

#### send_batch_notification

发送批量通知

```yaml
- action: send_batch_notification
  notifications:
    - title: "任务1完成"
      content: "数据处理任务执行成功"
      providers: ["dingtalk"]
      priority: "normal"
    - title: "任务2完成"
      content: "报告生成任务执行成功"
      providers: ["email"]
      priority: "low"
    - title: "所有任务完成"
      content: "批处理作业全部完成"
      providers: ["dingtalk", "slack"]
      priority: "high"
  target_variable: "batch_results"
```

#### send_conditional_notification

发送条件通知

```yaml
- action: send_conditional_notification
  condition: "${test_success_rate} < 0.9"
  title: "测试成功率告警"
  content: "测试成功率低于90%，当前成功率: ${test_success_rate}%"
  providers: ["dingtalk", "email"]
  priority: "high"
  type: "markdown"
  target_variable: "alert_result"
```

### 管理命令

#### get_notification_status

获取通知提供者状态

```yaml
- action: get_notification_status
  target_variable: "provider_status"
```

#### get_notification_history

获取通知历史记录

```yaml
- action: get_notification_history
  limit: 50
  target_variable: "notification_history"
```

#### get_notification_stats

获取通知统计信息

```yaml
- action: get_notification_stats
  target_variable: "notification_statistics"
```

#### cleanup_notification_history

清理通知历史记录

```yaml
- action: cleanup_notification_history
  days: 30
  target_variable: "cleanup_count"
```

## 配置选项

### 通用配置

```yaml
general:
  enabled: true
  logging:
    enabled: true
    level: "INFO"
    file: "logs/notification.log"
  timezone: "Asia/Shanghai"
  language: "zh-CN"
```

### 提供者配置

#### 钉钉配置

```yaml
providers:
  dingtalk:
    enabled: true
    access_token: "${DINGTALK_ACCESS_TOKEN}"
    secret: "${DINGTALK_SECRET}"
    timeout: 30
    retry:
      enabled: true
      max_retries: 3
      retry_delay: 5
    rate_limit:
      enabled: true
      max_requests: 20
      time_window: 60
```

#### 邮件配置

```yaml
providers:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "${EMAIL_USERNAME}"
    password: "${EMAIL_PASSWORD}"
    from_email: "${EMAIL_FROM}"
    use_tls: true
    timeout: 30
```

#### Webhook配置

```yaml
providers:
  webhook:
    enabled: true
    url: "${WEBHOOK_URL}"
    method: "POST"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer ${WEBHOOK_TOKEN}"
    timeout: 30
    verify_ssl: true
```

### 模板配置

```yaml
templates:
  test_report:
    type: "markdown"
    content: |
      ## 测试报告
      
      **测试项目**: {project_name}
      **测试环境**: {environment}
      **执行时间**: {execution_time}
      **测试结果**: {result}
      
      ### 测试统计
      - 总用例数: {total_cases}
      - 通过数: {passed_cases}
      - 失败数: {failed_cases}
      - 成功率: {success_rate}%
```

### 重试配置

```yaml
retry:
  enabled: true
  max_retries: 3
  retry_delay: 5
  backoff_factor: 2.0
  retry_on_status: [500, 502, 503, 504]
  retry_on_timeout: true
```

### 安全配置

```yaml
security:
  encryption:
    enabled: false
    algorithm: "AES-256-GCM"
  access_control:
    enabled: false
    allowed_ips: []
    api_key_required: false
  audit:
    enabled: true
    log_file: "logs/notification_audit.log"
    include_content: false
```

## 错误处理

### 常见错误类型

1. **配置错误**
    - 缺少必要的配置参数
    - 无效的提供者配置
    - 模板格式错误

2. **网络错误**
    - 连接超时
    - DNS解析失败
    - SSL证书验证失败

3. **认证错误**
    - 无效的访问令牌
    - 签名验证失败
    - 权限不足

4. **限流错误**
    - 请求频率过高
    - 配额超限
    - 服务暂时不可用

### 错误处理策略

```yaml
# 自动重试配置
retry:
  enabled: true
  max_retries: 3
  retry_delay: 5
  backoff_factor: 2.0

# 降级策略
fallback:
  enabled: true
  fallback_providers: ["webhook", "email"]
  fallback_on_failure: true

# 错误通知
error_notification:
  enabled: true
  notify_on_failure: true
  error_threshold: 5
  notification_providers: ["email"]
```

## 性能考虑

### 最佳实践

1. **连接池管理**
   ```yaml
   performance:
     connection_pool:
       enabled: true
       max_connections: 20
       connection_timeout: 30
   ```

2. **批量处理**
   ```yaml
   batch:
     enabled: true
     max_batch_size: 10
     parallel_execution: true
     max_workers: 5
   ```

3. **缓存优化**
   ```yaml
   performance:
     caching:
       enabled: true
       cache_size: 1000
       cache_ttl: 3600
   ```

4. **异步处理**
   ```yaml
   performance:
     async_processing:
       enabled: true
       queue_size: 1000
       worker_threads: 5
   ```

### 性能监控

```yaml
monitoring:
  enabled: true
  metrics:
    - "response_time"
    - "success_rate"
    - "error_rate"
    - "throughput"
  alerts:
    enabled: true
    thresholds:
      response_time: 30
      error_rate: 0.1
      success_rate: 0.9
```

## 扩展开发

### 自定义通知提供者

```python
from plugins.notification.plugin import NotificationProvider, NotificationMessage, NotificationResult

class CustomProvider(NotificationProvider):
    def __init__(self, config):
        super().__init__("custom", config)
        self.api_key = config.get('api_key')
        self.endpoint = config.get('endpoint')
    
    def validate_config(self) -> bool:
        return bool(self.api_key and self.endpoint)
    
    def send(self, message: NotificationMessage) -> NotificationResult:
        # 实现自定义发送逻辑
        result = NotificationResult(
            message_id=message.id,
            provider=self.name,
            status=NotificationStatus.SENDING
        )
        
        try:
            # 发送逻辑
            response = self._send_request(message)
            result.status = NotificationStatus.SUCCESS
            result.sent_at = datetime.now()
        except Exception as e:
            result.status = NotificationStatus.FAILED
            result.error_message = str(e)
        
        return result
```

### 自定义模板引擎

```python
from plugins.notification.plugin import NotificationTemplate

class AdvancedTemplate(NotificationTemplate):
    def render(self, variables):
        # 实现高级模板渲染逻辑
        # 支持条件语句、循环等
        return self._advanced_render(self.template, variables)
```

### 自定义命令

```python
from src.automation.commands.base_command import Command

class CustomNotificationCommand(Command):
    def execute(self, ui_helper, selector, value, step):
        # 实现自定义通知命令逻辑
        plugin = getattr(ui_helper, 'notification_plugin', None)
        if not plugin:
            raise RuntimeError("通知插件未初始化")
        
        # 自定义处理逻辑
        pass
```

## 使用场景

### 1. 自动化测试报告

```yaml
# 测试完成后发送报告
- action: send_template_notification
  template_name: "test_report"
  variables:
    project_name: "${project_name}"
    environment: "${test_environment}"
    total_cases: "${total_test_cases}"
    passed_cases: "${passed_cases}"
    failed_cases: "${failed_cases}"
    success_rate: "${success_rate}"
  title: "自动化测试报告 - ${project_name}"
  providers: ["dingtalk", "email"]
  priority: "normal"
```

### 2. 系统监控告警

```yaml
# 系统异常时发送告警
- action: send_conditional_notification
  condition: "${error_count} > 10"
  title: "系统异常告警"
  content: |
    系统检测到异常情况：
    
    - 错误数量: ${error_count}
    - 错误率: ${error_rate}%
    - 影响模块: ${affected_modules}
    
    请立即处理！
  providers: ["dingtalk", "sms"]
  priority: "urgent"
  recipients: ["${on_call_engineer}"]
```

### 3. 部署状态通知

```yaml
# 部署完成后通知
- action: send_notification
  title: "部署完成通知"
  content: |
    ## 部署成功 ✅
    
    **版本**: ${deploy_version}
    **环境**: ${target_environment}
    **耗时**: ${deploy_duration}
    **部署人**: ${deployer}
    
    服务已正常启动，可以开始测试。
  providers: ["slack", "dingtalk"]
  type: "markdown"
  priority: "normal"
```

### 4. 定时任务状态

```yaml
# 定时任务执行结果通知
- action: send_batch_notification
  notifications:
    - title: "数据备份完成"
      content: "每日数据备份任务执行成功"
      providers: ["email"]
    - title: "报表生成完成"
      content: "每日报表生成任务执行成功"
      providers: ["dingtalk"]
    - title: "系统清理完成"
      content: "系统日志清理任务执行成功"
      providers: ["webhook"]
```

## 注意事项

### 安全性

1. **敏感信息保护**
    - 使用环境变量存储访问令牌和密钥
    - 启用内容加密传输
    - 避免在日志中记录敏感信息

2. **访问控制**
    - 配置IP白名单限制访问
    - 使用API密钥验证请求
    - 定期轮换访问凭证

3. **审计追踪**
    - 启用操作审计日志
    - 记录所有通知发送活动
    - 定期检查异常访问

### 兼容性

1. **Python版本**: 需要Python 3.10或更高版本
2. **依赖库**: 确保安装所需的第三方库
3. **网络环境**: 确保能够访问各通知服务的API
4. **防火墙**: 配置必要的出站规则

### 可维护性

1. **配置管理**
    - 使用版本控制管理配置文件
    - 区分不同环境的配置
    - 定期备份配置数据

2. **监控运维**
    - 监控通知发送成功率
    - 设置告警阈值
    - 定期清理历史数据

3. **文档维护**
    - 及时更新配置文档
    - 记录变更历史
    - 提供故障排查指南

## 版本历史

### v1.0.0 (2024-01-15)

- 初始版本发布
- 支持钉钉、邮件、Webhook、Slack通知
- 提供完整的模板系统
- 实现批量和条件通知功能
- 包含监控统计和历史记录功能
- 提供安全和性能优化配置

## 许可证

MIT License

## 支持

如有问题或建议，请联系：

- 邮箱: automation-team@example.com
- 文档: [插件使用教程](../../docs/插件使用教程.md)
- 问题反馈: [GitHub Issues](https://github.com/example/automation-framework/issues)