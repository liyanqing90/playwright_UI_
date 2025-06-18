# 快速上手指南

## 概述

本指南将帮助新手快速理解并上手之家UI自动化测试框架。通过本指南，您将学会如何安装、配置和编写您的第一个自动化测试用例。

## 1. 环境准备

### 1.1 系统要求

- Python 3.10+
- Node.js 14+ (用于Playwright)
- 操作系统: Windows 10+, macOS 10.15+, Ubuntu 18.04+

### 1.2 安装步骤

#### 步骤1: 克隆项目

```bash
git clone <项目地址>
cd zhijia_ui
```

#### 步骤2: 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

#### 步骤3: 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install
```

#### 步骤4: 验证安装

```bash
# 运行示例测试
pytest test_data/demo/cases/demo.yaml -v
```

## 2. 项目结构理解

### 2.1 核心目录结构

```
zhijia_ui/
├── config/                  # 配置文件目录
│   ├── env_config.yaml      # 环境配置
│   ├── test_config.yaml     # 测试配置
│   └── performance_config.yaml # 性能配置
├── src/                     # 框架核心代码
│   ├── automation/          # 自动化执行引擎
│   │   ├── commands/        # 命令实现
│   │   ├── runner.py        # 测试运行器
│   │   └── step_executor.py # 步骤执行器
│   ├── core/                # 核心服务层
│   │   ├── base_page.py     # 基础页面类
│   │   ├── services/        # 服务组件
│   │   └── mixins/          # 混入功能
│   └── common/              # 公共组件
├── plugins/                 # 插件系统
├── test_data/               # 测试数据目录
│   └── demo/                # 示例项目
│       ├── cases/           # 测试用例定义
│       ├── data/            # 测试数据
│       ├── elements/        # 元素定义
│       └── vars/            # 变量定义
├── reports/                 # 测试报告
├── docs/                    # 文档
└── project_documentation/   # 项目详细文档
```

### 2.2 测试项目结构

每个测试项目都遵循以下结构：

```
test_data/your_project/
├── cases/
│   ├── case.yaml         # 测试用例列表
│   └── demo.yaml         # 具体用例定义
├── data/
│   └── data.yaml         # 测试数据和步骤
├── elements/
│   └── elements.yaml     # 页面元素定义
├── vars/
│   └── data.yaml         # 变量定义
└── modules/              # 可复用模块(可选)
    └── login.yaml        # 登录模块示例
```

## 3. 编写第一个测试用例

### 3.1 创建测试项目

#### 步骤1: 创建项目目录

```bash
mkdir -p test_data/my_first_test/{cases,data,elements,vars}
```

#### 步骤2: 定义测试用例列表

创建 `test_data/my_first_test/cases/case.yaml`:

```yaml
test_cases:
  - name: test_baidu_search
    depends_on: []
    fixtures: []
```

#### 步骤3: 定义页面元素

创建 `test_data/my_first_test/elements/elements.yaml`:

```yaml
elements:
  # 百度首页元素
  search_input: "#kw"                    # 搜索输入框
  search_button: "#su"                   # 搜索按钮
  search_results: ".result"              # 搜索结果
  first_result: ".result:first-child"    # 第一个结果
  
  # 通用元素
  page_title: "title"                    # 页面标题
  loading_indicator: ".loading"          # 加载指示器
```

#### 步骤4: 编写测试数据和步骤

创建 `test_data/my_first_test/data/data.yaml`:

```yaml
test_data:
  test_baidu_search:
    description: "百度搜索功能测试"
    variables:
      search_keyword: "Playwright自动化测试"
      expected_title: "Playwright自动化测试_百度搜索"
    
    steps:
      # 1. 打开百度首页
      - action: goto
        value: "https://www.baidu.com"
      
      # 2. 验证页面标题
      - action: assert_title_contains
        value: "百度"
      
      # 3. 输入搜索关键词
      - action: fill
        selector: "search_input"
        value: "${search_keyword}"
      
      # 4. 点击搜索按钮
      - action: click
        selector: "search_button"
      
      # 5. 等待搜索结果加载
      - action: wait_for_selector
        selector: "search_results"
        timeout: 10000
      
      # 6. 验证搜索结果
      - action: assert_visible
        selector: "search_results"
      
      # 7. 验证页面标题包含搜索关键词
      - action: assert_title_contains
        value: "${search_keyword}"
      
      # 8. 存储第一个搜索结果的文本
      - action: store_text
        selector: "first_result"
        variable: "first_result_text"
        scope: "test_case"
      
      # 9. 输出搜索结果
      - action: log_info
        value: "第一个搜索结果: ${first_result_text}"
