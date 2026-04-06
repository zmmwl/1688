"""
macOS stealth browser script using browser-use + Playwright + 智谱AI.
Combines 方案B (browser-use stealth) with 方案A adapted for macOS
(native headed mode — no Xvfb needed on macOS).
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from browser_use import Agent, Browser, BrowserProfile, ChatOpenAI
from browser_use.browser.profile import ViewportSize


AMAZON_URL = "https://www.amazon.com/-/zh/dp/B01NBKTPTS"


async def main():
    # ── 方案B: browser-use stealth mode ──
    profile = BrowserProfile(
        headless=False,           # macOS 有原生显示器，直接 headed 模式
        window_size=ViewportSize(width=1920, height=1080),
        disable_security=True,    # 绕过 navigator.webdriver 检测等
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/134.0.0.0 Safari/537.36"
        ),
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-features=AutomationControlled",
            "--disable-infobars",
            "--disable-notifications",
            "--lang=zh-CN",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ],
        user_data_dir=os.path.join(os.path.dirname(__file__), ".browser_data"),
    )

    # ── 创建 LLM（智谱 GLM，禁用 structured output 兼容智谱） ──
    llm = ChatOpenAI(
        model="glm-4-plus",
        temperature=0.1,
        api_key=os.environ["ZHIPUAI_API_KEY"],
        base_url="https://open.bigmodel.cn/api/paas/v4",
        dont_force_structured_output=True,
    )

    # ── 创建 Agent ──
    agent = Agent(
        task=(
            f"访问 {AMAZON_URL}，提取该商品页面的以下信息并以 JSON 格式返回：\n"
            "1. 商品名称 (title)\n"
            "2. 价格 (price)\n"
            "3. 评分 (rating)\n"
            "4. 评论数量 (review_count)\n"
            "5. 商品描述/卖点前5条 (top_features)\n"
            "6. 是否有货 (availability)\n"
            "如果遇到验证码或人机验证，请描述看到的内容。"
        ),
        llm=llm,
        browser_profile=profile,
        use_vision=False,
        max_failures=3,
        max_actions_per_step=5,
    )

    print("=" * 60)
    print("macOS Stealth Browser — browser-use + Playwright + 智谱GLM")
    print("=" * 60)
    print(f"Target: {AMAZON_URL}")
    print(f"LLM: glm-4-plus (Zhipu)")
    print(f"Mode: headed (native macOS display)")
    print(f"Stealth: AutomationControlled disabled + custom args")
    print("=" * 60)
    print()

    result = await agent.run()

    print()
    print("=" * 60)
    print("RESULT")
    print("=" * 60)
    print(result)
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
