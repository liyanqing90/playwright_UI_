# 技术实现细节

## 实现细节概述

本文档详细介绍之家UI自动化测试框架的具体技术实现，包括核心模块的代码实现、关键算法、数据结构设计等，帮助开发者深入理解框架内部机制。

## 最新优化成果

### 空指针安全检查机制

为提高框架稳定性，在2024年最新版本中对所有核心服务实现了完善的空指针检查机制，有效防止因依赖注入失败导致的AttributeError异常。

**修复范围：**
- `../../src/core/services/element_service.py`: 元素操作服务
- `../../src/core/services/navigation_service.py`: 导航服务
- `../../src/core/services/assertion_service.py`: 断言服务
- `../../src/core/mixins/variable_management.py`: 变量管理混入
- `../../src/core/mixins/performance_optimization.py`: 性能优化混入

**技术实现：**
```python
# 统一的空指针检查模式
def safe_variable_replacement(self, value: str) -> str:
    """安全的变量替换"""
    if self.variable_manager:
        return self.variable_manager.replace_variables_refactored(value)
    else:
        return value
```

这一改进显著提升了框架在各种运行环境下的稳定性和容错能力。

## 1. 测试用例动态生成实现

### 1.1 TestCaseGenerator核心实现

```python
class TestCaseGenerator(pytest.Item):
    """测试用例动态生成器"""
    
    def __init__(self, name, parent, test_cases, elements, test_datas, project_name):
        super().__init__(name, parent)
        self.test_cases = test_cases
        self.elements = elements
        self.test_datas = test_datas
        self.project_name = project_name
        self._generated_functions = {}
    
    def runtest(self):
        """pytest执行入口"""
        # 动态生成测试函数
        self._generate_test_functions()
        
        # 执行生成的测试函数
        for test_name, test_func in self._generated_functions.items():
            try:
                # 设置测试上下文
                self._setup_test_context(test_name)
                
                # 执行测试函数
                test_func()
                
                # 清理测试上下文
                self._cleanup_test_context(test_name)
                
            except Exception as e:
                logger.error(f"Test {test_name} failed: {e}")
                raise
    
    def _generate_test_functions(self):
        """生成测试函数"""
        for case in self.test_cases:
            test_name = case.get('name')
            if not test_name:
                continue
            
            # 创建测试函数
            test_func = self._create_test_function(case)
            
            # 设置函数属性
            test_func.__name__ = f"test_{test_name}"
            test_func.__doc__ = f"Auto-generated test for {test_name}"
            
            # 处理依赖关系
            depends_on = case.get('depends_on', [])
            if depends_on:
                test_func._depends_on = depends_on
            
            # 处理fixtures
            fixtures = case.get('fixtures', [])
            if fixtures:
                test_func._fixtures = fixtures
            
            self._generated_functions[test_name] = test_func
    
    def _create_test_function(self, case: dict):
        """创建单个测试函数"""
        test_name = case['name']
        
        def test_function():
            # 获取测试数据
            test_data = self.test_datas.get(test_name)
            if not test_data:
                pytest.skip(f"No test data found for {test_name}")
            
            # 创建执行器
            executor = CaseExecutor(
                elements=self.elements,
                test_datas=self.test_datas,
                project_name=self.project_name
            )
            
            # 执行测试用例
            executor.execute_case(case, test_name, test_data)
        
        return test_function
    
    def _setup_test_context(self, test_name: str):
        """设置测试上下文"""
        # 设置当前测试名称
        VariableManager().set_variable("current_test", test_name, "test_case")
        
        # 初始化测试级变量
        VariableManager().clear_scope("test_case")
        
        # 记录测试开始时间
        start_time = datetime.now().isoformat()
        VariableManager().set_variable("test_start_time", start_time, "test_case")
    
    def _cleanup_test_context(self, test_name: str):
        """清理测试上下文"""
        # 清理测试级变量
        VariableManager().clear_scope("test_case")
        VariableManager().clear_scope("step")
        
        # 记录测试结束时间
        end_time = datetime.now().isoformat()
        logger.info(f"Test {test_name} completed at {end_time}")
```

### 1.2 pytest集成机制

