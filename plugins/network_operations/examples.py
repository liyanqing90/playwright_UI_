# -*- coding: utf-8 -*-
"""
网络操作插件使用示例
"""

import asyncio
from typing import Dict, Any

from plugins.network_operations.plugin import (
    NetworkOperationsPlugin,
    NetworkRule,
    initialize_plugin,
    cleanup_plugin
)
from utils.logger import logger


def basic_usage_example():
    """基础使用示例"""
    print("=== 网络操作插件基础使用示例 ===")
    
    # 初始化插件
    plugin = initialize_plugin()
    
    # 获取插件信息
    info = plugin.get_plugin_info()
    print(f"插件名称: {info['name']}")
    print(f"插件版本: {info['version']}")
    print(f"插件描述: {info['description']}")
    
    # 更新配置
    plugin.update_config({
        "mock_enabled": True,
        "timeout": 60000,
        "logging_enabled": True
    })
    
    # 添加网络规则
    api_rule = NetworkRule(
        pattern="**/api/users/**",
        method="GET",
        headers={"X-Test-Header": "example"},
        delay=500
    )
    plugin.add_rule(api_rule)
    
    # 添加更多规则
    mock_rule = NetworkRule(
        pattern="**/api/mock/**",
        method="POST",
        delay=1000
    )
    plugin.add_rule(mock_rule)
    
    print(f"当前规则数量: {len(plugin.rules)}")
    
    # 模拟添加拦截数据
    plugin.intercepted_requests.append({
        "url": "https://api.example.com/users/123",
        "method": "GET",
        "headers": {"Authorization": "Bearer token"},
        "timestamp": "2024-01-01T12:00:00Z"
    })
    
    plugin.intercepted_responses.append({
        "url": "https://api.example.com/users/123",
        "status_code": 200,
        "response_body": {"id": 123, "name": "Test User"},
        "timestamp": "2024-01-01T12:00:01Z"
    })
    
    # 获取拦截数据
    all_data = plugin.get_intercepted_data()
    print(f"拦截的请求数: {len(all_data['requests'])}")
    print(f"拦截的响应数: {len(all_data['responses'])}")
    
    # 清理插件
    cleanup_plugin(plugin)
    print("插件已清理")


