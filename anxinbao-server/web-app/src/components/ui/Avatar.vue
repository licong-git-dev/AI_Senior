<template>
  <div
    :class="[
      'relative inline-flex items-center justify-center flex-shrink-0 rounded-full overflow-hidden',
      sizeClasses[size],
      bordered ? 'ring-2 ring-white' : ''
    ]"
  >
    <!-- 图片 -->
    <img
      v-if="src && !imageError"
      :src="src"
      :alt="alt"
      class="w-full h-full object-cover"
      @error="imageError = true"
    />

    <!-- 占位符 -->
    <div
      v-else
      :class="[
        'w-full h-full flex items-center justify-center',
        bgColorClasses[color]
      ]"
    >
      <!-- 文字 -->
      <span v-if="text" :class="['font-bold text-white', textSizeClasses[size]]">
        {{ displayText }}
      </span>

      <!-- 图标 -->
      <svg v-else :class="['text-white', iconSizeClasses[size]]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    </div>

    <!-- 状态指示器 -->
    <span
      v-if="status"
      :class="[
        'absolute bottom-0 right-0 rounded-full ring-2 ring-white',
        statusSizeClasses[size],
        statusColorClasses[status]
      ]"
    ></span>

    <!-- 徽章 -->
    <span
      v-if="badge"
      class="absolute -top-1 -right-1 px-1.5 py-0.5 text-xs font-bold text-white bg-danger-500 rounded-full min-w-[18px] text-center"
    >
      {{ badge > 99 ? '99+' : badge }}
    </span>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  src: String,
  alt: {
    type: String,
    default: ''
  },
  text: String,
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['xs', 'sm', 'md', 'lg', 'xl', '2xl'].includes(v)
  },
  color: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'success', 'warning', 'danger', 'gray'].includes(v)
  },
  status: {
    type: String,
    validator: (v) => ['online', 'offline', 'busy', 'away'].includes(v)
  },
  badge: [Number, String],
  bordered: Boolean
})

const imageError = ref(false)

const displayText = computed(() => {
  if (!props.text) return ''
  return props.text.charAt(0).toUpperCase()
})

const sizeClasses = {
  xs: 'w-6 h-6',
  sm: 'w-8 h-8',
  md: 'w-10 h-10',
  lg: 'w-12 h-12',
  xl: 'w-16 h-16',
  '2xl': 'w-20 h-20'
}

const textSizeClasses = {
  xs: 'text-xs',
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
  xl: 'text-2xl',
  '2xl': 'text-3xl'
}

const iconSizeClasses = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
  xl: 'w-8 h-8',
  '2xl': 'w-10 h-10'
}

const bgColorClasses = {
  primary: 'bg-primary-500',
  secondary: 'bg-secondary-500',
  success: 'bg-success-500',
  warning: 'bg-warning-500',
  danger: 'bg-danger-500',
  gray: 'bg-gray-400'
}

const statusSizeClasses = {
  xs: 'w-1.5 h-1.5',
  sm: 'w-2 h-2',
  md: 'w-2.5 h-2.5',
  lg: 'w-3 h-3',
  xl: 'w-3.5 h-3.5',
  '2xl': 'w-4 h-4'
}

const statusColorClasses = {
  online: 'bg-success-500',
  offline: 'bg-gray-400',
  busy: 'bg-danger-500',
  away: 'bg-warning-500'
}
</script>
