"""共享浏览器配置：反检测参数、User-Agent、窗口大小"""

import os

CHROME_STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=AutomationControlled",
    "--disable-infobars",
    "--disable-notifications",
    "--lang=zh-CN",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/134.0.0.0 Safari/537.36"
)

VIEWPORT = {"width": 1920, "height": 1080}

BROWSER_DATA_DIR = os.path.join(os.path.dirname(__file__), ".browser_data")

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
window.chrome = { runtime: {} };
"""
