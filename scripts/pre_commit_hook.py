#!/usr/bin/env python3
"""
Git Pre-Commit Hook - 代码提交前安全检查

功能：
1. 执行 make clean
2. 检查新增文件/目录是否被 Makefile 的 lint/test 覆盖
3. 检查大文件（>500行）
4. 扫描敏感信息（API Key、密码等）

安装：
    cp pre_commit_hook.py .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit

或软链接（推荐，便于更新）：
    ln -s ../../scripts/pre_commit_hook.py .git/hooks/pre-commit
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Tuple


# ============================================
# 配置
# ============================================
MAX_LINES = 500  # 大文件阈值
SENSITIVE_PATTERNS = [
    # API Keys
    r'sk-[a-zA-Z0-9]{48}',  # OpenAI/SiliconFlow
    r'[a-zA-Z0-9]{32}-[a-zA-Z0-9]{16}',  # Tushare
    r'AK[0-9a-zA-Z]{16,32}',  # 阿里云
    r'ghp_[a-zA-Z0-9]{36}',  # GitHub Personal Token
    # 密码
    r'password\s*=\s*["\'][^"\']+["\']',
    r'passwd\s*=\s*["\'][^"\']+["\']',
    r'secret\s*=\s*["\'][^"\']+["\']',
    # 其他敏感
    r'api_key\s*=\s*["\'][^"\']+["\']',
    r'apikey\s*=\s*["\'][^"\']+["\']',
    r'token\s*=\s*["\'][^"\']+["\']',
    r'private_key',
    r'BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY',
]

# 允许的文件扩展名（需要检查行数的）
CHECKED_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.h'}

# 忽略的路径模式
IGNORED_PATHS = [
    r'\.git/',
    r'__pycache__/',
    r'\.pytest_cache/',
    r'\.mypy_cache/',
    r'node_modules/',
    r'venv/',
    r'local_venv/',
    r'\.env',
    r'\.pyc$',
    r'\.log$',
    r'local_log/',
    r'local_test_report/',
]


# ============================================
# 颜色输出
# ============================================
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def error(msg: str) -> None:
    print(f"{Colors.RED}{Colors.BOLD}❌ {msg}{Colors.RESET}")


def success(msg: str) -> None:
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def warning(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")


def info(msg: str) -> None:
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")


# ============================================
# Git 操作
# ============================================
def run_cmd(cmd: List[str], cwd: str = None) -> Tuple[int, str, str]:
    """运行命令，返回 (returncode, stdout, stderr)"""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd or os.getcwd()
    )
    return result.returncode, result.stdout, result.stderr


def get_current_branch() -> str:
    """获取当前分支名"""
    code, stdout, _ = run_cmd(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    if code != 0:
        error("无法获取当前分支")
        sys.exit(1)
    return stdout.strip()


def get_repo_root() -> str:
    """获取仓库根目录"""
    code, stdout, _ = run_cmd(['git', 'rev-parse', '--show-toplevel'])
    if code != 0:
        error("无法获取仓库根目录")
        sys.exit(1)
    return stdout.strip()


def get_new_files_vs_master() -> Tuple[List[str], List[str]]:
    """
    比较当前分支和 master，返回新增的文件和目录
    返回: (new_files, new_dirs)
    """
    repo_root = get_repo_root()
    current_branch = get_current_branch()

    if current_branch == 'master':
        # 在 master 分支上，检查 staged 的文件
        code, stdout, _ = run_cmd(['git', 'diff', '--cached', '--name-only', '--diff-filter=A'])
        new_files = [f.strip() for f in stdout.strip().split('\n') if f.strip()]
    else:
        # 获取当前分支与 master 的差异
        # 先获取 merge base
        code, stdout, _ = run_cmd(['git', 'merge-base', 'master', current_branch])
        if code != 0:
            error("无法找到 master 和当前分支的 merge base")
            sys.exit(1)
        merge_base = stdout.strip()

        # 获取新增的文件
        code, stdout, _ = run_cmd(['git', 'diff', '--name-only', '--diff-filter=A', merge_base, current_branch])
        new_files = [f.strip() for f in stdout.strip().split('\n') if f.strip()]

    # 提取目录
    new_dirs = set()
    for f in new_files:
        dir_path = os.path.dirname(f)
        if dir_path:
            # 添加所有上级目录
            parts = dir_path.split('/')
            for i in range(len(parts)):
                new_dirs.add('/'.join(parts[:i+1]))

    return new_files, sorted(new_dirs)


def get_staged_files() -> List[str]:
    """获取暂存区中的文件"""
    code, stdout, _ = run_cmd(['git', 'diff', '--cached', '--name-only'])
    if code != 0:
        return []
    return [f.strip() for f in stdout.strip().split('\n') if f.strip()]


# ============================================
# Makefile 检查
# ============================================
def parse_makefile_coverage(makefile_path: str) -> Set[str]:
    """
    解析 Makefile，提取 lint 和 test 覆盖的目录/文件
    返回被覆盖的目录集合
    """
    covered = set()

    if not os.path.exists(makefile_path):
        warning(f"Makefile 不存在: {makefile_path}")
        return covered

    with open(makefile_path, 'r') as f:
        content = f.read()

    # 匹配模式：命令 + 目录列表
    # 例如: $(PYTHON) -m black --check app framework tests plugins frontend
    # 例如: $(PYTHON) -m pytest tests/ -v --cov=app --cov=framework

    # 提取 black/flake8/mypy 的目录参数
    dir_patterns = [
        r'(?:black|flake8|mypy|isort)\s+(?:--check\s+)?([a-zA-Z_\s/]+)(?:\s*\n|$)',
        r'pytest\s+.*--cov=([a-zA-Z_]+)',
        r'pytest\s+([a-zA-Z_\s/]+)/\s',
    ]

    for pattern in dir_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            dirs_str = match.group(1)
            # 分割目录
            for d in dirs_str.split():
                d = d.strip()
                if d and not d.startswith('--') and not d.startswith('$'):
                    covered.add(d)

    # 也检查 --cov=xxx 格式的参数
    cov_pattern = r'--cov=([a-zA-Z_]+)'
    for match in re.finditer(cov_pattern, content):
        covered.add(match.group(1))

    return covered


def check_makefile_coverage(new_files: List[str], new_dirs: List[str], covered: Set[str]) -> Tuple[bool, List[str]]:
    """
    检查新增文件/目录是否被 Makefile 覆盖
    返回: (是否通过, 未覆盖的项目列表)
    """
    uncovered = []

    # 检查新增目录
    for d in new_dirs:
        # 检查这个目录是否被覆盖
        is_covered = False
        for c in covered:
            if d == c or d.startswith(c + '/'):
                is_covered = True
                break

        if not is_covered:
            uncovered.append(f"目录: {d}/")

    # 检查新增文件（如果不在已覆盖的目录中）
    for f in new_files:
        dir_path = os.path.dirname(f)
        is_covered = False

        # 检查文件本身是否在 covered 中
        if os.path.basename(f) in covered:
            is_covered = True
        else:
            # 检查上级目录
            for c in covered:
                if dir_path == c or dir_path.startswith(c + '/'):
                    is_covered = True
                    break

        if not is_covered:
            uncovered.append(f"文件: {f}")

    return len(uncovered) == 0, uncovered


# ============================================
# 大文件检查
# ============================================
def check_large_files(files: List[str], max_lines: int = MAX_LINES) -> Tuple[bool, List[Tuple[str, int]]]:
    """
    检查文件是否超过最大行数
    返回: (是否通过, [(文件, 行数), ...])
    """
    large_files = []
    repo_root = get_repo_root()

    for f in files:
        # 检查扩展名
        ext = os.path.splitext(f)[1].lower()
        if ext not in CHECKED_EXTENSIONS:
            continue

        # 检查是否在忽略列表中
        if any(re.search(pattern, f) for pattern in IGNORED_PATHS):
            continue

        full_path = os.path.join(repo_root, f)
        if not os.path.exists(full_path):
            continue

        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as file:
                line_count = sum(1 for _ in file)

            if line_count > max_lines:
                large_files.append((f, line_count))
        except Exception as e:
            warning(f"无法读取文件 {f}: {e}")

    return len(large_files) == 0, large_files


# ============================================
# 敏感信息扫描
# ============================================
def scan_sensitive_info(files: List[str]) -> Tuple[bool, List[Tuple[str, str, int]]]:
    """
    扫描文件中的敏感信息
    返回: (是否通过, [(文件, 匹配内容, 行号), ...])
    """
    found = []
    repo_root = get_repo_root()

    for f in files:
        # 跳过二进制文件和特定类型
        ext = os.path.splitext(f)[1].lower()
        if ext in {'.pyc', '.log', '.png', '.jpg', '.gif', '.pdf', '.zip'}:
            continue

        # 检查是否在忽略列表中
        if any(re.search(pattern, f) for pattern in IGNORED_PATHS):
            continue

        full_path = os.path.join(repo_root, f)
        if not os.path.exists(full_path):
            continue

        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as file:
                for line_num, line in enumerate(file, 1):
                    for pattern in SENSITIVE_PATTERNS:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            # 排除常见的误报
                            matched_text = match.group(0)
                            if is_false_positive(matched_text, line):
                                continue

                            found.append((f, matched_text, line_num))
        except Exception as e:
            warning(f"无法扫描文件 {f}: {e}")

    return len(found) == 0, found


def is_false_positive(matched: str, line: str) -> bool:
    """判断是否是误报"""
    # 排除注释中的示例
    if line.strip().startswith('#') and 'example' in line.lower():
        return True

    # 排除测试数据中的假数据
    if 'test' in line.lower() and ('mock' in line.lower() or 'fake' in line.lower()):
        return True

    # 排除环境变量引用
    if 'os.environ' in line or 'getenv' in line:
        return True

    # 排除配置文件中的占位符
    if matched in {'your-api-key', 'your_api_key', 'placeholder', 'xxx', '***'}:
        return True

    # 排除正则表达式模式（在 SENSITIVE_PATTERNS 列表中）
    if 'SENSITIVE_PATTERNS' in line or 'r\'' in line or 'r"' in line:
        return True

    # 排除字符串字面量中的模式定义
    if line.strip().startswith("r'") or line.strip().startswith('r"'):
        return True

    return False


# ============================================
# 主流程
# ============================================
def main():
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  🔒 Git Pre-Commit 安全检查{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")

    repo_root = get_repo_root()
    os.chdir(repo_root)

    # 解析参数
    if len(sys.argv) > 1 and sys.argv[1] == '--dry-run':
        DRY_RUN = True
        info("🏃 DRY-RUN 模式：只检查，不阻止提交")
    else:
        DRY_RUN = False

    # Step 1: make clean
    info("Step 1: 执行 make clean...")
    if not DRY_RUN:
        code, stdout, stderr = run_cmd(['make', 'clean'])
        if code != 0:
            warning(f"make clean 返回非零退出码: {code}")
            print(stderr)
        else:
            success("make clean 完成")
    else:
        info("[DRY-RUN] 跳过 make clean")

    # Step 2: 检查新增文件/目录
    info("Step 2: 检查新增文件/目录...")
    new_files, new_dirs = get_new_files_vs_master()

    if new_files or new_dirs:
        info(f"发现 {len(new_files)} 个新增文件, {len(new_dirs)} 个新增目录")

        # 解析 Makefile
        makefile_path = os.path.join(repo_root, 'Makefile')
        covered = parse_makefile_coverage(makefile_path)
        info(f"Makefile 覆盖的目录: {', '.join(sorted(covered))}")

        # 检查覆盖
        passed, uncovered = check_makefile_coverage(new_files, new_dirs, covered)

        if not passed:
            error("发现未被 Makefile 覆盖的新增文件/目录！")
            for item in uncovered:
                print(f"   {Colors.RED}  - {item}{Colors.RESET}")
            print()
            error("立刻停止commit并上报系统架构师进行目录文件夹审查！！！")
            if not DRY_RUN:
                sys.exit(1)
            else:
                warning("[DRY-RUN] 本应阻止提交，但继续检查")
        else:
            success("所有新增文件/目录已被 Makefile 覆盖")
    else:
        info("未发现新增文件/目录")

    # Step 3: 检查大文件
    info("Step 3: 检查大文件...")
    staged_files = get_staged_files()

    passed, large_files = check_large_files(staged_files)
    if not passed:
        error("发现超过 500 行的大文件！")
        for f, lines in large_files:
            print(f"   {Colors.RED}  - {f} ({lines} 行){Colors.RESET}")
        print()
        error("立刻停止commit并上报系统架构师进行大文件拆分审查！！！")
        if not DRY_RUN:
            sys.exit(1)
        else:
            warning("[DRY-RUN] 本应阻止提交，但继续检查")
    else:
        success("大文件检查通过")

    # Step 4: 扫描敏感信息
    info("Step 4: 扫描敏感信息...")
    passed, sensitive = scan_sensitive_info(staged_files)
    if not passed:
        error("发现敏感信息！")
        for f, match, line_num in sensitive:
            print(f"   {Colors.RED}  - {f}:{line_num} -> {match}{Colors.RESET}")
        print()
        error("立刻停止commit并上报系统架构师进行安全审查！！！")
        if not DRY_RUN:
            sys.exit(1)
        else:
            warning("[DRY-RUN] 本应阻止提交，但继续检查")
    else:
        success("敏感信息扫描通过")

    # 全部通过
    print()
    print(f"{Colors.GREEN}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}  ✅ 所有安全检查通过，允许提交{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}{'='*60}{Colors.RESET}")
    sys.exit(0)


if __name__ == '__main__':
    main()
