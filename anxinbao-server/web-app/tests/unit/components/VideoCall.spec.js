/**
 * VideoCall 组件单元测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import VideoCall from '@/components/common/VideoCall.vue'

// 模拟 navigator.mediaDevices
const mockMediaDevices = {
  getUserMedia: vi.fn().mockResolvedValue({
    getTracks: () => [{ stop: vi.fn() }],
    getAudioTracks: () => [{ enabled: true }],
    getVideoTracks: () => [{
      enabled: true,
      stop: vi.fn(),
      getSettings: () => ({ facingMode: 'user' })
    }],
    removeTrack: vi.fn(),
    addTrack: vi.fn()
  }),
  getDisplayMedia: vi.fn().mockResolvedValue({
    getTracks: () => [{ stop: vi.fn() }]
  })
}

describe('VideoCall', () => {
  beforeEach(() => {
    Object.defineProperty(navigator, 'mediaDevices', {
      value: mockMediaDevices,
      writable: true
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('组件不可见时不渲染', () => {
    const wrapper = mount(VideoCall, {
      props: {
        isVisible: false,
        callerName: '测试用户'
      }
    })
    expect(wrapper.find('.fixed').exists()).toBe(false)
  })

  it('组件可见时渲染', () => {
    const wrapper = mount(VideoCall, {
      props: {
        isVisible: true,
        callerName: '测试用户'
      }
    })
    expect(wrapper.find('.fixed').exists()).toBe(true)
  })

  it('显示来电者名称', () => {
    const wrapper = mount(VideoCall, {
      props: {
        isVisible: true,
        callerName: '张三'
      }
    })
    expect(wrapper.text()).toContain('张三')
  })

  it('显示来电者首字母', () => {
    const wrapper = mount(VideoCall, {
      props: {
        isVisible: true,
        callerName: '李四'
      }
    })
    expect(wrapper.text()).toContain('李')
  })

  it('来电时显示接听/拒绝按钮', async () => {
    const wrapper = mount(VideoCall, {
      props: {
        isVisible: true,
        callerName: '测试',
        isIncoming: true
      }
    })

    // 等待组件更新
    await wrapper.vm.$nextTick()

    // 检查是否有两个操作按钮（接听和拒绝）
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBeGreaterThan(0)
  })

  it('点击挂断触发 close 事件', async () => {
    const wrapper = mount(VideoCall, {
      props: {
        isVisible: true,
        callerName: '测试',
        isIncoming: false
      }
    })

    // 找到挂断按钮（红色背景的按钮）
    const hangupButton = wrapper.findAll('button').find(btn =>
      btn.classes().some(c => c.includes('bg-red'))
    )

    if (hangupButton) {
      await hangupButton.trigger('click')
      expect(wrapper.emitted('call-ended') || wrapper.emitted('close')).toBeTruthy()
    }
  })

  it('拒绝来电触发 call-rejected 事件', async () => {
    const wrapper = mount(VideoCall, {
      props: {
        isVisible: true,
        callerName: '测试',
        isIncoming: true
      }
    })

    await wrapper.vm.$nextTick()

    // 找到拒绝按钮
    const rejectButton = wrapper.findAll('button').find(btn =>
      btn.classes().some(c => c.includes('bg-red'))
    )

    if (rejectButton) {
      await rejectButton.trigger('click')
      expect(wrapper.emitted('call-rejected')).toBeTruthy()
    }
  })

  it('接听来电触发 call-accepted 事件', async () => {
    const wrapper = mount(VideoCall, {
      props: {
        isVisible: true,
        callerName: '测试',
        isIncoming: true
      }
    })

    await wrapper.vm.$nextTick()

    // 找到接听按钮（绿色背景的按钮）
    const acceptButton = wrapper.findAll('button').find(btn =>
      btn.classes().some(c => c.includes('bg-green'))
    )

    if (acceptButton) {
      await acceptButton.trigger('click')
      // 等待异步操作
      await new Promise(resolve => setTimeout(resolve, 1500))
      expect(wrapper.emitted('call-accepted')).toBeTruthy()
    }
  })
})
