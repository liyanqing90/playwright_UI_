# 表达式评估插件

## 概述

表达式评估插件提供了安全的数学表达式计算功能，支持丰富的内置函数、自定义函数和变量管理，适用于各种测试场景中的数值计算需求。

## 功能特性

- **安全计算**：在受限环境中执行表达式，防止恶意代码执行
- **丰富函数库**：内置数学、三角、逻辑、字符串等多类函数
- **自定义函数**：支持注册和使用自定义函数
- **变量管理**：支持设置和获取表达式变量
- **类型转换**：支持多种数据类型转换
- **表达式验证**：提供表达式语法验证功能

## 支持的函数类型

### 数学函数

- `abs(x)` - 绝对值
- `round(x)` - 四舍五入
- `min(...)` - 最小值
- `max(...)` - 最大值
- `sum(iterable)` - 求和
- `sqrt(x)` - 平方根
- `pow(x, y)` - 幂运算
- `floor(x)` - 向下取整
- `ceil(x)` - 向上取整
- `log(x)` - 自然对数
- `log10(x)` - 常用对数
- `exp(x)` - 指数函数

### 三角函数

- `sin(x)` - 正弦
- `cos(x)` - 余弦
- `tan(x)` - 正切
- `asin(x)` - 反正弦
- `acos(x)` - 反余弦
- `atan(x)` - 反正切

### 类型转换函数

- `int(x)` - 转换为整数
- `float(x)` - 转换为浮点数
- `str(x)` - 转换为字符串
- `bool(x)` - 转换为布尔值

### 字符串函数

- `upper(s)` - 转大写
- `lower(s)` - 转小写
- `strip(s)` - 去除空白
- `replace(s, old, new)` - 替换字符串
- `len(s)` - 获取长度

### 逻辑函数

- `and_(a, b)` - 逻辑与
- `or_(a, b)` - 逻辑或
- `not_(a)` - 逻辑非

### 比较函数

- `eq(a, b)` - 等于
- `ne(a, b)` - 不等于
- `lt(a, b)` - 小于
- `le(a, b)` - 小于等于
- `gt(a, b)` - 大于
- `ge(a, b)` - 大于等于

### 条件函数

- `if_(condition, true_val, false_val)` - 条件判断

### 常量

- `pi` - 圆周率 (3.141592653589793)
- `e` - 自然常数 (2.718281828459045)

## 使用方法

### 基本表达式计算

```yaml
# 简单数学计算
- action: evaluate_expression
  value: "2 + 3 * 4"
  variable: result1

# 使用函数
- action: evaluate_expression
  value: "sqrt(16) + pow(2, 3)"
  variable: result2

# 使用常量
- action: evaluate_expression
  value: "pi * 2"
  variable: circumference
```

### 带上下文的表达式

```yaml
# 使用上下文变量
- action: evaluate_expression
  value:
    expression: "x + y * 2"
    context:
      x: 10
      y: 5
  variable: result
```

### 变量管理

```yaml
# 设置变量
- action: set_variable
  value:
    name: "radius"
    value: 5
    description: "圆的半径"

# 获取变量
- action: get_variable
  value:
    name: "radius"
    default: 1
  variable: r

# 使用变量计算
- action: evaluate_expression
  value: "pi * radius * radius"
  variable: area
```

### 自定义函数

```yaml
# 注册自定义函数
- action: register_function
  value:
    name: "circle_area"
    function: "pi * (args[0] ** 2)"
    description: "计算圆面积"
    category: "geometry"
    args_count: 1

# 使用自定义函数
- action: evaluate_expression
  value: "circle_area(5)"
  variable: area
```

### 复杂表达式示例

```yaml
# 条件判断
- action: evaluate_expression
  value: "if_(score >= 60, 'pass', 'fail')"
  variable: result

# 字符串操作
- action: evaluate_expression
  value: "upper('hello world')"
  variable: uppercase_text

# 三角函数计算
- action: evaluate_expression
  value: "sin(pi / 2) + cos(0)"
  variable: trig_result

# 逻辑运算
- action: evaluate_expression
  value: "and_(gt(score, 80), lt(score, 90))"
  variable: is_good_score
```

## 参数说明

### evaluate_expression 命令参数

#### 简单格式

```yaml
value: "expression_string"
```

