"""存储命令插件实现

提供全面的数据存储和状态管理功能。
"""

import json
import pickle
import sqlite3
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.automation.action_types import StepAction
from src.automation.commands.base_command import Command, CommandFactory
from src.automation.expression_evaluator import evaluate_math_expression
from utils.logger import logger


class StorageScope(Enum):
    """存储作用域"""

    GLOBAL = "global"
    SESSION = "session"
    TEST = "test"
    STEP = "step"
    TEMPORARY = "temporary"


class DataType(Enum):
    """数据类型"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    JSON = "json"
    BINARY = "binary"
    OBJECT = "object"


class SerializationFormat(Enum):
    """序列化格式"""

    JSON = "json"
    PICKLE = "pickle"
    STRING = "string"
    BINARY = "binary"


@dataclass
class StorageEntry:
    """存储条目"""

    key: str
    value: Any
    data_type: DataType
    scope: StorageScope
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
        data["data_type"] = self.data_type.value
        data["scope"] = self.scope.value
        return data


class StorageVariableManager:
    """存储插件专用的变量管理器"""

    def __init__(self):
        self.variables: Dict[str, StorageEntry] = {}
        self.scoped_variables: Dict[StorageScope, Dict[str, StorageEntry]] = {
            scope: {} for scope in StorageScope
        }
        self.lock = threading.RLock()
        self.listeners: List[callable] = []

    def set_variable(
        self,
        key: str,
        value: Any,
        scope: Union[str, StorageScope] = StorageScope.GLOBAL,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """设置变量"""
        if isinstance(scope, str):
            scope = StorageScope(scope)

        data_type = self._detect_data_type(value)
        now = datetime.now()
        expires_at = now + timedelta(seconds=ttl) if ttl else None

        entry = StorageEntry(
            key=key,
            value=value,
            data_type=data_type,
            scope=scope,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        with self.lock:
            self.scoped_variables[scope][key] = entry
            self.variables[f"{scope.value}:{key}"] = entry

        self._notify_listeners("set", key, value, scope)
        logger.debug(f"设置变量: {key}={value} (scope={scope.value}, ttl={ttl})")

    def get_variable(
        self,
        key: str,
        scope: Union[str, StorageScope] = StorageScope.GLOBAL,
        default: Any = None,
    ) -> Any:
        """获取变量"""
        if isinstance(scope, str):
            scope = StorageScope(scope)

        with self.lock:
            entry = self.scoped_variables[scope].get(key)
            if entry and not entry.is_expired():
                return entry.value
            elif entry and entry.is_expired():
                # 清理过期变量
                del self.scoped_variables[scope][key]
                del self.variables[f"{scope.value}:{key}"]

        return default

    def delete_variable(
        self, key: str, scope: Union[str, StorageScope] = StorageScope.GLOBAL
    ) -> bool:
        """删除变量"""
        if isinstance(scope, str):
            scope = StorageScope(scope)

        with self.lock:
            if key in self.scoped_variables[scope]:
                del self.scoped_variables[scope][key]
                del self.variables[f"{scope.value}:{key}"]
                self._notify_listeners("delete", key, None, scope)
                logger.debug(f"删除变量: {key} (scope={scope.value})")
                return True
        return False

    def clear_scope(self, scope: Union[str, StorageScope]) -> None:
        """清空作用域"""
        if isinstance(scope, str):
            scope = StorageScope(scope)

        with self.lock:
            keys_to_remove = list(self.scoped_variables[scope].keys())
            for key in keys_to_remove:
                del self.variables[f"{scope.value}:{key}"]
            self.scoped_variables[scope].clear()

        logger.debug(f"清空作用域: {scope.value}")

    def list_variables(
        self, scope: Optional[Union[str, StorageScope]] = None
    ) -> Dict[str, Any]:
        """列出变量"""
        if scope is None:
            return {
                key: entry.value
                for key, entry in self.variables.items()
                if not entry.is_expired()
            }

        if isinstance(scope, str):
            scope = StorageScope(scope)

        return {
            key: entry.value
            for key, entry in self.scoped_variables[scope].items()
            if not entry.is_expired()
        }

    def cleanup_expired(self) -> int:
        """清理过期变量"""
        count = 0
        with self.lock:
            for scope in StorageScope:
                expired_keys = [
                    key
                    for key, entry in self.scoped_variables[scope].items()
                    if entry.is_expired()
                ]
                for key in expired_keys:
                    del self.scoped_variables[scope][key]
                    del self.variables[f"{scope.value}:{key}"]
                    count += 1

        if count > 0:
            logger.debug(f"清理了 {count} 个过期变量")
        return count

    def add_listener(self, listener: callable) -> None:
        """添加变量变化监听器"""
        self.listeners.append(listener)

    def remove_listener(self, listener: callable) -> None:
        """移除变量变化监听器"""
        if listener in self.listeners:
            self.listeners.remove(listener)

    def _detect_data_type(self, value: Any) -> DataType:
        """检测数据类型"""
        if isinstance(value, str):
            return DataType.STRING
        elif isinstance(value, int):
            return DataType.INTEGER
        elif isinstance(value, float):
            return DataType.FLOAT
        elif isinstance(value, bool):
            return DataType.BOOLEAN
        elif isinstance(value, list):
            return DataType.LIST
        elif isinstance(value, dict):
            return DataType.DICT
        elif isinstance(value, bytes):
            return DataType.BINARY
        else:
            return DataType.OBJECT

    def _notify_listeners(
        self, action: str, key: str, value: Any, scope: StorageScope
    ) -> None:
        """通知监听器"""
        for listener in self.listeners:
            try:
                listener(action, key, value, scope)
            except Exception as e:
                logger.error(f"变量监听器错误: {e}")


class CacheManager:
    """缓存管理器"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, StorageEntry] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        ttl = ttl or self.default_ttl
        now = datetime.now()
        expires_at = now + timedelta(seconds=ttl)

        entry = StorageEntry(
            key=key,
            value=value,
            data_type=self._detect_data_type(value),
            scope=StorageScope.TEMPORARY,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
        )

        with self.lock:
            # 检查缓存大小限制
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()

            self.cache[key] = entry
            self.access_times[key] = time.time()

        logger.debug(f"设置缓存: {key} (ttl={ttl}s)")

    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存"""
        with self.lock:
            entry = self.cache.get(key)
            if entry and not entry.is_expired():
                self.access_times[key] = time.time()
                return entry.value
            elif entry and entry.is_expired():
                # 清理过期缓存
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]

        return default

    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
                logger.debug(f"删除缓存: {key}")
                return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
        logger.debug("清空缓存")

    def cleanup_expired(self) -> int:
        """清理过期缓存"""
        count = 0
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items() if entry.is_expired()
            ]
            for key in expired_keys:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
                count += 1

        if count > 0:
            logger.debug(f"清理了 {count} 个过期缓存")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            total = len(self.cache)
            expired = sum(1 for entry in self.cache.values() if entry.is_expired())
            active = total - expired

        return {
            "total_entries": total,
            "active_entries": active,
            "expired_entries": expired,
            "max_size": self.max_size,
            "usage_ratio": active / self.max_size if self.max_size > 0 else 0,
        }

    def _evict_lru(self) -> None:
        """LRU淘汰策略"""
        if not self.access_times:
            return

        # 找到最久未访问的键
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[lru_key]
        del self.access_times[lru_key]
        logger.debug(f"LRU淘汰缓存: {lru_key}")

    def _detect_data_type(self, value: Any) -> DataType:
        """检测数据类型"""
        if isinstance(value, str):
            return DataType.STRING
        elif isinstance(value, int):
            return DataType.INTEGER
        elif isinstance(value, float):
            return DataType.FLOAT
        elif isinstance(value, bool):
            return DataType.BOOLEAN
        elif isinstance(value, list):
            return DataType.LIST
        elif isinstance(value, dict):
            return DataType.DICT
        elif isinstance(value, bytes):
            return DataType.BINARY
        else:
            return DataType.OBJECT


class PersistenceManager:
    """持久化管理器"""

    def __init__(self, storage_path: str = "data/storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_path / "storage.db"
        self._init_database()

    def _init_database(self) -> None:
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS storage_entries
                (
                    id
                    INTEGER
                    PRIMARY
                    KEY
                    AUTOINCREMENT,
                    key
                    TEXT
                    NOT
                    NULL,
                    value
                    TEXT
                    NOT
                    NULL,
                    data_type
                    TEXT
                    NOT
                    NULL,
                    scope
                    TEXT
                    NOT
                    NULL,
                    format
                    TEXT
                    NOT
                    NULL,
                    created_at
                    TEXT
                    NOT
                    NULL,
                    updated_at
                    TEXT
                    NOT
                    NULL,
                    expires_at
                    TEXT,
                    metadata
                    TEXT,
                    UNIQUE
                (
                    key,
                    scope
                )
                    )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_key_scope ON storage_entries(key, scope)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_expires_at ON storage_entries(expires_at)
                """
            )

    def save(
        self,
        key: str,
        value: Any,
        scope: StorageScope = StorageScope.GLOBAL,
        ttl: Optional[int] = None,
        format: SerializationFormat = SerializationFormat.JSON,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """保存数据"""
        serialized_value = self._serialize(value, format)
        data_type = self._detect_data_type(value)
        now = datetime.now()
        expires_at = now + timedelta(seconds=ttl) if ttl else None

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO storage_entries 
                (key, value, data_type, scope, format, created_at, updated_at, expires_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    key,
                    serialized_value,
                    data_type.value,
                    scope.value,
                    format.value,
                    now.isoformat(),
                    now.isoformat(),
                    expires_at.isoformat() if expires_at else None,
                    json.dumps(metadata) if metadata else None,
                ),
            )

        logger.debug(f"持久化保存: {key} (scope={scope.value}, format={format.value})")

    def load(
        self, key: str, scope: StorageScope = StorageScope.GLOBAL, default: Any = None
    ) -> Any:
        """加载数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT value, data_type, format, expires_at
                FROM storage_entries
                WHERE key = ? AND scope = ?
                """,
                (key, scope.value),
            )
            row = cursor.fetchone()

            if row:
                value, data_type, format_str, expires_at = row

                # 检查是否过期
                if expires_at:
                    expires_dt = datetime.fromisoformat(expires_at)
                    if datetime.now() > expires_dt:
                        # 删除过期数据
                        conn.execute(
                            """
                            DELETE
                            FROM storage_entries
                            WHERE key = ? AND scope = ?
                            """,
                            (key, scope.value),
                        )
                        return default

                # 反序列化数据
                format_enum = SerializationFormat(format_str)
                return self._deserialize(value, format_enum)

        return default

    def delete(self, key: str, scope: StorageScope = StorageScope.GLOBAL) -> bool:
        """删除数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE
                FROM storage_entries
                WHERE key = ? AND scope = ?
                """,
                (key, scope.value),
            )

            if cursor.rowcount > 0:
                logger.debug(f"持久化删除: {key} (scope={scope.value})")
                return True
        return False

    def list_keys(self, scope: Optional[StorageScope] = None) -> List[str]:
        """列出键"""
        with sqlite3.connect(self.db_path) as conn:
            if scope:
                cursor = conn.execute(
                    """
                    SELECT key
                    FROM storage_entries
                    WHERE scope = ?
                      AND
                        (expires_at IS NULL
                       OR expires_at
                        > ?)
                    """,
                    (scope.value, datetime.now().isoformat()),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT key
                    FROM storage_entries
                    WHERE
                        (expires_at IS NULL
                       OR expires_at
                        > ?)
                    """,
                    (datetime.now().isoformat(),),
                )

            return [row[0] for row in cursor.fetchall()]

    def cleanup_expired(self) -> int:
        """清理过期数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE
                FROM storage_entries
                WHERE expires_at IS NOT NULL
                  AND expires_at <= ?
                """,
                (datetime.now().isoformat(),),
            )

            count = cursor.rowcount
            if count > 0:
                logger.debug(f"清理了 {count} 个过期持久化数据")
            return count

    def export_data(self, file_path: str, scope: Optional[StorageScope] = None) -> None:
        """导出数据"""
        data = []
        with sqlite3.connect(self.db_path) as conn:
            if scope:
                cursor = conn.execute(
                    """
                    SELECT *
                    FROM storage_entries
                    WHERE scope = ?
                    """,
                    (scope.value,),
                )
            else:
                cursor = conn.execute("SELECT * FROM storage_entries")

            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                data.append(dict(zip(columns, row)))

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"导出数据到: {file_path} ({len(data)} 条记录)")

    def import_data(self, file_path: str) -> int:
        """导入数据"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        with sqlite3.connect(self.db_path) as conn:
            for entry in data:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO storage_entries 
                    (key, value, data_type, scope, format, created_at, updated_at, expires_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        entry["key"],
                        entry["value"],
                        entry["data_type"],
                        entry["scope"],
                        entry["format"],
                        entry["created_at"],
                        entry["updated_at"],
                        entry.get("expires_at"),
                        entry.get("metadata"),
                    ),
                )
                count += 1

        logger.info(f"导入数据从: {file_path} ({count} 条记录)")
        return count

    def _serialize(self, value: Any, format: SerializationFormat) -> str:
        """序列化数据"""
        if format == SerializationFormat.JSON:
            return json.dumps(value, ensure_ascii=False)
        elif format == SerializationFormat.PICKLE:
            import base64

            return base64.b64encode(pickle.dumps(value)).decode("utf-8")
        elif format == SerializationFormat.STRING:
            return str(value)
        elif format == SerializationFormat.BINARY:
            import base64

            if isinstance(value, bytes):
                return base64.b64encode(value).decode("utf-8")
            else:
                return base64.b64encode(str(value).encode("utf-8")).decode("utf-8")
        else:
            return json.dumps(value, ensure_ascii=False)

    def _deserialize(self, value: str, format: SerializationFormat) -> Any:
        """反序列化数据"""
        if format == SerializationFormat.JSON:
            return json.loads(value)
        elif format == SerializationFormat.PICKLE:
            import base64

            return pickle.loads(base64.b64decode(value.encode("utf-8")))
        elif format == SerializationFormat.STRING:
            return value
        elif format == SerializationFormat.BINARY:
            import base64

            return base64.b64decode(value.encode("utf-8"))
        else:
            return json.loads(value)

    def _detect_data_type(self, value: Any) -> DataType:
        """检测数据类型"""
        if isinstance(value, str):
            return DataType.STRING
        elif isinstance(value, int):
            return DataType.INTEGER
        elif isinstance(value, float):
            return DataType.FLOAT
        elif isinstance(value, bool):
            return DataType.BOOLEAN
        elif isinstance(value, list):
            return DataType.LIST
        elif isinstance(value, dict):
            return DataType.DICT
        elif isinstance(value, bytes):
            return DataType.BINARY
        else:
            return DataType.OBJECT


