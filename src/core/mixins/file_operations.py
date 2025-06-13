"""文件操作混入类"""
import os
import glob
import time
import allure
from typing import Optional
from utils.logger import logger
from .decorators import handle_page_error
from config.constants import DEFAULT_TIMEOUT


class FileOperationsMixin:
    """文件操作混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @handle_page_error(description="上传文件")
    def upload_file(self, selector: str, file_path: str):
        """上传文件"""
        resolved_path = self.variable_manager.replace_variables_refactored(file_path)
        
        # 检查文件是否存在
        if not os.path.exists(resolved_path):
            raise FileNotFoundError(f"文件不存在: {resolved_path}")
        
        with allure.step(f"上传文件 {resolved_path} 到元素 {selector}"):
            # 获取文件输入元素
            file_input = self._locator(selector)
            
            # 设置文件
            file_input.set_input_files(resolved_path)
            
            logger.info(f"成功上传文件: {resolved_path}")
            
            # 添加文件信息到报告
            allure.attach(
                f"文件路径: {resolved_path}\n文件大小: {os.path.getsize(resolved_path)} bytes",
                name="上传文件信息",
                attachment_type=allure.attachment_type.TEXT
            )

    @handle_page_error(description="上传多个文件")
    def upload_multiple_files(self, selector: str, file_paths: list[str]):
        """上传多个文件"""
        resolved_paths = []
        for file_path in file_paths:
            resolved_path = self.variable_manager.replace_variables_refactored(file_path)
            if not os.path.exists(resolved_path):
                raise FileNotFoundError(f"文件不存在: {resolved_path}")
            resolved_paths.append(resolved_path)
        
        with allure.step(f"上传多个文件到元素 {selector}"):
            # 获取文件输入元素
            file_input = self._locator(selector)
            
            # 设置多个文件
            file_input.set_input_files(resolved_paths)
            
            logger.info(f"成功上传 {len(resolved_paths)} 个文件")
            
            # 添加文件信息到报告
            file_info = "\n".join([
                f"文件 {i+1}: {path} ({os.path.getsize(path)} bytes)"
                for i, path in enumerate(resolved_paths)
            ])
            allure.attach(
                file_info,
                name="上传文件列表",
                attachment_type=allure.attachment_type.TEXT
            )

    @handle_page_error(description="下载文件")
    def download_file(self, selector: str, save_path: Optional[str] = None) -> str:
        """点击下载按钮并获取下载的文件路径"""
        with allure.step(f"下载文件，触发元素: {selector}"):
            with self.page.expect_download() as download_info:
                self.click(selector)

            download = download_info.value
            suggested_filename = download.suggested_filename
            logger.info(f"开始下载文件: {suggested_filename}")

            if save_path:
                # 使用指定路径保存
                resolved_save_path = self.variable_manager.replace_variables_refactored(save_path)
                # 确保目录存在
                os.makedirs(os.path.dirname(resolved_save_path), exist_ok=True)
                download.save_as(resolved_save_path)
                final_path = resolved_save_path
            else:
                # 使用默认路径
                final_path = str(download.path())
            
            logger.info(f"文件下载完成: {final_path}")
            
            # 添加下载信息到报告
            allure.attach(
                f"下载文件: {suggested_filename}\n保存路径: {final_path}",
                name="文件下载信息",
                attachment_type=allure.attachment_type.TEXT
            )
            
            return final_path

    @handle_page_error(description="验证文件下载")
    def verify_download(self, file_pattern: str, timeout: int = DEFAULT_TIMEOUT, download_dir: Optional[str] = None) -> bool:
        """验证文件是否已下载（通过文件名模式匹配）"""
        if download_dir is None:
            # 获取默认下载目录
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            if not os.path.exists(download_dir):
                # 尝试使用项目下载目录作为备用
                download_dir = os.path.join("./downloads", self.page.context.browser.browser_type.name)
                os.makedirs(download_dir, exist_ok=True)
        
        with allure.step(f"验证文件下载: {file_pattern}"):
            logger.debug(f"检查下载目录: {download_dir}")
            start_time = time.time()

            while time.time() - start_time < timeout / 1000:
                # 检查下载目录中是否有匹配的文件
                search_pattern = os.path.join(download_dir, file_pattern)
                matching_files = glob.glob(search_pattern)
                
                if matching_files:
                    found_file = matching_files[0]
                    logger.info(f"找到下载文件: {found_file}")
                    
                    # 添加验证结果到报告
                    allure.attach(
                        f"验证成功\n文件模式: {file_pattern}\n找到文件: {found_file}\n文件大小: {os.path.getsize(found_file)} bytes",
                        name="下载验证结果",
                        attachment_type=allure.attachment_type.TEXT
                    )
                    
                    return True
                
                time.sleep(0.5)

            logger.error(f"未找到下载文件: {file_pattern}")
            
            # 列出下载目录中的所有文件用于调试
            try:
                existing_files = os.listdir(download_dir)
                allure.attach(
                    f"验证失败\n文件模式: {file_pattern}\n下载目录: {download_dir}\n现有文件: {existing_files}",
                    name="下载验证失败信息",
                    attachment_type=allure.attachment_type.TEXT
                )
            except Exception as e:
                logger.warning(f"无法列出下载目录文件: {e}")
            
            return False

    @handle_page_error(description="清理下载文件")
    def cleanup_downloads(self, file_pattern: str = "*", download_dir: Optional[str] = None):
        """清理下载目录中的文件"""
        if download_dir is None:
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        
        with allure.step(f"清理下载文件: {file_pattern}"):
            search_pattern = os.path.join(download_dir, file_pattern)
            matching_files = glob.glob(search_pattern)
            
            cleaned_count = 0
            for file_path in matching_files:
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                    logger.debug(f"删除文件: {file_path}")
                except Exception as e:
                    logger.warning(f"删除文件失败 {file_path}: {e}")
            
            logger.info(f"清理完成，删除了 {cleaned_count} 个文件")
            
            allure.attach(
                f"清理下载文件\n文件模式: {file_pattern}\n删除数量: {cleaned_count}",
                name="文件清理结果",
                attachment_type=allure.attachment_type.TEXT
            )

    @handle_page_error(description="获取文件信息")
    def get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
        resolved_path = self.variable_manager.replace_variables_refactored(file_path)
        
        if not os.path.exists(resolved_path):
            raise FileNotFoundError(f"文件不存在: {resolved_path}")
        
        stat = os.stat(resolved_path)
        file_info = {
            "path": resolved_path,
            "name": os.path.basename(resolved_path),
            "size": stat.st_size,
            "modified_time": stat.st_mtime,
            "created_time": stat.st_ctime,
            "is_file": os.path.isfile(resolved_path),
            "is_dir": os.path.isdir(resolved_path)
        }
        
        logger.debug(f"文件信息: {file_info}")
        return file_info