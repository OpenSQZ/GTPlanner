<template>
  <view class="chat-container">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">🤖 智能问诊</text>
      <text class="page-desc">AI医疗助手为您提供专业健康咨询</text>
    </view>

    <!-- 聊天消息区域 -->
    <view class="chat-messages" v-if="hasMessages">
      <scroll-view 
        class="message-scroll" 
        scroll-y 
        :scroll-top="scrollTop"
        scroll-with-animation
      >
        <view 
          class="message-item" 
          v-for="message in messages" 
          :key="message.id"
          :class="message.role"
        >
          <!-- 用户消息 -->
          <view v-if="message.role === 'user'" class="user-message">
            <view class="message-bubble user-bubble">
              <text class="message-text">{{ message.content }}</text>
            </view>
            <view class="message-avatar user-avatar">
              <text class="avatar-text">我</text>
            </view>
          </view>

          <!-- AI消息 -->
          <view v-else class="ai-message">
            <view class="message-avatar ai-avatar">
              <text class="avatar-text">AI</text>
            </view>
            <view class="message-bubble ai-bubble">
              <!-- 意图识别结果 -->
              <view v-if="message.intentResult" class="intent-section">
                <text class="intent-label">识别意图：</text>
                <text class="intent-value">{{ getIntentText(message.intentResult) }}</text>
              </view>
              
              <!-- AI回复内容 -->
              <view class="message-text">
                <text v-if="message.loading" class="loading-text">
                  正在思考中<span class="loading-dots">...</span>
                </text>
                <text v-else>{{ message.content }}</text>
              </view>
              
              <!-- 智能体类型标签 -->
              <view v-if="message.agentType" class="agent-tag">
                <text class="agent-text">{{ message.agentType }}</text>
              </view>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- 欢迎区域 -->
    <view class="welcome-section" v-else>
      <view class="welcome-card">
        <text class="welcome-icon">👋</text>
        <text class="welcome-title">欢迎使用智能问诊</text>
        <text class="welcome-desc">请描述您的症状或健康问题，AI将为您提供专业建议</text>
      </view>

      <!-- 功能说明 -->
      <view class="features-section">
        <text class="features-title">🔧 智能功能</text>
        <view class="features-list">
          <view class="feature-item">
            <text class="feature-icon">🏥</text>
            <text class="feature-text">智能分诊 - 推荐合适科室</text>
          </view>
          <view class="feature-item">
            <text class="feature-icon">🔍</text>
            <text class="feature-text">症状自诊 - 分析可能疾病</text>
          </view>
          <view class="feature-item">
            <text class="feature-icon">📋</text>
            <text class="feature-text">病例整理 - 生成结构化病历</text>
          </view>
          <view class="feature-item">
            <text class="feature-icon">💬</text>
            <text class="feature-text">日常健康咨询</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 快捷输入区域 -->
    <view class="quick-input-section" v-if="!inputText.trim()">
      <text class="section-title">💡 常见问题</text>
      <view class="quick-buttons">
        <button 
          class="quick-btn" 
          v-for="btn in quickButtons" 
          :key="btn.text"
          @click="selectQuickInput(btn.text)"
        >
          {{ btn.text }}
        </button>
      </view>
    </view>

    <!-- 输入区域 -->
    <view class="input-section">
      <view class="input-container">
        <textarea 
          class="message-input"
          v-model="inputText"
          placeholder="请描述您的症状或健康问题..."
          :maxlength="500"
          :auto-height="true"
          @input="onInput"
          @confirm="sendMessage"
        />
        <text class="char-count">{{ inputText.length }}/500</text>
      </view>
      
      <view class="send-container">
        <button 
          class="send-btn" 
          :disabled="!canSend"
          :class="{ active: canSend }"
          @click="sendMessage"
        >
          <text v-if="isLoading" class="send-text">发送中</text>
          <text v-else class="send-text">发送</text>
        </button>
      </view>
    </view>

    <!-- 功能菜单 -->
    <view class="function-menu" v-if="showFunctionMenu">
      <view class="menu-item" @click="clearChat">
        <text class="menu-icon">🗑️</text>
        <text class="menu-text">清空对话</text>
      </view>
      <view class="menu-item" @click="exportChat">
        <text class="menu-icon">📤</text>
        <text class="menu-text">导出记录</text>
      </view>
    </view>

    <!-- 功能按钮 -->
    <view class="function-btn" @click="toggleFunctionMenu">
      <text class="btn-icon">⚙️</text>
    </view>
  </view>