class StorageCommandsPlugin:
    """存储命令插件"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.variable_manager = StorageVariableManager()
        self.cache_manager = CacheManager(
            max_size=self.config.get("cache", {}).get("max_size", 1000),
            default_ttl=self.config.get("cache", {}).get("default_ttl", 3600),
        )
        self.persistence_manager = PersistenceManager(
            storage_path=self.config.get("persistence", {}).get(
                "storage_path", "data/storage"
            )
        )

        # 注册命令
        self._register_commands()

        # 启动清理任务
        if self.config.get("cleanup", {}).get("enabled", True):
            self._start_cleanup_task()

    def _register_commands(self) -> None:
        """注册命令"""
        # 变量存储命令
        CommandFactory.register(StepAction.STORE_VARIABLE)(StoreVariableCommand)
        CommandFactory.register(StepAction.STORE_TEXT)(StoreTextCommand)
        CommandFactory.register(StepAction.STORE_ATTRIBUTE)(StoreAttributeCommand)
        CommandFactory.register(StepAction.SAVE_ELEMENT_COUNT)(SaveElementCountCommand)

        # 扩展存储命令
        CommandFactory.register("store_json")(StoreJsonCommand)
        CommandFactory.register("store_list")(StoreListCommand)
        CommandFactory.register("store_expression")(StoreExpressionCommand)
        CommandFactory.register("get_variable")(GetVariableCommand)
        CommandFactory.register("delete_variable")(DeleteVariableCommand)
        CommandFactory.register("list_variables")(ListVariablesCommand)
        CommandFactory.register("clear_scope")(ClearScopeCommand)

        # 缓存命令
        CommandFactory.register("set_cache")(SetCacheCommand)
        CommandFactory.register("get_cache")(GetCacheCommand)
        CommandFactory.register("delete_cache")(DeleteCacheCommand)
        CommandFactory.register("clear_cache")(ClearCacheCommand)
        CommandFactory.register("cache_stats")(CacheStatsCommand)

        # 持久化命令
        CommandFactory.register("save_persistent")(SavePersistentCommand)
        CommandFactory.register("load_persistent")(LoadPersistentCommand)
        CommandFactory.register("delete_persistent")(DeletePersistentCommand)
        CommandFactory.register("export_data")(ExportDataCommand)
        CommandFactory.register("import_data")(ImportDataCommand)

        # 批量操作命令
        CommandFactory.register("batch_store")(BatchStoreCommand)
        CommandFactory.register("batch_get")(BatchGetCommand)
        CommandFactory.register("batch_delete")(BatchDeleteCommand)

        # 管理命令
        CommandFactory.register("cleanup_storage")(CleanupStorageCommand)
        CommandFactory.register("storage_stats")(StorageStatsCommand)

    def _start_cleanup_task(self) -> None:
        """启动清理任务"""
        import threading

        def cleanup_task():
            while True:
                try:
                    interval = self.config.get("cleanup", {}).get("interval", 3600)
                    time.sleep(interval)

                    # 清理过期数据
                    var_count = self.variable_manager.cleanup_expired()
                    cache_count = self.cache_manager.cleanup_expired()
                    persist_count = self.persistence_manager.cleanup_expired()

                    total_count = var_count + cache_count + persist_count
                    if total_count > 0:
                        logger.info(
                            f"定期清理完成: 变量({var_count}) 缓存({cache_count}) 持久化({persist_count})"
                        )

                except Exception as e:
                    logger.error(f"清理任务错误: {e}")

        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
        logger.info("存储清理任务已启动")


# 原有命令的插件包装
class StoreVariableCommand(Command):
    """存储变量命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        var_name = step.get("name", "temp_var")
        var_value = step.get("value")
        scope = step.get("scope", "global")
        expression = step.get("expression")
        ttl = step.get("ttl")
        metadata = step.get("metadata")

        # 如果提供了表达式，则计算表达式的值
        if expression:
            try:
                var_value = evaluate_math_expression(
                    expression, ui_helper.variable_manager
                )
                logger.info(f"计算表达式: {expression} = {var_value}")
            except Exception as e:
                logger.error(f"计算表达式错误: {expression} - {e}")
                raise

        # 使用插件的变量管理器
        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            plugin.variable_manager.set_variable(
                var_name, var_value, scope, ttl, metadata
            )
        else:
            # 向后兼容
            ui_helper.variable_manager.set_variable(var_name, var_value, scope)

        logger.debug(f"已存储变量 {var_name}={var_value} (scope={scope})")


