#!/bin/bash

# ============================================
# Nitter X 服务停止脚本
# ============================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# PID 文件路径
PIDS_FILE=".service_pids"

log_info "正在停止 Nitter X 服务..."

if [ ! -f "$PIDS_FILE" ]; then
    log_warning "未找到服务 PID 文件，服务可能未通过 start.sh 启动"
    log_info "尝试查找并停止所有相关进程..."

    # 查找并停止 Python 进程
    pkill -f "main.py" || true
    pkill -f "process_worker.py" || true
    pkill -f "streamlit run streamlit_app/app.py" || true

    log_success "已尝试停止所有相关进程"
    exit 0
fi

# 读取 PID 文件并停止服务
while IFS=: read -r service pid; do
    if [ -n "$pid" ]; then
        if ps -p "$pid" > /dev/null 2>&1; then
            log_info "停止 $service (PID: $pid)..."
            kill "$pid" 2>/dev/null || true

            # 等待进程结束
            sleep 1

            # 如果还在运行，强制停止
            if ps -p "$pid" > /dev/null 2>&1; then
                log_warning "$service 未响应，强制停止..."
                kill -9 "$pid" 2>/dev/null || true
            fi

            if ps -p "$pid" > /dev/null 2>&1; then
                log_error "无法停止 $service"
            else
                log_success "✓ $service 已停止"
            fi
        else
            log_info "$service (PID: $pid) 已经停止"
        fi
    fi
done < "$PIDS_FILE"

# 删除 PID 文件和信息文件
rm -f "$PIDS_FILE"
rm -f ".service_info"

log_success "🎯 所有服务已停止"
log_info "Docker 服务仍在运行，如需停止请执行: docker-compose down"
