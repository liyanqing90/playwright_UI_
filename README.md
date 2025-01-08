## 使用Poetry

本项目使用 [Poetry](https://python-poetry.org/) 进行依赖管理。要安装依赖项并运行项目，请按照以下步骤操作：

### 安装Poetry

如果您尚未安装Poetry，请按照官方安装说明进行安装：<https://python-poetry.org/docs/#installation>

### 安装依赖项

运行以下命令安装依赖项：
```bash
poetry install


“仅输出支持 Playwright 操作的元素定位方式，格式为 Playwright 支持的定位方式（如 text=、placeholder=、role=，xpath ,ccs之类的定位方式
等），不包含其他操作。”

steps:

- action: "goto"
  target: "${base_url}/login"
- action: "fill"
  target: "username_field"
  value: "${username}"
- action: "click"
  target: "login_button"
- action: "wait_for_selector"
  target: "dashboard"
- action: "expect_visible"
  target: "dashboard"
- action: "expect_text"
  target: "login_error_message"
  value: "Invalid credentials"
- action: "select_option"
  target: "dropdown_field"
  value: "option_value"
- action: "hover"
  target: "menu_item"
- action: "wait_for_selector"
  target: "modal_window"
- action: "dismiss_modal"
  target: "modal_window"
- action: "screenshot"
  target: "page_screenshot.png"
- action: "scroll_into_view"
  target: "footer"
- action: "drag_and_drop"
  target: "source_element"
  destination: "target_element"
- action: "accept_popup"
  target: "true"
- action: "wait_for_navigation"
  target: "true"
- action: "expect_disabled"
  target: "submit_button"
- action: "expect_enabled"
  target: "submit_button"
- action: "clear"
  target: "username_field"
- action: "focus"
  target: "username_field"
- action: "blur"
  target: "username_field"
- action: "dblclick"
  target: "button_field"
- action: "press"
  target: "username_field"
  key: "Enter"
- action: "set_input_files"
  target: "file_input"
  files: "/path/to/file"
- action: "wait_for_timeout"
  target: "3000"  # Wait for 3 seconds
