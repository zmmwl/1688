"""1688 选品：使用 DrissionPage 提取商品信息（零 API 成本）

使用方式：
  1. 运行程序，DrissionPage 打开浏览器
  2. 首次运行需在浏览器中登录 1688（可能需要短信验证 + 滑块验证）
  3. 登录成功后程序自动开始搜索，中途如遇验证码会暂停等待
"""

import json
import os
import re
import time
from datetime import datetime

from DrissionPage import Chromium, ChromiumOptions

from categories import CATEGORIES, Category

BROWSER_DATA_DIR = os.path.join(os.path.dirname(__file__), ".browser_data_1688")


def create_browser():
    """创建 DrissionPage 浏览器实例"""
    co = ChromiumOptions()
    co.headless(False)
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_argument("--lang=zh-CN")
    co.set_argument("--no-sandbox")
    co.set_user_agent(
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/134.0.0.0 Safari/537.36"
    )
    co.set_user_data_path(BROWSER_DATA_DIR)
    return Chromium(co)


def has_captcha(page):
    """检测页面是否有验证码"""
    try:
        text = page.ele("tag:body").text or ""
        if len(text) < 500 and "滑块" in text and "验证" in text:
            return True
        for sel in ["#nocaptcha", ".nc-container", "#baxia-dialog"]:
            el = page.ele(sel, timeout=0.5)
            if el:
                return True
        return False
    except Exception:
        return False


def wait_for_captcha_done(page, timeout=180):
    """等待用户手动完成验证码"""
    print("    [CAPTCHA] 请在浏览器中手动完成验证...")
    print(f"    (等待最长 {timeout} 秒)")
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(3)
        try:
            if not has_captcha(page):
                print("    [OK] 验证通过!")
                time.sleep(2)
                return True
        except Exception:
            return False
    print("    [WARN] 验证等待超时")
    return False


def wait_for_login(page, timeout=300):
    """等待用户完成登录"""
    print("    等待登录完成（最长 5 分钟）...")
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(3)
        try:
            if "login" not in page.url.lower():
                time.sleep(2)
                return True
        except Exception:
            return False
    print("    [WARN] 登录等待超时")
    return False


def extract_products(page, top_n):
    """用 DrissionPage 原生 API 提取商品数据"""
    products = []
    seen_titles = set()

    links = page.eles('css:a[href*="offerId"]')
    seen_ids = set()
    for link in links:
        href = link.attr('href') or ''
        m = re.search(r'offerId=(\d+)', href)
        if not m:
            continue
        offer_id = m.group(1)

        # 向上找包含价格和完整信息的容器（从父元素开始，最多6层）
        container = link.parent()
        container_text = ""
        for _ in range(6):
            if not container:
                break
            ct = (container.text or "")
            if len(ct) > 50 and '¥' in ct:
                container_text = ct
                break
            container = container.parent()

        if not container_text:
            continue

        # 提取标题
        lines = [l.strip() for l in container_text.split('\n') if l.strip()]
        title = ""
        for line in lines:
            if (len(line) > 8 and '¥' not in line and '旺旺' not in line
                    and '回头' not in line and '找相似' not in line
                    and '验厂' not in line and '综合服务' not in line
                    and '采购' not in line and '纠纷' not in line
                    and '退换' not in line and '品质' not in line
                    and '物流' not in line):
                title = line
                break

        if not title or len(title) < 5:
            continue

        # 跳过公司名作为标题的情况
        if re.search(r'(?:有限公司|贸易公司|工厂|商行|经营部|科技|电商|用品|商贸|实业|管理)$', title) and len(title) < 20:
            continue

        # 按标题去重
        if title in seen_titles:
            continue
        seen_titles.add(title)

        # 价格
        price_match = re.search(r'¥\s*([\d.]+)', container_text)
        price = f"{price_match.group(1)}元" if price_match else ""

        # 起订量
        moq_match = re.search(r'≥(\d+)', container_text)
        min_order = f"≥{moq_match.group(1)}个" if moq_match else ""
        if not min_order:
            moq_match = re.search(r'(\d+)\s*[件个只套包盒条对张]?\s*起', container_text)
            min_order = moq_match.group(0) if moq_match else ""

        # 供应商
        company_match = re.search(r'([\u4e00-\u9fa5]+(?:有限公司|贸易公司|工厂|商行|经营部|科技|电商|用品|商贸|实业|管理))', container_text)
        supplier = company_match.group(1) if company_match else ""

        # 销量
        sales_match = re.search(r'([\d.]+万?\+?件|已售[\d.]+万?\+?件|成交[\d.]+万?\+?元)', container_text)
        sales_volume = sales_match.group(1) if sales_match else ""

        # 回头率
        rate_match = re.search(r'回头率(\d+%)', container_text)
        repurchase_rate = f"回头率{rate_match.group(1)}" if rate_match else ""

        products.append({
            "title": title[:200],
            "price": price,
            "min_order": min_order,
            "supplier": supplier,
            "sales_volume": sales_volume,
            "repurchase_rate": repurchase_rate,
            "product_url": f"https://detail.1688.com/offer/{offer_id}.html",
        })

        if len(products) >= top_n:
            break

    return products


def filter_products(products, category):
    """按品类条件过滤"""
    filtered = []
    for p in products:
        price_str = p.get("price", "")
        if price_str:
            m = re.search(r"([\d.]+)", price_str)
            if m:
                price = float(m.group(1))
                if price < category.price_min or price > category.price_max:
                    continue
        filtered.append(p)
    return filtered


def output_results(all_results):
    """输出并保存结果"""
    total = sum(len(v) if isinstance(v, list) else 0 for v in all_results.values())

    output = {
        "source": "1688",
        "mode": "drissionpage",
        "timestamp": datetime.now().isoformat(),
        "total_categories": len(all_results),
        "total_products": total,
        "categories": [],
    }

    for cat_name, data in all_results.items():
        if isinstance(data, dict) and "error" in data:
            output["categories"].append({"name": cat_name, "error": data["error"], "products": []})
        else:
            products = data if isinstance(data, list) else []
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


def run(top_n=10, category_ids=None):
    """
    搜索 1688 商品信息

    Args:
        top_n: 每个品类提取的商品数量，默认 10
        category_ids: 指定品类 ID 列表，None 表示全部
    """
    categories = CATEGORIES
    if category_ids:
        categories = [c for c in categories if c.id in category_ids]

    print(f"\n[1688 选品] 品类: {len(categories)} 个 | 每品类 Top {top_n}")

    browser = create_browser()
    page = browser.latest_tab

    # 登录检查：访问首页
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

            # 提取
            products = extract_products(page, top_n * 2)

            # 过滤
            if products:
                products = filter_products(products, category)
            # 重编 rank
            for i, p in enumerate(products[:top_n]):
                p["rank"] = i + 1
            all_results[category.name] = products[:top_n]
            print(f"    提取到 {len(all_results[category.name])} 个商品")

        except Exception as e:
            print(f"    [ERROR] {e}")
            all_results[category.name] = {"error": str(e)}

        # 品类间间隔（防风控）
        if i < len(categories):
            delay = 5 + (i % 4) * 2
            print(f"    等待 {delay} 秒...")
            time.sleep(delay)

    browser.quit()
    output_results(all_results)
