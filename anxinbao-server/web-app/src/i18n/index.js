/**
 * 安心宝国际化配置
 * 支持中文简体、中文繁体、英文
 */

import { createI18n } from 'vue-i18n'

// 中文简体
const zhCN = {
  common: {
    confirm: '确定',
    cancel: '取消',
    save: '保存',
    delete: '删除',
    edit: '编辑',
    add: '添加',
    search: '搜索',
    reset: '重置',
    loading: '加载中...',
    noData: '暂无数据',
    success: '操作成功',
    failed: '操作失败',
    warning: '警告',
    info: '提示'
  },
  auth: {
    login: '登录',
    logout: '退出登录',
    register: '注册',
    phone: '手机号码',
    password: '密码',
    confirmPassword: '确认密码',
    verifyCode: '验证码',
    getCode: '获取验证码',
    resendCode: '{seconds}秒后重发',
    forgotPassword: '忘记密码？',
    hasAccount: '已有账号？',
    noAccount: '没有账号？',
    loginNow: '立即登录',
    registerNow: '立即注册',
    agreeTerms: '我已阅读并同意',
    userAgreement: '用户协议',
    privacyPolicy: '隐私政策',
    and: '和'
  },
  role: {
    elderly: '老人',
    family: '家属',
    admin: '管理员'
  },
  nav: {
    home: '首页',
    health: '健康',
    emergency: '紧急求助',
    medication: '用药',
    chat: '陪聊',
    profile: '我的',
    dashboard: '仪表盘',
    monitor: '监护',
    alerts: '告警',
    messages: '消息',
    settings: '设置',
    users: '用户',
    devices: '设备',
    reports: '报表'
  },
  health: {
    title: '健康数据',
    bloodPressure: '血压',
    heartRate: '心率',
    bloodSugar: '血糖',
    weight: '体重',
    temperature: '体温',
    systolic: '收缩压',
    diastolic: '舒张压',
    normal: '正常',
    abnormal: '异常',
    high: '偏高',
    low: '偏低',
    unit: {
      mmHg: 'mmHg',
      bpm: '次/分',
      mmol: 'mmol/L',
      kg: 'kg',
      celsius: '°C'
    },
    history: '历史记录',
    trend: '趋势',
    average: '平均值',
    normalRange: '正常范围',
    measureTime: '测量时间',
    measureNow: '立即测量',
    syncDevice: '同步设备数据'
  },
  emergency: {
    title: '紧急求助',
    sos: 'SOS紧急呼叫',
    sosDesc: '按住3秒发起紧急求助',
    contacts: '紧急联系人',
    addContact: '添加联系人',
    callNow: '立即呼叫',
    location: '当前位置',
    history: '求助记录',
    status: {
      pending: '待处理',
      handling: '处理中',
      resolved: '已解决',
      cancelled: '已取消'
    }
  },
  medication: {
    title: '用药管理',
    reminder: '用药提醒',
    addMedication: '添加药物',
    name: '药物名称',
    dosage: '剂量',
    frequency: '频率',
    time: '服药时间',
    notes: '备注',
    taken: '已服用',
    missed: '漏服',
    upcoming: '即将服药',
    schedule: '今日安排'
  },
  device: {
    title: '设备管理',
    add: '添加设备',
    bind: '绑定设备',
    unbind: '解绑设备',
    status: {
      online: '在线',
      offline: '离线'
    },
    battery: '电量',
    lastSync: '最后同步',
    type: {
      watch: '智能手表',
      bp_monitor: '血压仪',
      glucose_meter: '血糖仪',
      scale: '体重秤',
      thermometer: '体温计'
    }
  },
  alert: {
    title: '告警通知',
    type: {
      health: '健康告警',
      device: '设备告警',
      medication: '用药告警',
      sos: '紧急求助'
    },
    level: {
      low: '低',
      medium: '中',
      high: '高',
      critical: '紧急'
    },
    handle: '处理',
    handled: '已处理',
    ignore: '忽略'
  },
  settings: {
    title: '设置',
    account: '账号设置',
    notification: '通知设置',
    privacy: '隐私设置',
    language: '语言',
    about: '关于我们',
    version: '版本',
    feedback: '意见反馈',
    help: '帮助中心'
  },
  validation: {
    required: '此项为必填',
    phoneInvalid: '请输入正确的手机号',
    codeInvalid: '验证码格式不正确',
    passwordMin: '密码至少{min}位',
    passwordMax: '密码最多{max}位',
    passwordMismatch: '两次输入的密码不一致',
    nameInvalid: '姓名格式不正确'
  }
}

