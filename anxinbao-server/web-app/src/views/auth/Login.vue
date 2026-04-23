<template>
  <div class="min-h-screen bg-gradient-to-b from-primary-50 to-white flex flex-col">
    <!-- Logo区域 -->
    <div class="flex-1 flex flex-col items-center justify-center px-6 pt-12 pb-8">
      <div class="w-24 h-24 bg-primary-500 rounded-3xl flex items-center justify-center mb-6 shadow-lg">
        <svg class="w-14 h-14 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
      </div>
      <h1 class="text-4xl font-bold text-gray-800 mb-2">安心宝</h1>
      <p class="text-lg text-gray-500">让关爱更简单</p>
    </div>

    <!-- 登录表单 -->
    <div class="bg-white rounded-t-3xl shadow-soft px-6 pt-8 pb-safe">
      <h2 class="text-2xl font-bold text-gray-800 mb-6 text-center">欢迎登录</h2>

      <form @submit.prevent="handleLogin" class="space-y-5">
        <!-- 手机号 -->
        <Input
          v-model="form.phone"
          type="tel"
          label="手机号码"
          placeholder="请输入手机号"
          :error="errors.phone"
          required
        />

        <!-- 密码 -->
        <Input
          v-model="form.password"
          type="password"
          label="登录密码"
          placeholder="请输入密码"
          :error="errors.password"
          required
        />

        <!-- 记住登录 -->
        <div class="flex items-center justify-between">
          <label class="flex items-center cursor-pointer">
            <input
              type="checkbox"
              v-model="form.remember"
              class="w-5 h-5 rounded border-gray-300 text-primary-500 focus:ring-primary-500"
            />
            <span class="ml-2 text-gray-600">记住登录</span>
          </label>
          <a href="#" class="text-primary-500 hover:text-primary-600">忘记密码？</a>
        </div>

        <!-- 登录按钮 -->
        <Button
          type="submit"
          variant="primary"
          size="lg"
          block
          :loading="loading"
        >
          登 录
        </Button>
      </form>

      <!-- 角色切换 -->
      <div class="mt-6">
        <p class="text-center text-gray-500 mb-4">选择登录身份</p>
        <div class="flex gap-3">
          <button
            v-for="role in roles"
            :key="role.value"
            :class="[
              'flex-1 py-3 px-4 rounded-xl border-2 transition-all',
              selectedRole === role.value
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-gray-200 text-gray-600 hover:border-gray-300'
            ]"
            @click="selectedRole = role.value"
          >
            <div class="text-lg font-medium">{{ role.label }}</div>
          </button>
        </div>
      </div>

      <!-- 注册入口 -->
      <div class="mt-8 text-center">
        <p class="text-gray-500">
          还没有账号？
          <router-link to="/register" class="text-primary-500 font-medium hover:text-primary-600">
            立即注册
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@stores/user'
import Button from '@components/ui/Button.vue'
import Input from '@components/ui/Input.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const selectedRole = ref('elderly')

const form = reactive({
  phone: '',
  password: '',
  remember: true
})

const errors = reactive({
  phone: '',
  password: ''
})

const roles = [
  { value: 'elderly', label: '老人' },
  { value: 'family', label: '家属' },
  { value: 'admin', label: '管理' }
]

// 表单验证
function validate() {
  errors.phone = ''
  errors.password = ''

  if (!form.phone) {
    errors.phone = '请输入手机号'
    return false
  }

  if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    errors.phone = '手机号格式不正确'
    return false
  }

  if (!form.password) {
    errors.password = '请输入密码'
    return false
  }

  if (form.password.length < 6) {
    errors.password = '密码长度不能少于6位'
    return false
  }

  return true
}

// 登录处理
async function handleLogin() {
  if (!validate()) return

  loading.value = true

  try {
    const result = await userStore.login(form.phone, form.password)

    if (result.success) {
      window.$toast?.success('登录成功')

      // 跳转到对应页面
      const redirect = route.query.redirect
      if (redirect) {
        router.push(redirect)
      } else {
        const roleRoutes = {
          elderly: '/',
          family: '/family',
          admin: '/admin'
        }
        router.push(roleRoutes[selectedRole.value] || '/')
      }
    } else {
      window.$toast?.error(result.message || '登录失败')
    }
  } catch (error) {
    window.$toast?.error('登录失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>
