"""表达式评估插件
提供安全的数学表达式计算和自定义函数支持
"""

import math
import operator
import re
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable

from src.automation.commands.base_command import Command, CommandFactory
from src.automation.flow_control import preprocess_expression
from utils.logger import logger


@dataclass
class FunctionInfo:
    """函数信息配置"""

    name: str
    func: Callable
    description: str = ""
    category: str = "custom"
    args_count: Optional[int] = None


class ExpressionEvaluatorPlugin:
    """表达式评估插件主类"""

    def __init__(self):
        self.name = "expression_evaluator"
        self.version = "1.0.0"
        self.description = "表达式评估插件，提供安全的数学表达式计算和自定义函数支持"
        self.author = "Playwright UI Framework"

        # 插件配置
        self.config = {
            "enabled": True,
            "safe_mode": True,  # 安全模式，限制可用函数
            "max_expression_length": 1000,  # 表达式最大长度
            "timeout": 5,  # 计算超时时间（秒）
            "allow_custom_functions": True,  # 是否允许自定义函数
            "precision": 10,  # 浮点数精度
        }

        # 函数注册表
        self.functions: Dict[str, Callable] = {}
        self.function_info: Dict[str, FunctionInfo] = {}

        # 变量存储
        self.variables: Dict[str, Any] = {}

        # 注册内置函数
        self._register_builtin_functions()

        # 注册命令
        self._register_commands()

    def _register_commands(self):
        """注册插件命令"""
        # 注册表达式计算命令
        CommandFactory.register(["evaluate_expression", "计算表达式"])(
            EvaluateExpressionCommand
        )
        CommandFactory.register(["register_function", "注册函数"])(
            RegisterFunctionCommand
        )
        CommandFactory.register(["set_variable", "设置变量"])(SetVariableCommand)
        CommandFactory.register(["get_variable", "获取变量"])(GetVariableCommand)

    def _register_builtin_functions(self):
        """注册内置函数"""
        # 基本数学函数
        self.register_function("abs", abs, "绝对值", "math", 1)
        self.register_function("round", round, "四舍五入", "math", 1)
        self.register_function("min", min, "最小值", "math")
        self.register_function("max", max, "最大值", "math")
        self.register_function("sum", sum, "求和", "math", 1)
        self.register_function("len", len, "长度", "basic", 1)

        # 数学模块函数
        self.register_function("sqrt", math.sqrt, "平方根", "math", 1)
        self.register_function("pow", math.pow, "幂运算", "math", 2)
        self.register_function("sin", math.sin, "正弦", "trigonometry", 1)
        self.register_function("cos", math.cos, "余弦", "trigonometry", 1)
        self.register_function("tan", math.tan, "正切", "trigonometry", 1)
        self.register_function("asin", math.asin, "反正弦", "trigonometry", 1)
        self.register_function("acos", math.acos, "反余弦", "trigonometry", 1)
        self.register_function("atan", math.atan, "反正切", "trigonometry", 1)
        self.register_function("floor", math.floor, "向下取整", "math", 1)
        self.register_function("ceil", math.ceil, "向上取整", "math", 1)
        self.register_function("log", math.log, "自然对数", "math", 1)
        self.register_function("log10", math.log10, "常用对数", "math", 1)
        self.register_function("exp", math.exp, "指数函数", "math", 1)

        # 常量
        self.set_variable("pi", math.pi, "圆周率")
        self.set_variable("e", math.e, "自然常数")

        # 类型转换函数
        self.register_function("int", int, "转换为整数", "conversion", 1)
        self.register_function("float", float, "转换为浮点数", "conversion", 1)
        self.register_function("str", str, "转换为字符串", "conversion", 1)
        self.register_function("bool", bool, "转换为布尔值", "conversion", 1)

        # 字符串函数
        self.register_function("upper", lambda s: s.upper(), "转大写", "string", 1)
        self.register_function("lower", lambda s: s.lower(), "转小写", "string", 1)
        self.register_function("strip", lambda s: s.strip(), "去除空白", "string", 1)
        self.register_function(
            "replace",
            lambda s, old, new: s.replace(old, new),
            "替换字符串",
            "string",
            3,
        )

        # 逻辑函数
        self.register_function("and_", lambda a, b: a and b, "逻辑与", "logic", 2)
        self.register_function("or_", lambda a, b: a or b, "逻辑或", "logic", 2)
        self.register_function("not_", lambda a: not a, "逻辑非", "logic", 1)

        # 比较函数
        self.register_function("eq", operator.eq, "等于", "comparison", 2)
        self.register_function("ne", operator.ne, "不等于", "comparison", 2)
        self.register_function("lt", operator.lt, "小于", "comparison", 2)
        self.register_function("le", operator.le, "小于等于", "comparison", 2)
        self.register_function("gt", operator.gt, "大于", "comparison", 2)
        self.register_function("ge", operator.ge, "大于等于", "comparison", 2)

        # 条件函数
        self.register_function(
            "if_",
            lambda condition, true_val, false_val: true_val if condition else false_val,
            "条件判断",
            "conditional",
            3,
        )

    def register_function(
        self,
        name: str,
        func: Callable,
        description: str = "",
        category: str = "custom",
        args_count: Optional[int] = None,
    ):
        """注册函数"""
        self.functions[name] = func
        self.function_info[name] = FunctionInfo(
            name=name,
            func=func,
            description=description,
            category=category,
            args_count=args_count,
        )
        logger.debug(f"已注册函数: {name}")

    def unregister_function(self, name: str):
        """注销函数"""
        if name in self.functions:
            del self.functions[name]
            del self.function_info[name]
            logger.debug(f"已注销函数: {name}")

    def set_variable(self, name: str, value: Any, description: str = ""):
        """设置变量"""
        self.variables[name] = value
        logger.debug(f"设置变量: {name} = {value}")

    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(name, default)

    def clear_variables(self):
        """清空变量"""
        # 保留常量
        constants = {"pi": math.pi, "e": math.e}
        self.variables.clear()
        self.variables.update(constants)
        logger.debug("已清空变量")

    def evaluate(
        self,
        expression: str,
        context: Optional[Dict[str, Any]] = None,
        variable_manager=None,
    ) -> Any:
        """评估表达式"""
        try:
            # 检查表达式长度
            if len(expression) > self.config["max_expression_length"]:
                raise ValueError(
                    f"表达式长度超过限制: {len(expression)} > {self.config['max_expression_length']}"
                )

            # 如果表达式不是${{...}}格式，则包装为该格式
            if not (expression.startswith("${{") and expression.endswith("}}")):
                expression = f"${{{{{expression}}}}}"

            # 提取表达式内容
            expr_content = expression[3:-2].strip()

            # 使用变量管理器替换变量（如果提供）
            if variable_manager:
                expr_content = variable_manager.replace_variables_refactored(
                    expr_content
                )

            # 预处理表达式
            processed_expr = preprocess_expression(expr_content)

            # 构建安全的执行环境
            safe_globals = self._build_safe_globals(context)

            # 执行表达式
            result = eval(processed_expr, safe_globals)

            # 处理精度
            if isinstance(result, float):
                result = round(result, self.config["precision"])

            logger.debug(f"计算表达式: {expr_content} = {result}")
            return result

        except Exception as e:
            logger.error(f"计算表达式错误: {expression} - {e}")
            raise

    def _build_safe_globals(
        self, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """构建安全的全局环境"""
        safe_globals = {
            "__builtins__": {},  # 清空内置函数
        }

        # 添加注册的函数
        safe_globals.update(self.functions)

        # 添加变量
        safe_globals.update(self.variables)

        # 添加上下文变量
        if context:
            safe_globals.update(context)

        return safe_globals

    def get_available_functions(self, category: Optional[str] = None) -> Dict[str, str]:
        """获取可用函数列表"""
        if category:
            return {
                name: info.description
                for name, info in self.function_info.items()
                if info.category == category
            }
        return {name: info.description for name, info in self.function_info.items()}

    def get_function_categories(self) -> Dict[str, list]:
        """获取函数分类"""
        categories = {}
        for name, info in self.function_info.items():
            if info.category not in categories:
                categories[info.category] = []
            categories[info.category].append(name)
        return categories

    def validate_expression(self, expression: str) -> Dict[str, Any]:
        """验证表达式语法"""
        try:
            # 基本语法检查
            if not expression.strip():
                return {"valid": False, "error": "表达式不能为空"}

            # 检查括号匹配
            if not self._check_parentheses(expression):
                return {"valid": False, "error": "括号不匹配"}

            # 检查危险函数
            dangerous_patterns = [
                r"\b(exec|eval|compile|open|file|input|raw_input)\b",
                r"\b(__import__|getattr|setattr|delattr|hasattr)\b",
                r"\b(globals|locals|vars|dir)\b",
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, expression, re.IGNORECASE):
                    return {"valid": False, "error": f"包含危险函数: {pattern}"}

            # 尝试编译表达式
            try:
                compile(expression, "<string>", "eval")
            except SyntaxError as e:
                return {"valid": False, "error": f"语法错误: {e}"}

            return {"valid": True, "error": None}

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def _check_parentheses(self, expression: str) -> bool:
        """检查括号是否匹配"""
        stack = []
        pairs = {"(": ")", "[": "]", "{": "}"}

        for char in expression:
            if char in pairs:
                stack.append(char)
            elif char in pairs.values():
                if not stack:
                    return False
                if pairs[stack.pop()] != char:
                    return False

        return len(stack) == 0


# 插件命令实现
class EvaluateExpressionCommand(Command):
    """计算表达式命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> Any:
        """执行计算表达式命令"""
        try:
            # 获取插件实例
            plugin = getattr(ui_helper, "_expression_evaluator_plugin", None)
            if not plugin:
                plugin = ExpressionEvaluatorPlugin()
                setattr(ui_helper, "_expression_evaluator_plugin", plugin)

            # 解析参数
            if isinstance(value, dict):
                expression = value.get("expression", "")
                context = value.get("context", {})
            else:
                expression = str(value)
                context = {}

            # 获取变量管理器
            variable_manager = getattr(ui_helper, "variable_manager", None)

            # 计算表达式
            result = plugin.evaluate(expression, context, variable_manager)

            # 如果指定了变量名，保存到变量管理器
            var_name = step.get("variable")
            if var_name and variable_manager:
                variable_manager.set_variable(var_name, result)

            return result

        except Exception as e:
            logger.error(f"计算表达式失败: {e}")
            raise


class RegisterFunctionCommand(Command):
    """注册函数命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> Any:
        """执行注册函数命令"""
        try:
            # 获取插件实例
            plugin = getattr(ui_helper, "_expression_evaluator_plugin", None)
            if not plugin:
                plugin = ExpressionEvaluatorPlugin()
                setattr(ui_helper, "_expression_evaluator_plugin", plugin)

            # 解析参数
            if not isinstance(value, dict):
                raise ValueError("注册函数需要字典格式的参数")

            name = value.get("name")
            func_code = value.get("function")
            description = value.get("description", "")
            category = value.get("category", "custom")
            args_count = value.get("args_count")

            if not name or not func_code:
                raise ValueError("函数名称和函数代码不能为空")

            # 创建函数
            def custom_function(*args, **kwargs):
                # 为了安全，限制可用的函数和模块
                safe_globals = {
                    "math": math,
                    "operator": operator,
                    "len": len,
                    "abs": abs,
                    "min": min,
                    "max": max,
                    "sum": sum,
                    "round": round,
                    "int": int,
                    "float": float,
                    "str": str,
                    "bool": bool,
                }
                safe_locals = {"args": args, "kwargs": kwargs}
                return eval(func_code, safe_globals, safe_locals)

            # 注册函数
            plugin.register_function(
                name, custom_function, description, category, args_count
            )

            return f"函数 '{name}' 注册成功"

        except Exception as e:
            logger.error(f"注册函数失败: {e}")
            raise


class SetVariableCommand(Command):
    """设置变量命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> Any:
        """执行设置变量命令"""
        try:
            # 获取插件实例
            plugin = getattr(ui_helper, "_expression_evaluator_plugin", None)
            if not plugin:
                plugin = ExpressionEvaluatorPlugin()
                setattr(ui_helper, "_expression_evaluator_plugin", plugin)

            # 解析参数
            if isinstance(value, dict):
                var_name = value.get("name")
                var_value = value.get("value")
                description = value.get("description", "")
            else:
                raise ValueError("设置变量需要字典格式的参数")

            if not var_name:
                raise ValueError("变量名称不能为空")

            # 设置变量
            plugin.set_variable(var_name, var_value, description)

            return f"变量 '{var_name}' 设置成功"

        except Exception as e:
            logger.error(f"设置变量失败: {e}")
            raise


class GetVariableCommand(Command):
    """获取变量命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> Any:
        """执行获取变量命令"""
        try:
            # 获取插件实例
            plugin = getattr(ui_helper, "_expression_evaluator_plugin", None)
            if not plugin:
                plugin = ExpressionEvaluatorPlugin()
                setattr(ui_helper, "_expression_evaluator_plugin", plugin)

            # 解析参数
            if isinstance(value, dict):
                var_name = value.get("name")
                default_value = value.get("default")
            else:
                var_name = str(value)
                default_value = None

            if not var_name:
                raise ValueError("变量名称不能为空")

            # 获取变量
            result = plugin.get_variable(var_name, default_value)

            # 如果指定了变量名，保存到变量管理器
            target_var = step.get("variable")
            if target_var and hasattr(ui_helper, "variable_manager"):
                ui_helper.variable_manager.set_variable(target_var, result)

            return result

        except Exception as e:
            logger.error(f"获取变量失败: {e}")
            raise


# 插件初始化和清理函数
def plugin_init():
    """插件初始化函数"""
    logger.info("表达式评估插件已初始化")


def plugin_cleanup():
    """插件清理函数"""
    logger.info("表达式评估插件已清理")


# 创建插件实例
expression_evaluator_plugin = ExpressionEvaluatorPlugin()
