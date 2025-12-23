"""测试处理结果页面的数据加载"""
import sys
sys.path.insert(0, '.')
from src.storage.postgres_client import get_postgres_client

pg = get_postgres_client()

# 模拟页面的查询
selected_grades = ["P0", "P1", "P2"]
limit = 20
offset = 0

placeholders = ','.join(['%s'] * len(selected_grades))
query = f"""
SELECT
    p.id,
    p.tweet_id,
    t.author,
    t.content,
    t.tweet_url,
    t.media_urls,
    t.has_media,
    p.grade,
    p.summary_cn,
    p.keywords,
    p.translated_content,
    p.processing_time_ms,
    p.processed_at,
    t.published_at
FROM processed_tweets p
JOIN tweets t ON p.tweet_id = t.tweet_id
WHERE p.grade IN ({placeholders})
ORDER BY t.published_at DESC
LIMIT %s OFFSET %s
"""
params = tuple(selected_grades) + (limit, offset)

print(f"查询参数: {params}")
print(f"\n执行查询...")

result = pg.execute_query(query, params)

if result:
    print(f"✅ 查询成功，返回 {len(result)} 条数据\n")
    for i, row in enumerate(result, 1):
        print(f"{i}. {row['grade']} - {row['author']} - {row['summary_cn']}")
else:
    print("❌ 查询返回空结果")
