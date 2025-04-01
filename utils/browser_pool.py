import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from loguru import logger
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from utils.config import Config


class BrowserInstance:
    """浏览器实例包装类，包含实例本身以及状态信息"""

    def __init__(self, browser: Browser, browser_type: str):
        self.browser = browser
        self.browser_type = browser_type
        self.created_at = datetime.now()
        self.last_used_at = datetime.now()
        self.is_in_use = False
        self.health_check_time = datetime.now()
        self.health_status = True
        self.contexts: List[BrowserContext] = []
        self.error_count = 0
        self.stats = {
            "contexts_created": 0,
            "pages_created": 0,
            "errors": 0,
            "memory_usage": 0,
        }

    def mark_as_used(self):
        """标记浏览器实例为使用中"""
        self.is_in_use = True
        self.last_used_at = datetime.now()

    def mark_as_idle(self):
        """标记浏览器实例为空闲"""
        self.is_in_use = False
        self.last_used_at = datetime.now()

    def record_error(self):
        """记录错误次数"""
        self.error_count += 1
        self.stats["errors"] += 1

    def add_context(self, context: BrowserContext):
        """添加创建的上下文"""
        self.contexts.append(context)
        self.stats["contexts_created"] += 1

    def remove_context(self, context: BrowserContext):
        """移除上下文"""
        if context in self.contexts:
            self.contexts.remove(context)

    def record_page_created(self):
        """记录创建的页面数量"""
        self.stats["pages_created"] += 1

    def update_health_status(self, status: bool):
        """更新健康状态"""
        self.health_status = status
        self.health_check_time = datetime.now()

    def update_memory_usage(self, memory_usage: int):
        """更新内存使用情况"""
        self.stats["memory_usage"] = memory_usage

    def is_healthy(self) -> bool:
        """检查实例是否健康"""
        # 浏览器实例已标记为不健康
        if not self.health_status:
            return False

        # 错误次数过多
        if self.error_count > 10:
            return False

        # 浏览器实例太旧（超过8小时）
        if datetime.now() - self.created_at > timedelta(hours=8):
            return False

        return True

    def get_context_count(self) -> int:
        """获取当前上下文数量"""
        return len(self.contexts)

    def close(self):
        """关闭浏览器实例及所有相关资源"""
        try:
            for context in self.contexts[:]:  # 使用副本进行迭代
                try:
                    context.close()
                except Exception as e:
                    logger.error(f"关闭浏览器上下文时出错: {e}")
                self.contexts.remove(context)

            self.browser.close()
            logger.debug(f"浏览器实例已关闭，使用时间: {datetime.now() - self.created_at}")
        except Exception as e:
            logger.error(f"关闭浏览器实例时出错: {e}")


