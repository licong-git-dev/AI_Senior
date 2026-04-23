<template>
  <div class="min-h-screen bg-danger-50">
    <!-- 顶部返回 -->
    <div class="page-header bg-transparent">
      <router-link to="/" class="flex items-center text-gray-600">
        <svg class="w-6 h-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        返回
      </router-link>
    </div>

    <!-- 主内容 -->
    <div class="px-6 pt-4 pb-safe">
      <!-- SOS按钮 -->
      <div class="flex flex-col items-center py-8">
        <p class="text-xl text-gray-700 mb-8">遇到紧急情况？按下按钮呼救</p>

        <button
          :class="[
            'w-48 h-48 rounded-full flex flex-col items-center justify-center text-white shadow-xl transition-all duration-200',
            sosActive ? 'bg-danger-700 scale-95' : 'bg-danger-500 hover:bg-danger-600 active:scale-95'
          ]"
          @click="triggerSOS"
          :disabled="sosActive"
        >
          <svg class="w-20 h-20 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span class="text-2xl font-bold">{{ sosActive ? '呼救中...' : 'SOS' }}</span>
        </button>

        <p v-if="sosActive" class="text-danger-600 mt-6 text-lg animate-pulse">
          正在通知紧急联系人...
        </p>

        <button
          v-if="sosActive"
          class="mt-4 px-6 py-3 border-2 border-danger-500 text-danger-600 rounded-xl"
          @click="cancelSOS"
        >
          取消呼救
        </button>
      </div>

      <!-- 紧急联系人 -->
      <div class="card mt-8">
        <h2 class="text-lg font-bold text-gray-800 mb-4">紧急联系人</h2>

        <div class="space-y-3">
          <div
            v-for="contact in contacts"
            :key="contact.id"
            class="flex items-center justify-between p-3 bg-gray-50 rounded-xl"
          >
            <div class="flex items-center">
              <div class="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-bold">
                {{ contact.name.charAt(0) }}
              </div>
              <div class="ml-3">
                <p class="font-medium text-gray-800">{{ contact.name }}</p>
                <p class="text-sm text-gray-500">{{ contact.relation }}</p>
              </div>
            </div>
            <a
              :href="`tel:${contact.phone}`"
              class="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center text-white"
            >
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </a>
          </div>
        </div>
      </div>

      <!-- 快捷拨号 -->
      <div class="card mt-4">
        <h2 class="text-lg font-bold text-gray-800 mb-4">紧急号码</h2>

        <div class="grid grid-cols-3 gap-3">
          <a
            v-for="number in emergencyNumbers"
            :key="number.number"
            :href="`tel:${number.number}`"
            class="flex flex-col items-center p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <span class="text-2xl font-bold text-danger-600">{{ number.number }}</span>
            <span class="text-sm text-gray-600 mt-1">{{ number.label }}</span>
          </a>
        </div>
      </div>

      <!-- 安全提示 -->
      <div class="alert alert-warning mt-4">
        <svg class="w-6 h-6 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
          <p class="font-medium">安全提示</p>
          <p class="text-sm mt-1">按下SOS按钮后，系统会自动通知您的所有紧急联系人，并发送您的位置信息。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { emergencyApi } from '@api/index'

const sosActive = ref(false)
let sosAlertId = null

// 紧急联系人
const contacts = ref([
  { id: 1, name: '张小明', relation: '儿子', phone: '13800138001' },
  { id: 2, name: '李小红', relation: '女儿', phone: '13800138002' }
])

// 紧急号码
const emergencyNumbers = [
  { number: '120', label: '急救' },
  { number: '110', label: '报警' },
  { number: '119', label: '火警' }
]

// 触发SOS
async function triggerSOS() {
  if (sosActive.value) return

  sosActive.value = true

  try {
    // 获取位置
    let location = null
    if (navigator.geolocation) {
      try {
        const pos = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 })
        })
        location = `${pos.coords.latitude},${pos.coords.longitude}`
      } catch (e) {
        console.log('无法获取位置')
      }
    }

    const response = await emergencyApi.triggerSOS(location)
    sosAlertId = response.alert_id

    window.$toast?.success('已通知紧急联系人')
  } catch (error) {
    console.error('SOS触发失败:', error)
    window.$toast?.error('呼救发送失败，请直接拨打电话')
  }
}

// 取消SOS
async function cancelSOS() {
  if (!sosActive.value) return

  try {
    if (sosAlertId) {
      await emergencyApi.cancelSOS(sosAlertId)
    }
    sosActive.value = false
    sosAlertId = null
    window.$toast?.info('已取消呼救')
  } catch (error) {
    console.error('取消失败:', error)
  }
}
</script>
