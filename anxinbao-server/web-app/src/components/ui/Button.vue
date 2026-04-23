<template>
  <button
    :class="[
      'btn',
      sizeClasses[size],
      variantClasses[variant],
      { 'w-full': block, 'opacity-50 cursor-not-allowed': disabled || loading }
    ]"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <!-- 加载动画 -->
    <span v-if="loading" class="loading-spinner mr-2"></span>

    <!-- 图标 -->
    <span v-if="icon && !loading" class="mr-2">
      <component :is="icon" class="w-6 h-6" />
    </span>

    <!-- 内容 -->
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'danger', 'outline', 'ghost'].includes(v)
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg', 'xl'].includes(v)
  },
  block: Boolean,
  disabled: Boolean,
  loading: Boolean,
  icon: Object
})

const emit = defineEmits(['click'])

const sizeClasses = {
  sm: 'px-4 py-2 text-base min-h-[40px]',
  md: 'px-6 py-3 text-lg min-h-[48px]',
  lg: 'px-8 py-4 text-xl min-h-[56px]',
  xl: 'px-10 py-5 text-2xl min-h-[64px]'
}

const variantClasses = {
  primary: 'bg-primary-500 text-white hover:bg-primary-600 focus:ring-primary-300 shadow-soft',
  secondary: 'bg-secondary-500 text-white hover:bg-secondary-600 focus:ring-secondary-300',
  danger: 'bg-danger-500 text-white hover:bg-danger-600 focus:ring-danger-300',
  outline: 'border-2 border-primary-500 text-primary-600 bg-white hover:bg-primary-50',
  ghost: 'text-gray-600 bg-transparent hover:bg-gray-100'
}

function handleClick(e) {
  if (!props.disabled && !props.loading) {
    emit('click', e)
  }
}
</script>