```python
def pytest_collect_file(parent, path):
    """pytest收集文件钩子"""
    if path.ext == ".yaml" and "cases" in str(path):
        return YamlTestFile.from_parent(parent, fspath=path)
    return None

class YamlTestFile(pytest.File):
    """YAML测试文件处理器"""
    
    def collect(self):
        """收集测试用例"""
        try:
            # 解析YAML文件
            with open(self.fspath, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
            
            # 获取项目名称
            project_name = self._extract_project_name()
            
            # 加载相关数据文件
            elements = self._load_elements(project_name)
            test_datas = self._load_test_data(project_name)
            
            # 获取测试用例列表
            test_cases = yaml_content.get('test_cases', [])
            
            if test_cases:
                # 创建测试生成器
                yield TestCaseGenerator.from_parent(
                    self,
                    name=f"{project_name}_tests",
                    test_cases=test_cases,
                    elements=elements,
                    test_datas=test_datas,
                    project_name=project_name
                )
        
        except Exception as e:
            logger.error(f"Failed to collect tests from {self.fspath}: {e}")
    
    def _extract_project_name(self) -> str:
        """从文件路径提取项目名称"""
        path_parts = Path(self.fspath).parts
        test_data_index = path_parts.index('test_data')
        return path_parts[test_data_index + 1]
    
    def _load_elements(self, project_name: str) -> dict:
        """加载元素定义"""
        elements_path = f"test_data/{project_name}/elements/elements.yaml"
        try:
            with open(elements_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"Elements file not found: {elements_path}")
            return {}
    
    def _load_test_data(self, project_name: str) -> dict:
        """加载测试数据"""
        data_path = f"test_data/{project_name}/data/data.yaml"
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f) or {}
                return content.get('test_data', {})
        except FileNotFoundError:
            logger.warning(f"Test data file not found: {data_path}")
            return {}
```

## 2. 变量管理系统实现

### 2.1 VariableManager核心实现

