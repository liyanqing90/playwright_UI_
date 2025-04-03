from datetime import datetime
from pathlib import Path
from typing import Optional

import allure
from playwright.sync_api import Page


class ReportHandler:
    def __init__(self, page: Page):
        self.page = page
        self.screenshot_dir = Path("reports/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def attach_screenshot(self, name: Optional[str] = None):
        """添加截图到报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = name or f"screenshot_{timestamp}"
        screenshot = self.page.screenshot()
        allure.attach(screenshot, name=name, attachment_type=allure.attachment_type.PNG)

    def attach_page_source(self):
        """添加页面源码到报告"""
        allure.attach(
            self.page.content(),
            name="page_source",
            attachment_type=allure.attachment_type.HTML,
        )
