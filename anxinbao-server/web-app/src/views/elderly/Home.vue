<template>
  <div class="animate-fade-in-up">
    <!-- 顶部问候区域 -->
    <div class="gradient-primary text-white px-6 pt-safe pb-8 rounded-b-3xl">
      <div class="flex items-center justify-between mb-6">
        <div>
          <p class="text-primary-100 text-lg">{{ greeting }}</p>
          <h1 class="text-3xl font-bold mt-1">{{ userName }}</h1>
        </div>
        <div class="avatar-lg bg-white/20 text-white text-2xl font-bold">
          {{ userInitial }}
        </div>
      </div>

      <!-- 今日健康卡片 -->
      <div class="bg-white/10 backdrop-blur rounded-2xl p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-primary-100">今日健康状态</p>
            <div class="flex items-center mt-2">
              <span class="text-3xl font-bold">良好</span>
              <span class="ml-2 px-2 py-1 bg-green-400 text-white text-sm rounded-full">正常</span>
            </div>
          </div>
          <div class="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
            <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷功能区 -->
    <div class="px-4 -mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">常用功能</h2>
        <div class="grid grid-cols-4 gap-4">
          <router-link
            v-for="item in quickActions"
            :key="item.path"
            :to="item.path"
            class="flex flex-col items-center p-3 rounded-xl hover:bg-gray-50 transition-colors"
          >
            <div :class="['w-14 h-14 rounded-2xl flex items-center justify-center', item.bgColor]">
              <component :is="item.icon" :class="['w-8 h-8', item.iconColor]" />
            </div>
            <span class="mt-2 text-sm text-gray-700 text-center">{{ item.label }}</span>
          </router-link>
        </div>
      </div>
    </div>

    <!-- SOS紧急求助按钮 -->
    <div class="px-4 mt-4">
      <router-link to="/emergency" class="block">
        <div class="card bg-danger-50 border-2 border-danger-200 flex items-center justify-between">
          <div>
            <h3 class="text-xl font-bold text-danger-700">紧急求助</h3>
            <p class="text-danger-500 mt-1">点击呼叫家人或急救</p>
          </div>
          <div class="w-16 h-16 bg-danger-500 rounded-full flex items-center justify-center shadow-lg animate-pulse-slow">
            <svg class="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
        </div>
      </router-link>
    </div>

    <!-- 今日提醒 -->
    <div class="px-4 mt-4">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-800">今日提醒</h2>
          <router-link to="/medication" class="text-primary-500 text-sm">查看全部</router-link>
        </div>

        <div v-if="reminders.length > 0" class="space-y-3">
          <div
            v-for="reminder in reminders"
            :key="reminder.id"
            :class="[
              'flex items-center p-3 rounded-xl',
              reminder.done ? 'bg-gray-50' : 'bg-primary-50'
            ]"
          >
            <div :class="[
              'w-12 h-12 rounded-full flex items-center justify-center mr-3',
              reminder.done ? 'bg-gray-200' : 'bg-primary-200'
            ]">
              <component :is="reminder.icon" :class="['w-6 h-6', reminder.done ? 'text-gray-500' : 'text-primary-600']" />
            </div>
            <div class="flex-1">
              <p :class="['font-medium', reminder.done ? 'text-gray-500 line-through' : 'text-gray-800']">
                {{ reminder.title }}
              </p>
              <p class="text-sm text-gray-500">{{ reminder.time }}</p>
            </div>
            <button
              v-if="!reminder.done"
              class="px-4 py-2 bg-primary-500 text-white rounded-xl text-sm"
              @click="completeReminder(reminder.id)"
            >
              完成
            </button>
            <span v-else class="text-green-500 text-sm">已完成</span>
          </div>
        </div>

        <div v-else class="empty-state py-8">
          <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="text-gray-500">今天没有待办提醒</p>
        </div>
      </div>
    </div>

    <!-- 健康数据概览 -->
    <div class="px-4 mt-4 mb-6">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-800">健康数据</h2>
          <router-link to="/health" class="text-primary-500 text-sm">详情</router-link>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div v-for="stat in healthStats" :key="stat.label" class="bg-gray-50 rounded-xl p-4">
            <p class="text-sm text-gray-500">{{ stat.label }}</p>
            <div class="flex items-baseline mt-1">
              <span class="stat-value text-2xl">{{ stat.value }}</span>
              <span class="stat-unit text-sm">{{ stat.unit }}</span>
            </div>
            <div class="mt-2 flex items-center">
              <span :class="['text-xs px-2 py-0.5 rounded-full', stat.statusClass]">
                {{ stat.status }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue'
import { useUserStore } from '@stores/user'

const userStore = useUserStore()

// 计算问候语
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const userName = computed(() => userStore.userName)
const userInitial = computed(() => userName.value.charAt(0))

// 快捷功能
const quickActions = [
  {
    path: '/health',
    label: '健康记录',
    bgColor: 'bg-red-100',
    iconColor: 'text-red-500',
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z' })
    ])}
  },
  {
    path: '/medication',
    label: '用药提醒',
    bgColor: 'bg-blue-100',
    iconColor: 'text-blue-500',
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z' })
    ])}
  },
  {
    path: '/chat',
    label: '智能聊天',
    bgColor: 'bg-green-100',
    iconColor: 'text-green-500',
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' })
    ])}
  },
  {
    path: '/entertainment',
    label: '娱乐休闲',
    bgColor: 'bg-purple-100',
    iconColor: 'text-purple-500',
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3' })
    ])}
  }
]

// 今日提醒
const reminders = ref([
  {
    id: 1,
    title: '服用阿司匹林',
    time: '08:00',
    done: true,
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z' })
    ])}
  },
  {
    id: 2,
    title: '测量血压',
    time: '10:00',
    done: false,
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z' })
    ])}
  },
  {
    id: 3,
    title: '服用降压药',
    time: '12:00',
    done: false,
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z' })
    ])}
  }
])

// 健康数据
const healthStats = ref([
  { label: '血压', value: '125/82', unit: 'mmHg', status: '正常', statusClass: 'bg-green-100 text-green-700' },
  { label: '心率', value: '72', unit: '次/分', status: '正常', statusClass: 'bg-green-100 text-green-700' },
  { label: '血糖', value: '5.6', unit: 'mmol/L', status: '正常', statusClass: 'bg-green-100 text-green-700' },
  { label: '今日步数', value: '3,256', unit: '步', status: '继续加油', statusClass: 'bg-yellow-100 text-yellow-700' }
])

function completeReminder(id) {
  const reminder = reminders.value.find(r => r.id === id)
  if (reminder) {
    reminder.done = true
    window.$toast?.success('已完成')
  }
}
</script>
