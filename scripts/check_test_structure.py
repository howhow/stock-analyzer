#!/usr/bin/env python3
"""
测试目录对齐检查脚本
用法: python scripts/check_test_structure.py [--fix]

功能:
1. 检查 tests/unit/ 下的目录结构是否与业务代码目录一一对应
2. 检查测试文件是否放在正确的目录下
3. 可选: --fix 自动修复缺失的目录
"""

import os
import sys
from pathlib import Path

# 业务代码根目录 → 测试代码根目录的映射
BUSINESS_TO_TEST = {
    "app": "tests/unit/app",
    "framework": "tests/unit/framework",
    "frontend": "tests/unit/frontend",
    "plugins": "tests/unit/plugins",
}

# 需要排除的目录（不需要测试的）
EXCLUDED_DIRS = {"__pycache__", ".git", "node_modules", ".pytest_cache", "migrations", "static", "templates"}

# 需要排除的文件（不需要测试的）
EXCLUDED_FILES = {"__init__.py", "conftest.py"}

# 允许存在的测试目录（即使业务代码没有对应目录）
# 这些目录通常是因为历史原因或特殊用途而存在
ALLOWED_ORPHAN_DIRS = {
    "app/services",  # 服务层测试，虽然业务目录没有services/，但有对应的服务模块
    "app/schemas",   # 数据模型测试
    "app/services/tasks",  # 任务服务测试
}


def get_all_subdirs(root_dir: str) -> set:
    """获取目录下的所有子目录（相对路径）"""
    subdirs = set()
    for dirpath, dirnames, _ in os.walk(root_dir):
        # 排除不需要的目录
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]

        rel_path = os.path.relpath(dirpath, root_dir)
        if rel_path != ".":
            subdirs.add(rel_path)
    return subdirs


def check_directory_alignment(fix: bool = False) -> list:
    """
    检查测试目录与业务目录对齐（双向检查）
    返回问题列表
    """
    issues = []

    for biz_dir, test_dir in BUSINESS_TO_TEST.items():
        if not os.path.exists(biz_dir):
            continue

        # 获取业务目录的所有子目录
        biz_subdirs = get_all_subdirs(biz_dir)
        test_subdirs = get_all_subdirs(test_dir) if os.path.exists(test_dir) else set()

        print(f"\n[DEBUG] {biz_dir}: 业务子目录={len(biz_subdirs)}, 测试子目录={len(test_subdirs)}")
        print(f"  业务: {sorted(biz_subdirs)}")
        print(f"  测试: {sorted(test_subdirs)}")

        # 方向1: 检查业务目录是否有对应测试目录
        for subdir in biz_subdirs:
            expected_test_dir = os.path.join(test_dir, subdir)
            if not os.path.exists(expected_test_dir):
                issues.append({
                    "type": "missing_test_dir",
                    "business_dir": os.path.join(biz_dir, subdir),
                    "expected_test_dir": expected_test_dir,
                    "message": f"❌ 测试目录缺失: {expected_test_dir} (对应业务目录: {os.path.join(biz_dir, subdir)})",
                })

                if fix:
                    os.makedirs(expected_test_dir, exist_ok=True)
                    init_file = os.path.join(expected_test_dir, "__init__.py")
                    if not os.path.exists(init_file):
                        open(init_file, "w").close()
                    print(f"✅ 已创建: {expected_test_dir}/__init__.py")

        # 方向2: 检查测试目录是否有对应业务目录（新增）
        for subdir in test_subdirs:
            expected_biz_dir = os.path.join(biz_dir, subdir)
            if not os.path.exists(expected_biz_dir):
                # 检查是否在允许列表中
                full_test_path = os.path.join(test_dir, subdir)
                rel_test_path = os.path.relpath(full_test_path, "tests/unit")
                if rel_test_path in ALLOWED_ORPHAN_DIRS:
                    print(f"  ⚠️  允许存在的孤儿目录: {full_test_path} (在 ALLOWED_ORPHAN_DIRS 中)")
                    continue
                issues.append({
                    "type": "orphan_test_dir",
                    "test_dir": os.path.join(test_dir, subdir),
                    "expected_biz_dir": expected_biz_dir,
                    "message": f"❌ 孤儿测试目录: {os.path.join(test_dir, subdir)} (无对应业务目录: {expected_biz_dir})",
                })

    return issues


