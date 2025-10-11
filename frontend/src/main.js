import { createSSRApp } from 'vue'
import App from './App.vue'
import { createPinia } from 'pinia'
import uviewPlus from 'uview-plus'
// 引入uview-plus样式
import 'uview-plus/index.scss'
// 引入医疗主题CSS变量
import './styles/medical-theme.css'

export function createApp() {
  const app = createSSRApp(App)
  const pinia = createPinia()
  
  app.use(pinia)
  app.use(uviewPlus)
  
  return {
    app
  }
}
