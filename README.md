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

`poetry export -f requirements.txt --output requirements.txt ` #导出requirements.txt

###

全息录制命令
`playwright codegen "https://tauth.autohome.com.cn/fe/zt/sso/login?appId=app_h5_live-assistant&productType=product_ahoh&backUrl=https%3A%2F%2Fenergyspace-c-test.autohome.com.cn%2Flive-assistant%2Fassistant"`

元素提取方式

- 使用chrome插件: SelectorsHub
- 使用pycharm 插件: Test Automation
- 使用playwright录制功能提取元素，或使用prompt 提取步骤及元素
- 复制HTML元素，使用prompt提取

推荐使用chatgpt、deepseek提取元素

根据HTML提取元素 prompt

``` prompt
请根据以下要求提取 HTML 中的元素，并以 YAML 格式输出：
1. 提取 HTML 中的元素。
2. 元素命名需符合 Python 变量命名规范（小写字母，单词之间用下划线分隔）。
3. 保留注释信息，描述每个字段的功能或用途。
4. 避免 YAML 将 `#` 解析为注释符号，确保字段值中的 `#` 被正确保留。
5. 每一项均单独命名
请按照以下 YAML 格式输出：

yaml
full_name_input: "input#fullName"  # 输入全名
join_input: "input#join"           # 追加文本并按下键盘 Tab
get_me_input: "input#getMe"        # 获取文本框内容
clear_me_input: "input#clearMe"    # 清除文本
no_edit_input: "input#noEdit"      # 确认编辑字段已禁用
dont_write_input: "input#dontwrite" # 确认文本为只读
```

录制脚本转化prompt

角色设定:

你是一个代码转换助手，负责将给定的代码片段转换为更规范的步骤描述，并提取特定的元素定位信息。

核心任务:

1. 元素定位提取: 从 elements 示例数据中，提取并列出所有 Playwright 可用的元素定位符。定位符格式必须严格符合 Playwright
   的规范（如 text=, placeholder=, role=, xpath, css 等），且仅包含定位信息本身，不包含其他任何操作、说明或上下文。
2. 步骤转换: 将 steps 示例数据中定义的代码步骤转换为 Playwright 的标准步骤描述。每个步骤描述应包含 action、selector（若适用）和
   value（若适用）三个属性：

- action: 根据下方的 代码方法对应关系，将原始代码中的动作转换为对应的 Playwright 标准方法名称。
- selector: 将原始代码中步骤的 selector 值替换为第一步中提取的对应定位符。
- value: 如果原始代码的步骤中有 value 值，则将其原样保留。

3. 输出格式: 请分两部分输出结果，第一部分输出提取的元素定位符，第二部分输出转换后的步骤描述。
   代码方法对应关系 (原始代码 -> Playwright):

```navigate -> page.goto
pause -> page.pause
click -> page.click
fill -> page.fill
press_key -> page.locator(selector).press
upload_file -> page.locator(selector).set_input_files
assert_visible -> page.is_visible
assert_text -> page.inner_text
store_variable -> variable_manager.set_variable
store_text -> page.inner_text
store_attribute -> page.get_attribute
refresh -> page.reload
hover -> page.hover
double_click -> page.dblclick
right_click -> page.click(button='right')
select_option -> page.select_option
drag_and_drop -> page.locator(source).drag_to(page.locator(target))
get_value -> page.input_value
scroll_into_view -> page.locator(selector).scroll_into_view_if_needed
scroll_to -> page.evaluate(f"window.scrollTo({x}, {y})")
focus -> page.focus
blur -> page.evaluate("element => element.blur()", page.locator(selector))
type -> page.locator(selector).type
clear -> page.locator(selector).clear
enter_frame -> page.frame_locator
exit_frame -> page.main_frame
accept_alert -> page.once("dialog", handle_dialog)
dismiss_alert -> page.once("dialog", handle_dialog)
switch_window -> page.context.pages
close_window -> page.close
wait_for_new_window -> page.context.expect_page
wait_for_element_hidden -> page.wait_for_selector(state="hidden")
```

示例数据 (YAML 格式, 仅用于演示，请不要将其作为输入进行处理):

```YAML
    page.goto("https://www.baidu.com/")
    page.locator('//span[@class="soutu-btn"]').first.click()
    page.locator('//input[@value="上传图片"]').click()
    page.locator('//input[@value="上传图片"]').set_input_files("2024_12_20_15_11_IMG_0238.PNG")

```

输出要求:

第一部分: Playwright 元素定位符 (每行一个定位符):

```yaml
#<这里输出从示例数据中提取的定位符>
elements:
  title: .title
  图片: //span[@class="soutu-btn"]
  上传: //input[@value="上传图片"]
```

第二部分: 转换后的步骤描述 (YAML 格式):

```YAML
steps:
   - action: goto
     value: "https://www.baidu.com"
   - action: click
     selector: 图片
   - action: upload
     selector: 上传
     value: "./files/demo/01.PNG"
   - action: <Playwright 方法名称>
     selector: <对应的定位符> (如果需要)
     value: <值> (如果需要)
   - ... (其他步骤)
  
```

重要提示:

- 请严格按照上述指令进行操作，确保输出结果的正确性和格式规范。
- 示例数据仅用于演示，请不要将其作为输入进行处理。 你应该使用这些示例数据进行转换，并按照指定的格式输出结果。
- 如果某个步骤不需要 selector 或 value 属性，则省略这些属性。
- 请将 wait 步骤的 action 保留为 wait, 不要转换为 playwright 的 api