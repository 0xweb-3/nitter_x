# migrations 目录

## 目录作用

存储数据库迁移脚本。

## 说明

本目录包含数据库结构变更的 Python 脚本，用于：
- 添加新字段
- 修改表结构
- 数据迁移和转换
- 索引优化

## 现有迁移脚本

### add_notes_field.py
为 `watched_users` 表添加 `notes` 字段，用于记录用户备注信息。

### add_tweet_url_field.py
为 `tweets` 表添加 `tweet_url` 字段，用于存储推文原始链接。

## 使用方式

```bash
# 执行迁移脚本
python migrations/脚本名称.py
```

## 注意事项

- 迁移脚本应该是幂等的（可重复执行）
- 执行前务必备份数据库
- 新增迁移脚本应包含回滚逻辑
- 命名规范：`{操作描述}_{目标对象}.py`