```

#### 步骤5: 定义变量(可选)

创建 `test_data/my_first_test/vars/data.yaml`:

```yaml
variables:
  # 全局变量
  base_url: "https://www.baidu.com"
  default_timeout: 10000
  
  # 测试环境配置
  test_env: "staging"
  
  # 用户数据
  test_users:
    - username: "testuser1"
      password: "password123"
    - username: "testuser2"
      password: "password456"
### 3.2 运行测试

#### 基本运行方式

```bash
# 使用pytest直接运行
pytest test_data/my_first_test/cases/case.yaml -v

# 使用test_runner.py运行（推荐）
python test_runner.py --project my_first_test

# 运行测试并生成报告
python test_runner.py --project my_first_test
```

#### 使用标记和关键字筛选

```bash
# 使用标记筛选测试用例
python test_runner.py --project my_first_test --marker smoke
python test_runner.py --project my_first_test -m "smoke and login"

# 使用关键字筛选测试用例
python test_runner.py --project my_first_test --keyword login
python test_runner.py --project my_first_test -k "login or register"

# 组合使用标记和关键字
python test_runner.py --project my_first_test -m smoke -k login
```

#### 其他常用参数

```bash
# 有头模式运行（用于调试）
python test_runner.py --project my_first_test --headed

# 指定浏览器
python test_runner.py --project my_first_test --browser firefox

# 指定环境
python test_runner.py --project my_first_test --env test
```

# 查看Allure报告

allure serve reports

```

## 4. 常用操作示例

### 4.1 基础操作

```yaml
steps:
  # 页面导航
  - action: goto
    value: "https://example.com"
  
  # 点击元素
  - action: click
    selector: "#submit-btn"
  
  # 填写表单
  - action: fill
    selector: "#username"
    value: "testuser"
  
  # 选择下拉框
  - action: select
    selector: "#country"
    value: "China"
  
  # 等待元素
  - action: wait_for_selector
    selector: ".loading"
    timeout: 5000
  
  # 截图
  - action: screenshot
    value: "test_screenshot.png"
```

### 4.2 断言操作

```yaml
steps:
  # 文本断言
  - action: assert_text
    selector: ".welcome-msg"
    value: "欢迎登录"
  
  # 文本包含断言
  - action: assert_text_contains
    selector: ".error-msg"
    value: "用户名不能为空"
  
  # 元素可见性断言
  - action: assert_visible
    selector: ".success-icon"
  
  # 元素不存在断言
  - action: assert_not_exists
    selector: ".error-dialog"
  
  # URL断言
  - action: assert_url
    value: "https://example.com/dashboard"
  
  # 标题断言
  - action: assert_title_contains
    value: "用户中心"
```

### 4.3 变量操作

```yaml
steps:
  # 存储文本到变量
  - action: store_text
    selector: ".user-id"
    variable: "current_user_id"
    scope: "test_case"
  
  # 存储属性到变量
  - action: store_attribute
    selector: "#data-element"
    attribute: "data-value"
    variable: "element_data"
  
  # 使用变量
  - action: fill
    selector: "#search"
    value: "用户ID: ${current_user_id}"
  
  # 设置变量
  - action: store_variable
    variable: "test_status"
    value: "running"
    scope: "global"
```

### 4.4 流程控制

#### 条件分支

```yaml
steps:
  - action: store_text
    selector: ".user-role"
    variable: "user_role"
  
  # 条件执行
  - if: "${user_role} == 'admin'"
    then:
      - action: click
        selector: ".admin-panel"
      - action: assert_visible
        selector: ".admin-menu"
    else:
      - action: assert_not_exists
        selector: ".admin-panel"
