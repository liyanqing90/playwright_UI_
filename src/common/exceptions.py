"""自动化框架统一异常处理模块

本模块定义了框架中使用的所有自定义异常类，提供统一的异常处理机制。
"""

from typing import Optional, Dict, Any

class AutomationError(Exception):
    """自动化框架基础异常
    
    所有框架自定义异常的基类。
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message

class ElementNotFoundError(AutomationError):
    """元素未找到异常
    
    当页面元素无法定位时抛出此异常。
    """
    
    def __init__(self, selector: str, timeout: Optional[int] = None, page_url: Optional[str] = None):
        self.selector = selector
        self.timeout = timeout
        self.page_url = page_url
        
        message = f"Element not found: {selector}"
        if timeout:
            message += f" (timeout: {timeout}ms)"
        if page_url:
            message += f" on page: {page_url}"
            
        details = {
            "selector": selector,
            "timeout": timeout,
            "page_url": page_url
        }
        
        super().__init__(message, details)

class CommandExecutionError(AutomationError):
    """命令执行异常
    
    当自动化命令执行失败时抛出此异常。
    """
    
    def __init__(self, command: str, reason: str, step_data: Optional[Dict[str, Any]] = None):
        self.command = command
        self.reason = reason
        self.step_data = step_data
        
        message = f"Command '{command}' failed: {reason}"
        
        details = {
            "command": command,
            "reason": reason,
            "step_data": step_data
        }
        
        super().__init__(message, details)

class ConfigurationError(AutomationError):
    """配置错误异常
    
    当配置文件或配置项有问题时抛出此异常。
    """
    
    def __init__(self, config_key: str, config_file: Optional[str] = None, expected_type: Optional[str] = None):
        self.config_key = config_key
        self.config_file = config_file
        self.expected_type = expected_type
        
        message = f"Configuration error for key: {config_key}"
        if config_file:
            message += f" in file: {config_file}"
        if expected_type:
            message += f" (expected type: {expected_type})"
            
        details = {
            "config_key": config_key,
            "config_file": config_file,
            "expected_type": expected_type
        }
        
        super().__init__(message, details)

class ValidationError(AutomationError):
    """验证错误异常
    
    当数据验证失败时抛出此异常。
    """
    
    def __init__(self, field: str, value: Any, expected: str, validation_rule: Optional[str] = None):
        self.field = field
        self.value = value
        self.expected = expected
        self.validation_rule = validation_rule
        
        message = f"Validation failed for field '{field}': got {value}, expected {expected}"
        if validation_rule:
            message += f" (rule: {validation_rule})"
            
        details = {
            "field": field,
            "value": value,
            "expected": expected,
            "validation_rule": validation_rule
        }
        
        super().__init__(message, details)

class NetworkError(AutomationError):
    """网络错误异常
    
    当网络请求失败时抛出此异常。
    """
    
    def __init__(self, url: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        self.url = url
        self.status_code = status_code
        self.response_text = response_text
        
        message = f"Network error for URL: {url}"
        if status_code:
            message += f" (status: {status_code})"
            
        details = {
            "url": url,
            "status_code": status_code,
            "response_text": response_text
        }
        
        super().__init__(message, details)

class TimeoutError(AutomationError):
    """超时错误异常
    
    当操作超时时抛出此异常。
    """
    
    def __init__(self, operation: str, timeout: int, actual_time: Optional[float] = None):
        self.operation = operation
        self.timeout = timeout
        self.actual_time = actual_time
        
        message = f"Operation '{operation}' timed out after {timeout}ms"
        if actual_time:
            message += f" (actual time: {actual_time:.2f}ms)"
            
        details = {
            "operation": operation,
            "timeout": timeout,
            "actual_time": actual_time
        }
        
        super().__init__(message, details)

class BrowserError(AutomationError):
    """浏览器错误异常
    
    当浏览器操作失败时抛出此异常。
    """
    
    def __init__(self, browser_type: str, operation: str, error_message: str):
        self.browser_type = browser_type
        self.operation = operation
        self.error_message = error_message
        
        message = f"Browser error in {browser_type} during {operation}: {error_message}"
        
        details = {
            "browser_type": browser_type,
            "operation": operation,
            "error_message": error_message
        }
        
        super().__init__(message, details)

class DataError(AutomationError):
    """数据错误异常
    
    当测试数据有问题时抛出此异常。
    """
    
    def __init__(self, data_source: str, data_key: Optional[str] = None, error_type: str = "missing"):
        self.data_source = data_source
        self.data_key = data_key
        self.error_type = error_type
        
        message = f"Data error in {data_source}"
        if data_key:
            message += f" for key '{data_key}'"
        message += f": {error_type}"
        
        details = {
            "data_source": data_source,
            "data_key": data_key,
            "error_type": error_type
        }
        
        super().__init__(message, details)

class AssertionError(AutomationError):
    """断言错误异常
    
    当断言失败时抛出此异常。
    """
    
    def __init__(self, assertion_type: str, expected: Any, actual: Any, message: Optional[str] = None):
        self.assertion_type = assertion_type
        self.expected = expected
        self.actual = actual
        
        error_message = message or f"Assertion failed: expected {expected}, got {actual}"
        
        details = {
            "assertion_type": assertion_type,
            "expected": expected,
            "actual": actual
        }
        
        super().__init__(error_message, details)