def command_usage_example():
    """命令使用示例"""
    print("\n=== 网络命令使用示例 ===")
    
    # 模拟UI Helper类
    class MockUIHelper:
        def __init__(self):
            self.variable_manager = MockVariableManager()
            self.network_plugin = initialize_plugin()
        
        def monitor_action_request(self, **kwargs):
            return {
                "url": kwargs.get("url_pattern", ""),
                "method": "GET",
                "headers": {},
                "timestamp": "2024-01-01T12:00:00Z"
            }
        
        def monitor_action_response(self, **kwargs):
            return {
                "url": kwargs.get("url_pattern", ""),
                "status_code": 200,
                "response_body": {"success": True},
                "timestamp": "2024-01-01T12:00:01Z"
            }
        
        def get_current_timestamp(self):
            import datetime
            return datetime.datetime.now().isoformat()
    
    class MockVariableManager:
        def __init__(self):
            self.variables = {}
        
        def set_variable(self, name, value, scope="global"):
            self.variables[name] = value
            print(f"变量已设置: {name} = {value}")
    
    # 创建模拟对象
    ui_helper = MockUIHelper()
    
    # 导入命令类
    from plugins.network_operations.plugin import (
        MonitorRequestCommand,
        MonitorResponseCommand,
        InterceptRequestCommand,
        MockResponseCommand,
        NetworkDelayCommand,
        ClearNetworkCacheCommand
    )
    
    # 1. 监控请求命令示例
    print("\n1. 监控请求命令")
    monitor_request_cmd = MonitorRequestCommand()
    monitor_request_cmd.execute(
        ui_helper=ui_helper,
        selector="#submit-btn",
        value="**/api/users/**",
        step={
            "url_pattern": "**/api/users/**",
            "action_type": "click",
            "variable_name": "user_request",
            "scope": "global"
        }
    )
    
    # 2. 监控响应命令示例
    print("\n2. 监控响应命令")
    monitor_response_cmd = MonitorResponseCommand()
    monitor_response_cmd.execute(
        ui_helper=ui_helper,
        selector="#login-btn",
        value="**/api/login",
        step={
            "url_pattern": "**/api/login",
            "action_type": "click",
            "assert_params": {"status_code": 200},
            "variable_name": "login_response",
            "timeout": 30000
        }
    )
    
    # 3. 拦截请求命令示例
    print("\n3. 拦截请求命令")
    intercept_cmd = InterceptRequestCommand()
    intercept_cmd.execute(
        ui_helper=ui_helper,
        selector="",
        value="**/api/sensitive/**",
        step={
            "url_pattern": "**/api/sensitive/**",
            "method": "POST",
            "headers": {"Authorization": "Bearer fake-token"},
            "modify_request": True,
            "variable_name": "intercepted_request"
        }
    )
    
    # 4. 模拟响应命令示例
    print("\n4. 模拟响应命令")
    mock_cmd = MockResponseCommand()
    mock_cmd.execute(
        ui_helper=ui_helper,
        selector="",
        value="**/api/external/**",
        step={
            "url_pattern": "**/api/external/**",
            "status_code": 200,
            "response_body": {
                "success": True,
                "data": {"id": 123, "name": "Mock User"}
            },
            "headers": {"Content-Type": "application/json"},
            "delay": 1000
        }
    )
    
    # 5. 网络延迟命令示例
    print("\n5. 网络延迟命令")
    delay_cmd = NetworkDelayCommand()
    delay_cmd.execute(
        ui_helper=ui_helper,
        selector="",
        value="**/api/slow/**",
        step={
            "url_pattern": "**/api/slow/**",
            "delay_ms": 3000,
            "apply_to": "all"
        }
    )
    
    # 6. 清空缓存命令示例
    print("\n6. 清空缓存命令")
    clear_cmd = ClearNetworkCacheCommand()
    clear_cmd.execute(
        ui_helper=ui_helper,
        selector="",
        value="",
        step={"cache_type": "all"}
    )
    
    # 显示最终状态
    print(f"\n最终拦截数据: {ui_helper.network_plugin.get_intercepted_data()}")
    print(f"设置的变量: {ui_helper.variable_manager.variables}")


def yaml_integration_example():
    """YAML集成示例"""
    print("\n=== YAML集成示例 ===")
    
    yaml_example = """
# 网络操作插件YAML测试用例示例
test_case:
  name: "网络操作测试"
  description: "演示网络操作插件的各种功能"
  
  steps:
    # 1. 监控登录请求
    - action: MONITOR_REQUEST
      url_pattern: "**/api/auth/login"
      action_type: "click"
      selector: "#login-button"
      variable_name: "login_request"
      scope: "test"
    
    # 2. 监控登录响应并断言
    - action: MONITOR_RESPONSE
      url_pattern: "**/api/auth/login"
      action_type: "click"
      selector: "#login-button"
      assert_params:
        status_code: 200
        response_contains: "access_token"
      save_params:
        - path: "data.access_token"
          variable_name: "auth_token"
      variable_name: "login_response"
    
    # 3. 拦截敏感API请求
    - action: INTERCEPT_REQUEST
      url_pattern: "**/api/admin/**"
      method: "POST"
      modify_request: true
      headers:
        Authorization: "Bearer ${auth_token}"
        X-Test-Mode: "true"
    
    # 4. 模拟外部服务响应
    - action: MOCK_RESPONSE
      url_pattern: "**/api/external/weather"
      status_code: 200
      response_body:
        temperature: 25
        humidity: 60
        condition: "sunny"
      headers:
        Content-Type: "application/json"
        Cache-Control: "no-cache"
      delay: 500
    
    # 5. 模拟网络延迟
    - action: NETWORK_DELAY
      url_pattern: "**/api/slow-service/**"
      delay_ms: 2000
      apply_to: "responses"
    
    # 6. 执行业务操作
    - action: click
      selector: "#weather-button"
      description: "点击获取天气信息"
    
    # 7. 验证模拟响应
    - action: assert_text
      selector: "#weather-info"
      value: "25°C"
      description: "验证天气信息显示"
    
    # 8. 清理网络缓存
    - action: CLEAR_NETWORK_CACHE
      cache_type: "responses"
      description: "清理响应缓存"
"""
    
    print("YAML配置示例:")
    print(yaml_example)