```

#### 循环操作

```yaml
steps:
  # 定义循环数据
  - action: store_variable
    variable: "test_items"
    value: ["item1", "item2", "item3"]
  
  # 循环执行
  - for_each: "${test_items}"
    steps:
      - action: fill
        selector: "#search"
        value: "${item}"
      - action: click
        selector: "#search-btn"
      - action: assert_text_contains
        selector: ".results"
        value: "${item}"
```

#### 模块复用

创建模块 `test_data/my_first_test/modules/login.yaml`:

```yaml
name: "用户登录模块"
description: "通用的用户登录流程"

steps:
  - action: goto
    value: "${base_url}/login"
  
  - action: fill
    selector: "#username"
    value: "${username}"
  
  - action: fill
    selector: "#password"
    value: "${password}"
  
  - action: click
    selector: "#login-btn"
  
  - action: wait_for_selector
    selector: ".dashboard"
    timeout: 10000
```

使用模块:

```yaml
steps:
  # 使用登录模块
  - use_module: "login"
    params:
      username: "admin"
      password: "admin123"
  
  # 继续其他操作
  - action: click
    selector: ".user-menu"
```

## 5. 配置说明

### 5.1 全局配置

编辑 `config/test_config.yaml`:

```yaml
# 基础配置
timeout: 30000              # 默认超时时间(毫秒)
type_delay: 100             # 输入延迟(毫秒)
polling_interval: 500       # 轮询间隔(毫秒)

# 重试配置
retry:
  max_attempts: 3           # 最大重试次数
  delay: 1000              # 重试延迟(毫秒)

# 截图配置
screenshot:
  on_failure: true         # 失败时截图
  directory: "screenshots" # 截图目录
  quality: 80             # 截图质量(1-100)

# 报告配置
report:
  evidence_dir: "evidence" # 证据目录
  allure_results: "reports" # Allure报告目录

# 浏览器配置
browser:
  headless: false          # 是否无头模式
  viewport:
    width: 1920
    height: 1080
  slow_mo: 0              # 慢动作延迟(毫秒)
```

### 5.2 环境配置

创建 `.env` 文件:

```env
# 测试环境
TEST_ENV=staging
BASE_URL=https://staging.example.com

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=testdb

# API配置
API_BASE_URL=https://api.staging.example.com
API_TOKEN=your_api_token_here

# 其他配置
DEBUG=true
LOG_LEVEL=INFO
```

## 6. 调试技巧

### 6.1 启用调试模式

```bash
# 启用详细日志
pytest test_data/my_first_test/cases/case.yaml -v -s --log-cli-level=DEBUG

# 在失败时保持浏览器打开
pytest test_data/my_first_test/cases/case.yaml --headed --slowmo=1000
```

### 6.2 添加调试步骤

```yaml
steps:
  # 暂停执行，等待手动操作
  - action: pause
    value: 5000  # 暂停5秒
  
  # 输出调试信息
  - action: log_info
    value: "当前页面URL: ${current_url}"
  
  # 截图用于调试
  - action: screenshot
    value: "debug_screenshot_${timestamp}.png"
  
  # 输出页面源码
  - action: log_page_source
```

### 6.3 常见问题排查

#### 元素找不到

```yaml
# 增加等待时间
- action: wait_for_selector
  selector: ".dynamic-element"
  timeout: 15000

# 使用更稳定的选择器
- action: click
  selector: "[data-testid='submit-button']"  # 推荐
  # 而不是: ".btn.btn-primary"  # 不稳定
```

#### 时间相关问题

```yaml
# 等待页面加载完成
- action: wait_for_load_state
  value: "networkidle"

# 等待特定条件
- action: wait_for_function
  value: "() => document.readyState === 'complete'"
```

## 7. 最佳实践

### 7.1 元素选择器

```yaml
# 推荐：使用稳定的属性
selector: "[data-testid='user-menu']"
selector: "#unique-id"

