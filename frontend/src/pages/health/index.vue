<template>
  <view class="health-container">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">📚 健康科普</text>
      <text class="page-desc">获取权威医学知识科普</text>
    </view>

    <!-- 搜索区域 -->
    <view class="search-section">
      <view class="search-box">
        <input 
          class="search-input"
          v-model="searchQuery"
          placeholder="请输入您想了解的健康问题..."
          @confirm="searchHealth"
          @input="onSearchInput"
        />
        <button 
          class="search-btn" 
          :disabled="!canSearch || isPaying"
          :class="{ active: canSearch && !isPaying, paid: paymentVerified }"
          @click="searchHealth"
        >
          <text v-if="isPaying">支付中...</text>
          <text v-else-if="paymentVerified">🔍</text>
          <text v-else>💰</text>
        </button>
      </view>
    </view>

    <!-- 热门话题 -->
    <view class="topics-section" v-if="!searchResult && hotTopics.length > 0">
      <text class="section-title">🔥 热门话题</text>
      <view class="topics-grid">
        <view 
          class="topic-item" 
          v-for="topic in hotTopics" 
          :key="topic.id"
          @click="selectTopic(topic.text)"
        >
          <text class="topic-icon">{{ topic.icon }}</text>
          <text class="topic-text">{{ topic.text }}</text>
        </view>
      </view>
    </view>

    <!-- 搜索结果 -->
    <view class="result-section" v-if="searchResult">
      <view class="result-header">
        <text class="result-title">📖 科普结果</text>
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
          <text class="history-icon">🔍</text>
          <text class="history-text">{{ item.query }}</text>
          <text class="history-time">{{ formatTime(item.createdAt) }}</text>
        </view>
      </view>
    </view>

    <!-- 健康建议 -->
    <view class="suggestions-section" v-if="!searchResult">
      <text class="section-title">💡 健康建议</text>
      <view class="suggestions-content">
        <view class="suggestion-item" v-for="(suggestion, index) in healthSuggestions" :key="index">
          <text class="suggestion-title">{{ suggestion.title }}</text>
          <text class="suggestion-desc">{{ suggestion.desc }}</text>
        </view>
      </view>
    </view>

    <!-- 加载状态 -->
    <view class="loading-overlay" v-if="isSearching">
      <view class="loading-content">
        <view class="loading-spinner"></view>
        <text class="loading-text">正在搜索权威资料...</text>
        <text class="loading-desc">请稍候</text>
      </view>
    </view>
  </view>
</template>

<script>
import { ref, computed, onMounted, reactive } from 'vue'
import { useHistoryStore, useUserStore } from '@/store'
import { healthEducationApi, paymentApi, handleApiError } from '@/api'

