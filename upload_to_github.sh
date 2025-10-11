#!/usr/bin/env bash
# File: upload_to_github.sh
# 用法: ./upload_to_github.sh [GitHub用户名] [仓库名]
# 示例: ./upload_to_github.sh yourusername Medical_AI_Agent
set -eu

################################
# 配置区域
################################
GITHUB_DOMAIN="github.com"
DEFAULT_USERNAME="hmyjc"  # 请修改为您的GitHub用户名
DEFAULT_REPO_NAME="medai"

# Medical AI Agent 项目特定的忽略规则
MEDICAL_AI_IGNORE_RULES=(
  "# IDE files"
  ".idea/"
  ".vscode/"
  "*.code-workspace"
  "*.swp"
  "*.swo"

  "# Python compiled files"
  "__pycache__/"
  "*.py[cod]"
  "*.pyd"
  "*.pyo"
  "*.pyd"
  "*.so"
  "*.egg"
  "*.egg-info/"
  "dist/"
  "build/"

  "# Virtual environments"
  "venv/"
  "env/"
  ".venv/"
  ".env/"
  "medical_ai_agent/"

  "# Jupyter Notebook checkpoints"
  ".ipynb_checkpoints/"
  "*.ipynb_checkpoints"

  "# Log files"
  "logs/"
  "*.log"
  "log/"

  "# Environment variables and secrets"
  ".env"
  ".env.local"
  ".env.production"
  ".secret"
  "config.py"
  "secrets.json"

  "# API Keys and sensitive data"
  "*.key"
  "*.pem"
  "*.p12"
  "*.pfx"

  "# OS generated files"
  ".DS_Store"
  "Thumbs.db"
  "desktop.ini"
  "*.tmp"
  "*.temp"

  "# Coverage and testing"
  ".coverage"
  "htmlcov/"
  ".pytest_cache/"
  ".tox/"
  ".mypy_cache/"

  "# Node.js (for frontend)"
  "node_modules/"
  "npm-debug.log*"
  "yarn-debug.log*"
  "yarn-error.log*"
  ".npm"
  ".yarn"

  "# Frontend build files"
  "frontend/dist/"
  "frontend/build/"
  "frontend/.nuxt/"
  "frontend/.next/"
  "frontend/.cache/"

  "# Medical AI specific"
  "test_images/"
  "test_documents/"
  "uploads/"
  "temp/"
  "cache/"
  "*.dcm"
  "*.dicom"

  "# Database files"
  "*.db"
  "*.sqlite"
  "*.sqlite3"

  "# Backup files"
  "*.bak"
  "*.backup"
  "*.old"
)

################################
# 函数定义
################################
info(){ printf "\033[1;32m%s\033[0m\n" "$*"; }
warn(){ printf "\033[1;33m%s\033[0m\n" "$*"; }
err (){ printf "\033[1;31m%s\033[0m\n" "$*" >&2; }