# 避免：使用易变的样式类
selector: ".btn.btn-primary.large"  # 样式可能会变
selector: "div > div > span"        # 结构可能会变
```

### 7.2 变量命名

```yaml
variables:
  # 好的命名
  user_login_email: "test@example.com"
  max_retry_count: 3
  api_response_timeout: 30000
  
  # 避免的命名
  data1: "some value"  # 不明确
  temp: 123           # 不描述性
```

### 7.3 测试数据管理

```yaml
# 使用有意义的测试数据
variables:
  valid_user:
    username: "valid_test_user"
    email: "valid@example.com"
    password: "ValidPass123!"
  
  invalid_user:
    username: ""  # 空用户名
    email: "invalid-email"  # 无效邮箱
    password: "123"  # 弱密码
```

### 7.4 错误处理

```yaml
steps:
  # 使用软断言，不会立即停止测试
  - action: soft_assert_text
    selector: ".warning"
    value: "警告信息"
  
  # 在关键步骤后添加验证
  - action: click
    selector: "#submit"
  
  - action: wait_for_selector
    selector: ".success-message"
    timeout: 10000
```

## 8. 进阶功能

### 8.1 API测试集成

```yaml
steps:
  # 发送API请求
  - action: api_request
    method: "POST"
    url: "${api_base_url}/users"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer ${api_token}"
    body: |
      {
        "username": "${test_username}",
        "email": "${test_email}"
      }
    variable: "api_response"
  
  # 验证API响应
  - action: assert_api_response
    status_code: 201
    response_contains: "${test_username}"
```

### 8.2 数据库验证

```yaml
steps:
  # 执行数据库查询
  - action: db_query
    query: "SELECT * FROM users WHERE username = '${test_username}'"
    variable: "db_result"
  
  # 验证数据库结果
  - action: assert_db_result
    expected_count: 1
    contains:
      username: "${test_username}"
      status: "active"
```

### 8.3 文件操作

```yaml
steps:
  # 上传文件
  - action: upload_file
    selector: "#file-input"
    file_path: "test_data/sample.pdf"
  
  # 下载文件
  - action: download_file
    trigger_selector: "#download-btn"
    save_path: "downloads/report.pdf"
    variable: "download_path"
```

## 9. 持续集成

### 9.1 GitHub Actions配置

创建 `.github/workflows/ui-tests.yml`:

```yaml
name: UI Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        playwright install
    
    - name: Run tests
      run: |
        pytest test_data/*/cases/*.yaml --alluredir=allure-results
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: allure-results
        path: allure-results/
```

### 9.2 Docker支持

创建 `Dockerfile`:

```dockerfile
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install -r requirements.txt

# 安装Playwright
RUN playwright install --with-deps

# 复制项目文件
COPY . .

# 运行测试
CMD ["pytest", "test_data/", "--alluredir=reports"]
```

## 10. 总结

通过本快速上手指南，您已经学会了：

1. ✅ **环境搭建**: 安装和配置测试框架
2. ✅ **项目结构**: 理解框架的组织方式
3. ✅ **编写测试**: 创建您的第一个测试用例
4. ✅ **常用操作**: 掌握基础的测试操作
5. ✅ **流程控制**: 使用条件、循环和模块
6. ✅ **配置管理**: 自定义框架行为
7. ✅ **调试技巧**: 排查和解决问题
8. ✅ **最佳实践**: 编写高质量的测试
9. ✅ **进阶功能**: API测试、数据库验证等
10. ✅ **持续集成**: 集成到CI/CD流程

### 下一步建议

1. **深入学习**: 阅读 `project_documentation/` 中的详细文档
2. **实践练习**: 为您的实际项目编写测试用例
3. **社区参与**: 参与框架的改进和扩展
4. **分享经验**: 与团队分享测试自动化的最佳实践

### 获取帮助

- 📖 查看详细文档: `project_documentation/`
- 🐛 报告问题: 在项目仓库创建Issue
- 💬 技术讨论: 加入项目讨论群
- 📧 联系维护者: 发送邮件获取支持

祝您使用愉快！🎉