```python
@singleton
class VariableManager:
    """变量管理器 - 单例模式"""
    
    def __init__(self):
        # 多级变量存储
        self.variables = {
            "global": {},      # 全局变量
            "test_case": {},   # 测试用例级变量
            "module": {},      # 模块级变量
            "step": {},        # 步骤级变量
            "temp": {},        # 临时变量
        }
        
        # 作用域继承层次
        self.scope_hierarchy = {
            "step": ["step", "module", "test_case", "global"],
            "module": ["module", "test_case", "global"],
            "test_case": ["test_case", "global"],
            "global": ["global"],
            "temp": ["temp", "step", "module", "test_case", "global"],
        }
        
        # 性能优化相关
        self._replacement_cache = LRUCache(max_size=1000)
        self._expression_cache = LRUCache(max_size=500)
        self._variable_cache = LRUCache(max_size=2000)
        
        # 持久化配置
        self._persistent_scopes = {"global"}  # 需要持久化的作用域
        self._storage_backend = FileStorageBackend("variables.json")
        
        # 加载持久化变量
        self._load_persistent_variables()
    
    def set_variable(self, name: str, value: Any, scope: str = "step"):
        """设置变量"""
        if scope not in self.variables:
            raise ValueError(f"Invalid scope: {scope}")
        
        # 类型转换和验证
        processed_value = self._process_variable_value(value)
        
        # 设置变量
        self.variables[scope][name] = processed_value
        
        # 清除相关缓存
        self._invalidate_cache(name, scope)
        
        # 持久化处理
        if scope in self._persistent_scopes:
            self._save_persistent_variables()
        
        logger.debug(f"Set variable: {name} = {processed_value} (scope: {scope})")
    
    def get_variable(self, name: str, scope: str = "step", default: Any = None) -> Any:
        """获取变量"""
        # 检查缓存
        cache_key = f"{name}:{scope}"
        cached_value = self._variable_cache.get(cache_key)
        if cached_value is not None:
            return cached_value
        
        # 按作用域层次查找
        scopes_to_search = self.scope_hierarchy.get(scope, [scope])
        
        for search_scope in scopes_to_search:
            if name in self.variables[search_scope]:
                value = self.variables[search_scope][name]
                # 缓存结果
                self._variable_cache.set(cache_key, value)
                return value
        
        # 未找到变量，返回默认值
        return default
    
    def replace_variables_refactored(self, text: str, scope: str = "step") -> str:
        """高性能变量替换"""
        if not isinstance(text, str) or "${" not in text:
            return text
        
        # 生成缓存键
        all_vars = self._get_all_variables(scope)
        vars_hash = hash(frozenset(all_vars.items()))
        cache_key = f"{text}:{scope}:{vars_hash}"
        
        # 检查缓存
        cached_result = self._replacement_cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # 执行替换
        result = self._perform_replacement(text, scope)
        
        # 缓存结果
        self._replacement_cache.set(cache_key, result)
        
        return result
    
    def _perform_replacement(self, text: str, scope: str) -> str:
        """执行变量替换"""
        pattern = r'\$\{([^}]+)\}'
        all_variables = self._get_all_variables(scope)
        
        def replace_match(match):
            var_expr = match.group(1).strip()
            
            # 处理复杂表达式
            if self._is_expression(var_expr):
                return str(self._evaluate_expression(var_expr, all_variables))
            
            # 处理简单变量引用
            return str(self.get_variable(var_expr, scope, ""))
        
        return re.sub(pattern, replace_match, text)
    
    def _is_expression(self, expr: str) -> bool:
        """判断是否为表达式"""
        expression_operators = ['==', '!=', '>', '<', '>=', '<=', '+', '-', '*', '/', '?', ':']
        return any(op in expr for op in expression_operators)
    
    def _evaluate_expression(self, expression: str, variables: dict) -> Any:
        """计算表达式"""
        # 检查表达式缓存
        cache_key = f"{expression}:{hash(frozenset(variables.items()))}"
        cached_result = self._expression_cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        try:
            # 三元运算符处理
            if '?' in expression and ':' in expression:
                result = self._evaluate_ternary(expression, variables)
            else:
                # 普通表达式处理
                result = self._evaluate_normal_expression(expression, variables)
            
            # 缓存结果
            self._expression_cache.set(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Expression evaluation failed: {expression}, error: {e}")
            return expression
    
    def _evaluate_ternary(self, expression: str, variables: dict) -> Any:
        """计算三元运算符表达式"""
        # 解析 condition ? true_value : false_value
        parts = expression.split('?', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid ternary expression: {expression}")
        
        condition_expr = parts[0].strip()
        value_part = parts[1].strip()
        
        value_parts = value_part.split(':', 1)
        if len(value_parts) != 2:
            raise ValueError(f"Invalid ternary expression: {expression}")
        
        true_value = value_parts[0].strip()
        false_value = value_parts[1].strip()
        
        # 计算条件
        condition_result = self._evaluate_normal_expression(condition_expr, variables)
        
        # 返回相应的值
        if condition_result:
            return self._process_expression_value(true_value, variables)
        else:
            return self._process_expression_value(false_value, variables)
    
    def _evaluate_normal_expression(self, expression: str, variables: dict) -> Any:
        """计算普通表达式"""
        # 替换变量
        processed_expr = expression
        for var_name, var_value in variables.items():
            if var_name in processed_expr:
                if isinstance(var_value, str):
                    # 字符串需要加引号
                    processed_expr = processed_expr.replace(var_name, f"'{var_value}'")
                else:
                    processed_expr = processed_expr.replace(var_name, str(var_value))
        
        # 安全的表达式计算
        allowed_names = {
            "__builtins__": {},
            "abs": abs, "round": round, "min": min, "max": max,
            "len": len, "str": str, "int": int, "float": float,
            "bool": bool, "list": list, "dict": dict,
        }
        
        return eval(processed_expr, allowed_names)
    
    def _process_expression_value(self, value: str, variables: dict) -> Any:
        """处理表达式中的值"""
        value = value.strip()
        
        # 如果是变量引用
        if value in variables:
            return variables[value]
        
        # 如果是字符串字面量
        if (value.startswith("'") and value.endswith("'")) or \
           (value.startswith('"') and value.endswith('"')):
            return value[1:-1]
        
        # 如果是数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # 如果是布尔值
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # 默认返回字符串
        return value
    
    def _get_all_variables(self, scope: str) -> dict:
        """获取指定作用域的所有可见变量"""
        all_vars = {}
        scopes_to_search = self.scope_hierarchy.get(scope, [scope])
        
        # 按优先级合并变量（后面的覆盖前面的）
        for search_scope in reversed(scopes_to_search):
            all_vars.update(self.variables[search_scope])
        
        return all_vars
    
    def clear_scope(self, scope: str):
        """清空指定作用域的变量"""
        if scope in self.variables:
            self.variables[scope].clear()
            self._invalidate_scope_cache(scope)
            logger.debug(f"Cleared variables in scope: {scope}")
    
    def _invalidate_cache(self, var_name: str, scope: str):
        """使相关缓存失效"""
        # 清除变量缓存
        keys_to_remove = []
        for key in self._variable_cache._cache:
            if key.startswith(f"{var_name}:"):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._variable_cache._cache[key]
        
        # 清除替换缓存
        self._replacement_cache._cache.clear()
        self._expression_cache._cache.clear()
    
    def _invalidate_scope_cache(self, scope: str):
        """使作用域相关缓存失效"""
        self._variable_cache._cache.clear()
        self._replacement_cache._cache.clear()
        self._expression_cache._cache.clear()
```

### 2.2 缓存系统实现

```python
class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size=1000):
        self._cache = {}
        self._access_order = []
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
    
    def get(self, key):
        """获取缓存值"""
        if key in self._cache:
            # 更新访问顺序
            self._access_order.remove(key)
            self._access_order.append(key)
            self._hits += 1
            return self._cache[key]
        
        self._misses += 1
        return None
    
    def set(self, key, value):
        """设置缓存值"""
        if key in self._cache:
            # 更新现有值
            self._cache[key] = value
            self._access_order.remove(key)
            self._access_order.append(key)
        else:
            # 添加新值
            if len(self._cache) >= self._max_size:
                # 移除最少使用的项
                oldest_key = self._access_order.pop(0)
                del self._cache[oldest_key]
            
            self._cache[key] = value
            self._access_order.append(key)
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()
    
    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        return {
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': hit_rate,
            'size': len(self._cache),
            'max_size': self._max_size
        }
```

