"""
macOS Stealth Browser — 商品信息提取
提供四种模式：
  Amazon:
    1. Agent 模式（智谱 GLM 驱动）
    2. Playwright 模式（零 API 成本）
  1688 选品:
    3. Agent 模式（智谱 GLM 驱动，15 品类批量搜索）
    4. Playwright 模式（零 API 成本，15 品类批量搜索）
"""

import asyncio
import sys


def parse_args(argv):
    """解析命令行参数，返回 (mode, kwargs)"""
    if not argv:
        return None, {}
    mode = argv[0]
    kwargs = {}
    i = 1
    while i < len(argv):
        if argv[i] == "--top" and i + 1 < len(argv):
            kwargs["top_n"] = int(argv[i + 1])
            i += 2
        elif argv[i] == "--categories" and i + 1 < len(argv):
            kwargs["category_ids"] = [int(x) for x in argv[i + 1].split(",")]
            i += 2
        else:
            i += 1
    return mode, kwargs


def show_menu():
    print("=" * 50)
    print("  商品信息提取工具")
    print("=" * 50)
    print("  Amazon:")
    print("  [1] Agent 模式  — 智谱 GLM 驱动，智能提取")
    print("  [2] Playwright 模式 — 零 API 成本，纯 DOM 提取")
    print("  1688 选品:")
    print("  [3] Agent 模式  — 智谱 GLM 驱动，15 品类批量搜索")
    print("  [4] Playwright 模式 — 零 API 成本，15 品类批量搜索")
    print("  [0] 退出")
    print("=" * 50)


async def run_agent_mode():
    from agent_mode import run as agent_run
    await agent_run()


async def run_playwright_mode():
    from playwright_mode import run as pw_run
    await pw_run()


async def run_agent_mode_1688(top_n=10, category_ids=None):
    from agent_mode_1688 import run as agent_run_1688
    await agent_run_1688(top_n=top_n, category_ids=category_ids)


async def run_playwright_mode_1688(top_n=10, category_ids=None):
    from playwright_mode_1688 import run as pw_run_1688
    await pw_run_1688(top_n=top_n, category_ids=category_ids)


HANDLERS = {
    "1": lambda: run_agent_mode(),
    "2": lambda: run_playwright_mode(),
    "3": lambda kw: run_agent_mode_1688(**kw),
    "4": lambda kw: run_playwright_mode_1688(**kw),
}


async def main():
    args = sys.argv[1:]
    mode, kwargs = parse_args(args)

    if mode:
        if mode in ("1", "2"):
            await HANDLERS[mode]()
        elif mode in ("3", "4"):
            await HANDLERS[mode](kwargs)
        else:
            print(f"未知模式: {mode}")
            print("用法: python main.py [1|2|3|4] [--top N] [--categories 1,2,3]")
        return

    show_menu()
    choice = input("请选择模式 [1/2/3/4/0]: ").strip()
    if choice == "0":
        print("退出。")
    elif choice in HANDLERS:
        if choice in ("1", "2"):
            await HANDLERS[choice]()
        else:
            # 交互模式下的 1688 参数
            top_input = input("每品类提取数量 (默认10): ").strip()
            top_n = int(top_input) if top_input.isdigit() else 10
            cat_input = input("指定品类 ID，逗号分隔 (默认全部): ").strip()
            category_ids = [int(x) for x in cat_input.split(",") if x.strip().isdigit()] if cat_input.strip() else None
            await HANDLERS[choice]({"top_n": top_n, "category_ids": category_ids})
    else:
        print("无效选择，退出。")


if __name__ == "__main__":
    asyncio.run(main())
