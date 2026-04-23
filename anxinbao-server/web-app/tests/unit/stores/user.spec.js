/**
 * User Store 单元测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'

// 模拟 API
vi.mock('@api/index', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    refreshToken: vi.fn()
  },
  userApi: {
    updateProfile: vi.fn()
  }
}))

// 模拟 localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

describe('useUserStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue('')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('初始状态', () => {
    it('token 初始为空', () => {
      const store = useUserStore()
      expect(store.token).toBe('')
    })

    it('user 初始为 null', () => {
      const store = useUserStore()
      expect(store.user).toBeNull()
    })

    it('loading 初始为 false', () => {
      const store = useUserStore()
      expect(store.loading).toBe(false)
    })

    it('isLoggedIn 初始为 false', () => {
      const store = useUserStore()
      expect(store.isLoggedIn).toBe(false)
    })
  })

  describe('计算属性', () => {
    it('userRole 默认返回 elderly', () => {
      const store = useUserStore()
      expect(store.userRole).toBe('elderly')
    })

    it('userRole 返回用户角色', () => {
      const store = useUserStore()
      store.user = { role: 'family' }
      expect(store.userRole).toBe('family')
    })

    it('userName 返回用户名称', () => {
      const store = useUserStore()
      store.user = { name: '张三' }
      expect(store.userName).toBe('张三')
    })

    it('userName 无名称时返回手机号', () => {
      const store = useUserStore()
      store.user = { phone: '13800138000' }
      expect(store.userName).toBe('13800138000')
    })

    it('userName 无用户时返回默认值', () => {
      const store = useUserStore()
      expect(store.userName).toBe('用户')
    })

    it('userAvatar 返回用户头像', () => {
      const store = useUserStore()
      store.user = { avatar: '/avatar.jpg' }
      expect(store.userAvatar).toBe('/avatar.jpg')
    })

    it('userAvatar 无头像时返回默认值', () => {
      const store = useUserStore()
      expect(store.userAvatar).toBe('/default-avatar.png')
    })

    it('isLoggedIn 有 token 和 user 时为 true', () => {
      const store = useUserStore()
      store.token = 'test-token'
      store.user = { id: '1' }
      expect(store.isLoggedIn).toBe(true)
    })
  })

  describe('logout', () => {
    it('清除 token 和 user', () => {
      const store = useUserStore()
      store.token = 'test-token'
      store.user = { id: '1', name: '测试' }

      store.logout()

      expect(store.token).toBe('')
      expect(store.user).toBeNull()
    })

    it('清除 localStorage 中的 token', () => {
      const store = useUserStore()
      store.token = 'test-token'

      store.logout()

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token')
    })
  })
})
