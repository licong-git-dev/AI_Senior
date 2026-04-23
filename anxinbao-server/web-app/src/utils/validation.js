/**
 * 安心宝 - 表单验证工具
 * 适老化设计，提供清晰的错误提示
 */

// 验证规则
export const rules = {
  // 必填
  required: (message = '此项为必填项') => ({
    validate: (value) => {
      if (value === null || value === undefined) return false
      if (typeof value === 'string') return value.trim().length > 0
      if (Array.isArray(value)) return value.length > 0
      return true
    },
    message
  }),

  // 手机号
  phone: (message = '请输入正确的手机号码') => ({
    validate: (value) => {
      if (!value) return true
      return /^1[3-9]\d{9}$/.test(value)
    },
    message
  }),

  // 邮箱
  email: (message = '请输入正确的邮箱地址') => ({
    validate: (value) => {
      if (!value) return true
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
    },
    message
  }),

  // 最小长度
  minLength: (min, message) => ({
    validate: (value) => {
      if (!value) return true
      return String(value).length >= min
    },
    message: message || `至少需要输入${min}个字符`
  }),

  // 最大长度
  maxLength: (max, message) => ({
    validate: (value) => {
      if (!value) return true
      return String(value).length <= max
    },
    message: message || `最多只能输入${max}个字符`
  }),

  // 密码强度
  password: (message = '密码至少6位，包含字母和数字') => ({
    validate: (value) => {
      if (!value) return true
      return /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{6,}$/.test(value)
    },
    message
  }),

  // 确认密码
  confirmPassword: (passwordField, message = '两次输入的密码不一致') => ({
    validate: (value, formData) => {
      if (!value) return true
      return value === formData[passwordField]
    },
    message
  }),

  // 数字范围
  range: (min, max, message) => ({
    validate: (value) => {
      if (!value && value !== 0) return true
      const num = Number(value)
      return num >= min && num <= max
    },
    message: message || `数值需在${min}到${max}之间`
  }),

  // 身份证号
  idCard: (message = '请输入正确的身份证号码') => ({
    validate: (value) => {
      if (!value) return true
      return /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/.test(value)
    },
    message
  }),

  // 中文姓名
  chineseName: (message = '请输入正确的中文姓名') => ({
    validate: (value) => {
      if (!value) return true
      return /^[\u4e00-\u9fa5]{2,10}$/.test(value)
    },
    message
  }),

  // 年龄
  age: (min = 0, max = 150, message) => ({
    validate: (value) => {
      if (!value && value !== 0) return true
      const age = Number(value)
      return Number.isInteger(age) && age >= min && age <= max
    },
    message: message || `年龄需在${min}到${max}岁之间`
  }),

  // 血压格式
  bloodPressure: (message = '请输入正确的血压值，如：120/80') => ({
    validate: (value) => {
      if (!value) return true
      const match = value.match(/^(\d{2,3})\/(\d{2,3})$/)
      if (!match) return false
      const systolic = parseInt(match[1])
      const diastolic = parseInt(match[2])
      return systolic >= 60 && systolic <= 250 && diastolic >= 40 && diastolic <= 150
    },
    message
  }),

  // 自定义正则
  pattern: (regex, message = '格式不正确') => ({
    validate: (value) => {
      if (!value) return true
      return regex.test(value)
    },
    message
  }),

  // 自定义验证函数
  custom: (validateFn, message = '验证失败') => ({
    validate: validateFn,
    message
  })
}

/**
 * 验证单个字段
 * @param {any} value - 字段值
 * @param {Array} fieldRules - 验证规则数组
 * @param {Object} formData - 完整表单数据（用于跨字段验证）
 * @returns {string|null} - 错误信息或null
 */
export function validateField(value, fieldRules, formData = {}) {
  for (const rule of fieldRules) {
    if (!rule.validate(value, formData)) {
      return rule.message
    }
  }
  return null
}

/**
 * 验证整个表单
 * @param {Object} formData - 表单数据
 * @param {Object} schema - 验证schema { fieldName: [rules] }
 * @returns {Object} - { valid: boolean, errors: { fieldName: errorMessage } }
 */
export function validateForm(formData, schema) {
  const errors = {}
  let valid = true

  for (const [field, fieldRules] of Object.entries(schema)) {
    const error = validateField(formData[field], fieldRules, formData)
    if (error) {
      errors[field] = error
      valid = false
    }
  }

  return { valid, errors }
}

/**
 * 创建响应式表单验证器
 * @param {Object} initialData - 初始表单数据
 * @param {Object} schema - 验证schema
 * @returns {Object} - 响应式表单对象
 */
export function useFormValidation(initialData, schema) {
  const formData = { ...initialData }
  const errors = {}
  const touched = {}

  // 初始化错误和触摸状态
  for (const field of Object.keys(schema)) {
    errors[field] = null
    touched[field] = false
  }

  return {
    formData,
    errors,
    touched,

    // 设置字段值
    setField(field, value) {
      formData[field] = value
      if (touched[field]) {
        this.validateField(field)
      }
    },

    // 标记字段已触摸
    touch(field) {
      touched[field] = true
      this.validateField(field)
    },

    // 验证单个字段
    validateField(field) {
      if (schema[field]) {
        errors[field] = validateField(formData[field], schema[field], formData)
      }
      return !errors[field]
    },

    // 验证整个表单
    validate() {
      const result = validateForm(formData, schema)
      Object.assign(errors, result.errors)
      // 标记所有字段已触摸
      for (const field of Object.keys(schema)) {
        touched[field] = true
      }
      return result.valid
    },

    // 重置表单
    reset() {
      Object.assign(formData, initialData)
      for (const field of Object.keys(schema)) {
        errors[field] = null
        touched[field] = false
      }
    },

    // 获取第一个错误
    getFirstError() {
      for (const error of Object.values(errors)) {
        if (error) return error
      }
      return null
    }
  }
}

export default {
  rules,
  validateField,
  validateForm,
  useFormValidation
}
