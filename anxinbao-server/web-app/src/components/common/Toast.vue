<template>
  <Transition name="toast">
    <div
      v-if="visible"
      class="fixed top-4 left-1/2 -translate-x-1/2 z-[100] max-w-sm w-full mx-4"
    >
      <div
        :class="[
          'p-4 rounded-2xl shadow-lg flex items-center gap-3',
          typeClasses[type]
        ]"
      >
        <!-- 图标 -->
        <div class="flex-shrink-0">
          <component :is="icons[type]" class="w-6 h-6" />
        </div>

        <!-- 内容 -->
        <div class="flex-1 min-w-0">
          <p class="font-medium text-lg">{{ message }}</p>
        </div>

        <!-- 关闭按钮 -->
        <button
          @click="hide"
          class="flex-shrink-0 p-1 rounded-full hover:bg-black/10 transition-colors"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, h, onMounted, onUnmounted } from 'vue'

// 状态
const visible = ref(false)
const message = ref('')
const type = ref('info')
let timer = null

// 样式配置
const typeClasses = {
  success: 'bg-green-500 text-white',
  error: 'bg-red-500 text-white',
  warning: 'bg-yellow-500 text-white',
  info: 'bg-blue-500 text-white'
}

// 图标组件
const icons = {
  success: {
    render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M5 13l4 4L19 7' })
    ])
  },
  error: {
    render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M6 18L18 6M6 6l12 12' })
    ])
  },
  warning: {
    render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' })
    ])
  },
  info: {
    render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' })
    ])
  }
}

// 显示Toast
function show(msg, toastType = 'info', duration = 3000) {
  message.value = msg
  type.value = toastType
  visible.value = true

  clearTimeout(timer)
  timer = setTimeout(() => {
    hide()
  }, duration)
}

// 隐藏Toast
function hide() {
  visible.value = false
}

// 全局挂载
onMounted(() => {
  window.$toast = {
    show,
    success: (msg, duration) => show(msg, 'success', duration),
    error: (msg, duration) => show(msg, 'error', duration),
    warning: (msg, duration) => show(msg, 'warning', duration),
    info: (msg, duration) => show(msg, 'info', duration)
  }
})

onUnmounted(() => {
  clearTimeout(timer)
})
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -20px);
}
</style>
