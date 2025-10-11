/**
 * 🏥 医疗智能体前端 API 统一入口
 * - 真机 / 微信开发者工具（mp-weixin）必须用完整 HTTPS 域名
 * - 其余平台开发环境可走本地代理 `/api`
 */
const isMP = process.env.UNI_PLATFORM === 'mp-weixin'

// API地址配置
const DOMAIN_SERVER_URL = 'https://your-domain.com'  // 生产环境域名HTTPS访问
const LOCAL_SERVER_URL = 'http://localhost:8000'     // 本地开发服务器
const DEV_SERVER_URL = 'http://your-dev-server.com'  // 开发服务器

// 根据平台选择API地址
const API_BASE_URL = isMP
  ? DOMAIN_SERVER_URL  // 微信小程序使用HTTPS域名（真机环境必须）
  : (process.env.NODE_ENV === 'development'
       ? 'http://127.0.0.1:8000'  // 开发环境直接使用后端地址
      : DOMAIN_SERVER_URL)  // H5生产环境使用域名HTTPS

// 调试模式配置
const isDebug = import.meta.env?.VITE_DEBUG === 'true' || process.env.NODE_ENV === 'development'

// 调试日志函数
const debugLog = (...args) => {
  if (isDebug) {
    console.log('[API-DEBUG]', new Date().toLocaleTimeString(), ...args)
  }
}

// 输出当前API配置信息
console.log('🔧 医疗AI API配置信息:', {
  isMP,
  API_BASE_URL,
  isDebug,
  platform: process.env.UNI_PLATFORM,
  nodeEnv: process.env.NODE_ENV
})

// 请求拦截器（增强调试功能，支持备用地址）
const request = (url, options = {}) => {
  const makeRequest = (baseUrl, isRetry = false) => {
    const fullUrl = `${baseUrl}${url}`
    const requestId = Date.now() + Math.random().toString(36).substr(2, 9)
    
    // 调试日志
    if (isDebug) {
      debugLog(`📤 [${requestId}] ${isRetry ? '重试' : '发起'}请求:`, {
        url: fullUrl,
        method: options.method || 'GET',
        data: options.data,
        isRetry
      })
    }
    
    return new Promise((resolve, reject) => {
      const startTime = Date.now()
      
      uni.request({
        url: fullUrl,
        method: options.method || 'GET',
        data: options.data || {},
        timeout: options.timeout || 30000,
        header: {
          'Content-Type': 'application/json',
          'X-Request-ID': requestId,
          ...options.header
        },
        success: (res) => {
          console.log('👍 医疗AI请求:', options.method || 'GET', fullUrl)
          console.log('🔙 响应结果:', res.statusCode, res.data)
          const duration = Date.now() - startTime
          
          if (isDebug) {
            debugLog(`📥 [${requestId}] 请求响应 (${duration}ms):`, {
              status: res.statusCode,
              data: res.data,
              baseUrl
            })
          }
          
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data)
          } else {
            const error = new Error(res.data?.message || '请求失败')
            if (isDebug) {
              debugLog(`❌ [${requestId}] 请求失败:`, error)
            }
            reject(error)
          }
        },
        fail: (error) => {
          const duration = Date.now() - startTime
          if (isDebug) {
            debugLog(`💥 [${requestId}] 网络错误 (${duration}ms):`, {
              error: error.errMsg,
              baseUrl,
              isRetry
            })
          }
          reject(new Error(error.errMsg || '网络请求失败'))
        }
      })
    })
  }
  
  // 主请求，如果失败尝试备用地址
  return makeRequest(API_BASE_URL).catch(error => {
    // 开发环境才使用备用地址
    const backupUrl = process.env.NODE_ENV === 'development' ? LOCAL_SERVER_URL : null
    if (backupUrl && API_BASE_URL !== backupUrl) {
      console.log('🔄 主地址失败，尝试备用地址:', backupUrl)
      return makeRequest(backupUrl, true)
    }
    throw error
  })
}

// 医疗聊天API - 主入口功能
export const medicalChatApi = {
  // 智能医疗对话（主入口）
  sendMessage: (data) => {
    debugLog('发送医疗对话消息:', data)
    return request('/api/medical-chat', {
      method: 'POST',
      data,
      timeout: 120000  // 2分钟超时，专门为AI对话设置
    })
  }
}