// 中文繁体
const zhTW = {
  common: {
    confirm: '確定',
    cancel: '取消',
    save: '儲存',
    delete: '刪除',
    edit: '編輯',
    add: '新增',
    search: '搜尋',
    reset: '重置',
    loading: '載入中...',
    noData: '暫無資料',
    success: '操作成功',
    failed: '操作失敗',
    warning: '警告',
    info: '提示'
  },
  auth: {
    login: '登入',
    logout: '登出',
    register: '註冊',
    phone: '手機號碼',
    password: '密碼',
    confirmPassword: '確認密碼',
    verifyCode: '驗證碼',
    getCode: '獲取驗證碼',
    resendCode: '{seconds}秒後重發',
    forgotPassword: '忘記密碼？',
    hasAccount: '已有帳號？',
    noAccount: '沒有帳號？',
    loginNow: '立即登入',
    registerNow: '立即註冊',
    agreeTerms: '我已閱讀並同意',
    userAgreement: '用戶協議',
    privacyPolicy: '隱私政策',
    and: '和'
  },
  role: {
    elderly: '長者',
    family: '家屬',
    admin: '管理員'
  },
  nav: {
    home: '首頁',
    health: '健康',
    emergency: '緊急求助',
    medication: '用藥',
    chat: '陪聊',
    profile: '我的',
    dashboard: '儀表盤',
    monitor: '監護',
    alerts: '警報',
    messages: '訊息',
    settings: '設定',
    users: '用戶',
    devices: '設備',
    reports: '報表'
  },
  health: {
    title: '健康資料',
    bloodPressure: '血壓',
    heartRate: '心率',
    bloodSugar: '血糖',
    weight: '體重',
    temperature: '體溫',
    systolic: '收縮壓',
    diastolic: '舒張壓',
    normal: '正常',
    abnormal: '異常',
    high: '偏高',
    low: '偏低',
    unit: {
      mmHg: 'mmHg',
      bpm: '次/分',
      mmol: 'mmol/L',
      kg: 'kg',
      celsius: '°C'
    },
    history: '歷史記錄',
    trend: '趨勢',
    average: '平均值',
    normalRange: '正常範圍',
    measureTime: '測量時間',
    measureNow: '立即測量',
    syncDevice: '同步設備資料'
  },
  emergency: {
    title: '緊急求助',
    sos: 'SOS緊急呼叫',
    sosDesc: '按住3秒發起緊急求助',
    contacts: '緊急聯絡人',
    addContact: '新增聯絡人',
    callNow: '立即呼叫',
    location: '當前位置',
    history: '求助記錄',
    status: {
      pending: '待處理',
      handling: '處理中',
      resolved: '已解決',
      cancelled: '已取消'
    }
  },
  medication: {
    title: '用藥管理',
    reminder: '用藥提醒',
    addMedication: '新增藥物',
    name: '藥物名稱',
    dosage: '劑量',
    frequency: '頻率',
    time: '服藥時間',
    notes: '備註',
    taken: '已服用',
    missed: '漏服',
    upcoming: '即將服藥',
    schedule: '今日安排'
  },
  device: {
    title: '設備管理',
    add: '新增設備',
    bind: '綁定設備',
    unbind: '解綁設備',
    status: {
      online: '在線',
      offline: '離線'
    },
    battery: '電量',
    lastSync: '最後同步',
    type: {
      watch: '智慧手錶',
      bp_monitor: '血壓儀',
      glucose_meter: '血糖儀',
      scale: '體重秤',
      thermometer: '體溫計'
    }
  },
  alert: {
    title: '警報通知',
    type: {
      health: '健康警報',
      device: '設備警報',
      medication: '用藥警報',
      sos: '緊急求助'
    },
    level: {
      low: '低',
      medium: '中',
      high: '高',
      critical: '緊急'
    },
    handle: '處理',
    handled: '已處理',
    ignore: '忽略'
  },
  settings: {
    title: '設定',
    account: '帳號設定',
    notification: '通知設定',
    privacy: '隱私設定',
    language: '語言',
    about: '關於我們',
    version: '版本',
    feedback: '意見回饋',
    help: '幫助中心'
  },
  validation: {
    required: '此項為必填',
    phoneInvalid: '請輸入正確的手機號',
    codeInvalid: '驗證碼格式不正確',
    passwordMin: '密碼至少{min}位',
    passwordMax: '密碼最多{max}位',
    passwordMismatch: '兩次輸入的密碼不一致',
    nameInvalid: '姓名格式不正確'
  }
}

