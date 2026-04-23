/**
 * 工具函数单元测试
 */
import { describe, it, expect } from 'vitest'

// 日期格式化工具函数（模拟）
function formatDate(date, format = 'YYYY-MM-DD') {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

// 手机号格式化
function formatPhone(phone) {
  if (!phone || phone.length !== 11) return phone
  return phone.replace(/(\d{3})(\d{4})(\d{4})/, '$1 $2 $3')
}

// 手机号脱敏
function maskPhone(phone) {
  if (!phone || phone.length !== 11) return phone
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

// 金额格式化
function formatMoney(amount, decimal = 2) {
  return Number(amount).toFixed(decimal).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 文件大小格式化
function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 验证手机号
function isValidPhone(phone) {
  return /^1[3-9]\d{9}$/.test(phone)
}

// 验证邮箱
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

// 生成随机字符串
function generateRandomString(length = 8) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

describe('日期格式化', () => {
  it('默认格式 YYYY-MM-DD', () => {
    const date = new Date('2024-01-15')
    expect(formatDate(date)).toBe('2024-01-15')
  })

  it('自定义格式 YYYY/MM/DD', () => {
    const date = new Date('2024-01-15')
    expect(formatDate(date, 'YYYY/MM/DD')).toBe('2024/01/15')
  })

  it('包含时间的格式', () => {
    const date = new Date('2024-01-15T10:30:45')
    expect(formatDate(date, 'YYYY-MM-DD HH:mm:ss')).toBe('2024-01-15 10:30:45')
  })
})

describe('手机号格式化', () => {
  it('格式化11位手机号', () => {
    expect(formatPhone('13800138000')).toBe('138 0013 8000')
  })

  it('非11位手机号返回原值', () => {
    expect(formatPhone('1234567')).toBe('1234567')
  })

  it('空值返回空值', () => {
    expect(formatPhone('')).toBe('')
  })
})

describe('手机号脱敏', () => {
  it('脱敏11位手机号', () => {
    expect(maskPhone('13800138000')).toBe('138****8000')
  })

  it('非11位手机号返回原值', () => {
    expect(maskPhone('1234567')).toBe('1234567')
  })
})

describe('金额格式化', () => {
  it('格式化整数金额', () => {
    expect(formatMoney(1000)).toBe('1,000.00')
  })

  it('格式化小数金额', () => {
    expect(formatMoney(1234.5)).toBe('1,234.50')
  })

  it('大数金额格式化', () => {
    expect(formatMoney(1234567.89)).toBe('1,234,567.89')
  })

  it('指定小数位数', () => {
    expect(formatMoney(1234.5678, 3)).toBe('1,234.568')
  })
})

describe('文件大小格式化', () => {
  it('格式化字节', () => {
    expect(formatFileSize(500)).toBe('500 B')
  })

  it('格式化KB', () => {
    expect(formatFileSize(1024)).toBe('1 KB')
  })

  it('格式化MB', () => {
    expect(formatFileSize(1048576)).toBe('1 MB')
  })

  it('格式化GB', () => {
    expect(formatFileSize(1073741824)).toBe('1 GB')
  })

  it('零字节', () => {
    expect(formatFileSize(0)).toBe('0 B')
  })
})

describe('手机号验证', () => {
  it('有效手机号', () => {
    expect(isValidPhone('13800138000')).toBe(true)
    expect(isValidPhone('15912345678')).toBe(true)
    expect(isValidPhone('18612345678')).toBe(true)
  })

  it('无效手机号', () => {
    expect(isValidPhone('12345678901')).toBe(false)
    expect(isValidPhone('1380013800')).toBe(false)
    expect(isValidPhone('138001380001')).toBe(false)
    expect(isValidPhone('abc12345678')).toBe(false)
  })
})

describe('邮箱验证', () => {
  it('有效邮箱', () => {
    expect(isValidEmail('test@example.com')).toBe(true)
    expect(isValidEmail('user.name@domain.org')).toBe(true)
  })

  it('无效邮箱', () => {
    expect(isValidEmail('test')).toBe(false)
    expect(isValidEmail('test@')).toBe(false)
    expect(isValidEmail('@example.com')).toBe(false)
  })
})

describe('随机字符串生成', () => {
  it('生成指定长度', () => {
    expect(generateRandomString(8).length).toBe(8)
    expect(generateRandomString(16).length).toBe(16)
  })

  it('生成不同的字符串', () => {
    const str1 = generateRandomString(10)
    const str2 = generateRandomString(10)
    expect(str1).not.toBe(str2)
  })
})
