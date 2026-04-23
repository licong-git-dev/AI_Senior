<template>
  <div class="relative">
    <label v-if="label" :for="id" class="label">
      {{ label }}
      <span v-if="required" class="text-danger-500 ml-1">*</span>
    </label>

    <div class="relative">
      <!-- 前置图标 -->
      <div v-if="prefixIcon" class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
        <component :is="prefixIcon" class="w-6 h-6" />
      </div>

      <input
        :id="id"
        :type="inputType"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :class="[
          'input',
          prefixIcon ? 'pl-12' : '',
          suffixIcon || type === 'password' ? 'pr-12' : '',
          error ? 'input-error' : ''
        ]"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
      />

      <!-- 后置图标/密码切换 -->
      <div
        v-if="suffixIcon || type === 'password'"
        class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 cursor-pointer"
        @click="togglePassword"
      >
        <component v-if="suffixIcon" :is="suffixIcon" class="w-6 h-6" />
        <svg v-else-if="type === 'password'" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path v-if="showPassword" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path v-if="!showPassword" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
      </div>
    </div>

    <!-- 错误提示 -->
    <p v-if="error" class="mt-2 text-base text-danger-500">
      {{ error }}
    </p>

    <!-- 提示信息 -->
    <p v-else-if="hint" class="mt-2 text-base text-gray-500">
      {{ hint }}
    </p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: [String, Number],
  type: {
    type: String,
    default: 'text'
  },
  label: String,
  placeholder: String,
  hint: String,
  error: String,
  disabled: Boolean,
  readonly: Boolean,
  required: Boolean,
  prefixIcon: Object,
  suffixIcon: Object,
  id: {
    type: String,
    default: () => `input-${Math.random().toString(36).substr(2, 9)}`
  }
})

const emit = defineEmits(['update:modelValue', 'focus', 'blur'])

const showPassword = ref(false)

const inputType = computed(() => {
  if (props.type === 'password') {
    return showPassword.value ? 'text' : 'password'
  }
  return props.type
})

function handleInput(e) {
  emit('update:modelValue', e.target.value)
}

function handleFocus(e) {
  emit('focus', e)
}

function handleBlur(e) {
  emit('blur', e)
}

function togglePassword() {
  if (props.type === 'password') {
    showPassword.value = !showPassword.value
  }
}
</script>