</template>

<script>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useChatStore, useHistoryStore, useUserStore } from '@/store'
import { medicalChatApi, handleApiError } from '@/api'

export default {
  name: 'ChatPage',
  setup() {
    const chatStore = useChatStore()
    const historyStore = useHistoryStore()
    const userStore = useUserStore()

    // 响应式数据
    const inputText = ref('')
    const scrollTop = ref(0)
    const showFunctionMenu = ref(false)
    const isLoading = ref(false)

    // 快捷输入按钮
    const quickButtons = ref([
      { text: '我头痛发烧，应该看什么科？' },
      { text: '我最近失眠严重，可能是什么原因？' },
      { text: '胸闷气短，需要做什么检查？' },
      { text: '帮我整理病历信息' }
    ])

    // 计算属性
    const messages = computed(() => chatStore.messages)
    const hasMessages = computed(() => chatStore.hasMessages)
    const canSend = computed(() => inputText.value.trim().length > 0 && !isLoading.value)

    // 生命周期
    onMounted(() => {
      chatStore.generateSessionId()
      scrollToBottom()
    })

    // 方法
    const onInput = (e) => {
      inputText.value = e.detail.value
    }

    const selectQuickInput = (text) => {
      inputText.value = text
      sendMessage()
    }

    const sendMessage = async () => {
      const message = inputText.value.trim()
      console.log('📤 发送消息:', message, '是否加载中:', isLoading.value)

      if (!message || isLoading.value) {
        console.log('❌ 消息为空或正在加载中，取消发送')
        return
      }

      try {
        console.log('✅ 开始发送消息流程')

        // 添加用户消息
        chatStore.addUserMessage(message)
        inputText.value = ''
        isLoading.value = true

        await nextTick()
        scrollToBottom()

        // 添加加载中的AI消息
        const loadingMessage = chatStore.addAIMessage('', 'text', { loading: true })

        console.log('📡 准备调用API:', { message })
        const response = await medicalChatApi.sendMessage({ message })
        console.log('📨 API响应:', response)

        if (response.success) {
          const { intent_recognition, agent_type, response: agentResponse } = response.data

          // 使用响应式更新方式
          const responseContent = getResponseContent(agentResponse)
          
          // 更新消息内容
          chatStore.updateAIMessage(loadingMessage.id, {
            loading: false,
            content: responseContent,
            intentResult: intent_recognition,
            agentType: agent_type
          })

          userStore.incrementChats()

          historyStore.addChatRecord(
            message,
            responseContent,
            agent_type
          )

          chatStore.saveSessionToLocal()
        } else {
          // 更新错误消息
          chatStore.updateAIMessage(loadingMessage.id, {
            loading: false,
            content: '抱歉，服务暂时不可用，请稍后重试。'
          })
        }

        await nextTick()
        scrollToBottom()

      } catch (error) {
        console.error('发送消息失败:', error)

        // 更新最后一条消息为错误状态
        if (chatStore.messages.length > 0) {
          const lastMessage = chatStore.messages[chatStore.messages.length - 1]
          if (lastMessage.loading) {
            chatStore.updateAIMessage(lastMessage.id, {
              loading: false,
              content: '网络连接失败，请检查网络后重试。'
            })
          }
        }

        handleApiError(error)
      } finally {
        isLoading.value = false
      }
    }

    const scrollToBottom = () => {
      setTimeout(() => {
        scrollTop.value = 99999
      }, 100)
    }

    const getResponseContent = (agentResponse) => {
      if (typeof agentResponse === 'string') {
        return agentResponse
      }

      if (agentResponse.reply) {
        return agentResponse.reply
      }

      if (agentResponse.triage_result) {
        return agentResponse.triage_result
      }

      if (agentResponse.diagnosis_result) {
        return agentResponse.diagnosis_result
      }

      if (agentResponse.case_result) {
        return agentResponse.case_result
      }

      return JSON.stringify(agentResponse, null, 2)
    }

    const getIntentText = (intent) => {
      const intentMap = {
        'triage': '智能分诊',
        'diagnosis': '症状自诊',
        'case_generation': '病例整理',
        'general_chat': '日常咨询'
      }
      return intentMap[intent] || intent
    }

    const toggleFunctionMenu = () => {
      showFunctionMenu.value = !showFunctionMenu.value
    }

    const clearChat = () => {
      uni.showModal({
        title: '清空对话',
        content: '确定要清空所有对话记录吗？',
        success: (res) => {
          if (res.confirm) {
            chatStore.clearMessages()
            uni.showToast({
              title: '已清空对话',
              icon: 'success'
            })
          }
        }
      })
    }

    const exportChat = () => {
      if (!hasMessages.value) {
        uni.showToast({
          title: '暂无对话记录',
          icon: 'none'
        })
        return
      }

      const content = messages.value.map(msg => 
        `${msg.role === 'user' ? '我' : 'AI'}: ${msg.content}`
      ).join('\n\n')

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

    return {
      inputText,
      scrollTop,
      showFunctionMenu,
      isLoading,
      quickButtons,
      messages,
      hasMessages,
      canSend,
      onInput,
      selectQuickInput,
      sendMessage,
      getIntentText,
      toggleFunctionMenu,
      clearChat,
      exportChat
    }
  }
}
</script>

<style lang="scss" scoped>
.chat-container {
  height: 100vh;
  background: #f8f9fa;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 页面标题 */
.page-header {
  text-align: center;
  padding: 30rpx 20rpx;
  background: #fff;
  border-bottom: 1rpx solid #f0f0f0;
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

/* 聊天消息区域 */
.chat-messages {
  flex: 1;
  padding: 20rpx;
  overflow: hidden;
}

.message-scroll {
  height: 100%;
  overflow-y: auto;
}

.message-item {
  margin-bottom: 30rpx;
  
  &.user {
    display: flex;
    justify-content: flex-end;
    align-items: flex-end;
  }
  
  &.ai {
    display: flex;
    justify-content: flex-start;
    align-items: flex-start;
  }
}

.user-message {
  display: flex;
  align-items: flex-end;
  gap: 15rpx;
}

.ai-message {
  display: flex;
  align-items: flex-start;
  gap: 15rpx;
}

.message-avatar {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  
  &.user-avatar {
    background: #1658FF;
    color: #fff;
  }
  
  &.ai-avatar {
    background: #28a745;
    color: #fff;
  }
}

.avatar-text {
  font-size: 24rpx;
  font-weight: bold;
}

.message-bubble {
  max-width: 70%;
  padding: 20rpx 25rpx;
  border-radius: 20rpx;
  position: relative;
  
  &.user-bubble {
    background: #1658FF;
    color: #fff;
    border-bottom-right-radius: 8rpx;
  }
  
  &.ai-bubble {
    background: #fff;
    color: #333;
    border: 1rpx solid #e9ecef;
    border-bottom-left-radius: 8rpx;
  }
}

.message-text {
  font-size: 30rpx;
  line-height: 1.5;
}

.loading-text {
  color: #999;
  font-style: italic;
}

.loading-dots {
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.intent-section {
  margin-bottom: 15rpx;
  padding: 10rpx 15rpx;
  background: #f8f9fa;
  border-radius: 10rpx;
  border-left: 4rpx solid #1658FF;
}

.intent-label {
  font-size: 24rpx;
  color: #666;
  margin-right: 10rpx;
}

.intent-value {
  font-size: 24rpx;
  color: #1658FF;
  font-weight: bold;
}

.agent-tag {
  margin-top: 15rpx;
  display: inline-block;
  padding: 8rpx 15rpx;
  background: #e3f2fd;
  border-radius: 15rpx;
}

.agent-text {
  font-size: 22rpx;
  color: #1976d2;
}

/* 欢迎区域 */
.welcome-section {
  flex: 1;
  padding: 40rpx 20rpx;
  overflow-y: auto;
}

.welcome-card {
  background: #fff;
  border-radius: 20rpx;
  padding: 40rpx;
  text-align: center;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.1);
}

.welcome-icon {
  font-size: 80rpx;
  display: block;
  margin-bottom: 20rpx;
}

.welcome-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 15rpx;
}

.welcome-desc {
  font-size: 28rpx;
  color: #666;
  line-height: 1.5;
  display: block;
}

.features-section {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.1);
}

.features-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 25rpx;
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 15rpx;
}

