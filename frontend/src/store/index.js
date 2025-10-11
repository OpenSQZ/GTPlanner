import { createPinia } from 'pinia'
import { useChatStore } from './chat'
import { useHistoryStore } from './history'
import { useUserStore } from './user'

export { useChatStore, useHistoryStore, useUserStore }

export default createPinia()
