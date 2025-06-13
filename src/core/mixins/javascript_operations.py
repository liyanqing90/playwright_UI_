"""JavaScript执行混入类"""
import allure
from typing import Any, Optional
from utils.logger import logger
from .decorators import handle_page_error
from config.constants import DEFAULT_TIMEOUT


class JavaScriptOperationsMixin:
    """JavaScript执行混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @handle_page_error(description="执行JavaScript脚本")
    def execute_script(self, script: str, *args, timeout: int = DEFAULT_TIMEOUT) -> Any:
        """
        执行JavaScript脚本

        Args:
            script: 要执行的JavaScript代码
            *args: 传递给脚本的参数
            timeout: 超时时间(毫秒)

        Returns:
            脚本执行结果
        """
        # 替换变量
        resolved_script = self.variable_manager.replace_variables_refactored(script)
        
        logger.info(f"执行JavaScript脚本: {resolved_script[:100]}...")
        
        with allure.step(f"执行JavaScript脚本"):
            try:
                result = self.page.evaluate(resolved_script, *args, timeout=timeout)
                logger.info(f"脚本执行成功，结果: {result}")
                
                # 添加脚本信息到报告
                allure.attach(
                    f"脚本: {resolved_script}\n结果: {result}",
                    name="JavaScript执行结果",
                    attachment_type=allure.attachment_type.TEXT
                )
                
                return result
                
            except Exception as e:
                logger.error(f"JavaScript脚本执行失败: {e}")
                allure.attach(
                    f"脚本: {resolved_script}\n错误: {str(e)}",
                    name="JavaScript执行失败",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise

    @handle_page_error(description="滚动到页面顶部")
    def scroll_to_top(self):
        """滚动到页面顶部"""
        logger.info("滚动到页面顶部")
        
        with allure.step("滚动到页面顶部"):
            self.execute_script("window.scrollTo(0, 0)")
            logger.info("已滚动到页面顶部")

    @handle_page_error(description="滚动到页面底部")
    def scroll_to_bottom(self):
        """滚动到页面底部"""
        logger.info("滚动到页面底部")
        
        with allure.step("滚动到页面底部"):
            self.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            logger.info("已滚动到页面底部")

    @handle_page_error(description="滚动到指定位置")
    def scroll_to_position(self, x: int, y: int):
        """
        滚动到指定位置

        Args:
            x: 水平位置
            y: 垂直位置
        """
        logger.info(f"滚动到位置 ({x}, {y})")
        
        with allure.step(f"滚动到位置 ({x}, {y})"):
            self.execute_script(f"window.scrollTo({x}, {y})")
            logger.info(f"已滚动到位置 ({x}, {y})")

    @handle_page_error(description="滚动元素到可视区域")
    def scroll_element_into_view(self, selector: str, behavior: str = "smooth"):
        """
        滚动元素到可视区域

        Args:
            selector: 元素选择器
            behavior: 滚动行为，'smooth' 或 'auto'
        """
        logger.info(f"滚动元素到可视区域: {selector}")
        
        with allure.step(f"滚动元素到可视区域: {selector}"):
            script = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                element.scrollIntoView({{ behavior: '{behavior}', block: 'center' }});
                return true;
            }}
            return false;
            """
            
            result = self.execute_script(script)
            if result:
                logger.info(f"元素 {selector} 已滚动到可视区域")
            else:
                logger.warning(f"未找到元素 {selector}")

    @handle_page_error(description="获取页面高度")
    def get_page_height(self) -> int:
        """获取页面高度"""
        logger.info("获取页面高度")
        
        with allure.step("获取页面高度"):
            height = self.execute_script("return document.body.scrollHeight")
            logger.info(f"页面高度: {height}px")
            return height

    @handle_page_error(description="获取页面宽度")
    def get_page_width(self) -> int:
        """获取页面宽度"""
        logger.info("获取页面宽度")
        
        with allure.step("获取页面宽度"):
            width = self.execute_script("return document.body.scrollWidth")
            logger.info(f"页面宽度: {width}px")
            return width

    @handle_page_error(description="获取视口大小")
    def get_viewport_size(self) -> dict:
        """获取视口大小"""
        logger.info("获取视口大小")
        
        with allure.step("获取视口大小"):
            size = self.execute_script("""
                return {
                    width: window.innerWidth,
                    height: window.innerHeight
                }
            """)
            logger.info(f"视口大小: {size}")
            return size

    @handle_page_error(description="设置元素属性")
    def set_element_attribute(self, selector: str, attribute: str, value: str):
        """
        设置元素属性

        Args:
            selector: 元素选择器
            attribute: 属性名
            value: 属性值
        """
        # 替换变量
        resolved_value = self.variable_manager.replace_variables_refactored(value)
        
        logger.info(f"设置元素 {selector} 的属性 {attribute} = {resolved_value}")
        
        with allure.step(f"设置元素属性: {selector}.{attribute} = {resolved_value}"):
            script = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                element.setAttribute('{attribute}', '{resolved_value}');
                return true;
            }}
            return false;
            """
            
            result = self.execute_script(script)
            if result:
                logger.info(f"属性设置成功: {selector}.{attribute} = {resolved_value}")
            else:
                logger.warning(f"未找到元素 {selector}")

    @handle_page_error(description="移除元素属性")
    def remove_element_attribute(self, selector: str, attribute: str):
        """
        移除元素属性

        Args:
            selector: 元素选择器
            attribute: 属性名
        """
        logger.info(f"移除元素 {selector} 的属性 {attribute}")
        
        with allure.step(f"移除元素属性: {selector}.{attribute}"):
            script = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                element.removeAttribute('{attribute}');
                return true;
            }}
            return false;
            """
            
            result = self.execute_script(script)
            if result:
                logger.info(f"属性移除成功: {selector}.{attribute}")
            else:
                logger.warning(f"未找到元素 {selector}")

    @handle_page_error(description="设置元素样式")
    def set_element_style(self, selector: str, property_name: str, value: str):
        """
        设置元素样式

        Args:
            selector: 元素选择器
            property_name: CSS属性名
            value: CSS属性值
        """
        # 替换变量
        resolved_value = self.variable_manager.replace_variables_refactored(value)
        
        logger.info(f"设置元素 {selector} 的样式 {property_name} = {resolved_value}")
        
        with allure.step(f"设置元素样式: {selector}.{property_name} = {resolved_value}"):
            script = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                element.style['{property_name}'] = '{resolved_value}';
                return true;
            }}
            return false;
            """
            
            result = self.execute_script(script)
            if result:
                logger.info(f"样式设置成功: {selector}.{property_name} = {resolved_value}")
            else:
                logger.warning(f"未找到元素 {selector}")

    @handle_page_error(description="高亮显示元素")
    def highlight_element(self, selector: str, duration: int = 2000):
        """
        高亮显示元素

        Args:
            selector: 元素选择器
            duration: 高亮持续时间(毫秒)
        """
        logger.info(f"高亮显示元素: {selector}")
        
        with allure.step(f"高亮显示元素: {selector}"):
            script = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                const originalStyle = element.style.cssText;
                element.style.border = '3px solid red';
                element.style.backgroundColor = 'yellow';
                element.style.transition = 'all 0.3s';
                
                setTimeout(() => {{
                    element.style.cssText = originalStyle;
                }}, {duration});
                
                return true;
            }}
            return false;
            """
            
            result = self.execute_script(script)
            if result:
                logger.info(f"元素 {selector} 已高亮显示")
            else:
                logger.warning(f"未找到元素 {selector}")

    @handle_page_error(description="获取元素计算样式")
    def get_computed_style(self, selector: str, property_name: str) -> Optional[str]:
        """
        获取元素的计算样式

        Args:
            selector: 元素选择器
            property_name: CSS属性名

        Returns:
            CSS属性值
        """
        logger.info(f"获取元素 {selector} 的计算样式 {property_name}")
        
        with allure.step(f"获取计算样式: {selector}.{property_name}"):
            script = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                const style = window.getComputedStyle(element);
                return style.getPropertyValue('{property_name}');
            }}
            return null;
            """
            
            result = self.execute_script(script)
            logger.info(f"计算样式 {property_name}: {result}")
            return result

    @handle_page_error(description="检查元素是否在视口中")
    def is_element_in_viewport(self, selector: str) -> bool:
        """
        检查元素是否在视口中

        Args:
            selector: 元素选择器

        Returns:
            是否在视口中
        """
        logger.info(f"检查元素是否在视口中: {selector}")
        
        with allure.step(f"检查元素是否在视口中: {selector}"):
            script = f"""
            const element = document.querySelector('{selector}');
            if (!element) return false;
            
            const rect = element.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
            """
            
            result = self.execute_script(script)
            logger.info(f"元素 {selector} 在视口中: {result}")
            return result

    @handle_page_error(description="模拟鼠标悬停")
    def simulate_hover(self, selector: str):
        """
        模拟鼠标悬停

        Args:
            selector: 元素选择器
        """
        logger.info(f"模拟鼠标悬停: {selector}")
        
        with allure.step(f"模拟鼠标悬停: {selector}"):
            script = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                const event = new MouseEvent('mouseover', {{
                    view: window,
                    bubbles: true,
                    cancelable: true
                }});
                element.dispatchEvent(event);
                return true;
            }}
            return false;
            """
            
            result = self.execute_script(script)
            if result:
                logger.info(f"鼠标悬停模拟成功: {selector}")
            else:
                logger.warning(f"未找到元素 {selector}")

    @handle_page_error(description="触发自定义事件")
    def trigger_event(self, selector: str, event_type: str, event_data: Optional[dict] = None):
        """
        触发自定义事件

        Args:
            selector: 元素选择器
            event_type: 事件类型
            event_data: 事件数据
        """
        logger.info(f"触发事件: {selector} - {event_type}")
        
        with allure.step(f"触发事件: {selector} - {event_type}"):
            event_data_str = "{}" if not event_data else str(event_data).replace("'", '"')
            
            script = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                const event = new CustomEvent('{event_type}', {{
                    detail: {event_data_str},
                    bubbles: true,
                    cancelable: true
                }});
                element.dispatchEvent(event);
                return true;
            }}
            return false;
            """
            
            result = self.execute_script(script)
            if result:
                logger.info(f"事件触发成功: {selector} - {event_type}")
            else:
                logger.warning(f"未找到元素 {selector}")