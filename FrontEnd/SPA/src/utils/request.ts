import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api', // 后端API地址
  timeout: 30000,
})

// 请求拦截器：统一添加token等请求头
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一处理错误、格式化返回
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('请求错误：', error.response?.data?.message || error.message)
    // 可在这里统一处理401跳转登录、全局错误提示等
    return Promise.reject(error)
  }
)

export default request