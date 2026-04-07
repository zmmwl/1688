"""Agent 模式：DrissionPage 浏览器控制 + 智谱 GLM 智能提取

使用方式：
  1. 运行程序，DrissionPage 打开浏览器
  2. 首次运行需在浏览器中登录 1688
  3. 登录成功后程序自动开始搜索
"""

import asyncio
import json
import os
import re
import time
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

from categories import CATEGORIES, Category
from playwright_mode_1688 import (
    create_browser,
    has_captcha,
    wait_for_captcha_done,
    wait_for_login,
)

load_dotenv()

BROWSER_DATA_DIR = os.path.join(os.path.dirname(__file__), ".browser_data_1688")


def build_extraction_prompt(page_text: str, category: Category, top_n: int) -> str:
    """构建 LLM 提取 prompt，从页面文本中提取商品信息"""
    return (
        f"你是一个电商数据提取助手。以下是从 1688 搜索结果页面提取的原始文本，"
        f"每段文本对应一个商品。请从中提取商品信息。\n\n"
        f"输出格式为 JSON 数组，每个元素包含以下字段：\n"
        f"- title: 商品标题（字符串）\n"
        f"- price: 价格（数字，如 3.5）\n"
        f"- min_order: 起订量（字符串，如 '≥3个'）\n"
        f"- supplier: 供应商名称（字符串）\n"
        f"- sales_volume: 销量信息（字符串，如 '已售1000+件'）\n"
        f"- repurchase_rate: 回头率（字符串，如 '回头率58%'）\n\n"
        f"输出样例：\n"
        f'[{{"title": "超软粉扑干湿两用不吃粉", "price": 3.5, "min_order": "≥3个", '
        f'"supplier": "广州某某化妆品有限公司", "sales_volume": "已售1000+件", '
        f'"repurchase_rate": "回头率58%"}}]\n\n'
        f"注意事项：\n"
        f"1. 从每段文本中提取一个商品，最多返回 {top_n} 个\n"
        f"2. 跳过标题明显是公司名（如以'有限公司''工厂''商行'结尾且长度<20）的条目\n"
        f"3. 如果某个字段在文本中找不到，填空字符串 ''\n"
        f"4. 即使商品不完全满足理想条件，只要有商品标题和价格就应返回\n"
        f"5. 仅返回 JSON 数组，不要包含任何其他文字、解释或 markdown 标记\n\n"
        f"--- 页面原始文本 ---\n"
        f"{page_text}"
    )


def extract_page_text(page, top_n: int) -> str:
    """从 DrissionPage 页面中提取搜索结果的原始文本"""
    from DrissionPage.common import By

    # 获取所有商品链接
    links = page.eles('css:a[href*="offerId"]')
    seen_ids = set()
    texts = []

    for link in links[:top_n * 3]:  # 多取一些给 LLM 筛选
        href = link.attr('href') or ''
        m = re.search(r'offerId=(\d+)', href)
        if not m:
            continue
        offer_id = m.group(1)
        if offer_id in seen_ids:
            continue
        seen_ids.add(offer_id)

        # 向上找包含完整信息的容器
        container = link.parent()
        container_text = ""
        for _ in range(6):
            if not container:
                break
            ct = container.text or ""
            if len(ct) > 50 and '¥' in ct:
                container_text = ct
                break
            container = container.parent()

        if container_text:
            texts.append(container_text.strip())

    return "\n---\n".join(texts)


def parse_json_from_llm(content: str, category: Category, top_n: int) -> list:
    """从 LLM 返回的文本中解析 JSON 商品列表"""
    if not content:
        return []

    json_match = re.search(r'\[.*\]', content, re.DOTALL)
    if not json_match:
        return []

    try:
        products = json.loads(json_match.group())
        if isinstance(products, list):
            for p in products[:top_n]:
                p["category"] = category.name
                p["category_id"] = category.id
                # 标准化 product_url
                if "product_url" in p and p["product_url"]:
                    p["product_url"] = p["product_url"]
            return products[:top_n]
    except json.JSONDecodeError:
        pass

    return []