## 3. 步骤执行器实现

### 3.1 StepExecutor核心实现

```python
class StepExecutor:
    """步骤执行器"""
    
    def __init__(self, ui_helper, variable_manager: VariableManager):
        self.ui_helper = ui_helper
        self.variable_manager = variable_manager
        self.modules_cache = {}  # 模块缓存
        self.execution_context = ExecutionContext()
        self.performance_monitor = PerformanceMonitor()
    
    def execute_step(self, step: Dict[str, Any]) -> Any:
        """执行单个步骤"""
        step_id = self._generate_step_id(step)
        
        with self.performance_monitor.monitor_step(step_id):
            try:
                # 步骤前处理
                self._before_step_execution(step)
                
                # 执行步骤
                result = self._execute_step_internal(step)
                
                # 步骤后处理
                self._after_step_execution(step, result)
                
                return result
                
            except Exception as e:
                self._handle_step_error(step, e)
                raise
    
    def _execute_step_internal(self, step: Dict[str, Any]) -> Any:
        """内部步骤执行逻辑"""
        # 处理流程控制
        if "if" in step:
            return self._execute_conditional_step(step)
        elif "for_each" in step:
            return self._execute_loop_step(step)
        elif "use_module" in step:
            return self._execute_module_step(step)
        
        # 处理普通操作步骤
        action = step.get("action")
        if not action:
            raise ValueError("Step must have an 'action' field")
        
        return self._execute_action_step(step, action)
    
    def _execute_conditional_step(self, step: Dict[str, Any]) -> Any:
        """执行条件步骤"""
        condition = step.get("if")
        then_steps = step.get("then", [])
        else_steps = step.get("else", [])
        
        # 替换变量
        condition = self.variable_manager.replace_variables_refactored(condition, "step")
        
        # 计算条件
        variables = self.variable_manager._get_all_variables("step")
        condition_result = evaluate_expression(condition, variables)
        
        logger.info(f"Condition '{condition}' evaluated to: {condition_result}")
        
        # 执行相应分支
        if condition_result:
            return self._execute_steps_list(then_steps)
        else:
            return self._execute_steps_list(else_steps)
    
    def _execute_loop_step(self, step: Dict[str, Any]) -> List[Any]:
        """执行循环步骤"""
        for_each = step.get("for_each")
        loop_steps = step.get("steps", [])
        
        # 获取循环数据
        loop_data = self._resolve_loop_data(for_each)
        
        results = []
        for index, item in enumerate(loop_data):
            logger.info(f"Loop iteration {index + 1}/{len(loop_data)}, item: {item}")
            
            # 设置循环变量
            self.variable_manager.set_variable("item", item, "step")
            self.variable_manager.set_variable("index", index, "step")
            self.variable_manager.set_variable("is_first", index == 0, "step")
            self.variable_manager.set_variable("is_last", index == len(loop_data) - 1, "step")
            
            # 执行循环步骤
            loop_result = self._execute_steps_list(loop_steps)
            results.append(loop_result)
        
        return results
    
    def _execute_module_step(self, step: Dict[str, Any]) -> Any:
        """执行模块步骤"""
        module_name = step.get("use_module")
        module_params = step.get("params", {})
        
        # 加载模块
        module_data = self._load_module(module_name)
        
        # 保存当前模块级变量
        old_module_vars = self.variable_manager.variables["module"].copy()
        
        try:
            # 设置模块参数
            for param_name, param_value in module_params.items():
                # 替换参数值中的变量
                processed_value = self.variable_manager.replace_variables_refactored(
                    str(param_value), "step"
                )
                self.variable_manager.set_variable(param_name, processed_value, "module")
            
            # 执行模块步骤
            module_steps = module_data.get("steps", [])
            return self._execute_steps_list(module_steps)
            
        finally:
            # 恢复模块级变量
            self.variable_manager.variables["module"] = old_module_vars
    
    def _execute_action_step(self, step: Dict[str, Any], action: str) -> Any:
        """执行操作步骤"""
        # 预处理步骤数据
        processed_step = self._preprocess_step(step)
        
        # 使用命令模式执行
        return execute_action_with_command(self, action, processed_step)
    
    def _execute_steps_list(self, steps: List[Dict[str, Any]]) -> List[Any]:
        """执行步骤列表"""
        results = []
        for step in steps:
            result = self.execute_step(step)
            results.append(result)
        return results
    
    def _resolve_loop_data(self, for_each: str) -> List[Any]:
        """解析循环数据"""
        # 替换变量
        for_each = self.variable_manager.replace_variables_refactored(for_each, "step")
        
        # 如果是变量引用
        if for_each.startswith("${") and for_each.endswith("}"):
            var_name = for_each[2:-1]
            loop_data = self.variable_manager.get_variable(var_name, "step", [])
        else:
            # 直接解析数据
            try:
                # 安全的数据解析
                allowed_names = {"__builtins__": {}, "range": range, "list": list}
                loop_data = eval(for_each, allowed_names)
            except Exception as e:
                logger.error(f"Failed to parse loop data: {for_each}, error: {e}")
                loop_data = []
        
        if not isinstance(loop_data, (list, tuple, range)):
            logger.warning(f"Loop data is not iterable: {loop_data}, converting to list")
            loop_data = [loop_data]
        
        return list(loop_data)
    
    def _load_module(self, module_name: str) -> dict:
        """加载模块"""
        if module_name in self.modules_cache:
            return self.modules_cache[module_name]
        
        # 构建模块路径
        project_name = self.variable_manager.get_variable("project_name", "global", "default")
        module_path = f"test_data/{project_name}/modules/{module_name}.yaml"
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                module_data = yaml.safe_load(f)
            
            # 缓存模块
            self.modules_cache[module_name] = module_data
            logger.info(f"Loaded module: {module_name}")
            
            return module_data
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Module not found: {module_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in module {module_name}: {e}")
    
    def _preprocess_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """预处理步骤数据"""
        processed_step = {}
        
        for key, value in step.items():
            if isinstance(value, str):
                # 替换字符串中的变量
                processed_step[key] = self.variable_manager.replace_variables_refactored(
                    value, "step"
                )
            elif isinstance(value, (list, dict)):
                # 递归处理复杂数据结构
                processed_step[key] = self._preprocess_value(value)
            else:
                processed_step[key] = value
        
        return processed_step
    
    def _preprocess_value(self, value: Any) -> Any:
        """递归预处理值"""
        if isinstance(value, str):
            return self.variable_manager.replace_variables_refactored(value, "step")
        elif isinstance(value, list):
            return [self._preprocess_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._preprocess_value(v) for k, v in value.items()}
        else:
            return value
    
    def _generate_step_id(self, step: Dict[str, Any]) -> str:
        """生成步骤ID"""
        action = step.get("action", "unknown")
        selector = step.get("selector", "")
        timestamp = int(time.time() * 1000)
        return f"{action}_{hash(selector)}_{timestamp}"
    
    def _before_step_execution(self, step: Dict[str, Any]):
        """步骤执行前处理"""
        # 记录步骤开始时间
        self.variable_manager.set_variable(
            "step_start_time", 
            datetime.now().isoformat(), 
            "step"
        )
        
        # 清理临时变量
        self.variable_manager.clear_scope("temp")
    
    def _after_step_execution(self, step: Dict[str, Any], result: Any):
        """步骤执行后处理"""
        # 记录步骤结束时间
        self.variable_manager.set_variable(
            "step_end_time", 
            datetime.now().isoformat(), 
            "step"
        )
        
        # 存储步骤结果
        if result is not None:
            self.variable_manager.set_variable("last_step_result", result, "step")
    
    def _handle_step_error(self, step: Dict[str, Any], error: Exception):
        """处理步骤错误"""
        error_info = {
            "step": step,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        
        # 存储错误信息
        self.variable_manager.set_variable("last_error", error_info, "step")
        
        logger.error(f"Step execution failed: {error_info}")
```

