<template>
  <div class="min-h-screen bg-gradient-to-b from-primary-50 to-white flex flex-col">
    <div class="flex-1 flex flex-col items-center justify-center px-6 pt-12 pb-8">
      <div class="w-24 h-24 bg-primary-500 rounded-3xl flex items-center justify-center mb-6 shadow-lg">
        <svg class="w-14 h-14 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
      </div>
      <h1 class="text-4xl font-bold text-gray-800 mb-2">安心宝</h1>
      <p class="text-lg text-gray-500">创建新账号</p>
    </div>

    <div class="bg-white rounded-t-3xl shadow-soft px-6 pt-8 pb-safe">
      <h2 class="text-2xl font-bold text-gray-800 mb-6 text-center">用户注册</h2>
      <form @submit.prevent="handleRegister" class="space-y-5">
        <!-- 手机号 -->
        <div>
          <label class="block text-gray-700 font-medium mb-2">手机号码</label>
          <input
            type="tel"
            v-model="form.phone"
            @blur="validatePhone"
            :class="[
              'w-full px-4 py-3 border rounded-xl transition-colors focus:ring-2 focus:ring-primary-500 focus:border-transparent',
              errors.phone ? 'border-red-300 bg-red-50' : 'border-gray-200'
            ]"
            placeholder="请输入手机号"
            maxlength="11"
          />
          <p v-if="errors.phone" class="mt-1 text-sm text-red-500">{{ errors.phone }}</p>
        </div>

        <!-- 验证码 -->
        <div>
          <label class="block text-gray-700 font-medium mb-2">验证码</label>
          <div class="flex gap-3">
            <input
              type="text"
              v-model="form.code"
              @blur="validateCode"
              :class="[
                'flex-1 px-4 py-3 border rounded-xl transition-colors focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                errors.code ? 'border-red-300 bg-red-50' : 'border-gray-200'
              ]"
              placeholder="请输入验证码"
              maxlength="6"
            />
            <button
              type="button"
              @click="sendCode"
              :disabled="countdown > 0 || !isPhoneValid"
              :class="[
                'px-4 py-3 rounded-xl whitespace-nowrap transition-colors',
                countdown > 0 || !isPhoneValid
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-primary-100 text-primary-600 hover:bg-primary-200'
              ]"
            >
              {{ countdown > 0 ? `${countdown}秒后重发` : '获取验证码' }}
            </button>
          </div>
          <p v-if="errors.code" class="mt-1 text-sm text-red-500">{{ errors.code }}</p>
        </div>

        <!-- 姓名 -->
        <div>
          <label class="block text-gray-700 font-medium mb-2">真实姓名</label>
          <input
            type="text"
            v-model="form.name"
            @blur="validateName"
            :class="[
              'w-full px-4 py-3 border rounded-xl transition-colors focus:ring-2 focus:ring-primary-500 focus:border-transparent',
              errors.name ? 'border-red-300 bg-red-50' : 'border-gray-200'
            ]"
            placeholder="请输入真实姓名"
          />
          <p v-if="errors.name" class="mt-1 text-sm text-red-500">{{ errors.name }}</p>
        </div>

        <!-- 密码 -->
        <div>
          <label class="block text-gray-700 font-medium mb-2">设置密码</label>
          <div class="relative">
            <input
              :type="showPassword ? 'text' : 'password'"
              v-model="form.password"
              @blur="validatePassword"
              @input="checkPasswordStrength"
              :class="[
                'w-full px-4 py-3 pr-12 border rounded-xl transition-colors focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                errors.password ? 'border-red-300 bg-red-50' : 'border-gray-200'
              ]"
              placeholder="请设置6-20位密码"
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <svg v-if="showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
            </button>
          </div>
          <p v-if="errors.password" class="mt-1 text-sm text-red-500">{{ errors.password }}</p>
          <!-- 密码强度指示器 -->
          <div v-if="form.password" class="mt-2">
            <div class="flex gap-1">
              <div
                v-for="i in 4"
                :key="i"
                :class="[
                  'h-1 flex-1 rounded-full transition-colors',
                  i <= passwordStrength ? strengthColors[passwordStrength] : 'bg-gray-200'
                ]"
              ></div>
            </div>
            <p class="text-xs mt-1" :class="strengthTextColors[passwordStrength]">
              密码强度：{{ strengthTexts[passwordStrength] }}
            </p>
          </div>
        </div>

        <!-- 确认密码 -->
        <div>
          <label class="block text-gray-700 font-medium mb-2">确认密码</label>
          <input
            :type="showPassword ? 'text' : 'password'"
            v-model="form.confirmPassword"
            @blur="validateConfirmPassword"
            :class="[
              'w-full px-4 py-3 border rounded-xl transition-colors focus:ring-2 focus:ring-primary-500 focus:border-transparent',
              errors.confirmPassword ? 'border-red-300 bg-red-50' : 'border-gray-200'
            ]"
            placeholder="请再次输入密码"
          />
          <p v-if="errors.confirmPassword" class="mt-1 text-sm text-red-500">{{ errors.confirmPassword }}</p>
        </div>

        <!-- 选择身份 -->
        <div>
          <label class="block text-gray-700 font-medium mb-2">选择身份</label>
          <div class="flex gap-3">
            <button
              type="button"
              v-for="role in roles"
              :key="role.value"
              :class="[
                'flex-1 py-3 rounded-xl border-2 transition-all',
                form.role === role.value
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 text-gray-600 hover:border-gray-300'
              ]"
              @click="form.role = role.value"
            >
              <div class="flex flex-col items-center gap-1">
                <span class="text-2xl">{{ role.icon }}</span>
                <span>{{ role.label }}</span>
              </div>
            </button>
          </div>
        </div>

        <!-- 用户协议 -->
        <div class="flex items-start gap-2">
          <input
            type="checkbox"
            v-model="form.agreed"
            id="agreement"
            class="mt-1 w-4 h-4 rounded text-primary-500 focus:ring-primary-500"
          />
          <label for="agreement" class="text-sm text-gray-600">
            我已阅读并同意
            <a href="#" class="text-primary-500" @click.prevent="showAgreement('user')">《用户协议》</a>
            和
            <a href="#" class="text-primary-500" @click.prevent="showAgreement('privacy')">《隐私政策》</a>
          </label>
        </div>
        <p v-if="errors.agreed" class="text-sm text-red-500 -mt-3">{{ errors.agreed }}</p>

        <!-- 提交按钮 -->
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-4 bg-primary-500 text-white rounded-xl font-medium text-lg hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <svg v-if="loading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
          {{ loading ? '注册中...' : '注 册' }}
        </button>
      </form>

      <div class="mt-8 text-center">
        <p class="text-gray-500">
          已有账号？
          <router-link to="/login" class="text-primary-500 font-medium">立即登录</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 表单数据
