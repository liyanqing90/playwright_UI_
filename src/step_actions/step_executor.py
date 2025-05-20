"""
步骤执行器的核心实现
"""

from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Dict, Any, List

import allure

from src.step_actions.action_types import StepAction

# 导入命令模式执行器
from src.step_actions.command_executor import execute_action_with_command
from src.step_actions.flow_control import (
    execute_condition,
    execute_loop,
    evaluate_expression,
)
from src.step_actions.module_handler import execute_module
from utils.logger import logger
from utils.variable_manager import VariableManager


# 导入所有命令类


class StepExecutor:

    def __init__(self, page, ui_helper, elements: Dict[str, Any]):
        self.has_error = None
        self.page = page
        self.ui_helper = ui_helper
        self.elements = elements or {}
        self.start_time = None
        self.step_has_error = False  # 步骤错误状态
        self._log_buffer = StringIO()  # 步骤日志缓存
        self._buffer_handler_id = None
        self._prepare_evidence_dir()
        self._VALID_ACTIONS = {
            a.lower()
            for attr in dir(StepAction)
            if isinstance((alist := getattr(StepAction, attr)), list)
            for a in alist
        }

        self._NO_SELECTOR_ACTIONS = {a.lower() for a in StepAction.NO_SELECTOR_ACTIONS}

        # 初始化变量管理器
        self.variable_manager = VariableManager()

        # 初始化项目名称
        self.project_name = None

        # 已加载的模块缓存
        self.modules_cache = {}

    @staticmethod
    def _prepare_evidence_dir():
        """创建截图存储目录"""
        Path("./evidence/screenshots").mkdir(parents=True, exist_ok=True)

    def setup(self, elements: Dict[str, Any] = None):
        """设置元素定义，在测试开始前调用"""
        if elements:
            self.elements = elements

    def execute_steps(
        self, steps: List[Dict[str, Any]], project_name: str = None
    ) -> None:
        """
        执行多个测试步骤

        Args:
            steps: 测试步骤列表
            project_name: 项目名称，用于加载模块
        """
        self.project_name = project_name
        for step in steps:
            self.execute_step(step)

    def execute_step(self, step: Dict[str, Any]) -> None:
        try:
            self.start_time = datetime.now()
            self.step_has_error = False

            # 检查是否为流程控制步骤
            if "use_module" in step:
                execute_module(self, step)
                return
            elif "if" in step:
                execute_condition(self, step)
                return
            elif "for_each" in step:
                execute_loop(self, step)
                return

            action = step.get("action", "").lower()
            pre_selector = step.get("selector")
            selector = self.variable_manager.replace_variables_refactored(
                self.elements.get(pre_selector, pre_selector)
            )  # 替换变量
            value = self.variable_manager.replace_variables_refactored(
                step.get("value")
            )  # 替换变量
            logger.debug(f"执行步骤: {action} | 选择器: {selector} | 值: {value}")
            self._validate_step(action, selector)
            self._execute_action(action, selector, value, step)
        except AssertionError as e:
            self.has_error = True
            self.step_has_error = True
            # 检查是否为硬断言异常
            if hasattr(e, "_hard_assert") and getattr(e, "_hard_assert", False):
                logger.error(f"硬断言失败，终止测试执行: {e}")
                raise  # 硬断言失败时重新抛出异常，终止测试执行
            # 软断言失败时不抛出异常，继续执行
        except Exception as e:
            logger.error(f"步骤执行失败: {e}")
            self.has_error = True
            self.step_has_error = True
            raise e
        finally:
            self._finalize_step()

    def _validate_step(self, action, selector) -> None:
        if not action:
            raise ValueError("步骤缺少必要参数: action", f"原始输入: {action}")
        # 操作类型白名单校验
        if action not in self._VALID_ACTIONS:
            raise ValueError(f"不支持的操作类型: {action}")
        # 必要参数校验
        if action not in self._NO_SELECTOR_ACTIONS and not selector:
            raise ValueError(f"操作 {action} 需要提供selector参数")

    def _execute_action(
        self, action: str, selector: str, value: Any = None, step: Dict[str, Any] = None
    ) -> None:
        """执行具体操作，使用命令模式"""
        try:
            execute_action_with_command(self.ui_helper, action, selector, value, step)
        except AssertionError as e:
            # 标记异常为断言失败
            self.step_has_error = True
            raise e
        except Exception as e:
            # 统一处理所有异常，不区分超时与非超时
            # 标记步骤失败
            self.step_has_error = True
            self.has_error = True

            # 只添加必要的错误信息，不进行额外处理
            if not hasattr(e, "_logged"):
                logger.error(f"步骤执行失败: {e}")
                setattr(e, "_logged", True)

            # 添加关键信息
            setattr(e, "_action", action)
            setattr(e, "_selector", selector)
            setattr(e, "_value", value)

            # 直接抛出异常，不做其他任何处理
            raise

    def _replace_variables(self, value: Any) -> Any:
        """
        替换值中的变量引用

        Args:
            value: 原始值，可能包含变量引用 ${var_name} 或 $<var_name> 或 $[[expression]]

        Returns:
            替换后的值
        """
        if value is None:
            return value

        if isinstance(value, (int, float, bool)):
            return value

        if isinstance(value, str):
            # 处理数学表达式引用，如 $[[1 + 2 * ${var}]]
            if (
                value.startswith("$[[")
                and value.endswith("]]")
                and value.count("$[[") == 1
            ):
                try:
                    from src.step_actions.expression_evaluator import (
                        evaluate_math_expression,
                    )

                    # 提取表达式内容
                    expr = value[3:-2].strip()
                    # 计算表达式
                    result = evaluate_math_expression(expr, self.variable_manager)
                    return result
                except Exception as e:
                    logger.error(f"计算表达式错误: {value} - {e}")
                    return value  # 出错时返回原始值

            # 处理完整的变量引用，如 ${var_name} 或 $<var_name>
            if (
                value.startswith("${")
                and value.endswith("}")
                and value.count("${") == 1
            ) or (
                value.startswith("$<")
                and value.endswith(">")
                and value.count("$<") == 1
            ):

                if value.startswith("${"):
                    var_name = value[2:-1]
                else:  # value.startswith("$<")
                    var_name = value[2:-1]

                return self.variable_manager.get_variable(var_name)

            # 替换内嵌变量引用
            import re

            # 同时匹配 ${var_name} 和 $<var_name> 两种模式
            pattern = r"\${([^{}]+)}|\$<([^<>]+)>"

            def replace_var(match):
                # 获取匹配的组，第一个组是 ${} 形式，第二个组是 $<> 形式
                var_name = (
                    match.group(1) if match.group(1) is not None else match.group(2)
                )
                var_value = self.variable_manager.get_variable(var_name)
                return str(var_value) if var_value is not None else match.group(0)

            # 使用正则表达式替换所有变量引用
            result = re.sub(pattern, replace_var, value)

            # 处理内嵌的数学表达式引用，如 "Total: $[[1 + 2 * ${var}]]"
            pattern_expr = r"\$\[\[([^\[\]]+)\]\]"

            def replace_expr(match):
                try:
                    from src.step_actions.expression_evaluator import (
                        evaluate_math_expression,
                    )

                    # 提取表达式内容
                    expr = match.group(1).strip()
                    # 计算表达式
                    result = evaluate_math_expression(expr, self.variable_manager)
                    return str(result)
                except Exception as e:
                    logger.error(f"计算表达式错误: {match.group(0)} - {e}")
                    return match.group(0)  # 出错时返回原始表达式

            # 替换所有内嵌的数学表达式
            result = re.sub(pattern_expr, replace_expr, result)

            return result

        if isinstance(value, list):
            return [self._replace_variables(item) for item in value]

        if isinstance(value, dict):
            return {k: self._replace_variables(v) for k, v in value.items()}

        return value

    def _evaluate_expression(self, expression: str) -> bool:
        """
        计算表达式的值

        Args:
            expression: 表达式字符串，如 "${{ ${count} > 5 }}"

        Returns:
            表达式的布尔结果
        """
        return evaluate_expression(self, expression)

    def _finalize_step(self):
        """统一后处理逻辑"""
        # 移除日志handler
        if self._buffer_handler_id:
            logger.remove(self._buffer_handler_id)
            self._buffer_handler_id = None

        # 记录耗时
        self._log_step_duration()

        # 失败时采集证据
        if self.step_has_error:
            self._capture_failure_evidence()

    def _log_step_duration(self):
        """统一记录步骤耗时"""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            if self.step_has_error:
                logger.error(f"[失败] 步骤耗时: {duration:.2f}s")
            else:
                logger.info(f"[成功] 步骤耗时: {duration:.2f}s")

    def _capture_failure_evidence(self):
        """统一失败证据采集"""
        try:
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            context_info = f"URL: {self.page.url}\n错误时间: {timestamp}"
            allure.attach(
                context_info,
                name="失败上下文",
                attachment_type=allure.attachment_type.TEXT,
            )

        except Exception as e:
            logger.error(f"证据采集失败: {str(e)}")
