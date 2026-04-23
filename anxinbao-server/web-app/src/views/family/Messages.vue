<template>
  <div class="h-full flex">
    <!-- 左侧消息列表 -->
    <div class="w-80 bg-white border-r border-gray-200 flex flex-col">
      <!-- 搜索和筛选 -->
      <div class="p-4 border-b border-gray-100">
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索消息..."
            class="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        <!-- 消息类型筛选 -->
        <div class="flex gap-2 mt-3">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            @click="activeTab = tab.value"
            :class="[
              'px-3 py-1.5 text-sm rounded-full transition-colors',
              activeTab === tab.value
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            ]"
          >
            {{ tab.label }}
            <span v-if="tab.count > 0" class="ml-1 px-1.5 py-0.5 bg-red-500 text-white text-xs rounded-full">
              {{ tab.count }}
            </span>
          </button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="flex-1 overflow-y-auto">
        <div v-if="filteredMessages.length === 0" class="p-8 text-center text-gray-500">
          <svg class="w-12 h-12 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <p>暂无消息</p>
        </div>

        <div
          v-for="msg in filteredMessages"
          :key="msg.id"
          @click="selectMessage(msg)"
          :class="[
            'p-4 border-b border-gray-100 cursor-pointer transition-colors',
            selectedMessage?.id === msg.id ? 'bg-primary-50' : 'hover:bg-gray-50',
            !msg.read && 'bg-blue-50'
          ]"
        >
          <div class="flex items-start">
            <!-- 头像/图标 -->
            <div :class="[
              'w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 mr-3',
              getMessageIconStyle(msg.type)
            ]">
              <component :is="getMessageIcon(msg.type)" class="w-6 h-6" />
            </div>

            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-1">
                <h4 :class="['font-medium truncate', !msg.read ? 'text-gray-900' : 'text-gray-700']">
                  {{ msg.sender || msg.title }}
                </h4>
                <span class="text-xs text-gray-500 flex-shrink-0 ml-2">{{ formatTime(msg.time) }}</span>
              </div>
              <p class="text-sm text-gray-500 truncate">{{ msg.preview }}</p>

              <!-- 消息标签 -->
              <div class="flex items-center mt-2 gap-2">
                <span v-if="!msg.read" class="w-2 h-2 bg-primary-500 rounded-full"></span>
                <span :class="['text-xs px-2 py-0.5 rounded', getTypeStyle(msg.type)]">
                  {{ getTypeLabel(msg.type) }}
                </span>
                <span v-if="msg.priority === 'high'" class="text-xs px-2 py-0.5 rounded bg-red-100 text-red-600">
                  紧急
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧消息详情/聊天 -->
    <div class="flex-1 flex flex-col bg-gray-50">
      <!-- 未选择消息时的占位 -->
      <div v-if="!selectedMessage" class="flex-1 flex items-center justify-center">
        <div class="text-center text-gray-500">
          <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <p class="text-lg">选择一条消息查看详情</p>
          <p class="text-sm mt-2">或开始与家人聊天</p>
        </div>
      </div>

      <!-- 消息详情 -->
      <template v-else>
        <!-- 头部 -->
        <div class="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <div class="flex items-center">
            <div :class="[
              'w-10 h-10 rounded-full flex items-center justify-center mr-3',
              getMessageIconStyle(selectedMessage.type)
            ]">
              <component :is="getMessageIcon(selectedMessage.type)" class="w-5 h-5" />
            </div>
            <div>
              <h3 class="font-bold text-gray-800">{{ selectedMessage.sender || selectedMessage.title }}</h3>
              <p class="text-sm text-gray-500">{{ getTypeLabel(selectedMessage.type) }}</p>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button
              v-if="selectedMessage.type === 'chat'"
              @click="startVideoCall"
              class="p-2 text-green-600 hover:bg-green-50 rounded-lg"
              title="视频通话"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
            <button
              v-if="selectedMessage.type === 'chat'"
              @click="startVoiceCall"
              class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
              title="语音通话"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </button>
            <button
              @click="toggleRead"
              class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              :title="selectedMessage.read ? '标记未读' : '标记已读'"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path v-if="selectedMessage.read" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 19v-8.93a2 2 0 01.89-1.664l7-4.666a2 2 0 012.22 0l7 4.666A2 2 0 0121 10.07V19M3 19a2 2 0 002 2h14a2 2 0 002-2M3 19l6.75-4.5M21 19l-6.75-4.5M3 10l6.75 4.5M21 10l-6.75 4.5m0 0l-1.14.76a2 2 0 01-2.22 0l-1.14-.76" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </button>
            <button
              @click="deleteMessage"
              class="p-2 text-red-600 hover:bg-red-50 rounded-lg"
              title="删除"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>

        <!-- 聊天消息区域 -->
        <div v-if="selectedMessage.type === 'chat'" class="flex-1 overflow-y-auto p-4" ref="chatContainer">
          <div class="space-y-4">
            <div
              v-for="(chat, index) in chatHistory"
              :key="index"
              :class="['flex', chat.isMe ? 'justify-end' : 'justify-start']"
            >
              <div :class="['max-w-[70%]', chat.isMe ? 'order-2' : 'order-1']">
                <div :class="[
                  'px-4 py-3 rounded-2xl',
                  chat.isMe
                    ? 'bg-primary-500 text-white rounded-br-md'
                    : 'bg-white text-gray-800 rounded-bl-md shadow-sm'
                ]">
                  <p>{{ chat.content }}</p>
                </div>
                <p :class="['text-xs mt-1', chat.isMe ? 'text-right text-gray-500' : 'text-gray-500']">
                  {{ formatChatTime(chat.time) }}
                  <span v-if="chat.isMe && chat.status === 'sent'" class="ml-1">✓</span>
                  <span v-if="chat.isMe && chat.status === 'read'" class="ml-1">✓✓</span>
                </p>
              </div>
            </div>

            <!-- 对方正在输入 -->
            <div v-if="isTyping" class="flex justify-start">
              <div class="bg-white px-4 py-3 rounded-2xl rounded-bl-md shadow-sm">
                <div class="flex space-x-1">
                  <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                  <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                  <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 系统消息详情 -->
        <div v-else class="flex-1 overflow-y-auto p-6">
          <div class="bg-white rounded-xl shadow-sm p-6">
            <h2 class="text-xl font-bold text-gray-800 mb-4">{{ selectedMessage.title }}</h2>

            <div class="flex items-center gap-4 mb-6 text-sm text-gray-500">
              <span class="flex items-center">
                <svg class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {{ formatDetailTime(selectedMessage.time) }}
              </span>
              <span :class="['px-2 py-0.5 rounded text-xs', getTypeStyle(selectedMessage.type)]">
                {{ getTypeLabel(selectedMessage.type) }}
              </span>
            </div>

            <div class="prose prose-gray max-w-none">
              <p class="text-gray-600 leading-relaxed whitespace-pre-wrap">{{ selectedMessage.content }}</p>
            </div>

            <!-- 相关操作 -->
            <div v-if="selectedMessage.actions?.length > 0" class="mt-6 pt-6 border-t border-gray-100">
              <h4 class="text-sm font-medium text-gray-700 mb-3">相关操作</h4>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="action in selectedMessage.actions"
                  :key="action.id"
                  @click="handleAction(action)"
                  :class="[
                    'px-4 py-2 rounded-lg text-sm',
                    action.type === 'primary'
                      ? 'bg-primary-500 text-white hover:bg-primary-600'
                      : 'border border-gray-200 text-gray-600 hover:bg-gray-50'
                  ]"
                >
                  {{ action.label }}
                </button>
              </div>
            </div>

            <!-- 关联数据 -->
            <div v-if="selectedMessage.relatedData" class="mt-6 pt-6 border-t border-gray-100">
              <h4 class="text-sm font-medium text-gray-700 mb-3">详细数据</h4>
              <div class="bg-gray-50 rounded-lg p-4">
                <div class="grid grid-cols-2 gap-4">
                  <div v-for="(value, key) in selectedMessage.relatedData" :key="key">
                    <p class="text-xs text-gray-500">{{ key }}</p>
                    <p class="text-gray-800 font-medium">{{ value }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 聊天输入框 -->
        <div v-if="selectedMessage.type === 'chat'" class="bg-white border-t border-gray-200 p-4">
          <div class="flex items-end gap-3">
            <!-- 表情/附件按钮 -->
            <div class="flex gap-1">
              <button class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg">
                <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
              <button class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg">
                <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
              </button>
              <button class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg">
                <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </button>
            </div>

            <!-- 输入框 -->
            <div class="flex-1 relative">
              <textarea
                v-model="chatInput"
                @keydown.enter.exact.prevent="sendMessage"
                placeholder="输入消息..."
                rows="1"
                class="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                :style="{ minHeight: '48px', maxHeight: '120px' }"
              ></textarea>
            </div>

            <!-- 发送按钮 -->
            <button
              @click="sendMessage"
              :disabled="!chatInput.trim()"
              :class="[
                'p-3 rounded-xl transition-colors',
                chatInput.trim()
                  ? 'bg-primary-500 text-white hover:bg-primary-600'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              ]"
            >
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted, h } from 'vue'

