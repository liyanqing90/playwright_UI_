"""命令执行器"""

import asyncio
import time
import logging
from typing import Any, Dict, Optional, Callable, List
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from .base_command import Command, CommandRegistry
from .command_monitor import command_monitor
from .command_config import config_manager

logger = logging.getLogger(__name__)


class CommandExecutionError(Exception):
    """命令执行错误"""
    
    def __init__(self, command_name: str, message: str, original_error: Exception = None):
        self.command_name = command_name
        self.original_error = original_error
        super().__init__(f"Command '{command_name}' failed: {message}")


class CommandTimeoutError(CommandExecutionError):
    """命令超时错误"""
    pass


class CommandValidationError(CommandExecutionError):
    """命令验证错误"""
    pass


class CommandExecutor:
    """命令执行器"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or config_manager.get_global_config().max_concurrent_commands
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.execution_hooks: Dict[str, List[Callable]] = {
            'before_execute': [],
            'after_execute': [],
            'on_error': [],
            'on_timeout': [],
            'on_retry': []
        }
    
    def add_hook(self, hook_type: str, hook_func: Callable):
        """添加执行钩子"""
        if hook_type in self.execution_hooks:
            self.execution_hooks[hook_type].append(hook_func)
        else:
            logger.warning(f"Unknown hook type: {hook_type}")
    
    def remove_hook(self, hook_type: str, hook_func: Callable):
        """移除执行钩子"""
        if hook_type in self.execution_hooks and hook_func in self.execution_hooks[hook_type]:
            self.execution_hooks[hook_type].remove(hook_func)
    
    def _call_hooks(self, hook_type: str, *args, **kwargs):
        """调用钩子函数"""
        for hook in self.execution_hooks.get(hook_type, []):
            try:
                hook(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {hook_type} hook: {e}")
    
    def execute_command(self, action: str, *args, **kwargs) -> Any:
        """执行命令"""
        command = CommandRegistry.get_command(action)
        if not command:
            raise CommandExecutionError(action, f"Command not found: {action}")
        
        return self._execute_with_features(command, *args, **kwargs)
    
    def _execute_with_features(self, command: Command, *args, **kwargs) -> Any:
        """带完整功能的命令执行"""
        command_name = command.name
        config = command.config
        
        # 检查命令是否启用
        if not command.is_enabled():
            raise CommandExecutionError(command_name, "Command is disabled")
        
        # 验证参数
        if not command.validate_args(*args, **kwargs):
            raise CommandValidationError(command_name, "Invalid arguments")
        
        # 调用前置钩子
        self._call_hooks('before_execute', command_name, *args, **kwargs)
        
        # 执行命令（带重试和超时）
        retry_count = config.retry_count
        retry_delay = config.retry_delay
        timeout = config.timeout
        
        last_error = None
        
        for attempt in range(retry_count + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retrying command {command_name}, attempt {attempt + 1}/{retry_count + 1}")
                    self._call_hooks('on_retry', command_name, attempt, *args, **kwargs)
                    time.sleep(retry_delay)
                
                # 执行命令（带超时）
                result = self._execute_with_timeout(command, timeout, *args, **kwargs)
                
                # 调用后置钩子
                self._call_hooks('after_execute', command_name, result, *args, **kwargs)
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Command {command_name} failed on attempt {attempt + 1}: {e}")
                
                if attempt == retry_count:
                    # 最后一次尝试失败
                    self._call_hooks('on_error', command_name, e, *args, **kwargs)
                    if isinstance(e, (CommandTimeoutError, CommandValidationError)):
                        raise
                    else:
                        raise CommandExecutionError(command_name, str(e), e)
        
        # 不应该到达这里
        raise CommandExecutionError(command_name, "Unexpected execution path", last_error)
    
    def _execute_with_timeout(self, command: Command, timeout: float, *args, **kwargs) -> Any:
        """带超时的命令执行"""
        try:
            future = self.thread_pool.submit(command.execute_with_monitoring, *args, **kwargs)
            result = future.result(timeout=timeout)
            return result
        except FutureTimeoutError:
            self._call_hooks('on_timeout', command.name, timeout, *args, **kwargs)
            raise CommandTimeoutError(command.name, f"Command timed out after {timeout}s")
        except Exception as e:
            raise e
    
    async def execute_command_async(self, action: str, *args, **kwargs) -> Any:
        """异步执行命令"""
        command = CommandRegistry.get_command(action)
        if not command:
            raise CommandExecutionError(action, f"Command not found: {action}")
        
        return await self._execute_async_with_features(command, *args, **kwargs)
    
    async def _execute_async_with_features(self, command: Command, *args, **kwargs) -> Any:
        """异步带完整功能的命令执行"""
        command_name = command.name
        config = command.config
        
        # 检查命令是否启用
        if not command.is_enabled():
            raise CommandExecutionError(command_name, "Command is disabled")
        
        # 验证参数
        if not command.validate_args(*args, **kwargs):
            raise CommandValidationError(command_name, "Invalid arguments")
        
        # 调用前置钩子
        self._call_hooks('before_execute', command_name, *args, **kwargs)
        
        # 执行命令（带重试和超时）
        retry_count = config.retry_count
        retry_delay = config.retry_delay
        timeout = config.timeout
        
        last_error = None
        
        for attempt in range(retry_count + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retrying async command {command_name}, attempt {attempt + 1}/{retry_count + 1}")
                    self._call_hooks('on_retry', command_name, attempt, *args, **kwargs)
                    await asyncio.sleep(retry_delay)
                
                # 执行命令（带超时）
                result = await self._execute_async_with_timeout(command, timeout, *args, **kwargs)
                
                # 调用后置钩子
                self._call_hooks('after_execute', command_name, result, *args, **kwargs)
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Async command {command_name} failed on attempt {attempt + 1}: {e}")
                
                if attempt == retry_count:
                    # 最后一次尝试失败
                    self._call_hooks('on_error', command_name, e, *args, **kwargs)
                    if isinstance(e, (CommandTimeoutError, CommandValidationError)):
                        raise
                    else:
                        raise CommandExecutionError(command_name, str(e), e)
        
        # 不应该到达这里
        raise CommandExecutionError(command_name, "Unexpected execution path", last_error)
    
    async def _execute_async_with_timeout(self, command: Command, timeout: float, *args, **kwargs) -> Any:
        """异步带超时的命令执行"""
        try:
            # 使用监控上下文
            with command_monitor.monitor_command(command.name):
                result = await asyncio.wait_for(
                    command.execute_async(*args, **kwargs),
                    timeout=timeout
                )
            return result
        except asyncio.TimeoutError:
            self._call_hooks('on_timeout', command.name, timeout, *args, **kwargs)
            raise CommandTimeoutError(command.name, f"Async command timed out after {timeout}s")
        except Exception as e:
            raise e
    
    def execute_batch(self, commands: List[Dict[str, Any]], parallel: bool = False) -> List[Any]:
        """批量执行命令"""
        if parallel:
            return self._execute_batch_parallel(commands)
        else:
            return self._execute_batch_sequential(commands)
    
    def _execute_batch_sequential(self, commands: List[Dict[str, Any]]) -> List[Any]:
        """顺序执行命令批次"""
        results = []
        for cmd_info in commands:
            action = cmd_info['action']
            args = cmd_info.get('args', [])
            kwargs = cmd_info.get('kwargs', {})
            
            try:
                result = self.execute_command(action, *args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch command {action} failed: {e}")
                results.append(e)
        
        return results
    
    def _execute_batch_parallel(self, commands: List[Dict[str, Any]]) -> List[Any]:
        """并行执行命令批次"""
        futures = []
        
        for cmd_info in commands:
            action = cmd_info['action']
            args = cmd_info.get('args', [])
            kwargs = cmd_info.get('kwargs', {})
            
            future = self.thread_pool.submit(self.execute_command, action, *args, **kwargs)
            futures.append(future)
        
        results = []
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Parallel batch command failed: {e}")
                results.append(e)
        
        return results
    
    async def execute_batch_async(self, commands: List[Dict[str, Any]], parallel: bool = True) -> List[Any]:
        """异步批量执行命令"""
        if parallel:
            return await self._execute_batch_async_parallel(commands)
        else:
            return await self._execute_batch_async_sequential(commands)
    
    async def _execute_batch_async_sequential(self, commands: List[Dict[str, Any]]) -> List[Any]:
        """异步顺序执行命令批次"""
        results = []
        for cmd_info in commands:
            action = cmd_info['action']
            args = cmd_info.get('args', [])
            kwargs = cmd_info.get('kwargs', {})
            
            try:
                result = await self.execute_command_async(action, *args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Async batch command {action} failed: {e}")
                results.append(e)
        
        return results
    
    async def _execute_batch_async_parallel(self, commands: List[Dict[str, Any]]) -> List[Any]:
        """异步并行执行命令批次"""
        tasks = []
        
        for cmd_info in commands:
            action = cmd_info['action']
            args = cmd_info.get('args', [])
            kwargs = cmd_info.get('kwargs', {})
            
            task = self.execute_command_async(action, *args, **kwargs)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 记录异常
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Async parallel batch command {i} failed: {result}")
        
        return results
    
    def get_available_commands(self) -> List[str]:
        """获取可用命令列表"""
        return CommandRegistry.list_commands()
    
    def get_command_info(self, action: str) -> Optional[Dict[str, Any]]:
        """获取命令信息"""
        command = CommandRegistry.get_command(action)
        if not command:
            return None
        
        return {
            'name': command.name,
            'enabled': command.is_enabled(),
            'timeout': command.get_timeout(),
            'retry_count': command.config.retry_count,
            'retry_delay': command.config.retry_delay,
            'priority': command.config.priority,
            'tags': command.config.tags,
            'metadata': command.config.metadata
        }
    
    def shutdown(self):
        """关闭执行器"""
        self.thread_pool.shutdown(wait=True)
        logger.info("Command executor shutdown")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# 全局命令执行器实例
command_executor = CommandExecutor()