class StoreTextCommand(Command):
    """存储文本命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        var_name = step.get("variable_name", "text_var")
        scope = step.get("scope", "global")
        ttl = step.get("ttl")
        metadata = step.get("metadata")

        # 获取元素文本
        text = ui_helper.get_text(selector=selector)

        # 使用插件的变量管理器
        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            plugin.variable_manager.set_variable(var_name, text, scope, ttl, metadata)
        else:
            # 向后兼容
            ui_helper.variable_manager.set_variable(var_name, text, scope)

        logger.debug(f"已存储元素文本 {var_name}={text} (scope={scope})")


class StoreAttributeCommand(Command):
    """存储属性命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        var_name = step.get("variable_name", "attr_var")
        attribute = step.get("attribute")
        scope = step.get("scope", "global")
        ttl = step.get("ttl")
        metadata = step.get("metadata")

        # 获取元素属性
        attr_value = ui_helper.get_element_attribute(
            selector=selector, attribute=attribute
        )

        # 使用插件的变量管理器
        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            plugin.variable_manager.set_variable(
                var_name, attr_value, scope, ttl, metadata
            )
        else:
            # 向后兼容
            ui_helper.variable_manager.set_variable(var_name, attr_value, scope)

        logger.debug(f"已存储元素属性 {var_name}={attr_value} (scope={scope})")


