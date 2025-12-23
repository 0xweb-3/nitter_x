# utils 目录

## 目录作用

通用工具函数模块。

## 文件说明

### logger.py
日志配置工具，提供：
- 统一的日志格式配置
- 文件日志和控制台日志输出
- 日志级别控制
- 日志文件轮转（可选）

**日志格式**：
```
[YYYY-MM-DD HH:MM:SS] [日志级别] [模块名] - 消息内容
```

**使用示例**：
```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("信息日志")
logger.warning("警告日志")
logger.error("错误日志")
```

## 日志配置

### 日志级别
- DEBUG: 详细的调试信息
- INFO: 一般信息（默认）
- WARNING: 警告信息
- ERROR: 错误信息

### 日志文件
- 默认路径：`logs/crawler.log`
- 可通过环境变量 `LOG_FILE` 配置

### 日志时间
- 所有日志时间使用 UTC 格式
- 格式：`YYYY-MM-DD HH:MM:SS`

## 扩展建议

本目录可添加其他通用工具函数，例如：

### 时间处理
```python
# utils/time_helper.py
def utc_now():
    """返回当前 UTC 时间"""
    return datetime.now(timezone.utc)

def format_timestamp(dt):
    """格式化时间戳"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")
```

### 文本处理
```python
# utils/text_helper.py
def clean_text(text):
    """清洗文本"""
    # 去除多余空白、特殊字符等
    pass

def extract_urls(text):
    """提取文本中的 URL"""
    pass
```

### HTTP 工具
```python
# utils/http_helper.py
def retry_request(url, max_retries=3):
    """带重试的 HTTP 请求"""
    pass
```

## 注意事项

- 工具函数应该是无状态的纯函数
- 避免循环依赖
- 添加充分的文档字符串和类型注解
- 编写单元测试
