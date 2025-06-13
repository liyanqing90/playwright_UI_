"""变量管理混入类"""
import allure
from typing import Any, Dict, Optional
from utils.logger import logger
from .decorators import handle_page_error


class VariableManagementMixin:
    """变量管理混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @handle_page_error(description="存储变量")
    def store_variable(self, name: str, value: Any):
        """
        存储变量

        Args:
            name: 变量名
            value: 变量值
        """
        logger.info(f"存储变量: {name} = {value}")
        
        with allure.step(f"存储变量: {name}"):
            self.variable_manager.set_variable(name, value)
            logger.info(f"变量存储成功: {name} = {value}")
            
            allure.attach(
                f"变量名: {name}\n变量值: {value}\n类型: {type(value).__name__}",
                name="存储的变量",
                attachment_type=allure.attachment_type.TEXT
            )

    @handle_page_error(description="获取变量")
    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        获取变量

        Args:
            name: 变量名
            default: 默认值

        Returns:
            变量值
        """
        logger.info(f"获取变量: {name}")
        
        with allure.step(f"获取变量: {name}"):
            value = self.variable_manager.get_variable(name, default)
            logger.info(f"变量值: {name} = {value}")
            
            allure.attach(
                f"变量名: {name}\n变量值: {value}\n类型: {type(value).__name__}",
                name="获取的变量",
                attachment_type=allure.attachment_type.TEXT
            )
            
            return value

    @handle_page_error(description="删除变量")
    def delete_variable(self, name: str):
        """
        删除变量

        Args:
            name: 变量名
        """
        logger.info(f"删除变量: {name}")
        
        with allure.step(f"删除变量: {name}"):
            if self.variable_manager.has_variable(name):
                old_value = self.variable_manager.get_variable(name)
                self.variable_manager.delete_variable(name)
                logger.info(f"变量删除成功: {name} (原值: {old_value})")
                
                allure.attach(
                    f"已删除变量: {name}\n原值: {old_value}",
                    name="删除的变量",
                    attachment_type=allure.attachment_type.TEXT
                )
            else:
                logger.warning(f"变量不存在: {name}")
                allure.attach(
                    f"变量不存在: {name}",
                    name="删除变量警告",
                    attachment_type=allure.attachment_type.TEXT
                )

    @handle_page_error(description="检查变量是否存在")
    def has_variable(self, name: str) -> bool:
        """
        检查变量是否存在

        Args:
            name: 变量名

        Returns:
            是否存在
        """
        logger.info(f"检查变量是否存在: {name}")
        
        with allure.step(f"检查变量是否存在: {name}"):
            exists = self.variable_manager.has_variable(name)
            logger.info(f"变量 {name} 存在: {exists}")
            
            allure.attach(
                f"变量 {name} 存在: {exists}",
                name="变量存在性检查",
                attachment_type=allure.attachment_type.TEXT
            )
            
            return exists

    @handle_page_error(description="获取所有变量")
    def get_all_variables(self) -> Dict[str, Any]:
        """
        获取所有变量

        Returns:
            所有变量的字典
        """
        logger.info("获取所有变量")
        
        with allure.step("获取所有变量"):
            variables = self.variable_manager.get_all_variables()
            logger.info(f"共有 {len(variables)} 个变量")
            
            # 格式化变量信息用于报告
            if variables:
                var_info = "\n".join([
                    f"{name}: {value} ({type(value).__name__})"
                    for name, value in variables.items()
                ])
            else:
                var_info = "无变量"
            
            allure.attach(
                var_info,
                name="所有变量",
                attachment_type=allure.attachment_type.TEXT
            )
            
            return variables

    @handle_page_error(description="清除所有变量")
    def clear_all_variables(self):
        """
        清除所有变量
        """
        logger.info("清除所有变量")
        
        with allure.step("清除所有变量"):
            count = len(self.variable_manager.get_all_variables())
            self.variable_manager.clear_all_variables()
            logger.info(f"已清除 {count} 个变量")
            
            allure.attach(
                f"已清除 {count} 个变量",
                name="清除变量",
                attachment_type=allure.attachment_type.TEXT
            )

    @handle_page_error(description="替换字符串中的变量")
    def replace_variables(self, text: str) -> str:
        """
        替换字符串中的变量

        Args:
            text: 包含变量占位符的文本

        Returns:
            替换后的文本
        """
        if not text:
            return text
            
        logger.info(f"替换变量: {text}")
        
        with allure.step(f"替换变量"):
            result = self.variable_manager.replace_variables_refactored(text)
            
            if result != text:
                logger.info(f"变量替换结果: {text} -> {result}")
                
                allure.attach(
                    f"原文本: {text}\n替换后: {result}",
                    name="变量替换",
                    attachment_type=allure.attachment_type.TEXT
                )
            else:
                logger.debug(f"文本无需替换: {text}")
            
            return result

    @handle_page_error(description="批量存储变量")
    def store_variables_batch(self, variables: Dict[str, Any]):
        """
        批量存储变量

        Args:
            variables: 变量字典
        """
        logger.info(f"批量存储 {len(variables)} 个变量")
        
        with allure.step(f"批量存储变量"):
            for name, value in variables.items():
                self.variable_manager.set_variable(name, value)
                logger.debug(f"存储变量: {name} = {value}")
            
            logger.info(f"批量存储变量成功: {len(variables)} 个")
            
            # 格式化变量信息用于报告
            var_info = "\n".join([
                f"{name}: {value} ({type(value).__name__})"
                for name, value in variables.items()
            ])
            
            allure.attach(
                var_info,
                name="批量存储的变量",
                attachment_type=allure.attachment_type.TEXT
            )

    @handle_page_error(description="从元素文本存储变量")
    def store_element_text_as_variable(self, selector: str, variable_name: str):
        """
        从元素文本存储变量

        Args:
            selector: 元素选择器
            variable_name: 变量名
        """
        logger.info(f"从元素文本存储变量: {selector} -> {variable_name}")
        
        with allure.step(f"从元素文本存储变量: {selector}"):
            # 获取元素文本
            element_text = self.get_text(selector)
            
            # 存储到变量
            self.store_variable(variable_name, element_text)
            
            logger.info(f"元素文本已存储到变量: {variable_name} = {element_text}")
            
            allure.attach(
                f"元素: {selector}\n文本: {element_text}\n变量: {variable_name}",
                name="从元素存储的变量",
                attachment_type=allure.attachment_type.TEXT
            )

    @handle_page_error(description="从元素属性存储变量")
    def store_element_attribute_as_variable(self, selector: str, attribute: str, variable_name: str):
        """
        从元素属性存储变量

        Args:
            selector: 元素选择器
            attribute: 属性名
            variable_name: 变量名
        """
        logger.info(f"从元素属性存储变量: {selector}.{attribute} -> {variable_name}")
        
        with allure.step(f"从元素属性存储变量: {selector}.{attribute}"):
            # 获取元素属性
            attribute_value = self.get_element_attribute(selector, attribute)
            
            # 存储到变量
            self.store_variable(variable_name, attribute_value)
            
            logger.info(f"元素属性已存储到变量: {variable_name} = {attribute_value}")
            
            allure.attach(
                f"元素: {selector}\n属性: {attribute}\n值: {attribute_value}\n变量: {variable_name}",
                name="从元素属性存储的变量",
                attachment_type=allure.attachment_type.TEXT
            )

    @handle_page_error(description="从页面信息存储变量")
    def store_page_info_as_variable(self, info_type: str, variable_name: str):
        """
        从页面信息存储变量

        Args:
            info_type: 信息类型 ('url', 'title')
            variable_name: 变量名
        """
        logger.info(f"从页面信息存储变量: {info_type} -> {variable_name}")
        
        with allure.step(f"从页面信息存储变量: {info_type}"):
            if info_type == "url":
                value = self.get_current_url()
            elif info_type == "title":
                value = self.get_page_title()
            else:
                raise ValueError(f"不支持的页面信息类型: {info_type}")
            
            # 存储到变量
            self.store_variable(variable_name, value)
            
            logger.info(f"页面信息已存储到变量: {variable_name} = {value}")
            
            allure.attach(
                f"信息类型: {info_type}\n值: {value}\n变量: {variable_name}",
                name="从页面信息存储的变量",
                attachment_type=allure.attachment_type.TEXT
            )

    @handle_page_error(description="验证变量值")
    def verify_variable_value(self, variable_name: str, expected_value: Any):
        """
        验证变量值

        Args:
            variable_name: 变量名
            expected_value: 期望值
        """
        logger.info(f"验证变量值: {variable_name} = {expected_value}")
        
        with allure.step(f"验证变量值: {variable_name}"):
            if not self.has_variable(variable_name):
                raise AssertionError(f"变量不存在: {variable_name}")
            
            actual_value = self.get_variable(variable_name)
            
            # 处理变量替换
            resolved_expected = self.variable_manager.replace_variables_refactored(expected_value)
            
            assert str(actual_value) == str(resolved_expected), (
                f"变量值验证失败: {variable_name} 期望 '{resolved_expected}', 实际 '{actual_value}'"
            )
            
            logger.info(f"变量值验证成功: {variable_name} = {actual_value}")
            
            allure.attach(
                f"变量: {variable_name}\n期望值: {resolved_expected}\n实际值: {actual_value}\n结果: 验证成功",
                name="变量值验证",
                attachment_type=allure.attachment_type.TEXT
            )

    @handle_page_error(description="增加数值变量")
    def increment_variable(self, variable_name: str, increment: int = 1):
        """
        增加数值变量

        Args:
            variable_name: 变量名
            increment: 增量
        """
        logger.info(f"增加变量值: {variable_name} + {increment}")
        
        with allure.step(f"增加变量值: {variable_name}"):
            if not self.has_variable(variable_name):
                # 如果变量不存在，初始化为0
                self.store_variable(variable_name, 0)
                logger.info(f"变量不存在，初始化为0: {variable_name}")
            
            current_value = self.get_variable(variable_name)
            
            try:
                new_value = int(current_value) + increment
                self.store_variable(variable_name, new_value)
                
                logger.info(f"变量值增加成功: {variable_name} {current_value} -> {new_value}")
                
                allure.attach(
                    f"变量: {variable_name}\n原值: {current_value}\n增量: {increment}\n新值: {new_value}",
                    name="变量值增加",
                    attachment_type=allure.attachment_type.TEXT
                )
                
            except (ValueError, TypeError) as e:
                logger.error(f"变量值增加失败: {variable_name} 不是数值类型 ({current_value})")
                raise ValueError(f"变量 {variable_name} 不是数值类型: {current_value}")

    @handle_page_error(description="格式化变量")
    def format_variable(self, variable_name: str, format_string: str, new_variable_name: Optional[str] = None):
        """
        格式化变量

        Args:
            variable_name: 源变量名
            format_string: 格式化字符串，使用 {value} 作为占位符
            new_variable_name: 新变量名，如果不提供则覆盖原变量
        """
        target_var = new_variable_name or variable_name
        logger.info(f"格式化变量: {variable_name} -> {target_var}")
        
        with allure.step(f"格式化变量: {variable_name}"):
            if not self.has_variable(variable_name):
                raise ValueError(f"变量不存在: {variable_name}")
            
            original_value = self.get_variable(variable_name)
            
            try:
                # 替换格式化字符串中的变量
                resolved_format = self.variable_manager.replace_variables_refactored(format_string)
                
                # 格式化值
                formatted_value = resolved_format.format(value=original_value)
                
                # 存储格式化后的值
                self.store_variable(target_var, formatted_value)
                
                logger.info(f"变量格式化成功: {variable_name} ({original_value}) -> {target_var} ({formatted_value})")
                
                allure.attach(
                    f"源变量: {variable_name}\n原值: {original_value}\n格式: {resolved_format}\n目标变量: {target_var}\n格式化值: {formatted_value}",
                    name="变量格式化",
                    attachment_type=allure.attachment_type.TEXT
                )
                
            except Exception as e:
                logger.error(f"变量格式化失败: {e}")
                raise ValueError(f"变量格式化失败: {e}")