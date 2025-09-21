#!/bin/bash

# README文件修复验证脚本
# 用于验证编码问题修复和依赖版本更新

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查文件编码
check_file_encoding() {
    local file="$1"
    log_info "检查文件编码: $file"
    
    if [ ! -f "$file" ]; then
        log_error "文件不存在: $file"
        return 1
    fi
    
    local encoding=$(file -bi "$file" | cut -d'=' -f2)
    if [ "$encoding" = "utf-8" ]; then
        log_success "$file: UTF-8编码正确"
    else
        log_warning "$file: 编码为 $encoding (不是UTF-8)"
    fi
}

# 检查Python版本要求
check_python_version() {
    local file="$1"
    local expected_version="3.11"
    
    log_info "检查Python版本要求: $file"
    
    if grep -q "Python.*≥.*3\.11\|Python.*>=.*3\.11\|Python.*3\.11.*以降" "$file"; then
        log_success "$file: Python版本要求正确 (≥3.11)"
    elif grep -q "Python.*≥.*3\.10\|Python.*>=.*3\.10\|Python.*3\.10.*以降" "$file"; then
        log_warning "$file: Python版本要求需要更新 (发现3.10，应为3.11)"
    else
        log_warning "$file: 未找到明确的Python版本要求"
    fi
}

# 检查依赖版本
check_dependency_versions() {
    local file="$1"
    
    log_info "检查依赖版本: $file"
    
    # 检查openai版本
    if grep -q "openai.*1\.79\.0" "$file"; then
        log_success "$file: openai版本信息已更新"
    elif grep -q "openai.*>=.*1\.0\.0" "$file"; then
        log_warning "$file: openai版本信息可以更详细"
    fi
    
    # 检查aiohttp版本
    if grep -q "aiohttp.*3\.12\." "$file"; then
        log_success "$file: aiohttp版本信息已更新"
    elif grep -q "aiohttp.*>=.*3\.8\.0" "$file"; then
        log_warning "$file: aiohttp版本信息需要更新"
    fi
    
    # 检查pydantic版本
    if grep -q "pydantic.*2\.11\." "$file"; then
        log_success "$file: pydantic版本信息已更新"
    elif grep -q "pydantic.*>=.*2\.5\.0" "$file"; then
        log_warning "$file: pydantic版本信息可以更详细"
    fi
    
    # 检查pytest版本
    if grep -q "pytest.*8\.4\." "$file"; then
        log_success "$file: pytest版本信息已更新"
    elif grep -q "pytest" "$file"; then
        log_warning "$file: pytest版本信息可以更详细"
    fi
}

# 检查pyproject.toml重复依赖
check_duplicate_dependencies() {
    log_info "检查pyproject.toml重复依赖"
    
    local aiohttp_count=$(grep -c "aiohttp" pyproject.toml || echo "0")
    if [ "$aiohttp_count" -eq 1 ]; then
        log_success "pyproject.toml: aiohttp依赖无重复"
    elif [ "$aiohttp_count" -gt 1 ]; then
        log_error "pyproject.toml: 发现 $aiohttp_count 个aiohttp依赖，存在重复"
    else
        log_warning "pyproject.toml: 未找到aiohttp依赖"
    fi
}

# 检查多语言README一致性
check_multilingual_consistency() {
    log_info "检查多语言README一致性"
    
    local files=("README.md" "README_zh.md" "README_ja.md")
    local python_versions=()
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            local version=$(grep -o "Python.*≥.*3\.[0-9]\+\|Python.*>=.*3\.[0-9]\+\|Python.*3\.[0-9]\+.*以降" "$file" | head -1 | grep -o "3\.[0-9]\+" | head -1 || echo "未找到")
            python_versions+=("$file:$version")
        fi
    done
    
    log_info "Python版本要求对比:"
    for version_info in "${python_versions[@]}"; do
        echo "  $version_info"
    done
    
    # 检查是否所有文件都要求3.11
    local all_311=true
    for version_info in "${python_versions[@]}"; do
        if [[ ! "$version_info" =~ 3\.11 ]]; then
            all_311=false
            break
        fi
    done
    
    if [ "$all_311" = true ]; then
        log_success "所有README文件的Python版本要求一致 (3.11)"
    else
        log_warning "README文件的Python版本要求不一致"
    fi
}

# 验证实际安装的包版本
verify_installed_versions() {
    log_info "验证实际安装的包版本"
    
    if command -v uv >/dev/null 2>&1; then
        log_info "检查实际安装的包版本:"
        
        # 检查关键包版本
        local packages=("openai" "aiohttp" "pydantic" "pytest")
        for package in "${packages[@]}"; do
            local version=$(uv run python -c "import $package; print('$package:', $package.__version__)" 2>/dev/null || echo "$package: 未安装或导入失败")
            echo "  $version"
        done
    else
        log_warning "uv未安装，跳过包版本验证"
    fi
}

# 主函数
main() {
    log_info "🔍 开始README文件修复验证..."
    echo ""
    
    # 检查文件编码
    log_info "=== 文件编码检查 ==="
    check_file_encoding "README.md"
    check_file_encoding "README_zh.md"
    check_file_encoding "README_ja.md"
    echo ""
    
    # 检查Python版本要求
    log_info "=== Python版本要求检查 ==="
    check_python_version "README.md"
    check_python_version "README_zh.md"
    check_python_version "README_ja.md"
    echo ""
    
    # 检查依赖版本
    log_info "=== 依赖版本检查 ==="
    check_dependency_versions "README.md"
    check_dependency_versions "README_zh.md"
    check_dependency_versions "README_ja.md"
    echo ""
    
    # 检查重复依赖
    log_info "=== 重复依赖检查 ==="
    check_duplicate_dependencies
    echo ""
    
    # 检查多语言一致性
    log_info "=== 多语言一致性检查 ==="
    check_multilingual_consistency
    echo ""
    
    # 验证实际版本
    log_info "=== 实际安装版本验证 ==="
    verify_installed_versions
    echo ""
    
    log_success "🎉 README文件修复验证完成!"
}

# 执行主函数
main "$@"
