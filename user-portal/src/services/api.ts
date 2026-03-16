import axios from 'axios'
import { useAuthStore } from '../store/authStore'

// 创建 axios 实例
const api = axios.create({
  baseURL: (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config
    
    // 处理401错误
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      // 清除认证状态并跳转登录页
      useAuthStore.getState().clearAuth()
      window.location.href = '/login'
    }
    
    return Promise.reject(error)
  }
)

// 认证相关API
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  
  register: (data: { username: string; email: string; password: string; email_subscribed?: boolean }) =>
    api.post('/auth/register', data),
  
  logout: () => api.post('/auth/logout'),
  
  getMe: () => api.get('/auth/me'),
  
  subscribeEmail: (subscribe: boolean = true) =>
    api.post('/auth/subscribe-email', null, { params: { subscribe } }),
}

// 外贸数据API
export const tradeDataApi = {
  getList: (params?: any) => api.get('/trade-data', { params }),
  
  getById: (id: number) => api.get(`/trade-data/${id}`),
  
  create: (data: any) => api.post('/trade-data', data),
  
  update: (id: number, data: any) => api.put(`/trade-data/${id}`, data),
  
  delete: (id: number) => api.delete(`/trade-data/${id}`),
  
  confirm: (id: number) => api.post(`/trade-data/${id}/confirm`),
  
  getStatistics: (year?: number) => api.get('/trade-data/statistics/overview', { params: { year } }),
  
  getStatisticsByYear: () => api.get('/trade-data/statistics/by-year'),
}

// 爬虫API
export const crawlerApi = {
  getScripts: () => api.get('/crawler/scripts'),
  
  getScript: (id: number) => api.get(`/crawler/scripts/${id}`),
  
  createScript: (data: any) => api.post('/crawler/scripts', data),
  
  updateScript: (id: number, data: any) => api.put(`/crawler/scripts/${id}`, data),
  
  deleteScript: (id: number) => api.delete(`/crawler/scripts/${id}`),
  
  getTasks: (params?: any) => api.get('/crawler/tasks', { params }),
  
  getTask: (id: number) => api.get(`/crawler/tasks/${id}`),
  
  trigger: (scriptId: number, params?: any) =>
    api.post('/crawler/trigger', { script_id: scriptId, params }),
  
  cancelTask: (id: number) => api.post(`/crawler/tasks/${id}/cancel`),
}

// 系统API
export const systemApi = {
  getHealth: () => api.get('/system/health'),
  
  getStats: () => api.get('/system/stats'),
  
  getInfo: () => api.get('/system/info'),
}

export default api
