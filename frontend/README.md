# 医疗智能体前端

基于 uni-app + Vue3 + Pinia 构建的医疗智能体前端应用，支持微信小程序、H5等多端部署。

## 🌟 项目特色

### 完整的医疗AI功能
- **智能问诊** - 支持意图识别和多智能体对话
- **报告解读** - 上传医学报告获得专业解读
- **健康科普** - 权威医学知识查询
- **皮肤病咨询** - 图片分析+文字描述
- **药物咨询** - 基于药品说明书的用药指导

### 技术亮点
- 🎯 **版本兼容** - dcloud版本与参考项目完全一致
- 🔄 **状态管理** - Pinia状态管理，数据持久化
- 📱 **多端适配** - 支持微信小程序、H5、App等
- 🎨 **现代UI** - 医疗主题设计，响应式布局
- 🚀 **性能优化** - 组件懒加载，代码分割

## 📦 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| **uni-app** | `3.0.0-4070520250711001` | ✅ 与mirror_history_ai完全一致 |
| **Vue** | `3.5.18` | 最新稳定版 |
| **Pinia** | `2.0.36` | 状态管理 |
| **uview-plus** | `^3.4.45` | UI组件库 |
| **Vite** | `5.2.8` | 构建工具 |

## 🚀 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务

```bash
# 微信小程序
npm run dev:mp-weixin

# H5
npm run dev:h5

# 支付宝小程序
npm run dev:mp-alipay
```

### 3. 构建发布

```bash
# 微信小程序
npm run build:mp-weixin

# H5生产版本
npm run build:h5
```

## 📁 项目结构

```
frontend/
├── src/
│   ├── pages/                 # 页面文件
│   │   ├── home/             # 首页
│   │   ├── chat/             # 智能问诊
│   │   ├── reports/          # 报告解读
│   │   ├── health/           # 健康科普
│   │   ├── dermatology/      # 皮肤病咨询
│   │   ├── medication/       # 药物咨询
│   │   ├── history/          # 历史记录
│   │   └── profile/          # 个人中心
│   ├── components/           # 公共组件
│   ├── api/                  # API接口
│   ├── store/                # 状态管理
│   │   ├── chat.js          # 聊天状态
│   │   ├── history.js       # 历史记录
│   │   └── user.js          # 用户状态
│   ├── styles/              # 样式文件
│   ├── static/              # 静态资源
│   ├── App.vue              # 根组件
│   ├── main.js              # 入口文件
│   ├── pages.json           # 页面配置
│   ├── manifest.json        # 应用配置
│   └── uni.scss             # 全局样式
├── package.json             # 依赖配置
├── vite.config.js          # 构建配置
└── README.md               # 项目说明
```

## 🔧 核心功能

### 页面路由配置

```json
{
  "pages": [
    {
      "path": "pages/home/index",
      "style": { "navigationBarTitleText": "医疗智能体" }
    },
    {
      "path": "pages/chat/index", 
      "style": { "navigationBarTitleText": "智能问诊" }
    }
    // ... 其他页面
  ],
  "tabBar": {
    "list": [
      { "pagePath": "pages/home/index", "text": "首页" },
      { "pagePath": "pages/chat/index", "text": "问诊" },
      { "pagePath": "pages/history/index", "text": "历史" },
      { "pagePath": "pages/profile/index", "text": "我的" }
    ]
  }
}
```

### API接口配置

```javascript
// api/index.js
const API_BASE_URL = isMP 
  ? 'https://your-domain.com'        // 生产环境
  : '/api'                           // 开发代理

// 主要接口
export const medicalChatApi = {
  sendMessage: (data) => request('/api/medical-chat', { method: 'POST', data })
}

export const reportApi = {
  uploadAndInterpret: (filePath, fileName) => { /* 文件上传 */ }
}
```

### 状态管理

```javascript
// store/chat.js
export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [],           // 聊天记录
    loading: false,         // 加载状态
    currentSessionId: null  // 会话ID
  }),
  actions: {
    addUserMessage(content) { /* 添加用户消息 */ },
    addAIMessage(content) { /* 添加AI回复 */ }
  }
})
```

