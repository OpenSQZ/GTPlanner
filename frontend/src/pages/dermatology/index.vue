<template>
  <view class="dermatology-container">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">📷 皮肤病咨询</text>
      <text class="page-desc">上传皮肤图片，获得专业分析</text>
    </view>

    <!-- 拍照/选择图片区域 -->
    <view class="photo-section">
      <view class="photo-card" @click="chooseImage">
        <view class="photo-preview" v-if="selectedImage">
          <image class="preview-image" :src="selectedImage.path" mode="aspectFit" />
          <view class="image-overlay">
            <text class="change-text">点击重新选择</text>
          </view>
        </view>
        
        <view class="photo-placeholder" v-else>
          <text class="photo-icon">📷</text>
          <text class="photo-title">选择皮肤照片</text>
          <text class="photo-desc">请拍摄或选择清晰的皮肤患处照片</text>
        </view>
      </view>

      <!-- 拍照指导 -->
      <view class="photo-guide" v-if="!selectedImage">
        <text class="guide-title">📋 拍照建议</text>
        <view class="guide-list">
          <text class="guide-item">• 确保光线充足，避免阴影遮挡</text>
          <text class="guide-item">• 距离患处20-30cm拍摄</text>
          <text class="guide-item">• 保持手机稳定，确保图片清晰</text>
          <text class="guide-item">• 可对比拍摄（如硬币作参照物）</text>
        </view>
      </view>
    </view>

    <!-- 症状描述区域 -->
    <view class="symptoms-section">
      <text class="section-title">📝 症状描述</text>
      <textarea 
        class="symptoms-input"
        v-model="symptomsText"
        placeholder="请详细描述症状，如：出现时间、瘙痒程度、疼痛感、变化情况等..."
        :maxlength="300"
        @input="onSymptomsInput"
      />
      <text class="char-count">{{ symptomsText.length }}/300</text>
    </view>

    <!-- 快捷症状选择 -->
    <view class="quick-symptoms" v-if="!symptomsText">
      <text class="section-title">🏷️ 常见症状</text>
      <view class="symptoms-tags">
        <button 
          class="symptom-tag" 
          v-for="symptom in commonSymptoms" 
          :key="symptom"
          @click="addSymptom(symptom)"
        >
          {{ symptom }}
        </button>
      </view>
    </view>

    <!-- 分析按钮 -->
    <view class="analyze-section" v-if="selectedImage">
      <button 
        class="analyze-btn" 
        :disabled="isAnalyzing || isPaying"
        :class="{ analyzing: isAnalyzing, paid: paymentVerified }"
        @click="analyzeImage"
      >
        <text v-if="isAnalyzing">分析中...</text>
        <text v-else-if="isPaying">支付中...</text>
        <text v-else-if="paymentVerified">开始分析</text>
        <text v-else>支付分析 (¥9.9)</text>
      </button>
    </view>

    <!-- 分析结果 -->
    <view class="result-section" v-if="analysisResult">
      <view class="result-header">
        <text class="result-title">🔍 分析结果</text>
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

    <!-- 咨询历史 -->
    <view class="history-section" v-if="consultationHistory.length > 0">
      <view class="section-header">
        <text class="section-title">📋 咨询历史</text>
        <text class="view-all" @click="viewAllHistory">查看全部</text>
      </view>
      
      <view class="history-list">
        <view 
          class="history-item" 
          v-for="item in consultationHistory.slice(0, 3)" 
          :key="item.id"
          @click="viewHistoryItem(item)"
        >
          <view class="history-image">
            <image v-if="item.imagePath" :src="item.imagePath" mode="aspectFill" />
            <text v-else>📷</text>
          </view>
          <view class="history-content">
            <text class="history-title">{{ item.title }}</text>
            <text class="history-time">{{ formatTime(item.createdAt) }}</text>
          </view>
          <view class="history-arrow">›</view>
        </view>
      </view>
    </view>

    <!-- 专业提醒 -->
    <view class="notice-section">
      <view class="notice-card">
        <view class="notice-header">
          <text class="notice-icon">⚠️</text>
          <text class="notice-title">专业提醒</text>
        </view>
        <text class="notice-content">
          此分析结果仅供参考，不能替代专业医生的面诊。如症状严重或持续不改善，请及时到医院皮肤科就诊。
        </text>
      </view>
    </view>

    <!-- 加载蒙层 -->
    <view class="loading-overlay" v-if="isAnalyzing">
      <view class="loading-content">
        <view class="loading-spinner"></view>
        <text class="loading-text">AI正在分析中...</text>
        <text class="loading-desc">这可能需要一些时间</text>
      </view>
    </view>
  </view>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useHistoryStore, useUserStore } from '@/store'
import { dermatologyApi, paymentApi, handleApiError } from '@/api'

