/**
 * Input 组件单元测试
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Input from '@/components/ui/Input.vue'

describe('Input', () => {
  it('渲染默认输入框', () => {
    const wrapper = mount(Input, {
      props: { modelValue: '' }
    })
    expect(wrapper.find('input').exists()).toBe(true)
  })

  it('显示标签', () => {
    const wrapper = mount(Input, {
      props: {
        modelValue: '',
        label: '用户名'
      }
    })
    expect(wrapper.find('label').text()).toBe('用户名')
  })

  it('显示placeholder', () => {
    const wrapper = mount(Input, {
      props: {
        modelValue: '',
        placeholder: '请输入用户名'
      }
    })
    expect(wrapper.find('input').attributes('placeholder')).toBe('请输入用户名')
  })

  it('禁用状态', () => {
    const wrapper = mount(Input, {
      props: {
        modelValue: '',
        disabled: true
      }
    })
    expect(wrapper.find('input').attributes('disabled')).toBeDefined()
  })

  it('只读状态', () => {
    const wrapper = mount(Input, {
      props: {
        modelValue: '',
        readonly: true
      }
    })
    expect(wrapper.find('input').attributes('readonly')).toBeDefined()
  })

  it('显示错误信息', () => {
    const wrapper = mount(Input, {
      props: {
        modelValue: '',
        error: '用户名不能为空'
      }
    })
    expect(wrapper.text()).toContain('用户名不能为空')
  })

  it('显示帮助文本', () => {
    const wrapper = mount(Input, {
      props: {
        modelValue: '',
        hint: '请输入6-20个字符'
      }
    })
    expect(wrapper.text()).toContain('请输入6-20个字符')
  })

  it('输入时触发更新事件', async () => {
    const wrapper = mount(Input, {
      props: { modelValue: '' }
    })

    const input = wrapper.find('input')
    await input.setValue('测试内容')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['测试内容'])
  })

  it('支持不同类型', () => {
    const types = ['text', 'password', 'email', 'number', 'tel']

    types.forEach(type => {
      const wrapper = mount(Input, {
        props: { modelValue: '', type }
      })
      expect(wrapper.find('input').attributes('type')).toBe(type)
    })
  })
})