class SaveElementCountCommand(Command):
    """存储元素数量命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        count = ui_helper.get_element_count(selector=selector)
        var_name = step.get("variable_name", "element_count")
        scope = step.get("scope", "global")
        ttl = step.get("ttl")
        metadata = step.get("metadata")

        # 使用插件的变量管理器
        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            plugin.variable_manager.set_variable(
                var_name, str(count), scope, ttl, metadata
            )
        else:
            # 向后兼容
            if "variable_name" in step:
                ui_helper.store_variable(
                    step["variable_name"], str(count), step.get("scope", "global")
                )

        logger.debug(f"已存储元素数量 {var_name}={count} (scope={scope})")


# 扩展存储命令
class StoreJsonCommand(Command):
    """存储JSON命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        var_name = step.get("variable_name", "json_var")
        json_data = step.get("json_data")
        scope = step.get("scope", "global")
        ttl = step.get("ttl")
        metadata = step.get("metadata")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            plugin.variable_manager.set_variable(
                var_name, json_data, scope, ttl, metadata
            )
            logger.debug(f"已存储JSON数据 {var_name} (scope={scope})")
        else:
            raise RuntimeError("存储插件未初始化")


class StoreListCommand(Command):
    """存储列表命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        var_name = step.get("variable_name", "list_var")
        list_data = step.get("list_data", [])
        scope = step.get("scope", "global")
        ttl = step.get("ttl")
        metadata = step.get("metadata")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            plugin.variable_manager.set_variable(
                var_name, list_data, scope, ttl, metadata
            )
            logger.debug(f"已存储列表数据 {var_name} (scope={scope})")
        else:
            raise RuntimeError("存储插件未初始化")


class StoreExpressionCommand(Command):
    """存储表达式结果命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        var_name = step.get("variable_name", "expr_var")
        expression = step.get("expression")
        scope = step.get("scope", "global")
        ttl = step.get("ttl")
        metadata = step.get("metadata")

        if not expression:
            raise ValueError("表达式不能为空")

        try:
            result = evaluate_math_expression(expression, ui_helper.variable_manager)
            plugin = getattr(ui_helper, "storage_plugin", None)
            if plugin:
                plugin.variable_manager.set_variable(
                    var_name, result, scope, ttl, metadata
                )
                logger.debug(f"已存储表达式结果 {var_name}={result} (scope={scope})")
            else:
                raise RuntimeError("存储插件未初始化")
        except Exception as e:
            logger.error(f"计算表达式错误: {expression} - {e}")
            raise