// 支付API
export const paymentApi = {
  // 创建支付订单
  createPayment: (serviceType, openid) => {
    debugLog('创建支付订单:', { serviceType, openid })
    
    return new Promise((resolve, reject) => {
      uni.request({
        url: `${API_BASE_URL}/api/payment/create`,
        method: 'POST',
        data: {
          service_type: serviceType,
          openid: openid
        },
        header: {
          'Content-Type': 'application/json',
          'X-Request-ID': Date.now() + Math.random().toString(36).substr(2, 9)
        },
        success: (res) => {
          debugLog('支付订单创建成功:', res)
          if (res.statusCode === 200 && res.data.success) {
            resolve(res.data)
          } else {
            reject(new Error(res.data.message || '创建支付订单失败'))
          }
        },
        fail: (error) => {
          debugLog('支付订单创建失败:', error)
          reject(new Error(error.errMsg || '网络请求失败'))
        }
      })
    })
  },

  // 查询支付状态
  queryPayment: (outTradeNo) => {
    debugLog('查询支付状态:', { outTradeNo })
    
    return new Promise((resolve, reject) => {
      uni.request({
        url: `${API_BASE_URL}/api/payment/query`,
        method: 'POST',
        data: { out_trade_no: outTradeNo },
        header: {
          'Content-Type': 'application/json',
          'X-Request-ID': Date.now() + Math.random().toString(36).substr(2, 9)
        },
        success: (res) => {
          debugLog('支付状态查询成功:', res)
          if (res.statusCode === 200 && res.data.success) {
            resolve(res.data)
          } else {
            reject(new Error(res.data.message || '查询支付状态失败'))
          }
        },
        fail: (error) => {
          debugLog('支付状态查询失败:', error)
          reject(new Error(error.errMsg || '网络请求失败'))
        }
      })
    })
  },

  // 获取付费服务列表
  getPaymentServices: () => {
    debugLog('获取付费服务列表')
    
    return new Promise((resolve, reject) => {
      uni.request({
        url: `${API_BASE_URL}/api/payment/services`,
        method: 'GET',
        header: {
          'X-Request-ID': Date.now() + Math.random().toString(36).substr(2, 9)
        },
        success: (res) => {
          debugLog('付费服务列表获取成功:', res)
          if (res.statusCode === 200 && res.data.success) {
            resolve(res.data)
          } else {
            reject(new Error(res.data.message || '获取付费服务列表失败'))
          }
        },
        fail: (error) => {
          debugLog('付费服务列表获取失败:', error)
          reject(new Error(error.errMsg || '网络请求失败'))
        }
      })
    })
  },

  // 微信小程序支付
  requestPayment: (payParams) => {
    debugLog('发起微信支付:', payParams)
    
    return new Promise((resolve, reject) => {
      uni.requestPayment({
        provider: 'wxpay',
        timeStamp: payParams.timeStamp,
        nonceStr: payParams.nonceStr,
        package: payParams.package,
        signType: payParams.signType,
        paySign: payParams.paySign,
        success: (res) => {
          debugLog('微信支付成功:', res)
          resolve(res)
        },
        fail: (error) => {
          debugLog('微信支付失败:', error)
          reject(error)
        }
      })
    })
  }
}

