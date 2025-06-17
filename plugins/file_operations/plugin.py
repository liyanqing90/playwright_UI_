"""文件操作插件实现

提供文件和目录操作的相关功能，包括读取、写入、删除、复制、移动文件等操作。
"""

import csv
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

from src.automation.action_types import StepAction
from src.automation.commands.base_command import Command, CommandFactory
from utils.logger import logger


@dataclass
class FileInfo:
    """文件信息数据类"""

    path: str
    name: str
    size: int
    modified_time: datetime
    is_directory: bool
    extension: str = ""

    @classmethod
    def from_path(cls, file_path: str) -> "FileInfo":
        """从文件路径创建FileInfo对象"""
        path_obj = Path(file_path)
        stat = path_obj.stat()

        return cls(
            path=str(path_obj.absolute()),
            name=path_obj.name,
            size=stat.st_size,
            modified_time=datetime.fromtimestamp(stat.st_mtime),
            is_directory=path_obj.is_dir(),
            extension=path_obj.suffix if not path_obj.is_dir() else "",
        )


class FileOperationsPlugin:
    """文件操作插件"""

    def __init__(self):
        self.name = "file_operations"
        self.version = "1.0.0"
        self.description = "文件和目录操作插件"
        self.supported_formats = {
            "text": [".txt", ".log", ".md", ".rst"],
            "json": [".json"],
            "yaml": [".yaml", ".yml"],
            "csv": [".csv"],
            "xml": [".xml"],
            "binary": [".bin", ".dat"],
        }
        self.encoding = "utf-8"
        self.backup_enabled = True
        self.max_file_size = 100 * 1024 * 1024  # 100MB

        # 注册命令
        self._register_commands()

    def _register_commands(self):
        """注册文件操作命令"""
        commands = {
            "READ_FILE": ReadFileCommand,
            "WRITE_FILE": WriteFileCommand,
            "DELETE_FILE": DeleteFileCommand,
            "COPY_FILE": CopyFileCommand,
            "MOVE_FILE": MoveFileCommand,
            "CREATE_DIRECTORY": CreateDirectoryCommand,
            "LIST_DIRECTORY": ListDirectoryCommand,
            "FILE_EXISTS": FileExistsCommand,
            "GET_FILE_INFO": GetFileInfoCommand,
            "BACKUP_FILE": BackupFileCommand,
            "RESTORE_FILE": RestoreFileCommand,
            "COMPRESS_FILE": CompressFileCommand,
            "EXTRACT_FILE": ExtractFileCommand,
            "SEARCH_FILES": SearchFilesCommand,
            "BATCH_OPERATION": BatchOperationCommand,
        }

        for action_name, command_class in commands.items():
            try:
                # 动态创建StepAction属性
                if not hasattr(StepAction, action_name):
                    setattr(
                        StepAction,
                        action_name,
                        [action_name.lower(), action_name.lower().replace("_", " ")],
                    )

                action = getattr(StepAction, action_name)
                CommandFactory.register(action)(command_class)
                logger.info(f"已注册文件操作命令: {action_name}")
            except Exception as e:
                logger.error(f"注册文件操作命令失败 {action_name}: {e}")

    def validate_file_path(self, file_path: str, check_exists: bool = False) -> str:
        """验证文件路径"""
        if not file_path:
            raise ValueError("文件路径不能为空")

        # 转换为绝对路径
        abs_path = os.path.abspath(file_path)

        if check_exists and not os.path.exists(abs_path):
            raise FileNotFoundError(f"文件不存在: {abs_path}")

        return abs_path

    def check_file_size(self, file_path: str) -> bool:
        """检查文件大小是否超过限制"""
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            return size <= self.max_file_size
        return True

    def create_backup(self, file_path: str) -> Optional[str]:
        """创建文件备份"""
        if not self.backup_enabled or not os.path.exists(file_path):
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.backup_{timestamp}"
            shutil.copy2(file_path, backup_path)
            logger.info(f"已创建备份: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return None

    def detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        try:
            import chardet

            with open(file_path, "rb") as f:
                raw_data = f.read(10000)  # 读取前10KB检测编码
                result = chardet.detect(raw_data)
                return result.get("encoding", "utf-8") or "utf-8"
        except ImportError:
            return self.encoding
        except Exception:
            return self.encoding


@CommandFactory.register(StepAction.READ_FILE)
class ReadFileCommand(Command):
    """读取文件命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        file_path = step.get("file_path", value)
        encoding = step.get("encoding", "utf-8")
        format_type = step.get("format", "text")
        variable_name = step.get("variable_name")

        plugin = FileOperationsPlugin()
        abs_path = plugin.validate_file_path(file_path, check_exists=True)

        try:
            # 检测编码
            if encoding == "auto":
                encoding = plugin.detect_encoding(abs_path)

            # 根据格式读取文件
            if format_type == "json":
                with open(abs_path, "r", encoding=encoding) as f:
                    content = json.load(f)
            elif format_type == "yaml":
                with open(abs_path, "r", encoding=encoding) as f:
                    content = yaml.safe_load(f)
            elif format_type == "csv":
                content = []
                with open(abs_path, "r", encoding=encoding, newline="") as f:
                    reader = csv.DictReader(f)
                    content = list(reader)
            elif format_type == "binary":
                with open(abs_path, "rb") as f:
                    content = f.read()
            else:  # text format
                with open(abs_path, "r", encoding=encoding) as f:
                    content = f.read()

            # 存储到变量
            if variable_name:
                ui_helper.store_variable(
                    variable_name, content, step.get("scope", "global")
                )

            logger.info(f"成功读取文件: {abs_path}")

        except Exception as e:
            logger.error(f"读取文件失败 {abs_path}: {e}")
            raise


@CommandFactory.register(StepAction.WRITE_FILE)
class WriteFileCommand(Command):
    """写入文件命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        file_path = step.get("file_path", selector)
        content = step.get("content", value)
        encoding = step.get("encoding", "utf-8")
        format_type = step.get("format", "text")
        mode = step.get("mode", "w")  # w: 覆盖, a: 追加
        create_dirs = step.get("create_dirs", True)
        backup = step.get("backup", True)

        plugin = FileOperationsPlugin()
        abs_path = plugin.validate_file_path(file_path)

        try:
            # 创建目录
            if create_dirs:
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            # 创建备份
            if backup and os.path.exists(abs_path):
                plugin.create_backup(abs_path)

            # 根据格式写入文件
            if format_type == "json":
                with open(abs_path, mode, encoding=encoding) as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            elif format_type == "yaml":
                with open(abs_path, mode, encoding=encoding) as f:
                    yaml.dump(content, f, default_flow_style=False, allow_unicode=True)
            elif format_type == "csv":
                with open(abs_path, mode, encoding=encoding, newline="") as f:
                    if isinstance(content, list) and content:
                        fieldnames = (
                            content[0].keys() if isinstance(content[0], dict) else None
                        )
                        if fieldnames:
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            if mode == "w":
                                writer.writeheader()
                            writer.writerows(content)
                        else:
                            writer = csv.writer(f)
                            writer.writerows(content)
            elif format_type == "binary":
                with open(abs_path, "wb") as f:
                    f.write(content)
            else:  # text format
                with open(abs_path, mode, encoding=encoding) as f:
                    f.write(str(content))

            logger.info(f"成功写入文件: {abs_path}")

        except Exception as e:
            logger.error(f"写入文件失败 {abs_path}: {e}")
            raise


@CommandFactory.register(StepAction.DELETE_FILE)
class DeleteFileCommand(Command):
    """删除文件命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        file_path = step.get("file_path", value)
        backup = step.get("backup", True)
        force = step.get("force", False)

        plugin = FileOperationsPlugin()
        abs_path = plugin.validate_file_path(file_path, check_exists=True)

        try:
            # 创建备份
            if backup:
                plugin.create_backup(abs_path)

            # 删除文件或目录
            if os.path.isfile(abs_path):
                os.remove(abs_path)
            elif os.path.isdir(abs_path):
                if force:
                    shutil.rmtree(abs_path)
                else:
                    os.rmdir(abs_path)  # 只删除空目录

            logger.info(f"成功删除: {abs_path}")

        except Exception as e:
            logger.error(f"删除失败 {abs_path}: {e}")
            raise


@CommandFactory.register(StepAction.COPY_FILE)
class CopyFileCommand(Command):
    """复制文件命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        source_path = step.get("source_path", selector)
        dest_path = step.get("dest_path", value)
        overwrite = step.get("overwrite", False)
        preserve_metadata = step.get("preserve_metadata", True)

        plugin = FileOperationsPlugin()
        abs_source = plugin.validate_file_path(source_path, check_exists=True)
        abs_dest = plugin.validate_file_path(dest_path)

        try:
            # 检查目标是否存在
            if os.path.exists(abs_dest) and not overwrite:
                raise FileExistsError(f"目标文件已存在: {abs_dest}")

            # 创建目标目录
            os.makedirs(os.path.dirname(abs_dest), exist_ok=True)

            # 复制文件或目录
            if os.path.isfile(abs_source):
                if preserve_metadata:
                    shutil.copy2(abs_source, abs_dest)
                else:
                    shutil.copy(abs_source, abs_dest)
            elif os.path.isdir(abs_source):
                shutil.copytree(abs_source, abs_dest, dirs_exist_ok=overwrite)

            logger.info(f"成功复制: {abs_source} -> {abs_dest}")

        except Exception as e:
            logger.error(f"复制失败 {abs_source} -> {abs_dest}: {e}")
            raise


@CommandFactory.register(StepAction.MOVE_FILE)
class MoveFileCommand(Command):
    """移动文件命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        source_path = step.get("source_path", selector)
        dest_path = step.get("dest_path", value)
        overwrite = step.get("overwrite", False)

        plugin = FileOperationsPlugin()
        abs_source = plugin.validate_file_path(source_path, check_exists=True)
        abs_dest = plugin.validate_file_path(dest_path)

        try:
            # 检查目标是否存在
            if os.path.exists(abs_dest) and not overwrite:
                raise FileExistsError(f"目标文件已存在: {abs_dest}")

            # 创建目标目录
            os.makedirs(os.path.dirname(abs_dest), exist_ok=True)

            # 移动文件或目录
            shutil.move(abs_source, abs_dest)

            logger.info(f"成功移动: {abs_source} -> {abs_dest}")

        except Exception as e:
            logger.error(f"移动失败 {abs_source} -> {abs_dest}: {e}")
            raise


@CommandFactory.register(StepAction.CREATE_DIRECTORY)
class CreateDirectoryCommand(Command):
    """创建目录命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        dir_path = step.get("dir_path", value)
        parents = step.get("parents", True)
        exist_ok = step.get("exist_ok", True)

        plugin = FileOperationsPlugin()
        abs_path = plugin.validate_file_path(dir_path)

        try:
            if parents:
                os.makedirs(abs_path, exist_ok=exist_ok)
            else:
                os.mkdir(abs_path)

            logger.info(f"成功创建目录: {abs_path}")

        except Exception as e:
            logger.error(f"创建目录失败 {abs_path}: {e}")
            raise


@CommandFactory.register(StepAction.LIST_DIRECTORY)
class ListDirectoryCommand(Command):
    """列出目录内容命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        dir_path = step.get("dir_path", value)
        pattern = step.get("pattern", "*")
        recursive = step.get("recursive", False)
        include_hidden = step.get("include_hidden", False)
        variable_name = step.get("variable_name")

        plugin = FileOperationsPlugin()
        abs_path = plugin.validate_file_path(dir_path, check_exists=True)

        try:
            import glob

            if recursive:
                search_pattern = os.path.join(abs_path, "**", pattern)
                files = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = os.path.join(abs_path, pattern)
                files = glob.glob(search_pattern)

            # 过滤隐藏文件
            if not include_hidden:
                files = [f for f in files if not os.path.basename(f).startswith(".")]

            # 获取文件信息
            file_list = []
            for file_path in files:
                try:
                    file_info = FileInfo.from_path(file_path)
                    file_list.append(
                        {
                            "path": file_info.path,
                            "name": file_info.name,
                            "size": file_info.size,
                            "modified_time": file_info.modified_time.isoformat(),
                            "is_directory": file_info.is_directory,
                            "extension": file_info.extension,
                        }
                    )
                except Exception as e:
                    logger.warning(f"获取文件信息失败 {file_path}: {e}")

            # 存储到变量
            if variable_name:
                ui_helper.store_variable(
                    variable_name, file_list, step.get("scope", "global")
                )

            logger.info(f"成功列出目录内容: {abs_path}, 找到 {len(file_list)} 个项目")

        except Exception as e:
            logger.error(f"列出目录内容失败 {abs_path}: {e}")
            raise


@CommandFactory.register(StepAction.FILE_EXISTS)
class FileExistsCommand(Command):
    """检查文件是否存在命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        file_path = step.get("file_path", value)
        variable_name = step.get("variable_name")

        plugin = FileOperationsPlugin()
        abs_path = plugin.validate_file_path(file_path)

        exists = os.path.exists(abs_path)

        # 存储到变量
        if variable_name:
            ui_helper.store_variable(variable_name, exists, step.get("scope", "global"))

        logger.info(f"文件存在检查: {abs_path} = {exists}")


@CommandFactory.register(StepAction.GET_FILE_INFO)
class GetFileInfoCommand(Command):
    """获取文件信息命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        file_path = step.get("file_path", value)
        variable_name = step.get("variable_name")

        plugin = FileOperationsPlugin()
        abs_path = plugin.validate_file_path(file_path, check_exists=True)

        try:
            file_info = FileInfo.from_path(abs_path)
            info_dict = {
                "path": file_info.path,
                "name": file_info.name,
                "size": file_info.size,
                "modified_time": file_info.modified_time.isoformat(),
                "is_directory": file_info.is_directory,
                "extension": file_info.extension,
            }

            # 存储到变量
            if variable_name:
                ui_helper.store_variable(
                    variable_name, info_dict, step.get("scope", "global")
                )

            logger.info(f"成功获取文件信息: {abs_path}")

        except Exception as e:
            logger.error(f"获取文件信息失败 {abs_path}: {e}")
            raise


@CommandFactory.register(StepAction.BACKUP_FILE)
class BackupFileCommand(Command):
    """备份文件命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        file_path = step.get("file_path", value)
        backup_dir = step.get("backup_dir")
        variable_name = step.get("variable_name")

        plugin = FileOperationsPlugin()
        abs_path = plugin.validate_file_path(file_path, check_exists=True)

        try:
            if backup_dir:
                # 指定备份目录
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.basename(abs_path)
                backup_path = os.path.join(backup_dir, f"{filename}.backup_{timestamp}")
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(abs_path, backup_path)
            else:
                # 默认备份
                backup_path = plugin.create_backup(abs_path)

            # 存储备份路径到变量
            if variable_name and backup_path:
                ui_helper.store_variable(
                    variable_name, backup_path, step.get("scope", "global")
                )

            logger.info(f"成功备份文件: {abs_path} -> {backup_path}")

        except Exception as e:
            logger.error(f"备份文件失败 {abs_path}: {e}")
            raise


@CommandFactory.register(StepAction.RESTORE_FILE)
class RestoreFileCommand(Command):
    """恢复文件命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        backup_path = step.get("backup_path", value)
        original_path = step.get("original_path")
        overwrite = step.get("overwrite", False)

        plugin = FileOperationsPlugin()
        abs_backup = plugin.validate_file_path(backup_path, check_exists=True)

        try:
            # 确定原始文件路径
            if not original_path:
                # 从备份文件名推断原始路径
                if ".backup_" in abs_backup:
                    original_path = abs_backup.split(".backup_")[0]
                else:
                    raise ValueError("无法确定原始文件路径")

            abs_original = plugin.validate_file_path(original_path)

            # 检查是否覆盖
            if os.path.exists(abs_original) and not overwrite:
                raise FileExistsError(f"原始文件已存在: {abs_original}")

            # 恢复文件
            shutil.copy2(abs_backup, abs_original)

            logger.info(f"成功恢复文件: {abs_backup} -> {abs_original}")

        except Exception as e:
            logger.error(f"恢复文件失败 {abs_backup}: {e}")
            raise


@CommandFactory.register(StepAction.COMPRESS_FILE)
class CompressFileCommand(Command):
    """压缩文件命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        source_path = step.get("source_path", value)
        archive_path = step.get("archive_path")
        format_type = step.get("format", "zip")  # zip, tar, gztar, bztar, xztar
        variable_name = step.get("variable_name")

        plugin = FileOperationsPlugin()
        abs_source = plugin.validate_file_path(source_path, check_exists=True)

        try:
            # 确定压缩文件路径
            if not archive_path:
                archive_path = f"{abs_source}.{format_type}"

            abs_archive = plugin.validate_file_path(archive_path)

            # 创建压缩文件
            if format_type == "zip":
                import zipfile

                with zipfile.ZipFile(abs_archive, "w", zipfile.ZIP_DEFLATED) as zipf:
                    if os.path.isfile(abs_source):
                        zipf.write(abs_source, os.path.basename(abs_source))
                    else:
                        for root, dirs, files in os.walk(abs_source):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, abs_source)
                                zipf.write(file_path, arcname)
            else:
                # 使用shutil创建tar格式压缩文件
                base_name = abs_archive.rsplit(".", 1)[0]
                shutil.make_archive(
                    base_name,
                    format_type,
                    os.path.dirname(abs_source),
                    os.path.basename(abs_source),
                )

            # 存储压缩文件路径到变量
            if variable_name:
                ui_helper.store_variable(
                    variable_name, abs_archive, step.get("scope", "global")
                )

            logger.info(f"成功压缩文件: {abs_source} -> {abs_archive}")

        except Exception as e:
            logger.error(f"压缩文件失败 {abs_source}: {e}")
            raise