.feature-icon {
  font-size: 32rpx;
  width: 50rpx;
  text-align: center;
}

.feature-text {
  font-size: 28rpx;
  color: #666;
  flex: 1;
}

/* 快捷输入区域 */
.quick-input-section {
  padding: 20rpx;
  background: #fff;
  border-top: 1rpx solid #f0f0f0;
}

.section-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 20rpx;
}

.quick-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 15rpx;
}

.quick-btn {
  background: #f8f9fa;
  border: 1rpx solid #e9ecef;
  color: #666;
  font-size: 26rpx;
  padding: 15rpx 25rpx;
  border-radius: 25rpx;
  transition: all 0.2s ease;
  
  &:active {
    background: #e9ecef;
    transform: scale(0.98);
  }
}

/* 输入区域 */
.input-section {
  background: #fff;
  border-top: 1rpx solid #f0f0f0;
  padding: 20rpx;
  display: flex;
  align-items: flex-end;
  gap: 15rpx;
}

.input-container {
  flex: 1;
  position: relative;
}

.message-input {
  width: 100%;
  min-height: 80rpx;
  max-height: 200rpx;
  background: #f8f9fa;
  border: 1rpx solid #e9ecef;
  border-radius: 20rpx;
  padding: 20rpx 25rpx;
  font-size: 30rpx;
  color: #333;
  box-sizing: border-box;
  
  &:focus {
    border-color: #1658FF;
    background: #fff;
  }
}