export default {
  name: 'DermatologyPage',
  setup() {
    const historyStore = useHistoryStore()
    const userStore = useUserStore()

    // 响应式数据
    const selectedImage = ref(null)
    const symptomsText = ref('')
    const isAnalyzing = ref(false)
    const analysisResult = ref('')
    const isPaying = ref(false)
    const paymentVerified = ref(false)
    const userOpenid = ref('') // 用户openid，实际项目中从用户信息获取

    // 常见症状
    const commonSymptoms = ref([
      '瘙痒', '疼痛', '红肿', '脱屑', 
      '破溃', '渗液', '结痂', '色素沉着',
      '丘疹', '水疱', '脓疱', '斑块'
    ])

    // 计算属性
    const consultationHistory = computed(() => 
      historyStore.filteredRecords.filter(record => record.type === 'dermatology')
    )

    // 生命周期
    onMounted(() => {
      historyStore.loadFromLocal()
    })

    // 方法
    const chooseImage = () => {
      // H5环境使用原生input file
      // #ifdef H5
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = 'image/*'
      input.onchange = (event) => {
        const file = event.target.files[0]
        if (!file) return
        
        // 检查文件大小（10MB）
        if (file.size > 10 * 1024 * 1024) {
          uni.showToast({
            title: '图片大小不能超过10MB',
            icon: 'error'
          })
          return
        }

        // 检查是否为图片类型
        if (!file.type.startsWith('image/')) {
          uni.showToast({
            title: '请选择图片文件',
            icon: 'error'
          })
          return
        }

        selectedImage.value = {
          path: file, // H5环境下直接传文件对象
          size: file.size
        }

        // 清除之前的分析结果
        analysisResult.value = ''

        uni.showToast({
          title: '图片选择成功',
          icon: 'success'
        })
      }
      input.click()
      // #endif
      
      // #ifndef H5
      uni.showActionSheet({
        itemList: ['拍摄照片', '从相册选择'],
        success: (res) => {
          if (res.tapIndex === 0) {
            // 拍摄照片
            uni.chooseImage({
              count: 1,
              sourceType: ['camera'],
              sizeType: ['compressed'],
              success: handleImageSuccess,
              fail: handleImageFail
            })
          } else if (res.tapIndex === 1) {
            // 从相册选择
            uni.chooseImage({
              count: 1,
              sourceType: ['album'],
              sizeType: ['compressed'],
              success: handleImageSuccess,
              fail: handleImageFail
            })
          }
        }
      })
      // #endif
    }

    const handleImageSuccess = (res) => {
      const tempFilePath = res.tempFilePaths[0]
      const tempFile = res.tempFiles[0]

      // 检查文件大小（10MB）
      if (tempFile.size > 10 * 1024 * 1024) {
        uni.showToast({
          title: '图片大小不能超过10MB',
          icon: 'error'
        })
        return
      }

      selectedImage.value = {
        path: tempFilePath,
        size: tempFile.size
      }

      // 清除之前的分析结果
      analysisResult.value = ''

      uni.showToast({
        title: '图片选择成功',
        icon: 'success'
      })
    }

    const handleImageFail = (error) => {
      console.error('选择图片失败:', error)
      if (error.errMsg && !error.errMsg.includes('cancel')) {
        uni.showToast({
          title: '选择图片失败',
          icon: 'error'
        })
      }
    }

    const onSymptomsInput = (e) => {
      symptomsText.value = e.detail.value
    }

    const addSymptom = (symptom) => {
      if (symptomsText.value) {
        symptomsText.value += '、' + symptom
      } else {
        symptomsText.value = symptom
      }
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
        const paymentResponse = await paymentApi.createPayment('dermatology', userOpenid.value)
        
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
              analyzeImage()
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

    const analyzeImage = async () => {
      if (!selectedImage.value || isAnalyzing.value) {
        return
      }

      try {
        isAnalyzing.value = true

        // 调用皮肤病咨询API，传递支付验证状态
        const response = await dermatologyApi.uploadAndConsult(
          selectedImage.value.path,
          symptomsText.value,
          paymentVerified.value
        )

        if (response.success) {
          analysisResult.value = response.data.dermatology_result
          
          // 更新统计
          userStore.incrementQueries()
          
          // 保存到历史记录
          historyStore.addDermatologyRecord(
            symptomsText.value || '皮肤咨询',
            analysisResult.value,
            selectedImage.value.path
          )

          uni.showToast({
            title: '分析完成',
            icon: 'success'
          })
        } else {
          // 检查是否需要支付
          if (response.code === 'PAYMENT_REQUIRED') {
            uni.showModal({
              title: '付费服务',
              content: '皮肤病诊断服务需要支付9.9元，是否立即支付？',
              success: (res) => {
                if (res.confirm) {
                  handlePayment()
                }
              }
            })
          } else {
            throw new Error(response.message || '分析失败')
          }
        }

      } catch (error) {
        console.error('皮肤病分析失败:', error)
        handleApiError(error)
        analysisResult.value = ''
      } finally {
        isAnalyzing.value = false
      }
    }

    const saveResult = () => {
      if (!analysisResult.value) return

      uni.showActionSheet({
        itemList: ['保存图片', '复制分析结果'],
        success: (res) => {
          if (res.tapIndex === 0) {
            if (selectedImage.value) {
              uni.saveImageToPhotosAlbum({
                filePath: selectedImage.value.path,
                success: () => {
                  uni.showToast({
                    title: '图片已保存到相册',
                    icon: 'success'
                  })
                },
                fail: () => {
                  uni.showToast({
                    title: '保存失败',
                    icon: 'error'
                  })
                }
              })
            }
          } else if (res.tapIndex === 1) {
            const content = `症状描述：${symptomsText.value || '无'}\n\n分析结果：${analysisResult.value}`
            uni.setClipboardData({
              data: content,
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

      const content = `皮肤病AI分析结果：${analysisResult.value.substring(0, 100)}...`
      
      uni.share({
        title: '皮肤病咨询结果',
        summary: content,
        success: () => {
          uni.showToast({
            title: '分享成功',
            icon: 'success'
          })
        },
        fail: () => {
          uni.setClipboardData({
            data: content,
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
      selectedImage,
      symptomsText,
      isAnalyzing,
      analysisResult,
      isPaying,
      paymentVerified,
      userOpenid,
      commonSymptoms,
      consultationHistory,
      chooseImage,
      onSymptomsInput,
      addSymptom,
      analyzeImage,
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
.dermatology-container {
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

.photo-section {
  margin-bottom: 40rpx;
}

.photo-card {
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
  border: 2rpx dashed #e9ecef;
  transition: all 0.3s ease;

  &:active {
    border-color: #1658FF;
  }
}

.photo-preview {
  position: relative;
  height: 400rpx;
}

.preview-image {
  width: 100%;
  height: 100%;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.photo-preview:active .image-overlay {
  opacity: 1;
}

.change-text {
  color: #fff;
  font-size: 30rpx;
  font-weight: bold;
}

.photo-placeholder {
  padding: 80rpx 40rpx;
  text-align: center;
}

.photo-icon {
  font-size: 100rpx;
  color: #1658FF;
  display: block;
  margin-bottom: 20rpx;
}

.photo-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 15rpx;
}

.photo-desc {
  font-size: 26rpx;
  color: #999;
  display: block;
}

.photo-guide {
  margin-top: 30rpx;
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
}

.guide-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 20rpx;
}

.guide-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.guide-item {
  font-size: 26rpx;
  color: #666;
  line-height: 1.6;
}

.symptoms-section {
  margin-bottom: 30rpx;
}

.section-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 20rpx;
}

.symptoms-input {
  width: 100%;
  min-height: 200rpx;
  background: #fff;
  border: 2rpx solid #e9ecef;
  border-radius: 16rpx;
  padding: 25rpx;
  font-size: 30rpx;
  color: #333;
  box-sizing: border-box;
  line-height: 1.6;

  &:focus {
    border-color: #1658FF;
  }
}

.char-count {
  font-size: 24rpx;
  color: #999;
  text-align: right;
  display: block;
  margin-top: 10rpx;
}

.quick-symptoms {
  margin-bottom: 30rpx;
}

.symptoms-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 15rpx;
}

.symptom-tag {
  background: #f8f9fa;
  color: #666;
  border: 2rpx solid #e9ecef;
  border-radius: 30rpx;
  padding: 15rpx 30rpx;
  font-size: 26rpx;
  min-height: auto;
  line-height: 1.2;

  &:active {
    background: #1658FF;
    color: #fff;
    border-color: #1658FF;
  }
}

.analyze-section {
  margin-bottom: 40rpx;
  text-align: center;
}

.analyze-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 50rpx;
  padding: 30rpx 80rpx;
  font-size: 36rpx;
  font-weight: bold;
  box-shadow: 0 4rpx 12rpx rgba(102, 126, 234, 0.3);
  transition: all 0.2s ease;

  &.analyzing {
    background: #ccc;
    box-shadow: none;
  }
  
  &.paid {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  }

  &:disabled {
    opacity: 0.6;
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
  flex-wrap: wrap;
  gap: 15rpx;
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
  padding: 25rpx 30rpx;
  border-bottom: 1rpx solid #f0f0f0;

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background: #f8f9fa;
  }
}

.history-image {
  width: 80rpx;
  height: 80rpx;
  border-radius: 12rpx;
  overflow: hidden;
  margin-right: 20rpx;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  image {
    width: 100%;
    height: 100%;
  }

  text {
    font-size: 32rpx;
    color: #999;
  }
}

.history-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-right: 20rpx;
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
  flex-shrink: 0;
}

.notice-section {
  margin-bottom: 40rpx;
}

.notice-card {
  background: #fff3cd;
  border: 2rpx solid #ffeeba;
  border-radius: 16rpx;
  padding: 30rpx;
}

.notice-header {
  display: flex;
  align-items: center;
  gap: 15rpx;
  margin-bottom: 15rpx;
}

.notice-icon {
  font-size: 32rpx;
}

.notice-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #856404;
}

.notice-content {
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
