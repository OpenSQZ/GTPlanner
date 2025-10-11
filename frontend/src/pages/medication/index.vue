<template>
  <view class="medication-container">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">💊 药物咨询</text>
      <text class="page-desc">基于药品说明书的专业用药指导</text>
    </view>

    <!-- 搜索区域 -->
    <view class="search-section">
      <view class="search-box">
        <input 
          class="search-input"
          v-model="searchQuery"
          placeholder="请输入药品名称或用药问题..."
          @confirm="searchMedication"
          @input="onSearchInput"
        />
        <button 
          class="search-btn" 
          :disabled="!canSearch || isPaying"
          :class="{ active: canSearch && !isPaying, paid: paymentVerified }"
          @click="searchMedication"
        >
          <text v-if="isPaying">支付中...</text>
          <text v-else-if="paymentVerified">🔍</text>
          <text v-else>💰</text>
        </button>
      </view>
    </view>

    <!-- 常见问题 -->
    <view class="questions-section" v-if="!searchResult && commonQuestions.length > 0">
      <text class="section-title">❓ 常见咨询</text>
      <view class="questions-list">
        <view 
          class="question-item" 
          v-for="question in commonQuestions" 
          :key="question.id"
          @click="selectQuestion(question.text)"
        >
          <text class="question-icon">{{ question.icon }}</text>
          <text class="question-text">{{ question.text }}</text>
          <text class="question-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 搜索结果 -->
    <view class="result-section" v-if="searchResult">
      <view class="result-header">
        <text class="result-title">📋 咨询结果</text>
        <view class="result-actions">
          <button class="save-btn" @click="saveResult">保存</button>
          <button class="share-btn" @click="shareResult">分享</button>
          <button class="clear-btn" @click="clearResult">清除</button>
        </view>
      </view>
      
      <view class="result-content">
        <view class="result-card">
          <view class="query-info">
            <text class="query-label">咨询问题：</text>
            <text class="query-text">{{ lastQuery }}</text>
          </view>
          <view class="answer-content">
            <text class="answer-text">{{ searchResult }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 用药提醒 -->
    <view class="reminder-section" v-if="!searchResult">
      <text class="section-title">⏰ 用药提醒</text>
      <view class="reminder-card">
        <text class="reminder-title">设置用药提醒</text>
        <text class="reminder-desc">帮助您按时按量服药</text>
        <button class="reminder-btn" @click="setReminder">立即设置</button>
      </view>
    </view>

    <!-- 搜索历史 -->
    <view class="history-section" v-if="searchHistory.length > 0 && !searchResult">
      <view class="section-header">
        <text class="section-title">🕐 搜索历史</text>
        <text class="clear-history" @click="clearHistory">清空</text>
      </view>
      
      <view class="history-list">
        <view 
          class="history-item" 
          v-for="item in searchHistory.slice(0, 5)" 
          :key="item.id"
          @click="searchFromHistory(item.query)"
        >
          <text class="history-icon">💊</text>
          <text class="history-text">{{ item.query }}</text>
          <text class="history-time">{{ formatTime(item.createdAt) }}</text>
        </view>
      </view>
    </view>

    <!-- 用药安全提示 -->
    <view class="safety-section" v-if="!searchResult">
      <text class="section-title">⚠️ 用药安全</text>
      <view class="safety-content">
        <view class="safety-item" v-for="(tip, index) in safetyTips" :key="index">
          <text class="safety-number">{{ index + 1 }}</text>
          <text class="safety-text">{{ tip }}</text>
        </view>
      </view>
    </view>

    <!-- 加载状态 -->
    <view class="loading-overlay" v-if="isSearching">
      <view class="loading-content">
        <view class="loading-spinner"></view>
        <text class="loading-text">正在查询药品信息...</text>
        <text class="loading-desc">请稍候</text>
      </view>
    </view>
  </view>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useHistoryStore, useUserStore } from '@/store'
import { medicationApi, paymentApi, handleApiError } from '@/api'

