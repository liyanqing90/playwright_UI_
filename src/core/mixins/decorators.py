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
            self.slow_operations.append(
                {
                    "operation": operation_name,
                    "duration": duration,
                    "timestamp": time.time(),
                }
            )
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
                quality=60, type="jpeg"  # 降低质量  # 使用JPEG格式
            )
            allure.attach(
                screenshot, name=name, attachment_type=allure.attachment_type.JPG
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
                    if hasattr(self, "variable_manager"):
                        # 假设变量管理器有清理方法
                        if hasattr(self.variable_manager, "cleanup_temp_variables"):
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
