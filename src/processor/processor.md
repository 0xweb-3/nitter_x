# processor 目录

## 目录作用

处理与分析层，实现推文内容处理和分析功能。

## 已实现模块

### llm_client.py - LLM 客户端封装

提供统一的 LLM 调用接口，基于 LangChain 框架。

**主要功能**:
- 支持自定义 API 端点（兼容 OpenAI API 格式）
- 单例模式，避免重复初始化
- 提供多种调用方式：简单聊天、模板聊天、批量调用
- 完整的错误处理和日志记录

**主要方法**:
```python
# 简单聊天
def chat(user_message: str, system_message: Optional[str] = None, **kwargs) -> str:
    """发送聊天消息并获取响应"""
    pass

# 模板聊天
def chat_with_template(
    template: str,
    variables: Dict[str, Any],
    system_message: Optional[str] = None,
    **kwargs
) -> str:
    """使用模板发送消息（支持变量替换）"""
    pass

# 批量调用
def batch_chat(
    messages: List[str],
    system_message: Optional[str] = None,
    **kwargs
) -> List[str]:
    """批量发送消息（并发执行，提高效率）"""
    pass

# 获取单例
def get_llm_client() -> LLMClient:
    """获取 LLM 客户端单例"""
    pass
```

**使用示例**:
```python
from src.processor.llm_client import get_llm_client, chat

# 方式 1: 使用单例
client = get_llm_client()
response = client.chat("你好，请介绍一下自己。")

# 方式 2: 使用便捷函数
response = chat(
    user_message="请分析这条推文的情绪",
    system_message="你是一个专业的推文分析助手"
)

# 方式 3: 使用模板
response = client.chat_with_template(
    template="请分析这条推文：{content}",
    variables={"content": "今天天气真好！"},
    system_message="你是推文分析助手"
)
```

**配置要求**:
- `LLM_API_KEY`: API 密钥（必需）
- `LLM_API_URL`: API 端点 URL（默认：https://api.openai.com/v1）
- `LLM_MODEL`: 模型名称（默认：gpt-3.5-turbo）

**测试**:
```bash
# 测试 LLM 客户端配置
python test_llm.py
```

### prompts.py - 提示词统一管理

统一管理所有 LLM 调用的提示词，便于后续调优。

**主要类**:
- `TweetProcessingPrompts`: 推文处理相关提示词
  - `SYSTEM_GRADE`: 分级系统消息
  - `SYSTEM_PROCESS`: 处理系统消息
  - `GRADE_DEFINITIONS`: 分级标准定义
  - `get_grade_prompt(content)`: 获取分级提示词
  - `get_process_prompt(content)`: 获取详细处理提示词

**使用示例**:
```python
from src.processor.prompts import TweetProcessingPrompts

prompts = TweetProcessingPrompts

# 获取分级提示词
grade_prompt = prompts.get_grade_prompt("推文内容...")

# 获取处理提示词
process_prompt = prompts.get_process_prompt("推文内容...")
```

### tweet_processor.py - 推文处理器

完整的推文处理流程，包括分级、翻译、摘要、关键词提取和向量化。

**分级标准** (P0-P6，价格影响导向):
- **P0**: 直接、可验证、已发生的价格驱动事件（最高优先级）
  - 已经发生或即将确定发生，必然触发资金行为
  - 例如：Coinbase/Binance现货上架或下架、中/美/韩监管措施、闪崩/插针、系统性流动性枯竭、已确认黑客攻击、安全漏洞披露、稳定币脱锚/协议被盗
  - 价格影响：强烈、短期立刻反应（分钟级~小时级波动）

- **P1**: 高概率触发价格的"强信号事件"
  - 尚未完全落地，但市场共识认为"极可能发生"
  - 例如：美联储宣布加息/降息、美股大涨/大跌、代币销毁、ETF审批情况、代币解锁/回购计划、代币经济模型调整
  - 价格影响：提前交易（buy the rumor），波动可持续数天

- **P2**: 结构性、长期价格影响因素（慢变量）
  - 不会立刻拉盘/砸盘，但会改变价格中枢
  - 例如：顶级交易所上币强预期、官宣主网上线时间、BTC减半、大额融资披露、巨鲸转账、L2成本下降
  - 价格影响：慢热、趋势型，适合中长期配置判断

- **P3**: 宏观 & 政策级，对crypto整体估值有影响
  - 不直接针对crypto，但影响风险资产定价
  - 例如：美联储预期加息/降息、CPI/非农/PCE、美元流动性变化、全球性金融事件
  - 价格影响：全市场联动，对BTC/ETH权重更高

