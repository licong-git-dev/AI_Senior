<template>
  <div id="anxinbao-app" class="min-h-screen bg-surface">
    <!-- 加载状态 -->
    <div v-if="isLoading" class="fixed inset-0 bg-white flex items-center justify-center z-50">
      <div class="text-center">
        <div class="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-lg text-gray-600">正在加载...</p>
      </div>
    </div>

    <!-- 主内容 -->
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>

    <!-- 全局消息提示 -->
    <Teleport to="body">
      <Toast />
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, provide } from 'vue'
import { useUserStore } from '@stores/user'
import Toast from '@components/common/Toast.vue'

const isLoading = ref(true)
const userStore = useUserStore()

// 提供全局状态
provide('userStore', userStore)

onMounted(async () => {
  // 检查登录状态
  try {
    await userStore.checkAuth()
  } catch (error) {
    console.log('未登录或token过期')
  } finally {
    isLoading.value = false
  }
})
</script>

<style>
/* 页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 滑动过渡动画 */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from {
  transform: translateX(100%);
}

.slide-leave-to {
  transform: translateX(-100%);
}
</style>
