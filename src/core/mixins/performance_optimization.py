"""性能优化混入类"""
import time
import hashlib
from typing import Dict, Any, Optional, Tuple
from playwright.sync_api import Locator
from utils.logger import logger
from .decorators import handle_page_error
from config.constants import DEFAULT_TIMEOUT


class PerformanceOptimizationMixin:
    """性能优化混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 截图管理
        self._screenshot_count = 0
        self._max_screenshots = 50  # 最大截图数量
        self._last_screenshot_time = 0
        self._screenshot_interval = 1  # 截图间隔(秒)





    def _should_take_screenshot(self) -> bool:
        """判断是否应该截图"""
        current_time = time.time()
        
        # 检查截图数量限制
        if self._screenshot_count >= self._max_screenshots:
            logger.debug(f"截图数量已达上限: {self._max_screenshots}")
            return False
        
        # 检查截图间隔
        if current_time - self._last_screenshot_time < self._screenshot_interval:
            logger.debug(f"截图间隔不足: {current_time - self._last_screenshot_time:.1f}s")
            return False
        
        return True

    def _smart_screenshot(self, name: str = "screenshot", force: bool = False) -> Optional[bytes]:
        """智能截图管理"""
        if not force and not self._should_take_screenshot():
            return None
        
        try:
            screenshot = self.page.screenshot()
            self._screenshot_count += 1
            self._last_screenshot_time = time.time()
            
            logger.debug(f"截图成功: {name} (第{self._screenshot_count}张)")
            return screenshot
            
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None

    @handle_page_error(description="设置截图配置")
    def configure_screenshots(
        self,
        max_screenshots: Optional[int] = None,
        screenshot_interval: Optional[float] = None
    ):
        """
        配置截图参数

        Args:
            max_screenshots: 最大截图数量
            screenshot_interval: 截图间隔(秒)
        """
        if max_screenshots is not None:
            self._max_screenshots = max_screenshots
            logger.info(f"设置最大截图数量: {max_screenshots}")
        
        if screenshot_interval is not None:
            self._screenshot_interval = screenshot_interval
            logger.info(f"设置截图间隔: {screenshot_interval}秒")

    @handle_page_error(description="重置截图计数")
    def reset_screenshot_count(self):
        """重置截图计数"""
        old_count = self._screenshot_count
        self._screenshot_count = 0
        self._last_screenshot_time = 0
        logger.info(f"重置截图计数: {old_count} -> 0")

    @handle_page_error(description="批量预加载元素")
    def preload_elements(self, selectors: list, timeout: int = DEFAULT_TIMEOUT):
        """
        批量预加载元素到缓存

        Args:
            selectors: 元素选择器列表
            timeout: 超时时间
        """
        logger.info(f"批量预加载元素: {len(selectors)} 个")
        
        successful = 0
        failed = 0
        
        for selector in selectors:
            try:
                # 替换变量
                resolved_selector = self.variable_manager.replace_variables_refactored(selector)
                # 创建定位器并等待
                locator = self.page.locator(resolved_selector)
                locator.wait_for(state="attached", timeout=timeout)
                successful += 1
                logger.debug(f"预加载成功: {selector}")
            except Exception as e:
                failed += 1
                logger.warning(f"预加载失败: {selector} - {e}")
        
        logger.info(f"批量预加载完成: 成功 {successful}, 失败 {failed}")

    @handle_page_error(description="元素存在性快速检查")
    def quick_element_check(self, selector: str, use_cache: bool = True) -> bool:
        """
        快速检查元素是否存在（不等待）

        Args:
            selector: 元素选择器
            use_cache: 是否使用缓存

        Returns:
            元素是否存在
        """
        try:
            # 尝试从缓存获取
            if use_cache:
                cached_locator = self._get_cached_element(selector)
                if cached_locator:
                    try:
                        return cached_locator.count() > 0
                    except Exception:
                        pass
            
            # 快速检查（不等待）
            resolved_selector = self.variable_manager.replace_variables_refactored(selector)
            locator = self.page.locator(resolved_selector)
            return locator.count() > 0
            
        except Exception:
            return False

    @handle_page_error(description="获取元素数量")
    def get_element_count_cached(self, selector: str, use_cache: bool = True) -> int:
        """
        获取元素数量（带缓存）

        Args:
            selector: 元素选择器
            use_cache: 是否使用缓存

        Returns:
            元素数量
        """
        try:
            # 尝试从缓存获取
            if use_cache:
                cached_locator = self._get_cached_element(selector)
                if cached_locator:
                    try:
                        return cached_locator.count()
                    except Exception:
                        pass
            
            # 创建新的定位器
            resolved_selector = self.variable_manager.replace_variables_refactored(selector)
            locator = self.page.locator(resolved_selector)
            count = locator.count()
            
            # 如果元素存在，缓存定位器
            if use_cache and count > 0:
                self._cache_element(selector, locator)
            
            return count
            
        except Exception as e:
            logger.error(f"获取元素数量失败: {selector} - {e}")
            return 0

    @handle_page_error(description="性能监控装饰器")
    def monitor_performance(self, operation_name: str):
        """
        性能监控上下文管理器

        Args:
            operation_name: 操作名称
        """
        class PerformanceMonitor:
            def __init__(self, name: str, parent):
                self.name = name
                self.parent = parent
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                logger.debug(f"开始监控: {self.name}")
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                elapsed = time.time() - self.start_time
                if exc_type is None:
                    logger.info(f"操作完成: {self.name} - 耗时 {elapsed:.3f}s")
                else:
                    logger.error(f"操作失败: {self.name} - 耗时 {elapsed:.3f}s - {exc_val}")
                
                # 清理过期缓存
                self.parent._clear_expired_cache()
        
        return PerformanceMonitor(operation_name, self)

    @handle_page_error(description="优化页面加载")
    def optimize_page_load(self, disable_images: bool = False, disable_css: bool = False):
        """
        优化页面加载性能

        Args:
            disable_images: 是否禁用图片加载
            disable_css: 是否禁用CSS加载
        """
        logger.info(f"优化页面加载: 禁用图片={disable_images}, 禁用CSS={disable_css}")
        
        def handle_route(route):
            resource_type = route.request.resource_type
            
            if disable_images and resource_type == "image":
                route.abort()
                return
            
            if disable_css and resource_type == "stylesheet":
                route.abort()
                return
            
            route.continue_()
        
        if disable_images or disable_css:
            self.page.route("**/*", handle_route)
            logger.info("页面加载优化已启用")

    @handle_page_error(description="内存使用统计")
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取内存使用统计

        Returns:
            内存统计信息
        """
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        stats = {
            "rss_mb": memory_info.rss / 1024 / 1024,  # 物理内存
            "vms_mb": memory_info.vms / 1024 / 1024,  # 虚拟内存
            "cache_count": len(self._element_cache),
            "screenshot_count": self._screenshot_count,
        }
        
        logger.info(f"内存统计: {stats}")
        return stats