// 英文
const enUS = {
  common: {
    confirm: 'Confirm',
    cancel: 'Cancel',
    save: 'Save',
    delete: 'Delete',
    edit: 'Edit',
    add: 'Add',
    search: 'Search',
    reset: 'Reset',
    loading: 'Loading...',
    noData: 'No Data',
    success: 'Success',
    failed: 'Failed',
    warning: 'Warning',
    info: 'Info'
  },
  auth: {
    login: 'Login',
    logout: 'Logout',
    register: 'Register',
    phone: 'Phone Number',
    password: 'Password',
    confirmPassword: 'Confirm Password',
    verifyCode: 'Verification Code',
    getCode: 'Get Code',
    resendCode: 'Resend in {seconds}s',
    forgotPassword: 'Forgot Password?',
    hasAccount: 'Already have an account?',
    noAccount: "Don't have an account?",
    loginNow: 'Login Now',
    registerNow: 'Register Now',
    agreeTerms: 'I have read and agree to',
    userAgreement: 'User Agreement',
    privacyPolicy: 'Privacy Policy',
    and: 'and'
  },
  role: {
    elderly: 'Elderly',
    family: 'Family',
    admin: 'Admin'
  },
  nav: {
    home: 'Home',
    health: 'Health',
    emergency: 'Emergency',
    medication: 'Medication',
    chat: 'Chat',
    profile: 'Profile',
    dashboard: 'Dashboard',
    monitor: 'Monitor',
    alerts: 'Alerts',
    messages: 'Messages',
    settings: 'Settings',
    users: 'Users',
    devices: 'Devices',
    reports: 'Reports'
  },
  health: {
    title: 'Health Data',
    bloodPressure: 'Blood Pressure',
    heartRate: 'Heart Rate',
    bloodSugar: 'Blood Sugar',
    weight: 'Weight',
    temperature: 'Temperature',
    systolic: 'Systolic',
    diastolic: 'Diastolic',
    normal: 'Normal',
    abnormal: 'Abnormal',
    high: 'High',
    low: 'Low',
    unit: {
      mmHg: 'mmHg',
      bpm: 'bpm',
      mmol: 'mmol/L',
      kg: 'kg',
      celsius: '°C'
    },
    history: 'History',
    trend: 'Trend',
    average: 'Average',
    normalRange: 'Normal Range',
    measureTime: 'Measure Time',
    measureNow: 'Measure Now',
    syncDevice: 'Sync Device Data'
  },
  emergency: {
    title: 'Emergency',
    sos: 'SOS Emergency Call',
    sosDesc: 'Hold for 3 seconds to call for help',
    contacts: 'Emergency Contacts',
    addContact: 'Add Contact',
    callNow: 'Call Now',
    location: 'Current Location',
    history: 'History',
    status: {
      pending: 'Pending',
      handling: 'Handling',
      resolved: 'Resolved',
      cancelled: 'Cancelled'
    }
  },
  medication: {
    title: 'Medication',
    reminder: 'Reminder',
    addMedication: 'Add Medication',
    name: 'Name',
    dosage: 'Dosage',
    frequency: 'Frequency',
    time: 'Time',
    notes: 'Notes',
    taken: 'Taken',
    missed: 'Missed',
    upcoming: 'Upcoming',
    schedule: "Today's Schedule"
  },
  device: {
    title: 'Devices',
    add: 'Add Device',
    bind: 'Bind Device',
    unbind: 'Unbind Device',
    status: {
      online: 'Online',
      offline: 'Offline'
    },
    battery: 'Battery',
    lastSync: 'Last Sync',
    type: {
      watch: 'Smart Watch',
      bp_monitor: 'BP Monitor',
      glucose_meter: 'Glucose Meter',
      scale: 'Scale',
      thermometer: 'Thermometer'
    }
  },
  alert: {
    title: 'Alerts',
    type: {
      health: 'Health Alert',
      device: 'Device Alert',
      medication: 'Medication Alert',
      sos: 'SOS Alert'
    },
    level: {
      low: 'Low',
      medium: 'Medium',
      high: 'High',
      critical: 'Critical'
    },
    handle: 'Handle',
    handled: 'Handled',
    ignore: 'Ignore'
  },
  settings: {
    title: 'Settings',
    account: 'Account',
    notification: 'Notifications',
    privacy: 'Privacy',
    language: 'Language',
    about: 'About',
    version: 'Version',
    feedback: 'Feedback',
    help: 'Help'
  },
  validation: {
    required: 'This field is required',
    phoneInvalid: 'Please enter a valid phone number',
    codeInvalid: 'Invalid verification code',
    passwordMin: 'Password must be at least {min} characters',
    passwordMax: 'Password must be at most {max} characters',
    passwordMismatch: 'Passwords do not match',
    nameInvalid: 'Invalid name format'
  }
}

// 创建i18n实例
const i18n = createI18n({
  legacy: false, // 使用 Composition API 模式
  locale: localStorage.getItem('locale') || 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'zh-TW': zhTW,
    'en-US': enUS
  }
})

// 切换语言
export function setLocale(locale) {
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
  document.querySelector('html').setAttribute('lang', locale)
}

// 获取当前语言
export function getLocale() {
  return i18n.global.locale.value
}

// 可用语言列表
export const availableLocales = [
  { code: 'zh-CN', name: '简体中文' },
  { code: 'zh-TW', name: '繁體中文' },
  { code: 'en-US', name: 'English' }
]

export default i18n
