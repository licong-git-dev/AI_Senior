<template>
  <div class="min-h-screen pb-20">
    <!-- 页头 -->
    <div class="page-header">
      <h1 class="page-title">用药提醒</h1>
      <button class="text-primary-500" @click="showAddModal = true">
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </div>

    <!-- 今日用药 -->
    <div class="px-4 pt-4">
      <div class="card gradient-primary text-white">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-primary-100">今日用药进度</p>
            <div class="text-4xl font-bold mt-2">{{ completedCount }}/{{ todayMedications.length }}</div>
            <p class="text-primary-100 mt-1">{{ completedCount === todayMedications.length ? '太棒了，今日已完成!' : '继续加油' }}</p>
          </div>
          <div class="w-20 h-20">
            <svg viewBox="0 0 100 100" class="w-full h-full transform -rotate-90">
              <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="10"/>
              <circle
                cx="50" cy="50" r="40" fill="none" stroke="white" stroke-width="10"
                stroke-linecap="round"
                :stroke-dasharray="251.2"
                :stroke-dashoffset="251.2 * (1 - completedCount / Math.max(todayMedications.length, 1))"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 时间段筛选 -->
    <div class="px-4 mt-4">
      <div class="flex gap-2 overflow-x-auto pb-2">
        <button
          v-for="time in timeFilters"
          :key="time.value"
          :class="[
            'px-4 py-2 rounded-full whitespace-nowrap transition-colors',
            activeFilter === time.value
              ? 'bg-primary-500 text-white'
              : 'bg-gray-100 text-gray-600'
          ]"
          @click="activeFilter = time.value"
        >
          {{ time.label }}
        </button>
      </div>
    </div>

    <!-- 用药列表 -->
    <div class="px-4 mt-4">
      <div class="space-y-3">
        <div
          v-for="med in filteredMedications"
          :key="med.id"
          :class="[
            'card',
            med.taken ? 'bg-gray-50 opacity-75' : ''
          ]"
        >
          <div class="flex items-start">
            <!-- 药品图标 -->
            <div :class="[
              'w-14 h-14 rounded-2xl flex items-center justify-center mr-4 flex-shrink-0',
              med.taken ? 'bg-gray-200' : 'bg-primary-100'
            ]">
              <svg :class="['w-8 h-8', med.taken ? 'text-gray-500' : 'text-primary-600']" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>

            <!-- 药品信息 -->
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <h3 :class="['text-lg font-bold', med.taken ? 'text-gray-500' : 'text-gray-800']">
                  {{ med.name }}
                </h3>
                <span :class="[
                  'px-2 py-1 rounded-full text-sm',
                  med.taken ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                ]">
                  {{ med.taken ? '已服用' : '待服用' }}
                </span>
              </div>

              <div class="mt-2 flex items-center text-gray-500">
                <svg class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{{ med.time }}</span>
                <span class="mx-2">·</span>
                <span>{{ med.dosage }}</span>
              </div>

              <p class="text-sm text-gray-400 mt-1">{{ med.instruction }}</p>

              <!-- 操作按钮 -->
              <div class="mt-3 flex gap-2" v-if="!med.taken">
                <button
                  class="flex-1 py-2 bg-primary-500 text-white rounded-xl font-medium"
                  @click="takeMedication(med.id)"
                >
                  已服用
                </button>
                <button
                  class="px-4 py-2 border border-gray-300 text-gray-600 rounded-xl"
                  @click="skipMedication(med.id)"
                >
                  跳过
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="filteredMedications.length === 0" class="empty-state py-12">
        <svg class="w-20 h-20 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
        <p class="text-gray-500 text-lg">该时段没有用药安排</p>
      </div>
    </div>

    <!-- 用药历史 -->
    <div class="px-4 mt-6 mb-6">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">本周用药记录</h2>
        <div class="flex justify-between">
          <div v-for="day in weekRecord" :key="day.date" class="flex flex-col items-center">
            <span class="text-sm text-gray-500">{{ day.label }}</span>
            <div :class="[
              'w-10 h-10 rounded-full flex items-center justify-center mt-2',
              day.completed ? 'bg-green-100' : day.date === 'today' ? 'bg-primary-100' : 'bg-gray-100'
            ]">
              <svg v-if="day.completed" class="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <span v-else :class="day.date === 'today' ? 'text-primary-600' : 'text-gray-400'">{{ day.count }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const showAddModal = ref(false)
const activeFilter = ref('all')

const timeFilters = [
  { value: 'all', label: '全部' },
  { value: 'morning', label: '早晨' },
  { value: 'noon', label: '中午' },
  { value: 'evening', label: '晚上' },
  { value: 'night', label: '睡前' }
]

// 今日用药
const todayMedications = ref([
  {
    id: 1,
    name: '阿司匹林肠溶片',
    time: '08:00',
    period: 'morning',
    dosage: '1片',
    instruction: '饭后服用，用温水送服',
    taken: true
  },
  {
    id: 2,
    name: '氨氯地平片',
    time: '08:00',
    period: 'morning',
    dosage: '1片',
    instruction: '每日一次，可空腹服用',
    taken: true
  },
  {
    id: 3,
    name: '二甲双胍缓释片',
    time: '12:00',
    period: 'noon',
    dosage: '1片',
    instruction: '随餐服用，整片吞服',
    taken: false
  },
  {
    id: 4,
    name: '辛伐他汀片',
    time: '21:00',
    period: 'night',
    dosage: '1片',
    instruction: '睡前服用效果更佳',
    taken: false
  }
])

// 筛选后的用药
const filteredMedications = computed(() => {
  if (activeFilter.value === 'all') {
    return todayMedications.value
  }
  return todayMedications.value.filter(med => med.period === activeFilter.value)
})

// 完成数量
const completedCount = computed(() => {
  return todayMedications.value.filter(med => med.taken).length
})

// 本周记录
const weekRecord = ref([
  { label: '周一', date: 'mon', completed: true, count: 4 },
  { label: '周二', date: 'tue', completed: true, count: 4 },
  { label: '周三', date: 'wed', completed: true, count: 4 },
  { label: '周四', date: 'thu', completed: true, count: 4 },
  { label: '周五', date: 'fri', completed: false, count: 3 },
  { label: '周六', date: 'today', completed: false, count: 2 },
  { label: '周日', date: 'sun', completed: false, count: 0 }
])

// 服用药物
function takeMedication(id) {
  const med = todayMedications.value.find(m => m.id === id)
  if (med) {
    med.taken = true
    window.$toast?.success('已记录服药')
  }
}

// 跳过药物
function skipMedication(id) {
  window.$toast?.info('已跳过本次用药')
}
</script>
