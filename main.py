"""
macOS Stealth Browser — Amazon 商品信息提取
提供两种模式：
  1. Agent 模式（需要 LLM API，智谱 GLM 驱动）
  2. Playwright 模式（零 API 成本，纯 DOM 提取）
"""

import asyncio
import sys


def show_menu():
    print("=" * 50)
    print("  Amazon 商品信息提取")
    print("=" * 50)
    print("  [1] Agent 模式  — 智谱 GLM 驱动，智能提取")
    print("  [2] Playwright 模式 — 零 API 成本，纯 DOM 提取")
    print("  [0] 退出")
    print("=" * 50)


async def run_agent_mode():
    from agent_mode import run as agent_run
    await agent_run()


async def run_playwright_mode():
    from playwright_mode import run as pw_run
    await pw_run()


async def main():
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "1":
            await run_agent_mode()
        elif mode == "2":
            await run_playwright_mode()
        else:
            print(f"未知模式: {mode}")
            print("用法: python main.py [1|2]")
        return

    show_menu()
    choice = input("请选择模式 [1/2/0]: ").strip()
    if choice == "1":
        await run_agent_mode()
    elif choice == "2":
        await run_playwright_mode()
    elif choice == "0":
        print("退出。")
    else:
        print("无效选择，退出。")


if __name__ == "__main__":
    asyncio.run(main())
