<template>
  <span
    :class="[
      'inline-flex items-center font-medium rounded-full',
      sizeClasses[size],
      variantClasses[variant],
      clickable ? 'cursor-pointer hover:opacity-80' : ''
    ]"
    @click="handleClick"
  >
    <!-- 圆点 -->
    <span
      v-if="dot"
      :class="['rounded-full mr-1.5', dotSizeClasses[size], dotColorClasses[variant]]"
    ></span>

    <!-- 图标 -->
    <component v-if="icon" :is="icon" :class="['mr-1', iconSizeClasses[size]]" />

    <!-- 内容 -->
    <slot>{{ text }}</slot>

    <!-- 关闭按钮 -->
    <button
      v-if="closable"
      class="ml-1 hover:opacity-70"
      @click.stop="$emit('close')"
    >
      <svg :class="iconSizeClasses[size]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </span>
</template>

<script setup>
defineProps({
  text: String,
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'primary', 'success', 'warning', 'danger', 'info'].includes(v)
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  },
  dot: Boolean,
  icon: Object,
  closable: Boolean,
  clickable: Boolean
})

const emit = defineEmits(['click', 'close'])

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base'
}

const variantClasses = {
  default: 'bg-gray-100 text-gray-700',
  primary: 'bg-primary-100 text-primary-700',
  success: 'bg-success-100 text-success-700',
  warning: 'bg-warning-100 text-warning-700',
  danger: 'bg-danger-100 text-danger-700',
  info: 'bg-blue-100 text-blue-700'
}

const dotSizeClasses = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
  lg: 'w-2.5 h-2.5'
}

const dotColorClasses = {
  default: 'bg-gray-500',
  primary: 'bg-primary-500',
  success: 'bg-success-500',
  warning: 'bg-warning-500',
  danger: 'bg-danger-500',
  info: 'bg-blue-500'
}

const iconSizeClasses = {
  sm: 'w-3 h-3',
  md: 'w-4 h-4',
  lg: 'w-5 h-5'
}

function handleClick(e) {
  emit('click', e)
}
</script>
