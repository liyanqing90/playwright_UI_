"""
处理流程控制相关的操作（条件和循环）
"""
import json
from typing import Dict, Any

import allure

from utils.logger import logger


def execute_condition(step_executor, step: Dict[str, Any]) -> None:
    """
    执行条件分支

    Args:
        step_executor: StepExecutor实例
        step: 包含if字段的步骤
    """
    condition = step["if"]
    then_steps = step.get("then", [])
    else_steps = step.get("else", [])
    description = step.get("description", "条件分支")

    # 计算条件表达式
    # 先获取原始表达式内容用于日志
    original_condition = condition

    # 提取表达式内容（如果是${{...}}格式）
    if condition.startswith("${{") and condition.endswith("}}"):
        expr_content = condition[3:-2].strip()
        # 替换变量得到可读的表达式
        readable_expr = step_executor._replace_variables(expr_content)
    else:
        readable_expr = step_executor._replace_variables(condition)

    # 计算条件结果
    condition_result = step_executor._evaluate_expression(condition)

    with allure.step(
        f"条件分支: {description} ({readable_expr} = {condition_result})"
    ):
        if condition_result:
            logger.info(f"条件 '{readable_expr}' 为真，执行THEN分支")
            for then_step in then_steps:
                step_executor.execute_step(then_step)
        else:
            logger.info(f"条件 '{readable_expr}' 为假，执行ELSE分支")
            for else_step in else_steps:
                step_executor.execute_step(else_step)


def execute_loop(step_executor, step: Dict[str, Any]) -> None:
    """
    执行循环

    Args:
        step_executor: StepExecutor实例
        step: 包含for_each字段的步骤
    """
    items = step["for_each"]
    as_var = step.get("as", "item")
    do_steps = step.get("do", [])
    description = step.get("description", "循环")

    # 处理循环项，可能是变量引用或直接值
    if isinstance(items, str) and items.startswith("${") and items.endswith("}"):
        var_name = items[2:-1]
        items_value = step_executor.variable_manager.get_variable(var_name)
    else:
        items_value = items

    # 确保循环项是可迭代的
    if not isinstance(items_value, (list, tuple, dict)):
        if isinstance(items_value, str):
            try:
                # 尝试解析为JSON
                items_value = json.loads(items_value)
            except json.JSONDecodeError:
                # 如果不是JSON，则转为列表
                items_value = [items_value]
        else:
            items_value = [items_value]

    # 如果是字典，则遍历键
    if isinstance(items_value, dict):
        items_value = list(items_value.keys())

    with allure.step(f"循环: {description} (迭代 {len(items_value)} 个项)"):
        for i, item in enumerate(items_value):
            logger.info(f"循环项 {i + 1}/{len(items_value)}: {item}")

            # 设置循环变量
            step_executor.variable_manager.set_variable(as_var, item, "test_case")

            # 执行循环体
            for do_step in do_steps:
                step_executor.execute_step(do_step)


def evaluate_expression(step_executor, expression: str) -> bool:
    """
    计算表达式的值

    Args:
        step_executor: StepExecutor实例
        expression: 表达式字符串，如 "${{ ${count} > 5 }}"

    Returns:
        表达式的布尔结果
    """
    # 检查是否是表达式格式
    if not (expression.startswith("${{") and expression.endswith("}}")):
        # 不是表达式，直接返回表达式值的布尔性
        return bool(step_executor._replace_variables(expression))

    # 提取表达式内容
    expr_content = expression[3:-2].strip()

    # 替换所有变量引用
    expr_content = step_executor._replace_variables(expr_content)

    # 安全计算表达式
    try:
        # 为了安全起见，我们需要确保字符串值被正确引用
        # 创建一个安全的执行环境
        safe_globals = {"__builtins__": {}}

        # 尝试将表达式中的字符串值用引号括起来
        # 这是一个简单的方法，可能需要更复杂的解析来处理所有情况
        if "==" in expr_content or "!=" in expr_content:
            parts = []
            if "==" in expr_content:
                parts = expr_content.split("==")
                operator = "=="
            else:
                parts = expr_content.split("!=")
                operator = "!="

            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()

                # 如果左右两边不是已经被引号括起来的，且不是纯数字，则添加引号
                if not (left.startswith('"') and left.endswith('"')) and not (
                    left.startswith("'") and left.endswith("'")
                ):
                    try:
                        float(left)  # 尝试转换为数字
                    except ValueError:
                        left = f"'{left}'"  # 不是数字，添加引号

                if not (right.startswith('"') and right.endswith('"')) and not (
                    right.startswith("'") and right.endswith("'")
                ):
                    try:
                        float(right)  # 尝试转换为数字
                    except ValueError:
                        right = f"'{right}'"  # 不是数字，添加引号

                expr_content = f"{left} {operator} {right}"

        # 执行表达式
        result = eval(expr_content, safe_globals)
        return bool(result)
    except Exception as e:
        logger.error(f"表达式计算错误: {expr_content} - {e}")
        return False