## 4. 服务容器实现

### 4.1 ServiceContainer核心实现

```python
class ServiceContainer:
    """依赖注入服务容器"""
    
    def __init__(self, config_loader=None, environment_manager=None):
        # 服务注册表
        self._services: Dict[str, ServiceRegistration] = {}
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._service_configs: Dict[str, ServiceConfig] = {}
        
        # 依赖管理
        self._dependency_graph: Dict[str, List[str]] = {}
        self._resolution_stack: List[str] = []  # 用于检测循环依赖
        
        # 配置管理
        self._config_loader = config_loader or ConfigLoader()
        self._environment_manager = environment_manager or EnvironmentManager()
        
        # 容器配置
        global_config = self._config_loader.get_global_config()
        container_config = global_config.container
        
        self._auto_wire = container_config.get('auto_wire', True)
        self._lazy_loading = container_config.get('lazy_loading', True)
        self._circular_dependency_detection = container_config.get('circular_dependency_detection', True)
        self._service_validation = container_config.get('service_validation', True)
        
        # 性能监控
        self._resolution_stats = defaultdict(int)
        self._creation_times = {}
        
        # 自动装配
        if self._auto_wire:
            self._auto_register_services()
    
    def register_implementation(self, interface: Type[T], implementation: Type[T], 
                              scope: ServiceScope = ServiceScope.SINGLETON,
                              factory: Callable = None,
                              config: dict = None) -> 'ServiceContainer':
        """注册服务实现"""
        service_name = interface.__name__
        
        # 创建服务注册信息
        registration = ServiceRegistration(
            interface=interface,
            implementation=implementation,
            scope=scope,
            factory=factory,
            config=config or {},
            dependencies=self._extract_dependencies(implementation)
        )
        
        self._services[service_name] = registration
        
        # 更新依赖图
        self._dependency_graph[service_name] = registration.dependencies
        
        # 验证服务
        if self._service_validation:
            self._validate_service_registration(registration)
        
        logger.debug(f"Registered service: {service_name} -> {implementation.__name__}")
        return self
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T],
                        scope: ServiceScope = ServiceScope.SINGLETON) -> 'ServiceContainer':
        """注册工厂函数"""
        service_name = interface.__name__
        self._factories[service_name] = factory
        
        # 创建工厂注册信息
        registration = ServiceRegistration(
            interface=interface,
            implementation=None,
            scope=scope,
            factory=factory,
            dependencies=[]
        )
        
        self._services[service_name] = registration
        logger.debug(f"Registered factory for: {service_name}")
        return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """解析服务实例"""
        service_name = service_type.__name__
        
        # 统计解析次数
        self._resolution_stats[service_name] += 1
        
        # 检查是否已注册
        if service_name not in self._services:
            raise ServiceNotRegisteredException(f"Service not registered: {service_name}")
        
        registration = self._services[service_name]
        
        # 根据作用域处理
        if registration.scope == ServiceScope.SINGLETON:
            return self._resolve_singleton(service_name, registration)
        elif registration.scope == ServiceScope.TRANSIENT:
            return self._create_instance(service_name, registration)
        elif registration.scope == ServiceScope.SCOPED:
            return self._resolve_scoped(service_name, registration)
        else:
            raise ValueError(f"Unknown service scope: {registration.scope}")
    
    def _resolve_singleton(self, service_name: str, registration: ServiceRegistration) -> Any:
        """解析单例服务"""
        if service_name not in self._instances:
            # 检查循环依赖
            if self._circular_dependency_detection:
                self._check_circular_dependency(service_name)
            
            # 创建实例
            start_time = time.time()
            self._instances[service_name] = self._create_instance(service_name, registration)
            self._creation_times[service_name] = time.time() - start_time
        
        return self._instances[service_name]
    
    def _resolve_scoped(self, service_name: str, registration: ServiceRegistration) -> Any:
        """解析作用域服务"""
        scope_key = f"scoped_{service_name}"
        
        if scope_key not in self._instances:
            self._instances[scope_key] = self._create_instance(service_name, registration)
        
        return self._instances[scope_key]
    
    def _create_instance(self, service_name: str, registration: ServiceRegistration) -> Any:
        """创建服务实例"""
        try:
            # 添加到解析栈
            self._resolution_stack.append(service_name)
            
            # 使用工厂函数
            if registration.factory:
                return registration.factory()
            
            # 使用构造函数
            implementation = registration.implementation
            if not implementation:
                raise ValueError(f"No implementation or factory for service: {service_name}")
            
            # 解析构造函数依赖
            dependencies = self._resolve_dependencies(implementation)
            
            # 创建实例
            instance = implementation(**dependencies)
            
            # 执行初始化
            if hasattr(instance, 'initialize'):
                instance.initialize()
            
            return instance
            
        finally:
            # 从解析栈移除
            if service_name in self._resolution_stack:
                self._resolution_stack.remove(service_name)
    
    def _resolve_dependencies(self, implementation: Type) -> Dict[str, Any]:
        """解析构造函数依赖"""
        constructor = implementation.__init__
        sig = inspect.signature(constructor)
        
        dependencies = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # 获取参数类型
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                # 尝试从配置获取
                if param_name in self._service_configs:
                    dependencies[param_name] = self._service_configs[param_name]
                elif param.default != inspect.Parameter.empty:
                    # 使用默认值
                    dependencies[param_name] = param.default
                else:
                    raise ValueError(f"Cannot resolve dependency: {param_name} for {implementation.__name__}")
            else:
                # 递归解析依赖
                dependencies[param_name] = self.resolve(param_type)
        
        return dependencies
    
    def _extract_dependencies(self, implementation: Type) -> List[str]:
        """提取服务依赖"""
        if not implementation:
            return []
        
        constructor = implementation.__init__
        sig = inspect.signature(constructor)
        
        dependencies = []
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation != inspect.Parameter.empty:
                dependencies.append(param.annotation.__name__)
        
        return dependencies
    
    def _check_circular_dependency(self, service_name: str):
        """检查循环依赖"""
        if service_name in self._resolution_stack:
            cycle_path = ' -> '.join(self._resolution_stack + [service_name])
            raise CircularDependencyException(f"Circular dependency detected: {cycle_path}")
    
    def _validate_service_registration(self, registration: ServiceRegistration):
        """验证服务注册"""
        # 检查接口和实现的兼容性
        if registration.implementation:
            if not issubclass(registration.implementation, registration.interface):
                raise ValueError(
                    f"Implementation {registration.implementation.__name__} "
                    f"does not implement interface {registration.interface.__name__}"
                )
    
    def clear_scope(self, scope: ServiceScope):
        """清理指定作用域的实例"""
        if scope == ServiceScope.SCOPED:
            # 清理作用域实例
            scoped_keys = [k for k in self._instances.keys() if k.startswith('scoped_')]
            for key in scoped_keys:
                instance = self._instances.pop(key)
                if hasattr(instance, 'dispose'):
                    instance.dispose()
        elif scope == ServiceScope.SINGLETON:
            # 清理所有单例实例
            for instance in self._instances.values():
                if hasattr(instance, 'dispose'):
                    instance.dispose()
            self._instances.clear()
    
    def get_service_info(self, service_type: Type) -> dict:
        """获取服务信息"""
        service_name = service_type.__name__
        
        if service_name not in self._services:
            return {}
        
        registration = self._services[service_name]
        
        return {
            'name': service_name,
            'interface': registration.interface.__name__,
            'implementation': registration.implementation.__name__ if registration.implementation else 'Factory',
            'scope': registration.scope.value,
            'dependencies': registration.dependencies,
            'resolution_count': self._resolution_stats[service_name],
            'creation_time': self._creation_times.get(service_name, 0),
            'is_instantiated': service_name in self._instances
        }
    
    def get_container_stats(self) -> dict:
        """获取容器统计信息"""
        return {
            'registered_services': len(self._services),
            'instantiated_services': len(self._instances),
            'total_resolutions': sum(self._resolution_stats.values()),
            'resolution_stats': dict(self._resolution_stats),
            'creation_times': dict(self._creation_times)
        }
```

