# 之家UI自动化测试框架使用示例

本文档提供了之家UI自动化测试框架的使用示例，帮助您快速上手和理解框架的核心功能。

## 基本用法

### 1. 创建测试用例

测试用例使用YAML格式定义，包含测试步骤和元素定位信息。

**示例测试用例 (test_login.yaml)**:

```yaml
name: 登录测试
description: 验证用户登录功能
elements:
  username_input: "#username"
  password_input: "#password"
  login_button: "button[type='submit']"
  welcome_message: ".welcome-message"

steps:
  - action: navigate
    value: "/login"
    description: 打开登录页面

  - action: fill
    selector: username_input
    value: "testuser"
    description: 输入用户名

  - action: fill
    selector: password_input
    value: "password123"
    description: 输入密码

  - action: click
    selector: login_button
    description: 点击登录按钮

  - action: assert_text
    selector: welcome_message
    value: "欢迎, testuser"
    description: 验证登录成功
```

### 2. 运行测试

使用命令行运行测试：

```bash
python test_runner.py --project my_project --test login
```

### 3. 查看测试报告

测试完成后，可以查看Allure报告：

```bash
allure serve allure-results
```

## 高级功能

### 1. 变量使用

可以在测试用例中使用变量，支持全局变量、测试用例变量和临时变量。

**示例**:

```yaml
steps:
  - action: store_variable
    name: username
    value: "testuser"
    scope: test_case
    description: 存储用户名变量

  - action: fill
    selector: username_input
    value: "${username}"
    description: 使用变量填充用户名
```

### 2. 条件执行

支持条件分支，根据条件执行不同的步骤。

**示例**:

```yaml
steps:
  - action: store_text
    selector: ".user-role"
    variable_name: user_role
    description: 获取用户角色
    
  - if: "${user_role} == 'admin'"
    then:
      - action: click
        selector: ".admin-panel"
        description: 点击管理员面板
    else:
      - action: click
        selector: ".user-profile"
        description: 点击用户资料
```

### 3. 循环执行

支持循环执行步骤，可以遍历列表或范围。

**示例**:

```yaml
steps:
  - action: store_variable
    name: items
    value: [ "item1", "item2", "item3" ]
    description: 存储项目列表

  - for_each: "${items}"
    as: item
    do:
      - action: click
        selector: ".item[data-id='${item}']"
        description: 点击项目
```

### 4. 模块化

支持模块化测试，可以在测试用例中引用其他模块。

**模块定义 (login_module.yaml)**:

```yaml
steps:
  - action: navigate
    value: "/login"
    description: 打开登录页面

  - action: fill
    selector: username_input
    value: "${username}"
    description: 输入用户名

  - action: fill
    selector: password_input
    value: "${password}"
    description: 输入密码

  - action: click
    selector: login_button
    description: 点击登录按钮
```

**使用模块**:

```yaml
steps:
  - use_module: login_module
    params:
      username: "testuser"
      password: "password123"
    description: 执行登录模块
```

### 5. 数据驱动测试

支持数据驱动测试，可以使用不同的数据集执行相同的测试逻辑。

**示例**:

```yaml
name: 数据驱动登录测试
description: 使用不同的用户数据测试登录功能
data:
  - username: user1
    password: pass1
    expected: 欢迎, user1
  - username: user2
    password: pass2
    expected: 欢迎, user2

steps:
  - action: navigate
    value: "/login"
    description: 打开登录页面

  - action: fill
    selector: username_input
    value: "${username}"
    description: 输入用户名

  - action: fill
    selector: password_input
    value: "${password}"
    description: 输入密码

  - action: click
    selector: login_button
    description: 点击登录按钮

  - action: assert_text
    selector: welcome_message
    value: "${expected}"
    description: 验证登录成功
```

## 更多示例

更多示例请参考 `examples` 目录下的示例文件。
