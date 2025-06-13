"""键盘操作混入类"""
import allure
from utils.logger import logger
from .decorators import handle_page_error
from config.constants import DEFAULT_TYPE_DELAY


class KeyboardOperationsMixin:
    """键盘操作混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @handle_page_error(description="按下键盘快捷键")
    def press_keyboard_shortcut(self, key_combination: str):
        """
        按下键盘快捷键组合
        例如: "Control+A", "Shift+ArrowDown", "Control+Shift+V"
        """
        with allure.step(f"按下键盘快捷键: {key_combination}"):
            keys = key_combination.split("+")
            
            try:
                # 按下所有修饰键
                for i in range(len(keys) - 1):
                    self.page.keyboard.down(keys[i])
                    logger.debug(f"按下修饰键: {keys[i]}")

                # 按下最后一个键
                self.page.keyboard.press(keys[-1])
                logger.debug(f"按下主键: {keys[-1]}")

            finally:
                # 释放所有修饰键（从后往前）
                for i in range(len(keys) - 2, -1, -1):
                    try:
                        self.page.keyboard.up(keys[i])
                        logger.debug(f"释放修饰键: {keys[i]}")
                    except Exception as e:
                        logger.warning(f"释放修饰键 {keys[i]} 失败: {e}")

            logger.info(f"成功按下键盘快捷键: {key_combination}")

    @handle_page_error(description="全局按键")
    def keyboard_press(self, key: str):
        """全局按键，不针对特定元素"""
        with allure.step(f"全局按键: {key}"):
            self.page.keyboard.press(key)
            logger.debug(f"全局按键: {key}")

    @handle_page_error(description="全局输入文本")
    def keyboard_type(self, text: str, delay: int = DEFAULT_TYPE_DELAY):
        """全局输入文本，不针对特定元素"""
        resolved_text = self.variable_manager.replace_variables_refactored(text)
        if resolved_text is not None:
            resolved_text = str(resolved_text)
        
        with allure.step(f"全局输入文本: {resolved_text}"):
            self.page.keyboard.type(resolved_text, delay=delay)
            logger.debug(f"全局输入文本: {resolved_text}")

    @handle_page_error(description="按下键盘按键并保持")
    def keyboard_down(self, key: str):
        """按下键盘按键并保持"""
        with allure.step(f"按下并保持按键: {key}"):
            self.page.keyboard.down(key)
            logger.debug(f"按下并保持按键: {key}")

    @handle_page_error(description="释放键盘按键")
    def keyboard_up(self, key: str):
        """释放键盘按键"""
        with allure.step(f"释放按键: {key}"):
            self.page.keyboard.up(key)
            logger.debug(f"释放按键: {key}")

    @handle_page_error(description="插入文本")
    def keyboard_insert_text(self, text: str):
        """插入文本（不触发键盘事件）"""
        resolved_text = self.variable_manager.replace_variables_refactored(text)
        if resolved_text is not None:
            resolved_text = str(resolved_text)
        
        with allure.step(f"插入文本: {resolved_text}"):
            self.page.keyboard.insert_text(resolved_text)
            logger.debug(f"插入文本: {resolved_text}")

    @handle_page_error(description="模拟组合键操作")
    def simulate_key_combination(self, *keys):
        """
        模拟组合键操作（更灵活的方式）
        例如: simulate_key_combination('Control', 'Shift', 'I')
        """
        key_combination = '+'.join(keys)
        with allure.step(f"模拟组合键: {key_combination}"):
            try:
                # 按下所有修饰键
                for key in keys[:-1]:
                    self.page.keyboard.down(key)
                    logger.debug(f"按下修饰键: {key}")

                # 按下最后一个键
                self.page.keyboard.press(keys[-1])
                logger.debug(f"按下主键: {keys[-1]}")

            finally:
                # 释放所有修饰键（从后往前）
                for key in reversed(keys[:-1]):
                    try:
                        self.page.keyboard.up(key)
                        logger.debug(f"释放修饰键: {key}")
                    except Exception as e:
                        logger.warning(f"释放修饰键 {key} 失败: {e}")

            logger.info(f"成功模拟组合键: {key_combination}")

    @handle_page_error(description="清空输入框并输入")
    def clear_and_type(self, selector: str, text: str, delay: int = DEFAULT_TYPE_DELAY):
        """清空输入框并输入新文本"""
        resolved_text = self.variable_manager.replace_variables_refactored(text)
        if resolved_text is not None:
            resolved_text = str(resolved_text)
        
        with allure.step(f"清空并输入文本到 {selector}: {resolved_text}"):
            # 聚焦到元素
            self._locator(selector).first.focus()
            # 全选
            self.page.keyboard.press('Control+a')
            # 输入新文本
            self.page.keyboard.type(resolved_text, delay=delay)
            logger.info(f"清空并输入文本到 {selector}: {resolved_text}")