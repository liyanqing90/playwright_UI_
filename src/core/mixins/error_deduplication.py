"""错误去重管理器
提供错误去重功能，避免相同错误的重复记录
"""
import hashlib
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Set

import yaml

from utils.logger import logger


@dataclass
class ErrorRecord:
    """错误记录"""
    error_hash: str
    error_message: str
    first_occurrence: float
    last_occurrence: float
    count: int = 1
    
    def update_occurrence(self):
        """更新最后发生时间并增加计数"""
        self.last_occurrence = time.time()
        self.count += 1

class ErrorDeduplicationManager:
    """错误去重管理器"""
    
    def __init__(self, config_file: str = None):
        # 加载配置
        self.config = self._load_config(config_file)
        
        # 从配置中获取参数
        dedup_config = self.config.get('error_deduplication', {})
        self.time_window = dedup_config.get('time_window', 300)
        self.max_same_error_count = dedup_config.get('max_same_error_count', 3)
        self.cleanup_interval = dedup_config.get('cleanup_interval', 600)
        self.enabled = dedup_config.get('enabled', True)
        
        # 错误记录存储
        self.error_records: Dict[str, ErrorRecord] = {}
        self.suppressed_errors: Set[str] = set()
        
        # 上次清理时间
        self.last_cleanup = time.time()
        
        # 错误分类规则
        self.custom_patterns = self.config.get('advanced', {}).get('custom_error_patterns', [])
        self.ignore_patterns = self.config.get('advanced', {}).get('ignore_patterns', [])
        
        logger.info(f"错误去重管理器已初始化 - 启用: {self.enabled}, 时间窗口: {self.time_window}s, 最大重复: {self.max_same_error_count}次")
    
    def _load_config(self, config_file: str = None) -> Dict:
        """加载配置文件"""
        if config_file is None:
            config_file = Path("config") / "error_deduplication.yaml"
        else:
            config_file = Path(config_file)
        
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                logger.info(f"已加载错误去重配置: {config_file}")
                return config or {}
            else:
                logger.warning(f"配置文件不存在: {config_file}，使用默认配置")
                return {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return {}
    
    def _generate_error_hash(self, error_message: str, error_type: str = None, 
                           selector: str = None) -> str:
        """生成错误哈希值"""
        # 标准化错误消息，移除时间戳、行号等变化的信息
        normalized_message = self._normalize_error_message(error_message)
        
        # 组合关键信息
        key_info = f"{error_type or 'Unknown'}:{normalized_message}"
        if selector:
            key_info += f":selector:{selector}"
            
        return hashlib.md5(key_info.encode('utf-8')).hexdigest()
    
    def _normalize_error_message(self, message: str) -> str:
        """标准化错误消息，移除变化的部分"""
        import re
        
        # 移除时间戳
        message = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', '', message)
        
        # 移除行号信息
        message = re.sub(r'line\s+\d+', 'line X', message)
        message = re.sub(r'第\s*\d+\s*行', '第X行', message)
        
        # 移除具体的超时时间
        message = re.sub(r'\d+ms', 'Xms', message)
        message = re.sub(r'\d+\.\d+s', 'X.Xs', message)
        
        # 移除具体的数值
        message = re.sub(r'\d+', 'X', message)
        
        # 移除多余的空格
        message = re.sub(r'\s+', ' ', message).strip()
        
        return message
    
    def should_log_error(self, error_message: str, error_type: str = None, 
                        selector: str = None) -> bool:
        """判断是否应该记录错误"""
        # 如果功能未启用，直接返回True
        if not self.enabled:
            return True
        
        # 检查是否应该忽略此错误
        if self._should_ignore_error(error_message):
            return False
        
        current_time = time.time()
        
        # 定期清理过期记录
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired_records(current_time)
        
        error_hash = self._generate_error_hash(error_message, error_type, selector)
        
        # 检查是否已被抑制
        if error_hash in self.suppressed_errors:
            return False
        
        # 获取此错误类型的最大计数
        max_count = self._get_max_count_for_error(error_message, error_type)
        
        # 检查是否存在记录
        if error_hash in self.error_records:
            record = self.error_records[error_hash]
            
            # 检查时间窗口
            if current_time - record.first_occurrence > self.time_window:
                # 超出时间窗口，重置记录
                record.first_occurrence = current_time
                record.last_occurrence = current_time
                record.count = 1
                return True
            
            # 在时间窗口内，检查计数
            if record.count >= max_count:
                # 达到最大计数，抑制错误
                self.suppressed_errors.add(error_hash)
                logger.warning(
                    f"错误已被抑制（{max_count}次重复）: "
                    f"{self._truncate_message(error_message)}"
                )
                return False
            
            # 更新记录
            record.update_occurrence()
            return True
        
        # 新错误，创建记录
        self.error_records[error_hash] = ErrorRecord(
            error_hash=error_hash,
            error_message=error_message,
            first_occurrence=current_time,
            last_occurrence=current_time
        )
        return True
    
    def _should_ignore_error(self, error_message: str) -> bool:
        """检查是否应该忽略此错误"""
        for pattern in self.ignore_patterns:
            if re.search(pattern, error_message, re.IGNORECASE):
                logger.debug(f"忽略错误（匹配忽略规则）: {self._truncate_message(error_message)}")
                return True
        return False
    
    def _get_max_count_for_error(self, error_message: str, error_type: str = None) -> int:
        """获取特定错误的最大计数"""
        # 检查自定义模式
        for pattern_config in self.custom_patterns:
            pattern = pattern_config.get('pattern', '')
            if re.search(pattern, error_message, re.IGNORECASE):
                return pattern_config.get('max_count', self.max_same_error_count)
        
        # 检查错误类型配置
        error_types_config = self.config.get('error_types', {})
        
        if error_type:
            # 检查特定错误类型
            type_key = f"{error_type.lower()}_errors"
            if type_key in error_types_config:
                return error_types_config[type_key].get('max_count', self.max_same_error_count)
        
        # 检查错误消息中的关键词
        if 'timeout' in error_message.lower():
            timeout_config = error_types_config.get('timeout_errors', {})
            return timeout_config.get('max_count', self.max_same_error_count)
        
        if 'not found' in error_message.lower() or 'element' in error_message.lower():
            element_config = error_types_config.get('element_not_found_errors', {})
            return element_config.get('max_count', self.max_same_error_count)
        
        if 'assertion' in error_message.lower():
            assertion_config = error_types_config.get('assertion_errors', {})
            return assertion_config.get('max_count', self.max_same_error_count)
        
        return self.max_same_error_count
    
    def _cleanup_expired_records(self, current_time: float):
        """清理过期的错误记录"""
        expired_hashes = []
        
        for error_hash, record in self.error_records.items():
            if current_time - record.last_occurrence > self.time_window * 2:
                expired_hashes.append(error_hash)
        
        for error_hash in expired_hashes:
            del self.error_records[error_hash]
            self.suppressed_errors.discard(error_hash)
        
        self.last_cleanup = current_time
        
        if expired_hashes:
            logger.debug(f"清理了 {len(expired_hashes)} 个过期错误记录")
    
    def _truncate_message(self, message: str, max_length: int = 100) -> str:
        """截断错误消息"""
        if len(message) <= max_length:
            return message
        return message[:max_length] + "..."
    
    def get_error_statistics(self) -> Dict:
        """获取错误统计信息"""
        current_time = time.time()
        
        total_errors = len(self.error_records)
        suppressed_errors = len(self.suppressed_errors)
        
        # 统计最近时间窗口内的错误
        recent_errors = sum(
            1 for record in self.error_records.values()
            if current_time - record.last_occurrence <= self.time_window
        )
        
        # 统计重复错误
        repeated_errors = sum(
            1 for record in self.error_records.values()
            if record.count > 1
        )
        
        return {
            'total_unique_errors': total_errors,
            'suppressed_errors': suppressed_errors,
            'recent_errors': recent_errors,
            'repeated_errors': repeated_errors,
            'time_window_minutes': self.time_window / 60
        }
    
    def reset(self):
        """重置所有错误记录"""
        self.error_records.clear()
        self.suppressed_errors.clear()
        self.last_cleanup = time.time()
        logger.info("错误去重管理器已重置")

# 全局错误去重管理器实例
error_dedup_manager = ErrorDeduplicationManager()