### 4.2 服务注册数据结构

```python
@dataclass
class ServiceRegistration:
    """服务注册信息"""
    interface: Type
    implementation: Optional[Type]
    scope: ServiceScope
    factory: Optional[Callable]
    config: dict
    dependencies: List[str]

class ServiceScope(Enum):
    """服务作用域"""
    SINGLETON = "singleton"    # 单例
    TRANSIENT = "transient"    # 瞬态
    SCOPED = "scoped"          # 作用域

class ServiceNotRegisteredException(Exception):
    """服务未注册异常"""
    pass

class CircularDependencyException(Exception):
    """循环依赖异常"""
    pass
```

## 5. 命令系统实现

### 5.1 命令执行器实现

```python
class CommandExecutor:
    """命令执行器"""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
        self.command_registry = CommandRegistry()
        self.command_monitor = CommandMonitor()
        self.retry_policy = RetryPolicy()
    
    def execute_command(self, action: str, **kwargs) -> Any:
        """执行命令"""
        # 获取命令类
        command_class = self.command_registry.get_command(action)
        if not command_class:
            raise CommandNotFoundException(f"Command not found: {action}")
        
        # 创建命令实例
        command = self._create_command_instance(command_class)
        
        # 执行命令
        return self._execute_with_retry(command, **kwargs)
    
    def _create_command_instance(self, command_class: Type[Command]) -> Command:
        """创建命令实例"""
        # 使用依赖注入创建命令
        try:
            return self.container.resolve(command_class)
        except ServiceNotRegisteredException:
            # 如果未注册，直接实例化
            return command_class()
    
    def _execute_with_retry(self, command: Command, **kwargs) -> Any:
        """带重试的命令执行"""
        max_retries = command.get_max_retries()
        retry_delay = command.get_retry_delay()
        
        for attempt in range(max_retries + 1):
            try:
                with self.command_monitor.monitor_execution(command.name):
                    return command.execute_with_monitoring(**kwargs)
            
            except Exception as e:
                if attempt == max_retries:
                    # 最后一次尝试失败
                    raise CommandExecutionException(f"Command {command.name} failed after {max_retries} retries: {e}")
                
                # 检查是否应该重试
                if not command.should_retry(e):
                    raise
                
                logger.warning(f"Command {command.name} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                
                # 等待后重试
                if retry_delay > 0:
                    time.sleep(retry_delay)
```

