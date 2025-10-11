<template>
  <view class="home-container">
    <!-- 顶部欢迎区域 -->
    <view class="welcome-section">
      <view class="medical-card">
        <view class="welcome-content">
          <text class="welcome-title">🏥 医疗智能体</text>
          <text class="welcome-subtitle">您的专业医疗AI助手</text>
          <text class="welcome-desc">提供智能问诊、报告解读、健康科普等服务</text>
        </view>
      </view>
    </view>

    <!-- 快速功能区域 -->
    <view class="quick-actions">
      <text class="section-title">快速服务</text>
      <view class="feature-grid">
        <view class="feature-item" @click="navigateToChat">
          <view class="feature-icon">
            <text class="iconfont icon-chat">💬</text>
          </view>
          <text class="feature-title">智能问诊</text>
          <text class="feature-desc">症状描述，AI智能分析</text>
        </view>
        
        <view class="feature-item" @click="navigateToReports">
          <view class="feature-icon">
            <text class="iconfont icon-document">📋</text>
          </view>
          <text class="feature-title">报告解读</text>
          <text class="feature-desc">医学报告专业解读</text>
        </view>
        
        <view class="feature-item" @click="navigateToHealth">
          <view class="feature-icon">
            <text class="iconfont icon-book">📚</text>
          </view>
          <text class="feature-title">健康科普</text>
          <text class="feature-desc">权威医学知识普及</text>
        </view>
        
        <view class="feature-item" @click="navigateToDermatology">
          <view class="feature-icon">
            <text class="iconfont icon-camera">📷</text>
          </view>
          <text class="feature-title">皮肤病咨询</text>
          <text class="feature-desc">图片分析皮肤问题</text>
        </view>
        
        <view class="feature-item" @click="navigateToMedication">
          <view class="feature-icon">
            <text class="iconfont icon-pill">💊</text>
          </view>
          <text class="feature-title">药物咨询</text>
          <text class="feature-desc">用药指导安全提醒</text>
        </view>
        
        <view class="feature-item" @click="navigateToHistory">
          <view class="feature-icon">
            <text class="iconfont icon-history">📖</text>
          </view>
          <text class="feature-title">历史记录</text>
          <text class="feature-desc">查看使用历史</text>
        </view>
      </view>
    </view>

    <!-- 最近使用 -->
    <view class="recent-section" v-if="recentRecords.length > 0">
      <view class="section-header">
        <text class="section-title">最近使用</text>
        <text class="more-btn" @click="navigateToHistory">查看全部</text>
      </view>
      <view class="recent-list">
        <view 
          class="recent-item" 
          v-for="record in recentRecords.slice(0, 3)" 
          :key="record.id"
          @click="openRecord(record)"
        >
          <view class="recent-icon">
            <text>{{ getRecordIcon(record.type) }}</text>
          </view>
          <view class="recent-content">
            <text class="recent-title">{{ record.title }}</text>
            <text class="recent-time">{{ formatTime(record.createdAt) }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 使用统计 -->
    <view class="stats-section">
      <text class="section-title">使用统计</text>
      <view class="stats-grid">
        <view class="stats-item">
          <text class="stats-number">{{ userStats.totalChats }}</text>
          <text class="stats-label">智能问诊</text>
        </view>
        <view class="stats-item">
          <text class="stats-number">{{ userStats.totalReports }}</text>
          <text class="stats-label">报告解读</text>
        </view>
        <view class="stats-item">
          <text class="stats-number">{{ userStats.totalQueries }}</text>
          <text class="stats-label">健康咨询</text>
        </view>
        <view class="stats-item">
          <text class="stats-number">{{ totalUsage }}</text>
          <text class="stats-label">总计使用</text>
        </view>
      </view>
    </view>

    <!-- 健康提醒 -->
    <view class="tips-section">
      <view class="tips-card">
        <view class="tips-header">
          <text class="tips-icon">💡</text>
          <text class="tips-title">健康小贴士</text>
        </view>
        <text class="tips-content">{{ currentTip }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import { useHistoryStore, useUserStore } from '@/store'
import { computed, onMounted, reactive } from 'vue'

export default {
  name: 'HomePage',
  setup() {
    const historyStore = useHistoryStore()
    const userStore = useUserStore()

    // 健康小贴士
    const healthTips = [
      '定期体检是预防疾病的重要手段，建议每年至少进行一次全面体检。',
      '保持充足的睡眠，成年人每天需要7-9小时的睡眠时间。',
      '适量运动有助于增强免疫力，建议每周至少进行150分钟中等强度运动。',
      '均衡饮食，多吃蔬菜水果，少吃高盐高糖高脂肪食物。',
      '保持良好的心理状态，学会释放压力，必要时寻求专业帮助。'
    ]

    const state = reactive({
      currentTip: healthTips[Math.floor(Math.random() * healthTips.length)]
    })

    // 计算属性
    const recentRecords = computed(() => historyStore.recentRecords)
    const userStats = computed(() => userStore.statistics)
    const totalUsage = computed(() => 
      userStats.value.totalChats + userStats.value.totalReports + userStats.value.totalQueries
    )

    // 生命周期
    onMounted(() => {
      // 加载本地数据
      historyStore.loadFromLocal()
      userStore.loadFromLocal()
      userStore.initUserData()
    })

    // 方法
    const navigateToChat = () => {
      uni.switchTab({
        url: '/pages/chat/index'
      })
    }

    const navigateToReports = () => {
      uni.navigateTo({
        url: '/pages/reports/index'
      })
    }

    const navigateToHealth = () => {
      uni.navigateTo({
        url: '/pages/health/index'
      })
    }

    const navigateToDermatology = () => {
      uni.navigateTo({
        url: '/pages/dermatology/index'
      })
    }

    const navigateToMedication = () => {
      uni.navigateTo({
        url: '/pages/medication/index'
      })
    }

    const navigateToHistory = () => {
      uni.switchTab({
        url: '/pages/history/index'
      })
    }

    const openRecord = (record) => {
      // 根据记录类型打开对应页面
      const routeMap = {
        chat: '/pages/chat/index',
        report: '/pages/reports/index',
        health: '/pages/health/index',
        dermatology: '/pages/dermatology/index',
        medication: '/pages/medication/index'
      }

      const url = routeMap[record.type]
      if (url) {
        uni.navigateTo({
          url: `${url}?recordId=${record.id}`
        })
      }
    }

    const getRecordIcon = (type) => {
      const iconMap = {
        chat: '💬',
        report: '📋',
        health: '📚',
        dermatology: '📷',
        medication: '💊'
      }
      return iconMap[type] || '📄'
    }

    const formatTime = (date) => {
      const now = new Date()
      const recordDate = new Date(date)
      const diff = now - recordDate
      const minutes = Math.floor(diff / 60000)
      const hours = Math.floor(diff / 3600000)
      const days = Math.floor(diff / 86400000)

      if (minutes < 60) {
        return `${minutes}分钟前`
      } else if (hours < 24) {
        return `${hours}小时前`
      } else if (days < 7) {
        return `${days}天前`
      } else {
        return recordDate.toLocaleDateString()
      }
    }

    return {
      state,
      recentRecords,
      userStats,
      totalUsage,
      navigateToChat,
      navigateToReports,
      navigateToHealth,
      navigateToDermatology,
      navigateToMedication,
      navigateToHistory,
      openRecord,
      getRecordIcon,
      formatTime,
      currentTip: state.currentTip
    }
  }
}
</script>

<style lang="scss" scoped>
.home-container {
  min-height: 100vh;
  background: #f8f9fa;
  padding-bottom: 20rpx;
}

.welcome-section {
  padding: 30rpx 20rpx;
  
  .medical-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    border-radius: 20rpx;
    padding: 40rpx 30rpx;
    position: relative;
    overflow: hidden;
    
    &::before {
      content: '';
      position: absolute;
      top: -50%;
      right: -20%;
      width: 200rpx;
      height: 200rpx;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 50%;
    }
  }
  
  .welcome-content {
    display: flex;
    flex-direction: column;
    gap: 10rpx;
  }
  
  .welcome-title {
    font-size: 48rpx;
    font-weight: bold;
    margin-bottom: 10rpx;
  }
  
  .welcome-subtitle {
    font-size: 32rpx;
    opacity: 0.9;
  }
  
  .welcome-desc {
    font-size: 28rpx;
    opacity: 0.8;
    margin-top: 10rpx;
  }
}

.quick-actions {
  padding: 0 20rpx;
  margin-bottom: 30rpx;
}

.section-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
  display: block;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}

