# 微信支付功能配置说明

## 概述

已为医疗智能体的四个功能模块添加了微信支付功能，每次使用收费9.9元：

- 📋 **报告解读** - 医学报告智能解读服务
- 💊 **药物咨询** - 专业药物咨询指导服务  
- 📚 **健康科普** - 权威健康知识科普服务
- 🩺 **皮肤病诊断** - 皮肤病智能诊断分析服务

## 后端配置

### 1. 微信支付参数配置

在 `config.py` 中配置微信支付参数：

```python
WECHAT_PAY_CONFIG = {
    "app_id": "your_app_id",        # 微信小程序AppID
    "mch_id": "your_mch_id",        # 商户号
    "api_key": "your_api_key",      # API密钥
    "notify_url": "https://your-domain.com/api/payment/notify",  # 支付回调地址
    "cert_path": "certs/apiclient_cert.pem",
    "key_path": "certs/apiclient_key.pem"
}
```

### 2. 证书文件

确保 `certs` 目录下有以下文件：
- `apiclient_cert.pem` - 商户证书
- `apiclient_key.pem` - 商户私钥
- `apiclient_cert.p12` - PKCS#12格式证书
- `pub_key.pem` - 公钥

### 3. 新增API接口

- `POST /api/payment/create` - 创建支付订单
- `POST /api/payment/query` - 查询支付状态
- `POST /api/payment/notify` - 支付回调接口
- `GET /api/payment/services` - 获取付费服务列表

### 4. 修改现有接口

所有付费服务接口都添加了 `payment_verified` 参数：
- `POST /api/report-interpretation`
- `POST /api/health-education`
- `POST /api/dermatology-consultation`
- `POST /api/medication-consultation`

## 前端配置

### 1. API接口

在 `frontend/src/api/index.js` 中新增了 `paymentApi` 对象：

```javascript
export const paymentApi = {
  createPayment: (serviceType, openid),    // 创建支付订单
  queryPayment: (outTradeNo),             // 查询支付状态
  getPaymentServices: (),                 // 获取付费服务列表
  requestPayment: (payParams)              // 发起微信支付
}
```

### 2. 页面修改

已修改 `frontend/src/pages/reports/index.vue` 作为示例：

- 添加支付状态管理
- 集成支付流程
- 更新UI显示支付按钮
- 添加支付验证逻辑

### 3. 支付流程

1. 用户选择文件/输入问题
2. 点击"支付解读"按钮
3. 创建支付订单
4. 发起微信支付
5. 支付成功后验证状态
6. 调用对应的智能体服务

## 配置步骤

### 1. 微信商户平台配置

1. 登录微信商户平台
2. 获取商户号（mch_id）
3. 设置API密钥（api_key）
4. 下载证书文件到 `certs` 目录

### 2. 微信小程序配置

1. 在小程序后台配置支付域名
2. 获取小程序AppID
3. 配置支付回调URL

### 3. 后端配置

1. 修改 `config.py` 中的支付参数
2. 确保证书文件路径正确
3. 配置HTTPS域名（生产环境）

### 4. 前端配置

1. 获取用户openid（通过微信登录）
2. 配置支付域名白名单
3. 测试支付流程

## 其他页面配置

需要为以下页面添加类似的支付功能：

### 1. 药物咨询页面 (`frontend/src/pages/medication/index.vue`)

```javascript
// 添加支付相关状态
const isPaying = ref(false)
const paymentVerified = ref(false)

// 添加支付方法
const handlePayment = async () => {
  // 支付逻辑
}

// 修改咨询方法
const consultMedication = async () => {
  // 检查支付状态
  if (!paymentVerified.value) {
    // 显示支付弹窗
    return
  }
  // 调用API
}
```

### 2. 健康科普页面 (`frontend/src/pages/health/index.vue`)

### 3. 皮肤病诊断页面 (`frontend/src/pages/dermatology/index.vue`)

## 测试流程

### 1. 开发环境测试

1. 使用微信开发者工具
2. 配置测试商户号
3. 使用测试金额（0.01元）

### 2. 生产环境部署

1. 配置正式商户号
2. 部署HTTPS服务
3. 配置支付回调URL
4. 测试完整支付流程

## 注意事项

### 1. 安全注意事项

- 证书文件不要提交到版本控制
- API密钥要妥善保管
- 支付回调要验证签名

### 2. 用户体验

- 支付失败要有友好提示
- 支付成功后要自动跳转
- 支持支付状态查询

### 3. 业务逻辑

- 支付成功后要记录订单
- 支持退款处理
- 防止重复支付

## 故障排除

### 1. 常见问题

- 证书路径错误
- API密钥配置错误
- 域名白名单未配置
- 支付回调URL错误

### 2. 调试方法

- 查看后端日志
- 检查微信支付日志
- 使用微信支付调试工具

## 完成状态

- ✅ 后端支付接口开发
- ✅ 前端支付集成（报告解读页面）
- ✅ 支付流程设计
- ⏳ 其他页面支付集成
- ⏳ 生产环境配置
- ⏳ 完整测试流程

需要继续完成其他三个页面的支付功能集成。

