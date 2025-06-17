#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用操作装饰器模块

提供统一的操作记录、性能监控和错误处理装饰器，
可用于所有service的操作方法。
"""

import functools
import time
from typing import Any, Optional, Callable

import allure
from playwright.sync_api import Page

from utils.logger import logger


def operation_decorator(
    operation_type: str = "操作",
    auto_screenshot: bool = False,
    include_performance: bool = True,
):
    """
    通用操作装饰器

    为service方法提供统一的:
    - Allure步骤记录
    - 操作日志记录
    - 性能监控
    - 错误处理和截图
    - 参数信息提取

    Args:
        operation_type: 操作类型（如"元素操作"、"导航操作"、"等待操作"等）
        auto_screenshot: 是否在操作失败时自动截图
        include_performance: 是否包含性能监控

    示例:
        ```python
        @operation_decorator("元素操作", "点击按钮", auto_screenshot=True)
        def click(self, page: Page, selector: str, timeout: int = 5000):
            # 实际操作逻辑
            pass
        ```
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, page: Page, *args, **kwargs) -> Any:
            # 构建操作描述
            operation_description = func.__name__.upper()

            # 提取常见参数信息
            if params_info := _extract_operation_params(func.__name__, args, kwargs):
                operation_description += f" - {params_info}"

            # 记录操作开始
            if hasattr(self, "_log_operation"):
                self._log_operation(func.__name__, params_info)

            start_time = time.time() if include_performance else None

            try:
                with allure.step(f"[{operation_type}] {operation_description}"):
                    # 执行原始操作
                    result = func(self, page, *args, **kwargs)

                    # 记录成功的性能指标
                    if (
                        include_performance
                        and start_time
                        and hasattr(self, "_record_operation")
                    ):
                        duration = time.time() - start_time
                        self._record_operation(func.__name__, duration, True)

                    logger.debug(f"操作成功: {operation_description}")
                    return result

            except Exception as e:
                # 记录失败的性能指标
                if (
                    include_performance
                    and start_time
                    and hasattr(self, "_record_operation")
                ):
                    duration = time.time() - start_time
                    self._record_operation(func.__name__, duration, False)

                # 构建错误信息
                error_msg = f"操作失败: {operation_description} - {str(e)}"
                logger.error(error_msg)

                # 自动截图（如果启用）
                screenshot_data = None
                if auto_screenshot:
                    screenshot_data = _get_operation_screenshot(
                        page, kwargs.get("selector")
                    )

                # 记录错误详情到Allure
                _attach_error_details(error_msg, params_info, str(e), screenshot_data)

                # 重新抛出异常
                raise

        return wrapper

    return decorator


def _extract_operation_params(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    提取操作参数信息

    Args:
        func_name: 函数名
        args: 位置参数
        kwargs: 关键字参数

    Returns:
        格式化的参数信息字符串
    """
    params = []

    # 提取selector参数
    logger.debug(f"参数 args: {args}, kwargs: {kwargs}")
    if selector := kwargs.get("selector"):
        params.append(f"元素: {selector}")

    # 提取url参数
    if url := kwargs.get("url"):
        params.append(f"URL: {url}")

    # 提取value/text参数
    value = kwargs.get("value")
    if value and func_name in ["fill", "type", "wait_for_text"]:
        params.append(f"值: {value}")

    # 提取state参数
    state = kwargs.get("state")
    if state:
        params.append(f"状态: {state}")

    return ", ".join(params)


def _get_operation_screenshot(
    page: Page, selector: Optional[str] = None
) -> Optional[bytes]:
    """
    获取操作截图

    Args:
        page: Playwright页面对象
        selector: 可选的元素选择器，如果提供则高亮该元素

    Returns:
        截图数据（bytes）或None
    """
    try:
        if selector:
            # 尝试高亮目标元素
            page.locator(selector).first.highlight()
        return page.screenshot(full_page=True)
    except Exception as e:
        logger.warning(f"截图失败: {e}")
        return None


def _attach_error_details(
    error_msg: str,
    params_info: str,
    exception_str: str,
    screenshot_data: Optional[bytes] = None,
) -> None:
    """
    将错误详情附加到Allure报告

    Args:
        error_msg: 错误消息
        params_info: 参数信息
        exception_str: 异常字符串
        screenshot_data: 截图数据
    """
    import json

    # 附加错误详情
    error_details = {
        "错误消息": error_msg,
        "参数信息": params_info,
        "异常详情": exception_str,
        "时间戳": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    allure.attach(
        json.dumps(error_details, ensure_ascii=False, indent=2),
        name="操作错误详情",
        attachment_type=allure.attachment_type.JSON,
    )

    # 附加截图
    if screenshot_data:
        allure.attach(
            screenshot_data,
            name="操作失败截图",
            attachment_type=allure.attachment_type.PNG,
        )


# 预定义的常用装饰器
def element_operation(auto_screenshot: bool = True):
    """元素操作装饰器"""
    return operation_decorator(
        operation_type="元素操作",
        auto_screenshot=auto_screenshot,
        include_performance=True,
    )


def navigation_operation(auto_screenshot: bool = False):
    """导航操作装饰器"""
    return operation_decorator(
        operation_type="导航操作",
        auto_screenshot=auto_screenshot,
        include_performance=True,
    )


def wait_operation(auto_screenshot: bool = False):
    """等待操作装饰器"""
    return operation_decorator(
        operation_type="等待操作",
        auto_screenshot=auto_screenshot,
        include_performance=True,
    )


def performance_operation():
    """性能操作装饰器"""
    return operation_decorator(
        operation_type="性能操作", auto_screenshot=False, include_performance=True
    )
