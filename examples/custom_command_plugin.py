"""自定义命令插件示例"""

import random
import time
from typing import Dict, Any

from src.automation.commands.base_command import Command, CommandRegistry
from utils.logger import logger

# 插件元数据
PLUGIN_INFO = {
    'name': 'CustomCommandPlugin',
    'version': '1.0.0',
    'description': 'Example custom command plugin',
    'author': 'Plugin Developer',
    'commands': ['custom_wait', 'custom_log', 'custom_random']
}


@CommandRegistry.register('custom_wait')
class CustomWaitCommand(Command):
    """自定义等待命令"""
    
    def validate_args(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> bool:
        """验证等待参数"""
        wait_time = step.get('wait_time', value)
        if wait_time is None:
            logger.error("Wait time is required")
            return False
        
        try:
            float(wait_time)
        except (ValueError, TypeError):
            logger.error("Wait time must be a number")
            return False
        
        return True
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        """执行自定义等待"""
        self.before_execute(ui_helper, selector, value, step)
        
        try:
            wait_time = float(step.get('wait_time', value))
            reason = step.get('reason', 'Custom wait')
            
            logger.info(f"Custom wait: {wait_time}s - {reason}")
            time.sleep(wait_time)
            
            result = {'waited': wait_time, 'reason': reason}
            self.after_execute(result, ui_helper, selector, value, step)
            return result
            
        except Exception as e:
            self.on_error(e, ui_helper, selector, value, step)
            raise


@CommandRegistry.register('custom_log')
class CustomLogCommand(Command):
    """自定义日志命令"""
    
    def validate_args(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> bool:
        """验证日志参数"""
        message = step.get('message', value)
        if not message:
            logger.error("Log message is required")
            return False
        return True
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        """执行自定义日志"""
        self.before_execute(ui_helper, selector, value, step)
        
        try:
            message = step.get('message', value)
            level = step.get('level', 'info').lower()
            category = step.get('category', 'custom')
            
            log_message = f"[{category.upper()}] {message}"
            
            if level == 'debug':
                logger.debug(log_message)
            elif level == 'info':
                logger.info(log_message)
            elif level == 'warning':
                logger.warning(log_message)
            elif level == 'error':
                logger.error(log_message)
            else:
                logger.info(log_message)
            
            result = {
                'message': message,
                'level': level,
                'category': category,
                'timestamp': time.time()
            }
            
            self.after_execute(result, ui_helper, selector, value, step)
            return result
            
        except Exception as e:
            self.on_error(e, ui_helper, selector, value, step)
            raise


@CommandRegistry.register('custom_random')
class CustomRandomCommand(Command):
    """自定义随机命令"""
    
    def validate_args(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> bool:
        """验证随机参数"""
        action_type = step.get('type', 'number')
        if action_type not in ['number', 'choice', 'boolean']:
            logger.error(f"Invalid random type: {action_type}")
            return False
        
        if action_type == 'number':
            min_val = step.get('min', 0)
            max_val = step.get('max', 100)
            try:
                float(min_val)
                float(max_val)
            except (ValueError, TypeError):
                logger.error("Min and max values must be numbers")
                return False
        
        elif action_type == 'choice':
            choices = step.get('choices', [])
            if not choices or not isinstance(choices, list):
                logger.error("Choices must be a non-empty list")
                return False
        
        return True
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> Any:
        """执行自定义随机"""
        self.before_execute(ui_helper, selector, value, step)
        
        try:
            action_type = step.get('type', 'number')
            
            if action_type == 'number':
                min_val = float(step.get('min', 0))
                max_val = float(step.get('max', 100))
                is_int = step.get('integer', False)
                
                if is_int:
                    result = random.randint(int(min_val), int(max_val))
                else:
                    result = random.uniform(min_val, max_val)
                
                logger.info(f"Generated random number: {result}")
            
            elif action_type == 'choice':
                choices = step.get('choices', [])
                result = random.choice(choices)
                logger.info(f"Random choice from {choices}: {result}")
            
            elif action_type == 'boolean':
                result = random.choice([True, False])
                logger.info(f"Random boolean: {result}")
            
            else:
                raise ValueError(f"Unknown random type: {action_type}")
            
            # 可选：将结果存储到变量中
            var_name = step.get('store_in')
            if var_name and hasattr(ui_helper, 'set_variable'):
                ui_helper.set_variable(var_name, result)
                logger.info(f"Stored random result in variable: {var_name} = {result}")
            
            self.after_execute(result, ui_helper, selector, value, step)
            return result
            
        except Exception as e:
            self.on_error(e, ui_helper, selector, value, step)
            raise


# 插件初始化函数
def initialize_plugin():
    """初始化插件"""
    logger.info(f"Initializing plugin: {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")
    
    # 可以在这里进行插件特定的初始化
    # 例如：设置默认配置、注册事件监听器等
    
    return PLUGIN_INFO


# 插件清理函数
def cleanup_plugin():
    """清理插件"""
    logger.info(f"Cleaning up plugin: {PLUGIN_INFO['name']}")
    
    # 可以在这里进行插件特定的清理
    # 例如：取消注册命令、清理资源等
    
    # 取消注册命令
    for command_name in PLUGIN_INFO['commands']:
        try:
            CommandRegistry.unregister_command(command_name)
            logger.info(f"Unregistered command: {command_name}")
        except Exception as e:
            logger.error(f"Error unregistering command {command_name}: {e}")


# 插件配置验证函数
def validate_plugin_config(config: Dict[str, Any]) -> bool:
    """验证插件配置"""
    # 在这里可以验证插件特定的配置
    required_keys = ['enabled']
    
    for key in required_keys:
        if key not in config:
            logger.error(f"Missing required config key: {key}")
            return False
    
    return True


# 插件信息获取函数
def get_plugin_info() -> Dict[str, Any]:
    """获取插件信息"""
    return PLUGIN_INFO.copy()


if __name__ == '__main__':
    # 测试插件
    print(f"Plugin: {PLUGIN_INFO['name']}")
    print(f"Version: {PLUGIN_INFO['version']}")
    print(f"Commands: {', '.join(PLUGIN_INFO['commands'])}")
    
    # 初始化插件
    info = initialize_plugin()
    print(f"Plugin initialized: {info}")