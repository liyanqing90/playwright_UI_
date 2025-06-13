"""命令管理CLI工具"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from .base_command import CommandRegistry
from .command_monitor import command_monitor
from .command_config import config_manager
from .plugin_manager import PluginManager
from .command_executor import command_executor


class CommandCLI:
    """命令管理CLI"""
    
    def __init__(self):
        self.plugin_manager = PluginManager()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """创建命令行解析器"""
        parser = argparse.ArgumentParser(
            description="Command Management CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # 列出命令
        list_parser = subparsers.add_parser('list', help='List commands')
        list_parser.add_argument('--enabled-only', action='store_true', help='Show only enabled commands')
        list_parser.add_argument('--tag', help='Filter by tag')
        list_parser.add_argument('--format', choices=['table', 'json'], default='table', help='Output format')
        
        # 命令信息
        info_parser = subparsers.add_parser('info', help='Show command information')
        info_parser.add_argument('command_name', help='Command name')
        
        # 启用/禁用命令
        enable_parser = subparsers.add_parser('enable', help='Enable command')
        enable_parser.add_argument('command_name', help='Command name')
        
        disable_parser = subparsers.add_parser('disable', help='Disable command')
        disable_parser.add_argument('command_name', help='Command name')
        
        # 配置管理
        config_parser = subparsers.add_parser('config', help='Configuration management')
        config_subparsers = config_parser.add_subparsers(dest='config_action')
        
        # 显示配置
        config_subparsers.add_parser('show', help='Show configuration')
        
        # 设置配置
        set_config_parser = config_subparsers.add_parser('set', help='Set configuration')
        set_config_parser.add_argument('--command', help='Command name')
        set_config_parser.add_argument('--timeout', type=float, help='Timeout in seconds')
        set_config_parser.add_argument('--retry-count', type=int, help='Retry count')
        set_config_parser.add_argument('--retry-delay', type=float, help='Retry delay in seconds')
        set_config_parser.add_argument('--enabled', type=bool, help='Enable/disable command')
        set_config_parser.add_argument('--priority', type=int, help='Command priority')
        
        # 导入/导出配置
        import_config_parser = config_subparsers.add_parser('import', help='Import configuration')
        import_config_parser.add_argument('file', help='Configuration file path')
        import_config_parser.add_argument('--merge', action='store_true', help='Merge with existing config')
        
        export_config_parser = config_subparsers.add_parser('export', help='Export configuration')
        export_config_parser.add_argument('file', help='Output file path')
        
        # 重置配置
        config_subparsers.add_parser('reset', help='Reset configuration to defaults')
        
        # 监控管理
        monitor_parser = subparsers.add_parser('monitor', help='Monitoring management')
        monitor_subparsers = monitor_parser.add_subparsers(dest='monitor_action')
        
        # 显示监控报告
        monitor_subparsers.add_parser('report', help='Show monitoring report')
        
        # 显示指标
        metrics_parser = monitor_subparsers.add_parser('metrics', help='Show command metrics')
        metrics_parser.add_argument('--command', help='Specific command name')
        metrics_parser.add_argument('--format', choices=['table', 'json'], default='table', help='Output format')
        
        # 重置指标
        reset_metrics_parser = monitor_subparsers.add_parser('reset', help='Reset metrics')
        reset_metrics_parser.add_argument('--command', help='Specific command name (all if not specified)')
        
        # 启用/禁用监控
        monitor_subparsers.add_parser('enable', help='Enable monitoring')
        monitor_subparsers.add_parser('disable', help='Disable monitoring')
        
        # 插件管理
        plugin_parser = subparsers.add_parser('plugin', help='Plugin management')
        plugin_subparsers = plugin_parser.add_subparsers(dest='plugin_action')
        
        # 列出插件
        plugin_subparsers.add_parser('list', help='List plugins')
        
        # 加载插件
        load_plugin_parser = plugin_subparsers.add_parser('load', help='Load plugin')
        load_plugin_parser.add_argument('path', help='Plugin file path')
        
        # 卸载插件
        unload_plugin_parser = plugin_subparsers.add_parser('unload', help='Unload plugin')
        unload_plugin_parser.add_argument('name', help='Plugin name')
        
        # 启用/禁用插件
        enable_plugin_parser = plugin_subparsers.add_parser('enable', help='Enable plugin')
        enable_plugin_parser.add_argument('name', help='Plugin name')
        
        disable_plugin_parser = plugin_subparsers.add_parser('disable', help='Disable plugin')
        disable_plugin_parser.add_argument('name', help='Plugin name')
        
        # 发现命令
        discover_parser = subparsers.add_parser('discover', help='Discover commands')
        discover_parser.add_argument('--path', help='Discovery path')
        discover_parser.add_argument('--force', action='store_true', help='Force rediscovery')
        
        # 验证
        validate_parser = subparsers.add_parser('validate', help='Validate configuration')
        
        return parser
    
    def run(self, args: List[str] = None):
        """运行CLI"""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return
        
        try:
            if parsed_args.command == 'list':
                self.list_commands(parsed_args)
            elif parsed_args.command == 'info':
                self.show_command_info(parsed_args)
            elif parsed_args.command == 'enable':
                self.enable_command(parsed_args)
            elif parsed_args.command == 'disable':
                self.disable_command(parsed_args)
            elif parsed_args.command == 'config':
                self.handle_config(parsed_args)
            elif parsed_args.command == 'monitor':
                self.handle_monitor(parsed_args)
            elif parsed_args.command == 'plugin':
                self.handle_plugin(parsed_args)
            elif parsed_args.command == 'discover':
                self.discover_commands(parsed_args)
            elif parsed_args.command == 'validate':
                self.validate_config(parsed_args)
            else:
                print(f"Unknown command: {parsed_args.command}")
                
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    def list_commands(self, args):
        """列出命令"""
        commands = CommandRegistry.list_commands()
        
        if args.enabled_only:
            commands = [cmd for cmd in commands if config_manager.get_command_config(cmd).enabled]
        
        if args.tag:
            commands = [cmd for cmd in commands if args.tag in config_manager.get_command_config(cmd).tags]
        
        if args.format == 'json':
            command_info = []
            for cmd in commands:
                config = config_manager.get_command_config(cmd)
                command_info.append({
                    'name': cmd,
                    'enabled': config.enabled,
                    'timeout': config.timeout,
                    'retry_count': config.retry_count,
                    'priority': config.priority,
                    'tags': config.tags
                })
            print(json.dumps(command_info, indent=2))
        else:
            print(f"{'Command':<20} {'Enabled':<8} {'Timeout':<8} {'Retry':<6} {'Priority':<8} {'Tags'}")
            print("-" * 80)
            for cmd in commands:
                config = config_manager.get_command_config(cmd)
                tags_str = ', '.join(config.tags) if config.tags else ''
                print(f"{cmd:<20} {config.enabled!s:<8} {config.timeout:<8.1f} {config.retry_count:<6} {config.priority:<8} {tags_str}")
    
    def show_command_info(self, args):
        """显示命令信息"""
        command_name = args.command_name
        info = command_executor.get_command_info(command_name)
        
        if not info:
            print(f"Command not found: {command_name}")
            return
        
        print(f"Command: {info['name']}")
        print(f"Enabled: {info['enabled']}")
        print(f"Timeout: {info['timeout']}s")
        print(f"Retry Count: {info['retry_count']}")
        print(f"Retry Delay: {info['retry_delay']}s")
        print(f"Priority: {info['priority']}")
        print(f"Tags: {', '.join(info['tags'])}")
        
        if info['metadata']:
            print("\nMetadata:")
            for key, value in info['metadata'].items():
                print(f"  {key}: {value}")
    
    def enable_command(self, args):
        """启用命令"""
        config_manager.enable_command(args.command_name)
        print(f"Command '{args.command_name}' enabled")
    
    def disable_command(self, args):
        """禁用命令"""
        config_manager.disable_command(args.command_name)
        print(f"Command '{args.command_name}' disabled")
    
    def handle_config(self, args):
        """处理配置相关命令"""
        if args.config_action == 'show':
            self.show_config()
        elif args.config_action == 'set':
            self.set_config(args)
        elif args.config_action == 'import':
            self.import_config(args)
        elif args.config_action == 'export':
            self.export_config(args)
        elif args.config_action == 'reset':
            self.reset_config()
        else:
            print("Unknown config action")
    
    def show_config(self):
        """显示配置"""
        global_config = config_manager.get_global_config()
        print("Global Configuration:")
        print(f"  Default Timeout: {global_config.default_timeout}s")
        print(f"  Default Retry Count: {global_config.default_retry_count}")
        print(f"  Default Retry Delay: {global_config.default_retry_delay}s")
        print(f"  Max Concurrent Commands: {global_config.max_concurrent_commands}")
        print(f"  Monitoring Enabled: {global_config.enable_monitoring}")
        print(f"  Caching Enabled: {global_config.enable_caching}")
        print(f"  Auto Discovery Enabled: {global_config.auto_discovery_enabled}")
    
    def set_config(self, args):
        """设置配置"""
        if args.command:
            # 设置命令配置
            kwargs = {}
            if args.timeout is not None:
                kwargs['timeout'] = args.timeout
            if args.retry_count is not None:
                kwargs['retry_count'] = args.retry_count
            if args.retry_delay is not None:
                kwargs['retry_delay'] = args.retry_delay
            if args.enabled is not None:
                kwargs['enabled'] = args.enabled
            if args.priority is not None:
                kwargs['priority'] = args.priority
            
            if kwargs:
                config_manager.update_command_config(args.command, **kwargs)
                print(f"Updated configuration for command '{args.command}'")
            else:
                print("No configuration values provided")
        else:
            # 设置全局配置
            kwargs = {}
            if args.timeout is not None:
                kwargs['default_timeout'] = args.timeout
            if args.retry_count is not None:
                kwargs['default_retry_count'] = args.retry_count
            if args.retry_delay is not None:
                kwargs['default_retry_delay'] = args.retry_delay
            
            if kwargs:
                config_manager.update_global_config(**kwargs)
                print("Updated global configuration")
            else:
                print("No configuration values provided")
    
    def import_config(self, args):
        """导入配置"""
        config_manager.import_config(args.file, merge=args.merge)
        print(f"Configuration imported from {args.file}")
    
    def export_config(self, args):
        """导出配置"""
        config_manager.export_config(args.file)
        print(f"Configuration exported to {args.file}")
    
    def reset_config(self):
        """重置配置"""
        config_manager.reset_to_defaults()
        print("Configuration reset to defaults")
    
    def handle_monitor(self, args):
        """处理监控相关命令"""
        if args.monitor_action == 'report':
            self.show_monitor_report()
        elif args.monitor_action == 'metrics':
            self.show_metrics(args)
        elif args.monitor_action == 'reset':
            self.reset_metrics(args)
        elif args.monitor_action == 'enable':
            self.enable_monitoring()
        elif args.monitor_action == 'disable':
            self.disable_monitoring()
        else:
            print("Unknown monitor action")
    
    def show_monitor_report(self):
        """显示监控报告"""
        report = command_monitor.generate_report()
        print(report)
    
    def show_metrics(self, args):
        """显示指标"""
        metrics = command_monitor.get_metrics(args.command)
        
        if args.format == 'json':
            print(json.dumps(command_monitor.export_metrics(), indent=2))
        else:
            print(f"{'Command':<20} {'Count':<8} {'Total(s)':<10} {'Avg(s)':<8} {'Min(s)':<8} {'Max(s)':<8} {'Errors':<8}")
            print("-" * 90)
            for name, metric in metrics.items():
                min_time = metric.min_time if metric.min_time != float('inf') else 0
                print(f"{name:<20} {metric.execution_count:<8} {metric.total_time:<10.2f} {metric.avg_time:<8.2f} {min_time:<8.2f} {metric.max_time:<8.2f} {metric.error_count:<8}")
    
    def reset_metrics(self, args):
        """重置指标"""
        command_monitor.reset_metrics(args.command)
        if args.command:
            print(f"Reset metrics for command '{args.command}'")
        else:
            print("Reset all metrics")
    
    def enable_monitoring(self):
        """启用监控"""
        command_monitor.enable()
        print("Monitoring enabled")
    
    def disable_monitoring(self):
        """禁用监控"""
        command_monitor.disable()
        print("Monitoring disabled")
    
    def handle_plugin(self, args):
        """处理插件相关命令"""
        if args.plugin_action == 'list':
            self.list_plugins()
        elif args.plugin_action == 'load':
            self.load_plugin(args)
        elif args.plugin_action == 'unload':
            self.unload_plugin(args)
        elif args.plugin_action == 'enable':
            self.enable_plugin(args)
        elif args.plugin_action == 'disable':
            self.disable_plugin(args)
        else:
            print("Unknown plugin action")
    
    def list_plugins(self):
        """列出插件"""
        plugins = self.plugin_manager.list_plugins()
        if not plugins:
            print("No plugins loaded")
            return
        
        print(f"{'Plugin':<20} {'Version':<10} {'Enabled':<8} {'Commands':<10}")
        print("-" * 60)
        for plugin in plugins:
            info = self.plugin_manager.get_plugin_info(plugin)
            commands_count = len(info.get('commands', []))
            print(f"{plugin:<20} {info.get('version', 'N/A'):<10} {info.get('enabled', False)!s:<8} {commands_count:<10}")
    
    def load_plugin(self, args):
        """加载插件"""
        self.plugin_manager.load_plugin(args.path)
        print(f"Plugin loaded from {args.path}")
    
    def unload_plugin(self, args):
        """卸载插件"""
        self.plugin_manager.unload_plugin(args.name)
        print(f"Plugin '{args.name}' unloaded")
    
    def enable_plugin(self, args):
        """启用插件"""
        self.plugin_manager.enable_plugin(args.name)
        print(f"Plugin '{args.name}' enabled")
    
    def disable_plugin(self, args):
        """禁用插件"""
        self.plugin_manager.disable_plugin(args.name)
        print(f"Plugin '{args.name}' disabled")
    
    def discover_commands(self, args):
        """发现命令"""
        if args.path:
            CommandRegistry.auto_discover_commands(args.path, force=args.force)
            print(f"Commands discovered from {args.path}")
        else:
            CommandRegistry.auto_discover_commands(force=args.force)
            print("Commands auto-discovered")
    
    def validate_config(self, args):
        """验证配置"""
        errors = config_manager.validate_config()
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("Configuration is valid")


def main():
    """CLI入口点"""
    cli = CommandCLI()
    cli.run()


if __name__ == '__main__':
    main()