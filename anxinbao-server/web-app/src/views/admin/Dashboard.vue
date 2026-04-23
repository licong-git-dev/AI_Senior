<template>
  <div>
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">仪表盘</h1>
        <p class="text-gray-500 mt-1">欢迎回来，管理员</p>
      </div>
      <div class="flex gap-2">
        <select class="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm">
          <option>今天</option>
          <option>最近7天</option>
          <option>最近30天</option>
        </select>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg flex items-center">
          <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          导出报告
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      <div class="bg-white rounded-xl p-6 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500">注册用户</p>
            <p class="text-3xl font-bold text-gray-800 mt-2">{{ stats.totalUsers.toLocaleString() }}</p>
            <p class="text-sm text-green-600 mt-2 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
              +12.5%
            </p>
          </div>
          <div class="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center">
            <svg class="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-6 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500">在线设备</p>
            <p class="text-3xl font-bold text-gray-800 mt-2">{{ stats.onlineDevices.toLocaleString() }}</p>
            <p class="text-sm text-gray-500 mt-2">共 {{ stats.totalDevices }} 台设备</p>
          </div>
          <div class="w-14 h-14 bg-green-100 rounded-2xl flex items-center justify-center">
            <svg class="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-6 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500">今日告警</p>
            <p class="text-3xl font-bold text-gray-800 mt-2">{{ stats.todayAlerts }}</p>
            <p class="text-sm text-red-600 mt-2">{{ stats.pendingAlerts }} 待处理</p>
          </div>
          <div class="w-14 h-14 bg-red-100 rounded-2xl flex items-center justify-center">
            <svg class="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-6 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500">SOS求助</p>
            <p class="text-3xl font-bold text-gray-800 mt-2">{{ stats.sosAlerts }}</p>
            <p class="text-sm text-green-600 mt-2">100% 已响应</p>
          </div>
          <div class="w-14 h-14 bg-yellow-100 rounded-2xl flex items-center justify-center">
            <svg class="w-8 h-8 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 图表和列表 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <!-- 用户增长图表 -->
      <div class="bg-white rounded-xl p-6 shadow-sm">
        <h3 class="font-bold text-gray-800 mb-4">用户增长趋势</h3>
        <BarChart
          :data="userGrowthChartData"
          :color="['#FF6B35', '#22C55E', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899']"
          height="250px"
          :showLabel="true"
        />
      </div>

      <!-- 告警类型分布 -->
      <div class="bg-white rounded-xl p-6 shadow-sm">
        <h3 class="font-bold text-gray-800 mb-4">告警类型分布</h3>
        <PieChart
          :data="alertPieData"
          :colors="['#EF4444', '#F59E0B', '#3B82F6', '#8B5CF6', '#22C55E']"
          height="250px"
          innerRadius="40%"
          outerRadius="70%"
        />
      </div>
    </div>

    <!-- 最新数据 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 最新用户 -->
      <div class="bg-white rounded-xl shadow-sm">
        <div class="p-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="font-bold text-gray-800">最新注册用户</h3>
          <router-link to="/admin/users" class="text-primary-500 text-sm">查看全部</router-link>
        </div>
        <div class="divide-y divide-gray-100">
          <div v-for="user in recentUsers" :key="user.id" class="p-4 flex items-center">
            <div class="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-bold mr-4">
              {{ user.name.charAt(0) }}
            </div>
            <div class="flex-1">
              <p class="font-medium text-gray-800">{{ user.name }}</p>
              <p class="text-sm text-gray-500">{{ user.phone }}</p>
            </div>
            <div class="text-right">
              <span :class="[
                'px-2 py-1 rounded text-xs',
                user.role === 'elderly' ? 'bg-blue-100 text-blue-700' :
                user.role === 'family' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
              ]">
                {{ user.roleText }}
              </span>
              <p class="text-sm text-gray-500 mt-1">{{ user.registerTime }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 最新告警 -->
      <div class="bg-white rounded-xl shadow-sm">
        <div class="p-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="font-bold text-gray-800">最新告警</h3>
          <router-link to="/admin/alerts" class="text-primary-500 text-sm">查看全部</router-link>
        </div>
        <div class="divide-y divide-gray-100">
          <div v-for="alert in recentAlerts" :key="alert.id" class="p-4">
            <div class="flex items-start">
              <div :class="[
                'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 mr-4',
                alert.level === 'high' ? 'bg-red-100' : 'bg-yellow-100'
              ]">
                <svg :class="[
                  'w-5 h-5',
                  alert.level === 'high' ? 'text-red-600' : 'text-yellow-600'
                ]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div class="flex-1">
                <p class="font-medium text-gray-800">{{ alert.title }}</p>
                <p class="text-sm text-gray-500 mt-1">{{ alert.user }} · {{ alert.time }}</p>
              </div>
              <span :class="[
                'px-2 py-1 rounded text-xs',
                alert.status === 'pending' ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'
              ]">
                {{ alert.status === 'pending' ? '待处理' : '已处理' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { BarChart, PieChart } from '@/components/charts'

const stats = ref({
  totalUsers: 12580,
  onlineDevices: 8456,
  totalDevices: 10234,
  todayAlerts: 156,
  pendingAlerts: 23,
  sosAlerts: 3
})

const userGrowthData = ref([
  { month: '7月', value: 85 },
  { month: '8月', value: 95 },
  { month: '9月', value: 102 },
  { month: '10月', value: 118 },
  { month: '11月', value: 125 },
  { month: '12月', value: 142 }
])

// 图表数据格式转换
const userGrowthChartData = ref([
  { name: '7月', value: 850 },
  { name: '8月', value: 950 },
  { name: '9月', value: 1020 },
  { name: '10月', value: 1180 },
  { name: '11月', value: 1250 },
  { name: '12月', value: 1420 }
])

const alertPieData = ref([
  { name: '健康异常', value: 45 },
  { name: '用药提醒', value: 38 },
  { name: '设备离线', value: 28 },
  { name: 'SOS求助', value: 12 },
  { name: '电子围栏', value: 8 }
])

const alertTypeData = ref([
  { type: 'health', label: '健康异常', count: 45, color: 'bg-red-500' },
  { type: 'medication', label: '用药提醒', count: 38, color: 'bg-yellow-500' },
  { type: 'device', label: '设备离线', count: 28, color: 'bg-blue-500' },
  { type: 'sos', label: 'SOS求助', count: 12, color: 'bg-purple-500' },
  { type: 'fence', label: '电子围栏', count: 8, color: 'bg-green-500' }
])

const recentUsers = ref([
  { id: 1, name: '王建国', phone: '138****8001', role: 'elderly', roleText: '老人', registerTime: '1小时前' },
  { id: 2, name: '李明', phone: '139****8002', role: 'family', roleText: '家属', registerTime: '2小时前' },
  { id: 3, name: '张芳', phone: '136****8003', role: 'elderly', roleText: '老人', registerTime: '3小时前' },
  { id: 4, name: '刘伟', phone: '137****8004', role: 'family', roleText: '家属', registerTime: '5小时前' }
])

const recentAlerts = ref([
  { id: 1, title: 'SOS紧急求助', user: '王建国', time: '10分钟前', level: 'high', status: 'pending' },
  { id: 2, title: '血压异常偏高', user: '张芳', time: '30分钟前', level: 'high', status: 'pending' },
  { id: 3, title: '设备离线超过1小时', user: '李红', time: '1小时前', level: 'medium', status: 'handled' },
  { id: 4, title: '漏服药物提醒', user: '刘强', time: '2小时前', level: 'medium', status: 'handled' }
])
</script>