// 搜索和筛选
const searchQuery = ref('')
const activeTab = ref('all')

// 选中的消息
const selectedMessage = ref(null)

// 聊天相关
const chatInput = ref('')
const chatContainer = ref(null)
const isTyping = ref(false)

// 消息类型标签
const tabs = computed(() => [
  { value: 'all', label: '全部', count: unreadCount.value },
  { value: 'chat', label: '聊天', count: messages.value.filter(m => m.type === 'chat' && !m.read).length },
  { value: 'alert', label: '告警', count: messages.value.filter(m => m.type === 'alert' && !m.read).length },
  { value: 'system', label: '系统', count: messages.value.filter(m => m.type === 'system' && !m.read).length }
])

// 模拟消息数据
const messages = ref([
  {
    id: 1,
    type: 'chat',
    sender: '张芳（女儿）',
    avatar: null,
    preview: '爸，今天身体怎么样？',
    time: new Date(Date.now() - 5 * 60 * 1000),
    read: false,
    priority: 'normal'
  },
  {
    id: 2,
    type: 'alert',
    title: '血压异常提醒',
    preview: '王爷爷的血压读数偏高，建议关注',
    content: '尊敬的家属：\n\n王爷爷（张大爷）今日10:30的血压测量结果为150/95mmHg，略高于正常范围（正常值：收缩压90-140mmHg，舒张压60-90mmHg）。\n\n建议：\n1. 请关注是否按时服用降压药物\n2. 避免情绪激动和剧烈运动\n3. 如持续偏高，建议就医检查\n\n您可以通过APP查看详细的血压历史记录。',
    time: new Date(Date.now() - 30 * 60 * 1000),
    read: false,
    priority: 'high',
    relatedData: {
      '测量时间': '2024-01-15 10:30',
      '收缩压': '150 mmHg',
      '舒张压': '95 mmHg',
      '心率': '78 次/分'
    },
    actions: [
      { id: 1, label: '查看健康记录', type: 'primary', action: 'viewHealth' },
      { id: 2, label: '联系老人', type: 'secondary', action: 'contact' }
    ]
  },
  {
    id: 3,
    type: 'system',
    title: '月度健康报告已生成',
    preview: '王爷爷的12月健康月报已生成',
    content: '尊敬的家属：\n\n王爷爷（张大爷）的2024年12月健康月报已生成，报告包含以下内容：\n\n1. 本月血压趋势分析\n2. 心率变化情况\n3. 睡眠质量评估\n4. 运动步数统计\n5. 用药依从性分析\n6. 综合健康评分\n\n本月健康评分：85分（良好）\n较上月提升3分\n\n点击"查看报告"了解详情。',
    time: new Date(Date.now() - 2 * 60 * 60 * 1000),
    read: true,
    priority: 'normal',
    actions: [
      { id: 1, label: '查看报告', type: 'primary', action: 'viewReport' },
      { id: 2, label: '下载PDF', type: 'secondary', action: 'downloadPdf' }
    ]
  },
  {
    id: 4,
    type: 'chat',
    sender: '李明（儿子）',
    avatar: null,
    preview: '妈，周末我带孩子回去看你',
    time: new Date(Date.now() - 3 * 60 * 60 * 1000),
    read: true,
    priority: 'normal'
  },
  {
    id: 5,
    type: 'alert',
    title: '用药提醒确认',
    preview: '王爷爷已按时服用降压药',
    content: '王爷爷已于今日08:00确认服用降压药（苯磺酸氨氯地平片 5mg）。\n\n今日用药计划完成情况：\n- 08:00 降压药 ✓ 已服用\n- 12:00 降糖药 待服用\n- 20:00 钙片 待服用\n\n用药提醒功能正常运行中。',
    time: new Date(Date.now() - 5 * 60 * 60 * 1000),
    read: true,
    priority: 'normal',
    relatedData: {
      '药品名称': '苯磺酸氨氯地平片',
      '剂量': '5mg',
      '服药时间': '08:00',
      '确认时间': '08:02'
    }
  },
  {
    id: 6,
    type: 'system',
    title: '设备状态更新',
    preview: '智能手表已充满电',
    content: '王爷爷的智能手表（型号：安心宝 A1）已充满电，当前电量100%。\n\n设备状态：\n- 连接状态：正常\n- 信号强度：强\n- 定位功能：正常\n- 心率监测：正常\n\n设备将继续为您监测老人健康状态。',
    time: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
    read: true,
    priority: 'normal'
  }
])