def performance_testing_example():
    """性能测试示例"""
    print("\n=== 性能测试示例 ===")
    
    # 模拟性能测试场景
    performance_scenarios = [
        {
            "name": "高并发API测试",
            "description": "模拟高并发API请求",
            "config": {
                "concurrent_requests": 100,
                "request_interval": 10,  # ms
                "test_duration": 60,     # seconds
            },
            "network_rules": [
                {
                    "pattern": "**/api/high-load/**",
                    "delay_ms": 100,
                    "apply_to": "responses"
                }
            ]
        },
        {
            "name": "慢网络测试",
            "description": "模拟慢网络环境",
            "config": {
                "network_speed": "3G",
                "latency": 300,  # ms
                "packet_loss": 0.1,  # 10%
            },
            "network_rules": [
                {
                    "pattern": "**",
                    "delay_ms": 300,
                    "apply_to": "all"
                }
            ]
        },
        {
            "name": "API故障测试",
            "description": "模拟API服务故障",
            "config": {
                "error_rate": 0.2,  # 20%
                "timeout_rate": 0.1,  # 10%
            },
            "mock_responses": [
                {
                    "pattern": "**/api/unreliable/**",
                    "responses": [
                        {"status_code": 500, "weight": 20},
                        {"status_code": 503, "weight": 10},
                        {"status_code": 200, "weight": 70}
                    ]
                }
            ]
        }
    ]
    
    for scenario in performance_scenarios:
        print(f"\n场景: {scenario['name']}")
        print(f"描述: {scenario['description']}")
        print(f"配置: {scenario['config']}")
        
        if 'network_rules' in scenario:
            print("网络规则:")
            for rule in scenario['network_rules']:
                print(f"  - 模式: {rule['pattern']}, 延迟: {rule['delay_ms']}ms")
        
        if 'mock_responses' in scenario:
            print("模拟响应:")
            for mock in scenario['mock_responses']:
                print(f"  - 模式: {mock['pattern']}")
                for response in mock['responses']:
                    print(f"    状态码: {response['status_code']}, 权重: {response['weight']}%")


def error_handling_example():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    # 初始化插件
    plugin = initialize_plugin()
    
    # 测试配置验证
    from plugins.network_operations.plugin import validate_config
    
    # 有效配置
    valid_config = {
        "enabled": True,
        "timeout": 30000,
        "max_retries": 3
    }
    
    # 无效配置
    invalid_configs = [
        {"timeout": 30000},  # 缺少enabled字段
        {"enabled": "true", "timeout": 30000},  # enabled类型错误
        {"enabled": True, "timeout": -1000},  # timeout值无效
    ]
    
    print("配置验证测试:")
    print(f"有效配置验证: {validate_config(valid_config)}")
    
    for i, config in enumerate(invalid_configs):
        result = validate_config(config)
        print(f"无效配置{i+1}验证: {result}")
    
    # 测试规则管理错误处理
    try:
        # 添加重复规则
        rule1 = NetworkRule(pattern="**/api/test/**")
        rule2 = NetworkRule(pattern="**/api/test/**")
        
        plugin.add_rule(rule1)
        plugin.add_rule(rule2)  # 重复模式
        
        print(f"当前规则数: {len(plugin.rules)}")
        
        # 移除不存在的规则
        plugin.remove_rule("**/api/nonexistent/**")
        
    except Exception as e:
        print(f"规则管理错误: {e}")
    
    # 清理
    cleanup_plugin(plugin)


def main():
    """主函数 - 运行所有示例"""
    print("网络操作插件使用示例")
    print("=" * 50)
    
    try:
        # 运行各种示例
        basic_usage_example()
        command_usage_example()
        yaml_integration_example()
        performance_testing_example()
        error_handling_example()
        
        print("\n=== 所有示例运行完成 ===")
        
    except Exception as e:
        logger.error(f"示例运行出错: {e}")
        raise


if __name__ == "__main__":
    main()