// 报告解读API
export const reportApi = {
  // 上传并解读报告
  uploadAndInterpret: (filePath, fileName) => {
    debugLog('上传报告文件:', { filePath, fileName })
    
    // H5环境下使用fetch上传，非H5环境使用uni.uploadFile
    if (process.env.UNI_PLATFORM === 'h5') {
      return reportApi.uploadFileH5(filePath, fileName)
    }
    
    return new Promise((resolve, reject) => {
      uni.uploadFile({
        url: `${API_BASE_URL}/api/report-interpretation`,
        filePath: filePath,
        name: 'file',
        formData: {
          'filename': fileName
        },
        header: {
          'X-Request-ID': Date.now() + Math.random().toString(36).substr(2, 9)
        },
        success: (res) => {
          debugLog('报告上传成功:', res)
          try {
            if (res.statusCode === 200) {
              resolve(JSON.parse(res.data))
            } else {
              reject(new Error(`报告解读失败: ${res.statusCode}`))
            }
          } catch (error) {
            reject(new Error('响应解析失败'))
          }
        },
        fail: (error) => {
          debugLog('报告上传失败:', error)
          reject(new Error(error.errMsg || '文件上传失败'))
        }
      })
    })
  },

  // H5环境专用的文件上传方法
  uploadFileH5: async (file, fileName) => {
    try {
      const formData = new FormData()
      formData.append('file', file, fileName)
      
      const response = await fetch(`${API_BASE_URL}/api/report-interpretation`, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Request-ID': Date.now() + Math.random().toString(36).substr(2, 9)
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const result = await response.json()
      debugLog('H5报告上传成功:', result)
      return result
      
    } catch (error) {
      debugLog('H5报告上传失败:', error)
      throw error
    }
  }
}

// 健康科普API
export const healthEducationApi = {
  // 健康知识查询
  query: (data) => {
    debugLog('健康科普查询:', data)
    return request('/api/health-education', {
      method: 'POST',
      data,
      timeout: 60000
    })
  }
}

// 皮肤病咨询API
export const dermatologyApi = {
  // 上传皮肤图片并咨询
  uploadAndConsult: (filePath, symptoms = '') => {
    debugLog('皮肤病咨询:', { filePath, symptoms })
    
    // H5环境下使用fetch上传，非H5环境使用uni.uploadFile
    if (process.env.UNI_PLATFORM === 'h5') {
      return dermatologyApi.uploadImageH5(filePath, symptoms)
    }
    
    return new Promise((resolve, reject) => {
      uni.uploadFile({
        url: `${API_BASE_URL}/api/dermatology-consultation`,
        filePath: filePath,
        name: 'file',
        formData: {
          'symptoms': symptoms
        },
        header: {
          'X-Request-ID': Date.now() + Math.random().toString(36).substr(2, 9)
        },
        success: (res) => {
          debugLog('皮肤病咨询成功:', res)
          try {
            if (res.statusCode === 200) {
              resolve(JSON.parse(res.data))
            } else {
              reject(new Error(`皮肤病咨询失败: ${res.statusCode}`))
            }
          } catch (error) {
            reject(new Error('响应解析失败'))
          }
        },
        fail: (error) => {
          debugLog('皮肤病咨询失败:', error)
          reject(new Error(error.errMsg || '图片上传失败'))
        }
      })
    })
  },

  // H5环境专用的图片上传方法
  uploadImageH5: async (file, symptoms = '') => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('symptoms', symptoms)
      
      const response = await fetch(`${API_BASE_URL}/api/dermatology-consultation`, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Request-ID': Date.now() + Math.random().toString(36).substr(2, 9)
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const result = await response.json()
      debugLog('H5皮肤病咨询成功:', result)
      return result
      
    } catch (error) {
      debugLog('H5皮肤病咨询失败:', error)
      throw error
    }
  }
}

// 药物咨询API
export const medicationApi = {
  // 药物咨询查询
  query: (data) => {
    debugLog('药物咨询查询:', data)
    return request('/api/medication-consultation', {
      method: 'POST',
      data,
      timeout: 60000
    })
  }
}

// 系统API
export const systemApi = {
  // 健康检查
  healthCheck: () => request('/api/health'),
  
  // 获取系统配置
  getConfig: () => request('/api/config')
}

// 请求错误处理
export const handleApiError = (error) => {
  console.error('医疗AI API错误:', error)
  
  // 根据错误类型处理
  if (error.message.includes('网络')) {
    uni.showToast({
      title: '网络连接失败',
      icon: 'error'
    })
  } else if (error.message.includes('超时')) {
    uni.showToast({
      title: '请求超时，请重试',
      icon: 'error'
    })
  } else if (error.message.includes('500')) {
    uni.showToast({
      title: '服务器错误',
      icon: 'error'
    })
  } else if (error.message.includes('400')) {
    uni.showToast({
      title: '请求参数错误',
      icon: 'error'
    })
  } else {
    uni.showToast({
      title: error.message || '请求失败',
      icon: 'error'
    })
  }
}

// 导出所有API
export default {
  medicalChatApi,
  reportApi,
  healthEducationApi,
  dermatologyApi,
  medicationApi,
  systemApi,
  handleApiError
}
