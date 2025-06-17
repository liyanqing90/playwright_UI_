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

    original_condition = condition

    if condition.startswith("${{") and condition.endswith("}}"):
        expr_content = condition[3:-2].strip()
        readable_expr = step_executor._replace_variables(expr_content)
    else:
        readable_expr = step_executor._replace_variables(condition)

    condition_result = step_executor._evaluate_expression(condition)

    with allure.step(f"条件分支: {description} ({readable_expr} = {condition_result})"):
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

    if isinstance(items, str) and items.startswith("${") and items.endswith("}"):
        var_name = items[2:-1]
        items_value = step_executor.variable_manager.get_variable(var_name)
    else:
        items_value = items

    if not isinstance(items_value, (list, tuple, dict)):
        if isinstance(items_value, str):
            try:
                items_value = json.loads(items_value)
            except json.JSONDecodeError:
                items_value = [items_value]
        else:
            items_value = [items_value]

    if isinstance(items_value, dict):
        items_value = list(items_value.keys())

    with allure.step(f"循环: {description} (迭代 {len(items_value)} 个项)"):
        for i, item in enumerate(items_value):
            logger.info(f"循环项 {i + 1}/{len(items_value)}: {item}")

            step_executor.variable_manager.set_variable(as_var, item, "test_case")

            for do_step in do_steps:
                step_executor.execute_step(do_step)


def evaluate_expression(step_executor, expression: str) -> bool:
    """
    计算表达式的值，支持数学运算和比较操作

    Args:
        step_executor: StepExecutor实例
        expression: 表达式字符串，如 "${{ ${count} > 5 }}" 或 "${{ ${num1} + ${num2} * 2 }}"

    Returns:
        表达式的布尔结果
    """
    if not (expression.startswith("${{") and expression.endswith("}}")):
        return bool(step_executor._replace_variables(expression))

    expr_content = expression[3:-2].strip()

    expr_content = step_executor._replace_variables(expr_content)

    try:
        import math
        import operator

        safe_math_functions = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "len": len,
            "sqrt": math.sqrt,
            "pow": math.pow,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "floor": math.floor,
            "ceil": math.ceil,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
        }

        safe_globals = {
            "__builtins__": {},
            **safe_math_functions,
        }

        processed_expr = preprocess_expression(expr_content)

        result = eval(processed_expr, safe_globals)
        return bool(result)
    except Exception as e:
        logger.error(f"表达式计算错误: {expr_content} - {e}")
        return False


def preprocess_expression(expr: str) -> str:
    """
    预处理表达式，处理字符串和数字

    Args:
        expr: 原始表达式字符串

    Returns:
        处理后的表达式字符串
    """

    try:
        compile(expr, "<string>", "eval")
        return expr
    except SyntaxError:
        pass
    if (
        "==" in expr
        or "!=" in expr
        or ">" in expr
        or "<" in expr
        or ">=" in expr
        or "<=" in expr
    ):
        operators = ["==", "!=", ">=", "<=", ">", "<"]
        for op in operators:
            if op in expr:
                parts = expr.split(op, 1)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()

                    left = process_operand(left)
                    right = process_operand(right)

                    return f"{left} {op} {right}"

    return process_operand(expr)


def process_operand(operand: str) -> str:
    """
    处理操作数，确保字符串和数字格式正确

    Args:
        operand: 操作数字符串

    Returns:
        处理后的操作数字符串
    """
    operand = operand.strip()

    if (operand.startswith('"') and operand.endswith('"')) or (
        operand.startswith("'") and operand.endswith("'")
    ):
        return operand

    try:
        int(operand)
        return operand
    except ValueError:
        try:
            float(operand)
            return operand
        except ValueError:
            if any(c in operand for c in "+-*/()%"):
                return operand
            else:
                return f"'{operand}'"
