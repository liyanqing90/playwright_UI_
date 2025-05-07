# 导入重构后的模块
from src.step_actions.step_executor import StepExecutor as StepExecutorImpl

# 为了兼容性，保留原来的类名
StepExecutor = StepExecutorImpl
