"""页面操作装饰器模块
提供统一的错误处理、截图和性能监控功能
"""
import functools
import gc
import time
from typing import Callable

import allure
from pytest_check import check

from utils.logger import logger
from .error_deduplication import error_dedup_manager


class PerformanceMonitor:
    """性能监控器"""
    def __init__(self):
        self.operation_times = {}
        self.slow_operations = []
        
    def record_operation(self, operation_name: str, duration: float):
        """记录操作时间"""
        if operation_name not in self.operation_times:
            self.operation_times[operation_name] = []
        
        self.operation_times[operation_name].append(duration)
        
        # 记录慢操作（超过2秒）
        if duration > 2.0:
            self.slow_operations.append({
                'operation': operation_name,
                'duration': duration,
                'timestamp': time.time()
            })
            logger.warning(f"慢操作检测: {operation_name} 耗时 {duration:.2f}s")
    
    def get_average_time(self, operation_name: str) -> float:
        """获取操作平均时间"""
        times = self.operation_times.get(operation_name, [])
        return sum(times) / len(times) if times else 0.0

class ScreenshotManager:
    """截图管理器"""
    def __init__(self, max_screenshots: int = 10):
        self.screenshot_count = 0
        self.max_screenshots = max_screenshots
        
    def should_take_screenshot(self, force: bool = False) -> bool:
        """判断是否应该截图"""
        if force:
            return True
        return self.screenshot_count < self.max_screenshots
    
    def take_screenshot(self, page, name: str = "screenshot", force: bool = False):
        """智能截图"""
        if not self.should_take_screenshot(force):
            logger.debug("已达到最大截图数量限制，跳过截图")
            return
            
        try:
            # 压缩截图以减小文件大小
            screenshot = page.screenshot(
                quality=60,  # 降低质量
                type='jpeg'  # 使用JPEG格式
            )
            allure.attach(
                screenshot, 
                name=name, 
                attachment_type=allure.attachment_type.JPG
            )
            self.screenshot_count += 1
            logger.debug(f"截图成功: {name}")
        except Exception as e:
            logger.warning(f"截图失败: {e}")

# 全局实例
performance_monitor = PerformanceMonitor()
screenshot_manager = ScreenshotManager()

