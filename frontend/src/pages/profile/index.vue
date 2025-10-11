<template>
  <view class="profile-container">
    <!-- 用户信息卡片 -->
    <view class="user-card">
      <view class="user-avatar" @click="changeAvatar">
        <image v-if="userInfo.avatar" :src="userInfo.avatar" mode="aspectFill" />
        <text v-else class="avatar-placeholder">👤</text>
      </view>
      
      <view class="user-info">
        <text class="user-name">{{ displayName }}</text>
        <text class="user-level">{{ userLevelDesc }}</text>
        <text class="user-join-date">加入时间：{{ joinDate }}</text>
      </view>
      
      <button class="edit-btn" @click="editProfile">编辑</button>
    </view>

    <!-- 使用统计 -->
    <view class="stats-section">
      <text class="section-title">📊 使用统计</text>
      <view class="stats-grid">
        <view class="stats-item">
          <text class="stats-icon">💬</text>
          <text class="stats-number">{{ statistics.totalChats }}</text>
          <text class="stats-label">智能问诊</text>
        </view>
        <view class="stats-item">
          <text class="stats-icon">📋</text>
          <text class="stats-number">{{ statistics.totalReports }}</text>
          <text class="stats-label">报告解读</text>
        </view>
        <view class="stats-item">
          <text class="stats-icon">🔍</text>
          <text class="stats-number">{{ statistics.totalQueries }}</text>
          <text class="stats-label">健康咨询</text>
        </view>
        <view class="stats-item">
          <text class="stats-icon">🏆</text>
          <text class="stats-number">{{ totalUsage }}</text>
          <text class="stats-label">总计使用</text>
        </view>
      </view>
    </view>

    <!-- 功能菜单 -->
    <view class="menu-section">
      <view class="menu-group">
        <view class="menu-item" @click="viewHistory">
          <text class="menu-icon">📚</text>
          <text class="menu-text">历史记录</text>
          <text class="menu-badge" v-if="historyCount > 0">{{ historyCount }}</text>
          <text class="menu-arrow">›</text>
        </view>
        
        <view class="menu-item" @click="exportData">
          <text class="menu-icon">📤</text>
          <text class="menu-text">数据导出</text>
          <text class="menu-arrow">›</text>
        </view>
      </view>

      <view class="menu-group">
        <view class="menu-item" @click="showSettings">
          <text class="menu-icon">⚙️</text>
          <text class="menu-text">设置</text>
          <text class="menu-arrow">›</text>
        </view>
        
        <view class="menu-item" @click="showHelp">
          <text class="menu-icon">❓</text>
          <text class="menu-text">帮助与反馈</text>
          <text class="menu-arrow">›</text>
        </view>
        
        <view class="menu-item" @click="showAbout">
          <text class="menu-icon">ℹ️</text>
          <text class="menu-text">关于我们</text>
          <text class="menu-arrow">›</text>
        </view>
      </view>

      <view class="menu-group">
        <view class="menu-item danger" @click="clearAllData">
          <text class="menu-icon">🗑️</text>
          <text class="menu-text">清空所有数据</text>
          <text class="menu-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 健康提醒 -->
    <view class="reminder-section">
      <view class="reminder-card">
        <view class="reminder-header">
          <text class="reminder-icon">💡</text>
          <text class="reminder-title">健康提醒</text>
        </view>
        <text class="reminder-content">{{ healthReminder }}</text>
      </view>
    </view>

    <!-- 编辑资料弹窗 -->
    <view class="edit-modal" v-if="showEditModal" @click="closeEditModal">
      <view class="modal-content" @click.stop>
        <view class="modal-header">
          <text class="modal-title">编辑资料</text>
          <button class="modal-close" @click="closeEditModal">✕</button>
        </view>
        
        <view class="modal-body">
          <view class="form-group">
            <text class="form-label">昵称</text>
            <input 
              class="form-input" 
              v-model="editForm.nickname" 
              placeholder="请输入昵称"
              maxlength="20"
            />
          </view>
          
          <view class="form-group">
            <text class="form-label">性别</text>
            <view class="radio-group">
              <button 
                class="radio-btn" 
                :class="{ active: editForm.gender === 'male' }"
                @click="editForm.gender = 'male'"
              >
                男
              </button>
              <button 
                class="radio-btn" 
                :class="{ active: editForm.gender === 'female' }"
                @click="editForm.gender = 'female'"
              >
                女
              </button>
            </view>
          </view>
          
          <view class="form-group">
            <text class="form-label">年龄</text>
            <input 
              class="form-input" 
              v-model="editForm.age" 
              placeholder="请输入年龄"
              type="number"
            />
          </view>
        </view>
        
        <view class="modal-actions">
          <button class="modal-btn secondary" @click="closeEditModal">取消</button>
          <button class="modal-btn primary" @click="saveProfile">保存</button>
        </view>
      </view>
    </view>

    <!-- 设置弹窗 -->
    <view class="settings-modal" v-if="showSettingsModal" @click="closeSettingsModal">
      <view class="modal-content" @click.stop>
        <view class="modal-header">
          <text class="modal-title">设置</text>
          <button class="modal-close" @click="closeSettingsModal">✕</button>
        </view>
        
        <view class="modal-body">
          <view class="setting-group">
            <view class="setting-item">
              <text class="setting-label">主题模式</text>
              <view class="setting-control">
                <button 
                  class="theme-btn" 
                  :class="{ active: preferences.theme === 'light' }"
                  @click="setTheme('light')"
                >
                  浅色
                </button>
                <button 
                  class="theme-btn" 
                  :class="{ active: preferences.theme === 'dark' }"
                  @click="setTheme('dark')"
                >
                  深色
                </button>
              </view>
            </view>
            
            <view class="setting-item">
              <text class="setting-label">字体大小</text>
              <view class="setting-control">
                <button 
                  class="font-btn" 
                  :class="{ active: preferences.fontSize === 'small' }"
                  @click="setFontSize('small')"
                >
                  小
                </button>
                <button 
                  class="font-btn" 
                  :class="{ active: preferences.fontSize === 'medium' }"
                  @click="setFontSize('medium')"
                >
                  中
                </button>
                <button 
                  class="font-btn" 
                  :class="{ active: preferences.fontSize === 'large' }"
                  @click="setFontSize('large')"
                >
                  大
                </button>
              </view>
            </view>
            
            <view class="setting-item">
              <view class="setting-info">
                <text class="setting-label">推送通知</text>
                <text class="setting-desc">接收健康提醒和功能更新</text>
              </view>
              <switch 
                :checked="preferences.notifications" 
                @change="toggleNotifications"
              />
            </view>
            
            <view class="setting-item">
              <view class="setting-info">
                <text class="setting-label">自动保存</text>
                <text class="setting-desc">自动保存聊天记录和查询历史</text>
              </view>
              <switch 
                :checked="preferences.autoSave" 
                @change="toggleAutoSave"
              />
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { ref, computed, reactive, onMounted } from 'vue'
import { useUserStore, useHistoryStore } from '@/store'

