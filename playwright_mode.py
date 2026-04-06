"""Playwright 模式：零 API 成本，纯 DOM 选择器提取 Amazon 商品信息"""

import asyncio
import json
import os
from playwright.async_api import async_playwright


AMAZON_URL = "https://www.amazon.com/-/zh/dp/B01NBKTPTS"

# Amazon 商品页 DOM 选择器
SELECTORS = {
    "title": "#productTitle",
    "price": [
        "#corePrice_feature_div .a-price .a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        ".a-price-whole",
        "#price_inside_buybox",
    ],
    "rating": "#acrPopover .a-icon-alt",
    "review_count": "#acrCustomerReviewText",
    "features": "#feature-bullets ul li span.a-list-item",
    "availability": "#availability span",
}


async def extract_text(page, selectors):
    """依次尝试多个选择器，返回第一个匹配到的文本"""
    if isinstance(selectors, str):
        selectors = [selectors]
    for sel in selectors:
        try:
            el = await page.wait_for_selector(sel, timeout=5000)
            if el:
                text = (await el.text_content() or "").strip()
                if text:
                    return text
        except Exception:
            continue
    return None


async def run():
    print(f"\n[Playwright] 模式: headed | Stealth: 已启用 | API 成本: 0\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=AutomationControlled",
                "--disable-infobars",
                "--disable-notifications",
                "--lang=zh-CN",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/134.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )

        # 注入反检测脚本：隐藏 webdriver 标志
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
        """)

        page = await context.new_page()

        print(f"[Playwright] 正在访问 {AMAZON_URL} ...")
        await page.goto(AMAZON_URL, wait_until="domcontentloaded", timeout=30000)

        # 等待商品标题加载（说明页面主要内容已渲染）
        try:
            await page.wait_for_selector("#productTitle", timeout=15000)
        except Exception:
            # 可能遇到验证码
            content = await page.content()
            if "captcha" in content.lower() or "robot" in content.lower():
                print("[Playwright] 检测到验证码，等待 10 秒...")
                await asyncio.sleep(10)
            else:
                print("[Playwright] 页面加载超时，尝试继续提取...")

        # 滚动一次触发懒加载
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
        await asyncio.sleep(1)

        # 提取数据
        print("[Playwright] 正在提取商品信息...")

        title = await extract_text(page, SELECTORS["title"])
        price = await extract_text(page, SELECTORS["price"])
        rating_text = await extract_text(page, SELECTORS["rating"])
        review_text = await extract_text(page, SELECTORS["review_count"])
        availability = await extract_text(page, SELECTORS["availability"])

        # 提取 features 列表
        features = []
        try:
            feature_els = await page.query_selector_all(SELECTORS["features"])
            for el in feature_els:
                text = (await el.text_content() or "").strip()
                if text and len(text) > 5:
                    features.append(text)
        except Exception:
            pass

        # 清理评分格式 (如 "4.6 out of 5 stars" → "4.6")
        rating = None
        if rating_text:
            import re
            m = re.search(r"([\d.]+)", rating_text)
            if m:
                rating = m.group(1)

        # 清理评论数 (如 "52,339 ratings" → "52,339")
        review_count = None
        if review_text:
            import re
            m = re.search(r"([\d,]+)", review_text)
            if m:
                review_count = m.group(1)

        await browser.close()

        # 组装结果
        result = {
            "title": title,
            "price": price,
            "rating": rating,
            "review_count": review_count,
            "top_features": features[:5],
            "availability": availability,
        }

        print("\n" + "=" * 60)
        print("RESULT")
        print("=" * 60)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("=" * 60)
