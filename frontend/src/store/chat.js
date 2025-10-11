import { defineStore } from 'pinia'

export const useChatStore = defineStore('chat', {
  state: () => ({
    // 当前会话消息列表
    messages: [],
    // 是否正在加载中
    loading: false,
    // 当前会话ID
    currentSessionId: null,
    // 最后一次请求的类型
    lastRequestType: null
  }),

  getters: {
    // 获取用户消息
    userMessages: (state) => state.messages.filter(msg => msg.role === 'user'),
    
    // 获取AI消息
    aiMessages: (state) => state.messages.filter(msg => msg.role === 'assistant'),
    
    // 是否有消息
    hasMessages: (state) => state.messages.length > 0,
    
    // 最后一条消息
    lastMessage: (state) => state.messages[state.messages.length - 1]
  },

  actions: {
    // 添加消息
    addMessage(message) {
      const newMessage = {
        id: Date.now() + Math.random().toString(36).substr(2, 9),
        timestamp: new Date(),
        ...message
      }
      this.messages.push(newMessage)
      return newMessage
    },

    // 添加用户消息
    addUserMessage(content) {
      return this.addMessage({
        role: 'user',
        content,
        type: 'text'
      })
    },

    // 添加AI消息
    addAIMessage(content, type = 'text', extra = {}) {
      return this.addMessage({
        role: 'assistant',
        content,
        type,
        ...extra
      })
    },

    // 更新最后一条AI消息（用于流式输出）
    updateLastAIMessage(content) {
      const lastMsg = this.messages[this.messages.length - 1]
      if (lastMsg && lastMsg.role === 'assistant') {
        lastMsg.content = content
        lastMsg.timestamp = new Date()
      }
    },

    // 更新指定ID的AI消息
    updateAIMessage(messageId, updates) {
      const message = this.messages.find(msg => msg.id === messageId)
      if (message && message.role === 'assistant') {
        Object.assign(message, updates)
        message.timestamp = new Date()
      }
    },

    // 设置加载状态
    setLoading(loading) {
      this.loading = loading
    },

    // 设置请求类型
    setRequestType(type) {
      this.lastRequestType = type
    },

    // 清空消息
    clearMessages() {
      this.messages = []
      this.currentSessionId = null
      this.lastRequestType = null
    },

    // 删除指定消息
    deleteMessage(messageId) {
      const index = this.messages.findIndex(msg => msg.id === messageId)
      if (index > -1) {
        this.messages.splice(index, 1)
      }
    },

    // 生成新的会话ID
    generateSessionId() {
      this.currentSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
      return this.currentSessionId
    },

    // 保存会话到本地存储
    saveSessionToLocal() {
      if (this.messages.length > 0) {
        const sessionData = {
          id: this.currentSessionId || this.generateSessionId(),
          messages: this.messages,
          lastRequestType: this.lastRequestType,
          createdAt: new Date(),
          updatedAt: new Date()
        }
        
        // 获取已保存的会话列表
        const savedSessions = uni.getStorageSync('chat_sessions') || []
        
        // 查找是否已存在相同会话
        const existingIndex = savedSessions.findIndex(session => session.id === sessionData.id)
        
        if (existingIndex > -1) {
          // 更新现有会话
          savedSessions[existingIndex] = sessionData
        } else {
          // 添加新会话
          savedSessions.unshift(sessionData)
        }
        
        // 限制保存的会话数量（最多50个）
        if (savedSessions.length > 50) {
          savedSessions.splice(50)
        }
        
        // 保存到本地存储
        uni.setStorageSync('chat_sessions', savedSessions)
        
        return sessionData
      }
    },

    // 从本地存储加载会话
    loadSessionFromLocal(sessionId) {
      const savedSessions = uni.getStorageSync('chat_sessions') || []
      const session = savedSessions.find(s => s.id === sessionId)
      
      if (session) {
        this.messages = session.messages || []
        this.currentSessionId = session.id
        this.lastRequestType = session.lastRequestType
        return session
      }
      
      return null
    },

    // 获取所有本地会话
    getLocalSessions() {
      return uni.getStorageSync('chat_sessions') || []
    },

    // 删除本地会话
    deleteLocalSession(sessionId) {
      const savedSessions = uni.getStorageSync('chat_sessions') || []
      const filteredSessions = savedSessions.filter(s => s.id !== sessionId)
      uni.setStorageSync('chat_sessions', filteredSessions)
      
      // 如果删除的是当前会话，则清空当前状态
      if (this.currentSessionId === sessionId) {
        this.clearMessages()
      }
    },

    // 清空所有本地会话
    clearAllLocalSessions() {
      uni.removeStorageSync('chat_sessions')
      this.clearMessages()
    }
  }
})
