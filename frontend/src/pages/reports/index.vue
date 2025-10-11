<template>
  <view class="reports-container">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">📋 报告解读</text>
      <text class="page-desc">上传医学报告，获得专业解读</text>
    </view>

    <!-- 上传区域 -->
    <view class="upload-section">
      <view class="upload-card" @click="chooseFile">
        <view class="upload-icon">
          <text v-if="!uploadedFile">📄</text>
          <text v-else>✅</text>
        </view>
        <text class="upload-title" v-if="!uploadedFile">选择报告文件</text>
        <text class="upload-title" v-else>{{ uploadedFile.name }}</text>
        <text class="upload-desc">支持 Word、PDF 格式，大小不超过10MB</text>
        
        <button class="upload-btn" v-if="!uploadedFile">
          选择文件
        </button>
        <view class="upload-actions" v-else>
          <button class="change-btn" @click.stop="chooseFile">重新选择</button>
          <button 
            class="analyze-btn" 
            @click.stop="analyzeReport" 
            :disabled="isAnalyzing || isPaying"
            :class="{ 'paid': paymentVerified }"
          >
            <text v-if="isAnalyzing">分析中...</text>
            <text v-else-if="isPaying">支付中...</text>
            <text v-else-if="paymentVerified">开始解读</text>
            <text v-else>支付解读 (¥9.9)</text>
          </button>
        </view>
      </view>
    </view>

    <!-- 分析结果 -->
    <view class="result-section" v-if="analysisResult">
      <view class="result-header">
        <text class="result-title">📊 解读结果</text>
        <view class="result-actions">
          <button class="save-btn" @click="saveResult">保存</button>
          <button class="share-btn" @click="shareResult">分享</button>
        </view>
      </view>
      
      <view class="result-content">
        <view class="result-card">
          <text class="result-text">{{ analysisResult }}</text>
        </view>
      </view>
    </view>

    <!-- 历史记录 -->
    <view class="history-section" v-if="reportHistory.length > 0">
      <view class="section-header">
        <text class="section-title">📚 最近解读</text>
        <text class="view-all" @click="viewAllHistory">查看全部</text>
      </view>
      
      <view class="history-list">
        <view 
          class="history-item" 
          v-for="item in reportHistory.slice(0, 3)" 
          :key="item.id"
          @click="viewHistoryItem(item)"
        >
          <view class="history-icon">📋</view>
          <view class="history-content">
            <text class="history-title">{{ item.title }}</text>
            <text class="history-time">{{ formatTime(item.createdAt) }}</text>
          </view>
          <view class="history-arrow">›</view>
        </view>
      </view>
    </view>

    <!-- 使用说明 -->
    <view class="instructions-section">
      <text class="section-title">💡 使用说明</text>
      <view class="instructions-content">
        <view class="instruction-item">
          <text class="instruction-number">1</text>
          <text class="instruction-text">选择您要解读的医学报告文件</text>
        </view>
        <view class="instruction-item">
          <text class="instruction-number">2</text>
          <text class="instruction-text">等待AI分析报告内容</text>
        </view>
        <view class="instruction-item">
          <text class="instruction-number">3</text>
          <text class="instruction-text">查看专业的解读结果和建议</text>
        </view>
      </view>
      
      <view class="notice">
        <text class="notice-title">⚠️ 重要提醒</text>
        <text class="notice-text">本解读结果仅供参考，不能替代专业医生诊断，如有疑问请及时就医。</text>
      </view>
    </view>

    <!-- 加载蒙层 -->
    <view class="loading-overlay" v-if="isAnalyzing">
      <view class="loading-content">
        <view class="loading-spinner"></view>
        <text class="loading-text">正在分析报告...</text>
        <text class="loading-desc">请稍候，这可能需要一些时间</text>
      </view>
    </view>
  </view>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useHistoryStore, useUserStore } from '@/store'
import { reportApi, paymentApi, handleApiError } from '@/api'

