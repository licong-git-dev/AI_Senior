<template>
  <div class="relative">
    <!-- 标签 -->
    <label v-if="label" class="block text-gray-700 font-medium mb-2">
      {{ label }}
      <span v-if="required" class="text-danger-500">*</span>
    </label>

    <!-- 选择框 -->
    <div class="relative">
      <button
        type="button"
        :class="[
          'w-full flex items-center justify-between px-4 py-3 bg-white border-2 rounded-xl text-left transition-colors',
          isOpen ? 'border-primary-500 ring-2 ring-primary-100' : 'border-gray-200',
          disabled ? 'bg-gray-100 cursor-not-allowed' : 'hover:border-primary-300',
          sizeClasses[size]
        ]"
        :disabled="disabled"
        @click="toggle"
      >
        <span :class="selectedOption ? 'text-gray-800' : 'text-gray-400'">
          {{ selectedOption?.label || placeholder }}
        </span>
        <svg
          :class="['w-5 h-5 text-gray-400 transition-transform', { 'rotate-180': isOpen }]"
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <!-- 下拉选项 -->
      <Transition name="dropdown">
        <div
          v-if="isOpen"
          class="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden"
        >
          <!-- 搜索框 -->
          <div v-if="searchable" class="p-2 border-b border-gray-100">
            <input
              v-model="searchQuery"
              type="text"
              class="w-full px-3 py-2 border border-gray-200 rounded-lg text-base focus:outline-none focus:border-primary-500"
              placeholder="搜索..."
              @click.stop
            />
          </div>

          <!-- 选项列表 -->
          <div class="max-h-60 overflow-y-auto">
            <button
              v-for="option in filteredOptions"
              :key="option.value"
              type="button"
              :class="[
                'w-full px-4 py-3 text-left hover:bg-primary-50 transition-colors flex items-center justify-between',
                option.value === modelValue ? 'bg-primary-50 text-primary-600' : 'text-gray-700'
              ]"
              @click="select(option)"
            >
              <span>{{ option.label }}</span>
              <svg
                v-if="option.value === modelValue"
                class="w-5 h-5 text-primary-500"
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </button>

            <div v-if="filteredOptions.length === 0" class="px-4 py-3 text-gray-400 text-center">
              暂无选项
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- 错误提示 -->
    <p v-if="error" class="mt-2 text-danger-500 text-sm">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: [String, Number],
  options: {
    type: Array,
    default: () => []
  },
  label: String,
  placeholder: {
    type: String,
    default: '请选择'
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  },
  disabled: Boolean,
  required: Boolean,
  searchable: Boolean,
  error: String
})

const emit = defineEmits(['update:modelValue', 'change'])

const isOpen = ref(false)
const searchQuery = ref('')

const sizeClasses = {
  sm: 'text-base min-h-[40px]',
  md: 'text-lg min-h-[48px]',
  lg: 'text-xl min-h-[56px]'
}

const selectedOption = computed(() => {
  return props.options.find(opt => opt.value === props.modelValue)
})

const filteredOptions = computed(() => {
  if (!searchQuery.value) return props.options
  const query = searchQuery.value.toLowerCase()
  return props.options.filter(opt => opt.label.toLowerCase().includes(query))
})

function toggle() {
  if (!props.disabled) {
    isOpen.value = !isOpen.value
  }
}

function select(option) {
  emit('update:modelValue', option.value)
  emit('change', option)
  isOpen.value = false
  searchQuery.value = ''
}

function handleClickOutside(e) {
  if (!e.target.closest('.relative')) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