class BrowserPool:
    """浏览器资源池管理类"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BrowserPool, cls).__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._browser_instances: Dict[str, Dict[str, Any]] = {}
            self._context_pool: Dict[str, Dict[str, Any]] = {}
            self._page_pool: Dict[str, Dict[str, Any]] = {}
            self._stats = {
                'total_instances': 0,
                'active_instances': 0,
                'reused_instances': 0,
                'failed_instances': 0
            }
            self.config = Config()
            self.playwright = None

    def get_browser(self) -> tuple[BrowserInstance, bool]:
        """
        获取浏览器实例，如果没有可用实例则创建新实例
        
        Returns:
            tuple[BrowserInstance, bool]: (浏览器实例, 是否为新创建的实例)
        """
        with self._lock:
            # 尝试获取空闲的浏览器实例
            for project_name, browser_info in self._browser_instances.items():
                if not browser_info['is_active'] and browser_info['browser'].is_connected():
                    browser_info['is_active'] = True
                    browser_info['last_used'] = datetime.now()
                    self._stats['reused_instances'] += 1
                    return BrowserInstance(browser_info['browser'], self.config.browser.value), False

            # 如果没有可用实例，创建新实例
            if not self.playwright:
                self.playwright = sync_playwright().start()

            browser_type = getattr(self.playwright, self.config.browser.value)
            browser = browser_type.launch(headless=not self.config.headed)

            browser_info = {
                'browser': browser,
                'created_at': datetime.now(),
                'last_used': datetime.now(),
                'is_active': True
            }

            self._browser_instances[self.config.project.value] = browser_info
            self._stats['total_instances'] += 1
            self._stats['active_instances'] += 1

            return BrowserInstance(browser, self.config.browser.value), True

    def create_browser_context(self, context_options: Optional[dict] = None) -> BrowserContext:
        """
        创建新的浏览器上下文
        
        Args:
            context_options: 上下文配置选项
            
        Returns:
            BrowserContext: 新创建的浏览器上下文
        """
        browser_instance, _ = self.get_browser()
        context = browser_instance.browser.new_context(**(context_options or {}))
        browser_instance.add_context(context)
        return context

    def release_browser(self, browser_instance: BrowserInstance):
        """
        释放浏览器实例回池中
        
        Args:
            browser_instance: 要释放的浏览器实例
        """
        with self._lock:
            for project_name, browser_info in self._browser_instances.items():
                if browser_info['browser'] == browser_instance.browser:
                    browser_info['is_active'] = False
                    browser_info['last_used'] = datetime.now()
                    self._stats['active_instances'] -= 1
                    break

    def register_browser(self, browser: Browser, project_name: str) -> None:
        """
        注册新的浏览器实例
        
        Args:
            browser: Playwright浏览器实例
            project_name: 项目名称
        """
        with self._lock:
            if project_name not in self._browser_instances:
                self._browser_instances[project_name] = {
                    'browser': browser,
                    'created_at': datetime.now(),
                    'last_used': datetime.now(),
                    'is_active': True
                }
                self._stats['total_instances'] += 1
                self._stats['active_instances'] += 1
                logger.info(f"注册新浏览器实例: {project_name}")

    def get_context(self, project_name: str, browser: Browser) -> Optional[BrowserContext]:
        """
        获取或创建浏览器上下文
        
        Args:
            project_name: 项目名称
            browser: 浏览器实例
            
        Returns:
            BrowserContext实例
        """
        with self._lock:
            if project_name in self._context_pool:
                context_info = self._context_pool[project_name]
                if context_info['is_active']:
                    context_info['last_used'] = datetime.now()
                    return context_info['context']

            # 创建新的上下文
            context = browser.new_context()
            self._context_pool[project_name] = {
                'context': context,
                'created_at': datetime.now(),
                'last_used': datetime.now(),
                'is_active': True
            }
            return context

    def get_page(self, project_name: str, context: BrowserContext) -> Page:
        """
        获取或创建页面实例
        
        Args:
            project_name: 项目名称
            context: 浏览器上下文
            
        Returns:
            Page实例
        """
        with self._lock:
            if project_name in self._page_pool:
                page_info = self._page_pool[project_name]
                if page_info['is_active']:
                    page_info['last_used'] = datetime.now()
                    return page_info['page']

            # 创建新的页面
            page = context.new_page()
            self._page_pool[project_name] = {
                'page': page,
                'created_at': datetime.now(),
                'last_used': datetime.now(),
                'is_active': True
            }
            return page

    def release_resources(self, project_name: str) -> None:
        """
        释放项目相关的所有资源
        
        Args:
            project_name: 项目名称
        """
        with self._lock:
            # 释放页面
            if project_name in self._page_pool:
                page_info = self._page_pool[project_name]
                if page_info['is_active']:
                    try:
                        page_info['page'].close()
                    except Exception as e:
                        logger.error(f"关闭页面失败: {e}")
                    page_info['is_active'] = False

            # 释放上下文
            if project_name in self._context_pool:
                context_info = self._context_pool[project_name]
                if context_info['is_active']:
                    try:
                        context_info['context'].close()
                    except Exception as e:
                        logger.error(f"关闭上下文失败: {e}")
                    context_info['is_active'] = False

            # 更新浏览器实例状态
            if project_name in self._browser_instances:
                browser_info = self._browser_instances[project_name]
                if browser_info['is_active']:
                    browser_info['is_active'] = False
                    self._stats['active_instances'] -= 1

    def get_stats(self) -> Dict[str, int]:
        """
        获取资源池统计信息
        
        Returns:
            统计信息字典
        """
        return self._stats.copy()

    def cleanup_inactive_resources(self, timeout_seconds: int = 300) -> None:
        """
        清理超时的非活动资源
        
        Args:
            timeout_seconds: 超时时间（秒）
        """
        with self._lock:
            current_time = datetime.now()

            # 清理页面
            for project_name, page_info in list(self._page_pool.items()):
                if not page_info['is_active'] and \
                        (current_time - page_info['last_used']).total_seconds() > timeout_seconds:
                    try:
                        page_info['page'].close()
                    except Exception as e:
                        logger.error(f"清理页面失败: {e}")
                    del self._page_pool[project_name]

            # 清理上下文
            for project_name, context_info in list(self._context_pool.items()):
                if not context_info['is_active'] and \
                        (current_time - context_info['last_used']).total_seconds() > timeout_seconds:
                    try:
                        context_info['context'].close()
                    except Exception as e:
                        logger.error(f"清理上下文失败: {e}")
                    del self._context_pool[project_name]

    def shutdown(self):
        """关闭资源池，释放所有资源"""
        logger.info("正在关闭浏览器资源池...")
        self._shutdown = True

        # 关闭所有浏览器实例
        with self._lock:
            for project_name, browser_info in list(self._browser_instances.items()):
                try:
                    browser_info['browser'].close()
                except Exception as e:
                    logger.error(f"关闭浏览器实例时出错: {e}")
            self._browser_instances.clear()

        # 关闭Playwright
        if self.playwright:
            try:
                self.playwright.stop()
                self.playwright = None
            except Exception as e:
                logger.error(f"关闭Playwright时出错: {e}")

        logger.info("浏览器资源池已关闭")

    def __del__(self):
        """析构函数，确保资源被释放"""
        try:
            if hasattr(self, '_initialized') and self._initialized:
                self.shutdown()
        except:
            pass
