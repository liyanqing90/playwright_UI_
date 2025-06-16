"""命令注册机制使用示例"""

import asyncio
from typing import Dict, Any

# 导入新的命令系统组件
from src.automation.commands.base_command import CommandRegistry, Command
from src.automation.commands.command_config import command_config_manager
from src.automation.commands.command_executor import CommandExecutor
from src.automation.commands.command_loader import CommandLoader
from src.automation.commands.command_monitor import command_monitor
from src.core.plugin_compatibility import PluginManager
# 配置日志
from utils.logger import logger


def example_1_basic_command_usage():
    """示例1：基本命令使用"""
    print("\n=== 示例1：基本命令使用 ===")
    
    # 自动发现并注册所有命令
    CommandRegistry.auto_discover_commands('src.automation.commands')
    
    # 列出所有已注册的命令
    commands = CommandRegistry.list_commands()
    print(f"已注册的命令: {list(commands.keys())}")
    
    # 获取特定命令
    navigate_cmd = CommandRegistry.get_command('navigate')
    if navigate_cmd:
        print(f"获取到导航命令: {navigate_cmd.__class__.__name__}")
    
    # 检查命令是否启用
    is_enabled = CommandRegistry.is_command_enabled('navigate')
    print(f"导航命令是否启用: {is_enabled}")


def example_2_command_configuration():
    """示例2：命令配置管理"""
    print("\n=== 示例2：命令配置管理 ===")
    
    # 设置命令配置
    command_config_manager.set_command_config('navigate', {
        'timeout': 30,
        'retry_count': 3,
        'enabled': True,
        'log_level': 'INFO'
    })
    
    # 获取命令配置
    config = command_config_manager.get_command_config('navigate')
    print(f"导航命令配置: {config}")
    
    # 设置全局配置
    command_config_manager.set_global_config({
        'default_timeout': 30,
        'default_retry_count': 2,
        'enable_monitoring': True,
        'log_level': 'INFO'
    })
    
    # 获取全局配置
    global_config = command_config_manager.get_global_config()
    print(f"全局配置: {global_config}")


def example_3_command_monitoring():
    """示例3：命令监控"""
    print("\n=== 示例3：命令监控 ===")
    
    # 启用监控
    command_monitor.enable()
    
    # 设置性能阈值
    command_monitor.set_threshold('navigate', 'execution_time', 5.0)  # 5秒
    command_monitor.set_threshold('navigate', 'error_rate', 0.1)      # 10%
    
    # 添加监控监听器
    def on_threshold_exceeded(command_name: str, metric: str, value: float, threshold: float):
        print(f"⚠️ 阈值超出 - 命令: {command_name}, 指标: {metric}, 值: {value}, 阈值: {threshold}")
    
    command_monitor.add_listener('threshold_exceeded', on_threshold_exceeded)
    
    # 模拟命令执行（会被监控）
    @command_monitor.monitor_command
    def simulate_command_execution(command_name: str, duration: float, should_fail: bool = False):
        import time
        time.sleep(duration)
        if should_fail:
            raise Exception("模拟命令失败")
        return f"命令 {command_name} 执行成功"
    
    # 执行一些命令进行监控
    try:
        simulate_command_execution('navigate', 0.5)
        simulate_command_execution('click', 0.2)
        simulate_command_execution('fill', 0.3)
        simulate_command_execution('navigate', 6.0)  # 这个会触发阈值警告
    except Exception as e:
        print(f"命令执行失败: {e}")
    
    # 生成监控报告
    report = command_monitor.generate_report()
    print(f"\n监控报告:")
    for command_name, metrics in report.items():
        print(f"  {command_name}: {metrics}")


def example_4_plugin_management():
    """示例4：插件管理"""
    print("\n=== 示例4：插件管理 ===")
    
    plugin_manager = PluginManager()
    
    # 发现插件
    plugins = plugin_manager.discover_plugins('examples')
    print(f"发现的插件: {[p['name'] for p in plugins]}")
    
    # 加载插件
    if plugins:
        plugin_path = plugins[0]['path']
        success = plugin_manager.load_plugin(plugin_path)
        print(f"插件加载{'成功' if success else '失败'}: {plugin_path}")
        
        # 列出已加载的插件
        loaded_plugins = plugin_manager.list_plugins()
        print(f"已加载的插件: {list(loaded_plugins.keys())}")
        
        # 获取插件信息
        if loaded_plugins:
            plugin_name = list(loaded_plugins.keys())[0]
            plugin_info = plugin_manager.get_plugin_info(plugin_name)
            print(f"插件信息: {plugin_info}")


