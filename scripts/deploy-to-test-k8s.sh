#!/bin/bash

# Kubernetes测试环境部署脚本
# 修复CI/CD流水线中的403错误假阳性问题
# 
# 使用方法:
#   ./deploy-to-test-k8s.sh <image-tag> <auth-token>
#
# 环境变量:
#   DEBUG_MODE - 启用调试模式（默认false）

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

# 调试模式
DEBUG_MODE=${DEBUG_MODE:-false}

debug_log() {
    if [ "$DEBUG_MODE" = "true" ]; then
        echo -e "${YELLOW}🔍 DEBUG: $1${NC}"
    fi
}

# 参数验证
if [ $# -ne 2 ]; then
    log_error "使用方法: $0 <image-tag> <auth-token>"
    log_error "示例: $0 'ghcr.io/user/app:v1.0.0' 'Bearer your-token'"
    exit 1
fi

IMAGE_TAG="$1"
AUTH_TOKEN="$2"

# 配置常量
NAMESPACE="agent-build"
DEPLOYMENT_NAME="gt-planner-backend-test"
CONTAINER_NAME="gt-planner-backend-test"
K8S_API_BASE="http://kuboard.sensedeal.wiki/k8s-api"

# 构建API端点
endpoint="$K8S_API_BASE/apis/apps/v1/namespaces/$NAMESPACE/deployments/$DEPLOYMENT_NAME"

# 验证部署函数
deploy_to_kubernetes() {
    log_info "🚀 开始Kubernetes测试环境部署..."
    
    # 参数验证
    if [ -z "$IMAGE_TAG" ] || [ -z "$AUTH_TOKEN" ]; then
        log_error "镜像标签和认证令牌不能为空"
        return 1
    fi
    
    log_info "部署参数验证通过:"
    log_info "  镜像: $IMAGE_TAG"
    log_info "  命名空间: $NAMESPACE"
    log_info "  部署名称: $DEPLOYMENT_NAME"
    
    # 检查目标deployment是否存在
    log_info "检查目标deployment是否存在..."
    check_response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $AUTH_TOKEN" "$endpoint" 2>&1 || echo -e "\n000")
    check_http_code=$(echo "$check_response" | tail -n1)
    check_response_body=$(echo "$check_response" | head -n -1)
    
    debug_log "检查请求HTTP状态码: $check_http_code"
    debug_log "检查请求响应体: $check_response_body"
    
    case "$check_http_code" in
        200)
            log_success "目标deployment存在，可以进行更新"
            ;;
        401)
            log_error "认证失败 (HTTP 401): 无法访问deployment"
            log_error "请检查认证令牌和权限配置"
            return 1
            ;;
        403)
            log_error "权限被拒绝 (HTTP 403): 无法访问deployment"
            log_error "用户没有权限访问该资源"
            
            # 检测匿名用户访问
            if echo "$check_response_body" | grep -q "system:anonymous"; then
                log_error "检测到匿名用户访问，认证令牌可能无效"
            fi
            
            log_warning "建议检查项目:"
            log_warning "  1. 服务账户是否存在"
            log_warning "  2. RBAC权限是否正确配置"
            log_warning "  3. 认证令牌是否有效且未过期"
            return 1
            ;;
        404)
            log_error "资源未找到 (HTTP 404): deployment不存在"
            log_error "请确认deployment名称和命名空间是否正确"
            return 1
            ;;
        000)
            log_error "网络连接失败: 无法连接到Kubernetes API"
            log_error "请检查网络连接和API端点配置"
            return 1
            ;;
        *)
            log_error "未知错误 (HTTP $check_http_code): 无法检查deployment状态"
            debug_log "响应内容: $check_response_body"
            return 1
            ;;
    esac
    
    # 构建补丁数据
    patch_payload=$(cat <<EOF
{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "$CONTAINER_NAME",
            "image": "$IMAGE_TAG"
          }
        ]
      }
    }
  }
}
EOF
)
    
    debug_log "补丁数据: $patch_payload"
    
    # 执行部署更新
    log_info "执行deployment更新..."
    response=$(curl -s -w "\n%{http_code}" -X PATCH \
        -H "content-type: application/strategic-merge-patch+json" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -d "$patch_payload" "$endpoint" 2>&1 || echo -e "\n000")
    
    # 分离响应体和HTTP状态码
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    debug_log "部署请求HTTP状态码: $http_code"
    debug_log "部署请求响应体: $response_body"
    
    # 严格的HTTP状态码检查
    case "$http_code" in
        200)
            log_success "HTTP请求成功"
            ;;
        401)
            log_error "认证失败 (HTTP 401)"
            log_error "认证令牌无效或已过期"
            return 1
            ;;
        403)
            log_error "权限被拒绝 (HTTP 403)"
            log_error "用户没有权限修改deployment"
            
            # 检测匿名用户访问
            if echo "$response_body" | grep -q "system:anonymous"; then
                log_error "检测到匿名用户访问，认证令牌可能无效"
            fi
            
            log_warning "建议检查项目:"
            log_warning "  1. 服务账户是否存在"
            log_warning "  2. RBAC权限是否正确配置"
            log_warning "  3. 认证令牌是否有效且未过期"
            return 1
            ;;
        404)
            log_error "资源未找到 (HTTP 404)"
            log_error "deployment或命名空间不存在"
            return 1
            ;;
        422)
            log_error "请求数据无效 (HTTP 422)"
            log_error "补丁数据格式可能有误"
            debug_log "响应详情: $response_body"
            return 1
            ;;
        000)
            log_error "网络连接失败"
            log_error "无法连接到Kubernetes API服务器"
            return 1
            ;;
        *)
            log_error "未知错误 (HTTP $http_code)"
            debug_log "响应内容: $response_body"
            return 1
            ;;
    esac
    
    # 检查Kubernetes API响应状态
    if echo "$response_body" | jq -e '.status == "Failure"' >/dev/null 2>&1; then
        log_error "Kubernetes API返回失败状态"
        local error_message=$(echo "$response_body" | jq -r '.message // "未知错误"' 2>/dev/null || echo "解析错误信息失败")
        log_error "错误信息: $error_message"
        return 1
    fi
    
    # 验证响应包含预期的deployment信息
    if echo "$response_body" | jq -e '.kind == "Deployment"' >/dev/null 2>&1; then
        log_success "Kubernetes API响应验证通过"
        local updated_image=$(echo "$response_body" | jq -r '.spec.template.spec.containers[0].image // "未知"' 2>/dev/null || echo "解析失败")
        log_success "部署镜像已更新为: $updated_image"
    else
        log_warning "无法验证API响应格式，但HTTP状态码表示成功"
        debug_log "响应内容: $response_body"
    fi
    
    log_success "✨ 测试环境部署成功!"
    log_info "部署详情:"
    log_info "  命名空间: $NAMESPACE"
    log_info "  部署名称: $DEPLOYMENT_NAME"
    log_info "  容器名称: $CONTAINER_NAME"
    log_info "  镜像标签: $IMAGE_TAG"
    
    return 0
}

# 主函数
main() {
    if [ "$DEBUG_MODE" = "true" ]; then
        log_info "🔍 调试模式已启用"
    fi
    
    # 执行部署
    if deploy_to_kubernetes; then
        log_success "🎉 部署操作完成!"
        exit 0
    else
        log_error "💥 测试环境部署失败!"
        exit 1
    fi
}

# 执行主函数
main "$@"
