from datetime import datetime
from pathlib import Path

from loguru import logger

# 移除默认的 sink
logger.remove()

# 创建日志目录
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

# 生成日志文件名
log_file = log_dir / f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

# 添加控制台输出
logger.add(
    sink=lambda msg: print(msg),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> [<level>{level}</level>] <white>{message}</white> (<cyan>{file}:{line}</cyan>)",
    level="INFO",
    colorize=True
)

# 添加文件输出
logger.add(
    sink=str(log_file),
    format="{time:YYYY-MM-DD HH:mm:ss} [{level}] {message} ({file}:{line})",
    level="DEBUG",
    rotation="10 MB",  # 当文件达到10MB时轮转
    retention="1 week",  # 保留1周的日志
    encoding='utf-8'
)

# 导出 logger 实例供其他模块使用
__all__ = ['logger']
