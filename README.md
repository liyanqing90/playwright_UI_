# 之家 UI 自动化测试框架

之家 UI 自动化测试框架是一个基于 Playwright 的 UI 自动化测试框架，采用模块化设计，支持 YAML
格式的测试用例定义，提供灵活、高效、可维护的自动化测试解决方案。

## 目录

- [框架特性](#框架特性)
- [安装与配置](#安装与配置)
- [使用指南](#使用指南)
- [架构概述](#架构概述)
- [项目结构](#项目结构)
- [测试开发指南](#测试开发指南)
- [高级功能](#高级功能)
- [最佳实践](#最佳实践)
- [常用命令](#常用命令)
- [元素定位技巧](#元素定位技巧)
- [贡献指南](#贡献指南)
- [常见问题](#常见问题)
- [相关资源](#相关资源)

## 框架特性

### 核心功能

- **多浏览器支持**：基于Playwright实现，支持Chrome、Firefox、Safari等主流浏览器
- **YAML用例编写方式**：支持YAML方式编写测试用例
- **丰富的UI操作**：内置40+种常用UI操作，覆盖各种交互场景
- **多项目管理**：支持多项目、多环境配置，便于管理大型测试套件
- **Page Object模式**：完整的Page Object模式实现，提高代码复用性
- **详细日志与报告**：详细的操作日志、失败截图和Allure测试报告
- **健壮的错误处理**：完善的空指针检查和异常处理机制，提高框架稳定性
- **最新稳定性改进**：2024年版本全面优化了核心服务的空指针安全检查，彻底解决AttributeError异常问题

### 高级特性

- **数据驱动能力**：
    - 多级变量管理：支持全局变量、测试用例级变量和临时变量
    - 表达式计算：支持条件判断、数学运算等
    - 模块化组件：可复用的测试步骤片段
    - 流程控制：支持if-then-else条件分支和for_each循环结构

- **性能优化功能**：
    - 浏览器资源池：减少浏览器启动开销，支持复用和健康检查
    - 智能截图策略：仅在测试失败时截图，支持压缩和区域截图
    - 日志轮转机制：自动归档和清理日志，减少存储占用

## 架构概述

之家 UI 自动化测试框架采用模块化设计，由以下核心组件构成：

### 1. 测试运行器 (Runner)

测试运行器负责加载和执行测试用例，管理测试环境和浏览器实例，收集测试结果并生成报告。

**主要文件**:

- `test_runner.py`: 主入口文件，负责解析命令行参数和启动测试
- `src/automation/runner.py`: 核心运行器实现，负责测试用例的加载和执行

### 2. 测试用例执行器 (TestCaseExecutor)

测试用例执行器负责解析和执行单个测试用例，管理测试步骤的执行流程和错误处理。

**主要文件**:

- `src/automation/test_case_executor.py`: 测试用例执行器实现

### 3. 测试步骤执行器 (StepExecutor)

测试步骤执行器负责执行单个测试步骤，包括 UI 操作、断言、变量管理等。

**主要文件**:

- `src/automation/step_executor.py`: 测试步骤执行器核心实现
- `src/automation/action_types.py`: 操作类型定义
- `src/automation/command_executor.py`: 命令执行器
- `src/automation/flow_control.py`: 流程控制实现
- `src/automation/module_handler.py`: 模块处理器

### 4. 核心服务层 (Core Services)

核心服务层提供了模块化的服务组件，封装了各种UI操作、断言、导航等功能，采用依赖注入模式提供灵活的服务管理。

**主要文件**:

- `src/core/base_page.py`: 基础页面类，集成所有服务和混入功能
- `src/core/services/`: 服务层目录，包含各种专业化服务
  - `element_service.py`: 元素操作服务
  - `navigation_service.py`: 导航服务
  - `assertion_service.py`: 断言服务
  - `wait_service.py`: 等待服务
  - `variable_service.py`: 变量管理服务
  - `performance_service.py`: 性能监控服务
- `src/core/mixins/`: 混入层，提供横切关注点功能
  - `variable_management.py`: 变量管理混入
  - `performance_optimization.py`: 性能优化混入
  - `error_reporter.py`: 错误报告混入
  - `decorators.py`: 装饰器混入

### 5. 工具类 (Utils)

工具类提供了各种辅助功能，如变量管理、配置管理、日志记录等。

**主要文件**:

- `src/common/variable_manager.py`: 变量管理器
- `src/common/config_manager.py`: 配置管理
- `src/utils.py`: 通用工具函数
- `src/case_utils.py`: 测试用例工具

## 安装与配置

### 环境要求

1. Python 3.10+
2. Poetry包管理工具（[安装指南](https://python-poetry.org/docs/#installation)）

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/your-username/zhijia_ui.git
   cd zhijia_ui
   ```

2. **安装依赖**
   ```bash
   poetry install
   ```

3. **安装浏览器驱动**
   ```bash
   playwright install chromium
   # 或安装所有浏览器
   # playwright install
   ```

## 使用指南

### 运行测试

1. **运行指定项目的测试**
   ```bash
   python test_runner.py --project demo
   ```

2. **运行指定测试文件**
   ```bash
   python test_runner.py --project demo --test-file test_cases
   ```

3. **有头模式运行**
   ```bash
   python test_runner.py --project demo --headed
   ```

### 生成报告

```bash
allure serve reports/allure-results
```

### 工具命令

1. **检查重复元素和用例**
   ```bash
   python check_duplicates.py
   ```

2. **代码格式化**
   ```bash
   poetry run black .
   ```

3. **导出依赖清单**
   ```bash
   poetry export -f requirements.txt --output requirements.txt
   ```

## 项目结构

```
zhijia_ui/
├── config/                  # 配置文件目录
│   ├── env_config.yaml      # 环境配置
│   ├── test_config.yaml     # 测试配置
│   ├── performance_config.yaml # 性能配置
│   └── constants.py         # 常量定义
├── evidence/                # 测试证据目录
│   └── screenshots/         # 测试截图
├── reports/                 # 测试报告目录
│   └── allure-results/      # Allure报告数据
├── src/                     # 框架核心代码
│   ├── automation/          # 自动化执行引擎
│   │   ├── runner.py        # 测试运行器
│   │   ├── test_case_executor.py # 测试用例执行器
│   │   ├── step_executor.py # 测试步骤执行器
│   │   ├── command_executor.py # 命令执行器
│   │   ├── commands/        # 命令实现目录
│   │   ├── flow_control.py  # 流程控制
│   │   └── module_handler.py # 模块处理器
│   ├── core/                # 核心服务层
│   │   ├── base_page.py     # 基础页面类
│   │   ├── services/        # 服务层
│   │   ├── mixins/          # 混入层
│   │   ├── config/          # 配置管理
│   │   └── performance/     # 性能监控
│   ├── common/              # 公共组件
│   │   ├── config_manager.py # 配置管理器
│   │   ├── exceptions.py    # 异常定义
│   │   └── types.py         # 类型定义
│   └── utils.py             # 工具函数
├── plugins/                 # 插件系统
│   ├── assertion_commands/  # 断言命令插件
│   ├── network_operations/  # 网络操作插件
│   └── performance_management/ # 性能管理插件
├── test_data/               # 测试数据目录
│   ├── <project>/           # 各项目的测试数据
│   │   ├── cases/           # 测试用例定义
│   │   ├── data/            # 测试数据定义
│   │   ├── elements/        # 页面元素定义
│   │   ├── modules/         # 可复用测试模块
│   │   └── variables.json   # 项目级变量定义
│   └── common/              # 公共测试数据
└── project_documentation/   # 项目文档
    ├── architecture/        # 架构文档
    ├── api_reference/       # API参考
    ├── implementation_details/ # 实现细节
    └── quick_start/         # 快速开始指南
```

## 测试开发指南

### 测试用例编写

#### 用例组织结构

测试用例由三个核心文件协同定义，采用模块化组织方式：

1. **用例元数据文件** (`cases/cases.yaml`)
    - 定义测试用例的基本信息
    - 包含用例名称、描述、标签、前置条件等
    - 示例：
      ```yaml
      test_login:
        description: "用户登录测试"
        tags: ["smoke", "login"]
        fixtures: ["setup_browser"]
        depends_on: []
      ```

2. **测试步骤文件** (`data/index.yaml`)
    - 定义测试用例的具体执行步骤
    - 包含操作类型、目标元素、参数值等
    - 支持条件分支、循环和模块引用
    - 示例：
      ```yaml
      test_login:
        steps:
          - action: goto
            value: "${base_url}/login"
            description: "打开登录页面"
 
          - action: fill
            selector: "username_input"
            value: "${username}"
            description: "输入用户名"
 
          - action: fill
            selector: "password_input"
            value: "${password}"
            description: "输入密码"
 
          - action: click
            selector: "login_button"
            description: "点击登录按钮"
 
          - action: expect_visible
            selector: "welcome_message"
            timeout: 5000
            description: "验证登录成功"
      ```

3. **元素定义文件** (`elements/elements.yaml`)
    - 集中定义页面元素的定位策略
    - 支持多种定位方式（CSS、XPath、Text等）
    - 每个元素包含选择器和描述信息
    - 示例：
      ```yaml
      username_input:  "#username" # "用户名输入框"
 
      password_input:  "#password" # "密码输入框"
 
      login_button:  "button.login-btn" # "登录按钮"
 
      welcome_message: ".welcome-text" # "欢迎信息"
      ```

#### 用例编写流程

1. **规划测试用例**
    - 确定测试目标和范围
    - 设计测试步骤和预期结果

2. **定义页面元素**
    - 在 `elements/elements.yaml` 中添加所需元素
    - 使用最稳定的定位方式
    - 添加清晰的描述信息

3. **编写测试用例元数据**
    - 在 `cases/cases.yaml` 中添加用例定义
    - 指定用例名称、描述和标签
    - 配置必要的前置条件

4. **编写测试步骤**
    - 在 `data/index.yaml` 中添加测试步骤
    - 按顺序编写清晰的操作步骤
    - 使用变量和参数化数据
    - 添加必要的断言和验证步骤

## 高级功能

我们对原有 Playwright UI 自动化测试框架进行了一系列增强，使其更加灵活、可维护、高效。主要新增功能包括：

1. **模块化测试片段系统**：支持将常用测试步骤封装为可重用模块
2. **条件分支执行**：支持在测试用例中使用 if-then-else 条件分支
3. **循环执行**：支持循环遍历数据列表执行重复操作
4. **增强的变量管理**：支持全局/测试用例/临时多级作用域变量

### 模块化测试片段

模块化测试片段允许将常用操作封装为可重用模块，减少重复编写相同步骤的工作。

#### 定义模块

在 `test_data/<项目>/modules/` 目录下创建 YAML 文件，定义可重用的步骤：

```yaml
# test_data/demo/modules/login.yaml
login:
  - action: navigate
    value: "/login"
    description: "打开登录页面"

  - action: fill
    selector: "username_input"
    value: "${username}"
    description: "输入用户名"

  - action: fill
    selector: "password_input"
    value: "${password}"
    description: "输入密码"

  - action: click
    selector: "login_button"
    description: "点击登录按钮"
```

#### 使用模块

在测试用例中引用模块：

```yaml
# test_data/demo/data/test.yaml
login_test:
  steps:
    - use_module: login
      params:
        username: "test_user"
        password: "password123"
      description: "使用登录模块"

    - action: assert_text
      selector: "welcome_message"
      expected: "欢迎回来"
      description: "验证登录成功"
```

### 条件分支

条件分支允许基于条件执行不同的测试步骤，增加测试用例的灵活性。

```yaml
# 条件分支示例
- if: "${{ ${user_type} == 'admin' }}"
  then:
    - action: click
      selector: "admin_panel"
      description: "点击管理员面板"
  else:
    - action: click
      selector: "user_dashboard"
      description: "点击用户仪表盘"
```

### 循环执行

循环执行允许对列表中的数据项执行重复操作，适用于批量处理场景。

```yaml
# 循环执行示例
- action: store_variable
  name: "product_ids"
  value: [ 1, 2, 3 ]
  scope: "test_case"
  description: "设置产品ID列表"

- for_each: "${product_ids}"
  as: "product_id"
  do:
    - action: click
      selector: "product_${product_id}_view"
      description: "查看产品${product_id}详情"

    - action: click
      selector: "add_to_cart_button"
      description: "添加到购物车"
```

### 变量管理

框架支持多级作用域的变量管理，包括全局变量、测试用例变量和临时变量。

```yaml
# 设置变量
- action: store_variable
  name: "username"
  value: "test_user"
  scope: "global"  # global, test_case, temp
  description: "存储用户名"

# 使用变量
- action: fill
  selector: "username_input"
  value: "${username}"
  description: "输入用户名"

# 变量表达式计算
- if: "${{ ${count} > 5 }}"
  then:
  # 当 count 大于 5 时执行的步骤
```

## 最佳实践

### 用例组织与管理

1. **模块化组织**
    - 按功能模块组织测试用例
    - 将常用操作封装为可复用模块
    - 使用标签对用例进行分类

2. **命名规范**
    - 使用描述性的用例名称，如 `test_login_valid_credentials`
    - 元素ID采用功能描述性命名，如 `login_button`
    - 测试步骤添加清晰的描述信息

3. **数据管理**
    - 使用变量文件管理测试数据，避免硬编码
    - 分离测试数据与测试逻辑
    - 使用参数化实现数据驱动测试

### 编写技巧

1. **元素定位**
    - 优先使用ID、CSS选择器等稳定的定位方式
    - 避免使用绝对路径和索引定位
    - 为复杂元素添加详细注释

2. **等待策略**
    - 使用显式等待而非固定等待时间
    - 为关键操作添加适当的超时时间
    - 利用自适应等待机制提高测试稳定性

3. **断言与验证**
    - 每个关键步骤后添加验证
    - 使用精确的断言而非模糊的检查
    - 在流程转换点添加状态验证

4. **错误处理**
    - 添加适当的错误捕获和恢复机制
    - 为失败用例提供详细的错误信息
    - 实现智能重试机制处理闪现问题

## 常用命令

### 测试运行命令

```bash
# 基本运行
$ python test_runner.py --project demo

# 使用标记筛选测试用例
$ python test_runner.py --project demo --marker smoke
$ python test_runner.py --project demo -m "smoke and login"
$ python test_runner.py --project demo -m "not slow"

# 使用关键字筛选测试用例
$ python test_runner.py --project demo --keyword login
$ python test_runner.py --project demo -k "login or register"
$ python test_runner.py --project demo -k "test_user and not admin"

# 组合使用标记和关键字
$ python test_runner.py --project demo -m smoke -k login

# 指定浏览器和环境
$ python test_runner.py --project demo --browser firefox --env test

# 有头模式运行（用于调试）
$ python test_runner.py --project demo --headed

# 运行特定测试文件
$ python test_runner.py --project demo --test-file login_test.yaml
```

### 命令行参数说明

| 参数 | 短参数 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--marker` | `-m` | string | None | 只运行特定标记的测试用例，支持pytest标记表达式 |
| `--keyword` | `-k` | string | None | 只运行匹配关键字的测试用例，支持pytest关键字表达式 |
| `--headed` | 无 | bool | True | 是否以有头模式运行浏览器 |
| `--browser` | 无 | enum | chromium | 指定浏览器（chromium/firefox/webkit） |
| `--env` | 无 | enum | prod | 指定环境（dev/test/stage/prod） |
| `--project` | 无 | string | demo | 指定项目名称 |
| `--base-url` | 无 | string | 空 | 指定基础URL，覆盖配置文件中的设置 |
| `--test-file` | 无 | string | 空 | 指定要运行的测试文件 |
| `--no-parallel` | 无 | bool | False | 禁用并行执行 |

### 标记（Marker）使用说明

标记用于对测试用例进行分类和筛选，常用的标记包括：

- `smoke`: 冒烟测试用例
- `regression`: 回归测试用例
- `slow`: 执行时间较长的测试用例
- `fast`: 执行时间较短的测试用例
- `critical`: 关键功能测试用例
- `login`: 登录相关测试用例
- `payment`: 支付相关测试用例

标记表达式支持逻辑运算符：
- `and`: 逻辑与，例如 `smoke and login`
- `or`: 逻辑或，例如 `login or register`
- `not`: 逻辑非，例如 `not slow`
- 括号: 用于分组，例如 `(smoke or regression) and not slow`

### 关键字（Keyword）使用说明

关键字筛选基于测试用例的名称、描述等文本内容进行匹配：

- 支持部分匹配：`login` 会匹配包含"login"的所有测试用例
- 支持逻辑运算符：`and`、`or`、`not`
- 支持括号分组：`(login or register) and not admin`
- 大小写敏感：需要注意测试用例名称的大小写

### 其他工具命令

```bash
# 导出依赖清单
$ poetry export -f requirements.txt --output requirements.txt

# 录制测试脚本
$ playwright codegen "https://example.com"

# 代码格式化
$ poetry run black .

# 检查重复元素和用例
$ python check_duplicates.py
```

## 元素定位技巧

### 元素提取工具

- **Chrome插件**: SelectorsHub
- **PyCharm插件**: Test Automation
- **Playwright录制功能**: 自动生成元素定位符
- **AI辅助**: 使用ChatGPT或DeepSeek分析HTML并生成定位符

### 元素定位最佳实践

1. **优先使用稳定定位符**
    - 优先级: ID > 数据属性 > CSS选择器 > XPath
    - 避免使用索引和绝对路径

2. **使用语义化命名**
    - 元素ID应描述其功能而非位置
    - 例如: `login_button` 而非 `button_1`

3. **添加详细注释**
    - 为复杂元素添加清晰的描述
    - 说明元素的用途和位置

### 代码规范

- 遵循 PEP 8 Python 代码风格指南
- 为所有新功能添加测试
- 保持文档和代码注释的同步更新

## 常见问题

### 安装问题

**Q: 安装依赖时出现错误**

A: 尝试以下解决方案：

1. 确保您使用的是 Python 3.10 或更高版本
2. 更新 Poetry: `pip install --upgrade poetry`
3. 清除 Poetry 缓存: `poetry cache clear --all pypi`

**Q: Playwright 浏览器安装失败**

A: 手动安装浏览器：

```bash
python -m playwright install chromium
```

### 运行问题

**Q: 测试运行不稳定，经常失败**

A: 可能的原因和解决方案：

1. 增加等待时间或使用显式等待
2. 检查元素定位符是否稳定
3. 在调试模式下运行以获取更多信息

**Q: 如何调试复杂的测试用例？**

A: 使用以下方法：

1. 添加 `page.pause()` 暂停浏览器
2. 使用有头模式运行: `python test_runner.py --project demo --headed`
3. 检查生成的日志和截图

### 其他问题

**Q: 如何实现数据驱动测试？**

A: 请参考文档中的"变量管理"部分，使用全局变量或测试用例变量来实现数据驱动。

**Q: 如何添加自定义操作？**

A: 可以通过扩展 `test_step_executor.py` 添加新的操作类型，或者使用模块化测试片段封装复杂操作。

## 相关资源

- [录制文档](https://test-crdqcu2hkpbr.feishu.cn/docx/YpIRdgOXGo1CQdxp1cacxwGbnZd?from=from_copylink)
- [Playwright 官方文档](https://playwright.dev/python/docs/intro)
- [PyTest 文档](https://docs.pytest.org/)
