<template>
  <div class="min-h-screen flex flex-col pb-20">
    <!-- 页头 -->
    <div class="page-header">
      <h1 class="page-title">智能聊天</h1>
      <button class="text-gray-500">
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
        </svg>
      </button>
    </div>

    <!-- 聊天消息区 -->
    <div class="flex-1 overflow-y-auto px-4 py-4 space-y-4">
      <div v-for="msg in messages" :key="msg.id" :class="['flex', msg.isMe ? 'justify-end' : 'justify-start']">
        <div :class="['max-w-[80%] rounded-2xl px-4 py-3', msg.isMe ? 'bg-primary-500 text-white' : 'bg-white shadow-soft']">
          <p class="text-lg">{{ msg.content }}</p>
          <p :class="['text-xs mt-1', msg.isMe ? 'text-primary-100' : 'text-gray-400']">{{ msg.time }}</p>
        </div>
      </div>

      <!-- 加载动画 -->
      <div v-if="loading" class="flex justify-start">
        <div class="bg-white shadow-soft rounded-2xl px-4 py-3">
          <div class="flex space-x-2">
            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="bg-white border-t border-gray-100 px-4 py-3">
      <div class="flex items-center gap-3">
        <!-- 语音按钮 -->
        <button
          class="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center text-primary-600"
          @click="toggleVoice"
        >
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        </button>

        <!-- 输入框 -->
        <input
          v-model="inputText"
          type="text"
          placeholder="输入消息..."
          class="flex-1 input"
          @keyup.enter="sendMessage"
        />

        <!-- 发送按钮 -->
        <button
          class="w-12 h-12 bg-primary-500 rounded-full flex items-center justify-center text-white"
          :disabled="!inputText.trim()"
          @click="sendMessage"
        >
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { chatApi } from '@api/index'

const messages = ref([
  { id: 1, content: '您好！我是安心宝智能助手，有什么可以帮助您的吗？', isMe: false, time: '10:00' },
  { id: 2, content: '今天天气怎么样？', isMe: true, time: '10:01' },
  { id: 3, content: '今天天气晴朗，温度适宜，非常适合外出散步。不过中午阳光较强，建议出门时带上帽子和水杯。', isMe: false, time: '10:01' }
])

const inputText = ref('')
const loading = ref(false)

async function sendMessage() {
  if (!inputText.value.trim()) return

  const text = inputText.value.trim()
  inputText.value = ''

  // 添加用户消息
  messages.value.push({
    id: Date.now(),
    content: text,
    isMe: true,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })

  loading.value = true

  try {
    const response = await chatApi.sendMessage(text)
    messages.value.push({
      id: Date.now() + 1,
      content: response.response || response.message || '抱歉，我没有理解您的意思。',
      isMe: false,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })
  } catch (error) {
    messages.value.push({
      id: Date.now() + 1,
      content: '抱歉，网络出现问题，请稍后再试。',
      isMe: false,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })
  } finally {
    loading.value = false
  }
}

function toggleVoice() {
  window.$toast?.info('语音功能开发中')
}
</script>
