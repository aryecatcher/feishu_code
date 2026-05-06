import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { ApiClient } from './api/generated'
import './style.css'

// 全局初始化并导出 API 客户端实例
export const apiClient = new ApiClient({
  BASE: import.meta.env.VITE_API_BASE_URL || 'http://60.204.174.188:8000',
  HEADERS: {
    'Content-Type': 'application/json'
  }
})

createApp(App).use(router).mount('#app')
