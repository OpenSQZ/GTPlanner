<template>
  <view class="history-container">
    <!-- 搜索和筛选 -->
    <view class="search-filter-section">
      <view class="search-box">
        <input 
          class="search-input"
          v-model="searchKeyword"
          placeholder="搜索历史记录..."
          @input="onSearchInput"
        />
        <button class="search-btn" @click="clearSearch" v-if="searchKeyword">
          ✕
        </button>
      </view>
      
      <view class="filter-tabs">
        <button 
          class="filter-tab" 
          v-for="filter in filterOptions" 
          :key="filter.value"
          :class="{ active: filterType === filter.value }"
          @click="setFilter(filter.value)"
        >
          <text class="filter-icon">{{ filter.icon }}</text>
          <text class="filter-text">{{ filter.label }}</text>
          <text class="filter-count" v-if="filter.count > 0">({{ filter.count }})</text>
        </button>
      </view>
    </view>

    <!-- 统计信息 -->
    <view class="stats-section" v-if="!searchKeyword">
      <text class="section-title">📊 使用统计</text>
      <view class="stats-cards">
        <view class="stats-card">
          <text class="stats-number">{{ statistics.total }}</text>
          <text class="stats-label">总记录</text>
        </view>
        <view class="stats-card">
          <text class="stats-number">{{ statistics.today }}</text>
          <text class="stats-label">今日</text>
        </view>
        <view class="stats-card">
          <text class="stats-number">{{ statistics.thisWeek }}</text>
          <text class="stats-label">本周</text>
        </view>
        <view class="stats-card">
          <text class="stats-number">{{ statistics.thisMonth }}</text>
          <text class="stats-label">本月</text>
        </view>
      </view>
    </view>

    <!-- 历史记录列表 -->
    <view class="records-section">
      <view class="section-header" v-if="filteredRecords.length > 0">
        <text class="section-title">
          {{ searchKeyword ? '搜索结果' : '历史记录' }}
          ({{ filteredRecords.length }})
        </text>
        <view class="header-actions">
          <button class="action-btn" @click="exportRecords">导出</button>
          <button class="action-btn danger" @click="clearAllRecords">清空</button>
        </view>
      </view>

      <!-- 记录列表 -->
      <view class="records-list" v-if="filteredRecords.length > 0">
        <view 
          class="record-item" 
          v-for="record in filteredRecords" 
          :key="record.id"
          @click="viewRecord(record)"
          @longpress="showRecordActions(record)"
        >
          <view class="record-icon">
            <text>{{ getRecordIcon(record.type) }}</text>
          </view>
          
          <view class="record-content">
            <text class="record-title">{{ record.title }}</text>
            <text class="record-preview">{{ getRecordPreview(record.content) }}</text>
            <text class="record-time">{{ formatTime(record.createdAt) }}</text>
          </view>
          
          <view class="record-type">
            <text class="type-tag" :class="record.type">{{ getTypeLabel(record.type) }}</text>
          </view>
        </view>
      </view>

      <!-- 空状态 -->
      <view class="empty-state" v-else>
        <text class="empty-icon">📝</text>
        <text class="empty-title">
          {{ searchKeyword ? '未找到相关记录' : '暂无历史记录' }}
        </text>
        <text class="empty-desc">
          {{ searchKeyword ? '尝试使用其他关键词搜索' : '开始使用医疗智能体服务吧' }}
        </text>
        <button class="empty-btn" @click="goToHome" v-if="!searchKeyword">
          立即体验
        </button>
      </view>
    </view>

    <!-- 记录详情弹窗 -->
    <view class="record-modal" v-if="selectedRecord" @click="closeModal">
      <view class="modal-content" @click.stop>
        <view class="modal-header">
          <text class="modal-title">{{ selectedRecord.title }}</text>
          <button class="modal-close" @click="closeModal">✕</button>
        </view>
        
        <view class="modal-body">
          <view class="record-info">
            <text class="info-label">类型：</text>
            <text class="info-value">{{ getTypeLabel(selectedRecord.type) }}</text>
          </view>
          <view class="record-info">
            <text class="info-label">时间：</text>
            <text class="info-value">{{ formatDetailTime(selectedRecord.createdAt) }}</text>
          </view>
          
          <view class="record-detail">
            <text class="detail-content">{{ selectedRecord.content }}</text>
          </view>
        </view>
        
        <view class="modal-actions">
          <button class="modal-btn" @click="copyRecord">复制</button>
          <button class="modal-btn" @click="shareRecord">分享</button>
          <button class="modal-btn danger" @click="deleteRecord">删除</button>
        </view>
      </view>
    </view>

    <!-- 操作菜单 -->
    <view class="action-menu" v-if="showActionMenu" @click="hideActionMenu">
      <view class="menu-content" @click.stop>
        <button class="menu-item" @click="copySelectedRecord">
          <text class="menu-icon">📋</text>
          <text class="menu-text">复制</text>
        </button>
        <button class="menu-item" @click="shareSelectedRecord">
          <text class="menu-icon">📤</text>
          <text class="menu-text">分享</text>
        </button>
        <button class="menu-item danger" @click="deleteSelectedRecord">
          <text class="menu-icon">🗑️</text>
          <text class="menu-text">删除</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useHistoryStore, useUserStore } from '@/store'

