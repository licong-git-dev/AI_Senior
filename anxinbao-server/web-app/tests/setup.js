/**
 * Vitest 测试设置文件
 */
import { config } from '@vue/test-utils'
import { vi } from 'vitest'

// 全局模拟 Vue Router
config.global.mocks = {
  $router: {
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn()
  },
  $route: {
    path: '/',
    params: {},
    query: {}
  }
}

// 全局模拟组件
config.global.stubs = {
  RouterLink: {
    template: '<a><slot /></a>'
  },
  RouterView: {
    template: '<div><slot /></div>'
  }
}

// 模拟 window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// 模拟 ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// 模拟 IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))
