"""数据生成插件
提供各种类型的测试数据生成功能
"""

import datetime
import random
import string
import uuid
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable

from faker import Faker

from src.automation.commands.base_command import Command, CommandFactory
from utils.logger import logger


@dataclass
class DataTemplate:
    """数据模板配置"""

    name: str
    generator: Callable
    description: str = ""
    category: str = "custom"


class DataGeneratorPlugin:
    """数据生成插件主类"""

    def __init__(self):
        self.name = "data_generator"
        self.version = "1.0.0"
        self.description = "数据生成插件，提供各种类型的测试数据生成功能"
        self.author = "Playwright UI Framework"

        # 初始化Faker
        self.faker = Faker(["zh_CN", "en_US"])

        # 插件配置
        self.config = {
            "enabled": True,
            "locale": "zh_CN",
            "seed": None,  # 随机种子，用于可重复的数据生成
            "custom_providers": [],
            "default_length": 10,
        }

        # 数据生成器注册表
        self.generators: Dict[str, Callable] = {}
        self.templates: Dict[str, DataTemplate] = {}

        # 注册内置生成器
        self._register_builtin_generators()

        # 注册命令
        self._register_commands()

    def _register_commands(self):
        """注册插件命令"""
        # 注册生成数据命令
        CommandFactory.register(["generate_data", "生成数据"])(GenerateDataCommand)
        CommandFactory.register(["generate_batch_data", "批量生成数据"])(
            GenerateBatchDataCommand
        )
        CommandFactory.register(["register_data_template", "注册数据模板"])(
            RegisterDataTemplateCommand
        )

    def _register_builtin_generators(self):
        """注册内置数据生成器"""
        # 基础类型
        self.register_generator("name", self._generate_name, "姓名", "basic")
        self.register_generator("email", self._generate_email, "邮箱", "basic")
        self.register_generator("phone", self._generate_phone, "手机号", "basic")
        self.register_generator(
            "mobile", self._generate_mobile, "手机号（别名）", "basic"
        )
        self.register_generator("address", self._generate_address, "地址", "basic")
        self.register_generator(
            "datetime", self._generate_datetime, "日期时间", "basic"
        )
        self.register_generator("date", self._generate_date, "日期", "basic")
        self.register_generator("time", self._generate_time, "时间", "basic")

        # 业务类型
        self.register_generator("user_id", self._generate_user_id, "用户ID", "business")
        self.register_generator(
            "order_id", self._generate_order_id, "订单ID", "business"
        )
        self.register_generator(
            "product_code", self._generate_product_code, "产品编码", "business"
        )
        self.register_generator(
            "company_name", self._generate_company_name, "公司名称", "business"
        )
        self.register_generator(
            "bank_card", self._generate_bank_card, "银行卡号", "business"
        )
        self.register_generator(
            "id_card", self._generate_id_card, "身份证号", "business"
        )

        # 数字类型
        self.register_generator("integer", self._generate_integer, "整数", "number")
        self.register_generator("float", self._generate_float, "浮点数", "number")
        self.register_generator("price", self._generate_price, "价格", "number")

        # 文本类型
        self.register_generator("text", self._generate_text, "文本", "text")
        self.register_generator("paragraph", self._generate_paragraph, "段落", "text")
        self.register_generator("sentence", self._generate_sentence, "句子", "text")
        self.register_generator("word", self._generate_word, "单词", "text")

        # 网络类型
        self.register_generator("url", self._generate_url, "URL", "network")
        self.register_generator("domain", self._generate_domain, "域名", "network")
        self.register_generator("ip", self._generate_ip, "IP地址", "network")

        # UUID类型
        self.register_generator("uuid", self._generate_uuid, "UUID", "uuid")
        self.register_generator("uuid4", self._generate_uuid4, "UUID4", "uuid")

    def register_generator(
        self,
        data_type: str,
        generator: Callable,
        description: str = "",
        category: str = "custom",
    ):
        """注册数据生成器"""
        self.generators[data_type] = generator
        self.templates[data_type] = DataTemplate(
            name=data_type,
            generator=generator,
            description=description,
            category=category,
        )
        logger.debug(f"已注册数据生成器: {data_type}")

    def generate(self, data_type: str, **kwargs) -> Any:
        """生成指定类型的数据"""
        if data_type not in self.generators:
            raise ValueError(f"不支持的数据类型: {data_type}")

        try:
            generator = self.generators[data_type]
            result = generator(**kwargs)
            logger.debug(f"生成数据: {data_type} = {result}")
            return result
        except Exception as e:
            logger.error(f"生成数据失败: {data_type} - {e}")
            raise

    def generate_batch(self, data_type: str, count: int, **kwargs) -> list:
        """批量生成数据"""
        return [self.generate(data_type, **kwargs) for _ in range(count)]

    def get_available_types(self, category: Optional[str] = None) -> Dict[str, str]:
        """获取可用的数据类型"""
        if category:
            return {
                name: template.description
                for name, template in self.templates.items()
                if template.category == category
            }
        return {name: template.description for name, template in self.templates.items()}

    # 内置生成器实现
    def _generate_name(self, **kwargs) -> str:
        """生成姓名"""
        prefix = kwargs.get("prefix", "新零售")
        if kwargs.get("english", False):
            return self.faker.name()
        return prefix + self.faker.uuid4().replace("-", "")[:6]

    def _generate_email(self, **kwargs) -> str:
        """生成邮箱"""
        domain = kwargs.get("domain", None)
        if domain:
            username = self.faker.user_name()
            return f"{username}@{domain}"
        return self.faker.email()

    def _generate_phone(self, **kwargs) -> str:
        """生成手机号"""
        return kwargs.get("default", "18210233933")

    def _generate_mobile(self, **kwargs) -> str:
        """生成手机号（别名）"""
        return self._generate_phone(**kwargs)

    def _generate_address(self, **kwargs) -> str:
        """生成地址"""
        return self.faker.address()

    def _generate_datetime(self, **kwargs) -> str:
        """生成日期时间"""
        format_str = kwargs.get("format", "%Y-%m-%d")
        if kwargs.get("today", True):
            return datetime.date.today().strftime(format_str)
        return self.faker.date_time().strftime(format_str)

    def _generate_date(self, **kwargs) -> str:
        """生成日期"""
        kwargs.setdefault("format", "%Y-%m-%d")
        return self._generate_datetime(**kwargs)

    def _generate_time(self, **kwargs) -> str:
        """生成时间"""
        kwargs.setdefault("format", "%H:%M:%S")
        return self._generate_datetime(**kwargs)

    def _generate_user_id(self, **kwargs) -> str:
        """生成用户ID"""
        prefix = kwargs.get("prefix", "USER")
        length = kwargs.get("length", 8)
        return f"{prefix}{random.randint(10**(length-1), 10**length-1)}"

    def _generate_order_id(self, **kwargs) -> str:
        """生成订单ID"""
        prefix = kwargs.get("prefix", "ORD")
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        suffix = random.randint(1000, 9999)
        return f"{prefix}{timestamp}{suffix}"

    def _generate_product_code(self, **kwargs) -> str:
        """生成产品编码"""
        prefix = kwargs.get("prefix", "PRD")
        length = kwargs.get("length", 6)
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
        return f"{prefix}{code}"

    def _generate_company_name(self, **kwargs) -> str:
        """生成公司名称"""
        return self.faker.company()

    def _generate_bank_card(self, **kwargs) -> str:
        """生成银行卡号"""
        return self.faker.credit_card_number()

    def _generate_id_card(self, **kwargs) -> str:
        """生成身份证号"""
        return self.faker.ssn()

    def _generate_integer(self, **kwargs) -> int:
        """生成整数"""
        min_val = kwargs.get("min", 1)
        max_val = kwargs.get("max", 1000)
        return random.randint(min_val, max_val)

    def _generate_float(self, **kwargs) -> float:
        """生成浮点数"""
        min_val = kwargs.get("min", 0.0)
        max_val = kwargs.get("max", 1000.0)
        decimals = kwargs.get("decimals", 2)
        return round(random.uniform(min_val, max_val), decimals)

    def _generate_price(self, **kwargs) -> str:
        """生成价格"""
        min_val = kwargs.get("min", 1.0)
        max_val = kwargs.get("max", 10000.0)
        price = round(random.uniform(min_val, max_val), 2)
        return f"{price:.2f}"

    def _generate_text(self, **kwargs) -> str:
        """生成文本"""
        length = kwargs.get("length", self.config["default_length"])
        return self.faker.text(max_nb_chars=length)

    def _generate_paragraph(self, **kwargs) -> str:
        """生成段落"""
        nb_sentences = kwargs.get("sentences", 5)
        return self.faker.paragraph(nb_sentences=nb_sentences)

    def _generate_sentence(self, **kwargs) -> str:
        """生成句子"""
        nb_words = kwargs.get("words", 10)
        return self.faker.sentence(nb_words=nb_words)

    def _generate_word(self, **kwargs) -> str:
        """生成单词"""
        return self.faker.word()

    def _generate_url(self, **kwargs) -> str:
        """生成URL"""
        return self.faker.url()

    def _generate_domain(self, **kwargs) -> str:
        """生成域名"""
        return self.faker.domain_name()

    def _generate_ip(self, **kwargs) -> str:
        """生成IP地址"""
        return self.faker.ipv4()

    def _generate_uuid(self, **kwargs) -> str:
        """生成UUID"""
        return str(uuid.uuid4())

    def _generate_uuid4(self, **kwargs) -> str:
        """生成UUID4"""
        return self._generate_uuid(**kwargs)