.char-count {
  position: absolute;
  bottom: 10rpx;
  right: 20rpx;
  font-size: 22rpx;
  color: #999;
}

.send-container {
  flex-shrink: 0;
}

.send-btn {
  width: 120rpx;
  height: 80rpx;
  background: #e9ecef;
  color: #999;
  border: none;
  border-radius: 20rpx;
  font-size: 28rpx;
  transition: all 0.2s ease;
  
  &.active {
    background: #1658FF;
    color: #fff;
    box-shadow: 0 4rpx 15rpx rgba(22, 88, 255, 0.3);
  }
  
  &:disabled {
    opacity: 0.6;
  }
}

.send-text {
  font-size: 28rpx;
}

/* 功能菜单 */
.function-menu {
  position: fixed;
  top: 50%;
  right: 150rpx;
  transform: translateY(-50%);
  background: #fff;
  border-radius: 15rpx;
  box-shadow: 0 8rpx 30rpx rgba(0, 0, 0, 0.15);
  overflow: hidden;
  z-index: 1000;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 15rpx;
  padding: 20rpx 25rpx;
  border-bottom: 1rpx solid #f0f0f0;
  transition: background 0.2s ease;
  
  &:last-child {
    border-bottom: none;
  }
  
  &:active {
    background: #f8f9fa;
  }
}

.menu-icon {
  font-size: 32rpx;
}

.menu-text {
  font-size: 28rpx;
  color: #333;
}

.function-btn {
  position: fixed;
  top: 50%;
  right: 30rpx;
  transform: translateY(-50%);
  width: 100rpx;
  height: 100rpx;
  background: #1658FF;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 25rpx rgba(22, 88, 255, 0.3);
  z-index: 999;
}

.btn-icon {
  font-size: 40rpx;
  color: #fff;
}
</style>