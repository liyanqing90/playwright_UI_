# 之家UI自动化测试框架文档

欢迎使用之家UI自动化测试框架！本文档提供了框架的详细说明、使用示例和最佳实践指南。

## 目录

- [架构文档](architecture/README.md)
- [使用示例](examples/README.md)
- [最佳实践](best_practices/README.md)

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/zhijia_ui.git
cd zhijia_ui

# 安装依赖
pip install -r requirements.txt
```

### 运行测试

```bash
# 运行单个测试
python test_runner.py --project your_project --test your_test

# 运行所有测试
python test_runner.py --project your_project

# 生成报告
allure serve allure-results
```

## 主要特性

- **YAML格式测试用例**: 使用简单的YAML格式定义测试用例，无需编写代码
- **页面对象模式**: 使用页面对象模式封装页面元素和操作，提高代码复用性
- **模块化设计**: 支持模块化测试，可以在测试用例中引用其他模块
- **数据驱动**: 支持数据驱动测试，可以使用不同的数据集执行相同的测试逻辑
- **变量管理**: 支持全局变量、测试用例变量和临时变量，方便数据共享和传递
- **条件执行**: 支持条件分支，根据条件执行不同的步骤
- **循环执行**: 支持循环执行步骤，可以遍历列表或范围
- **丰富的断言**: 提供多种断言方式，满足不同的验证需求
- **详细的报告**: 集成Allure报告，提供详细的测试结果和执行过程

## 贡献

欢迎贡献代码、报告问题或提出改进建议。请遵循以下步骤：

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](../LICENSE) 文件。