export default {
  name: 'ProfilePage',
  setup() {
    const userStore = useUserStore()
    const historyStore = useHistoryStore()

    // 响应式数据
    const showEditModal = ref(false)
    const showSettingsModal = ref(false)
    const editForm = reactive({
      nickname: '',
      gender: '',
      age: ''
    })

    // 健康提醒
    const healthReminders = [
      '记得多喝水，每天至少8杯水有助于身体健康',
      '适当运动，每天30分钟运动能增强免疫力',
      '保持良好作息，规律睡眠有助于身体恢复',
      '均衡饮食，多吃蔬菜水果少吃油腻食物',
      '定期体检，预防胜于治疗'
    ]
    
    const healthReminder = ref(healthReminders[Math.floor(Math.random() * healthReminders.length)])

    // 计算属性
    const userInfo = computed(() => userStore.userInfo)
    const displayName = computed(() => userStore.displayName)
    const userLevelDesc = computed(() => userStore.userLevelDesc)
    const statistics = computed(() => userStore.statistics)
    const preferences = computed(() => userStore.preferences)
    const totalUsage = computed(() => 
      statistics.value.totalChats + statistics.value.totalReports + statistics.value.totalQueries
    )
    const historyCount = computed(() => historyStore.records.length)

    const joinDate = computed(() => {
      if (statistics.value.joinDate) {
        return new Date(statistics.value.joinDate).toLocaleDateString()
      }
      return '今天'
    })

    // 生命周期
    onMounted(() => {
      userStore.loadFromLocal()
      historyStore.loadFromLocal()
    })

    // 方法
    const changeAvatar = () => {
      uni.chooseImage({
        count: 1,
        sourceType: ['camera', 'album'],
        success: (res) => {
          const tempFilePath = res.tempFilePaths[0]
          userStore.setUserInfo({ avatar: tempFilePath })
          uni.showToast({
            title: '头像更新成功',
            icon: 'success'
          })
        }
      })
    }

    const editProfile = () => {
      editForm.nickname = userInfo.value.nickname
      editForm.gender = userInfo.value.gender
      editForm.age = userInfo.value.age
      showEditModal.value = true
    }

    const closeEditModal = () => {
      showEditModal.value = false
    }

    const saveProfile = () => {
      const updates = {
        nickname: editForm.nickname.trim(),
        gender: editForm.gender,
        age: parseInt(editForm.age) || null
      }

      userStore.setUserInfo(updates)
      closeEditModal()
      
      uni.showToast({
        title: '保存成功',
        icon: 'success'
      })
    }

    const viewHistory = () => {
      uni.switchTab({
        url: '/pages/history/index'
      })
    }

    const exportData = () => {
      const userData = userStore.exportUserData()
      const historyData = historyStore.exportRecords()
      
      const exportData = {
        user: userData,
        history: historyData,
        exportTime: new Date()
      }

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

    const showSettings = () => {
      showSettingsModal.value = true
    }

    const closeSettingsModal = () => {
      showSettingsModal.value = false
    }

    const setTheme = (theme) => {
      userStore.setTheme(theme)
      uni.showToast({
        title: `已切换到${theme === 'light' ? '浅色' : '深色'}主题`,
        icon: 'success'
      })
    }

    const setFontSize = (fontSize) => {
      userStore.setFontSize(fontSize)
      uni.showToast({
        title: '字体大小已更新',
        icon: 'success'
      })
    }

    const toggleNotifications = (e) => {
      userStore.updatePreferences({ notifications: e.detail.value })
    }

    const toggleAutoSave = (e) => {
      userStore.updatePreferences({ autoSave: e.detail.value })
    }

    const showHelp = () => {
      uni.showModal({
        title: '帮助与反馈',
        content: '如有问题请联系客服或发送邮件至：support@medical-ai.com',
        showCancel: false,
        confirmText: '知道了'
      })
    }

    const showAbout = () => {
      uni.showModal({
        title: '关于医疗智能体',
        content: '版本：1.0.0\n基于AI技术的智能医疗助手\n仅供参考，不替代专业医疗建议',
        showCancel: false,
        confirmText: '知道了'
      })
    }

    const clearAllData = () => {
      uni.showModal({
        title: '清空所有数据',
        content: '此操作将清空所有个人数据和历史记录，且不可恢复。确定要继续吗？',
        success: (res) => {
          if (res.confirm) {
            userStore.clearAllData()
            historyStore.clearAllRecords()
            
            uni.showToast({
              title: '数据已清空',
              icon: 'success'
            })
          }
        }
      })
    }

    return {
      showEditModal,
      showSettingsModal,
      editForm,
      healthReminder,
      userInfo,
      displayName,
      userLevelDesc,
      statistics,
      preferences,
      totalUsage,
      historyCount,
      joinDate,
      changeAvatar,
      editProfile,
      closeEditModal,
      saveProfile,
      viewHistory,
      exportData,
      showSettings,
      closeSettingsModal,
      setTheme,
      setFontSize,
      toggleNotifications,
      toggleAutoSave,
      showHelp,
      showAbout,
      clearAllData
    }
  }
}
</script>

<style lang="scss" scoped>
.profile-container {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 20rpx;
}

.user-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 20rpx;
  padding: 40rpx 30rpx;
  margin-bottom: 30rpx;
  display: flex;
  align-items: center;
  gap: 25rpx;
  box-shadow: 0 4rpx 12rpx rgba(102, 126, 234, 0.3);
}

