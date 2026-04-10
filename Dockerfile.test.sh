#!/bin/bash
# Docker 构建测试脚本
# 使用方式: bash Dockerfile.test.sh

set -e

echo "=== Docker 构建测试 ==="
echo ""

# 1. 检查 Docker
echo "1. 检查 Docker 安装..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    echo "请先安装 Docker: https://docs.docker.com/engine/install/"
    exit 1
fi
echo "✅ Docker 已安装: $(docker --version)"
echo ""

# 2. 检查 Docker Compose
echo "2. 检查 Docker Compose..."
if docker compose version &> /dev/null; then
    echo "✅ Docker Compose V2: $(docker compose version)"
elif command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose V1: $(docker-compose --version)"
else
    echo "❌ Docker Compose 未安装"
    exit 1
fi
echo ""

# 3. 构建 Backend
echo "3. 构建 Backend 镜像..."
docker build -f docker/Dockerfile -t stock-analyzer-backend:test . || {
    echo "❌ Backend 构建失败"
    exit 1
}
echo "✅ Backend 构建成功"
echo ""

# 4. 构建 Frontend
echo "4. 构建 Frontend 镜像..."
docker build -f docker/frontend.Dockerfile -t stock-analyzer-frontend:test . || {
    echo "❌ Frontend 构建失败"
    exit 1
}
echo "✅ Frontend 构建成功"
echo ""

# 5. 启动服务
echo "5. 启动 Docker Compose 服务..."
cd docker
docker compose up -d || {
    echo "❌ 服务启动失败"
    exit 1
}
echo "✅ 服务启动成功"
echo ""

# 6. 等待健康检查
echo "6. 等待服务健康检查（30秒）..."
sleep 30

# 7. 检查服务状态
echo "7. 检查服务状态..."
docker compose ps

echo ""
echo "=== 测试完成 ==="
echo ""
echo "访问地址:"
echo "  - 后端 API: http://localhost:8000"
echo "  - API 文档: http://localhost:8000/docs"
echo "  - 前端界面: http://localhost:8501"
echo ""
echo "停止服务: cd docker && docker compose down"
