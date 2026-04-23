<template>
  <div>
    <!-- 欢迎卡片 -->
    <div class="bg-gradient-to-r from-primary-500 to-primary-600 rounded-2xl p-6 text-white mb-6">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-primary-100">{{ greeting }}</p>
          <h1 class="text-2xl font-bold mt-1">{{ userName }}</h1>
          <p class="text-primary-100 mt-2">您正在监护 {{ elderCount }} 位老人</p>
        </div>
        <div class="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
          <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
      </div>
    </div>

    <!-- 监护状态概览 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-xl p-4 shadow-sm">
        <div class="flex items-center justify-between">
          <div class="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="text-2xl font-bold text-green-600">{{ stats.normal }}</span>
        </div>
        <p class="text-gray-500 mt-2">状态正常</p>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm">
        <div class="flex items-center justify-between">
          <div class="w-10 h-10 bg-yellow-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <span class="text-2xl font-bold text-yellow-600">{{ stats.warning }}</span>
        </div>
        <p class="text-gray-500 mt-2">需要关注</p>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm">
        <div class="flex items-center justify-between">
          <div class="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="text-2xl font-bold text-red-600">{{ stats.alert }}</span>
        </div>
        <p class="text-gray-500 mt-2">告警中</p>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm">
        <div class="flex items-center justify-between">
          <div class="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" />
            </svg>
          </div>
          <span class="text-2xl font-bold text-gray-600">{{ stats.offline }}</span>
        </div>
        <p class="text-gray-500 mt-2">设备离线</p>
      </div>
    </div>

    <!-- 被监护老人列表 -->
    <div class="bg-white rounded-xl shadow-sm mb-6">
      <div class="p-4 border-b border-gray-100">
        <h2 class="text-lg font-bold text-gray-800">被监护老人</h2>
      </div>
      <div class="divide-y divide-gray-100">
        <div
          v-for="elder in elders"
          :key="elder.id"
          class="p-4 hover:bg-gray-50 transition-colors cursor-pointer"
          @click="viewElderDetail(elder.id)"
        >
          <div class="flex items-center">
            <div :class="[
              'w-14 h-14 rounded-full flex items-center justify-center text-white font-bold text-xl',
              elder.status === 'normal' ? 'bg-green-500' :
              elder.status === 'warning' ? 'bg-yellow-500' :
              elder.status === 'alert' ? 'bg-red-500' : 'bg-gray-400'
            ]">
              {{ elder.name.charAt(0) }}
            </div>
            <div class="ml-4 flex-1">
              <div class="flex items-center">
                <h3 class="font-bold text-gray-800">{{ elder.name }}</h3>
                <span :class="[
                  'ml-2 px-2 py-0.5 rounded-full text-xs',
                  elder.status === 'normal' ? 'bg-green-100 text-green-700' :
                  elder.status === 'warning' ? 'bg-yellow-100 text-yellow-700' :
                  elder.status === 'alert' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                ]">
                  {{ elder.statusText }}
                </span>
              </div>
              <p class="text-sm text-gray-500 mt-1">{{ elder.relation }} · {{ elder.age }}岁</p>
              <div class="flex items-center mt-2 text-sm text-gray-500">
                <span>血压 {{ elder.health.bp }}</span>
                <span class="mx-2">·</span>
                <span>心率 {{ elder.health.hr }}</span>
                <span class="mx-2">·</span>
                <span>更新于 {{ elder.lastUpdate }}</span>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <a
                :href="`tel:${elder.phone}`"
                class="p-2 bg-green-100 text-green-600 rounded-lg hover:bg-green-200"
                @click.stop
              >
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
              </a>
              <button class="p-2 bg-primary-100 text-primary-600 rounded-lg hover:bg-primary-200">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 健康数据趋势 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      <!-- 综合健康评分 -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <h2 class="text-lg font-bold text-gray-800 mb-4">综合健康评分</h2>
        <GaugeChart
          :value="overallHealthScore"
          :max="100"
          unit="分"
          status="状态良好"
          color="#22C55E"
          height="180px"
        />
      </div>

      <!-- 血压趋势 -->
      <div class="bg-white rounded-xl shadow-sm p-6 lg:col-span-2">
        <h2 class="text-lg font-bold text-gray-800 mb-4">7日血压趋势 (收缩压)</h2>
        <LineChart
          :data="healthTrendData"
          unit="mmHg"
          color="#FF6B35"
          :normalRange="[90, 140]"
          height="180px"
        />
      </div>
    </div>

    <!-- 最近告警 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white rounded-xl shadow-sm">
        <div class="p-4 border-b border-gray-100 flex items-center justify-between">
          <h2 class="text-lg font-bold text-gray-800">最近告警</h2>
          <router-link to="/family/alerts" class="text-primary-500 text-sm">查看全部</router-link>
        </div>
        <div class="divide-y divide-gray-100">
          <div v-for="alert in recentAlerts" :key="alert.id" class="p-4">
            <div class="flex items-start">
              <div :class="[
                'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0',
                alert.level === 'high' ? 'bg-red-100' : 'bg-yellow-100'
              ]">
                <svg :class="[
                  'w-5 h-5',
                  alert.level === 'high' ? 'text-red-600' : 'text-yellow-600'
                ]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div class="ml-3 flex-1">
                <p class="font-medium text-gray-800">{{ alert.title }}</p>
                <p class="text-sm text-gray-500 mt-1">{{ alert.elderName }} · {{ alert.time }}</p>
              </div>
              <span :class="[
                'px-2 py-1 rounded text-xs',
                alert.handled ? 'bg-gray-100 text-gray-600' : 'bg-red-100 text-red-600'
              ]">
                {{ alert.handled ? '已处理' : '待处理' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 用药提醒 -->
      <div class="bg-white rounded-xl shadow-sm">
        <div class="p-4 border-b border-gray-100 flex items-center justify-between">
          <h2 class="text-lg font-bold text-gray-800">今日用药</h2>
          <span class="text-sm text-gray-500">{{ medicationProgress }}</span>
        </div>
        <div class="divide-y divide-gray-100">
          <div v-for="med in todayMedications" :key="med.id" class="p-4">
            <div class="flex items-center">
              <div :class="[
                'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0',
                med.taken ? 'bg-green-100' : 'bg-yellow-100'
              ]">
                <svg :class="[
                  'w-5 h-5',
                  med.taken ? 'text-green-600' : 'text-yellow-600'
                ]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path v-if="med.taken" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div class="ml-3 flex-1">
                <p class="font-medium text-gray-800">{{ med.elderName }} - {{ med.medicine }}</p>
                <p class="text-sm text-gray-500 mt-1">{{ med.time }} · {{ med.dosage }}</p>
              </div>
              <span :class="[
                'text-sm',
                med.taken ? 'text-green-600' : 'text-yellow-600'
              ]">
                {{ med.taken ? '已服用' : '待服用' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@stores/user'
import { LineChart, GaugeChart } from '@/components/charts'

const router = useRouter()
const userStore = useUserStore()

const userName = computed(() => userStore.userName)
const elderCount = computed(() => elders.value.length)

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const stats = ref({
  normal: 1,
  warning: 1,
  alert: 0,
  offline: 0
})

const elders = ref([
  {
    id: 1,
    name: '王爷爷',
    relation: '父亲',
    age: 72,
    phone: '13800138000',
    status: 'normal',
    statusText: '状态良好',
    health: { bp: '125/82', hr: '72' },
    lastUpdate: '5分钟前'
  },
  {
    id: 2,
    name: '李奶奶',
    relation: '母亲',
    age: 68,
    phone: '13800138001',
    status: 'warning',
    statusText: '血压偏高',
    health: { bp: '145/95', hr: '78' },
    lastUpdate: '10分钟前'
  }
])

const recentAlerts = ref([
  { id: 1, title: '血压异常偏高', elderName: '李奶奶', time: '1小时前', level: 'high', handled: false },
  { id: 2, title: '今日步数不足', elderName: '王爷爷', time: '3小时前', level: 'medium', handled: true },
  { id: 3, title: '漏服药物提醒', elderName: '李奶奶', time: '昨天', level: 'medium', handled: true }
])

const todayMedications = ref([
  { id: 1, elderName: '王爷爷', medicine: '阿司匹林', time: '08:00', dosage: '1片', taken: true },
  { id: 2, elderName: '李奶奶', medicine: '氨氯地平', time: '08:00', dosage: '1片', taken: true },
  { id: 3, elderName: '王爷爷', medicine: '降压药', time: '12:00', dosage: '1片', taken: false },
  { id: 4, elderName: '李奶奶', medicine: '降糖药', time: '12:00', dosage: '1片', taken: false }
])

const medicationProgress = computed(() => {
  const taken = todayMedications.value.filter(m => m.taken).length
  return `${taken}/${todayMedications.value.length} 已完成`
})

function viewElderDetail(id) {
  router.push(`/family/monitor/${id}`)
}

// 健康趋势数据
const healthTrendData = ref([
  { date: '01/06', value: 125 },
  { date: '01/07', value: 128 },
  { date: '01/08', value: 122 },
  { date: '01/09', value: 130 },
  { date: '01/10', value: 127 },
  { date: '01/11', value: 125 },
  { date: '01/12', value: 124 }
])

// 综合健康评分
const overallHealthScore = ref(85)
</script>