# 检查依赖
check_dependencies() {
  local missing_deps=()
  
  command -v git >/dev/null 2>&1 || missing_deps+=("git")
  command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1 || missing_deps+=("python")
  command -v pip >/dev/null 2>&1 || command -v pip3 >/dev/null 2>&1 || missing_deps+=("pip")
  
  if [[ ${#missing_deps[@]} -gt 0 ]]; then
    err "❌ 缺少必要依赖: ${missing_deps[*]}"
    err "   请先安装这些依赖后再运行脚本"
    exit 1
  fi
}

# 创建或更新 .gitignore
update_gitignore() {
  local gitignore_path="$1/.gitignore"
  [[ -f $gitignore_path ]] || touch "$gitignore_path"

  info "🛡️  更新 .gitignore 文件"

  if ! grep -q "# Medical AI Agent Ignore Rules" "$gitignore_path"; then
    printf "\n# Medical AI Agent Ignore Rules\n# Added by upload script\n" >> "$gitignore_path"
  fi

  for rule in "${MEDICAL_AI_IGNORE_RULES[@]}"; do
    grep -qxF "$rule" "$gitignore_path" || echo "$rule" >> "$gitignore_path"
  done
}

# 清理被忽略的文件
cleanup_ignored_files() {
  info "🗑️  清理被忽略的文件..."
  
  # 移除已跟踪但应该被忽略的文件
  git ls-files -z --cached --exclude-standard -i | xargs -0 --no-run-if-empty git rm --cached -q || true
  
  # 清理临时文件
  find . -name "*.pyc" -delete 2>/dev/null || true
  find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
  find . -name ".DS_Store" -delete 2>/dev/null || true
}

# 检查项目结构
check_project_structure() {
  info "🔍 检查项目结构..."
  
  local required_files=(
    "requirements.txt"
    "config.py"
    "main.py"
    "agents.py"
    "utils.py"
    "run.py"
  )
  
  local required_dirs=(
    "frontend"
    "frontend/src"
    "frontend/src/pages"
    "frontend/src/store"
    "frontend/src/api"
  )
  
  for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
      warn "⚠️  缺少文件: $file"
    fi
  done
  
  for dir in "${required_dirs[@]}"; do
    if [[ ! -d "$dir" ]]; then
      warn "⚠️  缺少目录: $dir"
    fi
  done
}

# 创建 README.md
create_readme() {
  local readme_path="README.md"
  
  if [[ -f "$readme_path" ]]; then
    info "📄 README.md 已存在，跳过创建"
    return
  fi
  
  info "📄 创建 README.md 文件"
  
  cat > "$readme_path" << 'EOF'
# Medical AI Agent

一个基于FastAPI和uni-app的智能医疗助手系统，提供多种AI医疗功能。

## 🚀 功能特性

- **智能问诊**: AI医疗助手提供专业健康咨询
- **智能分诊**: 根据症状推荐合适科室
- **症状自诊**: 分析可能疾病并提供建议
- **报告解读**: 解读医学检查报告
- **皮肤病咨询**: 基于图片的皮肤病分析
- **病例整理**: 生成结构化病历信息
- **健康教育**: 提供医疗知识科普

## 🏗️ 技术架构

### 后端 (FastAPI)
- **框架**: FastAPI + Python 3.8+
- **AI模型**: 阿里云百炼 (Dashscope)
- **数据库**: 支持多种数据库
- **API**: RESTful API设计

### 前端 (uni-app)
- **框架**: uni-app + Vue 3
- **UI库**: uview-plus
- **构建工具**: Vite
- **样式**: SCSS

## 📦 安装部署

### 后端部署

1. **克隆项目**
```bash
git clone https://github.com/yourusername/Medical_AI_Agent.git
cd Medical_AI_Agent
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**
```bash
# 复制配置文件
cp config.py.example config.py
# 编辑配置文件，填入API密钥
```

4. **启动服务**
```bash
python run.py
```

### 前端部署

1. **进入前端目录**
```bash
cd frontend
```

2. **安装依赖**
```bash
npm install
```

3. **开发模式**
```bash
npm run dev:h5
```

4. **生产构建**
```bash
npm run build:h5
```

## 🔧 配置说明

### 后端配置 (config.py)

```python
# 阿里云百炼API配置
DASHSCOPE_API_KEY = "your-api-key"
TEXT_MODEL = "qwen-plus"
VISION_MODEL = "qwen-vl-plus"
```

### 前端配置 (frontend/src/api/index.js)

```javascript
// API地址配置
const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://127.0.0.1:8000' 
  : 'https://your-domain.com'
```

## 📚 API文档

启动后端服务后，访问 `http://localhost:8000/docs` 查看API文档。

### 主要接口

- `POST /api/medical-chat` - 智能问诊
- `POST /api/report-interpretation` - 报告解读
- `POST /api/dermatology-consultation` - 皮肤病咨询

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至: your-email@example.com

## 🙏 致谢

感谢以下开源项目的支持：
- [FastAPI](https://fastapi.tiangolo.com/)
- [uni-app](https://uniapp.dcloud.net.cn/)
- [uview-plus](https://www.uviewui.com/)
- [阿里云百炼](https://dashscope.aliyun.com/)
EOF
}

# 创建 LICENSE 文件
create_license() {
  local license_path="LICENSE"
  
  if [[ -f "$license_path" ]]; then
    info "📄 LICENSE 已存在，跳过创建"
    return
  fi
  
  info "📄 创建 MIT LICENSE 文件"
  
  cat > "$license_path" << 'EOF'
MIT License

Copyright (c) 2024 Medical AI Agent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
}

# 主处理函数
process_repo() {
  local github_username="$1"
  local repo_name="$2"
  
  info "📦 处理 Medical AI Agent 项目"
  info "🔗 GitHub 仓库: https://${GITHUB_DOMAIN}/${github_username}/${repo_name}"
  
  # 检查项目结构
  check_project_structure
  
  # 初始化或检查 Git 仓库
  if [[ ! -d .git ]]; then
    info "🆕 初始化 Git 仓库"
    git init
  fi
  
  # 设置远程仓库
  git remote remove origin >/dev/null 2>&1 || true
  git remote add origin "https://${GITHUB_DOMAIN}/${github_username}/${repo_name}.git"
  
  # 配置 Git 用户信息
  git config user.name "$github_username"
  git config user.email "${github_username}@users.noreply.${GITHUB_DOMAIN}"
  
  # 更新 .gitignore
  update_gitignore "$PWD"
  
  # 清理被忽略的文件
  cleanup_ignored_files
  
  # 创建必要文件
  create_readme
  create_license
  
  # 添加所有文件
  git add --all
  
  # 提交更改
  info "💾 提交更改"
  git commit -m "Initial commit: Medical AI Agent project

- 智能医疗助手后端系统 (FastAPI)
- 前端界面 (uni-app + Vue 3)
- 多种AI医疗功能模块
- 完整的项目文档和配置" --allow-empty
  
  # 推送到 GitHub
  info "🚀 推送到 GitHub"
  git branch -M main >/dev/null 2>&1 || true
  
  if ! git push -u origin main --force; then
    warn "⚠️  推送失败! 可能仓库尚未在 GitHub 创建"
    warn "   请手动创建仓库: https://${GITHUB_DOMAIN}/${github_username}/${repo_name}"
    warn "   或者检查网络连接和权限"
    return 1
  fi
  
  info "✅ 项目已成功上传到 GitHub!"
  info "🔗 仓库地址: https://${GITHUB_DOMAIN}/${github_username}/${repo_name}"
}

# 显示帮助信息
show_help() {
  cat << EOF
Medical AI Agent GitHub 上传脚本

用法:
  $0 [GitHub用户名] [仓库名]

参数:
  GitHub用户名    您的 GitHub 用户名
  仓库名          仓库名称 (默认: Medical_AI_Agent)

示例:
  $0 yourusername Medical_AI_Agent
  $0 yourusername my-medical-ai

功能:
  - 自动初始化 Git 仓库
  - 创建适合的 .gitignore 文件
  - 生成项目 README.md 和 LICENSE
  - 清理敏感文件和临时文件
  - 推送到 GitHub 仓库

注意事项:
  - 请确保已在 GitHub 创建对应仓库
  - 确保有推送权限
  - 敏感信息 (如 API 密钥) 会被自动忽略
EOF
}

# 主函数
main() {
  local github_username="${1:-$DEFAULT_USERNAME}"
  local repo_name="${2:-$DEFAULT_REPO_NAME}"
  
  # 显示帮助
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_help
    exit 0
  fi
  
  info "🚩 Medical AI Agent GitHub 上传脚本"
  echo   "========================================"
  echo   "⚙️ 配置:"
  echo   " - GitHub 用户名: $github_username"
  echo   " - 仓库名称    : $repo_name"
  echo   " - 仓库地址    : https://${GITHUB_DOMAIN}/${github_username}/${repo_name}"
  echo   "========================================"
  
  # 检查依赖
  check_dependencies
  
  # 检查是否在项目根目录
  if [[ ! -f "main.py" || ! -d "frontend" ]]; then
    err "❌ 请在 Medical AI Agent 项目根目录下运行此脚本"
    err "   确保 main.py 和 frontend/ 目录存在"
    exit 1
  fi
  
  # 处理仓库
  process_repo "$github_username" "$repo_name"
  
  echo "========================================"
  info "🎉 上传完成！"
  info "📖 查看仓库: https://${GITHUB_DOMAIN}/${github_username}/${repo_name}"
}

################################
# 执行入口
################################
main "$@"