class GetVariableCommand(Command):
    """获取变量命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        var_name = step.get("variable_name")
        scope = step.get("scope", "global")
        default_value = step.get("default")
        target_var = step.get("target_variable", "retrieved_var")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            result = plugin.variable_manager.get_variable(
                var_name, scope, default_value
            )
            plugin.variable_manager.set_variable(target_var, result, scope)
            logger.debug(
                f"获取变量 {var_name}={result} -> {target_var} (scope={scope})"
            )
        else:
            raise RuntimeError("存储插件未初始化")


class DeleteVariableCommand(Command):
    """删除变量命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        var_name = step.get("variable_name")
        scope = step.get("scope", "global")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            success = plugin.variable_manager.delete_variable(var_name, scope)
            logger.debug(
                f"删除变量 {var_name} (scope={scope}): {'成功' if success else '失败'}"
            )
        else:
            raise RuntimeError("存储插件未初始化")


class ListVariablesCommand(Command):
    """列出变量命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        scope = step.get("scope")
        target_var = step.get("target_variable", "variable_list")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            variables = plugin.variable_manager.list_variables(scope)
            plugin.variable_manager.set_variable(target_var, variables, "global")
            logger.debug(f"列出变量 (scope={scope}): {len(variables)} 个变量")
        else:
            raise RuntimeError("存储插件未初始化")


class ClearScopeCommand(Command):
    """清空作用域命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        scope = step.get("scope", "global")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            plugin.variable_manager.clear_scope(scope)
            logger.debug(f"清空作用域: {scope}")
        else:
            raise RuntimeError("存储插件未初始化")