// 聊天记录
const chatHistory = ref([
  { content: '爸，今天身体怎么样？', time: new Date(Date.now() - 5 * 60 * 1000), isMe: false, status: 'read' },
  { content: '挺好的，今天早上在公园走了半小时', time: new Date(Date.now() - 4 * 60 * 1000), isMe: true, status: 'read' },
  { content: '血压量了吗？', time: new Date(Date.now() - 3 * 60 * 1000), isMe: false, status: 'read' },
  { content: '量了，130/85，正常', time: new Date(Date.now() - 2 * 60 * 1000), isMe: true, status: 'read' },
  { content: '那就好，记得按时吃药', time: new Date(Date.now() - 1 * 60 * 1000), isMe: false, status: 'sent' }
])

// 计算属性
const unreadCount = computed(() => messages.value.filter(m => !m.read).length)

const filteredMessages = computed(() => {
  let result = messages.value

  // 按类型筛选
  if (activeTab.value !== 'all') {
    result = result.filter(m => m.type === activeTab.value)
  }

  // 按关键词搜索
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(m => {
      const title = (m.title || m.sender || '').toLowerCase()
      const preview = (m.preview || '').toLowerCase()
      return title.includes(query) || preview.includes(query)
    })
  }

  // 按时间排序
  return result.sort((a, b) => new Date(b.time) - new Date(a.time))
})

