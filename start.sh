#!/bin/bash

# ============================================
# Nitter X 服务一键启动脚本
# ============================================

set -e  # 遇到错误立即退出

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

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================
# 1. 环境检查
# ============================================
log_info "开始环境检查..."

# 检查 Docker
if ! command_exists docker; then
    log_error "Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    log_error "Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 使用正确的 docker-compose 命令
if command_exists docker-compose; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# 检查 Python
if ! command_exists python3 && ! command_exists python; then
    log_error "Python 未安装，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_CMD=$(command_exists python3 && echo "python3" || echo "python")

# 检查 Python 版本
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
log_info "检测到 Python 版本: $PYTHON_VERSION"

# 检查 venv 模块是否可用
if ! $PYTHON_CMD -m venv --help >/dev/null 2>&1; then
    log_warning "Python venv 模块不可用，正在尝试自动安装..."

    # 检测系统类型并自动安装
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu 系统
        log_info "检测到 Debian/Ubuntu 系统"
        log_info "正在安装 python3-venv..."

        if sudo apt-get update && sudo apt-get install -y python3-venv; then
            log_success "python3-venv 安装成功"
        else
            log_error "python3-venv 安装失败"
            log_info "请手动运行："
            log_info "  sudo apt-get update"
            log_info "  sudo apt-get install python3-venv"
            exit 1
        fi

    elif [ -f /etc/redhat-release ]; then
        # RedHat/CentOS/Fedora 系统
        log_info "检测到 RedHat/CentOS/Fedora 系统"
        log_info "正在安装 python3-venv..."

        if sudo yum install -y python3-venv; then
            log_success "python3-venv 安装成功"
        else
            log_error "python3-venv 安装失败"
            log_info "请手动运行："
            log_info "  sudo yum install python3-venv"
            exit 1
        fi

    elif [ -f /etc/arch-release ]; then
        # Arch Linux 系统
        log_info "检测到 Arch Linux 系统"
        log_info "Arch Linux 的 Python 自带 venv 模块，请检查 Python 安装"
        exit 1

    else
        # 其他系统或 macOS
        log_error "无法自动安装 venv 模块"
        log_info "请根据您的系统手动安装 Python venv 模块"
        exit 1
    fi

    # 再次检查 venv 是否可用
    if ! $PYTHON_CMD -m venv --help >/dev/null 2>&1; then
        log_error "venv 模块安装后仍不可用，请检查安装"
        exit 1
    fi

    log_success "venv 模块已准备就绪"
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    log_warning "虚拟环境不存在，正在自动创建..."

    # 创建虚拟环境
    log_info "创建虚拟环境: $PYTHON_CMD -m venv .venv"
    if ! $PYTHON_CMD -m venv .venv; then
        log_error "虚拟环境创建失败"
        exit 1
    fi
    log_success "虚拟环境创建成功"

    # 设置虚拟环境 Python 路径
    VENV_PYTHON=".venv/bin/python"
    VENV_PIP=".venv/bin/pip"

    # 升级 pip
    log_info "升级 pip..."
    if ! $VENV_PYTHON -m pip install --upgrade pip; then
        log_warning "pip 升级失败，继续安装依赖..."
    fi

    # 安装依赖
    if [ -f "requirements.txt" ]; then
        log_info "安装主要依赖: requirements.txt"
        if ! $VENV_PIP install -r requirements.txt; then
            log_error "依赖安装失败: requirements.txt"
            exit 1
        fi
        log_success "requirements.txt 安装完成"
    else
        log_warning "未找到 requirements.txt"
    fi

    if [ -f "requirements-streamlit.txt" ]; then
        log_info "安装 Streamlit 依赖: requirements-streamlit.txt"
        if ! $VENV_PIP install -r requirements-streamlit.txt; then
            log_error "依赖安装失败: requirements-streamlit.txt"
            exit 1
        fi
        log_success "requirements-streamlit.txt 安装完成"
    else
        log_warning "未找到 requirements-streamlit.txt"
    fi

    log_success "虚拟环境和依赖安装完成"
else
    log_success "虚拟环境已存在"
    VENV_PYTHON=".venv/bin/python"
fi

log_success "环境检查通过"

# ============================================
# 2. 检查 Docker 服务
# ============================================
log_info "检查 Docker 服务状态..."

# 检查 Docker daemon 是否运行
if ! docker info >/dev/null 2>&1; then
    log_error "Docker daemon 未运行，请先启动 Docker"
    exit 1
fi

# 检查容器是否运行
POSTGRES_RUNNING=$($DOCKER_COMPOSE ps postgres | grep -i "up" || true)
REDIS_RUNNING=$($DOCKER_COMPOSE ps redis | grep -i "up" || true)