# 缓存命令
class SetCacheCommand(Command):
    """设置缓存命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        key = step.get("key")
        cache_value = step.get("value")
        ttl = step.get("ttl")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            plugin.cache_manager.set(key, cache_value, ttl)
            logger.debug(f"设置缓存 {key}={cache_value} (ttl={ttl})")
        else:
            raise RuntimeError("存储插件未初始化")


class GetCacheCommand(Command):
    """获取缓存命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        key = step.get("key")
        default_value = step.get("default")
        target_var = step.get("target_variable", "cache_value")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            result = plugin.cache_manager.get(key, default_value)
            plugin.variable_manager.set_variable(target_var, result, "global")
            logger.debug(f"获取缓存 {key}={result} -> {target_var}")
        else:
            raise RuntimeError("存储插件未初始化")


class DeleteCacheCommand(Command):
    """删除缓存命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        key = step.get("key")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            success = plugin.cache_manager.delete(key)
            logger.debug(f"删除缓存 {key}: {'成功' if success else '失败'}")
        else:
            raise RuntimeError("存储插件未初始化")


class ClearCacheCommand(Command):
    """清空缓存命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            plugin.cache_manager.clear()
            logger.debug("清空缓存")
        else:
            raise RuntimeError("存储插件未初始化")


class CacheStatsCommand(Command):
    """缓存统计命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        target_var = step.get("target_variable", "cache_stats")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            stats = plugin.cache_manager.get_stats()
            plugin.variable_manager.set_variable(target_var, stats, "global")
            logger.debug(f"缓存统计: {stats}")
        else:
            raise RuntimeError("存储插件未初始化")


# 持久化命令
class SavePersistentCommand(Command):
    """保存持久化数据命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        key = step.get("key")
        persist_value = step.get("value")
        scope = step.get("scope", "global")
        ttl = step.get("ttl")
        format_str = step.get("format", "json")
        metadata = step.get("metadata")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            scope_enum = StorageScope(scope)
            format_enum = SerializationFormat(format_str)
            plugin.persistence_manager.save(
                key, persist_value, scope_enum, ttl, format_enum, metadata
            )
            logger.debug(f"保存持久化数据 {key} (scope={scope}, format={format_str})")
        else:
            raise RuntimeError("存储插件未初始化")