export default {
  name: 'ReportsPage',
  setup() {
    const historyStore = useHistoryStore()
    const userStore = useUserStore()

    // 响应式数据
    const uploadedFile = ref(null)
    const isAnalyzing = ref(false)
    const analysisResult = ref('')
    const isPaying = ref(false)
    const paymentVerified = ref(false)
    const userOpenid = ref('') // 用户openid，实际项目中从用户信息获取

    // 计算属性
    const reportHistory = computed(() => 
      historyStore.filteredRecords.filter(record => record.type === 'report')
    )

    // 生命周期
    onMounted(() => {
      historyStore.loadFromLocal()
    })

    // 方法
    const chooseFile = () => {
      // H5环境使用原生input file
      // #ifdef H5
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.pdf,.doc,.docx,.txt'
      input.onchange = (event) => {
        const file = event.target.files[0]
        if (!file) return
        
        // 检查文件大小（10MB）
        if (file.size > 10 * 1024 * 1024) {
          uni.showToast({
            title: '文件大小不能超过10MB',
            icon: 'error'
          })
          return
        }

        // 检查文件类型
        const allowedTypes = ['.pdf', '.doc', '.docx', '.txt']
        const fileExt = '.' + file.name.split('.').pop().toLowerCase()
        if (!allowedTypes.includes(fileExt)) {
          uni.showToast({
            title: '仅支持PDF、Word、TXT格式',
            icon: 'error'
          })
          return
        }

        uploadedFile.value = {
          name: file.name,
          path: file, // H5环境下直接传文件对象
          size: file.size
        }

        uni.showToast({
          title: '文件选择成功',
          icon: 'success'
        })
      }
      input.click()
      // #endif
      
      // 微信小程序环境
      // #ifdef MP-WEIXIN
      wx.chooseMessageFile({
        count: 1,
        type: 'file',
        extension: ['pdf', 'doc', 'docx', 'txt'],
        success: (res) => {
          const file = res.tempFiles[0]
          
          // 检查文件大小（10MB）
          if (file.size > 10 * 1024 * 1024) {
            uni.showToast({
              title: '文件大小不能超过10MB',
              icon: 'error'
            })
            return
          }

          // 检查文件类型
          const allowedTypes = ['pdf', 'doc', 'docx', 'txt']
          const fileExt = file.name.split('.').pop().toLowerCase()
          if (!allowedTypes.includes(fileExt)) {
            uni.showToast({
              title: '仅支持PDF、Word、TXT格式',
              icon: 'error'
            })
            return
          }

          uploadedFile.value = {
            name: file.name,
            path: file.path,
            size: file.size
          }

          uni.showToast({
            title: '文件选择成功',
            icon: 'success'
          })
        },
        fail: (error) => {
          console.error('选择文件失败:', error)
          uni.showToast({
            title: '选择文件失败',
            icon: 'error'
          })
        }
      })
      // #endif
      
      // 其他小程序环境（支付宝、百度等）
      // #ifndef H5 || MP-WEIXIN
      uni.chooseFile({
        count: 1,
        extension: ['.pdf', '.doc', '.docx', '.txt'],
        success: (res) => {
          const file = res.tempFiles[0]
          
          // 检查文件大小（10MB）
          if (file.size > 10 * 1024 * 1024) {
            uni.showToast({
              title: '文件大小不能超过10MB',
              icon: 'error'
            })
            return
          }

          // 检查文件类型
          const allowedTypes = ['.pdf', '.doc', '.docx', '.txt']
          const fileExt = '.' + file.name.split('.').pop().toLowerCase()
          if (!allowedTypes.includes(fileExt)) {
            uni.showToast({
              title: '仅支持PDF、Word、TXT格式',
              icon: 'error'
            })
            return
          }

          uploadedFile.value = {
            name: file.name,
            path: file.path,
            size: file.size
          }

          uni.showToast({
            title: '文件选择成功',
            icon: 'success'
          })
        },
        fail: (error) => {
          console.error('选择文件失败:', error)
          uni.showToast({
            title: '选择文件失败',
            icon: 'error'
          })
        }
      })
      // #endif
    }

    // 支付相关方法
    const handlePayment = async () => {
      if (!userOpenid.value) {
        uni.showToast({
          title: '请先获取用户信息',
          icon: 'error'
        })
        return
      }

      try {
        isPaying.value = true
        
        // 创建支付订单
        const paymentResponse = await paymentApi.createPayment('report', userOpenid.value)
        
        if (paymentResponse.success) {
          // 发起微信支付
          const payResult = await paymentApi.requestPayment(paymentResponse.data.pay_params)
          
          if (payResult.errMsg === 'requestPayment:ok') {
            // 支付成功，验证支付状态
            const queryResult = await paymentApi.queryPayment(paymentResponse.data.out_trade_no)
            
            if (queryResult.success && queryResult.data.trade_state === 'SUCCESS') {
              paymentVerified.value = true
              uni.showToast({
                title: '支付成功',
                icon: 'success'
              })
              // 支付成功后自动开始分析
              analyzeReport()
            } else {
              uni.showToast({
                title: '支付验证失败',
                icon: 'error'
              })
            }
          } else {
            uni.showToast({
              title: '支付取消',
              icon: 'none'
            })
          }
        } else {
          uni.showToast({
            title: paymentResponse.message || '创建支付订单失败',
            icon: 'error'
          })
        }
      } catch (error) {
        console.error('支付失败:', error)
        uni.showToast({
          title: '支付失败',
          icon: 'error'
        })
      } finally {
        isPaying.value = false
      }
    }

    const analyzeReport = async () => {
      if (!uploadedFile.value || isAnalyzing.value) {
        return
      }

      try {
        isAnalyzing.value = true
        
        // 调用报告解读API，传递支付验证状态
        const response = await reportApi.uploadAndInterpret(
          uploadedFile.value.path,
          uploadedFile.value.name,
          paymentVerified.value
        )

        if (response.success) {
          analysisResult.value = response.data.interpretation_result
          
          // 更新统计
          userStore.incrementReports()
          
          // 保存到历史记录
          historyStore.addReportRecord(
            uploadedFile.value.name,
            analysisResult.value
          )

          uni.showToast({
            title: '解读完成',
            icon: 'success'
          })
        } else {
          // 检查是否需要支付
          if (response.code === 'PAYMENT_REQUIRED') {
            uni.showModal({
              title: '付费服务',
              content: '报告解读服务需要支付9.9元，是否立即支付？',
              success: (res) => {
                if (res.confirm) {
                  handlePayment()
                }
              }
            })
          } else {
            throw new Error(response.message || '解读失败')
          }
        }

      } catch (error) {
        console.error('报告解读失败:', error)
        handleApiError(error)
        analysisResult.value = ''
      } finally {
        isAnalyzing.value = false
      }
    }

    const saveResult = () => {
      if (!analysisResult.value) return

      // 保存到本地相册或文件
      uni.showActionSheet({
        itemList: ['保存到相册', '复制文本'],
        success: (res) => {
          if (res.tapIndex === 0) {
            // 保存到相册的逻辑
            uni.showToast({
              title: '保存功能开发中',
              icon: 'none'
            })
          } else if (res.tapIndex === 1) {
            // 复制文本
            uni.setClipboardData({
              data: analysisResult.value,
              success: () => {
                uni.showToast({
                  title: '已复制到剪贴板',
                  icon: 'success'
                })
              }
            })
          }
        }
      })
    }

    const shareResult = () => {
      if (!analysisResult.value) return

      uni.share({
        title: '医疗报告解读结果',
        summary: analysisResult.value.substring(0, 100) + '...',
        success: () => {
          uni.showToast({
            title: '分享成功',
            icon: 'success'
          })
        },
        fail: () => {
          // 如果分享失败，提供复制链接选项
          uni.setClipboardData({
            data: analysisResult.value,
            success: () => {
              uni.showToast({
                title: '已复制内容到剪贴板',
                icon: 'success'
              })
            }
          })
        }
      })
    }

    const viewAllHistory = () => {
      uni.switchTab({
        url: '/pages/history/index'
      })
    }

    const viewHistoryItem = (item) => {
      // 显示历史记录详情
      uni.showModal({
        title: item.title,
        content: item.content.substring(0, 200) + '...',
        showCancel: false,
        confirmText: '知道了'
      })
    }

    const formatTime = (date) => {
      const now = new Date()
      const recordDate = new Date(date)
      const diff = now - recordDate
      const hours = Math.floor(diff / 3600000)
      const days = Math.floor(diff / 86400000)

      if (hours < 24) {
        return `${hours}小时前`
      } else if (days < 7) {
        return `${days}天前`
      } else {
        return recordDate.toLocaleDateString()
      }
    }

    return {
      uploadedFile,
      isAnalyzing,
      analysisResult,
      isPaying,
      paymentVerified,
      userOpenid,
      reportHistory,
      chooseFile,
      analyzeReport,
      handlePayment,
      saveResult,
      shareResult,
      viewAllHistory,
      viewHistoryItem,
      formatTime
    }
  }
}
</script>

