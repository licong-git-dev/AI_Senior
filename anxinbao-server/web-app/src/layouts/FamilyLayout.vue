<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 顶部导航 -->
    <header class="bg-white shadow-sm sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="flex items-center justify-between h-16">
          <!-- Logo -->
          <div class="flex items-center">
            <div class="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </div>
            <span class="ml-3 text-xl font-bold text-gray-800">安心宝 · 家属端</span>
          </div>

          <!-- 导航菜单 -->
          <nav class="hidden md:flex items-center space-x-1">
            <router-link
              v-for="item in navItems"
              :key="item.path"
              :to="item.path"
              :class="[
                'px-4 py-2 rounded-lg font-medium transition-colors',
                isActive(item.path)
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-600 hover:bg-gray-100'
              ]"
            >
              {{ item.label }}
            </router-link>
          </nav>

          <!-- 右侧操作 -->
          <div class="flex items-center space-x-4">
            <!-- 紧急通知 -->
            <button class="relative p-2 text-gray-500 hover:bg-gray-100 rounded-lg">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <span v-if="hasAlert" class="absolute top-1 right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
            </button>

            <!-- 用户菜单 -->
            <div class="relative">
              <button
                class="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100"
                @click="showUserMenu = !showUserMenu"
              >
                <div class="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-bold">
                  {{ userInitial }}
                </div>
                <span class="hidden sm:block text-gray-700">{{ userName }}</span>
                <svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              <!-- 下拉菜单 -->
              <div
                v-if="showUserMenu"
                class="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg py-2 z-50"
              >
                <router-link to="/family/settings" class="block px-4 py-2 text-gray-700 hover:bg-gray-100">
                  设置
                </router-link>
                <button @click="handleLogout" class="w-full text-left px-4 py-2 text-red-600 hover:bg-gray-100">
                  退出登录
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 移动端导航 -->
      <div class="md:hidden border-t border-gray-100">
        <div class="flex overflow-x-auto px-4 py-2 space-x-1">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            :class="[
              'px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-colors',
              isActive(item.path)
                ? 'bg-primary-50 text-primary-600'
                : 'text-gray-600'
            ]"
          >
            {{ item.label }}
          </router-link>
        </div>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 py-6">
      <router-view />
    </main>

    <!-- 紧急警报弹窗 -->
    <div v-if="sosAlert" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="bg-white rounded-2xl p-6 max-w-md mx-4 animate-bounce-in">
        <div class="text-center">
          <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-12 h-12 text-red-600 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 class="text-2xl font-bold text-red-600 mb-2">紧急求助!</h2>
          <p class="text-gray-600 mb-4">{{ sosAlert.elderName }} 发起了紧急求助</p>
          <p class="text-sm text-gray-500 mb-6">{{ sosAlert.time }} · {{ sosAlert.location || '位置获取中...' }}</p>
          <div class="flex gap-3">
            <a
              :href="`tel:${sosAlert.elderPhone}`"
              class="flex-1 py-3 bg-green-500 text-white rounded-xl font-medium"
            >
              立即拨打电话
            </a>
            <button
              @click="dismissAlert"
              class="px-6 py-3 border border-gray-300 text-gray-700 rounded-xl"
            >
              知道了
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const showUserMenu = ref(false)
const hasAlert = ref(true)
const sosAlert = ref(null)

const userName = computed(() => userStore.userName)
const userInitial = computed(() => userName.value.charAt(0))

const navItems = [
  { path: '/family', label: '监护首页' },
  { path: '/family/monitor', label: '实时监护' },
  { path: '/family/health', label: '健康数据' },
  { path: '/family/alerts', label: '告警记录' },
  { path: '/family/messages', label: '消息' }
]

function isActive(path) {
  if (path === '/family') {
    return route.path === '/family'
  }
  return route.path.startsWith(path)
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

function dismissAlert() {
  sosAlert.value = null
}

// 模拟接收SOS警报
// setTimeout(() => {
//   sosAlert.value = {
//     elderName: '王爷爷',
//     elderPhone: '13800138000',
//     time: '刚刚',
//     location: '北京市朝阳区xxx小区'
//   }
// }, 3000)
</script>

<style scoped>
@keyframes bounce-in {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.animate-bounce-in {
  animation: bounce-in 0.3s ease-out;
}
</style>