## 🎨 UI设计规范

### 色彩方案
- **主色调** - `#1658FF` (医疗蓝)
- **成功色** - `#28a745` (绿色)
- **警告色** - `#ffc107` (黄色) 
- **危险色** - `#dc3545` (红色)

### 医疗主题样式
```scss
.medical-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}
```

## 📱 平台适配

### 微信小程序
- **开发工具** - 微信开发者工具
- **调试命令** - `npm run dev:mp-weixin`
- **真机预览** - 扫码预览
- **发布流程** - 上传代码 → 提交审核 → 发布

### H5版本
- **开发服务** - `npm run dev:h5`
- **本地访问** - http://localhost:3000
- **部署方式** - 静态文件部署

### App版本
- **开发工具** - HBuilderX
- **打包配置** - manifest.json
- **发布平台** - 各大应用商店

## 🔄 与后端集成

### 开发环境
```javascript
// vite.config.js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // 后端服务地址
      changeOrigin: true
    }
  }
}
```

### 生产环境
```javascript
// 配置域名
const API_BASE_URL = 'https://your-medical-api.com'
```

### 接口对接
- `/api/medical-chat` - 主入口智能对话
- `/api/report-interpretation` - 报告解读
- `/api/health-education` - 健康科普
- `/api/dermatology-consultation` - 皮肤病咨询
- `/api/medication-consultation` - 药物咨询

## 📊 功能模块

### 1. 智能问诊 (`pages/chat/`)
- 意图识别展示
- 多智能体对话
- 实时消息流
- 会话管理

### 2. 报告解读 (`pages/reports/`)
- 文件上传 (Word/PDF)
- 解读结果展示
- 历史记录查看

### 3. 健康科普 (`pages/health/`)
- 关键词搜索
- 热门话题
- 搜索历史

### 4. 皮肤病咨询 (`pages/dermatology/`)
- 图片拍摄/选择
- 症状描述
- AI分析结果

### 5. 历史记录 (`pages/history/`)
- 记录分类筛选
- 搜索功能
- 数据导出

## 🛠️ 开发指南

### 添加新页面
1. 在 `src/pages/` 创建页面目录
2. 在 `pages.json` 注册路由
3. 实现页面组件

### 状态管理
```javascript
// 1. 创建store
export const useNewStore = defineStore('new', {
  state: () => ({ data: [] }),
  actions: { addData(item) { this.data.push(item) } }
})

// 2. 在组件中使用
const newStore = useNewStore()
```

### API接口
```javascript
// 1. 在api/index.js添加接口
export const newApi = {
  getData: () => request('/api/new-endpoint')
}

// 2. 在组件中调用
import { newApi } from '@/api'
const result = await newApi.getData()
```

## 🔧 调试技巧

### 微信小程序调试
1. 开启调试模式
2. 查看Console输出
3. Network面板查看接口
4. Storage查看本地数据

### H5调试
1. 浏览器开发者工具
2. 移动设备模拟
3. 网络请求监控

### 常见问题
- **跨域问题** - 配置代理或CORS
- **图片不显示** - 检查路径和权限
- **接口调用失败** - 验证URL和参数

## 📋 部署清单

### 微信小程序发布
- [ ] 配置AppID
- [ ] 设置服务器域名
- [ ] 隐私协议配置
- [ ] 功能页面截图
- [ ] 提交审核资料

### H5部署
- [ ] 构建生产版本
- [ ] 配置CDN/服务器
- [ ] SSL证书配置
- [ ] 域名解析

## 📞 技术支持

- **开发文档** - [uni-app官方文档](https://uniapp.dcloud.net.cn/)
- **UI组件** - [uview-plus文档](https://uviewui.com/)
- **状态管理** - [Pinia文档](https://pinia.vuejs.org/)

## 🎉 项目成果

✅ **完整功能** - 5大医疗AI功能模块
✅ **多端适配** - 微信小程序、H5、App
✅ **现代架构** - Vue3 + Pinia + TypeScript支持
✅ **用户体验** - 响应式设计，流畅交互
✅ **数据管理** - 完整的状态管理和持久化