# 插件命令实现
class GenerateDataCommand(Command):
    """生成数据命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> Any:
        """执行生成数据命令"""
        try:
            # 获取插件实例
            plugin = getattr(ui_helper, "_data_generator_plugin", None)
            if not plugin:
                plugin = DataGeneratorPlugin()
                setattr(ui_helper, "_data_generator_plugin", plugin)

            # 解析参数
            if isinstance(value, dict):
                data_type = value.get("type", "name")
                kwargs = value.get("params", {})
            else:
                data_type = str(value)
                kwargs = {}

            # 生成数据
            result = plugin.generate(data_type, **kwargs)

            # 如果指定了变量名，保存到变量管理器
            var_name = step.get("variable")
            if var_name and hasattr(ui_helper, "variable_manager"):
                ui_helper.variable_manager.set_variable(var_name, result)

            return result

        except Exception as e:
            logger.error(f"生成数据失败: {e}")
            raise


class GenerateBatchDataCommand(Command):
    """批量生成数据命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> Any:
        """执行批量生成数据命令"""
        try:
            # 获取插件实例
            plugin = getattr(ui_helper, "_data_generator_plugin", None)
            if not plugin:
                plugin = DataGeneratorPlugin()
                setattr(ui_helper, "_data_generator_plugin", plugin)

            # 解析参数
            if isinstance(value, dict):
                data_type = value.get("type", "name")
                count = value.get("count", 10)
                kwargs = value.get("params", {})
            else:
                raise ValueError("批量生成数据需要字典格式的参数")

            # 批量生成数据
            result = plugin.generate_batch(data_type, count, **kwargs)

            # 如果指定了变量名，保存到变量管理器
            var_name = step.get("variable")
            if var_name and hasattr(ui_helper, "variable_manager"):
                ui_helper.variable_manager.set_variable(var_name, result)

            return result

        except Exception as e:
            logger.error(f"批量生成数据失败: {e}")
            raise


