# 性能优化指南

## 概述

本指南介绍了在 `base_page` 拆分后如何使用新的性能优化功能来提升测试执行效率。

## 性能优化功能

### 1. 智能缓存系统

#### 元素定位缓存
- **功能**: 自动缓存已定位的元素，避免重复查找
- **配置**: 通过 `config/performance_optimization.yaml` 配置缓存参数
- **效果**: 显著减少重复元素定位的时间

```python
# 缓存配置示例
element_cache:
  timeout: 30        # 缓存超时时间(秒)
  enabled: true      # 是否启用缓存
  max_size: 1000     # 最大缓存数量
  cleanup_interval: 60  # 缓存清理间隔(秒)
```

#### 缓存使用示例

```python
from page_objects.base_page import BasePage

class TestPage(BasePage):
    def test_cached_operations(self):
        # 第一次定位 - 缓存未命中
        element1 = self._locator("input[name='username']")
        
        # 第二次定位 - 缓存命中，速度更快
        element2 = self._locator("input[name='username']")
        
        # 获取缓存统计
        stats = self.get_cache_stats()
        print(f"缓存命中率: {stats['hit_rate']:.1f}%")
```

### 2. 性能监控

#### 实时性能统计
- **操作计时**: 自动记录每个操作的执行时间
- **慢操作检测**: 自动识别和报告慢操作
- **缓存效率**: 监控缓存命中率和效果

```python
from utils.performance_manager import performance_manager

# 获取性能统计
stats = performance_manager.get_performance_stats()
print(f"""
运行时间: {stats['runtime_seconds']:.2f}秒
总操作数: {stats['total_operations']}
慢操作数: {stats['slow_operations']}
缓存命中率: {stats['cache_hit_rate']:.1f}%
每秒操作数: {stats['operations_per_second']:.1f}
""")
```

### 3. 环境优化

#### 自动环境适配

```python
# CI环境优化
performance_manager.optimize_for_environment("ci")
# - 减少截图数量
# - 缩短缓存时间
# - 禁用图片加载

# 调试环境优化
performance_manager.optimize_for_environment("debug")
# - 启用详细日志
# - 记录缓存命中
# - 显示性能统计

# 生产环境优化
performance_manager.optimize_for_environment("production")
# - 最大化缓存时间
# - 启用智能截图
# - 优化页面加载
```

### 4. 配置管理

#### 配置文件结构

`config/performance_optimization.yaml` 包含以下配置节：

- **element_cache**: 元素缓存配置
- **screenshot**: 截图管理配置
- **page_load**: 页面加载优化
- **element_wait**: 元素等待配置
- **monitoring**: 性能监控配置
- **concurrency**: 并发优化配置
- **debug**: 调试配置

#### 动态配置修改

```python
# 运行时修改配置
performance_manager.config['element_cache']['timeout'] = 60
performance_manager.config['screenshot']['max_count'] = 100

# 获取配置值
cache_timeout = performance_manager.get_cache_timeout()
max_screenshots = performance_manager.get_max_screenshots()
```

## 性能优化最佳实践

### 1. 合理使用缓存

```python
# ✅ 好的做法：重复使用相同选择器
class LoginPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.username_input = "input[name='username']"
        self.password_input = "input[name='password']"
        self.login_button = "button[type='submit']"
    
    def login(self, username, password):
        # 这些操作会受益于缓存
        self.fill(self.username_input, username)
        self.fill(self.password_input, password)
        self.click(self.login_button)

# ❌ 避免的做法：每次都构造新的选择器
class BadLoginPage(BasePage):
    def login(self, username, password):
        # 每次都是新的选择器，无法利用缓存
        self.fill(f"input[name='username'][value='{username}']", username)
        self.fill(f"input[name='password'][placeholder='密码']", password)
```

### 2. 监控性能瓶颈

```python
# 在测试开始前重置统计
performance_manager.reset_stats()

# 执行测试
test_suite.run()

# 分析性能统计
stats = performance_manager.get_performance_stats()
if stats['slow_operation_rate'] > 10:  # 超过10%的操作是慢操作
    print("警告：检测到性能问题，建议优化")
    
if stats['cache_hit_rate'] < 50:  # 缓存命中率低于50%
    print("建议：优化选择器重用以提高缓存效率")
```