def call_llm(prompt: str) -> str:
    """调用智谱 GLM 提取商品信息"""
    client = OpenAI(
        api_key=os.environ["ZHIPUAI_API_KEY"],
        # base_url="https://open.bigmodel.cn/api/paas/v4",
        base_url="https://open.bigmodel.cn/api/coding/paas/v4",
        
    )

    response = client.chat.completions.create(
        # model="glm-4-plus",
        model="glm-5-turbo",
        temperature=0.1,
        messages=[
            {"role": "system", "content": "你是一个专业的电商数据提取助手。只返回 JSON 数组，不要其他文字。"},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
    )

    return response.choices[0].message.content or ""


def output_results(all_results, mode="agent"):
    """输出并保存结果"""
    total_products = sum(
        len(v.get("products", [])) if isinstance(v, dict) else len(v)
        for v in all_results.values()
    )

    output = {
        "source": "1688",
        "mode": mode,
        "timestamp": datetime.now().isoformat(),
        "total_categories": len(all_results),
        "total_products": total_products,
        "categories": [],
    }

    for cat_name, data in all_results.items():
        if isinstance(data, dict) and "error" in data:
            output["categories"].append({"name": cat_name, "error": data["error"], "products": []})
        else:
            products = data if isinstance(data, list) else data.get("products", [])
            output["categories"].append({
                "name": cat_name,
                "product_count": len(products),
                "products": products,
            })

    json_str = json.dumps(output, ensure_ascii=False, indent=2)
    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(json_str)
    print("=" * 60)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output_1688_{ts}.json"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(json_str)
    print(f"\n结果已保存到: {filename}")


async def run(top_n=10, category_ids=None):
    """
    搜索 1688 商品信息（Agent 模式：DrissionPage + GLM）

    Args:
        top_n: 每个品类提取的商品数量，默认 10
        category_ids: 指定品类 ID 列表，None 表示全部
    """
    categories = CATEGORIES
    if category_ids:
        categories = [c for c in categories if c.id in category_ids]

    print(f"\n[Agent 1688] DrissionPage + GLM-4-plus | 品类: {len(categories)} 个 | 每品类 Top {top_n}")

    browser = create_browser()
    page = browser.latest_tab

    # 登录检查
    print("\n  正在打开 1688 首页...")
    page.get("https://www.1688.com")
    time.sleep(3)

    if "login" in page.url.lower():
        print("\n  ========================================")
        print("  请在浏览器中登录 1688（可能需要短信验证）")
        print("  登录后程序自动继续（最长 5 分钟）")
        print("  ========================================\n")
        wait_for_login(page, timeout=300)
        page.get("https://www.1688.com")
        time.sleep(3)

    print("  [OK] 就绪，开始搜索\n")

    all_results = {}

    for i, category in enumerate(categories, 1):
        print(f"[{i}/{len(categories)}] {category.name}")

        try:
            # 搜索
            page.get(category.search_url)
            time.sleep(8)

            # 处理验证码
            if has_captcha(page):
                wait_for_captcha_done(page, timeout=180)
                page.get(category.search_url)
                time.sleep(8)

            # 处理登录重定向
            if "login" in page.url.lower():
                print("    被重定向到登录页，等待重新登录...")
                wait_for_login(page, timeout=300)
                page.get(category.search_url)
                time.sleep(8)

            # 滚动加载更多内容
            page.run_js("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            # 提取页面文本
            page_text = extract_page_text(page, top_n)

            if not page_text:
                print(f"    页面无商品数据")
                all_results[category.name] = []
                continue

            print(f"    提取到 {page_text.count('---')} 个商品卡片，调用 GLM 解析...")

            # 调用 LLM 智能提取
            prompt = build_extraction_prompt(page_text, category, top_n)

            for attempt in range(1, 3):
                try:
                    llm_response = call_llm(prompt)
                    products = parse_json_from_llm(llm_response, category, top_n)

                    if products:
                        # 添加 rank
                        for idx, p in enumerate(products):
                            p["rank"] = idx + 1
                        all_results[category.name] = products
                        print(f"    GLM 提取到 {len(products)} 个商品")
                        break
                    else:
                        print(f"    第 {attempt} 次 LLM 返回无有效结果")
                        print(f"    LLM 原始响应（前300字）: {(llm_response or '')[:300]}")
                        if attempt < 2:
                            await asyncio.sleep(2)
                except Exception as e:
                    print(f"    第 {attempt} 次 LLM 调用出错: {e}")
                    if attempt < 2:
                        await asyncio.sleep(3)
            else:
                all_results[category.name] = []

        except Exception as e:
            print(f"    [ERROR] {e}")
            all_results[category.name] = {"error": str(e)}

        # 品类间间隔
        if i < len(categories):
            delay = 5 + (i % 4) * 2
            print(f"    等待 {delay} 秒...")
            time.sleep(delay)

    browser.quit()
    output_results(all_results, mode="agent")