// 方法
function selectMessage(msg) {
  selectedMessage.value = msg

  // 标记为已读
  if (!msg.read) {
    const index = messages.value.findIndex(m => m.id === msg.id)
    if (index > -1) {
      messages.value[index].read = true
    }
  }

  // 如果是聊天，滚动到底部
  if (msg.type === 'chat') {
    nextTick(() => {
      scrollToBottom()
    })
  }
}

function toggleRead() {
  if (selectedMessage.value) {
    const index = messages.value.findIndex(m => m.id === selectedMessage.value.id)
    if (index > -1) {
      messages.value[index].read = !messages.value[index].read
      selectedMessage.value.read = messages.value[index].read
    }
  }
}

function deleteMessage() {
  if (selectedMessage.value && confirm('确定要删除这条消息吗？')) {
    const index = messages.value.findIndex(m => m.id === selectedMessage.value.id)
    if (index > -1) {
      messages.value.splice(index, 1)
      selectedMessage.value = null
    }
  }
}

function sendMessage() {
  if (!chatInput.value.trim()) return

  chatHistory.value.push({
    content: chatInput.value.trim(),
    time: new Date(),
    isMe: true,
    status: 'sent'
  })

  chatInput.value = ''

  nextTick(() => {
    scrollToBottom()
  })

  // 模拟对方正在输入
  setTimeout(() => {
    isTyping.value = true
  }, 1000)

  // 模拟回复
  setTimeout(() => {
    isTyping.value = false
    chatHistory.value.push({
      content: '好的，我知道了',
      time: new Date(),
      isMe: false,
      status: 'read'
    })
    nextTick(() => {
      scrollToBottom()
    })
  }, 3000)
}

