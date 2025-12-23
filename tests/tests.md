# tests 目录

## 目录作用

存储项目的测试代码。

## 说明

本目录用于存放单元测试、集成测试和端到端测试代码。

## 测试框架

推荐使用 pytest 作为测试框架。

## 测试结构（规划）

```
tests/
├── unit/           # 单元测试
│   ├── test_crawler.py
│   ├── test_storage.py
│   └── test_processor.py
├── integration/    # 集成测试
│   ├── test_crawler_storage.py
│   └── test_end_to_end.py
└── fixtures/       # 测试数据和 fixtures
    └── sample_tweets.json
```

## 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/unit/test_crawler.py

# 显示详细输出
pytest -v tests/
```

## 注意事项

- 测试代码应该独立于生产环境
- 使用模拟数据，避免依赖真实外部服务
- 保持测试的快速和可重复性
