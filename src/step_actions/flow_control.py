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
    计算表达式的值，支持数学运算和比较操作

    Args:
        step_executor: StepExecutor实例
        expression: 表达式字符串，如 "${{ ${count} > 5 }}" 或 "${{ ${num1} + ${num2} * 2 }}"

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
        # 创建一个安全的执行环境，添加必要的数学函数和操作
        import math
        import operator
        
        # 定义安全的数学函数集合
        safe_math_functions = {
            # 基本数学函数
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'len': len,
            
            # 数学模块函数
            'sqrt': math.sqrt,
            'pow': math.pow,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'floor': math.floor,
            'ceil': math.ceil,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            
            # 常量
            'pi': math.pi,
            'e': math.e,
            
            # 类型转换
            'int': int,
            'float': float,
            'str': str,
            'bool': bool
        }
        
        # 设置安全的执行环境
        safe_globals = {
            '__builtins__': {},  # 清空内置函数
            **safe_math_functions  # 添加安全的数学函数
        }

        # 预处理表达式，处理字符串和数字
        processed_expr = preprocess_expression(expr_content)
        
        # 执行表达式
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
    import re
    
    # 已经是合法Python表达式的情况直接返回
    try:
        # 尝试编译表达式，如果成功则直接返回
        compile(expr, '<string>', 'eval')
        return expr
    except SyntaxError:
        pass  # 继续处理
    
    # 处理常见的比较操作符
    if "==" in expr or "!=" in expr or ">" in expr or "<" in expr or ">=" in expr or "<=" in expr:
        # 使用正则表达式匹配操作符
        operators = ["==", "!=", ">=", "<=", ">", "<"]
        for op in operators:
            if op in expr:
                # 分割表达式
                parts = expr.split(op, 1)  # 只分割一次，处理第一个操作符
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    # 处理左侧
                    left = process_operand(left)
                    
                    # 处理右侧
                    right = process_operand(right)
                    
                    # 重新组合表达式
                    return f"{left} {op} {right}"
    
    # 处理数学运算表达式
    # 这里我们假设如果没有比较操作符，那么整个表达式就是一个数学运算
    return process_operand(expr)


def process_operand(operand: str) -> str:
    """
    处理操作数，确保字符串和数字格式正确
    
    Args:
        operand: 操作数字符串
        
    Returns:
        处理后的操作数字符串
    """
    # 去除首尾空格
    operand = operand.strip()
    
    # 如果已经是引号括起来的字符串，直接返回
    if (operand.startswith('"') and operand.endswith('"')) or \
       (operand.startswith("'") and operand.endswith("'")):
        return operand
    
    # 尝试解析为数字
    try:
        # 尝试解析为整数
        int(operand)
        return operand  # 是整数，直接返回
    except ValueError:
        try:
            # 尝试解析为浮点数
            float(operand)
            return operand  # 是浮点数，直接返回
        except ValueError:
            # 不是数字，也不是已引用的字符串，添加引号
            # 检查是否包含数学表达式的特殊字符
            if any(c in operand for c in '+-*/()%'):
                # 可能是复杂表达式，不添加引号
                return operand
            else:
                # 普通字符串，添加引号
                return f"'{operand}'"