#### 完整格式

```yaml
value:
  expression: "expression_string"  # 必需：表达式字符串
  context:                         # 可选：上下文变量
    var1: value1
    var2: value2
```

### register_function 命令参数

```yaml
value:
  name: "function_name"           # 必需：函数名称
  function: "function_code"       # 必需：函数代码
  description: "function_desc"    # 可选：函数描述
  category: "category_name"       # 可选：函数分类
  args_count: 2                   # 可选：参数数量
```

### set_variable 命令参数

```yaml
value:
  name: "variable_name"           # 必需：变量名称
  value: variable_value           # 必需：变量值
  description: "variable_desc"    # 可选：变量描述
```

### get_variable 命令参数

#### 简单格式

```yaml
value: "variable_name"
```

#### 完整格式

```yaml
value:
  name: "variable_name"           # 必需：变量名称
  default: default_value          # 可选：默认值
```

## 安全特性

### 安全限制

1. **函数白名单**：只允许使用预定义的安全函数
2. **模块限制**：禁止导入危险模块
3. **代码注入防护**：检测和阻止恶意代码模式
4. **表达式长度限制**：防止过长表达式导致的性能问题
5. **括号匹配检查**：确保表达式语法正确

### 禁用的危险函数

- `exec`, `eval`, `compile`
- `open`, `file`, `input`
- `__import__`, `getattr`, `setattr`
- `globals`, `locals`, `vars`, `dir`

## 配置选项

```yaml
settings:
  enabled: true                    # 是否启用插件
  safe_mode: true                  # 安全模式
  max_expression_length: 1000      # 表达式最大长度
  timeout: 5                       # 计算超时时间
  allow_custom_functions: true     # 是否允许自定义函数
  precision: 10                    # 浮点数精度
```

## 错误处理

插件会捕获并报告以下类型的错误：

1. **语法错误**：表达式语法不正确
2. **类型错误**：函数参数类型不匹配
3. **名称错误**：使用了未定义的变量或函数
4. **值错误**：函数参数值不在有效范围内
5. **安全错误**：尝试使用被禁止的函数或操作

## 性能考虑

1. **表达式缓存**：复杂表达式可以考虑缓存结果
2. **变量作用域**：合理管理变量生命周期
3. **函数复杂度**：避免注册过于复杂的自定义函数
4. **递归限制**：防止无限递归

## 扩展开发

### 添加新的内置函数

```python
# 在插件初始化时注册
plugin.register_function(
    "custom_func",
    lambda x: x * 2,
    "自定义函数",
    "custom",
    1
)
```

### 创建函数分类

```python
# 注册同一分类的多个函数
geometry_functions = {
    "circle_area": lambda r: math.pi * r * r,
    "circle_circumference": lambda r: 2 * math.pi * r,
    "rectangle_area": lambda w, h: w * h
}

for name, func in geometry_functions.items():
    plugin.register_function(name, func, category="geometry")
```

## 使用示例

### 测试数据计算

```yaml
# 计算测试用例的期望值
- action: set_variable
  value:
    name: "base_price"
    value: 100

- action: set_variable
  value:
    name: "discount_rate"
    value: 0.1

- action: evaluate_expression
  value: "base_price * (1 - discount_rate)"
  variable: expected_price
```

### 条件验证

```yaml
# 验证测试结果
- action: evaluate_expression
  value: "and_(ge(actual_value, min_value), le(actual_value, max_value))"
  variable: is_valid_range
```

### 数据转换

```yaml
# 温度转换
- action: register_function
  value:
    name: "celsius_to_fahrenheit"
    function: "args[0] * 9 / 5 + 32"
    description: "摄氏度转华氏度"

- action: evaluate_expression
  value: "celsius_to_fahrenheit(25)"
  variable: fahrenheit_temp
```

## 注意事项

1. **表达式格式**：支持 `${{expression}}` 格式，也可以直接使用表达式字符串
2. **变量作用域**：插件变量与系统变量管理器是独立的
3. **函数命名**：避免与内置函数重名
4. **安全性**：自定义函数代码会被执行，请确保代码安全
5. **性能**：复杂表达式可能影响执行性能

## 版本历史

- v1.0.0 - 初始版本，支持基本表达式计算和函数管理

## 许可证

本插件遵循项目主许可证。