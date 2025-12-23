"""
测试 LLM 客户端配置

验证 LangChain 和 LLM API 配置是否正确
"""

import sys
from src.processor.llm_client import get_llm_client, chat
from src.config.settings import settings


def test_configuration():
    """测试配置是否正确"""
    print("=" * 80)
    print("LLM 配置测试")
    print("=" * 80)

    print("\n配置信息:")
    print(f"  - API URL: {settings.LLM_API_URL}")
    print(f"  - Model: {settings.LLM_MODEL}")
    print(f"  - API Key: {settings.LLM_API_KEY[:20]}..." if settings.LLM_API_KEY else "  - API Key: 未配置")

    if not settings.LLM_API_KEY:
        print("\n❌ 错误: LLM_API_KEY 未配置")
        print("请在 .env 文件中设置 LLM_API_KEY")
        return False

    print("\n" + "=" * 80)
    return True


def test_simple_chat():
    """测试简单聊天"""
    print("\n测试 1: 简单聊天")
    print("-" * 80)

    try:
        client = get_llm_client()
        print("✓ LLM 客户端初始化成功")

        print("\n发送测试消息: '你好，请用一句话介绍自己。'")
        response = client.chat("你好，请用一句话介绍自己。")

        print(f"\n✓ LLM 响应:")
        print(f"  {response}")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False


def test_template_chat():
    """测试模板聊天"""
    print("\n" + "=" * 80)
    print("测试 2: 模板聊天")
    print("-" * 80)

    try:
        client = get_llm_client()

        template = "请分析这条推文的主题和情绪：\n\n{tweet_content}"
        variables = {
            "tweet_content": "今天发布了一个新的开源项目，希望能帮助到更多开发者！"
        }

        print(f"\n模板: {template}")
        print(f"变量: {variables}")

        response = client.chat_with_template(
            template=template,
            variables=variables,
            system_message="你是一个专业的推文分析助手，擅长分析推文的主题和情绪。",
        )

        print(f"\n✓ LLM 响应:")
        print(f"  {response}")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False


def test_convenience_function():
    """测试便捷函数"""
    print("\n" + "=" * 80)
    print("测试 3: 便捷函数")
    print("-" * 80)

    try:
        print("\n使用便捷函数 chat() 发送消息...")
        response = chat(
            user_message="请列举 3 个 Python 编程的最佳实践，每个用一句话说明。",
            system_message="你是一个 Python 编程专家。",
        )

        print(f"\n✓ LLM 响应:")
        print(f"  {response}")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 25 + "LLM 客户端测试" + " " * 39 + "║")
    print("╚" + "═" * 78 + "╝")

    # 测试配置
    if not test_configuration():
        return

    # 测试简单聊天
    test1_passed = test_simple_chat()

    # 测试模板聊天
    test2_passed = test_template_chat()

    # 测试便捷函数
    test3_passed = test_convenience_function()

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"  测试 1 (简单聊天): {'✓ 通过' if test1_passed else '✗ 失败'}")
    print(f"  测试 2 (模板聊天): {'✓ 通过' if test2_passed else '✗ 失败'}")
    print(f"  测试 3 (便捷函数): {'✓ 通过' if test3_passed else '✗ 失败'}")

    all_passed = test1_passed and test2_passed and test3_passed
    print(f"\n{'✓ 所有测试通过！' if all_passed else '✗ 部分测试失败'}")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
