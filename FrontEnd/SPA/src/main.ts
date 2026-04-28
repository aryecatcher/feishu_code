import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { ApiClient } from './api/generated'
import './style.css'

// 全局初始化并导出 API 客户端实例
export const apiClient = new ApiClient({
  BASE: import.meta.env.VITE_API_BASE_URL || 'https://127.0.0.1:4523/m1/8175900-7935055-default',
  HEADERS: {
    'Content-Type': 'application/json'
  }
})

createApp(App).use(router).mount('#app')
