<template>
  <div>
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">告警记录</h1>
      <div class="flex gap-2">
        <select v-model="filterStatus" class="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm">
          <option value="all">全部状态</option>
          <option value="pending">待处理</option>
          <option value="handled">已处理</option>
        </select>
        <select v-model="filterLevel" class="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm">
          <option value="all">全部级别</option>
          <option value="high">紧急</option>
          <option value="medium">警告</option>
          <option value="low">提示</option>
        </select>
      </div>
    </div>

    <!-- 告警统计 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-xl p-4 shadow-sm">
        <div class="flex items-center">
          <div class="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center mr-4">
            <svg class="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-800">{{ stats.pending }}</p>
            <p class="text-gray-500">待处理</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm">
        <div class="flex items-center">
          <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mr-4">
            <svg class="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-800">{{ stats.handled }}</p>
            <p class="text-gray-500">已处理</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm">
        <div class="flex items-center">
          <div class="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center mr-4">
            <svg class="w-6 h-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-800">{{ stats.today }}</p>
            <p class="text-gray-500">今日告警</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm">
        <div class="flex items-center">
          <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mr-4">
            <svg class="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-800">{{ stats.week }}</p>
            <p class="text-gray-500">本周告警</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 告警列表 -->
    <div class="bg-white rounded-xl shadow-sm">
      <div class="divide-y divide-gray-100">
        <div
          v-for="alert in filteredAlerts"
          :key="alert.id"
          class="p-4 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-start">
            <div :class="[
              'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 mr-4',
              alert.level === 'high' ? 'bg-red-100' :
              alert.level === 'medium' ? 'bg-yellow-100' : 'bg-blue-100'
            ]">
              <svg :class="[
                'w-6 h-6',
                alert.level === 'high' ? 'text-red-600' :
                alert.level === 'medium' ? 'text-yellow-600' : 'text-blue-600'
              ]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path v-if="alert.level === 'high'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                <path v-else-if="alert.level === 'medium'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  <h3 class="font-bold text-gray-800">{{ alert.title }}</h3>
                  <span :class="[
                    'ml-2 px-2 py-0.5 rounded text-xs',
                    alert.level === 'high' ? 'bg-red-100 text-red-700' :
                    alert.level === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-blue-100 text-blue-700'
                  ]">
                    {{ alert.levelText }}
                  </span>
                </div>
                <span :class="[
                  'px-2 py-1 rounded text-xs',
                  alert.status === 'pending' ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'
                ]">
                  {{ alert.status === 'pending' ? '待处理' : '已处理' }}
                </span>
              </div>
              <p class="text-gray-600 mt-1">{{ alert.description }}</p>
              <div class="flex items-center mt-2 text-sm text-gray-500">
                <span>{{ alert.elderName }}</span>
                <span class="mx-2">·</span>
                <span>{{ alert.time }}</span>
              </div>
              <div v-if="alert.status === 'pending'" class="mt-3 flex gap-2">
                <button
                  class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm"
                  @click="handleAlert(alert.id)"
                >
                  标记已处理
                </button>
                <a
                  :href="`tel:${alert.elderPhone}`"
                  class="px-4 py-2 bg-green-500 text-white rounded-lg text-sm"
                >
                  联系老人
                </a>
              </div>
              <div v-else class="mt-2 text-sm text-gray-500">
                处理人：{{ alert.handler }} · {{ alert.handledTime }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="filteredAlerts.length === 0" class="p-12 text-center">
        <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-gray-500">暂无告警记录</p>
      </div>

      <!-- 分页 -->
      <div class="p-4 border-t border-gray-100 flex items-center justify-between">
        <span class="text-sm text-gray-500">共 {{ alerts.length }} 条记录</span>
        <div class="flex gap-2">
          <button class="px-3 py-1 border border-gray-200 rounded text-sm text-gray-600 hover:bg-gray-50">上一页</button>
          <button class="px-3 py-1 border border-gray-200 rounded text-sm text-gray-600 hover:bg-gray-50">下一页</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const filterStatus = ref('all')
const filterLevel = ref('all')

const stats = ref({
  pending: 2,
  handled: 15,
  today: 3,
  week: 12
})

const alerts = ref([
  {
    id: 1,
    title: 'SOS紧急求助',
    description: '老人按下SOS按钮，请立即确认情况',
    level: 'high',
    levelText: '紧急',
    elderName: '王爷爷',
    elderPhone: '13800138000',
    time: '今天 14:30',
    status: 'pending'
  },
  {
    id: 2,
    title: '血压异常',
    description: '检测到血压145/95 mmHg，高于正常范围',
    level: 'high',
    levelText: '紧急',
    elderName: '李奶奶',
    elderPhone: '13800138001',
    time: '今天 10:30',
    status: 'pending'
  },
  {
    id: 3,
    title: '漏服药物',
    description: '12:00 的降压药未按时服用',
    level: 'medium',
    levelText: '警告',
    elderName: '王爷爷',
    elderPhone: '13800138000',
    time: '今天 12:30',
    status: 'handled',
    handler: '张小明',
    handledTime: '今天 12:45'
  },
  {
    id: 4,
    title: '步数不足',
    description: '今日步数仅1890步，低于建议目标',
    level: 'low',
    levelText: '提示',
    elderName: '李奶奶',
    elderPhone: '13800138001',
    time: '今天 18:00',
    status: 'handled',
    handler: '系统',
    handledTime: '今天 18:00'
  },
  {
    id: 5,
    title: '设备电量低',
    description: '智能手表电量低于20%，请提醒老人充电',
    level: 'low',
    levelText: '提示',
    elderName: '李奶奶',
    elderPhone: '13800138001',
    time: '昨天 20:00',
    status: 'handled',
    handler: '李小红',
    handledTime: '昨天 20:30'
  }
])

const filteredAlerts = computed(() => {
  return alerts.value.filter(alert => {
    if (filterStatus.value !== 'all' && alert.status !== filterStatus.value) return false
    if (filterLevel.value !== 'all' && alert.level !== filterLevel.value) return false
    return true
  })
})

function handleAlert(id) {
  const alert = alerts.value.find(a => a.id === id)
  if (alert) {
    alert.status = 'handled'
    alert.handler = '当前用户'
    alert.handledTime = '刚刚'
    stats.value.pending--
    stats.value.handled++
  }
}
</script>
