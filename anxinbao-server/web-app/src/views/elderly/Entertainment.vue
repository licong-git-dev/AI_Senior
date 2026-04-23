<template>
  <div class="min-h-screen pb-20">
    <!-- 页头 -->
    <div class="page-header">
      <h1 class="page-title">娱乐休闲</h1>
    </div>

    <!-- 分类标签 -->
    <div class="px-4 pt-4">
      <div class="flex gap-2 overflow-x-auto pb-2">
        <button
          v-for="cat in categories"
          :key="cat.value"
          :class="[
            'px-5 py-2 rounded-full whitespace-nowrap transition-colors text-lg',
            activeCategory === cat.value
              ? 'bg-primary-500 text-white'
              : 'bg-gray-100 text-gray-600'
          ]"
          @click="activeCategory = cat.value"
        >
          {{ cat.label }}
        </button>
      </div>
    </div>

    <!-- 音乐板块 -->
    <div v-if="activeCategory === 'music'" class="px-4 mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">推荐音乐</h2>
        <div class="space-y-3">
          <div
            v-for="song in musicList"
            :key="song.id"
            class="flex items-center p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer"
            @click="playSong(song)"
          >
            <div class="w-14 h-14 bg-primary-100 rounded-xl flex items-center justify-center mr-4">
              <svg class="w-8 h-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
            </div>
            <div class="flex-1">
              <h3 class="font-bold text-gray-800">{{ song.title }}</h3>
              <p class="text-sm text-gray-500">{{ song.artist }}</p>
            </div>
            <button class="w-12 h-12 bg-primary-500 rounded-full flex items-center justify-center text-white">
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 戏曲专区 -->
      <div class="card mt-4">
        <h2 class="text-lg font-bold text-gray-800 mb-4">戏曲专区</h2>
        <div class="grid grid-cols-2 gap-3">
          <div
            v-for="opera in operaList"
            :key="opera.id"
            class="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-4 cursor-pointer"
            @click="playOpera(opera)"
          >
            <div class="w-12 h-12 bg-red-200 rounded-xl flex items-center justify-center mb-3">
              <svg class="w-7 h-7 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
            </div>
            <h3 class="font-bold text-gray-800">{{ opera.title }}</h3>
            <p class="text-sm text-gray-500 mt-1">{{ opera.type }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 视频板块 -->
    <div v-if="activeCategory === 'video'" class="px-4 mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">热门视频</h2>
        <div class="space-y-4">
          <div
            v-for="video in videoList"
            :key="video.id"
            class="rounded-xl overflow-hidden bg-gray-100 cursor-pointer"
            @click="playVideo(video)"
          >
            <div class="relative aspect-video bg-gray-200 flex items-center justify-center">
              <div class="absolute inset-0 bg-black/30 flex items-center justify-center">
                <div class="w-16 h-16 bg-white/90 rounded-full flex items-center justify-center">
                  <svg class="w-8 h-8 text-primary-600 ml-1" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z"/>
                  </svg>
                </div>
              </div>
              <span class="absolute bottom-2 right-2 bg-black/70 text-white text-sm px-2 py-1 rounded">
                {{ video.duration }}
              </span>
            </div>
            <div class="p-3">
              <h3 class="font-bold text-gray-800">{{ video.title }}</h3>
              <p class="text-sm text-gray-500 mt-1">{{ video.views }}次播放</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 游戏板块 -->
    <div v-if="activeCategory === 'game'" class="px-4 mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">益智游戏</h2>
        <div class="grid grid-cols-2 gap-4">
          <div
            v-for="game in gameList"
            :key="game.id"
            class="bg-gray-50 rounded-2xl p-4 text-center cursor-pointer hover:bg-gray-100 transition-colors"
            @click="playGame(game)"
          >
            <div :class="['w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-3', game.bgColor]">
              <component :is="game.icon" :class="['w-10 h-10', game.iconColor]" />
            </div>
            <h3 class="font-bold text-gray-800">{{ game.name }}</h3>
            <p class="text-sm text-gray-500 mt-1">{{ game.desc }}</p>
          </div>
        </div>
      </div>

      <!-- 每日挑战 -->
      <div class="card mt-4">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-800">每日挑战</h2>
          <span class="text-sm text-primary-500">已完成 2/3</span>
        </div>
        <div class="space-y-3">
          <div class="flex items-center p-3 bg-green-50 rounded-xl">
            <div class="w-10 h-10 bg-green-200 rounded-full flex items-center justify-center mr-3">
              <svg class="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div class="flex-1">
              <p class="font-medium text-gray-800">完成一局数独</p>
              <p class="text-sm text-gray-500">+10积分</p>
            </div>
            <span class="text-green-600">已完成</span>
          </div>
          <div class="flex items-center p-3 bg-green-50 rounded-xl">
            <div class="w-10 h-10 bg-green-200 rounded-full flex items-center justify-center mr-3">
              <svg class="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div class="flex-1">
              <p class="font-medium text-gray-800">听三首歌曲</p>
              <p class="text-sm text-gray-500">+5积分</p>
            </div>
            <span class="text-green-600">已完成</span>
          </div>
          <div class="flex items-center p-3 bg-yellow-50 rounded-xl">
            <div class="w-10 h-10 bg-yellow-200 rounded-full flex items-center justify-center mr-3">
              <span class="text-yellow-600 font-bold">3</span>
            </div>
            <div class="flex-1">
              <p class="font-medium text-gray-800">完成记忆翻牌</p>
              <p class="text-sm text-gray-500">+15积分</p>
            </div>
            <button class="px-4 py-2 bg-primary-500 text-white rounded-xl text-sm">去完成</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 阅读板块 -->
    <div v-if="activeCategory === 'read'" class="px-4 mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">今日推荐</h2>
        <div class="space-y-4">
          <div
            v-for="article in articleList"
            :key="article.id"
            class="flex items-start p-3 bg-gray-50 rounded-xl cursor-pointer hover:bg-gray-100 transition-colors"
            @click="readArticle(article)"
          >
            <div class="w-24 h-20 bg-gray-200 rounded-lg mr-4 flex-shrink-0"></div>
            <div class="flex-1">
              <h3 class="font-bold text-gray-800 line-clamp-2">{{ article.title }}</h3>
              <div class="flex items-center mt-2 text-sm text-gray-500">
                <span>{{ article.category }}</span>
                <span class="mx-2">·</span>
                <span>{{ article.readTime }}分钟阅读</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 有声书 -->
      <div class="card mt-4 mb-6">
        <h2 class="text-lg font-bold text-gray-800 mb-4">有声书</h2>
        <div class="grid grid-cols-3 gap-3">
          <div
            v-for="book in audioBookList"
            :key="book.id"
            class="text-center cursor-pointer"
            @click="playAudioBook(book)"
          >
            <div class="aspect-[3/4] bg-gradient-to-b from-amber-100 to-amber-200 rounded-xl flex items-center justify-center mb-2">
              <svg class="w-10 h-10 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <p class="text-sm font-medium text-gray-800 line-clamp-2">{{ book.title }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, h } from 'vue'

const activeCategory = ref('music')

const categories = [
  { value: 'music', label: '音乐' },
  { value: 'video', label: '视频' },
  { value: 'game', label: '游戏' },
  { value: 'read', label: '阅读' }
]

// 音乐列表
const musicList = ref([
  { id: 1, title: '月亮代表我的心', artist: '邓丽君' },
  { id: 2, title: '甜蜜蜜', artist: '邓丽君' },
  { id: 3, title: '夕阳红', artist: '佟铁鑫' },
  { id: 4, title: '军港之夜', artist: '苏小明' }
])

// 戏曲列表
const operaList = ref([
  { id: 1, title: '贵妃醉酒', type: '京剧' },
  { id: 2, title: '天仙配', type: '黄梅戏' },
  { id: 3, title: '梁祝', type: '越剧' },
  { id: 4, title: '花木兰', type: '豫剧' }
])

// 视频列表
const videoList = ref([
  { id: 1, title: '养生太极拳教学', duration: '15:30', views: '2.3万' },
  { id: 2, title: '八段锦完整版', duration: '12:45', views: '1.8万' },
  { id: 3, title: '广场舞《最炫民族风》', duration: '08:20', views: '3.5万' }
])

// 游戏列表
const gameList = ref([
  {
    id: 1,
    name: '数独',
    desc: '锻炼逻辑思维',
    bgColor: 'bg-blue-100',
    iconColor: 'text-blue-600',
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' })
    ])}
  },
  {
    id: 2,
    name: '记忆翻牌',
    desc: '增强记忆力',
    bgColor: 'bg-green-100',
    iconColor: 'text-green-600',
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' })
    ])}
  },
  {
    id: 3,
    name: '象棋',
    desc: '经典对弈',
    bgColor: 'bg-red-100',
    iconColor: 'text-red-600',
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z' })
    ])}
  },
  {
    id: 4,
    name: '消消乐',
    desc: '休闲益智',
    bgColor: 'bg-purple-100',
    iconColor: 'text-purple-600',
    icon: { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 2, d: 'M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' })
    ])}
  }
])

// 文章列表
const articleList = ref([
  { id: 1, title: '老年人春季养生五大要点', category: '健康养生', readTime: 5 },
  { id: 2, title: '退休生活怎么过？这些兴趣爱好值得尝试', category: '生活', readTime: 8 },
  { id: 3, title: '高血压患者的饮食注意事项', category: '健康养生', readTime: 6 }
])

// 有声书列表
const audioBookList = ref([
  { id: 1, title: '三国演义' },
  { id: 2, title: '西游记' },
  { id: 3, title: '红楼梦' },
  { id: 4, title: '水浒传' },
  { id: 5, title: '平凡的世界' },
  { id: 6, title: '围城' }
])

function playSong(song) {
  window.$toast?.info(`正在播放：${song.title}`)
}

function playOpera(opera) {
  window.$toast?.info(`正在播放：${opera.title}`)
}

function playVideo(video) {
  window.$toast?.info(`正在播放：${video.title}`)
}

function playGame(game) {
  window.$toast?.info(`${game.name}功能开发中`)
}

function readArticle(article) {
  window.$toast?.info(`正在打开：${article.title}`)
}

function playAudioBook(book) {
  window.$toast?.info(`正在播放：${book.title}`)
}
</script>