def example_5_command_executor():
    """示例5：命令执行器"""
    print("\n=== 示例5：命令执行器 ===")
    
    executor = CommandExecutor()
    
    # 模拟UI助手和步骤数据
    class MockUIHelper:
        def navigate(self, url):
            print(f"导航到: {url}")
            return True
        
        def click(self, selector):
            print(f"点击: {selector}")
            return True
    
    ui_helper = MockUIHelper()
    
    # 单个命令执行
    step = {
        'action': 'navigate',
        'selector': '',
        'value': 'https://example.com',
        'timeout': 10
    }
    
    try:
        result = executor.execute_command(
            command_name='navigate',
            ui_helper=ui_helper,
            selector=step['selector'],
            value=step['value'],
            step=step
        )
        print(f"命令执行结果: {result}")
    except Exception as e:
        print(f"命令执行失败: {e}")
    
    # 批量命令执行
    steps = [
        {'action': 'navigate', 'selector': '', 'value': 'https://example.com'},
        {'action': 'click', 'selector': '#button1', 'value': ''},
        {'action': 'click', 'selector': '#button2', 'value': ''}
    ]
    
    try:
        results = executor.execute_batch(
            steps=steps,
            ui_helper=ui_helper,
            parallel=False  # 顺序执行
        )
        print(f"批量执行结果: {results}")
    except Exception as e:
        print(f"批量执行失败: {e}")


async def example_6_async_execution():
    """示例6：异步命令执行"""
    print("\n=== 示例6：异步命令执行 ===")
    
    executor = CommandExecutor()
    
    # 模拟异步UI助手
    class AsyncMockUIHelper:
        async def navigate(self, url):
            await asyncio.sleep(0.1)  # 模拟异步操作
            print(f"异步导航到: {url}")
            return True
        
        async def click(self, selector):
            await asyncio.sleep(0.05)  # 模拟异步操作
            print(f"异步点击: {selector}")
            return True
    
    ui_helper = AsyncMockUIHelper()
    
    # 异步单个命令执行
    step = {
        'action': 'navigate',
        'selector': '',
        'value': 'https://example.com'
    }
    
    try:
        result = await executor.execute_command_async(
            command_name='navigate',
            ui_helper=ui_helper,
            selector=step['selector'],
            value=step['value'],
            step=step
        )
        print(f"异步命令执行结果: {result}")
    except Exception as e:
        print(f"异步命令执行失败: {e}")
    
    # 异步批量命令执行（并行）
    steps = [
        {'action': 'click', 'selector': '#button1', 'value': ''},
        {'action': 'click', 'selector': '#button2', 'value': ''},
        {'action': 'click', 'selector': '#button3', 'value': ''}
    ]
    
    try:
        results = await executor.execute_batch_async(
            steps=steps,
            ui_helper=ui_helper,
            parallel=True  # 并行执行
        )
        print(f"异步批量执行结果: {results}")
    except Exception as e:
        print(f"异步批量执行失败: {e}")


def example_7_lazy_loading():
    """示例7：延迟加载"""
    print("\n=== 示例7：延迟加载 ===")
    
    loader = CommandLoader()
    
    # 预加载常用命令
    loader.preload_common_commands()
    print("已预加载常用命令")
    
    # 获取命令类（延迟加载）
    navigate_class = loader.get_command_class('navigate')
    if navigate_class:
        print(f"延迟加载的导航命令类: {navigate_class.__name__}")
    
    # 查看缓存状态
    cache_info = loader.get_cache_info()
    print(f"缓存信息: {cache_info}")
    
    # 清理缓存
    loader.clear_cache()
    print("缓存已清理")


def example_8_custom_command():
    """示例8：自定义命令"""
    print("\n=== 示例8：自定义命令 ===")
    
    # 定义自定义命令
    @CommandRegistry.register('custom_hello')
    class CustomHelloCommand(Command):
        """自定义问候命令"""
        
        def validate_args(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> bool:
            return value is not None
        
        def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> str:
            name = value or "World"
            message = f"Hello, {name}!"
            print(message)
            return message
    
    # 使用自定义命令
    hello_cmd = CommandRegistry.get_command('custom_hello')
    if hello_cmd:
        result = hello_cmd.execute(None, '', 'Python开发者', {})
        print(f"自定义命令结果: {result}")


def main():
    """主函数：运行所有示例"""
    print("命令注册机制改进 - 使用示例")
    print("=" * 50)
    
    try:
        # 运行同步示例
        example_1_basic_command_usage()
        example_2_command_configuration()
        example_3_command_monitoring()
        example_4_plugin_management()
        example_5_command_executor()
        example_7_lazy_loading()
        example_8_custom_command()
        
        # 运行异步示例
        print("\n运行异步示例...")
        asyncio.run(example_6_async_execution())
        
        print("\n=== 所有示例执行完成 ===")
        
    except Exception as e:
        logger.error(f"示例执行失败: {e}", exc_info=True)


if __name__ == '__main__':
    main()