- **P4**: 行业、叙事、情绪层面的信息
  - 会影响市场"讲什么故事"，但资金反应不稳定
  - 例如：AI+Crypto叙事、RWA/DePIN/Restaking热度、大佬喊单、VC报告
  - 价格影响：高度依赖情绪，容易过期

- **P5**: 信息噪音（相关但基本不影响价格）
  - 和crypto有关，但几乎不改变任何资金决策
  - 例如：项目PR合作、普通AMA/采访、社区治理投票、已消化的旧消息
  - 价格影响：极低

- **P6**: 可直接舍弃（无价格影响）
  - 例如：无链上/资金/政策影响的内容、单纯观点输出

**处理流程**:
1. 对所有推文进行分级（P0-P6）
2. 对 P0/P1/P2 级推文进行详细处理：
   - 语言检测
   - 非中文自动翻译为中文
   - 生成 50 字以内中文摘要
   - 提取 3-5 个关键词
   - 生成摘要的向量表示（用于后续相似度检索）

**主要方法**:
```python
def process_tweet(tweet_id: str, content: str, author: str = "") -> Dict[str, Any]:
    """
    完整处理一条推文

    Returns:
        {
            "tweet_id": "推文ID",
            "grade": "P0/P1/P2/P3/P4/P5/P6",
            "summary_cn": "中文摘要（≤30字）",
            "keywords": ["关键词1", "关键词2", ...],
            "translated_content": "翻译内容（如果原文非中文）",
            "embedding": [0.1, 0.2, ...],  # 向量
            "processing_time_ms": 处理耗时（毫秒）
        }
    """
```

**使用示例**:
```python
from src.processor.tweet_processor import get_tweet_processor

processor = get_tweet_processor()

result = processor.process_tweet(
    tweet_id="123456",
    content="Bitcoin hits new all-time high!",
    author="elonmusk"
)

print(f"分级: {result['grade']}")
print(f"摘要: {result['summary_cn']}")
print(f"关键词: {result['keywords']}")
```

### embedder.py - 文本向量化模块

使用本地 sentence-transformers 模型生成文本嵌入向量。

**使用的模型**:
- `paraphrase-multilingual-MiniLM-L12-v2`
- 支持多语言（包括中文）
- 向量维度: 384
- 模型自动缓存到 `data/models/` 目录

**主要方法**:
```python
# 生成单个文本向量
def generate_embedding(text: str) -> Optional[List[float]]:
    """生成文本的嵌入向量"""
    pass

# 批量生成向量
def generate_embeddings_batch(texts: List[str]) -> List[Optional[List[float]]]:
    """批量生成文本嵌入向量（效率更高）"""
    pass

# 计算相似度
def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    pass
```

**使用示例**:
```python
from src.processor.embedder import generate_embedding, calculate_similarity

# 生成向量
embedding1 = generate_embedding("比特币价格上涨")
embedding2 = generate_embedding("BTC突破新高")

# 计算相似度
similarity = calculate_similarity(embedding1, embedding2)
print(f"相似度: {similarity:.2f}")
```

## 使用指南

### 1. 处理单条推文（测试）

```bash
# 运行测试脚本
python test_tweet_processing.py
```

### 2. 批量处理推文（Worker）

```bash
# 启动处理 Worker（持续运行）
python process_worker.py
```

Worker 会：
- 每 5 秒检查一次待处理推文
- 每批处理 10 条推文
- 自动更新推文处理状态
- 保存处理结果到数据库

### 3. 查看处理结果（Streamlit）

```bash
# 启动 Streamlit
streamlit run streamlit_app/app.py

# 访问 http://localhost:8501/处理结果
```

页面功能：
- 按分级筛选展示（A/B/C/D/E/F）
- 显示摘要、关键词
- 查看翻译内容（如果有）
- 统计各分级推文数量

## 数据库表结构

### processed_tweets 表

存储推文处理结果：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| tweet_id | VARCHAR(100) | 推文ID（外键，唯一） |
| grade | CHAR(1) | 分级（A/B/C/D/E/F） |
| summary_cn | VARCHAR(100) | 中文摘要（≤30字） |
| keywords | JSONB | 关键词数组 |
| embedding | JSONB | 向量表示 |
| translated_content | TEXT | 翻译内容 |
| processing_time_ms | INTEGER | 处理耗时（毫秒） |
| processed_at | TIMESTAMP | 处理时间（UTC） |

### tweets 表新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| processing_status | ENUM | 处理状态（pending/processing/completed/failed/skipped） |

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
