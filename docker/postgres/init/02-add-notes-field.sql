-- 添加 notes 字段到 watched_users 表
-- 用于 Streamlit Web UI 的用户备注功能

-- 添加 notes 字段
ALTER TABLE watched_users
ADD COLUMN IF NOT EXISTS notes TEXT;

-- 添加注释
COMMENT ON COLUMN watched_users.notes IS '用户备注信息';

-- 验证
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'watched_users'
ORDER BY ordinal_position;
