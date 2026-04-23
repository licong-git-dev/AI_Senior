<template>
  <div class="min-h-screen pb-20">
    <!-- 页头 -->
    <div class="page-header">
      <h1 class="page-title">社区</h1>
      <button class="text-primary-500" @click="showPostModal = true">
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>
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

    <!-- 热门话题 -->
    <div class="px-4 mt-4" v-if="activeCategory === 'all'">
      <div class="card bg-gradient-to-r from-primary-50 to-blue-50">
        <h2 class="text-lg font-bold text-gray-800 mb-3">热门话题</h2>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="topic in hotTopics"
            :key="topic"
            class="px-3 py-1 bg-white rounded-full text-sm text-gray-700 shadow-sm cursor-pointer hover:bg-primary-50"
          >
            #{{ topic }}
          </span>
        </div>
      </div>
    </div>

    <!-- 帖子列表 -->
    <div class="px-4 mt-4 space-y-4">
      <div
        v-for="post in filteredPosts"
        :key="post.id"
        class="card"
      >
        <!-- 用户信息 -->
        <div class="flex items-center mb-3">
          <div class="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-bold text-lg">
            {{ post.author.charAt(0) }}
          </div>
          <div class="ml-3 flex-1">
            <p class="font-bold text-gray-800">{{ post.author }}</p>
            <p class="text-sm text-gray-500">{{ post.time }}</p>
          </div>
          <span class="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-600">
            {{ post.category }}
          </span>
        </div>

        <!-- 帖子内容 -->
        <p class="text-gray-800 text-lg leading-relaxed">{{ post.content }}</p>

        <!-- 图片 -->
        <div v-if="post.images && post.images.length > 0" class="mt-3 grid gap-2" :class="post.images.length === 1 ? 'grid-cols-1' : 'grid-cols-3'">
          <div
            v-for="(img, idx) in post.images"
            :key="idx"
            class="aspect-square bg-gray-200 rounded-xl"
          ></div>
        </div>

        <!-- 互动区 -->
        <div class="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
          <button
            :class="[
              'flex items-center px-4 py-2 rounded-xl transition-colors',
              post.liked ? 'bg-red-50 text-red-500' : 'text-gray-500 hover:bg-gray-50'
            ]"
            @click="toggleLike(post)"
          >
            <svg class="w-5 h-5 mr-1" :fill="post.liked ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            {{ post.likes }}
          </button>
          <button class="flex items-center px-4 py-2 rounded-xl text-gray-500 hover:bg-gray-50 transition-colors">
            <svg class="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            {{ post.comments }}
          </button>
          <button class="flex items-center px-4 py-2 rounded-xl text-gray-500 hover:bg-gray-50 transition-colors">
            <svg class="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
            分享
          </button>
        </div>
      </div>
    </div>

    <!-- 加载更多 -->
    <div class="px-4 mt-4 mb-6">
      <button class="w-full py-3 bg-gray-100 text-gray-600 rounded-xl font-medium">
        加载更多
      </button>
    </div>

    <!-- 附近活动 -->
    <div class="px-4 mb-6" v-if="activeCategory === 'all'">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-800">附近活动</h2>
          <button class="text-primary-500 text-sm">查看全部</button>
        </div>
        <div class="space-y-3">
          <div
            v-for="event in nearbyEvents"
            :key="event.id"
            class="flex items-center p-3 bg-gray-50 rounded-xl"
          >
            <div class="w-16 h-16 bg-primary-100 rounded-xl flex items-center justify-center mr-4">
              <svg class="w-8 h-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div class="flex-1">
              <h3 class="font-bold text-gray-800">{{ event.title }}</h3>
              <p class="text-sm text-gray-500 mt-1">{{ event.time }} · {{ event.location }}</p>
              <p class="text-sm text-primary-500 mt-1">{{ event.participants }}人参与</p>
            </div>
            <button class="px-4 py-2 bg-primary-500 text-white rounded-xl text-sm">
              参加
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const showPostModal = ref(false)
const activeCategory = ref('all')

const categories = [
  { value: 'all', label: '全部' },
  { value: 'health', label: '养生' },
  { value: 'life', label: '生活' },
  { value: 'hobby', label: '兴趣' },
  { value: 'help', label: '互助' }
]

// 热门话题
const hotTopics = ref([
  '春季养生', '广场舞', '书法交流', '摄影分享', '钓鱼', '太极拳'
])

// 帖子列表
const posts = ref([
  {
    id: 1,
    author: '王阿姨',
    time: '2小时前',
    category: '养生',
    content: '今天分享一道养生粥的做法：红枣枸杞小米粥，补气养血，特别适合我们这个年纪的人喝。做法很简单...',
    images: ['1.jpg'],
    likes: 56,
    comments: 12,
    liked: false
  },
  {
    id: 2,
    author: '李大爷',
    time: '4小时前',
    category: '兴趣',
    content: '今天在公园练太极，遇到几位老友，大家一起交流，收获很多。太极拳不仅能强身健体，还能结交朋友！',
    images: ['1.jpg', '2.jpg', '3.jpg'],
    likes: 89,
    comments: 23,
    liked: true
  },
  {
    id: 3,
    author: '张奶奶',
    time: '昨天',
    category: '生活',
    content: '今天孙子来看我啦，给我带了很多好吃的。看着孩子们都长大了，心里真高兴！',
    images: [],
    likes: 128,
    comments: 35,
    liked: false
  },
  {
    id: 4,
    author: '刘叔叔',
    time: '昨天',
    category: '互助',
    content: '有没有住在和平路附近的老友？我家里有一批旧书想送人，都是历史和养生方面的，有兴趣的可以联系我。',
    images: ['1.jpg', '2.jpg'],
    likes: 45,
    comments: 18,
    liked: false
  }
])

// 筛选帖子
const filteredPosts = computed(() => {
  if (activeCategory.value === 'all') {
    return posts.value
  }
  const categoryMap = {
    'health': '养生',
    'life': '生活',
    'hobby': '兴趣',
    'help': '互助'
  }
  return posts.value.filter(p => p.category === categoryMap[activeCategory.value])
})

// 附近活动
const nearbyEvents = ref([
  {
    id: 1,
    title: '社区太极拳晨练',
    time: '每周一三五 7:00',
    location: '中心公园',
    participants: 23
  },
  {
    id: 2,
    title: '书法交流会',
    time: '本周六 14:00',
    location: '社区活动中心',
    participants: 15
  }
])

// 点赞
function toggleLike(post) {
  post.liked = !post.liked
  post.likes += post.liked ? 1 : -1
}
</script>
