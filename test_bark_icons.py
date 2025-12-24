"""
测试不同的 Bark 推送图标

这个脚本会发送多条测试推送，每条使用不同的图标，
让你可以直观地看到不同图标的效果，选择你最喜欢的。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.notification.bark_client import get_bark_client
import time

# 测试 key
TEST_KEY = "https://api.day.app/rHptkyHMnXTwb479svYRoV/"

# 可用的图标选项（Apple Emoji PNG）
ICON_OPTIONS = [
    {
        "name": "💰 钱袋",
        "url": "https://em-content.zobj.net/source/apple/391/money-bag_1f4b0.png",
        "description": "经典的金钱象征，适合财经类消息"
    },
    {
        "name": "🪙 金币",
        "url": "https://em-content.zobj.net/source/apple/391/coin_1fa99.png",
        "description": "金币图标，直接代表加密货币"
    },
    {
        "name": "💵 美元纸币",
        "url": "https://em-content.zobj.net/source/apple/391/dollar-banknote_1f4b5.png",
        "description": "美元纸币，适合美元相关消息"
    },
    {
        "name": "📈 上涨图表",
        "url": "https://em-content.zobj.net/source/apple/391/chart-increasing_1f4c8.png",
        "description": "上涨趋势图表，适合利好消息"
    },
    {
        "name": "💎 钻石",
        "url": "https://em-content.zobj.net/source/apple/391/gem-stone_1f48e.png",
        "description": "钻石手（Diamond Hands），加密社区流行象征"
    },
    {
        "name": "🚀 火箭",
        "url": "https://em-content.zobj.net/source/apple/391/rocket_1f680.png",
        "description": "To the moon! 加密社区常用，表示价格飞涨"
    },
    {
        "name": "⚡ 闪电",
        "url": "https://em-content.zobj.net/source/apple/391/high-voltage_26a1.png",
        "description": "闪电网络象征，也代表快速/高能量"
    },
    {
        "name": "🎯 靶心",
        "url": "https://em-content.zobj.net/source/apple/391/direct-hit_1f3af.png",
        "description": "目标达成，精准信息"
    },
]


def main():
    print("=" * 80)
    print("Bark 推送图标预览测试")
    print("=" * 80)
    print()
    print("将依次发送不同图标的测试推送，请查看你的 iOS 设备...")
    print(f"使用测试 key: {TEST_KEY}")
    print()
    print("⚠️  注意：每条推送间隔 3 秒，请耐心等待")
    print("=" * 80)
    print()

    bark_client = get_bark_client()

    for i, icon in enumerate(ICON_OPTIONS, 1):
        print(f"[{i}/{len(ICON_OPTIONS)}] 正在发送: {icon['name']}")
        print(f"  说明: {icon['description']}")
        print(f"  URL: {icon['url']}")

        result = bark_client.send_notification(
            bark_url=TEST_KEY,
            title=f"{icon['name']} 图标测试",
            content=f"这是 {icon['name']} 图标的推送效果\n\n{icon['description']}",
            url="https://x.com",
            icon=icon['url'],
            sound="default",
            group="Icon-Test"
        )

        if result['success']:
            print(f"  ✅ 发送成功")
        else:
            print(f"  ❌ 发送失败: {result['message']}")

        print()

        # 最后一条不需要等待
        if i < len(ICON_OPTIONS):
            print("  等待 3 秒...")
            time.sleep(3)

    print("=" * 80)
    print("所有测试推送已发送完成！")
    print()
    print("📱 请查看你的 iOS 设备，选择你最喜欢的图标")
    print()
    print("修改方法：")
    print("1. 在 Streamlit 配置页面（推送配置 -> 推送图标）")
    print("2. 或修改 .env 文件中的 BARK_PUSH_ICON 变量")
    print("=" * 80)


if __name__ == "__main__":
    main()