<style lang="scss" scoped>
.reports-container {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 20rpx;
}

.page-header {
  text-align: center;
  margin-bottom: 40rpx;
}

.page-title {
  font-size: 48rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 15rpx;
}

.page-desc {
  font-size: 28rpx;
  color: #666;
  display: block;
}

.upload-section {
  margin-bottom: 40rpx;
}

.upload-card {
  background: #fff;
  border-radius: 20rpx;
  padding: 60rpx 40rpx;
  text-align: center;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
  border: 2rpx dashed #e9ecef;
  transition: all 0.3s ease;

  &:active {
    border-color: #1658FF;
    background: #f8f9ff;
  }
}

.upload-icon {
  font-size: 80rpx;
  margin-bottom: 20rpx;
  color: #1658FF;
}

.upload-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 15rpx;
}

.upload-desc {
  font-size: 26rpx;
  color: #999;
  display: block;
  margin-bottom: 30rpx;
}

.upload-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 50rpx;
  padding: 24rpx 48rpx;
  font-size: 32rpx;
}

.upload-actions {
  display: flex;
  gap: 20rpx;
  justify-content: center;
}

.change-btn {
  background: #f8f9fa;
  color: #666;
  border: 2rpx solid #e9ecef;
  border-radius: 50rpx;
  padding: 20rpx 40rpx;
  font-size: 28rpx;
}