### 5.2 命令监控实现

```python
class CommandMonitor:
    """命令监控器"""
    
    def __init__(self):
        self.execution_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'success_count': 0,
            'error_count': 0,
            'last_execution': None
        })
        self.active_commands = {}
    
    @contextmanager
    def monitor_execution(self, command_name: str):
        """监控命令执行"""
        start_time = time.time()
        execution_id = f"{command_name}_{int(start_time * 1000)}"
        
        self.active_commands[execution_id] = {
            'command': command_name,
            'start_time': start_time,
            'status': 'running'
        }
        
        try:
            yield execution_id
            
            # 执行成功
            execution_time = time.time() - start_time
            self._record_success(command_name, execution_time)
            self.active_commands[execution_id]['status'] = 'success'
            
        except Exception as e:
            # 执行失败
            execution_time = time.time() - start_time
            self._record_error(command_name, execution_time, e)
            self.active_commands[execution_id]['status'] = 'error'
            self.active_commands[execution_id]['error'] = str(e)
            raise
        
        finally:
            # 清理活动命令记录
            if execution_id in self.active_commands:
                del self.active_commands[execution_id]
    
    def _record_success(self, command_name: str, execution_time: float):
        """记录成功执行"""
        stats = self.execution_stats[command_name]
        stats['count'] += 1
        stats['success_count'] += 1
        stats['total_time'] += execution_time
        stats['last_execution'] = datetime.now().isoformat()
    
    def _record_error(self, command_name: str, execution_time: float, error: Exception):
        """记录错误执行"""
        stats = self.execution_stats[command_name]
        stats['count'] += 1
        stats['error_count'] += 1
        stats['total_time'] += execution_time
        stats['last_execution'] = datetime.now().isoformat()
    
    def get_command_stats(self, command_name: str) -> dict:
        """获取命令统计信息"""
        stats = self.execution_stats[command_name]
        
        avg_time = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0
        success_rate = stats['success_count'] / stats['count'] if stats['count'] > 0 else 0
        
        return {
            'command_name': command_name,
            'execution_count': stats['count'],
            'success_count': stats['success_count'],
            'error_count': stats['error_count'],
            'success_rate': success_rate,
            'average_execution_time': avg_time,
            'total_execution_time': stats['total_time'],
            'last_execution': stats['last_execution']
        }
    
    def get_all_stats(self) -> dict:
        """获取所有命令统计信息"""
        return {
            command_name: self.get_command_stats(command_name)
            for command_name in self.execution_stats.keys()
        }
```

