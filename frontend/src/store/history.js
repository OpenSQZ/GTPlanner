import { defineStore } from 'pinia'

export const useHistoryStore = defineStore('history', {
  state: () => ({
    // 历史记录列表
    records: [],
    // 加载状态
    loading: false,
    // 搜索关键词
    searchKeyword: '',
    // 过滤类型
    filterType: 'all' // all, chat, report, health, dermatology, medication
  }),

  getters: {
    // 过滤后的记录
    filteredRecords: (state) => {
      let filtered = state.records

      // 按类型过滤
      if (state.filterType !== 'all') {
        filtered = filtered.filter(record => record.type === state.filterType)
      }

      // 按关键词搜索
      if (state.searchKeyword) {
        const keyword = state.searchKeyword.toLowerCase()
        filtered = filtered.filter(record => 
          record.title.toLowerCase().includes(keyword) ||
          record.content.toLowerCase().includes(keyword)
        )
      }

      // 按时间倒序排列
      return filtered.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    },

    // 按类型分组的记录数量
    recordCountByType: (state) => {
      const counts = {
        all: state.records.length,
        chat: 0,
        report: 0,
        health: 0,
        dermatology: 0,
        medication: 0
      }

      state.records.forEach(record => {
        if (counts.hasOwnProperty(record.type)) {
          counts[record.type]++
        }
      })

      return counts
    },

    // 最近的记录（最近7天）
    recentRecords: (state) => {
      const sevenDaysAgo = new Date()
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
      
      return state.records.filter(record => 
        new Date(record.createdAt) >= sevenDaysAgo
      ).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    }
  },

  actions: {
    // 添加历史记录
    addRecord(record) {
      const newRecord = {
        id: Date.now() + Math.random().toString(36).substr(2, 9),
        createdAt: new Date(),
        ...record
      }
      
      this.records.unshift(newRecord)
      this.saveToLocal()
      return newRecord
    },

    // 添加聊天记录
    addChatRecord(title, content, agentType) {
      return this.addRecord({
        type: 'chat',
        title: title || '智能问诊',
        content,
        agentType,
        icon: 'chat'
      })
    },

    // 添加报告解读记录
    addReportRecord(fileName, content) {
      return this.addRecord({
        type: 'report',
        title: `报告解读 - ${fileName}`,
        content,
        fileName,
        icon: 'document'
      })
    },

    // 添加健康科普记录
    addHealthRecord(question, content) {
      return this.addRecord({
        type: 'health',
        title: `健康科普 - ${question}`,
        content,
        question,
        icon: 'book'
      })
    },

    // 添加皮肤病咨询记录
    addDermatologyRecord(symptoms, content, imagePath) {
      return this.addRecord({
        type: 'dermatology',
        title: `皮肤病咨询 - ${symptoms || '症状描述'}`,
        content,
        symptoms,
        imagePath,
        icon: 'camera'
      })
    },

    // 添加药物咨询记录
    addMedicationRecord(question, content) {
      return this.addRecord({
        type: 'medication',
        title: `药物咨询 - ${question}`,
        content,
        question,
        icon: 'pill'
      })
    },

    // 删除记录
    deleteRecord(recordId) {
      const index = this.records.findIndex(record => record.id === recordId)
      if (index > -1) {
        this.records.splice(index, 1)
        this.saveToLocal()
      }
    },

    // 批量删除记录
    deleteRecords(recordIds) {
      this.records = this.records.filter(record => !recordIds.includes(record.id))
      this.saveToLocal()
    },

    // 清空所有记录
    clearAllRecords() {
      this.records = []
      this.saveToLocal()
    },

    // 清空指定类型的记录
    clearRecordsByType(type) {
      this.records = this.records.filter(record => record.type !== type)
      this.saveToLocal()
    },

    // 设置搜索关键词
    setSearchKeyword(keyword) {
      this.searchKeyword = keyword
    },

    // 设置过滤类型
    setFilterType(type) {
      this.filterType = type
    },

    // 设置加载状态
    setLoading(loading) {
      this.loading = loading
    },

    // 获取指定记录
    getRecord(recordId) {
      return this.records.find(record => record.id === recordId)
    },

    // 更新记录
    updateRecord(recordId, updates) {
      const index = this.records.findIndex(record => record.id === recordId)
      if (index > -1) {
        this.records[index] = {
          ...this.records[index],
          ...updates,
          updatedAt: new Date()
        }
        this.saveToLocal()
      }
    },

    // 保存到本地存储
    saveToLocal() {
      try {
        uni.setStorageSync('history_records', this.records)
      } catch (error) {
        console.error('保存历史记录失败:', error)
      }
    },

    // 从本地存储加载
    loadFromLocal() {
      try {
        const records = uni.getStorageSync('history_records')
        if (records && Array.isArray(records)) {
          this.records = records
        }
      } catch (error) {
        console.error('加载历史记录失败:', error)
        this.records = []
      }
    },

    // 导出记录
    exportRecords(type = 'all') {
      let recordsToExport = this.records
      
      if (type !== 'all') {
        recordsToExport = this.records.filter(record => record.type === type)
      }
      
      const exportData = {
        exportTime: new Date(),
        totalCount: recordsToExport.length,
        records: recordsToExport
      }
      
      return exportData
    },

    // 获取统计信息
    getStatistics() {
      const now = new Date()
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
      const thisWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
      const thisMonth = new Date(now.getFullYear(), now.getMonth(), 1)

      const todayRecords = this.records.filter(r => new Date(r.createdAt) >= today)
      const yesterdayRecords = this.records.filter(r => 
        new Date(r.createdAt) >= yesterday && new Date(r.createdAt) < today
      )
      const thisWeekRecords = this.records.filter(r => new Date(r.createdAt) >= thisWeek)
      const thisMonthRecords = this.records.filter(r => new Date(r.createdAt) >= thisMonth)

      return {
        total: this.records.length,
        today: todayRecords.length,
        yesterday: yesterdayRecords.length,
        thisWeek: thisWeekRecords.length,
        thisMonth: thisMonthRecords.length,
        byType: this.recordCountByType
      }
    }
  }
})
