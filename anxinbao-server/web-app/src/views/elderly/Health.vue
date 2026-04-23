<template>
  <div class="min-h-screen pb-20">
    <!-- 页头 -->
    <div class="page-header">
      <h1 class="page-title">健康管理</h1>
    </div>

    <!-- 健康概览 -->
    <div class="px-4 pt-4">
      <div class="card gradient-primary text-white">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-primary-100">今日健康评分</p>
            <div class="text-5xl font-bold mt-2">85</div>
            <p class="text-primary-100 mt-1">状态良好</p>
          </div>
          <div class="w-24 h-24">
            <svg viewBox="0 0 100 100" class="w-full h-full">
              <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="8"/>
              <circle cx="50" cy="50" r="40" fill="none" stroke="white" stroke-width="8"
                stroke-dasharray="251.2" stroke-dashoffset="37.68" stroke-linecap="round"
                transform="rotate(-90 50 50)"/>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 生命体征 -->
    <div class="px-4 mt-4">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-800">生命体征</h2>
          <button class="text-primary-500">记录数据</button>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div v-for="vital in vitalSigns" :key="vital.type" class="bg-gray-50 rounded-xl p-4">
            <div class="flex items-center justify-between">
              <span class="text-gray-500">{{ vital.label }}</span>
              <span :class="['health-badge', `health-badge-${vital.status}`]">{{ vital.statusText }}</span>
            </div>
            <div class="mt-2">
              <span class="text-3xl font-bold">{{ vital.value }}</span>
              <span class="text-gray-400 ml-1">{{ vital.unit }}</span>
            </div>
            <p class="text-xs text-gray-400 mt-2">{{ vital.time }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 健康趋势 -->
    <div class="px-4 mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">7日趋势</h2>
        <div class="h-48 flex items-end justify-between gap-2">
          <div v-for="(day, i) in weekData" :key="i" class="flex-1 flex flex-col items-center">
            <div class="w-full bg-primary-100 rounded-t" :style="{ height: day.height + '%' }">
              <div class="w-full bg-primary-500 rounded-t h-1/2"></div>
            </div>
            <span class="text-xs text-gray-500 mt-2">{{ day.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 健康建议 -->
    <div class="px-4 mt-4 mb-6">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">健康建议</h2>
        <div class="space-y-3">
          <div v-for="tip in healthTips" :key="tip.id" class="flex items-start p-3 bg-gray-50 rounded-xl">
            <div class="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center mr-3 flex-shrink-0">
              <svg class="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p class="font-medium text-gray-800">{{ tip.title }}</p>
              <p class="text-sm text-gray-500 mt-1">{{ tip.content }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const vitalSigns = ref([
  { type: 'bp', label: '血压', value: '125/82', unit: 'mmHg', status: 'normal', statusText: '正常', time: '今天 08:30' },
  { type: 'hr', label: '心率', value: '72', unit: '次/分', status: 'normal', statusText: '正常', time: '今天 08:30' },
  { type: 'bs', label: '血糖', value: '5.6', unit: 'mmol/L', status: 'normal', statusText: '正常', time: '今天 07:00' },
  { type: 'weight', label: '体重', value: '65.5', unit: 'kg', status: 'normal', statusText: '正常', time: '昨天 08:00' }
])

const weekData = ref([
  { label: '周一', height: 75 },
  { label: '周二', height: 82 },
  { label: '周三', height: 78 },
  { label: '周四', height: 85 },
  { label: '周五', height: 80 },
  { label: '周六', height: 88 },
  { label: '周日', height: 85 }
])

const healthTips = ref([
  { id: 1, title: '血压控制良好', content: '继续保持规律作息和清淡饮食，每天坚持测量血压。' },
  { id: 2, title: '建议增加运动', content: '今日步数偏低，建议饭后散步30分钟。' },
  { id: 3, title: '注意补充水分', content: '天气较热，请注意多喝水，每天至少8杯。' }
])
</script>
