# Nitter 实例来源扩展指南

## 架构说明

实例发现系统已重构为模块化设计：

1. **constants.py** - 常量定义
   - `KNOWN_INSTANCES`: 内置的 40+ 个已验证实例列表

2. **instance_sources.py** - 实例来源获取
   - 支持多种来源
   - 基于抽象类设计，易于扩展

3. **instance_discovery.py** - 健康检测
   - 并发检测实例可用性
   - 按响应时间排序

## 文件结构

```
src/crawler/
├── constants.py              # 常量：KNOWN_INSTANCES
├── instance_sources.py       # 来源管理
├── instance_discovery.py     # 健康检测
└── README_SOURCES.md         # 本文档
```

## 已实现的来源

### 1. BuiltinSource（内置列表）
- 从 `constants.py` 中读取 `KNOWN_INSTANCES`
- 维护 40+ 个已验证的实例
- 作为备用来源

**如何更新内置实例列表**：

直接编辑 `src/crawler/constants.py`：

```python
# src/crawler/constants.py

KNOWN_INSTANCES = [
    "https://xcancel.com",
    "https://nitter.net",
    # ... 添加更多实例
    "https://your-new-instance.com",
]
```

或通过代码动态添加：

```python
from src.crawler.constants import KNOWN_INSTANCES

# 添加新实例
KNOWN_INSTANCES.append("https://new-instance.com")

# 或批量添加
new_instances = ["https://a.com", "https://b.com"]
KNOWN_INSTANCES.extend(new_instances)
```

### 2. StatusPageSource（状态监控页面）
- 从 https://status.d420.de/ 获取实例
- 自动解析 HTML 提取实例 URL

## 如何添加新的实例来源

### 步骤 1：创建自定义来源类

在 `src/crawler/instance_sources.py` 中添加新类，继承 `InstanceSource`：

```python
class GitHubSource(InstanceSource):
    """从 GitHub 仓库获取实例列表"""

    def __init__(self, repo_url: str):
        self.repo_url = repo_url

    def get_source_name(self) -> str:
        return f"GitHub({self.repo_url})"

    def fetch_instances(self) -> List[str]:
        """
        从 GitHub 获取实例列表

        Returns:
            实例 URL 列表
        """
        try:
            # 实现你的获取逻辑
            # 例如：从 README 或 JSON 文件解析
            response = requests.get(self.repo_url)
            # ... 解析逻辑
            instances = []  # 提取的实例列表

            logger.info(f"从 GitHub 获取到 {len(instances)} 个实例")
            return instances
        except Exception as e:
            logger.error(f"从 GitHub 获取失败: {e}")
            return []
```

### 步骤 2：注册到默认来源

在 `get_default_sources()` 函数中添加：

```python
def get_default_sources() -> InstanceSourceManager:
    manager = InstanceSourceManager()

    # 现有来源
    manager.add_source(BuiltinSource())
    manager.add_source(StatusPageSource("https://status.d420.de/"))

    # 添加新来源
    manager.add_source(GitHubSource("https://raw.githubusercontent.com/..."))

    return manager
```

### 步骤 3：测试

```bash
python discover_instances.py --count 10 --update-env
```

## 示例：添加社区 API 来源

```python
class CommunityAPISource(InstanceSource):
    """从社区 API 获取实例列表"""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.session = requests.Session()

    def get_source_name(self) -> str:
        return f"CommunityAPI({self.api_url})"

    def fetch_instances(self) -> List[str]:
        try:
            logger.info(f"从社区 API 获取实例: {self.api_url}")
            response = self.session.get(self.api_url, timeout=10)
            response.raise_for_status()

            # 假设 API 返回 JSON 格式
            data = response.json()
            instances = [item["url"] for item in data.get("instances", [])]

            logger.info(f"从社区 API 获取到 {len(instances)} 个实例")
            return instances
        except Exception as e:
            logger.error(f"从社区 API 获取失败: {e}")
            return []
```

## 示例：添加 RSS Feed 来源

```python
import feedparser

class RSSFeedSource(InstanceSource):
    """从 RSS Feed 获取实例列表"""

    def __init__(self, feed_url: str):
        self.feed_url = feed_url

    def get_source_name(self) -> str:
        return f"RSSFeed({self.feed_url})"

    def fetch_instances(self) -> List[str]:
        try:
            logger.info(f"从 RSS Feed 获取实例: {self.feed_url}")
            feed = feedparser.parse(self.feed_url)

            instances = []
            for entry in feed.entries:
                # 从条目中提取实例 URL
                if 'link' in entry:
                    instances.append(entry.link)

            logger.info(f"从 RSS Feed 获取到 {len(instances)} 个实例")
            return instances
        except Exception as e:
            logger.error(f"从 RSS Feed 获取失败: {e}")
            return []
```

## 最佳实践

1. **错误处理**：所有来源必须处理异常，失败时返回空列表
2. **超时设置**：网络请求设置合理的超时时间
3. **日志记录**：记录获取过程和结果
4. **去重逻辑**：`InstanceSourceManager` 会自动去重，无需在来源中处理
5. **URL 验证**：确保返回的是有效的 HTTP/HTTPS URL

## 使用自定义来源

### 方式 1：在代码中直接使用

```python
from src.crawler.instance_sources import InstanceSourceManager, BuiltinSource
from src.crawler.instance_discovery import NitterInstanceChecker

# 创建自定义来源管理器
manager = InstanceSourceManager()
manager.add_source(BuiltinSource())
manager.add_source(GitHubSource("https://..."))

# 获取所有实例
instances = manager.fetch_all_instances()

# 健康检测
checker = NitterInstanceChecker()
available = checker.check_instances_batch(list(instances))
```

### 方式 2：修改默认配置

直接修改 `get_default_sources()` 函数，添加你的自定义来源。

## 调试技巧

```python
# 测试单个来源
from src.crawler.instance_sources import StatusPageSource

source = StatusPageSource()
instances = source.fetch_instances()
print(f"获取到 {len(instances)} 个实例:")
for url in instances:
    print(f"  - {url}")
```

## 贡献

如果你实现了有用的新来源，欢迎提交 PR！

可能的扩展方向：
- GitHub 仓库列表
- Awesome Lists
- 社区维护的 JSON API
- Mastodon/Fediverse 实例列表
- DNS 记录查询