@CommandFactory.register(StepAction.EXTRACT_FILE)
class ExtractFileCommand(Command):
    """解压文件命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        archive_path = step.get("archive_path", value)
        extract_path = step.get("extract_path")
        variable_name = step.get("variable_name")

        plugin = FileOperationsPlugin()
        abs_archive = plugin.validate_file_path(archive_path, check_exists=True)

        try:
            # 确定解压路径
            if not extract_path:
                extract_path = os.path.dirname(abs_archive)

            abs_extract = plugin.validate_file_path(extract_path)
            os.makedirs(abs_extract, exist_ok=True)

            # 解压文件
            if abs_archive.endswith(".zip"):
                import zipfile

                with zipfile.ZipFile(abs_archive, "r") as zipf:
                    zipf.extractall(abs_extract)
            else:
                # 使用shutil解压tar格式文件
                shutil.unpack_archive(abs_archive, abs_extract)

            # 存储解压路径到变量
            if variable_name:
                ui_helper.store_variable(
                    variable_name, abs_extract, step.get("scope", "global")
                )

            logger.info(f"成功解压文件: {abs_archive} -> {abs_extract}")

        except Exception as e:
            logger.error(f"解压文件失败 {abs_archive}: {e}")
            raise


@CommandFactory.register(StepAction.SEARCH_FILES)
class SearchFilesCommand(Command):
    """搜索文件命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        search_path = step.get("search_path", value)
        pattern = step.get("pattern", "*")
        content_pattern = step.get("content_pattern")
        recursive = step.get("recursive", True)
        case_sensitive = step.get("case_sensitive", False)
        variable_name = step.get("variable_name")

        plugin = FileOperationsPlugin()
        abs_path = plugin.validate_file_path(search_path, check_exists=True)

        try:
            import glob
            import re

            # 搜索文件
            if recursive:
                search_pattern = os.path.join(abs_path, "**", pattern)
                files = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = os.path.join(abs_path, pattern)
                files = glob.glob(search_pattern)

            # 过滤文件（只保留文件，不包括目录）
            files = [f for f in files if os.path.isfile(f)]

            # 内容搜索
            if content_pattern:
                matching_files = []
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern_re = re.compile(content_pattern, flags)

                for file_path in files:
                    try:
                        encoding = plugin.detect_encoding(file_path)
                        with open(file_path, "r", encoding=encoding) as f:
                            content = f.read()
                            if pattern_re.search(content):
                                matching_files.append(file_path)
                    except Exception as e:
                        logger.warning(f"搜索文件内容失败 {file_path}: {e}")

                files = matching_files

            # 获取文件信息
            result = []
            for file_path in files:
                try:
                    file_info = FileInfo.from_path(file_path)
                    result.append(
                        {
                            "path": file_info.path,
                            "name": file_info.name,
                            "size": file_info.size,
                            "modified_time": file_info.modified_time.isoformat(),
                            "extension": file_info.extension,
                        }
                    )
                except Exception as e:
                    logger.warning(f"获取文件信息失败 {file_path}: {e}")

            # 存储到变量
            if variable_name:
                ui_helper.store_variable(
                    variable_name, result, step.get("scope", "global")
                )

            logger.info(f"搜索完成: 在 {abs_path} 中找到 {len(result)} 个匹配文件")

        except Exception as e:
            logger.error(f"搜索文件失败 {abs_path}: {e}")
            raise