function scrollToBottom() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

function startVideoCall() {
  alert('视频通话功能开发中...')
}

function startVoiceCall() {
  alert('语音通话功能开发中...')
}

function handleAction(action) {
  switch (action.action) {
    case 'viewHealth':
      alert('跳转到健康记录页面')
      break
    case 'viewReport':
      alert('跳转到健康报告页面')
      break
    case 'contact':
      alert('拨打老人电话')
      break
    case 'downloadPdf':
      alert('下载PDF报告')
      break
    default:
      console.log('Action:', action)
  }
}

function getMessageIcon(type) {
  const icons = {
    chat: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' })
    ]),
    alert: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' })
    ]),
    system: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' })
    ])
  }
  return icons[type] || icons.system
}

function getMessageIconStyle(type) {
  const styles = {
    chat: 'bg-green-100 text-green-600',
    alert: 'bg-red-100 text-red-600',
    system: 'bg-blue-100 text-blue-600'
  }
  return styles[type] || styles.system
}

function getTypeLabel(type) {
  const labels = {
    chat: '家人聊天',
    alert: '健康告警',
    system: '系统通知'
  }
  return labels[type] || '其他'
}

function getTypeStyle(type) {
  const styles = {
    chat: 'bg-green-100 text-green-600',
    alert: 'bg-red-100 text-red-600',
    system: 'bg-blue-100 text-blue-600'
  }
  return styles[type] || 'bg-gray-100 text-gray-600'
}

function formatTime(date) {
  const now = new Date()
  const msgDate = new Date(date)
  const diff = now - msgDate

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 172800000) return '昨天'

  return msgDate.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

function formatChatTime(date) {
  const msgDate = new Date(date)
  return msgDate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function formatDetailTime(date) {
  const msgDate = new Date(date)
  return msgDate.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// WebSocket模拟
let wsTimer = null

onMounted(() => {
  // 模拟WebSocket接收新消息
  wsTimer = setInterval(() => {
    // 随机模拟新消息
    if (Math.random() > 0.95) {
      const newMsg = {
        id: Date.now(),
        type: 'system',
        title: '设备状态更新',
        preview: '血压仪同步完成',
        content: '血压仪数据已同步完成，共同步3条健康记录。',
        time: new Date(),
        read: false,
        priority: 'normal'
      }
      messages.value.unshift(newMsg)
    }
  }, 10000)
})

onUnmounted(() => {
  if (wsTimer) {
    clearInterval(wsTimer)
  }
})
</script>

<style scoped>
.prose p {
  margin-bottom: 1rem;
}
</style>
