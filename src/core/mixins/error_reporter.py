"""错误报告器
提供错误统计、分析和报告功能
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from .error_deduplication import error_dedup_manager
from utils.logger import logger


class ErrorReporter:
    """错误报告器"""
    
    def __init__(self, report_dir: str = "reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
        
        # 报告文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.error_report_file = self.report_dir / f"error_report_{timestamp}.json"
        self.summary_report_file = self.report_dir / f"error_summary_{timestamp}.txt"
    
    def generate_error_report(self) -> Dict:
        """生成详细的错误报告"""
        stats = error_dedup_manager.get_error_statistics()
        
        # 获取错误详情
        error_details = []
        for error_hash, record in error_dedup_manager.error_records.items():
            error_details.append({
                'error_hash': error_hash,
                'error_message': record.error_message,
                'first_occurrence': datetime.fromtimestamp(record.first_occurrence).isoformat(),
                'last_occurrence': datetime.fromtimestamp(record.last_occurrence).isoformat(),
                'count': record.count,
                'is_suppressed': error_hash in error_dedup_manager.suppressed_errors
            })
        
        # 按发生次数排序
        error_details.sort(key=lambda x: x['count'], reverse=True)
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'error_details': error_details,
            'configuration': {
                'time_window_seconds': error_dedup_manager.time_window,
                'max_same_error_count': error_dedup_manager.max_same_error_count,
                'cleanup_interval_seconds': error_dedup_manager.cleanup_interval
            }
        }
        
        return report
    
    def save_error_report(self) -> str:
        """保存错误报告到文件"""
        report = self.generate_error_report()
        
        try:
            with open(self.error_report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"错误报告已保存到: {self.error_report_file}")
            return str(self.error_report_file)
        
        except Exception as e:
            logger.error(f"保存错误报告失败: {e}")
            return ""
    
    def generate_summary_report(self) -> str:
        """生成错误摘要报告"""
        report = self.generate_error_report()
        stats = report['statistics']
        error_details = report['error_details']
        
        lines = []
        lines.append("=" * 60)
        lines.append("错误去重效果报告")
        lines.append("=" * 60)
        lines.append(f"报告生成时间: {report['report_timestamp']}")
        lines.append("")
        
        # 统计信息
        lines.append("📊 错误统计信息:")
        lines.append(f"  • 唯一错误类型数量: {stats['total_unique_errors']}")
        lines.append(f"  • 被抑制的错误数量: {stats['suppressed_errors']}")
        lines.append(f"  • 最近{stats['time_window_minutes']:.1f}分钟内的错误: {stats['recent_errors']}")
        lines.append(f"  • 重复发生的错误: {stats['repeated_errors']}")
        lines.append("")
        
        # 去重效果
        if stats['suppressed_errors'] > 0:
            lines.append("✅ 错误去重效果:")
            lines.append(f"  • 成功抑制了 {stats['suppressed_errors']} 种重复错误")
            lines.append(f"  • 减少了大量重复日志记录")
        else:
            lines.append("ℹ️  当前没有被抑制的重复错误")
        lines.append("")
        
        # 配置信息
        config = report['configuration']
        lines.append("⚙️ 去重配置:")
        lines.append(f"  • 时间窗口: {config['time_window_seconds']}秒")
        lines.append(f"  • 最大重复次数: {config['max_same_error_count']}次")
        lines.append(f"  • 清理间隔: {config['cleanup_interval_seconds']}秒")
        lines.append("")
        
        # 高频错误Top 10
        if error_details:
            lines.append("🔥 高频错误 Top 10:")
            for i, error in enumerate(error_details[:10], 1):
                status = "[已抑制]" if error['is_suppressed'] else "[活跃]"
                lines.append(f"  {i:2d}. {status} 发生{error['count']}次")
                lines.append(f"      {self._truncate_message(error['error_message'], 80)}")
                lines.append(f"      首次: {error['first_occurrence'][:19]}")
                lines.append(f"      最近: {error['last_occurrence'][:19]}")
                lines.append("")
        
        # 建议
        lines.append("💡 优化建议:")
        if stats['repeated_errors'] > stats['total_unique_errors'] * 0.5:
            lines.append("  • 检测到大量重复错误，建议检查测试用例或页面元素定位")
        
        if stats['suppressed_errors'] > 10:
            lines.append("  • 抑制的错误较多，可能需要优化错误处理逻辑")
        
        if stats['total_unique_errors'] > 50:
            lines.append("  • 错误类型较多，建议分类分析并优先修复高频错误")
        
        lines.append("  • 定期查看错误报告，持续优化测试稳定性")
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def save_summary_report(self) -> str:
        """保存摘要报告到文件"""
        summary = self.generate_summary_report()
        
        try:
            with open(self.summary_report_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            logger.info(f"错误摘要报告已保存到: {self.summary_report_file}")
            return str(self.summary_report_file)
        
        except Exception as e:
            logger.error(f"保存摘要报告失败: {e}")
            return ""
    
    def print_summary(self):
        """打印摘要报告到控制台"""
        summary = self.generate_summary_report()
        print(summary)
    
    def _truncate_message(self, message: str, max_length: int = 100) -> str:
        """截断消息"""
        if len(message) <= max_length:
            return message
        return message[:max_length] + "..."
    
    def get_error_trends(self, hours: int = 24) -> Dict:
        """获取错误趋势（最近N小时）"""
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)
        
        recent_errors = []
        for record in error_dedup_manager.error_records.values():
            if record.first_occurrence >= cutoff_time:
                recent_errors.append({
                    'timestamp': record.first_occurrence,
                    'message': record.error_message,
                    'count': record.count
                })
        
        # 按时间排序
        recent_errors.sort(key=lambda x: x['timestamp'])
        
        return {
            'time_range_hours': hours,
            'total_new_errors': len(recent_errors),
            'errors': recent_errors
        }


# 创建全局错误报告器实例
error_reporter = ErrorReporter()


def generate_final_error_report():
    """生成最终错误报告（测试结束时调用）"""
    try:
        # 保存详细报告
        report_file = error_reporter.save_error_report()
        
        # 保存摘要报告
        summary_file = error_reporter.save_summary_report()
        
        # 打印摘要到控制台
        error_reporter.print_summary()
        
        return {
            'detailed_report': report_file,
            'summary_report': summary_file
        }
    
    except Exception as e:
        logger.error(f"生成最终错误报告失败: {e}")
        return {}