class LoadPersistentCommand(Command):
    """加载持久化数据命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        key = step.get("key")
        scope = step.get("scope", "global")
        default_value = step.get("default")
        target_var = step.get("target_variable", "persistent_value")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            scope_enum = StorageScope(scope)
            result = plugin.persistence_manager.load(key, scope_enum, default_value)
            plugin.variable_manager.set_variable(target_var, result, "global")
            logger.debug(
                f"加载持久化数据 {key}={result} -> {target_var} (scope={scope})"
            )
        else:
            raise RuntimeError("存储插件未初始化")


class DeletePersistentCommand(Command):
    """删除持久化数据命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        key = step.get("key")
        scope = step.get("scope", "global")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            scope_enum = StorageScope(scope)
            success = plugin.persistence_manager.delete(key, scope_enum)
            logger.debug(
                f"删除持久化数据 {key} (scope={scope}): {'成功' if success else '失败'}"
            )
        else:
            raise RuntimeError("存储插件未初始化")


class ExportDataCommand(Command):
    """导出数据命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        file_path = step.get("file_path")
        scope = step.get("scope")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            scope_enum = StorageScope(scope) if scope else None
            plugin.persistence_manager.export_data(file_path, scope_enum)
            logger.info(f"导出数据到: {file_path}")
        else:
            raise RuntimeError("存储插件未初始化")


class ImportDataCommand(Command):
    """导入数据命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        file_path = step.get("file_path")
        target_var = step.get("target_variable", "import_count")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            count = plugin.persistence_manager.import_data(file_path)
            plugin.variable_manager.set_variable(target_var, count, "global")
            logger.info(f"导入数据从: {file_path} ({count} 条记录)")
        else:
            raise RuntimeError("存储插件未初始化")