export default {
  name: 'HealthPage',
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

    // 热门话题
    const hotTopics = ref([
      { id: 1, icon: '🫀', text: '高血压预防' },
      { id: 2, icon: '🍎', text: '健康饮食' },
      { id: 3, icon: '🏃', text: '运动健身' },
      { id: 4, icon: '😴', text: '睡眠质量' },
      { id: 5, icon: '🧠', text: '心理健康' },
      { id: 6, icon: '🦷', text: '口腔健康' }
    ])

    // 健康建议
    const healthSuggestions = ref([
      {
        title: '定期体检',
        desc: '建议每年进行一次全面体检，及早发现健康问题'
      },
      {
        title: '均衡饮食',
        desc: '多吃蔬菜水果，少吃高盐高糖高脂肪食物'
      },
      {
        title: '适量运动',
        desc: '每周至少150分钟中等强度的有氧运动'
      },
      {
        title: '充足睡眠',
        desc: '成年人每天需要7-9小时的优质睡眠'
      }
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
        const paymentResponse = await paymentApi.createPayment('education', userOpenid.value)
        
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
              searchHealth()
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

    const searchHealth = async () => {
      const query = searchQuery.value.trim()
      if (!query || isSearching.value) {
        return
      }

      try {
        isSearching.value = true
        lastQuery.value = query

        // 调用健康科普API，传递支付验证状态
        const response = await healthEducationApi.query({
          question: query,
          payment_verified: paymentVerified.value
        })

        if (response.success) {
          searchResult.value = response.data.education_result
          
          // 添加到搜索历史
          addToSearchHistory(query)
          
          // 更新统计
          userStore.incrementQueries()
          
          // 保存到历史记录
          historyStore.addHealthRecord(query, searchResult.value)

          // 清空搜索框
          searchQuery.value = ''

          uni.showToast({
            title: '搜索完成',
            icon: 'success'
          })
        } else {
          // 检查是否需要支付
          if (response.code === 'PAYMENT_REQUIRED') {
            uni.showModal({
              title: '付费服务',
              content: '健康科普服务需要支付9.9元，是否立即支付？',
              success: (res) => {
                if (res.confirm) {
                  handlePayment()
                }
              }
            })
          } else {
            throw new Error(response.message || '搜索失败')
          }
        }

      } catch (error) {
        console.error('健康科普搜索失败:', error)
        handleApiError(error)
        searchResult.value = ''
      } finally {
        isSearching.value = false
      }
    }

    const selectTopic = (topic) => {
      searchQuery.value = topic
      searchHealth()
    }

    const searchFromHistory = (query) => {
      searchQuery.value = query
      searchHealth()
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
        itemList: ['复制文本', '保存到相册'],
        success: (res) => {
          if (res.tapIndex === 0) {
            // 复制文本
            uni.setClipboardData({
              data: `问题：${lastQuery.value}\n\n答案：${searchResult.value}`,
              success: () => {
                uni.showToast({
                  title: '已复制到剪贴板',
                  icon: 'success'
                })
              }
            })
          } else if (res.tapIndex === 1) {
            uni.showToast({
              title: '保存功能开发中',
              icon: 'none'
            })
          }
        }
      })
    }

    const shareResult = () => {
      if (!searchResult.value) return

      uni.share({
        title: '健康科普分享',
        summary: `${lastQuery.value}: ${searchResult.value.substring(0, 100)}...`,
        success: () => {
          uni.showToast({
            title: '分享成功',
            icon: 'success'
          })
        },
        fail: () => {
          uni.setClipboardData({
            data: `问题：${lastQuery.value}\n\n答案：${searchResult.value}`,
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

    const saveSearchHistory = () => {
      try {
        uni.setStorageSync('health_search_history', searchHistory.value)
      } catch (error) {
        console.error('保存搜索历史失败:', error)
      }
    }

    const loadSearchHistory = () => {
      try {
        const history = uni.getStorageSync('health_search_history')
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
      hotTopics,
      healthSuggestions,
      canSearch,
      onSearchInput,
      searchHealth,
      handlePayment,
      selectTopic,
      searchFromHistory,
      clearHistory,
      saveResult,
      shareResult,
      clearResult,
      formatTime
    }
  }
}
</script>

<style lang="scss" scoped>
.health-container {
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

.topics-section {
  margin-bottom: 40rpx;
}

.section-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 20rpx;
}

.topics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15rpx;
}

.topic-item {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx 20rpx;
  text-align: center;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;

  &:active {
    transform: scale(0.98);
    background: #f8f9fa;
  }
}

.topic-icon {
  font-size: 40rpx;
  display: block;
  margin-bottom: 10rpx;
}

.topic-text {
  font-size: 26rpx;
  color: #333;
  font-weight: 500;
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

.suggestions-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.suggestions-content {
  margin-top: 25rpx;
}

.suggestion-item {
  margin-bottom: 30rpx;
  padding: 25rpx;
  background: #f8f9fa;
  border-radius: 12rpx;
  border-left: 6rpx solid #28a745;

  &:last-child {
    margin-bottom: 0;
  }
}

.suggestion-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 10rpx;
}

.suggestion-desc {
  font-size: 26rpx;
  color: #666;
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