## 6. 性能监控实现

### 6.1 性能监控器

```python
class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.thresholds = {
            'step_execution_time': 30.0,  # 秒
            'page_load_time': 10.0,       # 秒
            'element_wait_time': 5.0,     # 秒
        }
        self.alerts = []
    
    @contextmanager
    def monitor_step(self, step_id: str):
        """监控步骤执行"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            # 记录指标
            self.metrics['step_execution_time'].append({
                'step_id': step_id,
                'execution_time': execution_time,
                'memory_delta': memory_delta,
                'timestamp': datetime.now().isoformat()
            })
            
            # 检查阈值
            if execution_time > self.thresholds['step_execution_time']:
                self._create_alert('step_execution_time', step_id, execution_time)
    
    def _get_memory_usage(self) -> float:
        """获取内存使用量"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB
    
    def _create_alert(self, metric_type: str, context: str, value: float):
        """创建性能告警"""
        alert = {
            'type': metric_type,
            'context': context,
            'value': value,
            'threshold': self.thresholds[metric_type],
            'timestamp': datetime.now().isoformat()
        }
        
        self.alerts.append(alert)
        logger.warning(f"Performance alert: {metric_type} = {value} > {self.thresholds[metric_type]} for {context}")
    
    def get_performance_report(self) -> dict:
        """生成性能报告"""
        report = {
            'summary': self._generate_summary(),
            'metrics': dict(self.metrics),
            'alerts': self.alerts,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_summary(self) -> dict:
        """生成性能摘要"""
        step_times = [m['execution_time'] for m in self.metrics['step_execution_time']]
        
        if not step_times:
            return {}
        
        return {
            'total_steps': len(step_times),
            'average_step_time': sum(step_times) / len(step_times),
            'max_step_time': max(step_times),
            'min_step_time': min(step_times),
            'total_execution_time': sum(step_times),
            'slow_steps_count': len([t for t in step_times if t > self.thresholds['step_execution_time']])
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        # 分析慢步骤
        slow_steps = [m for m in self.metrics['step_execution_time'] 
                     if m['execution_time'] > self.thresholds['step_execution_time']]
        
        if slow_steps:
            recommendations.append(f"发现 {len(slow_steps)} 个慢步骤，建议优化等待策略或选择器")
        
        # 分析内存使用
        memory_deltas = [m['memory_delta'] for m in self.metrics['step_execution_time']]
        if memory_deltas and max(memory_deltas) > 100:  # 100MB
            recommendations.append("检测到高内存使用，建议优化资源管理")
        
        return recommendations
```

## 总结

本文档详细介绍了之家UI自动化测试框架的核心技术实现，包括：

1. **动态测试生成**: 通过pytest钩子和YAML解析实现测试用例的动态生成
2. **变量管理系统**: 多级作用域、高性能缓存、表达式计算的完整实现
3. **步骤执行器**: 支持流程控制、模块化、错误处理的执行引擎
4. **服务容器**: 完整的依赖注入实现，支持多种作用域和循环依赖检测
5. **命令系统**: 基于命令模式的操作执行，支持监控和重试
6. **性能监控**: 全面的性能指标收集和分析

这些实现细节展示了框架的技术深度和工程质量，为开发者提供了深入理解和扩展框架的基础。