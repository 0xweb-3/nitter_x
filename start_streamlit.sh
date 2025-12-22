#!/bin/bash

# Nitter X Streamlit 启动脚本

echo "==================================="
echo "  Nitter X Streamlit Web UI"
echo "==================================="
echo ""

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo "❌ Python 未安装，请先安装 Python 3.8+"
    exit 1
fi

# 检查 Streamlit 是否安装
if ! python -c "import streamlit" &> /dev/null; then
    echo "⚠️  Streamlit 未安装，正在安装依赖..."
    pip install -r requirements-streamlit.txt

    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    echo "✅ 依赖安装完成"
    echo ""
fi

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，请先配置环境变量"
    exit 1
fi

# 默认端口
PORT=${STREAMLIT_PORT:-8501}

echo "🚀 启动 Streamlit 应用..."
echo "📍 访问地址: http://localhost:$PORT"
echo ""
echo "💡 提示: 按 Ctrl+C 停止服务"
echo ""

# 启动 Streamlit (移除冲突的配置)
streamlit run streamlit_app/app.py \
    --server.port $PORT \
    --server.headless true \
    --theme.primaryColor "#1DA1F2" \
    --theme.backgroundColor "#FFFFFF" \
    --theme.secondaryBackgroundColor "#F0F2F6"
