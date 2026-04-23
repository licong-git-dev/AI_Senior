<template>
  <div>
    <!-- 标签头 -->
    <div
      :class="[
        'flex',
        type === 'line' ? 'border-b border-gray-200' : '',
        type === 'card' ? 'bg-gray-100 p-1 rounded-xl' : '',
        type === 'pill' ? 'gap-2' : ''
      ]"
    >
      <button
        v-for="tab in tabs"
        :key="tab.value"
        :class="[
          'transition-all font-medium',
          tabClasses,
          modelValue === tab.value ? activeClasses : inactiveClasses,
          tab.disabled ? 'opacity-50 cursor-not-allowed' : ''
        ]"
        :disabled="tab.disabled"
        @click="selectTab(tab)"
      >
        <!-- 图标 -->
        <component v-if="tab.icon" :is="tab.icon" class="w-5 h-5 mr-2" />

        <!-- 标签文字 -->
        {{ tab.label }}

        <!-- 徽章 -->
        <span
          v-if="tab.badge"
          class="ml-2 px-2 py-0.5 text-xs rounded-full bg-danger-500 text-white"
        >
          {{ tab.badge }}
        </span>
      </button>
    </div>

    <!-- 内容区 -->
    <div class="mt-4">
      <slot :name="modelValue" />
      <slot />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: [String, Number],
  tabs: {
    type: Array,
    required: true
    // 每个tab: { value, label, icon?, badge?, disabled? }
  },
  type: {
    type: String,
    default: 'line',
    validator: (v) => ['line', 'card', 'pill'].includes(v)
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const sizeClasses = {
  sm: 'px-3 py-2 text-sm',
  md: 'px-4 py-3 text-base',
  lg: 'px-6 py-4 text-lg'
}

const tabClasses = computed(() => {
  const base = sizeClasses[props.size] + ' flex items-center'

  if (props.type === 'line') {
    return base + ' border-b-2 -mb-px'
  }
  if (props.type === 'card') {
    return base + ' rounded-lg'
  }
  if (props.type === 'pill') {
    return base + ' rounded-full'
  }
  return base
})

const activeClasses = computed(() => {
  if (props.type === 'line') {
    return 'border-primary-500 text-primary-600'
  }
  if (props.type === 'card') {
    return 'bg-white shadow text-primary-600'
  }
  if (props.type === 'pill') {
    return 'bg-primary-500 text-white'
  }
  return ''
})

const inactiveClasses = computed(() => {
  if (props.type === 'line') {
    return 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
  }
  if (props.type === 'card') {
    return 'text-gray-500 hover:text-gray-700'
  }
  if (props.type === 'pill') {
    return 'bg-gray-100 text-gray-600 hover:bg-gray-200'
  }
  return ''
})

function selectTab(tab) {
  if (!tab.disabled) {
    emit('update:modelValue', tab.value)
    emit('change', tab)
  }
}
</script>