export default {
  name: 'HistoryPage',
  setup() {
    const historyStore = useHistoryStore()
    const userStore = useUserStore()

    // 响应式数据
    const searchKeyword = ref('')
    const filterType = ref('all')
    const selectedRecord = ref(null)
    const showActionMenu = ref(false)
    const actionRecord = ref(null)

    // 筛选选项
    const filterOptions = computed(() => [
      { value: 'all', label: '全部', icon: '📄', count: historyStore.recordCountByType.all },
      { value: 'chat', label: '问诊', icon: '💬', count: historyStore.recordCountByType.chat },
      { value: 'report', label: '报告', icon: '📋', count: historyStore.recordCountByType.report },
      { value: 'health', label: '科普', icon: '📚', count: historyStore.recordCountByType.health },
      { value: 'dermatology', label: '皮肤', icon: '📷', count: historyStore.recordCountByType.dermatology },
      { value: 'medication', label: '用药', icon: '💊', count: historyStore.recordCountByType.medication }
    ])

    // 计算属性
    const filteredRecords = computed(() => historyStore.filteredRecords)
    const statistics = computed(() => historyStore.getStatistics())

    // 生命周期
    onMounted(() => {
      historyStore.loadFromLocal()
      userStore.loadFromLocal()
    })

    // 方法
    const onSearchInput = (e) => {
      searchKeyword.value = e.detail.value
      historyStore.setSearchKeyword(searchKeyword.value)
    }

    const clearSearch = () => {
      searchKeyword.value = ''
      historyStore.setSearchKeyword('')
    }

    const setFilter = (type) => {
      filterType.value = type
      historyStore.setFilterType(type)
    }

    const viewRecord = (record) => {
      selectedRecord.value = record
    }

    const closeModal = () => {
      selectedRecord.value = null
    }

    const showRecordActions = (record) => {
      actionRecord.value = record
      showActionMenu.value = true
    }

    const hideActionMenu = () => {
      showActionMenu.value = false
      actionRecord.value = null
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

    const getTypeLabel = (type) => {
      const labelMap = {
        chat: '智能问诊',
        report: '报告解读',
        health: '健康科普',
        dermatology: '皮肤咨询',
        medication: '药物咨询'
      }
      return labelMap[type] || '未知类型'
    }

    const getRecordPreview = (content) => {
      return content.length > 50 ? content.substring(0, 50) + '...' : content
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

    const formatDetailTime = (date) => {
      const recordDate = new Date(date)
      return recordDate.toLocaleString()
    }

    const copyRecord = () => {
      if (!selectedRecord.value) return

      const content = `${selectedRecord.value.title}\n\n${selectedRecord.value.content}`
      uni.setClipboardData({
        data: content,
        success: () => {
          uni.showToast({
            title: '已复制到剪贴板',
            icon: 'success'
          })
          closeModal()
        }
      })
    }

    const shareRecord = () => {
      if (!selectedRecord.value) return

      const content = `${selectedRecord.value.title}\n\n${selectedRecord.value.content}`
      uni.share({
        title: selectedRecord.value.title,
        summary: content.substring(0, 100) + '...',
        success: () => {
          uni.showToast({
            title: '分享成功',
            icon: 'success'
          })
          closeModal()
        },
        fail: () => {
          copyRecord()
        }
      })
    }

    const deleteRecord = () => {
      if (!selectedRecord.value) return

      uni.showModal({
        title: '确认删除',
        content: '是否删除这条记录？',
        success: (res) => {
          if (res.confirm) {
            historyStore.deleteRecord(selectedRecord.value.id)
            closeModal()
            uni.showToast({
              title: '已删除',
              icon: 'success'
            })
          }
        }
      })
    }

    const copySelectedRecord = () => {
      if (!actionRecord.value) return
      selectedRecord.value = actionRecord.value
      hideActionMenu()
      copyRecord()
    }

    const shareSelectedRecord = () => {
      if (!actionRecord.value) return
      selectedRecord.value = actionRecord.value
      hideActionMenu()
      shareRecord()
    }

    const deleteSelectedRecord = () => {
      if (!actionRecord.value) return
      selectedRecord.value = actionRecord.value
      hideActionMenu()
      deleteRecord()
    }

    const exportRecords = () => {
      const exportData = historyStore.exportRecords(filterType.value)
      const content = JSON.stringify(exportData, null, 2)
      
      uni.setClipboardData({
        data: content,
        success: () => {
          uni.showToast({
            title: '数据已复制到剪贴板',
            icon: 'success'
          })
        }
      })
    }

    const clearAllRecords = () => {
      uni.showModal({
        title: '确认清空',
        content: '是否清空所有历史记录？此操作不可恢复。',
        success: (res) => {
          if (res.confirm) {
            if (filterType.value === 'all') {
              historyStore.clearAllRecords()
            } else {
              historyStore.clearRecordsByType(filterType.value)
            }
            uni.showToast({
              title: '已清空',
              icon: 'success'
            })
          }
        }
      })
    }

    const goToHome = () => {
      uni.switchTab({
        url: '/pages/home/index'
      })
    }

    return {
      searchKeyword,
      filterType,
      selectedRecord,
      showActionMenu,
      filterOptions,
      filteredRecords,
      statistics,
      onSearchInput,
      clearSearch,
      setFilter,
      viewRecord,
      closeModal,
      showRecordActions,
      hideActionMenu,
      getRecordIcon,
      getTypeLabel,
      getRecordPreview,
      formatTime,
      formatDetailTime,
      copyRecord,
      shareRecord,
      deleteRecord,
      copySelectedRecord,
      shareSelectedRecord,
      deleteSelectedRecord,
      exportRecords,
      clearAllRecords,
      goToHome
    }
  }
}
</script>

<style lang="scss" scoped>
.history-container {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 20rpx;
}

.search-filter-section {
  margin-bottom: 30rpx;
}

.search-box {
  display: flex;
  background: #fff;
  border-radius: 50rpx;
  padding: 10rpx 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
  align-items: center;
  margin-bottom: 20rpx;
}

.search-input {
  flex: 1;
  padding: 15rpx 20rpx;
  font-size: 28rpx;
  color: #333;
  background: transparent;
  border: none;
}

.search-btn {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  background: #f0f0f0;
  color: #999;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
}

.filter-tabs {
  display: flex;
  overflow-x: auto;
  gap: 15rpx;
  padding: 10rpx 0;
}

.filter-tab {
  display: flex;
  align-items: center;
  gap: 8rpx;
  background: #fff;
  border: 2rpx solid #e9ecef;
  border-radius: 30rpx;
  padding: 15rpx 25rpx;
  font-size: 26rpx;
  color: #666;
  white-space: nowrap;
  transition: all 0.2s ease;

  &.active {
    background: #1658FF;
    color: #fff;
    border-color: #1658FF;
  }
}

.filter-icon {
  font-size: 24rpx;
}

.filter-text {
  font-size: 26rpx;
}

.filter-count {
  font-size: 22rpx;
  opacity: 0.8;
}

.stats-section {
  margin-bottom: 30rpx;
}

.section-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 20rpx;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15rpx;
}

.stats-card {
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

.records-section {
  flex: 1;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
  flex-wrap: wrap;
  gap: 15rpx;
}

.header-actions {
  display: flex;
  gap: 10rpx;
}

.action-btn {
  background: #f8f9fa;
  color: #666;
  border: 2rpx solid #e9ecef;
  border-radius: 30rpx;
  padding: 12rpx 24rpx;
  font-size: 24rpx;

  &.danger {
    color: #dc3545;
    border-color: #dc3545;
  }
}

.records-list {
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.record-item {
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

.record-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  font-size: 32rpx;
  flex-shrink: 0;
}

.record-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-right: 15rpx;
}

.record-title {
  font-size: 30rpx;
  color: #333;
  font-weight: 500;
}

.record-preview {
  font-size: 26rpx;
  color: #666;
  line-height: 1.4;
}

.record-time {
  font-size: 22rpx;
  color: #999;
}

.record-type {
  flex-shrink: 0;
}

.type-tag {
  background: #f0f0f0;
  color: #666;
  padding: 8rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;

  &.chat { background: #e3f2fd; color: #1976d2; }
  &.report { background: #f3e5f5; color: #7b1fa2; }
  &.health { background: #e8f5e8; color: #388e3c; }
  &.dermatology { background: #fff3e0; color: #f57c00; }
  &.medication { background: #fce4ec; color: #c2185b; }
}

.empty-state {
  text-align: center;
  padding: 100rpx 40rpx;
  background: #fff;
  border-radius: 16rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.empty-icon {
  font-size: 120rpx;
  display: block;
  margin-bottom: 30rpx;
  opacity: 0.5;
}

.empty-title {
  font-size: 36rpx;
  color: #333;
  font-weight: bold;
  display: block;
  margin-bottom: 15rpx;
}

.empty-desc {
  font-size: 28rpx;
  color: #666;
  display: block;
  margin-bottom: 40rpx;
}

.empty-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 50rpx;
  padding: 24rpx 48rpx;
  font-size: 30rpx;
}

.record-modal {
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
  padding: 40rpx;
}

.modal-content {
  background: #fff;
  border-radius: 20rpx;
  max-width: 100%;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.modal-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  flex: 1;
  margin-right: 20rpx;
}

.modal-close {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  background: #f0f0f0;
  color: #999;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
}

.modal-body {
  flex: 1;
  padding: 30rpx;
  overflow-y: auto;
}

.record-info {
  display: flex;
  margin-bottom: 20rpx;
}

.info-label {
  font-size: 28rpx;
  color: #666;
  margin-right: 10rpx;
  flex-shrink: 0;
}

.info-value {
  font-size: 28rpx;
  color: #333;
  flex: 1;
}

.record-detail {
  margin-top: 30rpx;
  padding: 25rpx;
  background: #f8f9fa;
  border-radius: 12rpx;
}

.detail-content {
  font-size: 28rpx;
  color: #333;
  line-height: 1.6;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.modal-actions {
  display: flex;
  gap: 15rpx;
  padding: 30rpx;
  border-top: 1rpx solid #f0f0f0;
}

.modal-btn {
  flex: 1;
  background: #f8f9fa;
  color: #666;
  border: 2rpx solid #e9ecef;
  border-radius: 30rpx;
  padding: 20rpx;
  font-size: 28rpx;

  &.danger {
    color: #dc3545;
    border-color: #dc3545;
  }
}

.action-menu {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1000;
}

.menu-content {
  background: #fff;
  border-radius: 20rpx 20rpx 0 0;
  width: 100%;
  max-width: 750rpx;
  padding: 30rpx;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  width: 100%;
  padding: 30rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
  background: transparent;
  border: none;
  font-size: 30rpx;
  color: #333;

  &:last-child {
    border-bottom: none;
  }

  &.danger {
    color: #dc3545;
  }
}

.menu-icon {
  font-size: 32rpx;
}

.menu-text {
  font-size: 30rpx;
}
</style>
