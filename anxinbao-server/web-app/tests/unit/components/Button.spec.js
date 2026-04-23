/**
 * Button 组件单元测试
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Button from '@/components/ui/Button.vue'

describe('Button', () => {
  it('渲染默认按钮', () => {
    const wrapper = mount(Button, {
      slots: {
        default: '点击我'
      }
    })
    expect(wrapper.text()).toBe('点击我')
    expect(wrapper.classes()).toContain('btn')
  })

  it('渲染不同变体', () => {
    const variants = ['primary', 'secondary', 'danger', 'outline', 'ghost']

    variants.forEach(variant => {
      const wrapper = mount(Button, {
        props: { variant },
        slots: { default: '按钮' }
      })
      expect(wrapper.classes()).toContain('btn')
    })
  })

  it('渲染不同尺寸', () => {
    const sizes = ['sm', 'md', 'lg', 'xl']

    sizes.forEach(size => {
      const wrapper = mount(Button, {
        props: { size },
        slots: { default: '按钮' }
      })
      expect(wrapper.classes()).toContain('btn')
    })
  })

  it('block 属性使按钮全宽', () => {
    const wrapper = mount(Button, {
      props: { block: true },
      slots: { default: '全宽按钮' }
    })
    expect(wrapper.classes()).toContain('w-full')
  })

  it('禁用状态不触发点击事件', async () => {
    const handleClick = vi.fn()
    const wrapper = mount(Button, {
      props: { disabled: true },
      slots: { default: '禁用按钮' },
      attrs: { onClick: handleClick }
    })

    await wrapper.trigger('click')
    expect(handleClick).not.toHaveBeenCalled()
    expect(wrapper.attributes('disabled')).toBeDefined()
  })

  it('加载状态显示加载动画', () => {
    const wrapper = mount(Button, {
      props: { loading: true },
      slots: { default: '加载中' }
    })

    expect(wrapper.find('.loading-spinner').exists()).toBe(true)
    expect(wrapper.attributes('disabled')).toBeDefined()
  })

  it('点击事件正常触发', async () => {
    const wrapper = mount(Button, {
      slots: { default: '点击' }
    })

    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('加载状态下不触发点击事件', async () => {
    const wrapper = mount(Button, {
      props: { loading: true },
      slots: { default: '加载中' }
    })

    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeFalsy()
  })
})
