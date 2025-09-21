#!/bin/bash

# 部署修复验证脚本
# 用于测试部署脚本是否正确处理各种错误情况

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

# 测试用例
test_invalid_token() {
    log_info "测试场景: 无效认证令牌"
    
    if ./scripts/deploy-to-test-k8s.sh "test-image:latest" "invalid-token" 2>/dev/null; then
        log_error "测试失败: 应该检测到无效令牌"
        return 1
    else
        log_success "测试通过: 正确检测到无效令牌"
        return 0
    fi
}

test_missing_parameters() {
    log_info "测试场景: 缺少参数"
    
    if ./scripts/deploy-to-test-k8s.sh 2>/dev/null; then
        log_error "测试失败: 应该检测到缺少参数"
        return 1
    else
        log_success "测试通过: 正确检测到缺少参数"
        return 0
    fi
}

test_empty_parameters() {
    log_info "测试场景: 空参数"
    
    if ./scripts/deploy-to-test-k8s.sh "" "" 2>/dev/null; then
        log_error "测试失败: 应该检测到空参数"
        return 1
    else
        log_success "测试通过: 正确检测到空参数"
        return 0
    fi
}

# 主测试函数
main() {
    log_info "🧪 开始部署修复验证测试..."
    echo ""
    
    # 检查部署脚本是否存在
    if [ ! -f "scripts/deploy-to-test-k8s.sh" ]; then
        log_error "部署脚本不存在: scripts/deploy-to-test-k8s.sh"
        exit 1
    fi
    
    # 确保脚本可执行
    chmod +x scripts/deploy-to-test-k8s.sh
    
    local passed=0
    local total=0
    
    # 运行测试用例
    echo "=== 参数验证测试 ==="
    
    total=$((total + 1))
    if test_missing_parameters; then
        passed=$((passed + 1))
    fi
    echo ""
    
    total=$((total + 1))
    if test_empty_parameters; then
        passed=$((passed + 1))
    fi
    echo ""
    
    total=$((total + 1))
    if test_invalid_token; then
        passed=$((passed + 1))
    fi
    echo ""
    
    # 测试结果汇总
    log_info "=== 测试结果汇总 ==="
    log_info "通过测试: $passed/$total"
    
    if [ $passed -eq $total ]; then
        log_success "🎉 所有测试通过!"
        log_success "部署脚本错误处理功能正常"
        exit 0
    else
        log_error "❌ 部分测试失败"
        log_error "部署脚本需要进一步修复"
        exit 1
    fi
}

# 执行主函数
main "$@"
