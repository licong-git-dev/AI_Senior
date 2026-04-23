<template>
  <div>
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">实时监护</h1>
      <div class="flex items-center space-x-2">
        <span class="text-sm text-gray-500">自动刷新</span>
        <label class="relative inline-flex items-center cursor-pointer">
          <input type="checkbox" v-model="autoRefresh" class="sr-only peer">
          <div class="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-primary-500 transition-colors"></div>
          <div class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-5"></div>
        </label>
      </div>
    </div>

    <!-- 老人选择 -->
    <div class="flex space-x-3 mb-6 overflow-x-auto pb-2">
      <button
        v-for="elder in elders"
        :key="elder.id"
        :class="[
          'flex items-center px-4 py-3 rounded-xl whitespace-nowrap transition-all',
          selectedElder === elder.id
            ? 'bg-primary-500 text-white shadow-lg'
            : 'bg-white text-gray-700 shadow-sm hover:shadow'
        ]"
        @click="selectedElder = elder.id"
      >
        <div :class="[
          'w-10 h-10 rounded-full flex items-center justify-center font-bold mr-3',
          selectedElder === elder.id ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-600'
        ]">
          {{ elder.name.charAt(0) }}
        </div>
        <div class="text-left">
          <p class="font-medium">{{ elder.name }}</p>
          <p :class="selectedElder === elder.id ? 'text-primary-100' : 'text-gray-500'" class="text-sm">
            {{ elder.relation }}
          </p>
        </div>
      </button>
    </div>

    <!-- 实时状态 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      <!-- 位置信息 -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-gray-800">当前位置</h3>
          <span class="text-sm text-gray-500">{{ currentElder.location.updateTime }}</span>
        </div>
        <div class="aspect-video bg-gray-100 rounded-xl mb-4 flex items-center justify-center">
          <div class="text-center text-gray-400">
            <svg class="w-12 h-12 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <p>地图加载中...</p>
          </div>
        </div>
        <p class="text-gray-800 font-medium">{{ currentElder.location.address }}</p>
        <p class="text-sm text-gray-500 mt-1">{{ currentElder.location.detail }}</p>
      </div>

      <!-- 生命体征 -->
      <div class="lg:col-span-2 bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-gray-800">生命体征</h3>
          <span :class="[
            'px-3 py-1 rounded-full text-sm',
            currentElder.healthStatus === 'normal' ? 'bg-green-100 text-green-700' :
            currentElder.healthStatus === 'warning' ? 'bg-yellow-100 text-yellow-700' :
            'bg-red-100 text-red-700'
          ]">
            {{ currentElder.healthStatusText }}
          </span>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div v-for="vital in currentElder.vitals" :key="vital.type" class="bg-gray-50 rounded-xl p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-gray-500">{{ vital.label }}</span>
              <span :class="[
                'w-2 h-2 rounded-full',
                vital.status === 'normal' ? 'bg-green-500' :
                vital.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
              ]"></span>
            </div>
            <p class="text-2xl font-bold text-gray-800">{{ vital.value }}</p>
            <p class="text-sm text-gray-400">{{ vital.unit }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 活动状态 & 设备状态 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <!-- 今日活动 -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <h3 class="font-bold text-gray-800 mb-4">今日活动</h3>
        <div class="space-y-4">
          <div class="flex items-center">
            <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mr-4">
              <svg class="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div class="flex-1">
              <p class="text-gray-500">步数</p>
              <p class="text-xl font-bold text-gray-800">{{ currentElder.activity.steps.toLocaleString() }}</p>
            </div>
            <div class="text-right">
              <p class="text-sm text-gray-500">目标 {{ currentElder.activity.stepGoal.toLocaleString() }}</p>
              <div class="w-24 h-2 bg-gray-200 rounded-full mt-1">
                <div
                  class="h-full bg-blue-500 rounded-full"
                  :style="{ width: Math.min(100, currentElder.activity.steps / currentElder.activity.stepGoal * 100) + '%' }"
                ></div>
              </div>
            </div>
          </div>
          <div class="flex items-center">
            <div class="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mr-4">
              <svg class="w-6 h-6 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
              </svg>
            </div>
            <div class="flex-1">
              <p class="text-gray-500">消耗热量</p>
              <p class="text-xl font-bold text-gray-800">{{ currentElder.activity.calories }} kcal</p>
            </div>
          </div>
          <div class="flex items-center">
            <div class="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mr-4">
              <svg class="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            </div>
            <div class="flex-1">
              <p class="text-gray-500">睡眠时长</p>
              <p class="text-xl font-bold text-gray-800">{{ currentElder.activity.sleepHours }} 小时</p>
            </div>
            <span class="text-sm text-green-600">质量良好</span>
          </div>
        </div>
      </div>

      <!-- 设备状态 -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <h3 class="font-bold text-gray-800 mb-4">设备状态</h3>
        <div class="space-y-4">
          <div v-for="device in currentElder.devices" :key="device.id" class="flex items-center p-3 bg-gray-50 rounded-xl">
            <div :class="[
              'w-12 h-12 rounded-xl flex items-center justify-center mr-4',
              device.online ? 'bg-green-100' : 'bg-gray-200'
            ]">
              <svg :class="['w-6 h-6', device.online ? 'text-green-600' : 'text-gray-400']" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div class="flex-1">
              <p class="font-medium text-gray-800">{{ device.name }}</p>
              <p class="text-sm text-gray-500">{{ device.model }}</p>
            </div>
            <div class="text-right">
              <span :class="[
                'px-2 py-1 rounded text-xs',
                device.online ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'
              ]">
                {{ device.online ? '在线' : '离线' }}
              </span>
              <div class="flex items-center justify-end mt-1 text-sm text-gray-500">
                <svg class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                {{ device.battery }}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史轨迹 -->
    <div class="bg-white rounded-xl shadow-sm p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-bold text-gray-800">今日轨迹</h3>
        <select class="border border-gray-200 rounded-lg px-3 py-2 text-sm">
          <option>今天</option>
          <option>昨天</option>
          <option>最近7天</option>
        </select>
      </div>
      <div class="space-y-3">
        <div v-for="track in currentElder.tracks" :key="track.id" class="flex items-start">
          <div class="flex flex-col items-center mr-4">
            <div class="w-3 h-3 bg-primary-500 rounded-full"></div>
            <div class="w-0.5 h-12 bg-gray-200"></div>
          </div>
          <div class="flex-1 pb-4">
            <p class="font-medium text-gray-800">{{ track.location }}</p>
            <p class="text-sm text-gray-500">{{ track.time }} · 停留 {{ track.duration }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const autoRefresh = ref(true)
const selectedElder = ref(1)

const elders = ref([
  { id: 1, name: '王爷爷', relation: '父亲' },
  { id: 2, name: '李奶奶', relation: '母亲' }
])

const elderData = {
  1: {
    healthStatus: 'normal',
    healthStatusText: '状态良好',
    location: {
      address: '北京市朝阳区xxx小区',
      detail: 'A栋 12层 1202室（家中）',
      updateTime: '刚刚'
    },
    vitals: [
      { type: 'bp', label: '血压', value: '125/82', unit: 'mmHg', status: 'normal' },
      { type: 'hr', label: '心率', value: '72', unit: '次/分', status: 'normal' },
      { type: 'spo2', label: '血氧', value: '98', unit: '%', status: 'normal' },
      { type: 'temp', label: '体温', value: '36.5', unit: '°C', status: 'normal' }
    ],
    activity: {
      steps: 3256,
      stepGoal: 6000,
      calories: 156,
      sleepHours: 7.5
    },
    devices: [
      { id: 1, name: '智能手表', model: 'AX-Watch Pro', online: true, battery: 85 },
      { id: 2, name: '血压计', model: 'AX-BP100', online: true, battery: 62 }
    ],
    tracks: [
      { id: 1, location: '家中', time: '06:30', duration: '2小时' },
      { id: 2, location: '小区公园', time: '08:30', duration: '45分钟' },
      { id: 3, location: '菜市场', time: '09:30', duration: '30分钟' },
      { id: 4, location: '家中', time: '10:15', duration: '至今' }
    ]
  },
  2: {
    healthStatus: 'warning',
    healthStatusText: '血压偏高',
    location: {
      address: '北京市朝阳区xxx小区',
      detail: 'B栋 8层 802室（家中）',
      updateTime: '2分钟前'
    },
    vitals: [
      { type: 'bp', label: '血压', value: '145/95', unit: 'mmHg', status: 'warning' },
      { type: 'hr', label: '心率', value: '78', unit: '次/分', status: 'normal' },
      { type: 'spo2', label: '血氧', value: '97', unit: '%', status: 'normal' },
      { type: 'temp', label: '体温', value: '36.3', unit: '°C', status: 'normal' }
    ],
    activity: {
      steps: 1890,
      stepGoal: 5000,
      calories: 98,
      sleepHours: 6.5
    },
    devices: [
      { id: 1, name: '智能手表', model: 'AX-Watch Lite', online: true, battery: 45 }
    ],
    tracks: [
      { id: 1, location: '家中', time: '07:00', duration: '3小时' },
      { id: 2, location: '社区活动中心', time: '10:00', duration: '1小时' },
      { id: 3, location: '家中', time: '11:15', duration: '至今' }
    ]
  }
}

const currentElder = computed(() => elderData[selectedElder.value])
</script>
