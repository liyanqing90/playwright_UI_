#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误去重功能使用示例
演示如何使用错误去重管理器来避免重复记录相同错误
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.mixins.error_deduplication import ErrorDeduplicationManager
from utils.logger import logger

def simulate_timeout_errors():
    """模拟超时错误"""
    print("\n=== 模拟超时错误 ===")
    
    error_manager = ErrorDeduplicationManager()
    
    # 模拟相同的超时错误多次发生
    timeout_error = "Timeout waiting for element '#submit-button' to be visible"
    
    for i in range(8):
        should_log = error_manager.should_log_error(
            error_message=timeout_error,
            error_type="TimeoutError",
            selector="#submit-button"
        )
        
        if should_log:
            logger.error(f"[第{i+1}次] {timeout_error}")
            print(f"✓ 第{i+1}次错误已记录")
        else:
            print(f"✗ 第{i+1}次错误被抑制（重复错误）")
        
        time.sleep(0.1)  # 短暂延迟

def simulate_element_not_found_errors():
    """模拟元素未找到错误"""
    print("\n=== 模拟元素未找到错误 ===")
    
    error_manager = ErrorDeduplicationManager()
    
    # 模拟不同元素的未找到错误
    errors = [
        ("Element not found: #login-form", "#login-form"),
        ("Element not found: #login-form", "#login-form"),  # 重复
        ("Element not found: .submit-btn", ".submit-btn"),  # 不同元素
        ("Element not found: #login-form", "#login-form"),  # 重复
    ]
    
    for i, (error_msg, selector) in enumerate(errors):
        should_log = error_manager.should_log_error(
            error_message=error_msg,
            error_type="ElementNotFoundError",
            selector=selector
        )
        
        if should_log:
            logger.error(f"[第{i+1}次] {error_msg}")
            print(f"✓ 第{i+1}次错误已记录: {selector}")
        else:
            print(f"✗ 第{i+1}次错误被抑制: {selector}")

def simulate_assertion_errors():
    """模拟断言错误"""
    print("\n=== 模拟断言错误 ===")
    
    error_manager = ErrorDeduplicationManager()
    
    # 模拟断言失败
    assertion_error = "Assertion failed: Expected 'Welcome' but got 'Error'"
    
    for i in range(5):
        should_log = error_manager.should_log_error(
            error_message=assertion_error,
            error_type="AssertionError"
        )
        
        if should_log:
            logger.error(f"[第{i+1}次] {assertion_error}")
            print(f"✓ 第{i+1}次断言错误已记录")
        else:
            print(f"✗ 第{i+1}次断言错误被抑制")

def demonstrate_time_window():
    """演示时间窗口功能"""
    print("\n=== 演示时间窗口功能 ===")
    
    # 创建一个短时间窗口的管理器用于演示
    config = {
        'error_deduplication': {
            'time_window': 2,  # 2秒时间窗口
            'max_same_error_count': 2,
            'enabled': True
        }
    }
    
    # 临时保存配置
    import yaml
    temp_config_file = project_root / "temp_config.yaml"
    with open(temp_config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)
    
    try:
        error_manager = ErrorDeduplicationManager(str(temp_config_file))
        
        error_msg = "Demo error for time window test"
        
        # 第一轮：在时间窗口内
        print("第一轮（时间窗口内）:")
        for i in range(3):
            should_log = error_manager.should_log_error(error_msg)
            print(f"  第{i+1}次: {'记录' if should_log else '抑制'}")
        
        print("等待时间窗口过期...")
        time.sleep(3)  # 等待时间窗口过期
        
        # 第二轮：时间窗口过期后
        print("第二轮（时间窗口过期后）:")
        for i in range(3):
            should_log = error_manager.should_log_error(error_msg)
            print(f"  第{i+1}次: {'记录' if should_log else '抑制'}")
    
    finally:
        # 清理临时配置文件
        if temp_config_file.exists():
            temp_config_file.unlink()

def show_statistics():
    """显示错误统计信息"""
    print("\n=== 错误统计信息 ===")
    
    error_manager = ErrorDeduplicationManager()
    
    # 生成一些错误
    errors = [
        "Timeout error A",
        "Timeout error A",  # 重复
        "Timeout error B",
        "Element not found error",
        "Element not found error",  # 重复
        "Assertion error",
    ]
    
    for error in errors:
        error_manager.should_log_error(error)
    
    # 获取统计信息
    stats = error_manager.get_error_statistics()
    
    print(f"总错误类型数: {stats['total_error_types']}")
    print(f"被抑制的错误数: {stats['suppressed_errors']}")
    print(f"活跃错误记录数: {stats['active_records']}")
    
    print("\n错误详情:")
    for error_hash, record in error_manager.error_records.items():
        print(f"  - {record.error_message[:50]}... (出现{record.count}次)")

def main():
    """主函数"""
    print("错误去重功能演示")
    print("=" * 50)
    
    # 运行各种演示
    simulate_timeout_errors()
    simulate_element_not_found_errors()
    simulate_assertion_errors()
    demonstrate_time_window()
    show_statistics()
    
    print("\n=== 演示完成 ===")
    print("\n配置说明:")
    print("- 可以通过 config/error_deduplication.yaml 文件自定义配置")
    print("- 支持不同错误类型的不同处理策略")
    print("- 支持自定义错误模式和忽略规则")
    print("- 支持时间窗口和错误计数限制")

if __name__ == "__main__":
    main()