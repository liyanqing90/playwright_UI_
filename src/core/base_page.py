import os
import time
from typing import Literal
from playwright.sync_api import Page

from config.constants import DEFAULT_TIMEOUT
from utils.logger import logger
from utils.variable_manager import VariableManager
from utils.performance_manager import performance_manager

# 导入新的混入模块
from .mixins.element_operations import ElementOperationsMixin
from .mixins.wait_operations import WaitOperationsMixin
from .mixins.navigation_operations import NavigationOperationsMixin
from .mixins.window_operations import WindowOperationsMixin
from .mixins.keyboard_operations import KeyboardOperationsMixin
from .mixins.file_operations import FileOperationsMixin
from .mixins.network_monitoring import NetworkMonitoringMixin
from .mixins.javascript_operations import JavaScriptOperationsMixin
from .mixins.variable_management import VariableManagementMixin
from .mixins.performance_optimization import PerformanceOptimizationMixin
from .mixins.assertion_operations import AssertionOperationsMixin
from .mixins.decorators import handle_page_error, check_and_screenshot


# 装饰器已移至 mixins/decorators.py 中


def base_url():
    return os.environ.get("BASE_URL")


class BasePage(
    ElementOperationsMixin,
    WaitOperationsMixin,
    NavigationOperationsMixin,
    WindowOperationsMixin,
    KeyboardOperationsMixin,
    FileOperationsMixin,
    NetworkMonitoringMixin,
    JavaScriptOperationsMixin,
    VariableManagementMixin,
    PerformanceOptimizationMixin,
    AssertionOperationsMixin
):
    def __init__(self, page: Page):
        self.page = page
        self.pages = [self.page]
        self.variable_manager = VariableManager()
        
        # 初始化所有混入模块
        super().__init__()
        
        # 设置页面事件处理器
        self._setup_page_handlers()
        
        # 初始化性能优化相关属性
        self._screenshot_count = 0
        self._last_screenshot_time = 0

    def _setup_page_handlers(self):
        """设置页面事件处理器"""
        def handle_page_error(exc):
            error_msg = str(exc)
            # 过滤掉一些不重要的错误
            if "The play() request was interrupted" in error_msg:
                logger.debug(f"页面媒体播放中断（可忽略）: {error_msg}")
            else:
                logger.error(f"页面错误: {exc}")

        self.page.on("pageerror", handle_page_error)
        self.page.on("crash", lambda: logger.error("页面崩溃"))

    def _locator(
        self,
        selector: str,
        state: Literal["attached", "detached", "hidden", "visible"] = "visible",
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """统一的高性能元素定位与等待方法"""
        start_time = time.time()
        
        try:
            # 替换变量
            resolved_selector = self.variable_manager.replace_variables_refactored(selector)
            
            # 创建定位器
            locator = self.page.locator(resolved_selector)
            
            # 使用配置的超时时间
            actual_timeout = timeout if timeout != DEFAULT_TIMEOUT else performance_manager.get_default_timeout()
            
            # 等待元素状态 - 使用first避免严格模式违规
            locator.first.wait_for(state=state, timeout=actual_timeout)
            
            duration = time.time() - start_time
            performance_manager.record_operation(duration, f"locator_{selector}")
            
            return locator
            
        except Exception as e:
            error_msg = str(e)
            # 只记录性能数据，不记录错误日志
            duration = time.time() - start_time
            performance_manager.record_operation(duration, f"locator_failed_{selector}")
            
            # 标记错误已处理
            setattr(e, "_logged", True)
            raise Exception(f"定位或等待元素 {selector} 失败 (state={state}): {error_msg}")

    @handle_page_error(description="暂停")
    def pause(self):
        self.page.pause()

    def close(self):
        self.page.close()


    @handle_page_error(description="进入iframe")
    def enter_frame(self, selector: str):
        """进入iframe"""
        self._locator(selector, state="attached")
        return self.page.frame_locator(selector)