# 批量操作命令
class BatchStoreCommand(Command):
    """批量存储命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        variables = step.get("variables", {})
        scope = step.get("scope", "global")
        ttl = step.get("ttl")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            for var_name, var_value in variables.items():
                plugin.variable_manager.set_variable(var_name, var_value, scope, ttl)
            logger.debug(f"批量存储 {len(variables)} 个变量 (scope={scope})")
        else:
            raise RuntimeError("存储插件未初始化")


class BatchGetCommand(Command):
    """批量获取命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        variable_names = step.get("variable_names", [])
        scope = step.get("scope", "global")
        target_var = step.get("target_variable", "batch_values")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            results = {}
            for var_name in variable_names:
                results[var_name] = plugin.variable_manager.get_variable(
                    var_name, scope
                )
            plugin.variable_manager.set_variable(target_var, results, "global")
            logger.debug(f"批量获取 {len(variable_names)} 个变量 -> {target_var}")
        else:
            raise RuntimeError("存储插件未初始化")


class BatchDeleteCommand(Command):
    """批量删除命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        variable_names = step.get("variable_names", [])
        scope = step.get("scope", "global")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            count = 0
            for var_name in variable_names:
                if plugin.variable_manager.delete_variable(var_name, scope):
                    count += 1
            logger.debug(
                f"批量删除 {count}/{len(variable_names)} 个变量 (scope={scope})"
            )
        else:
            raise RuntimeError("存储插件未初始化")


# 管理命令
class CleanupStorageCommand(Command):
    """清理存储命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        target_var = step.get("target_variable", "cleanup_stats")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            var_count = plugin.variable_manager.cleanup_expired()
            cache_count = plugin.cache_manager.cleanup_expired()
            persist_count = plugin.persistence_manager.cleanup_expired()

            stats = {
                "variables_cleaned": var_count,
                "cache_cleaned": cache_count,
                "persistent_cleaned": persist_count,
                "total_cleaned": var_count + cache_count + persist_count,
            }

            plugin.variable_manager.set_variable(target_var, stats, "global")
            logger.info(f"清理存储完成: {stats}")
        else:
            raise RuntimeError("存储插件未初始化")


class StorageStatsCommand(Command):
    """存储统计命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        target_var = step.get("target_variable", "storage_stats")

        plugin = getattr(ui_helper, "storage_plugin", None)
        if plugin:
            # 变量统计
            var_stats = {}
            for scope in StorageScope:
                var_stats[scope.value] = len(
                    plugin.variable_manager.list_variables(scope)
                )

            # 缓存统计
            cache_stats = plugin.cache_manager.get_stats()

            # 持久化统计
            persist_stats = {"total_keys": len(plugin.persistence_manager.list_keys())}

            stats = {
                "variables": var_stats,
                "cache": cache_stats,
                "persistent": persist_stats,
                "timestamp": datetime.now().isoformat(),
            }

            plugin.variable_manager.set_variable(target_var, stats, "global")
            logger.debug(f"存储统计: {stats}")
        else:
            raise RuntimeError("存储插件未初始化")