def check_test_file_placement() -> list:
    """
    检查测试文件是否放在正确的目录下
    返回问题列表
    """
    issues = []

    # 检查 tests/unit/ 根目录下是否有不应该在那里的测试文件
    unit_root = Path("tests/unit")
    if unit_root.exists():
        for test_file in unit_root.glob("test_*.py"):
            issues.append({
                "type": "misplaced_test_file",
                "file": str(test_file),
                "message": f"⚠️  测试文件位置不当: {test_file} 应该在 tests/unit/<对应模块>/ 子目录下",
            })

    # 检查 tests/ 根目录下是否有测试文件（应该在 tests/unit/ 或 tests/integration/ 下）
    tests_root = Path("tests")
    if tests_root.exists():
        for test_file in tests_root.glob("test_*.py"):
            issues.append({
                "type": "misplaced_test_file",
                "file": str(test_file),
                "message": f"⚠️  测试文件位置不当: {test_file} 应该在 tests/unit/ 或 tests/integration/ 子目录下",
            })

    return issues


def check_duplicate_test_dirs() -> list:
    """
    检查是否有重复的测试目录（如 test_core/ 和 core/）
    返回问题列表
    """
    issues = []

    for test_root in BUSINESS_TO_TEST.values():
        if not os.path.exists(test_root):
            continue

        for dirpath, dirnames, _ in os.walk(test_root):
            for dirname in dirnames:
                if dirname.startswith("test_"):
                    # 检查是否有对应的非 test_ 前缀目录
                    parent_dir = os.path.dirname(dirpath)
                    expected_dir = os.path.join(parent_dir, dirname[5:])  # 去掉 test_ 前缀

                    if os.path.exists(expected_dir):
                        issues.append({
                            "type": "duplicate_test_dir",
                            "test_dir": os.path.join(dirpath, dirname),
                            "correct_dir": expected_dir,
                            "message": f"❌ 重复测试目录: {os.path.join(dirpath, dirname)} 应该合并到 {expected_dir}",
                        })

    return issues


def main():
    fix = "--fix" in sys.argv

    print("🔍 检查测试目录与业务目录对齐...")
    print("=" * 60)

    # 1. 检查目录对齐
    alignment_issues = check_directory_alignment(fix=fix)

    # 2. 检查测试文件位置
    placement_issues = check_test_file_placement()

    # 3. 检查重复目录
    duplicate_issues = check_duplicate_test_dirs()

    all_issues = alignment_issues + placement_issues + duplicate_issues

    if not all_issues:
        print("\n✅ 测试目录与业务目录完全对齐")
        print("✅ 测试文件位置正确")
        print("✅ 无重复测试目录")
        sys.exit(0)

    # 按类型分组输出
    missing_dirs = [i for i in all_issues if i["type"] == "missing_test_dir"]
    orphan_dirs = [i for i in all_issues if i["type"] == "orphan_test_dir"]
    misplaced_files = [i for i in all_issues if i["type"] == "misplaced_test_file"]
    duplicate_dirs = [i for i in all_issues if i["type"] == "duplicate_test_dir"]

    if missing_dirs:
        print(f"\n❌ 缺失 {len(missing_dirs)} 个测试目录:")
        for issue in missing_dirs:
            print(f"   {issue['message']}")
        if fix:
            print(f"\n✅ 已自动创建缺失目录")
        else:
            print(f"\n修复命令:")
            for issue in missing_dirs:
                print(f"   mkdir -p {issue['expected_test_dir']} && touch {issue['expected_test_dir']}/__init__.py")

    if orphan_dirs:
        print(f"\n❌ 发现 {len(orphan_dirs)} 个孤儿测试目录（无对应业务目录）:")
        for issue in orphan_dirs:
            print(f"   {issue['message']}")
        print(f"\n处理建议:")
        for issue in orphan_dirs:
            print(f"   检查是否需要删除: {issue['test_dir']}")
            print(f"   或确认业务目录是否被遗漏: {issue['expected_biz_dir']}")

    if duplicate_dirs:
        print(f"\n❌ 发现 {len(duplicate_dirs)} 个重复测试目录:")
        for issue in duplicate_dirs:
            print(f"   {issue['message']}")

    if misplaced_files:
        print(f"\n⚠️  发现 {len(misplaced_files)} 个位置不当的测试文件:")
        for issue in misplaced_files:
            print(f"   {issue['message']}")

    print("\n" + "=" * 60)
    print("❌ 测试目录结构检查未通过")

    if fix:
        print("\n💡 已自动修复部分问题，请重新运行检查")
    else:
        print("\n💡 使用 --fix 参数自动修复缺失目录:")
        print("   python scripts/check_test_structure.py --fix")

    sys.exit(1)


if __name__ == "__main__":
    main()
