# processor 目录

## 目录作用

处理与分析层（预留 v3.0.0）。

## 说明

本目录预留用于实现推文内容处理和分析功能，包括：

### 1. 文本清洗（Rule-based）
- 去除 URL、表情符号、无效换行
- 去除 RT 标记、引用冗余
- 统一编码和时间格式

### 2. LLM 标签系统
- 输入：清洗后的推文正文 + 元数据
- 输出：
  - 主题标签（如：Crypto / AI / 宏观 / 项目）
  - 情绪标签（利好 / 利空 / 中性）
  - 信息类型（新闻 / 观点 / 传言）

### 3. 权重与等级计算
- 多因子加权模型：
  - 作者权重（KOL 等级、是否白名单）
  - 标签权重（关注主题加分）
  - 时效性（时间衰减函数）
  - 互动指标（若可获取）
- 最终映射为等级：S / A / B / C

## 规划

### 架构设计
```python
# 预期的模块结构
processor/
├── __init__.py
├── text_cleaner.py      # 文本清洗
├── llm_tagger.py        # LLM 标签系统
├── scorer.py            # 权重评分器
└── worker.py            # 处理 Worker（从 Redis 消费）
```

### 工作流程
1. Worker 从 Redis 队列消费 tweet_id
2. 从 PostgreSQL 读取原始推文
3. 文本清洗
4. 调用 LLM API 生成标签
5. 计算权重与等级
6. 更新 PostgreSQL：clean_content, tags, score, level, status=DONE

## 当前状态

该模块尚未实现，预计在 v3.0.0 版本开发。

## 参考资料

- 使用 OpenAI GPT API 或其他 LLM 服务
- 标签结构以 JSON 格式存储
- 支持后续规则或模型升级
