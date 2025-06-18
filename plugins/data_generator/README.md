# 数据生成插件

## 概述

数据生成插件提供了丰富的测试数据生成功能，支持多种数据类型和自定义模板，帮助测试人员快速生成所需的测试数据。

## 功能特性

- **多种数据类型支持**：基础类型、业务类型、数字类型、文本类型、网络类型、UUID类型
- **批量数据生成**：支持一次性生成多条数据
- **自定义模板**：支持注册自定义数据生成模板
- **国际化支持**：支持中文和英文数据生成
- **可配置性**：通过配置文件灵活调整插件行为

## 支持的数据类型

### 基础类型

- `name` - 姓名
- `email` - 邮箱地址
- `phone` / `mobile` - 手机号码
- `address` - 地址
- `datetime` - 日期时间
- `date` - 日期
- `time` - 时间

### 业务类型

- `user_id` - 用户ID
- `order_id` - 订单ID
- `product_code` - 产品编码
- `company_name` - 公司名称
- `bank_card` - 银行卡号
- `id_card` - 身份证号

### 数字类型

- `integer` - 整数
- `float` - 浮点数
- `price` - 价格

### 文本类型

- `text` - 文本
- `paragraph` - 段落
- `sentence` - 句子
- `word` - 单词

### 网络类型

- `url` - URL地址
- `domain` - 域名
- `ip` - IP地址

### UUID类型

- `uuid` / `uuid4` - UUID

## 使用方法

### 基本用法

```yaml
# 生成单个数据
- action: generate_data
  value: name
  variable: user_name

# 生成带参数的数据
- action: generate_data
  value:
    type: email
    params:
      domain: example.com
  variable: user_email

# 生成整数
- action: generate_data
  value:
    type: integer
    params:
      min: 1
      max: 100
  variable: random_number
```

### 批量生成

```yaml
# 批量生成数据
- action: generate_batch_data
  value:
    type: name
    count: 10
    params:
      prefix: "测试用户"
  variable: user_list

# 批量生成订单ID
- action: generate_batch_data
  value:
    type: order_id
    count: 5
    params:
      prefix: "ORD"
  variable: order_ids
```

### 自定义模板

```yaml
# 注册自定义模板
- action: register_data_template
  value:
    name: custom_product_id
    generator: "'PROD' + str(random.randint(10000, 99999))"
    description: "自定义产品ID"
    category: "business"

# 使用自定义模板
- action: generate_data
  value: custom_product_id
  variable: product_id
```

## 参数说明

### 通用参数

所有数据类型都支持以下通用参数：

- 无通用参数（每种类型有自己的特定参数）

### 特定参数

#### name（姓名）

- `prefix` - 前缀，默认为"新零售"
- `english` - 是否生成英文姓名，默认为false

#### email（邮箱）

- `domain` - 指定域名

#### phone/mobile（手机号）

- `default` - 默认手机号，默认为"18210233933"

#### datetime/date/time（日期时间）

- `format` - 日期格式，默认为"%Y-%m-%d"
- `today` - 是否使用今天的日期，默认为true

#### user_id（用户ID）

- `prefix` - 前缀，默认为"USER"
- `length` - ID长度，默认为8

#### order_id（订单ID）

- `prefix` - 前缀，默认为"ORD"

#### product_code（产品编码）

- `prefix` - 前缀，默认为"PRD"
- `length` - 编码长度，默认为6

#### integer（整数）

- `min` - 最小值，默认为1
- `max` - 最大值，默认为1000

#### float（浮点数）

- `min` - 最小值，默认为0.0
- `max` - 最大值，默认为1000.0
- `decimals` - 小数位数，默认为2

#### price（价格）

- `min` - 最小价格，默认为1.0
- `max` - 最大价格，默认为10000.0

#### text（文本）

- `length` - 文本长度，默认为10

#### paragraph（段落）

- `sentences` - 句子数量，默认为5

#### sentence（句子）

- `words` - 单词数量，默认为10

## 配置文件

插件配置文件位于 `config.yaml`，可以调整以下设置：

```yaml
settings:
  enabled: true          # 是否启用插件
  locale: zh_CN         # 本地化设置
  seed: null            # 随机种子
  default_length: 10    # 默认长度

faker:
  locales:              # 支持的本地化
    - zh_CN
    - en_US
```

## 扩展开发

### 添加新的数据类型

```python
# 在插件中注册新的生成器
plugin.register_generator(
    "custom_type",
    lambda **kwargs: "custom_value",
    "自定义类型",
    "custom"
)
```

### 自定义生成器函数

```python
def custom_generator(**kwargs):
    # 自定义生成逻辑
    return "generated_value"

plugin.register_generator("my_type", custom_generator)
```

## 注意事项

1. **安全性**：自定义模板的生成器代码会被执行，请确保代码安全
2. **性能**：批量生成大量数据时注意内存使用
3. **唯一性**：某些数据类型（如UUID）保证唯一性，其他类型可能重复
4. **本地化**：根据locale设置生成相应语言的数据

## 版本历史

- v1.0.0 - 初始版本，支持基本数据类型生成

## 许可证

本插件遵循项目主许可证。