export default {
  name: 'MedicationPage',
  setup() {
    const historyStore = useHistoryStore()
    const userStore = useUserStore()

    // 响应式数据
    const searchQuery = ref('')
    const searchResult = ref('')
    const lastQuery = ref('')
    const isSearching = ref(false)
    const searchHistory = ref([])
    const isPaying = ref(false)
    const paymentVerified = ref(false)
    const userOpenid = ref('') // 用户openid，实际项目中从用户信息获取

    // 常见问题
    const commonQuestions = ref([
      { id: 1, icon: '💊', text: '阿莫西林的用法用量是什么？' },
      { id: 2, icon: '⚠️', text: '感冒药和抗生素能一起吃吗？' },
      { id: 3, icon: '🤰', text: '孕妇可以服用哪些感冒药？' },
      { id: 4, icon: '👶', text: '儿童用药剂量如何计算？' },
      { id: 5, icon: '🍷', text: '服药期间可以饮酒吗？' },
      { id: 6, icon: '🥛', text: '药物应该用什么水服用？' }
    ])

    // 用药安全提示
    const safetyTips = ref([
      '严格按照医生处方或药品说明书用药',
      '不要随意增减药物剂量或停药',
      '注意药物的保存条件和有效期',
      '如出现不良反应，及时停药就医',
      '不要与他人共用处方药',
      '服药前仔细阅读说明书'
    ])

    // 计算属性
    const canSearch = computed(() => searchQuery.value.trim().length > 0 && !isSearching.value)

    // 生命周期
    onMounted(() => {
      loadSearchHistory()
    })

    // 方法
    const onSearchInput = (e) => {
      searchQuery.value = e.detail.value
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
        const paymentResponse = await paymentApi.createPayment('medication', userOpenid.value)
        
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
              // 支付成功后自动开始搜索
              searchMedication()
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

    const searchMedication = async () => {
      const query = searchQuery.value.trim()
      if (!query || isSearching.value) {
        return
      }

      try {
        isSearching.value = true
        lastQuery.value = query

        // 调用药物咨询API，传递支付验证状态
        const response = await medicationApi.query({
          question: query,
          payment_verified: paymentVerified.value
        })

        if (response.success) {
          searchResult.value = response.data.medication_result
          
          // 添加到搜索历史
          addToSearchHistory(query)
          
          // 更新统计
          userStore.incrementQueries()
          
          // 保存到历史记录
          historyStore.addMedicationRecord(query, searchResult.value)

          // 清空搜索框
          searchQuery.value = ''

          uni.showToast({
            title: '查询完成',
            icon: 'success'
          })
        } else {
          // 检查是否需要支付
          if (response.code === 'PAYMENT_REQUIRED') {
            uni.showModal({
              title: '付费服务',
              content: '药物咨询服务需要支付9.9元，是否立即支付？',
              success: (res) => {
                if (res.confirm) {
                  handlePayment()
                }
              }
            })
          } else {
            throw new Error(response.message || '查询失败')
          }
        }

      } catch (error) {
        console.error('药物咨询失败:', error)
        handleApiError(error)
        searchResult.value = ''
      } finally {
        isSearching.value = false
      }
    }

    const selectQuestion = (question) => {
      searchQuery.value = question
      searchMedication()
    }

    const searchFromHistory = (query) => {
      searchQuery.value = query
      searchMedication()
    }

    const addToSearchHistory = (query) => {
      const newItem = {
        id: Date.now(),
        query,
        createdAt: new Date()
      }
      
      // 避免重复
      searchHistory.value = searchHistory.value.filter(item => item.query !== query)
      searchHistory.value.unshift(newItem)
      
      // 限制历史记录数量
      if (searchHistory.value.length > 20) {
        searchHistory.value = searchHistory.value.slice(0, 20)
      }
      
      saveSearchHistory()
    }

    const clearHistory = () => {
      uni.showModal({
        title: '确认清空',
        content: '是否清空搜索历史？',
        success: (res) => {
          if (res.confirm) {
            searchHistory.value = []
            saveSearchHistory()
            uni.showToast({
              title: '已清空',
              icon: 'success'
            })
          }
        }
      })
    }

    const saveResult = () => {
      if (!searchResult.value) return

      uni.showActionSheet({
        itemList: ['复制文本', '添加提醒'],
        success: (res) => {
          if (res.tapIndex === 0) {
            // 复制文本
            uni.setClipboardData({
              data: `问题：${lastQuery.value}\n\n回答：${searchResult.value}`,
              success: () => {
                uni.showToast({
                  title: '已复制到剪贴板',
                  icon: 'success'
                })
              }
            })
          } else if (res.tapIndex === 1) {
            // 添加提醒
            setReminder()
          }
        }
      })
    }

    const shareResult = () => {
      if (!searchResult.value) return

      const content = `药物咨询：${lastQuery.value}\n\n${searchResult.value.substring(0, 100)}...`
      
      uni.share({
        title: '药物咨询结果分享',
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

    const clearResult = () => {
      searchResult.value = ''
      lastQuery.value = ''
    }

    const setReminder = () => {
      uni.showToast({
        title: '用药提醒功能开发中',
        icon: 'none'
      })
    }

    const saveSearchHistory = () => {
      try {
        uni.setStorageSync('medication_search_history', searchHistory.value)
      } catch (error) {
        console.error('保存搜索历史失败:', error)
      }
    }

    const loadSearchHistory = () => {
      try {
        const history = uni.getStorageSync('medication_search_history')
        if (history && Array.isArray(history)) {
          searchHistory.value = history
        }
      } catch (error) {
        console.error('加载搜索历史失败:', error)
      }
    }

    const formatTime = (date) => {
      const now = new Date()
      const recordDate = new Date(date)
      const diff = now - recordDate
      const hours = Math.floor(diff / 3600000)
      const days = Math.floor(diff / 86400000)

      if (hours < 1) {
        return '刚刚'
      } else if (hours < 24) {
        return `${hours}小时前`
      } else if (days < 7) {
        return `${days}天前`
      } else {
        return recordDate.toLocaleDateString()
      }
    }

    return {
      searchQuery,
      searchResult,
      lastQuery,
      isSearching,
      searchHistory,
      isPaying,
      paymentVerified,
      userOpenid,
      commonQuestions,
      safetyTips,
      canSearch,
      onSearchInput,
      searchMedication,
      handlePayment,
      selectQuestion,
      searchFromHistory,
      clearHistory,
      saveResult,
      shareResult,
      clearResult,
      setReminder,
      formatTime
    }
  }
}
</script>

<style lang="scss" scoped>
.medication-container {
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

.search-section {
  margin-bottom: 40rpx;
}

.search-box {
  display: flex;
  background: #fff;
  border-radius: 50rpx;
  padding: 10rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
  align-items: center;
}

.search-input {
  flex: 1;
  padding: 20rpx 30rpx;
  font-size: 30rpx;
  color: #333;
  background: transparent;
  border: none;
}

.search-btn {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: #e9ecef;
  color: #999;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  transition: all 0.2s ease;

  &.active {
    background: #1658FF;
    color: #fff;
  }
  
  &.paid {
    background: #28a745;
    color: #fff;
  }

  &:disabled {
    opacity: 0.6;
  }
}

.questions-section {
  margin-bottom: 40rpx;
}

.section-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 20rpx;
}

.questions-list {
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.question-item {
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

.question-icon {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  font-size: 28rpx;
  flex-shrink: 0;
}

.question-text {
  flex: 1;
  font-size: 30rpx;
  color: #333;
  margin-right: 20rpx;
}

.question-arrow {
  font-size: 32rpx;
  color: #ccc;
  flex-shrink: 0;
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
  gap: 10rpx;
  flex-wrap: wrap;
}

.save-btn, .share-btn, .clear-btn {
  background: #f8f9fa;
  color: #666;
  border: 2rpx solid #e9ecef;
  border-radius: 30rpx;
  padding: 12rpx 24rpx;
  font-size: 24rpx;
}

.clear-btn {
  color: #dc3545;
  border-color: #dc3545;
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

.query-info {
  margin-bottom: 25rpx;
  padding: 20rpx;
  background: #f8f9fa;
  border-radius: 12rpx;
  border-left: 6rpx solid #1658FF;
}

.query-label {
  font-size: 26rpx;
  color: #666;
  margin-right: 10rpx;
}

.query-text {
  font-size: 28rpx;
  color: #1658FF;
  font-weight: 500;
}

.answer-content {
  line-height: 1.8;
}

.answer-text {
  font-size: 30rpx;
  color: #333;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.reminder-section {
  margin-bottom: 40rpx;
}

.reminder-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 20rpx;
  padding: 40rpx 30rpx;
  text-align: center;
  box-shadow: 0 4rpx 12rpx rgba(102, 126, 234, 0.3);
}

.reminder-title {
  font-size: 36rpx;
  font-weight: bold;
  display: block;
  margin-bottom: 15rpx;
}

.reminder-desc {
  font-size: 28rpx;
  opacity: 0.9;
  display: block;
  margin-bottom: 30rpx;
}

.reminder-btn {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  border: 2rpx solid rgba(255, 255, 255, 0.3);
  border-radius: 50rpx;
  padding: 20rpx 40rpx;
  font-size: 30rpx;

  &:active {
    background: rgba(255, 255, 255, 0.3);
  }
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

.clear-history {
  font-size: 28rpx;
  color: #dc3545;
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

.history-icon {
  width: 50rpx;
  height: 50rpx;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  font-size: 24rpx;
  flex-shrink: 0;
}

.history-text {
  flex: 1;
  font-size: 28rpx;
  color: #333;
  margin-right: 20rpx;
}

.history-time {
  font-size: 22rpx;
  color: #999;
  flex-shrink: 0;
}

.safety-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.safety-content {
  margin-top: 25rpx;
}

.safety-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 20rpx;
  gap: 20rpx;

  &:last-child {
    margin-bottom: 0;
  }
}

.safety-number {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: #dc3545;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: bold;
  flex-shrink: 0;
}

.safety-text {
  font-size: 28rpx;
  color: #333;
  line-height: 1.6;
  flex: 1;
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
