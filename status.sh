#!/bin/bash

# ============================================
# Nitter X 服务状态查看脚本
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

echo "============================================"
echo "📊 Nitter X 服务状态"
echo "============================================"
echo ""

# 检查 Docker Compose 命令
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    log_error "Docker Compose 未安装"
    exit 1
fi

# ============================================
# 1. Docker 服务状态
# ============================================
log_info "Docker 服务:"
echo ""

# PostgreSQL
if $DOCKER_COMPOSE ps postgres | grep -i "up" > /dev/null; then
    log_success "✓ PostgreSQL 运行中"
else
    log_error "✗ PostgreSQL 未运行"
fi

# Redis
if $DOCKER_COMPOSE ps redis | grep -i "up" > /dev/null; then
    log_success "✓ Redis 运行中"
else
    log_error "✗ Redis 未运行"
fi

echo ""

# ============================================
# 2. Python 服务状态
# ============================================
log_info "Python 服务:"
echo ""

PIDS_FILE=".service_pids"

if [ -f "$PIDS_FILE" ]; then
    while IFS=: read -r service pid; do
        if [ -n "$pid" ]; then
            if ps -p "$pid" > /dev/null 2>&1; then
                # 获取进程运行时间
                UPTIME=$(ps -o etime= -p "$pid" | tr -d ' ')
                log_success "✓ $service (PID: $pid, 运行时间: $UPTIME)"
            else
                log_error "✗ $service (PID: $pid) 已停止"
            fi
        fi
    done < "$PIDS_FILE"
else
    log_warning "未找到服务 PID 文件"
    log_info "检查是否有 Python 进程运行..."

    # 检查推文采集
    if pgrep -f "main.py" > /dev/null; then
        PID=$(pgrep -f "main.py")
        log_success "✓ 推文采集服务 (PID: $PID)"
    else
        log_error "✗ 推文采集服务未运行"
    fi

    # 检查推文处理
    if pgrep -f "process_worker.py" > /dev/null; then
        PID=$(pgrep -f "process_worker.py")
        log_success "✓ 推文处理服务 (PID: $PID)"
    else
        log_error "✗ 推文处理服务未运行"
    fi

    # 检查 Streamlit
    if pgrep -f "streamlit" > /dev/null; then
        PID=$(pgrep -f "streamlit")
        log_success "✓ Streamlit 服务 (PID: $PID)"
    else
        log_error "✗ Streamlit 服务未运行"
    fi
fi

echo ""

# ============================================
# 3. 启动信息
# ============================================
if [ -f ".service_info" ]; then
    log_info "启动信息:"
    echo ""
    cat ".service_info" | while read -r line; do
        echo "  $line"
    done
    echo ""
fi

# ============================================
# 4. 最近日志
# ============================================
log_info "最近日志（最后 5 行）:"
echo ""

for log_file in logs/crawler.log logs/process_worker.log logs/streamlit.log; do
    if [ -f "$log_file" ]; then
        echo "📝 $log_file:"
        tail -5 "$log_file" 2>/dev/null | sed 's/^/  /'
        echo ""
    fi
done

# ============================================
# 5. 访问地址
# ============================================
log_info "访问地址:"
echo "  🌐 Streamlit Web 界面: http://localhost:8501"
echo ""

# ============================================
# 6. 管理命令
# ============================================
log_info "管理命令:"
echo "  🚀 启动所有服务: ./start.sh"
echo "  ⏸️  停止所有服务: ./stop.sh"
echo "  📋 查看实时日志: tail -f logs/crawler.log"
echo ""
