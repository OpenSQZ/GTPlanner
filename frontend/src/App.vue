<script>
export default {
  name: 'App',
  onLaunch: function () {
    console.log('医疗智能体应用启动')
    
    // 检查系统健康状态
    this.checkSystemHealth()
  },
  onShow: function () {
    console.log('医疗智能体应用显示')
  },
  onHide: function () {
    console.log('医疗智能体应用隐藏')
  },
  methods: {
    async checkSystemHealth() {
      try {
        const { systemApi } = await import('@/api/index.js')
        await systemApi.healthCheck()
        console.log('✅ 医疗AI后端服务连接正常')
      } catch (error) {
        console.warn('⚠️ 医疗AI后端服务连接异常:', error.message)
      }
    }
  }
}
</script>

<style lang="scss">
/* 全局样式 */
page {
  background-color: #f8f9fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Helvetica Neue', STHeiti, 'Microsoft Yahei', Tahoma, Simsun, sans-serif;
}

.container {
  padding: 20rpx;
}

.page-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
  text-align: center;
}

.card {
  background: #fff;
  border-radius: 12rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.1);
  margin-bottom: 20rpx;
  overflow: hidden;
}

.card-header {
  padding: 30rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.card-body {
  padding: 30rpx;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 50rpx;
  padding: 24rpx 48rpx;
  font-size: 32rpx;
  border: none;
}

.btn-secondary {
  background: #f8f9fa;
  color: #6c757d;
  border: 2rpx solid #dee2e6;
  border-radius: 50rpx;
  padding: 24rpx 48rpx;
  font-size: 32rpx;
}

.text-primary {
  color: #1658FF !important;
}

.text-secondary {
  color: #6c757d !important;
}

.text-success {
  color: #28a745 !important;
}

.text-danger {
  color: #dc3545 !important;
}

.text-warning {
  color: #ffc107 !important;
}

.mb-20 {
  margin-bottom: 20rpx;
}

.mt-20 {
  margin-top: 20rpx;
}

.p-20 {
  padding: 20rpx;
}

.text-center {
  text-align: center;
}

.text-left {
  text-align: left;
}

.text-right {
  text-align: right;
}

/* 医疗相关样式 */
.medical-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.medical-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
  margin-top: 30rpx;
}

.feature-item {
  background: #fff;
  border-radius: 12rpx;
  padding: 30rpx 20rpx;
  text-align: center;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

.feature-item:active {
  transform: scale(0.98);
}

.feature-icon {
  width: 60rpx;
  height: 60rpx;
  margin: 0 auto 15rpx;
}

.feature-title {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.chat-bubble {
  max-width: 80%;
  padding: 20rpx 30rpx;
  border-radius: 20rpx;
  margin-bottom: 20rpx;
  word-wrap: break-word;
}

.chat-bubble.user {
  background: #1658FF;
  color: #fff;
  margin-left: auto;
  margin-right: 20rpx;
}

.chat-bubble.ai {
  background: #f1f3f4;
  color: #333;
  margin-left: 20rpx;
  margin-right: auto;
}

.loading-dots {
  display: inline-block;
}

.loading-dots::after {
  content: '';
  animation: loading 1.5s infinite;
}

@keyframes loading {
  0% { content: ''; }
  33% { content: '.'; }
  66% { content: '..'; }
  100% { content: '...'; }
}
</style>
