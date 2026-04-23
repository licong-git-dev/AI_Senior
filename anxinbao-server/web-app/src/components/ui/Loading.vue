<template>
  <div
    v-if="visible"
    :class="[
      'flex items-center justify-center',
      fullscreen ? 'fixed inset-0 bg-white/80 backdrop-blur-sm z-50' : '',
      center ? 'flex-col' : ''
    ]"
  >
    <!-- 加载动画 -->
    <div :class="['relative', spinnerSizeClasses[size]]">
      <!-- 圆形加载器 -->
      <svg
        v-if="type === 'spinner'"
        class="animate-spin"
        :class="spinnerSizeClasses[size]"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
          :class="colorClasses[color]"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          :class="fillColorClasses[color]"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>

      <!-- 点状加载器 -->
      <div v-else-if="type === 'dots'" class="flex space-x-1">
        <div
          v-for="i in 3"
          :key="i"
          :class="[
            'rounded-full animate-bounce',
            dotSizeClasses[size],
            fillColorClasses[color]
          ]"
          :style="{ animationDelay: `${(i - 1) * 0.1}s` }"
        ></div>
      </div>

      <!-- 脉冲加载器 -->
      <div
        v-else-if="type === 'pulse'"
        :class="[
          'rounded-full animate-pulse',
          pulseSizeClasses[size],
          fillColorClasses[color]
        ]"
      ></div>
    </div>

    <!-- 提示文字 -->
    <p
      v-if="text"
      :class="[
        'text-gray-600',
        center ? 'mt-4' : 'ml-3',
        textSizeClasses[size]
      ]"
    >
      {{ text }}
    </p>
  </div>
</template>

<script setup>
defineProps({
  visible: {
    type: Boolean,
    default: true
  },
  type: {
    type: String,
    default: 'spinner',
    validator: (v) => ['spinner', 'dots', 'pulse'].includes(v)
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg', 'xl'].includes(v)
  },
  color: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'white', 'gray'].includes(v)
  },
  text: String,
  fullscreen: Boolean,
  center: Boolean
})

const spinnerSizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12'
}

const dotSizeClasses = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
  lg: 'w-3 h-3',
  xl: 'w-4 h-4'
}

const pulseSizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12'
}

const colorClasses = {
  primary: 'stroke-primary-200',
  secondary: 'stroke-secondary-200',
  white: 'stroke-white/30',
  gray: 'stroke-gray-200'
}

const fillColorClasses = {
  primary: 'bg-primary-500 fill-primary-500',
  secondary: 'bg-secondary-500 fill-secondary-500',
  white: 'bg-white fill-white',
  gray: 'bg-gray-500 fill-gray-500'
}

const textSizeClasses = {
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
  xl: 'text-xl'
}
</script>