.feature-item {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx 20rpx;
  text-align: center;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
  
  &:active {
    transform: scale(0.98);
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.15);
  }
}

.feature-icon {
  width: 80rpx;
  height: 80rpx;
  margin: 0 auto 15rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  font-size: 36rpx;
}

.feature-title {
  font-size: 32rpx;
  color: #333;
  font-weight: 500;
  display: block;
  margin-bottom: 8rpx;
}

.feature-desc {
  font-size: 24rpx;
  color: #666;
  display: block;
}

.recent-section {
  padding: 0 20rpx;
  margin-bottom: 30rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.more-btn {
  font-size: 28rpx;
  color: #1658FF;
}

.recent-list {
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.recent-item {
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

.recent-icon {
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

.recent-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.recent-title {
  font-size: 30rpx;
  color: #333;
  font-weight: 500;
}

.recent-time {
  font-size: 24rpx;
  color: #999;
}

.stats-section {
  padding: 0 20rpx;
  margin-bottom: 30rpx;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15rpx;
}

.stats-item {
  background: #fff;
  border-radius: 12rpx;
  padding: 25rpx 15rpx;
  text-align: center;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.stats-number {
  font-size: 36rpx;
  font-weight: bold;
  color: #1658FF;
}

.stats-label {
  font-size: 24rpx;
  color: #666;
}

.tips-section {
  padding: 0 20rpx;
}

.tips-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.tips-header {
  display: flex;
  align-items: center;
  margin-bottom: 15rpx;
  gap: 10rpx;
}

.tips-icon {
  font-size: 32rpx;
}

.tips-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.tips-content {
  font-size: 28rpx;
  color: #666;
  line-height: 1.6;
}
</style>
