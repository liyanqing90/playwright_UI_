"""基础页面类

采用组合模式重构的BasePage，通过依赖注入获取各种服务。
"""

from typing import Optional, Any, Dict

from playwright.sync_api import Page, Browser, BrowserContext

from config.constants import DEFAULT_TIMEOUT
from utils.logger import logger
from .config import ConfigLoader, EnvironmentManager
from .container import ServiceContainer
from .services.assertion_service import AssertionOperations
from .services.element_service import ElementOperations
from .services.navigation_service import NavigationOperations
from .services.variable_service import VariableOperations
from .services.wait_service import WaitOperations


class BasePage:
    """基础页面类

    采用组合模式，通过依赖注入获取各种服务，
    避免了传统继承模式的复杂性和耦合问题。
    """

    def __init__(
        self,
        page: Optional[Page] = None,
        browser: Optional[Browser] = None,
        context: Optional[BrowserContext] = None,
        container: Optional[ServiceContainer] = None,
        config_loader: Optional[ConfigLoader] = None,
        environment_manager: Optional[EnvironmentManager] = None,
        base_url: Optional[str] = None,
        service_group: str = "full_page",
    ):
        """初始化BasePage

        Args:
            page: Playwright页面对象
            browser: Playwright浏览器对象
            context: Playwright浏览器上下文
            container: 服务容器，如果为None则创建新的容器
            config_loader: 配置加载器
            environment_manager: 环境管理器
            base_url: 基础URL
            service_group: 要使用的服务组名称
        """
        self.page = page
        self.browser = browser
        self.context = context
        self.base_url = base_url
        self.service_group = service_group

        # 初始化配置管理
        self.config_loader = config_loader or ConfigLoader()
        self.environment_manager = environment_manager or EnvironmentManager()

        # 初始化服务容器（使用单例模式）
        if container is None:
            from .container_singleton import ServiceContainerSingleton

            # 检查是否是首次初始化
            is_first_init = not ServiceContainerSingleton.is_initialized()
            self.container = ServiceContainerSingleton.get_instance(
                config_loader=self.config_loader,
                environment_manager=self.environment_manager,
            )
            # 注册指定的服务组（仅在首次初始化时）
            if is_first_init:
                self.container.register_service_group(service_group)
        else:
            self.container = container

        # 注册默认服务（如果需要）
        self._register_default_services()

        # 解析服务实例
        self._resolve_services()

        logger.debug(f"BasePage已初始化，使用服务组: {service_group}")

    def _register_default_services(self):
        """注册默认服务（仅在需要时）"""
        # 检查是否已经通过配置注册了服务
        try:
            # 尝试解析核心服务，如果失败则注册默认实现
            from .services.element_service import ElementService
            from .services.navigation_service import NavigationService
            from .services.wait_service import WaitService
            from .services.assertion_service import AssertionService
            from .services.variable_service import VariableService

            # 只有在服务尚未注册时才注册默认实现
            if not self.container.is_registered(ElementOperations):
                self.container.register_implementation(
                    ElementOperations, ElementService
                )
                logger.debug("注册默认ElementService")

            if not self.container.is_registered(NavigationOperations):
                self.container.register_implementation(
                    NavigationOperations, NavigationService
                )
                logger.debug("注册默认NavigationService")

            if not self.container.is_registered(WaitOperations):
                self.container.register_implementation(WaitOperations, WaitService)
                logger.debug("注册默认WaitService")

            if not self.container.is_registered(AssertionOperations):
                self.container.register_implementation(
                    AssertionOperations, AssertionService
                )
                logger.debug("注册默认AssertionService")

            if not self.container.is_registered(VariableOperations):
                self.container.register_implementation(
                    VariableOperations, VariableService
                )
                logger.debug("注册默认VariableService")

        except ImportError as e:
            logger.warning(f"导入服务类失败，跳过默认服务注册: {e}")

    def _resolve_services(self):
        """解析服务实例"""
        try:
            # 解析服务实例
            self.element_service = self.container.resolve(ElementOperations)
            self.navigation_service = self.container.resolve(NavigationOperations)
            self.wait_service = self.container.resolve(WaitOperations)
            self.assertion_service = self.container.resolve(AssertionOperations)
            self.variable_service = self.container.resolve(VariableOperations)

            # 为了兼容性，添加别名
            self.variable_manager = self.variable_service

            # 设置页面对象到服务中
            self._inject_page_to_services()

            logger.debug("服务解析完成")

        except Exception as e:
            logger.error(f"服务解析失败: {e}")
            raise

    def _inject_page_to_services(self):
        """将页面对象注入到服务中"""
        if self.page:
            services = [
                self.element_service,
                self.navigation_service,
                self.wait_service,
                self.assertion_service,
            ]

            for service in services:
                if hasattr(service, "set_page"):
                    service.set_page(self.page)
                elif hasattr(service, "page"):
                    service.page = self.page

    # ==================== 页面基础操作 ====================

    def goto(self, url: str, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """导航到指定URL

        Args:
            url: 目标URL
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        # 处理相对URL
        if self.base_url and not url.startswith(("http://", "https://")):
            url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"

        # 替换变量
        url = self.variable_service.replace_variables(url)

        self.navigation_service.goto(page=self.page, url=url, timeout=timeout)

    def navigate(self, url: str, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """导航到指定URL (navigate方法的别名)

        Args:
            url: 目标URL
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
        """
        return self.goto(url=url, timeout=timeout)

    def reload(self, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """重新加载页面

        Args:
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.navigation_service.reload(page=self.page, timeout=timeout)

    def go_back(self, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """后退

        Args:
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.navigation_service.go_back(page=self.page, timeout=timeout)

    def go_forward(self, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """前进

        Args:
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.navigation_service.go_forward(page=self.page, timeout=timeout)

    def get_url(self) -> str:
        """获取当前URL"""
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        return self.navigation_service.get_url(page=self.page)

    def get_title(self) -> str:
        """获取页面标题"""
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        return self.navigation_service.get_title(page=self.page)

    # ==================== 元素操作 ====================

    def click(self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """点击元素

        Args:
            selector: 选择器
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.element_service.click(page=self.page, selector=selector, timeout=timeout)

    def fill(
        self,
        selector: str,
        value: str,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> None:
        """填充输入框

        Args:
            selector: 选择器
            value: 要填写的值
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        value = self.variable_service.replace_variables(value)
        self.element_service.fill(
            page=self.page, selector=selector, value=value, timeout=timeout
        )

    def double_click(
        self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """双击元素

        Args:
            selector: 选择器
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.element_service.double_click(
            page=self.page, selector=selector, timeout=timeout
        )

    def hover(self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """悬停在元素上

        Args:
            selector: 选择器
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.element_service.hover(page=self.page, selector=selector, timeout=timeout)

    def get_text(self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT) -> str:
        """获取元素文本

        Args:
            selector: 选择器
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT

        Returns:
            str: 元素的文本内容
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        return self.element_service.get_text(
            page=self.page, selector=selector, timeout=timeout
        )

    def get_attribute(
        self, selector: str, attribute: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> Optional[str]:
        """获取元素属性

        Args:
            selector: 选择器
            attribute: 要获取的属性名
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT

        Returns:
            Optional[str]: 属性的值
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        return self.element_service.get_attribute(
            page=self.page, selector=selector, attribute=attribute, timeout=timeout
        )

    def is_visible(
        self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> bool:
        """检查元素是否可见

        Args:
            selector: 选择器
            timeout: 超时时间（毫秒），默认使用1000ms

        Returns:
            bool: 元素是否可见
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        return self.element_service.is_visible(
            page=self.page, selector=selector, timeout=timeout
        )

    def is_enabled(
        self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> bool:
        """检查元素是否启用

        Args:
            selector: 选择器
            timeout: 超时时间（毫秒），默认使用1000ms

        Returns:
            bool: 元素是否启用
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        return self.element_service.is_enabled(
            page=self.page, selector=selector, timeout=timeout
        )

    # ==================== 等待操作 ====================

    def wait_for_element(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> None:
        """等待元素状态

        Args:
            selector: 选择器
            state: 要等待的状态 ('attached', 'detached', 'visible', 'hidden')
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.wait_service.wait_for_element(
            page=self.page, selector=selector, state=state, timeout=timeout
        )

    def wait_for_text(
        self, selector: str, text: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """等待元素包含指定文本

        Args:
            selector: 选择器
            text: 要等待的文本内容
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        text = self.variable_service.replace_variables(text)
        self.wait_service.wait_for_text(
            page=self.page, selector=selector, text=text, timeout=timeout
        )

    def wait_for_url(
        self, url_pattern: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """等待URL匹配

        Args:
            url_pattern: URL匹配模式
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        url_pattern = self.variable_service.replace_variables(url_pattern)
        self.wait_service.wait_for_url(
            page=self.page, url_pattern=url_pattern, timeout=timeout
        )

    def wait_for_timeout(self, timeout: int) -> None:
        """等待指定时间（毫秒）"""
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.wait_service.wait_for_timeout(page=self.page, timeout=timeout)

    def sleep(self, seconds: float) -> None:
        """休眠"""
        self.wait_service.sleep(seconds=seconds)

    # ==================== 断言操作 ====================

    def assert_element_visible(
        self,
        selector: str,
    ) -> None:
        """断言元素可见

        Args:
            selector: 选择器
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.assertion_service.assert_element_visible(page=self.page, selector=selector)

    def assert_element_hidden(
        self,
        selector: str,
    ) -> None:
        """断言元素隐藏

        Args:
            selector: 选择器
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.assertion_service.assert_element_hidden(page=self.page, selector=selector)

    def assert_text(
        self,
        selector: str,
        expected: str,
    ) -> None:
        """断言元素文本等于指定值

        Args:
            selector: 选择器
            expected: 期望的文本内容
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        expected = self.variable_service.replace_variables(expected)
        self.assertion_service.assert_text(
            page=self.page, selector=selector, expected=expected
        )

    def assert_text_contains(
        self,
        selector: str,
        text: str,
    ) -> None:
        """断言元素包含指定文本

        Args:
            selector: 选择器
            text: 期望包含的文本内容
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        text = self.variable_service.replace_variables(text)
        self.assertion_service.assert_text_contains(
            page=self.page, selector=selector, text=text
        )

    def assert_url_contains(
        self,
        url_part: str,
    ) -> None:
        """断言URL包含指定部分

        Args:
            url_part: URL应包含的部分
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        url_part = self.variable_service.replace_variables(url_part)
        self.assertion_service.assert_url_contains(page=self.page, url_part=url_part)

    def assert_url(
        self,
        expected: str,
    ) -> None:
        """断言URL等于指定值

        Args:
            expected: 期望的URL
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        expected = self.variable_service.replace_variables(expected)
        self.assertion_service.assert_url(page=self.page, url=expected)

    def assert_title_contains(
        self,
        title_part: str,
    ) -> None:
        """断言标题包含指定文本

        Args:
            title_part: 标题应包含的部分
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        title_part = self.variable_service.replace_variables(title_part)
        self.assertion_service.assert_title_contains(
            page=self.page, title_part=title_part
        )

    def assert_title(
        self,
        expected: str,
    ) -> None:
        """断言页面标题等于指定值

        Args:
            expected: 期望的页面标题
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        expected = self.variable_service.replace_variables(expected)
        self.assertion_service.assert_title(page=self.page, title=expected)

    def assert_element_count(
        self,
        selector: str,
        expected: int,
    ) -> None:
        """断言元素数量等于指定值

        Args:
            selector: 选择器
            expected: 期望的元素数量
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.assertion_service.assert_element_count(
            page=self.page, selector=selector, count=expected
        )

    def assert_visible(
        self,
        selector: str,
    ) -> None:
        """断言元素可见（别名方法）

        Args:
            selector: 选择器
        """
        self.assert_element_visible(selector=selector)

    # ==================== 网络监控操作 ====================

    def monitor_action_request(
        self,
        url_pattern: str,
        selector: str,
        action: str = "click",
        assert_params: Optional[Dict[str, Any]] = None,
        timeout: int = DEFAULT_TIMEOUT,
        **kwargs,
    ) -> Dict[str, Any]:
        """监测操作触发的请求并验证参数

        Args:
            url_pattern: URL匹配模式，如 "**/api/user/**"
            selector: 要操作的元素选择器
            action: 要执行的操作，如 "click", "goto" 等
            assert_params: 要验证的参数字典，格式为 {"$.path.to.field": expected_value}
            timeout: 等待超时时间(毫秒)
            **kwargs: 其他操作参数，如 goto 操作的 value

        Returns:
            Dict[str, Any]: 捕获的请求数据
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        logger.info(f"开始监测请求: {url_pattern}, 操作: {action} 元素: {selector}")
        pattern = (
            f"**{url_pattern}**" if not url_pattern.startswith("*") else url_pattern
        )
        try:
            with self.page.expect_request(pattern, timeout=timeout) as request_info:
                # 执行操作
                logger.info(f"准备执行操作: {action} on {selector}")
                # 确保将timeout参数传递给_execute_monitor_action方法
                kwargs["timeout"] = timeout
                self._execute_monitor_action(action, selector, **kwargs)
                logger.info(f"操作执行完成，等待请求")
                logger.info(f"请求信息: {request_info}")
                # 等待请求完成

                request = request_info.value
                logger.info(f"捕获到请求: {request.url}")

                # 获取请求数据
                request_data = self._extract_monitor_request_data(request)

                # 构建完整的请求信息
                captured_data = {
                    "url": request.url,
                    "method": request.method,
                    "data": request_data,
                    "headers": {k: v for k, v in request.headers.items()},
                }

                return captured_data

        except Exception as e:
            logger.error(f"监测请求失败: {e}")
            raise

    def monitor_action_response(
        self,
        url_pattern: str,
        selector: str,
        action: str = "click",
        assert_params: Optional[Dict[str, Any]] = None,
        timeout: int = DEFAULT_TIMEOUT,
        **kwargs,
    ) -> Dict[str, Any]:
        """监测操作触发的响应并验证参数

        Args:
            url_pattern: URL匹配模式，如 "**/api/user/**"
            selector: 要操作的元素选择器
            action: 要执行的操作，如 "click", "goto" 等
            assert_params: 要验证的参数字典，格式为 {"$.path.to.field": expected_value}
            timeout: 等待超时时间(毫秒)
            **kwargs: 其他操作参数，如 goto 操作的 value

        Returns:
            Dict[str, Any]: 捕获的响应数据
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        logger.info(f"开始监测响应: {url_pattern}, 操作: {action} 元素: {selector}")

        try:
            with self.page.expect_response(
                url_pattern, timeout=timeout
            ) as response_info:
                # 执行操作
                # 确保将timeout参数传递给_execute_monitor_action方法
                kwargs["timeout"] = timeout
                self._execute_monitor_action(action, selector, **kwargs)
                # 等待响应完成
                response = response_info.value
                logger.info(f"捕获到响应: {response.url}")

                # 获取响应数据
                response_data = self._extract_monitor_response_data(response)

                # 构建完整的响应信息
                captured_data = {
                    "url": response.url,
                    "status": response.status,
                    "data": response_data,
                    "headers": {k: v for k, v in response.headers.items()},
                }

                # 验证参数（如果需要）
                if assert_params and response_data:
                    logger.info(f"开始验证响应参数: {assert_params}")
                    # 处理断言参数
                    for jsonpath_expr, expected_value in assert_params.items():
                        self._verify_jsonpath(
                            response_data, jsonpath_expr, expected_value
                        )

                return captured_data

        except Exception as e:
            logger.error(f"监测响应失败: {e}")
            raise

    def _execute_monitor_action(self, action: str, selector: str, **kwargs) -> None:
        """执行监控操作

        Args:
            action: 要执行的操作类型
            selector: 元素选择器
            **kwargs: 额外参数，可包含timeout和操作特定参数
        """
        # 获取timeout参数，如果没有则为None
        timeout = kwargs.get("timeout", None)

        if action == "click":
            self.click(selector=selector, timeout=timeout)
        elif action == "fill":
            value = kwargs.get("value", "")
            self.fill(selector=selector, value=value, timeout=timeout)
        elif action == "goto":
            url = kwargs.get("value", kwargs.get("url", ""))
            self.navigate(url=url, timeout=timeout)
        else:
            logger.warning(f"不支持的操作类型: {action}，将执行默认点击操作")
            self.click(selector=selector, timeout=timeout)

    def _extract_monitor_request_data(self, request) -> Dict[str, Any]:
        """提取请求数据"""
        import json
        from urllib.parse import urlparse, parse_qs

        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # 尝试解析JSON数据
                request_data = request.post_data_json()
            except Exception:
                try:
                    # 尝试解析为JSON字符串
                    post_data = request.post_data
                    if post_data:
                        request_data = json.loads(post_data)
                    else:
                        request_data = {}
                except Exception:
                    # 如果都失败，返回原始数据
                    request_data = {"raw_data": request.post_data}
        else:
            # 对于GET请求，获取URL参数
            parsed_url = urlparse(request.url)
            request_data = parse_qs(parsed_url.query)

            # 将单项列表值转换为单个值
            for key, value in request_data.items():
                if isinstance(value, list) and len(value) == 1:
                    request_data[key] = value[0]

        return request_data

    def _extract_monitor_response_data(self, response) -> Dict[str, Any]:
        """提取响应数据"""
        import json

        try:
            # 尝试解析JSON响应
            response_text = response.text()
            if response_text:
                try:
                    response_data = json.loads(response_text)
                except json.JSONDecodeError:
                    # 如果不是JSON格式，返回原始文本
                    response_data = {"raw_text": response_text}
            else:
                response_data = {}
        except Exception as e:
            logger.warning(f"提取响应数据失败: {e}")
            response_data = {"error": str(e)}

        return response_data

    # ==================== 断言操作 ====================

    def assert_attribute(
        self,
        selector: str,
        attribute: str,
        expected: str,
    ) -> None:
        """断言元素属性值

        Args:
            selector: CSS选择器
            attribute: 属性名
            expected: 期望的属性值
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        expected = self.variable_service.replace_variables(expected)
        self.assertion_service.assert_attribute(
            page=self.page, selector=selector, attribute=attribute, expected=expected
        )

    def assert_value(
        self,
        selector: str,
        expected: str,
    ) -> None:
        """断言元素值等于指定值

        Args:
            selector: CSS选择器
            expected: 期望的值
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        expected = self.variable_service.replace_variables(expected)
        self.assertion_service.assert_value(
            page=self.page, selector=selector, expected=expected
        )

    def assert_exists(
        self,
        selector: str,
    ) -> None:
        """断言元素存在

        Args:
            selector: CSS选择器
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.assertion_service.assert_exists(page=self.page, selector=selector)

    def assert_not_exists(
        self,
        selector: str,
    ) -> None:
        """断言元素不存在

        Args:
            selector: CSS选择器
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.assertion_service.assert_not_exists(page=self.page, selector=selector)

    def assert_element_enabled(
        self,
        selector: str,
    ) -> None:
        """断言元素启用

        Args:
            selector: CSS选择器
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.assertion_service.assert_element_enabled(page=self.page, selector=selector)

    def assert_element_disabled(
        self,
        selector: str,
    ) -> None:
        """断言元素禁用

        Args:
            selector: CSS选择器
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        self.assertion_service.assert_element_disabled(
            page=self.page, selector=selector
        )

    def assert_values(
        self,
        selector: str,
        expected: list,
    ) -> None:
        """断言元素多个值

        Args:
            selector: CSS选择器
            expected: 期望的值列表
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        # 如果 expected 是字符串，尝试解析为列表
        if isinstance(expected, str):
            try:
                import json

                expected = json.loads(expected)
            except json.JSONDecodeError:
                # 如果不是 JSON 格式，按逗号分割
                expected = [item.strip() for item in expected.split(",")]
        self.assertion_service.assert_values(
            page=self.page, selector=selector, expected=expected
        )

    # ==================== 变量操作 ====================

    def set_variable(self, name: str, value: Any) -> None:
        """设置变量"""
        self.variable_service.set_variable(name=name, value=value)

    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variable_service.get_variable(name=name, default=default)

    def clear_variables(self) -> None:
        """清空所有变量"""
        self.variable_service.clear_variables()

    # ==================== 高级功能 ====================

    def execute_script(
        self, script: str, *args, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> Any:
        """执行JavaScript脚本

        Args:
            script: JavaScript代码
            *args: 传递给脚本的参数
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT

        Returns:
            Any: 脚本执行结果
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        try:
            script = self.variable_service.replace_variables(script)
            result = self.page.evaluate(
                script,
                *args,
            )
            logger.debug(f"JavaScript执行成功: {script[:50]}...")
            return result
        except Exception as e:
            logger.error(f"JavaScript执行失败: {script[:50]}..., 错误: {e}")
            raise

    def screenshot(
        self,
        path: Optional[str] = None,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
        **kwargs,
    ) -> bytes:
        """截图

        Args:
            path: 保存路径
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
            **kwargs: 其他截图参数

        Returns:
            bytes: 截图数据
        """
        if not self.page:
            raise RuntimeError("页面对象未初始化")

        try:
            if path:
                path = self.variable_service.replace_variables(path)

            if timeout is not None:
                kwargs["timeout"] = timeout
            screenshot_data = self.page.screenshot(path=path, **kwargs)
            logger.debug(f"截图完成: {path or '内存'}")
            return screenshot_data
        except Exception as e:
            logger.error(f"截图失败: {e}")
            raise

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标

        Returns:
            Dict[str, Any]: 性能指标数据
        """
        try:
            # 从各个服务获取性能数据
            metrics = {}

            # 获取元素操作性能
            if (
                hasattr(self.element_service, "performance_manager")
                and self.element_service.performance_manager
            ):
                metrics["element_operations"] = (
                    self.element_service.performance_manager.get_summary()
                )

            # 获取导航操作性能
            if (
                hasattr(self.navigation_service, "performance_manager")
                and self.navigation_service.performance_manager
            ):
                metrics["navigation_operations"] = (
                    self.navigation_service.performance_manager.get_summary()
                )

            # 获取等待操作性能
            if (
                hasattr(self.wait_service, "performance_manager")
                and self.wait_service.performance_manager
            ):
                metrics["wait_operations"] = (
                    self.wait_service.performance_manager.get_summary()
                )

            # 获取断言操作性能
            if (
                hasattr(self.assertion_service, "performance_manager")
                and self.assertion_service.performance_manager
            ):
                metrics["assertion_operations"] = (
                    self.assertion_service.performance_manager.get_summary()
                )

            return metrics
        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return {}

    def close(self, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """关闭页面

        Args:
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
        """
        try:
            if self.page:
                # 如果提供了timeout，使用它，否则使用默认值
                if timeout is not None:
                    self.page.close()
                else:
                    self.page.close()
                logger.debug("页面已关闭")
        except Exception as e:
            logger.error(f"关闭页面失败: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        # 使用默认超时关闭页面
        self.close(timeout=None)
