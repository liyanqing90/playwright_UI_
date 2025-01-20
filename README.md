# Playwright UI 自动化测试框架

一个基于Playwright的UI自动化测试框架,支持多种方式编写和管理测试用例。

## 特性

- 基于Playwright实现,支持多种主流浏览器
- 支持YAML/Excel两种方式编写测试用例
- 内置40+种常用UI操作
- 支持多项目、多环境配置
- 完整的Page Object模式实现
- 灵活的变量管理和数据驱动
- 详细的操作日志和失败截图
- 集成Allure测试报告

## 安装

### 环境准备

1. 安装Python 3.8+
2. 安装Poetry（参考[官方文档](https://python-poetry.org/docs/#installation)）

### 安装依赖

```bash
poetry install
```

### 运行测试

运行所有测试：

```bash
poetry run pytest
```

运行单个测试文件：

```bash
poetry run pytest path/to/test_file.py
```

生成测试报告：

```bash
poetry run pytest --alluredir=reports
```

## 项目结构

```
playwright_UI/
├── config/                  # 配置文件
│   ├── cookie.json          # Cookie配置
│   ├── env_config.yaml      # 环境配置
│   ├── storage_state.json   # 浏览器存储状态
│   └── test_config.yaml     # 测试配置
├── evidence/                # 测试证据
│   └── screenshots/         # 截图
├── page_objects/            # 页面对象
│   └── base_page.py         # 基础页面类
├── reports/                 # 测试报告
├── src/                     # 源代码
│   ├── fixtures.py          # Pytest fixtures
│   ├── load_data.py         # 数据加载
│   ├── test_case_executor.py # 测试用例执行器
│   └── test_step_executor.py # 测试步骤执行器
├── test_data/               # 测试数据
│   ├── 新零售B端.xlsx       # Excel格式的测试数据，包含业务测试数据
│   ├── variables.json       # 全局变量定义，支持JSON格式的变量存储
│   ├── cases/               # 测试用例目录
│   │   └── cases.yaml       # YAML格式的测试用例定义，包含测试步骤和断言
│   ├── data/                # 测试数据目录
│   │   └── index.yaml       # 测试数据索引文件，用于管理测试数据集
│   └── elements/            # 页面元素目录
│       └── elements.yaml    # 页面元素定位器定义，支持多种定位方式
├── utils/                   # 工具类
│   ├── allure_logger.py     # Allure日志
│   ├── config.py            # 配置处理
│   ├── excel_handler.py     # Excel处理
│   ├── logger.py            # 日志处理
│   ├── report_handler.py    # 报告处理
│   ├── variable_manager.py  # 变量管理
│   └── yaml_handler.py      # YAML处理
├── conftest.py              # Pytest配置
├── create_structure.py      # 项目结构创建
├── poetry.lock              # Poetry依赖锁
├── pyproject.toml           # Poetry项目配置
├── pytest.ini               # Pytest配置
├── README.md                # 项目文档
└── test_runner.py           # 测试运行器
```

## 测试开发指南

### 测试用例编写

#### 用例文件结构

测试用例由三个核心文件协同定义：

1. `cases/cases.yaml` - 定义测试用例元数据
    - 用例名称
    - 前置条件（fixtures）
    - 依赖关系
    - 示例：
      ```yaml
      test_demo:
        description: "示例测试用例"
        fixtures: ["login"]
        depends_on: []
      ```

2. `data/index.yaml` - 定义测试步骤
    - 操作步骤序列
    - 操作类型（点击、输入、断言等）
    - 参数配置
    - 示例：
      ```yaml
      test_demo:
        steps:
          - action: goto
            value: "https://example.com"
          - action: click
            selector: "login_button"
      ```

3. `elements/elements.yaml` - 定义页面元素
    - 元素名称
    - 定位方式（CSS、XPath、Text等）
    - 示例：
      ```yaml
      login_button:  "button.login"
      ```

#### 用例编写流程

1. 在`cases/cases.yaml`中定义新用例
    - 指定用例名称
    - 配置前置条件和依赖

2. 在`elements/elements.yaml`中添加所需元素
    - 使用合适的定位方式
    - 添加描述信息

3. 在`data/index.yaml`中编写测试步骤
    - 按顺序添加操作步骤
    - 引用已定义的元素
    - 配置操作参数

#### 示例用例

```yaml
# cases/test_cases.yaml
login_test:
  description: "用户登录测试"
  fixtures: ["setup_browser"]
  depends_on: []
```

```yaml
# elements/elements.yaml
title:
  selector: ".title"
  description: "页面标题"

全城比价:
  selector: "text=全城比价"
  description: "全城比价按钮"

对比试驾:
  selector: "text=对比试驾"
  description: "对比试驾按钮"

旧车估值:
  selector: "text=旧车估值"
  description: "旧车估值按钮"

送充电桩:
  selector: "text=送充电桩"
  description: "送充电桩按钮"

到店领好礼:
  selector: "text=到店领好礼"
  description: "到店领好礼按钮"

询底价:
  selector: ".series-card__price > .btn:first-child"
  description: "询底价按钮"

查看更多:
  selector: "text=查看更多"
  description: "查看更多按钮"

热门车系弹框标题:
  selector: ".fill-info-popup-header-title"
  description: "热门车系弹框标题"

热门车系关闭:
  selector: ".fill-info-popup-close"
  description: "热门车系关闭按钮"
```

```yaml
# data/index.yaml
login_test:
  steps:
    - action: goto
      value: "https://example.com/login"
    - action: fill
      selector: "username_input"
      value: "username"
    - action: click
      selector: "login_button"
    - action: expect_visible
      selector: "welcome_message"
```

#### 最佳实践

1. 保持元素定义与页面结构一致
2. 使用描述性的元素名称
3. 将复杂操作拆分为多个简单步骤
4. 合理使用变量和参数化
5. 及时更新元素定位信息
6. 添加必要的断言步骤
7. 保持用例的独立性
8. 定期review和维护用例

### 最佳实践

1. 将页面元素定义在`test_data/elements/elements.yaml`中
2. 将测试用例定义在`test_data/data/index.yaml`中
3. 每个测试用例文件应专注于一个测试场景
4. 使用清晰的步骤描述和合理的断言
5. 充分利用Playwright的等待机制，避免使用固定等待时间
6. 保持用例文件简洁，单个文件不超过20个步骤
7. 使用描述性的步骤名称，便于维护和调试
8. 合理使用变量，避免硬编码
9. 及时清理测试数据，保持测试独立性
10. 定期review测试用例，保持与业务同步

```
配置文件优化

补充pytest.ini配置，添加常用配置项如：
测试标记（markers）
日志配置
并行测试配置
测试报告配置
测试框架优化

添加环境变量管理，支持多环境配置
实现配置优先级：命令行参数 > 环境变量 > 配置文件
添加测试数据驱动支持，优化test_data目录结构
报告系统优化

整合Allure报告，添加自定义步骤和附件
添加失败重试机制
实现测试结果通知（邮件/钉钉等）
代码结构优化

将page_objects重构为更清晰的页面对象模型
提取公共操作到base_page
添加元素定位器管理
持续集成

添加GitHub Actions CI配置
实现测试结果可视化
添加测试覆盖率统计
其他优化

添加类型注解
完善日志系统
添加API测试支持
实现测试数据生成工具
```

###

全息录制命令
`playwright codegen "https://tauth.autohome.com.cn/fe/zt/sso/login?appId=app_h5_live-assistant&productType=product_ahoh&backUrl=https%3A%2F%2Fenergyspace-c-test.autohome.com.cn%2Flive-assistant%2Fassistant"`