.user-avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  image {
    width: 100%;
    height: 100%;
  }
}

.avatar-placeholder {
  font-size: 48rpx;
  color: rgba(255, 255, 255, 0.8);
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.user-name {
  font-size: 36rpx;
  font-weight: bold;
}

.user-level {
  font-size: 26rpx;
  opacity: 0.9;
}

.user-join-date {
  font-size: 24rpx;
  opacity: 0.8;
}

.edit-btn {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  border: 2rpx solid rgba(255, 255, 255, 0.3);
  border-radius: 30rpx;
  padding: 15rpx 30rpx;
  font-size: 26rpx;
  flex-shrink: 0;
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15rpx;
}

.stats-item {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx 20rpx;
  text-align: center;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.stats-icon {
  font-size: 36rpx;
}

.stats-number {
  font-size: 40rpx;
  font-weight: bold;
  color: #1658FF;
}

.stats-label {
  font-size: 26rpx;
  color: #666;
}

.menu-section {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  margin-bottom: 30rpx;
}

.menu-group {
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
}

.menu-item {
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

  &.danger {
    .menu-text, .menu-icon {
      color: #dc3545;
    }
  }
}

.menu-icon {
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

.menu-text {
  flex: 1;
  font-size: 30rpx;
  color: #333;
  margin-right: 15rpx;
}

.menu-badge {
  background: #ff4757;
  color: #fff;
  font-size: 22rpx;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  margin-right: 15rpx;
}

.menu-arrow {
  font-size: 32rpx;
  color: #ccc;
  flex-shrink: 0;
}

.reminder-section {
  margin-bottom: 30rpx;
}

.reminder-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
  border-left: 6rpx solid #28a745;
}

.reminder-header {
  display: flex;
  align-items: center;
  gap: 15rpx;
  margin-bottom: 15rpx;
}

.reminder-icon {
  font-size: 32rpx;
}

.reminder-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.reminder-content {
  font-size: 28rpx;
  color: #666;
  line-height: 1.6;
}

.edit-modal, .settings-modal {
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
  min-width: 600rpx;
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

.form-group {
  margin-bottom: 30rpx;
}

.form-label {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 15rpx;
  display: block;
}

.form-input {
  width: 100%;
  background: #f8f9fa;
  border: 2rpx solid #e9ecef;
  border-radius: 12rpx;
  padding: 20rpx 25rpx;
  font-size: 30rpx;
  color: #333;
  box-sizing: border-box;

  &:focus {
    border-color: #1658FF;
  }
}

.radio-group {
  display: flex;
  gap: 15rpx;
}

.radio-btn {
  flex: 1;
  background: #f8f9fa;
  color: #666;
  border: 2rpx solid #e9ecef;
  border-radius: 30rpx;
  padding: 20rpx;
  font-size: 28rpx;

  &.active {
    background: #1658FF;
    color: #fff;
    border-color: #1658FF;
  }
}

.modal-actions {
  display: flex;
  gap: 15rpx;
  padding: 30rpx;
  border-top: 1rpx solid #f0f0f0;
}

.modal-btn {
  flex: 1;
  padding: 20rpx;
  border-radius: 30rpx;
  font-size: 30rpx;
  border: none;

  &.secondary {
    background: #f8f9fa;
    color: #666;
  }

  &.primary {
    background: #1658FF;
    color: #fff;
  }
}

.setting-group {
  display: flex;
  flex-direction: column;
  gap: 30rpx;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20rpx;
}

.setting-info {
  flex: 1;
}

.setting-label {
  font-size: 30rpx;
  color: #333;
  display: block;
  margin-bottom: 5rpx;
}

.setting-desc {
  font-size: 24rpx;
  color: #666;
}

.setting-control {
  display: flex;
  gap: 10rpx;
}

.theme-btn, .font-btn {
  background: #f8f9fa;
  color: #666;
  border: 2rpx solid #e9ecef;
  border-radius: 20rpx;
  padding: 12rpx 20rpx;
  font-size: 24rpx;

  &.active {
    background: #1658FF;
    color: #fff;
    border-color: #1658FF;
  }
}
</style>
