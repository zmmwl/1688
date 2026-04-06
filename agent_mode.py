"""Agent 模式：browser-use + 智谱 GLM 驱动的智能浏览器爬虫"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from browser_use import Agent, Browser, BrowserProfile, ChatOpenAI
from browser_use.browser.profile import ViewportSize


AMAZON_URL = "https://www.amazon.com/-/zh/dp/B01NBKTPTS"


async def run():
    profile = BrowserProfile(
        headless=False,
        window_size=ViewportSize(width=1920, height=1080),
        disable_security=True,
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

    llm = ChatOpenAI(
        model="glm-4-plus",
        temperature=0.1,
        api_key=os.environ["ZHIPUAI_API_KEY"],
        base_url="https://open.bigmodel.cn/api/paas/v4",
        dont_force_structured_output=True,
    )

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

    print(f"\n[Agent] LLM: glm-4-plus | 模式: headed | Stealth: 已启用\n")

    result = await agent.run()

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    # 提取最终结果文本
    final = result.all_results[-1] if result.all_results else None
    if final and final.extracted_content:
        print(final.extracted_content)
    elif final and final.long_term_memory:
        print(final.long_term_memory)
    else:
        print(result)
    print("=" * 60)