@CommandFactory.register(StepAction.BATCH_OPERATION)
class BatchOperationCommand(Command):
    """批量操作命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        operations = step.get("operations", [])
        continue_on_error = step.get("continue_on_error", False)
        variable_name = step.get("variable_name")

        results = []

        try:
            for i, operation in enumerate(operations):
                try:
                    # 执行单个操作
                    op_type = operation.get("type")
                    op_params = operation.get("params", {})

                    # 根据操作类型创建对应的命令
                    command_map = {
                        "read": ReadFileCommand(),
                        "write": WriteFileCommand(),
                        "delete": DeleteFileCommand(),
                        "copy": CopyFileCommand(),
                        "move": MoveFileCommand(),
                        "backup": BackupFileCommand(),
                    }

                    if op_type in command_map:
                        command = command_map[op_type]
                        command.execute(ui_helper, "", "", op_params)
                        results.append(
                            {"index": i, "status": "success", "operation": operation}
                        )
                    else:
                        raise ValueError(f"不支持的操作类型: {op_type}")

                except Exception as e:
                    error_info = {
                        "index": i,
                        "status": "error",
                        "operation": operation,
                        "error": str(e),
                    }
                    results.append(error_info)

                    if not continue_on_error:
                        raise
                    else:
                        logger.warning(f"批量操作第 {i+1} 项失败: {e}")

            # 存储结果到变量
            if variable_name:
                ui_helper.store_variable(
                    variable_name, results, step.get("scope", "global")
                )

            success_count = len([r for r in results if r["status"] == "success"])
            error_count = len([r for r in results if r["status"] == "error"])

            logger.info(f"批量操作完成: 成功 {success_count} 项, 失败 {error_count} 项")

        except Exception as e:
            logger.error(f"批量操作失败: {e}")
            raise


def plugin_init():
    """插件初始化函数"""
    plugin = FileOperationsPlugin()
    logger.info(f"文件操作插件已初始化: {plugin.name} v{plugin.version}")
    return plugin


def plugin_cleanup():
    """插件清理函数"""
    logger.info("文件操作插件已清理")