.analyze-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 50rpx;
  padding: 20rpx 40rpx;
  font-size: 28rpx;
  transition: all 0.2s ease;

  &:disabled {
    opacity: 0.6;
  }
  
  &.paid {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  }
  
  &:active:not(:disabled) {
    transform: scale(0.98);
  }
}

.result-section {
  margin-bottom: 40rpx;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.result-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.result-actions {
  display: flex;
  gap: 15rpx;
}

.save-btn, .share-btn {
  background: #f8f9fa;
  color: #666;
  border: 2rpx solid #e9ecef;
  border-radius: 30rpx;
  padding: 15rpx 30rpx;
  font-size: 26rpx;
}

.result-content {
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.result-card {
  padding: 30rpx;
}

.result-text {
  font-size: 30rpx;
  color: #333;
  line-height: 1.8;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.history-section {
  margin-bottom: 40rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.view-all {
  font-size: 28rpx;
  color: #1658FF;
}

.history-list {
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.history-item {
  display: flex;
  align-items: center;
  padding: 30rpx;
  border-bottom: 1rpx solid #f0f0f0;

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background: #f8f9fa;
  }
}

.history-icon {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  font-size: 28rpx;
}

.history-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.history-title {
  font-size: 30rpx;
  color: #333;
  font-weight: 500;
}

.history-time {
  font-size: 24rpx;
  color: #999;
}

.history-arrow {
  font-size: 32rpx;
  color: #ccc;
}

.instructions-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.instructions-content {
  margin: 30rpx 0;
}

.instruction-item {
  display: flex;
  align-items: center;
  margin-bottom: 25rpx;
  gap: 20rpx;
}

.instruction-number {
  width: 50rpx;
  height: 50rpx;
  border-radius: 50%;
  background: #1658FF;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: bold;
  flex-shrink: 0;
}

.instruction-text {
  font-size: 30rpx;
  color: #333;
  flex: 1;
}

.notice {
  background: #fff3cd;
  border: 2rpx solid #ffeeba;
  border-radius: 12rpx;
  padding: 25rpx;
  margin-top: 30rpx;
}

.notice-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #856404;
  display: block;
  margin-bottom: 10rpx;
}

.notice-text {
  font-size: 28rpx;
  color: #856404;
  line-height: 1.6;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  background: #fff;
  border-radius: 20rpx;
  padding: 60rpx 40rpx;
  text-align: center;
  margin: 0 40rpx;
  min-width: 400rpx;
}

.loading-spinner {
  width: 80rpx;
  height: 80rpx;
  border: 6rpx solid #f3f3f3;
  border-top: 6rpx solid #1658FF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 30rpx;
}

.loading-text {
  font-size: 32rpx;
  color: #333;
  font-weight: bold;
  display: block;
  margin-bottom: 15rpx;
}

.loading-desc {
  font-size: 26rpx;
  color: #666;
  display: block;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