class RegisterDataTemplateCommand(Command):
    """注册数据模板命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> Any:
        """执行注册数据模板命令"""
        try:
            # 获取插件实例
            plugin = getattr(ui_helper, "_data_generator_plugin", None)
            if not plugin:
                plugin = DataGeneratorPlugin()
                setattr(ui_helper, "_data_generator_plugin", plugin)

            # 解析参数
            if not isinstance(value, dict):
                raise ValueError("注册数据模板需要字典格式的参数")

            name = value.get("name")
            generator_code = value.get("generator")
            description = value.get("description", "")
            category = value.get("category", "custom")

            if not name or not generator_code:
                raise ValueError("模板名称和生成器代码不能为空")

            # 创建生成器函数
            def custom_generator(**kwargs):
                # 这里可以执行用户自定义的生成器代码
                # 为了安全，可以限制可用的函数和模块
                safe_globals = {
                    "random": random,
                    "datetime": datetime,
                    "string": string,
                    "uuid": uuid,
                    "faker": plugin.faker,
                }
                return eval(generator_code, safe_globals, kwargs)

            # 注册生成器
            plugin.register_generator(name, custom_generator, description, category)

            return f"数据模板 '{name}' 注册成功"

        except Exception as e:
            logger.error(f"注册数据模板失败: {e}")
            raise


# 插件初始化和清理函数
def plugin_init():
    """插件初始化函数"""
    logger.info("数据生成插件已初始化")


def plugin_cleanup():
    """插件清理函数"""
    logger.info("数据生成插件已清理")


# 创建插件实例
data_generator_plugin = DataGeneratorPlugin()