const form = reactive({
  phone: '',
  code: '',
  name: '',
  password: '',
  confirmPassword: '',
  role: 'elderly',
  agreed: false
})

// 错误信息
const errors = reactive({
  phone: '',
  code: '',
  name: '',
  password: '',
  confirmPassword: '',
  agreed: ''
})

// 状态
const loading = ref(false)
const countdown = ref(0)
const showPassword = ref(false)
const passwordStrength = ref(0)

// 角色选项
const roles = [
  { value: 'elderly', label: '老人', icon: '👴' },
  { value: 'family', label: '家属', icon: '👨‍👩‍👧' }
]

// 密码强度配置
const strengthColors = {
  1: 'bg-red-500',
  2: 'bg-orange-500',
  3: 'bg-yellow-500',
  4: 'bg-green-500'
}

const strengthTextColors = {
  1: 'text-red-500',
  2: 'text-orange-500',
  3: 'text-yellow-500',
  4: 'text-green-500'
}

const strengthTexts = {
  0: '',
  1: '弱',
  2: '一般',
  3: '较强',
  4: '强'
}

// 手机号是否有效
const isPhoneValid = computed(() => {
  return /^1[3-9]\d{9}$/.test(form.phone)
})

// 验证手机号
function validatePhone() {
  if (!form.phone) {
    errors.phone = '请输入手机号码'
    return false
  }
  if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    errors.phone = '请输入正确的手机号码'
    return false
  }
  errors.phone = ''
  return true
}

// 验证验证码
function validateCode() {
  if (!form.code) {
    errors.code = '请输入验证码'
    return false
  }
  if (!/^\d{6}$/.test(form.code)) {
    errors.code = '验证码格式不正确'
    return false
  }
  errors.code = ''
  return true
}

// 验证姓名
function validateName() {
  if (!form.name) {
    errors.name = '请输入真实姓名'
    return false
  }
  if (form.name.length < 2) {
    errors.name = '姓名至少2个字符'
    return false
  }
  if (!/^[\u4e00-\u9fa5a-zA-Z]+$/.test(form.name)) {
    errors.name = '姓名只能包含中文或英文'
    return false
  }
  errors.name = ''
  return true
}

// 验证密码
function validatePassword() {
  if (!form.password) {
    errors.password = '请设置密码'
    return false
  }
  if (form.password.length < 6) {
    errors.password = '密码至少6位'
    return false
  }
  if (form.password.length > 20) {
    errors.password = '密码最多20位'
    return false
  }
  errors.password = ''
  return true
}

// 验证确认密码
function validateConfirmPassword() {
  if (!form.confirmPassword) {
    errors.confirmPassword = '请再次输入密码'
    return false
  }
  if (form.confirmPassword !== form.password) {
    errors.confirmPassword = '两次输入的密码不一致'
    return false
  }
  errors.confirmPassword = ''
  return true
}

// 验证协议
function validateAgreed() {
  if (!form.agreed) {
    errors.agreed = '请阅读并同意用户协议和隐私政策'
    return false
  }
  errors.agreed = ''
  return true
}

// 检查密码强度
function checkPasswordStrength() {
  const pwd = form.password
  let strength = 0

  if (pwd.length >= 6) strength++
  if (pwd.length >= 8 && /[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) strength++
  if (/\d/.test(pwd)) strength++
  if (/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) strength++

  passwordStrength.value = strength
}

// 发送验证码
async function sendCode() {
  if (!validatePhone()) return
  if (countdown.value > 0) return

  try {
    // 模拟发送验证码API
    await new Promise(resolve => setTimeout(resolve, 500))
    window.$toast?.success('验证码已发送')

    // 开始倒计时
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  } catch (error) {
    window.$toast?.error('发送失败，请稍后重试')
  }
}

// 显示协议
function showAgreement(type) {
  const title = type === 'user' ? '用户协议' : '隐私政策'
  alert(`${title}内容将在正式版本中展示`)
}

// 表单验证
function validateForm() {
  const phoneValid = validatePhone()
  const codeValid = validateCode()
  const nameValid = validateName()
  const passwordValid = validatePassword()
  const confirmValid = validateConfirmPassword()
  const agreedValid = validateAgreed()

  return phoneValid && codeValid && nameValid && passwordValid && confirmValid && agreedValid
}

// 提交注册
async function handleRegister() {
  if (!validateForm()) {
    window.$toast?.warning('请完善表单信息')
    return
  }

  loading.value = true

  try {
    // 模拟注册API
    await new Promise(resolve => setTimeout(resolve, 1500))

    window.$toast?.success('注册成功！')
    router.push('/login')
  } catch (error) {
    window.$toast?.error(error.message || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>
