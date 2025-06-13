"""网络监控混入类"""
import json
import allure
from typing import Dict, Any, Optional
from jsonpath_ng import parse
from urllib.parse import urlparse, parse_qs
from utils.logger import logger
from .decorators import handle_page_error
from config.constants import DEFAULT_TIMEOUT


class NetworkMonitoringMixin:
    """网络监控混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @handle_page_error(description="监测操作触发的请求")
    def monitor_action_request(
        self,
        url_pattern: str,
        selector: str,
        action: str = "click",
        assert_params: Optional[Dict[str, Any]] = None,
        timeout: int = DEFAULT_TIMEOUT,
        **kwargs,
    ):
        """
        监测操作触发的请求并验证参数

        Args:
            url_pattern: URL匹配模式，如 "**/api/user/**"
            selector: 要操作的元素选择器
            action: 要执行的操作，如 "click", "goto" 等
            assert_params: 要验证的参数字典，格式为 {"$.path.to.field": expected_value}
            timeout: 等待超时时间(毫秒)
            **kwargs: 其他操作参数，如 goto 操作的 value

        Returns:
            捕获的请求数据
        """
        logger.info(f"开始监测请求: {url_pattern}, 操作: {action} 元素: {selector}")

        with allure.step(f"监测请求: {url_pattern}"):
            try:
                with self.page.expect_request(url_pattern, timeout=timeout) as request_info:
                    # 执行操作
                    self._execute_action(action, selector, **kwargs)

                    # 等待请求完成
                    request = request_info.value
                    logger.info(f"捕获到请求: {request.url}")

                    # 获取请求数据
                    request_data = self._extract_request_data(request)
                    
                    # 构建完整的请求信息
                    captured_data = {
                        "url": request.url,
                        "method": request.method,
                        "data": request_data,
                        "headers": {k: v for k, v in request.headers.items()},
                    }

                    # 验证参数（如果需要）
                    if assert_params and request_data:
                        self._verify_request_params(request_data, assert_params)

                    # 添加请求信息到报告
                    allure.attach(
                        json.dumps(captured_data, indent=2, ensure_ascii=False),
                        name="捕获的请求数据",
                        attachment_type=allure.attachment_type.JSON
                    )

                    return captured_data

            except Exception as e:
                logger.error(f"监测请求失败: {e}")
                screenshot = self.page.screenshot()
                allure.attach(
                    screenshot,
                    name="请求捕获失败截图",
                    attachment_type=allure.attachment_type.PNG,
                )
                raise

    @handle_page_error(description="监测操作触发的响应")
    def monitor_action_response(
        self,
        url_pattern: str,
        selector: str,
        action: str = "click",
        assert_params: Optional[Dict[str, Any]] = None,
        save_params: Optional[Dict[str, Any]] = None,
        timeout: int = DEFAULT_TIMEOUT,
        **kwargs,
    ):
        """
        监测操作触发的响应并验证参数

        Args:
            url_pattern: URL匹配模式，如 "**/api/user/**"
            selector: 要操作的元素选择器
            action: 要执行的操作，如 "click", "fill" 等
            assert_params: 要验证的参数字典，格式为 {"$.path.to.field": expected_value}
            save_params: 要保存的参数字典，格式为 {"$.path.to.field": variable_name}
            timeout: 等待超时时间(毫秒)
            **kwargs: 其他操作参数，如 fill 操作的 value

        Returns:
            捕获的响应数据
        """
        logger.info(f"开始监测响应: {url_pattern}, 操作: {action} 元素: {selector}")

        with allure.step(f"监测响应: {url_pattern}"):
            try:
                with self.page.expect_response(url_pattern, timeout=timeout) as response_info:
                    # 执行操作
                    self._execute_action(action, selector, **kwargs)

                    # 等待响应完成
                    response = response_info.value
                    logger.info(f"捕获到响应: {response.url}, 状态码: {response.status}")

                    # 获取响应数据
                    try:
                        response_data = response.json()
                        logger.info(f"响应数据: {response_data}")

                        # 验证参数（如果需要）
                        if response_data:
                            if assert_params:
                                self._verify_response_params(response_data, assert_params)

                            if save_params:
                                self._save_response_params(response_data, save_params)

                        # 添加响应信息到报告
                        response_info_dict = {
                            "url": response.url,
                            "status": response.status,
                            "headers": {k: v for k, v in response.headers.items()},
                            "data": response_data
                        }
                        
                        allure.attach(
                            json.dumps(response_info_dict, indent=2, ensure_ascii=False),
                            name="捕获的响应数据",
                            attachment_type=allure.attachment_type.JSON
                        )

                        return response_data

                    except Exception as e:
                        logger.error(f"处理响应数据失败: {e}")
                        # 尝试获取文本响应
                        try:
                            response_text = response.text()
                            logger.info(f"响应文本: {response_text}")
                            return {"text": response_text, "status": response.status}
                        except Exception as text_error:
                            logger.error(f"获取响应文本也失败: {text_error}")
                            raise

            except Exception as e:
                logger.error(f"监测响应失败: {e}")
                screenshot = self.page.screenshot()
                allure.attach(
                    screenshot,
                    name="响应捕获失败截图",
                    attachment_type=allure.attachment_type.PNG,
                )
                raise

    def _execute_action(self, action: str, selector: str, **kwargs):
        """执行指定的操作"""
        if action == "click":
            self.click(selector)
        elif action == "fill":
            value = kwargs.get("value", "")
            self.fill(selector, value)
        elif action == "press_key":
            key = kwargs.get("key", "Enter")
            self.press_key(selector, key)
        elif action == "select":
            value = kwargs.get("value", "")
            self.select_option(selector, value)
        elif action == "goto":
            url = kwargs.get("value", kwargs.get("url", ""))
            self.navigate(url)
        else:
            logger.warning(f"不支持的操作类型: {action}，将执行默认点击操作")
            self.click(selector)

    def _extract_request_data(self, request) -> dict:
        """提取请求数据"""
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
            
            logger.info(f"请求数据 (解析为JSON): {request_data}")
        else:
            # 对于GET请求，获取URL参数
            parsed_url = urlparse(request.url)
            request_data = parse_qs(parsed_url.query)

            # 将单项列表值转换为单个值
            for key, value in request_data.items():
                if isinstance(value, list) and len(value) == 1:
                    request_data[key] = value[0]

            logger.info(f"请求参数: {request_data}")
        
        return request_data

    def _verify_request_params(self, request_data: dict, assert_params: Dict[str, Any]):
        """验证请求参数"""
        for jsonpath_expr, expected_value in assert_params.items():
            self._verify_jsonpath(request_data, jsonpath_expr, expected_value, "请求参数")

    def _verify_response_params(self, response_data: dict, assert_params: Dict[str, Any]):
        """验证响应参数"""
        for jsonpath_expr, expected_value in assert_params.items():
            self._verify_jsonpath(response_data, jsonpath_expr, expected_value, "响应参数")

    def _save_response_params(self, response_data: dict, save_params: Dict[str, Any]):
        """保存响应参数到变量"""
        for jsonpath_expr, variable_name in save_params.items():
            self._save_jsonpath(response_data, jsonpath_expr, variable_name)

    def _save_jsonpath(self, data: dict, jsonpath_expr: str, variable_name: str):
        """
        保存JSONPath表达式的值到变量

        Args:
            data: 要保存的数据
            jsonpath_expr: JSONPath表达式
            variable_name: 变量名称
        """
        jsonpath_expr = jsonpath_expr.strip()
        expr = parse(jsonpath_expr)
        logger.debug(f"JSONPath表达式: {jsonpath_expr}")
        logger.debug(f"变量名称: {variable_name}")

        # 查找匹配的值
        matches = [value.value for value in expr.find(data)]
        if not matches:
            logger.warning(f"JSONPath {jsonpath_expr} 未找到匹配项，数据: {data}")
            return
        
        # 如果只有一个匹配项，保存单个值；否则保存列表
        value_to_save = matches[0] if len(matches) == 1 else matches
        logger.debug(f"匹配的值: {value_to_save}")
        
        self.store_variable(variable_name, value_to_save)
        logger.info(f"已保存变量 {variable_name} = {value_to_save}")

    def _verify_jsonpath(self, data: dict, jsonpath_expr: str, expected: Any, data_type: str = "数据"):
        """
        验证JSONPath表达式的值是否符合预期

        Args:
            data: 要验证的数据
            jsonpath_expr: JSONPath表达式
            expected: 期望值
            data_type: 数据类型描述
        """
        jsonpath_expr = jsonpath_expr.strip()
        expr = parse(jsonpath_expr)

        # 查找匹配的值
        matches = [value.value for value in expr.find(data)]
        
        if not matches:
            error_msg = f"JSONPath {jsonpath_expr} 未找到匹配项，当前{data_type}: {data}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        actual_value = matches[0] if len(matches) == 1 else matches
        
        # 处理变量替换
        resolved_expected = self.variable_manager.replace_variables_refactored(expected)

        # 执行断言
        with allure.step(f"验证{data_type} {jsonpath_expr}"):
            if isinstance(actual_value, list) and isinstance(resolved_expected, list):
                # 列表比较
                assert sorted([str(x) for x in actual_value]) == sorted(
                    [str(x) for x in resolved_expected]
                ), f"断言失败: {data_type} {jsonpath_expr} 期望值为 '{resolved_expected}', 实际值为 '{actual_value}'"
            elif isinstance(actual_value, list):
                # 检查列表中是否包含期望值
                expected_str = str(resolved_expected)
                found = any(str(item) == expected_str for item in actual_value)
                assert found, f"断言失败: {data_type} {jsonpath_expr} 期望包含值 '{resolved_expected}', 实际值为 '{actual_value}'"
            else:
                # 单值比较
                assert str(actual_value) == str(
                    resolved_expected
                ), f"断言失败: {data_type} {jsonpath_expr} 期望值为 '{resolved_expected}', 实际值为 '{actual_value}'"

        allure.attach(
            f"断言成功: {data_type} {jsonpath_expr} 匹配期望值 {resolved_expected}",
            name="断言结果",
            attachment_type=allure.attachment_type.TEXT,
        )

        logger.info(f"{data_type}验证成功: {jsonpath_expr} 匹配期望值 {resolved_expected}")