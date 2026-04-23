<template>
  <div class="min-h-screen pb-20">
    <!-- 页头 -->
    <div class="gradient-primary text-white px-6 pt-safe pb-8 rounded-b-3xl">
      <h1 class="text-2xl font-bold text-center">个人中心</h1>

      <!-- 用户头像和信息 -->
      <div class="flex flex-col items-center mt-6">
        <div class="avatar-xl bg-white/20 text-white text-4xl font-bold mb-4">
          {{ userInitial }}
        </div>
        <h2 class="text-2xl font-bold">{{ userName }}</h2>
        <p class="text-primary-100 mt-1">{{ userPhone }}</p>
      </div>
    </div>

    <!-- 健康档案卡片 -->
    <div class="px-4 -mt-4">
      <div class="card">
        <h3 class="text-lg font-bold text-gray-800 mb-4">健康档案</h3>
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-sm text-gray-500">年龄</p>
            <p class="text-xl font-bold text-gray-800">{{ healthProfile.age }}岁</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-sm text-gray-500">血型</p>
            <p class="text-xl font-bold text-gray-800">{{ healthProfile.bloodType }}</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-sm text-gray-500">身高</p>
            <p class="text-xl font-bold text-gray-800">{{ healthProfile.height }}cm</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-sm text-gray-500">体重</p>
            <p class="text-xl font-bold text-gray-800">{{ healthProfile.weight }}kg</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能列表 -->
    <div class="px-4 mt-4">
      <div class="card p-0 divide-y divide-gray-100">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center justify-between px-4 py-4 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-center">
            <div :class="['w-10 h-10 rounded-xl flex items-center justify-center mr-3', item.bgColor]">
              <component :is="item.icon" :class="['w-5 h-5', item.iconColor]" />
            </div>
            <span class="text-gray-800 font-medium">{{ item.label }}</span>
          </div>
          <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </router-link>
      </div>
    </div>

    <!-- 紧急联系人 -->
    <div class="px-4 mt-4">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-gray-800">紧急联系人</h3>
          <button class="text-primary-500">编辑</button>
        </div>
        <div class="space-y-3">
          <div
            v-for="contact in emergencyContacts"
            :key="contact.id"
            class="flex items-center justify-between p-3 bg-gray-50 rounded-xl"
          >
            <div class="flex items-center">
              <div class="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-bold">
                {{ contact.name.charAt(0) }}
              </div>
              <div class="ml-3">
                <p class="font-medium text-gray-800">{{ contact.name }}</p>
                <p class="text-sm text-gray-500">{{ contact.relation }}</p>
              </div>
            </div>
            <a :href="`tel:${contact.phone}`" class="text-primary-500">
              {{ contact.phone }}
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- 设置选项 -->
    <div class="px-4 mt-4 mb-6">
      <div class="card p-0 divide-y divide-gray-100">
        <div class="flex items-center justify-between px-4 py-4">
          <span class="text-gray-800">大字体模式</span>
          <label class="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" v-model="settings.largeFont" class="sr-only peer">
            <div class="w-14 h-8 bg-gray-200 rounded-full peer peer-checked:bg-primary-500 transition-colors"></div>
            <div class="absolute left-1 top-1 w-6 h-6 bg-white rounded-full shadow transition-transform peer-checked:translate-x-6"></div>
          </label>
        </div>
        <div class="flex items-center justify-between px-4 py-4">
          <span class="text-gray-800">语音播报</span>
          <label class="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" v-model="settings.voiceAnnounce" class="sr-only peer">
            <div class="w-14 h-8 bg-gray-200 rounded-full peer peer-checked:bg-primary-500 transition-colors"></div>
            <div class="absolute left-1 top-1 w-6 h-6 bg-white rounded-full shadow transition-transform peer-checked:translate-x-6"></div>
          </label>
        </div>
        <div class="flex items-center justify-between px-4 py-4">
          <span class="text-gray-800">消息通知</span>
          <label class="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" v-model="settings.notifications" class="sr-only peer">
            <div class="w-14 h-8 bg-gray-200 rounded-full peer peer-checked:bg-primary-500 transition-colors"></div>
            <div class="absolute left-1 top-1 w-6 h-6 bg-white rounded-full shadow transition-transform peer-checked:translate-x-6"></div>
          </label>
        </div>
      </div>
    </div>

    <!-- 退出登录 -->
    <div class="px-4 mb-6">
      <button
        class="w-full py-4 bg-gray-100 text-danger-600 rounded-2xl font-medium text-lg"
        @click="handleLogout"
      >
        退出登录
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, h } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@stores/user'

const router = useRouter()
const userStore = useUserStore()

const userName = computed(() => userStore.userName)
const userInitial = computed(() => userName.value.charAt(0))
const userPhone = computed(() => userStore.user?.phone || '138****8888')

// 健康档案
const healthProfile = ref({
  age: 68,
  bloodType: 'A型',
  height: 168,
  weight: 65
})

// 紧急联系人
const emergencyContacts = ref([
  { id: 1, name: '张小明', relation: '儿子', phone: '138****8001' },
  { id: 2, name: '李小红', relation: '女儿', phone: '138****8002' }
])

// 设置
const settings = ref({
  largeFont: false,
  voiceAnnounce: true,
  notifications: true
})

// 菜单项
const menuItems = [
  {
    path: '/profile/info',
    label: '个人信息',
    bgColor: 'bg-blue-100',
    iconColor: 'text-blue-500',
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' })
    ])}
  },
  {
    path: '/profile/health-record',
    label: '健康档案',
    bgColor: 'bg-red-100',
    iconColor: 'text-red-500',
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' })
    ])}
  },
  {
    path: '/profile/family',
    label: '家人管理',
    bgColor: 'bg-green-100',
    iconColor: 'text-green-500',
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' })
    ])}
  },
  {
    path: '/profile/devices',
    label: '设备管理',
    bgColor: 'bg-purple-100',
    iconColor: 'text-purple-500',
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z' })
    ])}
  }
]

// 退出登录
function handleLogout() {
  if (confirm('确定要退出登录吗？')) {
    userStore.logout()
    router.push('/login')
    window.$toast?.info('已退出登录')
  }
}
</script>
