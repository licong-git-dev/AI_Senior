<template>
  <div
    :class="[
      'bg-white rounded-2xl transition-all',
      shadow ? 'shadow-soft' : '',
      hoverable ? 'hover:shadow-lg hover:-translate-y-1 cursor-pointer' : '',
      bordered ? 'border border-gray-100' : '',
      padding ? paddingClasses[padding] : ''
    ]"
    @click="handleClick"
  >
    <!-- 头部 -->
    <div
      v-if="title || $slots.header"
      :class="[
        'flex items-center justify-between',
        padding ? 'px-6 pt-6 pb-4' : '',
        headerBorder ? 'border-b border-gray-100 pb-4 mb-4' : ''
      ]"
    >
      <slot name="header">
        <div>
          <h3 class="text-lg font-bold text-gray-800">{{ title }}</h3>
          <p v-if="subtitle" class="text-sm text-gray-500 mt-1">{{ subtitle }}</p>
        </div>
      </slot>
      <slot name="header-action">
        <button v-if="actionText" class="text-primary-500 text-sm font-medium" @click.stop="$emit('action')">
          {{ actionText }}
        </button>
      </slot>
    </div>

    <!-- 内容 -->
    <div :class="padding && !title && !$slots.header ? paddingClasses[padding] : (padding ? 'px-6 pb-6' : '')">
      <slot />
    </div>

    <!-- 底部 -->
    <div
      v-if="$slots.footer"
      :class="[
        padding ? 'px-6 pb-6 pt-4' : '',
        footerBorder ? 'border-t border-gray-100 mt-4 pt-4' : ''
      ]"
    >
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  subtitle: String,
  actionText: String,
  shadow: {
    type: Boolean,
    default: true
  },
  hoverable: Boolean,
  bordered: Boolean,
  headerBorder: Boolean,
  footerBorder: Boolean,
  padding: {
    type: String,
    default: 'md',
    validator: (v) => ['none', 'sm', 'md', 'lg'].includes(v)
  }
})

const emit = defineEmits(['click', 'action'])

const paddingClasses = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8'
}

function handleClick(e) {
  emit('click', e)
}
</script>
