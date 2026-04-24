#!/bin/bash
# Pre-commit hook: 检查测试目录与业务目录对齐
# 安装: make install-hooks 或手动复制到 .git/hooks/pre-commit

set -e

echo "🔍 检查测试目录与业务目录对齐..."

# 运行检查脚本
if [ -f "scripts/check_test_structure.py" ]; then
    python3 scripts/check_test_structure.py
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ 测试目录结构检查未通过，提交被阻止"
        echo "   请修复上述问题后再提交"
        exit 1
    fi
else
    echo "⚠️  检查脚本不存在: scripts/check_test_structure.py"
    echo "   跳过目录对齐检查"
fi

echo "✅ 测试目录结构检查通过"
exit 0
