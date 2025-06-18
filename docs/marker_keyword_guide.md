# 标记（Marker）和关键字（Keyword）使用指南

本文档详细介绍如何在之家UI自动化测试框架中使用标记（marker）和关键字（keyword）参数来筛选和组织测试用例。

## 目录

- [概述](#概述)
- [标记（Marker）使用](#标记marker使用)
- [关键字（Keyword）使用](#关键字keyword使用)
- [命令行参数](#命令行参数)
- [最佳实践](#最佳实践)
- [示例用法](#示例用法)
- [常见问题](#常见问题)

## 概述

标记和关键字是pytest提供的强大功能，允许您：

- **选择性运行测试**：只运行特定类型的测试用例
- **组织测试套件**：将测试用例按功能、优先级等分类
- **提高测试效率**：在开发过程中快速验证特定功能
- **支持CI/CD**：在不同阶段运行不同级别的测试

## 标记（Marker）使用

### 什么是标记

标记是附加到测试用例上的元数据标签，用于对测试用例进行分类。在YAML测试用例中，通过`markers`字段定义。

### 预定义标记

框架预定义了以下常用标记：

| 标记            | 用途    | 示例场景         |
|---------------|-------|--------------|
| `smoke`       | 冒烟测试  | 快速验证核心功能是否正常 |
| `regression`  | 回归测试  | 验证修复后的功能是否正常 |
| `critical`    | 关键功能  | 核心业务流程测试     |
| `slow`        | 慢速测试  | 执行时间较长的测试    |
| `fast`        | 快速测试  | 执行时间较短的测试    |
| `login`       | 登录功能  | 用户认证相关测试     |
| `payment`     | 支付功能  | 支付流程相关测试     |
| `search`      | 搜索功能  | 搜索相关测试       |
| `ui`          | 界面测试  | 用户界面相关测试     |
| `api`         | 接口测试  | API接口测试      |
| `integration` | 集成测试  | 多模块集成测试      |
| `e2e`         | 端到端测试 | 完整业务流程测试     |
| `mobile`      | 移动端测试 | 移动设备相关测试     |
| `desktop`     | 桌面端测试 | 桌面浏览器测试      |

### 在测试用例中使用标记

```yaml
tests:
  - name: test_login_smoke
    description: "登录功能冒烟测试"
    markers: ["smoke", "login", "critical"]  # 多个标记
    steps:
      - action: goto
        value: "/login"
      # ... 其他步骤

  - name: test_payment_flow
    description: "支付流程测试"
    markers: ["payment", "slow", "critical"]  # 组合标记
    steps:
      - action: goto
        value: "/checkout"
      # ... 其他步骤
```

### 标记表达式

支持使用逻辑运算符组合标记：

- **AND运算**：`smoke and login` - 同时包含smoke和login标记的测试
- **OR运算**：`smoke or regression` - 包含smoke或regression标记的测试
- **NOT运算**：`not slow` - 不包含slow标记的测试
- **括号分组**：`(smoke or regression) and not slow` - 复杂逻辑组合

## 关键字（Keyword）使用

### 什么是关键字

关键字筛选基于测试用例的名称、描述等文本内容进行模糊匹配。这是一种更灵活的筛选方式。

### 关键字匹配规则

- **部分匹配**：关键字只需要在测试名称或描述中出现即可
- **大小写敏感**：需要注意测试用例名称的大小写
- **支持正则表达式**：可以使用正则表达式进行复杂匹配

### 关键字表达式

支持使用逻辑运算符组合关键字：

- **AND运算**：`login and success` - 同时包含"login"和"success"的测试
- **OR运算**：`login or register` - 包含"login"或"register"的测试
- **NOT运算**：`login and not admin` - 包含"login"但不包含"admin"的测试
- **括号分组**：`(login or register) and not admin` - 复杂逻辑组合

## 命令行参数

### 基本语法

```bash
# 使用标记
python test_runner.py --project <项目名> --marker <标记表达式>
python test_runner.py --project <项目名> -m <标记表达式>

# 使用关键字
python test_runner.py --project <项目名> --keyword <关键字表达式>
python test_runner.py --project <项目名> -k <关键字表达式>

# 组合使用
python test_runner.py --project <项目名> -m <标记表达式> -k <关键字表达式>
```

### 参数说明

| 参数          | 短参数  | 类型     | 说明                          |
|-------------|------|--------|-----------------------------|
| `--marker`  | `-m` | string | pytest标记表达式，用于筛选特定标记的测试用例   |
| `--keyword` | `-k` | string | pytest关键字表达式，用于筛选匹配关键字的测试用例 |

## 最佳实践

### 1. 标记命名规范

- **功能分类**：按功能模块命名，如`login`、`payment`、`search`
- **优先级分类**：按重要性命名，如`critical`、`high`、`medium`、`low`
- **执行特性**：按执行特点命名，如`smoke`、`regression`、`slow`、`fast`
- **平台分类**：按平台命名，如`mobile`、`desktop`、`api`

### 2. 标记使用策略

```yaml
# 推荐：使用多个标记进行精确分类
markers: ["smoke", "login", "critical", "fast"]

# 避免：标记过于宽泛或重复
markers: ["test", "ui", "ui_test"]  # 不推荐
```

### 3. 测试套件组织

```bash
# 开发阶段：运行快速冒烟测试
python test_runner.py --project demo -m "smoke and fast"

# 功能测试：运行特定功能的所有测试
python test_runner.py --project demo -m login

# 回归测试：运行关键功能测试
python test_runner.py --project demo -m "critical or regression"

# 完整测试：排除慢速测试的所有测试
python test_runner.py --project demo -m "not slow"
```

### 4. CI/CD集成

```yaml
# GitHub Actions示例
- name: Run Smoke Tests
  run: python test_runner.py --project demo -m smoke

- name: Run Regression Tests
  run: python test_runner.py --project demo -m regression
  if: github.event_name == 'pull_request'

- name: Run Full Test Suite
  run: python test_runner.py --project demo
  if: github.ref == 'refs/heads/main'
```

## 示例用法

### 基础筛选

```bash
# 运行所有冒烟测试
python test_runner.py --project demo -m smoke

# 运行登录相关测试
python test_runner.py --project demo -m login

# 运行包含"payment"关键字的测试
python test_runner.py --project demo -k payment
```

### 复杂筛选

```bash
# 运行冒烟测试和回归测试
python test_runner.py --project demo -m "smoke or regression"

# 运行关键功能但排除慢速测试
python test_runner.py --project demo -m "critical and not slow"

# 运行登录或注册相关的快速测试
python test_runner.py --project demo -m fast -k "login or register"
```

### 组合筛选

```bash
# 标记和关键字组合
python test_runner.py --project demo -m smoke -k login

# 复杂逻辑组合
python test_runner.py --project demo -m "(smoke or critical) and not slow" -k "user"
```

### 特定场景

```bash
# 移动端测试
python test_runner.py --project demo -m mobile

# API接口测试
python test_runner.py --project demo -m api

# 端到端测试
python test_runner.py --project demo -m e2e

# 调试模式运行关键测试
python test_runner.py --project demo -m critical --headed
```

## 常见问题

### Q1: 如何查看所有可用的标记？

**A**: 查看`pytest.ini`文件中的`markers`部分，或运行：

```bash
pytest --markers
```

### Q2: 标记表达式不生效怎么办？

**A**: 检查以下几点：

1. 标记名称是否正确（区分大小写）
2. 表达式语法是否正确
3. 测试用例中是否正确定义了标记
4. 使用引号包围复杂表达式

### Q3: 关键字匹配不到测试用例？

**A**: 确认：

1. 关键字是否存在于测试用例名称或描述中
2. 大小写是否匹配
3. 使用`-v`参数查看详细的测试用例名称

### Q4: 如何添加自定义标记？

**A**: 在`pytest.ini`文件的`markers`部分添加：

```ini
markers =
    custom_marker: 自定义标记说明
```

### Q5: 标记和关键字的优先级？

**A**: 当同时使用标记和关键字时，测试用例必须同时满足两个条件才会被执行。

## 实现原理

### 动态标记应用

框架通过以下方式实现marker功能：

1. **YAML解析**：从测试用例文件中读取`markers`字段
2. **动态函数生成**：在`runner.py`中为每个测试用例动态创建pytest测试函数
3. **标记应用**：使用`pytest.mark`动态为生成的函数添加标记
4. **pytest集成**：通过命令行参数`-m`和`-k`传递给pytest执行器

### 代码实现示例

```python
# 在 ../src/automation/runner.py 中的实现
markers = case.get("markers", [])

# 添加自定义标记
for marker in markers:
    if isinstance(marker, str):
        marked_func = getattr(pytest.mark, marker)(marked_func)
    elif isinstance(marker, dict):
        # 支持带参数的标记
        for mark_name, mark_args in marker.items():
            if isinstance(mark_args, dict):
                marked_func = getattr(pytest.mark, mark_name)(**mark_args)(marked_func)
            else:
                marked_func = getattr(pytest.mark, mark_name)(mark_args)(marked_func)
```

### 验证方法

可以通过以下方式验证marker功能：

```bash
# 查看收集到的测试用例和标记
python test_runner.py --project demo --collect-only

# 运行特定标记的测试
python test_runner.py --project demo -m smoke

# 查看pytest标记信息
pytest --markers
```

## 总结

标记和关键字是测试用例管理的重要工具，合理使用可以：

1. **提高开发效率**：快速运行相关测试
2. **优化CI/CD流程**：在不同阶段运行不同级别的测试
3. **改善测试组织**：清晰的测试分类和管理
4. **支持团队协作**：统一的测试标准和规范
5. **动态标记应用**：通过YAML配置自动应用到动态生成的pytest函数

建议在项目开始时就制定标记使用规范，并在团队中推广使用。