### 3. 批量操作优化

```python
# ✅ 使用批量预加载
class DataPage(BasePage):
    def preload_form_elements(self):
        """预加载表单元素到缓存"""
        selectors = [
            "input[name='name']",
            "input[name='email']",
            "select[name='country']",
            "textarea[name='message']"
        ]
        self.preload_elements(selectors)
    
    def fill_form_fast(self, data):
        # 预加载后，这些操作会很快
        self.fill("input[name='name']", data['name'])
        self.fill("input[name='email']", data['email'])
        # ...
```

### 4. 环境特定优化

```python
# conftest.py
import os
from utils.performance_manager import performance_manager

@pytest.fixture(scope="session", autouse=True)
def setup_performance_optimization():
    """根据环境自动优化性能"""
    env = os.getenv('TEST_ENV', 'test')
    performance_manager.optimize_for_environment(env)
    
    if env == 'ci':
        # CI环境额外优化
        performance_manager.config['page_load']['disable_images'] = True
        performance_manager.config['element_cache']['max_size'] = 500
```

## 性能测试

### 运行性能测试

```bash
# 运行性能测试套件
pytest tests/performance_test.py -v

# 运行特定性能测试
pytest tests/performance_test.py::TestPerformance::test_cache_effectiveness -v
```

### 性能基准测试

```python
# 创建性能基准
class PerformanceBenchmark:
    def benchmark_element_location(self, page, iterations=100):
        """基准测试：元素定位性能"""
        base_page = BasePage(page)
        selector = "input[name='search']"
        
        # 测试无缓存性能
        performance_manager.config['element_cache']['enabled'] = False
        start_time = time.time()
        for _ in range(iterations):
            base_page._locator(selector)
        no_cache_time = time.time() - start_time
        
        # 测试有缓存性能
        performance_manager.config['element_cache']['enabled'] = True
        performance_manager.reset_stats()
        start_time = time.time()
        for _ in range(iterations):
            base_page._locator(selector)
        cache_time = time.time() - start_time
        
        improvement = ((no_cache_time - cache_time) / no_cache_time) * 100
        print(f"性能提升: {improvement:.1f}%")
        
        return {
            'no_cache_time': no_cache_time,
            'cache_time': cache_time,
            'improvement_percent': improvement
        }
```

## 故障排除

### 常见问题

#### 1. 缓存未生效

**症状**: 缓存命中率为0或很低

**解决方案**:
```python
# 检查缓存是否启用
if not performance_manager.is_cache_enabled():
    print("缓存未启用，请检查配置")

# 检查选择器是否一致
# 确保使用相同的选择器字符串
selector = "input[name='username']"  # 一致的选择器
# 避免: "input[name='username'] ", "input[name=\"username\"]"
```

#### 2. 性能反而下降

**症状**: 启用优化后性能变差

**解决方案**:
```python
# 检查缓存大小是否过大
if performance_manager.get_config('element_cache', 'max_size') > 2000:
    performance_manager.config['element_cache']['max_size'] = 1000

# 检查缓存超时是否过长
if performance_manager.get_cache_timeout() > 60:
    performance_manager.config['element_cache']['timeout'] = 30

# 清理缓存
base_page.clear_element_cache()
```

#### 3. 内存使用过高

**症状**: 测试运行时内存持续增长

**解决方案**:
```python
# 定期清理缓存
if performance_manager.get_performance_stats()['total_operations'] % 1000 == 0:
    base_page.clear_element_cache()

# 减少缓存大小
performance_manager.config['element_cache']['max_size'] = 500

# 缩短缓存超时
performance_manager.config['element_cache']['timeout'] = 15
```

## 总结

通过合理使用这些性能优化功能，你可以：

1. **提升测试执行速度** - 通过智能缓存减少重复操作
2. **监控性能瓶颈** - 实时了解测试性能状况
3. **优化资源使用** - 根据环境自动调整配置
4. **提高测试稳定性** - 减少因性能问题导致的测试失败

建议在项目中逐步启用这些功能，并根据实际情况调整配置参数以获得最佳性能。