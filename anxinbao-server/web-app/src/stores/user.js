/**
 * 安心宝 - 用户状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, userApi } from '@api/index'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)
  const loading = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!user.value)

  const userRole = computed(() => user.value?.role || 'elderly')

  const userName = computed(() => user.value?.name || user.value?.phone || '用户')

  const userAvatar = computed(() => user.value?.avatar || '/default-avatar.png')

  // 操作

  /**
   * 检查认证状态
   */
  async function checkAuth() {
    if (!token.value) {
      return false
    }

    try {
      loading.value = true
      const response = await authApi.getCurrentUser()
      user.value = response.user || response
      return true
    } catch (error) {
      // Token无效，清除
      logout()
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 登录
   */
  async function login(phone, password, captcha = null) {
    loading.value = true

    try {
      const response = await authApi.login(phone, password, captcha)

      token.value = response.access_token
      user.value = response.user

      // 持久化
      localStorage.setItem('token', token.value)

      return { success: true, user: user.value }
    } catch (error) {
      const message = error.response?.data?.detail || '登录失败'
      return { success: false, message }
    } finally {
      loading.value = false
    }
  }

  /**
   * 注册
   */
  async function register(data) {
    loading.value = true

    try {
      const response = await authApi.register(data)

      if (response.access_token) {
        token.value = response.access_token
        user.value = response.user
        localStorage.setItem('token', token.value)
      }

      return { success: true, user: response.user }
    } catch (error) {
      const message = error.response?.data?.detail || '注册失败'
      return { success: false, message }
    } finally {
      loading.value = false
    }
  }

  /**
   * 登出
   */
  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')

    // 尝试通知服务端
    authApi.logout().catch(() => {})
  }

  /**
   * 更新用户信息
   */
  async function updateProfile(data) {
    try {
      const response = await userApi.updateProfile(data)
      user.value = { ...user.value, ...response }
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || '更新失败'
      return { success: false, message }
    }
  }

  /**
   * 刷新Token
   */
  async function refreshToken() {
    try {
      const response = await authApi.refreshToken()
      token.value = response.access_token
      localStorage.setItem('token', token.value)
      return true
    } catch (error) {
      logout()
      return false
    }
  }

  return {
    // 状态
    token,
    user,
    loading,

    // 计算属性
    isLoggedIn,
    userRole,
    userName,
    userAvatar,

    // 操作
    checkAuth,
    login,
    register,
    logout,
    updateProfile,
    refreshToken
  }
})
