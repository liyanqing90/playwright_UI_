"""窗口管理操作混入类"""
import allure
from playwright.sync_api import Page
from utils.logger import logger
from .decorators import handle_page_error


class WindowOperationsMixin:
    """窗口管理操作混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @handle_page_error(description="切换窗口")
    def switch_window(self, value: int = 0):
        """切换到指定窗口（修复逻辑错误）"""
        if value < 0 or value >= len(self.pages):
            raise ValueError(f"无效的窗口索引: {value}，当前窗口数量: {len(self.pages)}")
        
        with allure.step(f"切换到窗口索引: {value}"):
            self.page = self.pages[value]
            logger.info(f"成功切换到窗口索引: {value}")

    @handle_page_error(description="关闭当前窗口")
    def close_window(self):
        """关闭当前窗口"""
        if len(self.page.context.pages) == 1:
            raise RuntimeError("无法关闭最后一个窗口")
        
        with allure.step("关闭当前窗口"):
            self.page.close()
            # 切换到最后一个可用窗口
            self.page = self.page.context.pages[-1]
            # 更新页面列表
            self.pages = self.page.context.pages
            logger.info("当前窗口已关闭，切换到最后一个窗口")

    @handle_page_error(description="等待新窗口打开")
    def wait_for_new_window(self) -> Page:
        """等待新窗口打开并返回新窗口"""
        with allure.step("等待新窗口打开"):
            with self.page.context.expect_page() as new_page_info:
                new_page = new_page_info.value
                new_page.wait_for_load_state()
                # 更新页面列表
                self.pages = self.page.context.pages
                logger.info(f"新窗口已打开，当前窗口数量: {len(self.pages)}")
                return new_page

    @handle_page_error(description="获取窗口数量")
    def get_window_count(self) -> int:
        """获取当前窗口数量"""
        count = len(self.page.context.pages)
        logger.debug(f"当前窗口数量: {count}")
        return count

    @handle_page_error(description="获取所有窗口标题")
    def get_all_window_titles(self) -> list[str]:
        """获取所有窗口的标题"""
        titles = []
        for page in self.page.context.pages:
            try:
                title = page.title()
                titles.append(title)
            except Exception as e:
                logger.warning(f"获取窗口标题失败: {e}")
                titles.append("未知标题")
        
        logger.debug(f"所有窗口标题: {titles}")
        return titles

    @handle_page_error(description="根据标题切换窗口")
    def switch_window_by_title(self, title: str):
        """根据窗口标题切换窗口"""
        for i, page in enumerate(self.page.context.pages):
            try:
                if page.title() == title:
                    with allure.step(f"切换到标题为 '{title}' 的窗口"):
                        self.page = page
                        logger.info(f"成功切换到标题为 '{title}' 的窗口")
                        return
            except Exception as e:
                logger.warning(f"检查窗口标题失败: {e}")
                continue
        
        raise ValueError(f"未找到标题为 '{title}' 的窗口")

    @handle_page_error(description="根据URL切换窗口")
    def switch_window_by_url(self, url_pattern: str):
        """根据URL模式切换窗口"""
        import re
        
        for i, page in enumerate(self.page.context.pages):
            try:
                if re.search(url_pattern, page.url):
                    with allure.step(f"切换到URL匹配 '{url_pattern}' 的窗口"):
                        self.page = page
                        logger.info(f"成功切换到URL匹配 '{url_pattern}' 的窗口: {page.url}")
                        return
            except Exception as e:
                logger.warning(f"检查窗口URL失败: {e}")
                continue
        
        raise ValueError(f"未找到URL匹配 '{url_pattern}' 的窗口")