def performance_monitor_decorator(operation_name: str = None):
    """性能监控装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            name = operation_name or f"{func.__name__}"
            start_time = time.time()
            
            try:
                result = func(self, *args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                # 只有当操作耗时超过阈值时才记录慢操作警告，避免重复记录
                if duration > 5.0:  # 5秒阈值
                    logger.warning(f"慢操作检测: {name} 耗时 {duration:.3f}s")
                
        return wrapper
    return decorator

def handle_page_error(description: str = "操作") -> Callable:
    """统一的页面操作错误处理装饰器"""

    def decorator(func):
        @functools.wraps(func)
        @performance_monitor_decorator(f"{description}")
        def wrapper(self, *args, **kwargs):
            # 构建步骤描述
            operation_description = description
            selector = kwargs.get("selector", args[0] if args else None)

            # 记录操作内容
            if selector and isinstance(selector, str):
                operation_description += f"，操作元素: {selector}"

            try:
                with allure.step(f"{operation_description}"):
                    return func(self, *args, **kwargs)
                    
            except TimeoutError as e:
                # 构建明确的定位失败错误信息
                if selector:
                    error_msg = f"定位元素失败: 元素 '{selector}' 在指定时间内未找到"
                else:
                    error_msg = f"{operation_description} 操作超时: {str(e)}"
                
                # 检查错误去重
                from src.core.mixins.error_deduplication import error_dedup_manager
                if error_dedup_manager.should_log_error(error_msg):
                    logger.error(error_msg)
                
                # 标记错误已处理，避免上层重复记录
                setattr(e, "_logged", True)
                setattr(e, "_error_info", error_msg)
                
                # 智能截图
                screenshot_manager.take_screenshot(
                    self.page, 
                    name="定位失败截图"
                )
                
                raise TimeoutError(error_msg)

            except Exception as e:
                # 构建错误信息
                error_msg = f"{operation_description} 操作失败: {str(e)}"
                if selector:
                    error_msg += f"，元素: {selector}"

                # 标记错误已处理，避免上层重复记录
                setattr(e, "_logged", True)
                setattr(e, "_error_info", error_msg)
                
                # 智能截图（但不记录日志）
                screenshot_manager.take_screenshot(
                    self.page, 
                    name="错误截图"
                )
                
                raise Exception(error_msg)

        return wrapper
    return decorator

def check_and_screenshot(description="断言"):
    """断言装饰器，用于捕获断言失败并进行截图"""

    def decorator(func):
        @functools.wraps(func)
        @performance_monitor_decorator(f"断言_{description}")
        def wrapper(self, *args, **kwargs):
            step_description = description
            selector = kwargs.get("selector", args[0] if args else None)
            expected = kwargs.get("expected", args[1] if len(args) > 1 else None)
            
            if selector and isinstance(selector, str):
                step_description += f"，断言元素: {selector}"
            if expected:
                step_description += f"，断言值: {expected}"

            try:
                with allure.step(f"{step_description}"):
                    try:
                        return func(self, *args, **kwargs)
                    except AssertionError as e:
                        # 提取断言错误信息中的关键部分
                        simplified_error = f"断言失败：{step_description}"
                        error_str = str(e)
                        
                        # 尝试提取实际值
                        import re
                        actual_pattern = r"Actual value: ([^\n]*)"
                        actual_match = re.search(actual_pattern, error_str)
                        actual_text = actual_match.group(1) if actual_match else ""
                        
                        if actual_text:
                            simplified_error += f"，实际值: '{actual_text}'"
                        
                        # 智能截图
                        screenshot_manager.take_screenshot(
                            self.page, 
                            name="断言失败截图",
                            force=True  # 断言失败时强制截图
                        )

                        raise AssertionError(simplified_error)
                        
            except Exception as e:
                logger.error(f"断言失败********************************: {str(e)}")
                check.fail(e)

                if not hasattr(e, "_logged"):
                    # 检查是否应该记录错误（去重）
                    if error_dedup_manager.should_log_error(
                        error_message=str(e),
                        error_type=type(e).__name__
                    ):
                        logger.error(e)
                    setattr(e, "_logged", True)

                    # 通知步骤执行器
                    try:
                        from src.automation.step_executor import StepExecutor
                        # 搜索内存中的所有 StepExecutor 实例
                        for obj in gc.get_objects():
                            if isinstance(obj, StepExecutor):
                                obj.step_has_error = True
                                obj.has_error = True
                                setattr(obj, "_last_assertion_error", str(e))
                                break
                    except ImportError:
                        pass  # 如果找不到 StepExecutor，忽略

                raise AssertionError(e)

        return wrapper
    return decorator

def memory_cleanup(threshold: int = 100):
    """内存清理装饰器"""
    def decorator(func):
        operation_count = 0
        
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            nonlocal operation_count
            operation_count += 1
            
            try:
                result = func(self, *args, **kwargs)
                
                # 定期清理内存
                if operation_count % threshold == 0:
                    # 元素定位缓存清理代码已移除
                    if hasattr(self, 'variable_manager'):
                        # 假设变量管理器有清理方法
                        if hasattr(self.variable_manager, 'cleanup_temp_variables'):
                            self.variable_manager.cleanup_temp_variables()
                    
                    gc.collect()
                    logger.debug(f"执行内存清理 (操作计数: {operation_count})")
                
                return result
            except Exception as e:
                raise
                
        return wrapper
    return decorator

def attach_screenshot(page, name="screenshot"):
    """将屏幕截图添加到 Allure 报告"""
    screenshot_manager.take_screenshot(page, name)
