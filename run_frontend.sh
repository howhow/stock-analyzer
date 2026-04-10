#!/bin/bash
# Stock Analyzer Frontend 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Stock Analyzer Frontend${NC}"
echo "=============================="

# 检查虚拟环境
if [ ! -d "local_venv" ]; then
    echo -e "${RED}❌ 虚拟环境不存在，请先运行: make venv${NC}"
    exit 1
fi

# 激活虚拟环境
source local_venv/bin/activate

# 检查依赖
if ! python -c "import streamlit" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Streamlit 未安装，正在安装...${NC}"
    pip install streamlit plotly -q
fi

# 检查后端服务是否运行
echo -e "${YELLOW}🔍 检查后端服务...${NC}"
if ! curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  后端服务未启动，请先启动后端:${NC}"
    echo "   make dev"
    echo ""
    echo -e "${YELLOW}是否继续启动前端? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        exit 0
    fi
fi

# 设置环境变量
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# 启动前端
echo -e "${GREEN}✅ 启动前端服务...${NC}"
echo -e "${GREEN}🌐 访问地址: http://localhost:8501${NC}"
echo "=============================="

cd frontend
streamlit run app.py