if [ -z "$POSTGRES_RUNNING" ] || [ -z "$REDIS_RUNNING" ]; then
    log_warning "数据库服务未运行，正在启动..."
    $DOCKER_COMPOSE up -d

    log_info "等待数据库服务启动..."
    sleep 5

    # 再次检查
    POSTGRES_RUNNING=$($DOCKER_COMPOSE ps postgres | grep -i "up" || true)
    REDIS_RUNNING=$($DOCKER_COMPOSE ps redis | grep -i "up" || true)

    if [ -z "$POSTGRES_RUNNING" ] || [ -z "$REDIS_RUNNING" ]; then
        log_error "数据库服务启动失败，请查看日志："
        log_info "  $DOCKER_COMPOSE logs postgres"
        log_info "  $DOCKER_COMPOSE logs redis"
        exit 1
    fi
fi

log_success "Docker 服务运行正常"

# ============================================
# 3. 运行部署验证
# ============================================
log_info "运行部署验证..."

if ! $VENV_PYTHON verify_deployment.py; then
    log_warning "部署验证发现问题，是否继续启动服务？"
    read -p "继续？ (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

log_success "部署验证完成"

# ============================================
# 4. 创建必要的目录
# ============================================
mkdir -p logs
mkdir -p data/models

# ============================================
# 5. 启动服务
# ============================================
log_info "正在启动所有服务..."

# 检查是否已有服务在运行
PIDS_FILE=".service_pids"
if [ -f "$PIDS_FILE" ]; then
    log_warning "检测到服务可能已在运行"
    log_info "如需重新启动，请先运行 ./stop.sh"
    read -p "是否继续（可能导致重复运行）？ (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 清空 PID 文件
> "$PIDS_FILE"

# 启动推文采集
log_info "启动推文采集服务..."
nohup $VENV_PYTHON main.py > logs/crawler.log 2>&1 &
CRAWLER_PID=$!
echo "crawler:$CRAWLER_PID" >> "$PIDS_FILE"
log_success "推文采集服务已启动 (PID: $CRAWLER_PID)"

# 启动推文处理
log_info "启动推文处理服务..."
nohup $VENV_PYTHON process_worker.py > logs/process_worker.log 2>&1 &
WORKER_PID=$!
echo "worker:$WORKER_PID" >> "$PIDS_FILE"
log_success "推文处理服务已启动 (PID: $WORKER_PID)"

# 启动 Streamlit
log_info "启动 Streamlit Web 界面..."
if [ -f "start_streamlit.sh" ]; then
    nohup ./start_streamlit.sh > logs/streamlit.log 2>&1 &
else
    nohup $VENV_PYTHON -m streamlit run streamlit_app/app.py > logs/streamlit.log 2>&1 &
fi
STREAMLIT_PID=$!
echo "streamlit:$STREAMLIT_PID" >> "$PIDS_FILE"
log_success "Streamlit 已启动 (PID: $STREAMLIT_PID)"

# 等待服务启动
sleep 3

# ============================================
# 6. 验证服务状态
# ============================================
log_info "验证服务状态..."

# 检查进程是否还在运行
check_process() {
    if ps -p $1 > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

ALL_RUNNING=true

if check_process $CRAWLER_PID; then
    log_success "✓ 推文采集服务运行正常"
else
    log_error "✗ 推文采集服务启动失败"
    ALL_RUNNING=false
fi

if check_process $WORKER_PID; then
    log_success "✓ 推文处理服务运行正常"
else
    log_error "✗ 推文处理服务启动失败"
    ALL_RUNNING=false
fi

if check_process $STREAMLIT_PID; then
    log_success "✓ Streamlit 服务运行正常"
else
    log_error "✗ Streamlit 服务启动失败"
    ALL_RUNNING=false
fi

# ============================================
# 7. 完成信息
# ============================================
echo ""
echo "============================================"
if [ "$ALL_RUNNING" = true ]; then
    log_success "🎉 所有服务已成功启动！"
else
    log_warning "⚠️  部分服务启动失败，请查看日志"
fi
echo "============================================"
echo ""
log_info "服务信息："
echo "  📊 Streamlit Web 界面: http://localhost:8501"
echo "  🐦 推文采集服务: 后台运行中 (PID: $CRAWLER_PID)"
echo "  🤖 推文处理服务: 后台运行中 (PID: $WORKER_PID)"
echo ""
log_info "日志文件："
echo "  📝 采集日志: tail -f logs/crawler.log"
echo "  📝 处理日志: tail -f logs/process_worker.log"
echo "  📝 Streamlit 日志: tail -f logs/streamlit.log"
echo ""
log_info "管理命令："
echo "  ⏸️  停止所有服务: ./stop.sh"
echo "  🔄 查看服务状态: ./status.sh"
echo "  📋 查看所有日志: tail -f logs/*.log"
echo ""

# ============================================
# 8. 保存启动信息
# ============================================
cat > .service_info << EOF
启动时间: $(date)
推文采集 PID: $CRAWLER_PID
推文处理 PID: $WORKER_PID
Streamlit PID: $STREAMLIT_PID
EOF

log_info "提示: 使用 Ctrl+C 不会停止后台服务"
log_info "      使用 ./stop.sh 停止所有服务"
