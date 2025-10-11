import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    // 用户基本信息
    userInfo: {
      id: null,
      nickname: '',
      avatar: '',
      phone: '',
      email: '',
      gender: '', // male, female, unknown
      age: null,
      location: ''
    },
    // 用户偏好设置
    preferences: {
      theme: 'light', // light, dark
      language: 'zh-CN',
      notifications: true,
      autoSave: true,
      voiceInput: false,
      fontSize: 'medium' // small, medium, large
    },
    // 用户使用统计
    statistics: {
      totalChats: 0,
      totalReports: 0,
      totalQueries: 0,
      joinDate: null,
      lastActiveDate: null
    },
    // 登录状态
    isLoggedIn: false,
    // 访客模式
    isGuestMode: true
  }),

  getters: {
    // 是否已完善基本信息
    hasCompleteProfile: (state) => {
      return !!(state.userInfo.nickname && state.userInfo.gender && state.userInfo.age)
    },

    // 用户显示名称
    displayName: (state) => {
      return state.userInfo.nickname || '医疗助手用户'
    },

    // 用户头像
    displayAvatar: (state) => {
      return state.userInfo.avatar || '/static/images/default-avatar.png'
    },

    // 是否开启通知
    notificationsEnabled: (state) => {
      return state.preferences.notifications
    },

    // 主题模式
    currentTheme: (state) => {
      return state.preferences.theme
    },

    // 用户等级（基于使用次数）
    userLevel: (state) => {
      const total = state.statistics.totalChats + state.statistics.totalReports + state.statistics.totalQueries
      if (total >= 100) return 'expert'
      if (total >= 50) return 'advanced'
      if (total >= 20) return 'intermediate'
      if (total >= 5) return 'beginner'
      return 'newcomer'
    },

    // 用户等级描述
    userLevelDesc: (state) => {
      const levelMap = {
        newcomer: '新手用户',
        beginner: '初级用户',
        intermediate: '中级用户',
        advanced: '高级用户',
        expert: '专家用户'
      }
      return levelMap[state.userLevel] || '新手用户'
    }
  },

  actions: {
    // 设置用户信息
    setUserInfo(userInfo) {
      this.userInfo = { ...this.userInfo, ...userInfo }
      this.saveToLocal()
    },

    // 更新用户偏好
    updatePreferences(preferences) {
      this.preferences = { ...this.preferences, ...preferences }
      this.saveToLocal()
    },

    // 设置登录状态
    setLoginStatus(isLoggedIn) {
      this.isLoggedIn = isLoggedIn
      this.isGuestMode = !isLoggedIn
      
      if (isLoggedIn) {
        this.updateStatistics({ lastActiveDate: new Date() })
      }
      
      this.saveToLocal()
    },

    // 退出登录
    logout() {
      this.userInfo = {
        id: null,
        nickname: '',
        avatar: '',
        phone: '',
        email: '',
        gender: '',
        age: null,
        location: ''
      }
      this.isLoggedIn = false
      this.isGuestMode = true
      this.saveToLocal()
    },

    // 切换访客模式
    toggleGuestMode() {
      this.isGuestMode = !this.isGuestMode
      this.saveToLocal()
    },

    // 更新统计信息
    updateStatistics(stats) {
      this.statistics = { ...this.statistics, ...stats }
      this.saveToLocal()
    },

    // 增加聊天次数
    incrementChats() {
      this.statistics.totalChats++
      this.statistics.lastActiveDate = new Date()
      this.saveToLocal()
    },

    // 增加报告解读次数
    incrementReports() {
      this.statistics.totalReports++
      this.statistics.lastActiveDate = new Date()
      this.saveToLocal()
    },

    // 增加查询次数
    incrementQueries() {
      this.statistics.totalQueries++
      this.statistics.lastActiveDate = new Date()
      this.saveToLocal()
    },

    // 设置主题
    setTheme(theme) {
      this.preferences.theme = theme
      this.saveToLocal()
      
      // 应用主题到系统
      this.applyTheme(theme)
    },

    // 应用主题
    applyTheme(theme) {
      // 这里可以添加主题切换逻辑
      if (theme === 'dark') {
        // 应用暗色主题
        uni.setTabBarStyle({
          backgroundColor: '#1f1f1f',
          color: '#999999',
          selectedColor: '#1658FF'
        })
      } else {
        // 应用亮色主题
        uni.setTabBarStyle({
          backgroundColor: '#ffffff',
          color: '#7A7E83',
          selectedColor: '#1658FF'
        })
      }
    },

    // 设置字体大小
    setFontSize(fontSize) {
      this.preferences.fontSize = fontSize
      this.saveToLocal()
    },

    // 切换通知设置
    toggleNotifications() {
      this.preferences.notifications = !this.preferences.notifications
      this.saveToLocal()
    },

    // 切换自动保存
    toggleAutoSave() {
      this.preferences.autoSave = !this.preferences.autoSave
      this.saveToLocal()
    },

    // 切换语音输入
    toggleVoiceInput() {
      this.preferences.voiceInput = !this.preferences.voiceInput
      this.saveToLocal()
    },

    // 初始化用户数据
    initUserData() {
      if (!this.statistics.joinDate) {
        this.statistics.joinDate = new Date()
      }
      this.statistics.lastActiveDate = new Date()
      this.saveToLocal()
    },

    // 重置统计数据
    resetStatistics() {
      this.statistics = {
        totalChats: 0,
        totalReports: 0,
        totalQueries: 0,
        joinDate: new Date(),
        lastActiveDate: new Date()
      }
      this.saveToLocal()
    },

    // 保存到本地存储
    saveToLocal() {
      try {
        const userData = {
          userInfo: this.userInfo,
          preferences: this.preferences,
          statistics: this.statistics,
          isLoggedIn: this.isLoggedIn,
          isGuestMode: this.isGuestMode
        }
        uni.setStorageSync('user_data', userData)
      } catch (error) {
        console.error('保存用户数据失败:', error)
      }
    },

    // 从本地存储加载
    loadFromLocal() {
      try {
        const userData = uni.getStorageSync('user_data')
        if (userData) {
          this.userInfo = userData.userInfo || this.userInfo
          this.preferences = userData.preferences || this.preferences
          this.statistics = userData.statistics || this.statistics
          this.isLoggedIn = userData.isLoggedIn || false
          this.isGuestMode = userData.isGuestMode !== undefined ? userData.isGuestMode : true
          
          // 应用主题
          this.applyTheme(this.preferences.theme)
        }
      } catch (error) {
        console.error('加载用户数据失败:', error)
      }
    },

    // 清除所有用户数据
    clearAllData() {
      this.userInfo = {
        id: null,
        nickname: '',
        avatar: '',
        phone: '',
        email: '',
        gender: '',
        age: null,
        location: ''
      }
      this.preferences = {
        theme: 'light',
        language: 'zh-CN',
        notifications: true,
        autoSave: true,
        voiceInput: false,
        fontSize: 'medium'
      }
      this.statistics = {
        totalChats: 0,
        totalReports: 0,
        totalQueries: 0,
        joinDate: null,
        lastActiveDate: null
      }
      this.isLoggedIn = false
      this.isGuestMode = true
      
      uni.removeStorageSync('user_data')
    },

    // 导出用户数据
    exportUserData() {
      return {
        userInfo: this.userInfo,
        preferences: this.preferences,
        statistics: this.statistics,
        exportDate: new Date()
      }
    }
  }
})
