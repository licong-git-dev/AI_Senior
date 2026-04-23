/**
 * 安心宝 - API客户端
 */
import axios from 'axios'
import { useUserStore } from '@stores/user'
import router from '@/router'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()

    // 添加认证Token
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
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
    return response.data
  },
  (error) => {
    const { response } = error

    if (response) {
      switch (response.status) {
        case 401:
          // Token过期或无效
          const userStore = useUserStore()
          userStore.logout()
          router.push({ name: 'Login' })
          break
        case 403:
          console.error('无权限访问')
          break
        case 404:
          console.error('资源不存在')
          break
        case 500:
          console.error('服务器错误')
          break
      }
    }

    return Promise.reject(error)
  }
)

export default api

// ==================== 认证API ====================

export const authApi = {
  // 登录
  login(phone, password, captcha = null) {
    return api.post('/auth/login', { phone, password, captcha })
  },

  // 注册
  register(data) {
    return api.post('/auth/register', data)
  },

  // 发送验证码
  sendCode(phone) {
    return api.post('/auth/send-code', { phone })
  },

  // 刷新Token
  refreshToken() {
    return api.post('/auth/refresh')
  },

  // 获取当前用户信息
  getCurrentUser() {
    return api.get('/auth/me')
  },

  // 登出
  logout() {
    return api.post('/auth/logout')
  }
}

// ==================== 用户API ====================

export const userApi = {
  // 获取用户信息
  getProfile() {
    return api.get('/users/profile')
  },

  // 更新用户信息
  updateProfile(data) {
    return api.put('/users/profile', data)
  },

  // 修改密码
  changePassword(oldPassword, newPassword) {
    return api.post('/users/change-password', { old_password: oldPassword, new_password: newPassword })
  },

  // 上传头像
  uploadAvatar(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/files/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

// ==================== 健康API ====================

export const healthApi = {
  // 获取健康仪表板
  getDashboard() {
    return api.get('/health/dashboard')
  },

  // 记录生命体征
  recordVitalSigns(data) {
    return api.post('/health/vital-signs', data)
  },

  // 获取生命体征历史
  getVitalSignsHistory(type, days = 7) {
    return api.get('/health/vital-signs/history', { params: { type, days } })
  },

  // 获取健康趋势
  getHealthTrends(days = 30) {
    return api.get('/health/trends', { params: { days } })
  },

  // 获取健康建议
  getHealthAdvice() {
    return api.get('/health/advice')
  }
}

// ==================== 用药API ====================

export const medicationApi = {
  // 获取用药计划
  getPlans() {
    return api.get('/medication/plans')
  },

  // 添加用药计划
  addPlan(data) {
    return api.post('/medication/plans', data)
  },

  // 记录服药
  recordIntake(planId, taken = true) {
    return api.post(`/medication/plans/${planId}/intake`, { taken })
  },

  // 获取今日服药情况
  getTodaySchedule() {
    return api.get('/medication/today')
  },

  // 获取用药统计
  getStatistics(days = 30) {
    return api.get('/medication/statistics', { params: { days } })
  }
}

// ==================== 紧急求助API ====================

export const emergencyApi = {
  // 触发SOS
  triggerSOS(location = null, type = 'general') {
    return api.post('/emergency/sos', { location, emergency_type: type })
  },

  // 取消SOS
  cancelSOS(alertId) {
    return api.post(`/emergency/sos/${alertId}/cancel`)
  },

  // 获取紧急联系人
  getContacts() {
    return api.get('/emergency/contacts')
  },

  // 添加紧急联系人
  addContact(data) {
    return api.post('/emergency/contacts', data)
  },

  // 删除紧急联系人
  deleteContact(contactId) {
    return api.delete(`/emergency/contacts/${contactId}`)
  }
}

// ==================== 聊天API ====================

export const chatApi = {
  // 发送消息
  sendMessage(message, context = null) {
    return api.post('/chat/message', { message, context })
  },

  // 获取聊天历史
  getHistory(limit = 50) {
    return api.get('/chat/history', { params: { limit } })
  },

  // 语音转文字
  speechToText(audioBlob) {
    const formData = new FormData()
    formData.append('audio', audioBlob)
    return api.post('/voice/stt', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 文字转语音
  textToSpeech(text) {
    return api.post('/voice/tts', { text }, { responseType: 'blob' })
  }
}

// ==================== 家属API ====================

export const familyApi = {
  // 获取绑定的老人列表
  getBoundElderly() {
    return api.get('/family/elderly')
  },

  // 获取老人健康概览
  getElderlyOverview(elderlyId) {
    return api.get(`/family/elderly/${elderlyId}/overview`)
  },

  // 获取老人位置
  getElderlyLocation(elderlyId) {
    return api.get(`/family/elderly/${elderlyId}/location`)
  },

  // 获取健康报告
  getHealthReport(elderlyId, days = 7) {
    return api.get(`/family/elderly/${elderlyId}/health-report`, { params: { days } })
  },

  // 发送关怀消息
  sendCareMessage(elderlyId, message) {
    return api.post(`/family/elderly/${elderlyId}/message`, { message })
  },

  // 设置提醒
  setReminder(elderlyId, data) {
    return api.post(`/family/elderly/${elderlyId}/reminder`, data)
  }
}

// ==================== 社区API ====================

export const communityApi = {
  // 获取活动列表
  getActivities(type = null) {
    return api.get('/community/activities', { params: { activity_type: type } })
  },

  // 报名活动
  registerActivity(activityId) {
    return api.post('/community/activities/register', { activity_id: activityId })
  },

  // 获取邻里帖子
  getNeighborPosts(type = null, limit = 50) {
    return api.get('/community/neighbor/posts', { params: { post_type: type, limit } })
  },

  // 发布帖子
  createPost(data) {
    return api.post('/community/neighbor/posts', data)
  }
}

// ==================== 消息通知API ====================

export const messageApi = {
  // 获取消息列表
  getMessages(type = null, status = null) {
    return api.get('/messages', { params: { message_type: type, status } })
  },

  // 标记已读
  markAsRead(messageId) {
    return api.post(`/messages/${messageId}/read`)
  },

  // 获取未读数量
  getUnreadCount() {
    return api.get('/messages/unread-count')
  }
}
