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
