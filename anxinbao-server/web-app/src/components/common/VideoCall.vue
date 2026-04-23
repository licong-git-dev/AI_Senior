<template>
  <div v-if="isVisible" class="fixed inset-0 z-50">
    <!-- 视频通话界面 -->
    <div class="relative w-full h-full bg-gray-900">
      <!-- 远程视频 (对方画面) -->
      <div class="absolute inset-0">
        <video
          ref="remoteVideoRef"
          class="w-full h-full object-cover"
          autoplay
          playsinline
        ></video>

        <!-- 无视频时显示头像 -->
        <div v-if="!remoteVideoEnabled" class="absolute inset-0 flex items-center justify-center bg-gray-800">
          <div class="text-center">
            <div class="w-32 h-32 rounded-full bg-primary-500 flex items-center justify-center mx-auto mb-4">
              <span class="text-5xl text-white">{{ callerInitial }}</span>
            </div>
            <p class="text-white text-xl">{{ callerName }}</p>
            <p v-if="callStatus === 'calling'" class="text-gray-400 mt-2">
              <span class="animate-pulse">正在呼叫...</span>
            </p>
            <p v-else-if="callStatus === 'connecting'" class="text-gray-400 mt-2">
              <span class="animate-pulse">正在连接...</span>
            </p>
            <p v-else-if="callStatus === 'connected'" class="text-gray-400 mt-2">
              {{ callDurationFormatted }}
            </p>
          </div>
        </div>
      </div>

      <!-- 本地视频 (自己画面) -->
      <div
        class="absolute top-4 right-4 w-32 h-44 rounded-xl overflow-hidden bg-gray-700 shadow-lg border-2 border-white/20"
        :class="{ 'cursor-move': true }"
      >
        <video
          ref="localVideoRef"
          class="w-full h-full object-cover"
          autoplay
          playsinline
          muted
        ></video>

        <!-- 摄像头关闭时 -->
        <div v-if="!videoEnabled" class="absolute inset-0 flex items-center justify-center bg-gray-800">
          <svg class="w-10 h-10 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </div>
      </div>

      <!-- 顶部信息栏 -->
      <div class="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/50 to-transparent">
        <div class="flex items-center justify-between">
          <div class="flex items-center text-white">
            <div class="w-2 h-2 rounded-full mr-2" :class="signalQualityClass"></div>
            <span class="text-sm">{{ signalQualityText }}</span>
          </div>
          <div v-if="callStatus === 'connected'" class="text-white text-lg font-medium">
            {{ callDurationFormatted }}
          </div>
          <button @click="toggleSpeaker" class="text-white">
            <svg v-if="speakerEnabled" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
            </svg>
            <svg v-else class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
            </svg>
          </button>
        </div>
      </div>

      <!-- 底部控制栏 -->
      <div class="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/50 to-transparent">
        <div class="flex items-center justify-center gap-6">
          <!-- 静音 -->
          <button
            @click="toggleMute"
            :class="[
              'w-14 h-14 rounded-full flex items-center justify-center transition-all',
              audioEnabled ? 'bg-gray-700 hover:bg-gray-600' : 'bg-red-500 hover:bg-red-600'
            ]"
          >
            <svg v-if="audioEnabled" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
            <svg v-else class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
            </svg>
          </button>

          <!-- 摄像头 -->
          <button
            @click="toggleVideo"
            :class="[
              'w-14 h-14 rounded-full flex items-center justify-center transition-all',
              videoEnabled ? 'bg-gray-700 hover:bg-gray-600' : 'bg-red-500 hover:bg-red-600'
            ]"
          >
            <svg v-if="videoEnabled" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <svg v-else class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18" />
            </svg>
          </button>

          <!-- 挂断 -->
          <button
            @click="endCall"
            class="w-16 h-16 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center transition-all"
          >
            <svg class="w-8 h-8 text-white transform rotate-135" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
          </button>

          <!-- 切换摄像头 -->
          <button
            @click="switchCamera"
            class="w-14 h-14 rounded-full bg-gray-700 hover:bg-gray-600 flex items-center justify-center transition-all"
          >
            <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>

          <!-- 更多选项 -->
          <button
            @click="showMoreOptions = !showMoreOptions"
            class="w-14 h-14 rounded-full bg-gray-700 hover:bg-gray-600 flex items-center justify-center transition-all"
          >
            <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z" />
            </svg>
          </button>
        </div>

        <!-- 更多选项菜单 -->
        <transition name="slide-up">
          <div v-if="showMoreOptions" class="absolute bottom-24 left-1/2 transform -translate-x-1/2 bg-gray-800 rounded-xl p-4 min-w-64">
            <div class="space-y-3">
              <button
                @click="toggleBeauty"
                class="w-full flex items-center justify-between p-3 rounded-xl hover:bg-gray-700 text-white"
              >
                <span class="flex items-center">
                  <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                  </svg>
                  美颜
                </span>
                <div :class="['w-10 h-6 rounded-full transition-colors', beautyEnabled ? 'bg-primary-500' : 'bg-gray-600']">
                  <div :class="['w-5 h-5 rounded-full bg-white shadow transform transition-transform mt-0.5', beautyEnabled ? 'translate-x-4.5 ml-0.5' : 'translate-x-0.5']"></div>
                </div>
              </button>

              <button
                @click="sendMessage"
                class="w-full flex items-center p-3 rounded-xl hover:bg-gray-700 text-white"
              >
                <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                发送消息
              </button>

              <button
                @click="shareScreen"
                class="w-full flex items-center p-3 rounded-xl hover:bg-gray-700 text-white"
              >
                <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                共享屏幕
              </button>

              <button
                @click="reportProblem"
                class="w-full flex items-center p-3 rounded-xl hover:bg-gray-700 text-white"
              >
                <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                报告问题
              </button>
            </div>
          </div>
        </transition>
      </div>

      <!-- 来电界面 -->
      <div v-if="callStatus === 'incoming'" class="absolute inset-0 bg-gray-900 flex flex-col items-center justify-center">
        <div class="text-center">
          <div class="w-32 h-32 rounded-full bg-primary-500 flex items-center justify-center mx-auto mb-6 animate-pulse">
            <span class="text-5xl text-white">{{ callerInitial }}</span>
          </div>
          <p class="text-white text-2xl font-medium mb-2">{{ callerName }}</p>
          <p class="text-gray-400 mb-8">视频通话邀请</p>

          <div class="flex gap-8">
            <button
              @click="rejectCall"
              class="w-16 h-16 rounded-full bg-red-500 flex items-center justify-center"
            >
              <svg class="w-8 h-8 text-white transform rotate-135" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </button>
            <button
              @click="acceptCall"
              class="w-16 h-16 rounded-full bg-green-500 flex items-center justify-center animate-bounce"
            >
              <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  },
  callerName: {
    type: String,
    default: '未知'
  },
  callerId: {
    type: String,
    default: ''
  },
  isIncoming: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'call-ended', 'call-accepted', 'call-rejected'])

// 视频元素引用
const localVideoRef = ref(null)
const remoteVideoRef = ref(null)

// 通话状态
const callStatus = ref('idle') // idle, incoming, calling, connecting, connected
const callDuration = ref(0)
let callTimer = null

// 媒体控制
const audioEnabled = ref(true)
const videoEnabled = ref(true)
const speakerEnabled = ref(true)
const remoteVideoEnabled = ref(true)
const beautyEnabled = ref(false)

// UI状态
const showMoreOptions = ref(false)

// 信号质量
const signalQuality = ref(3) // 1-3

// 本地媒体流
let localStream = null
let peerConnection = null

// 计算属性
const callerInitial = computed(() => {
  return props.callerName ? props.callerName.charAt(0).toUpperCase() : '?'
})

const callDurationFormatted = computed(() => {
  const mins = Math.floor(callDuration.value / 60)
  const secs = callDuration.value % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
})

const signalQualityClass = computed(() => {
  if (signalQuality.value >= 3) return 'bg-green-500'
  if (signalQuality.value >= 2) return 'bg-yellow-500'
  return 'bg-red-500'
})

const signalQualityText = computed(() => {
  if (signalQuality.value >= 3) return '信号良好'
  if (signalQuality.value >= 2) return '信号一般'
  return '信号较差'
})

// 方法
const initLocalMedia = async () => {
  try {
    localStream = await navigator.mediaDevices.getUserMedia({
      video: true,
      audio: true
    })

    if (localVideoRef.value) {
      localVideoRef.value.srcObject = localStream
    }
  } catch (error) {
    console.error('获取本地媒体失败:', error)
    // 降级处理：只获取音频
    try {
      localStream = await navigator.mediaDevices.getUserMedia({
        video: false,
        audio: true
      })
      videoEnabled.value = false
    } catch (audioError) {
      console.error('获取音频也失败:', audioError)
    }
  }
}

const startCall = () => {
  callStatus.value = 'calling'
  initLocalMedia()

  // 模拟对方接听（实际应通过WebSocket/信令服务器）
  setTimeout(() => {
    callStatus.value = 'connecting'
    setTimeout(() => {
      callStatus.value = 'connected'
      startCallTimer()
    }, 1000)
  }, 2000)
}

const acceptCall = () => {
  callStatus.value = 'connecting'
  initLocalMedia()

  setTimeout(() => {
    callStatus.value = 'connected'
    startCallTimer()
    emit('call-accepted')
  }, 1000)
}

const rejectCall = () => {
  emit('call-rejected')
  cleanup()
}

const endCall = () => {
  emit('call-ended', {
    duration: callDuration.value
  })
  cleanup()
}

const cleanup = () => {
  if (callTimer) {
    clearInterval(callTimer)
    callTimer = null
  }

  if (localStream) {
    localStream.getTracks().forEach(track => track.stop())
    localStream = null
  }

  if (peerConnection) {
    peerConnection.close()
    peerConnection = null
  }

  callStatus.value = 'idle'
  callDuration.value = 0
  emit('close')
}

const startCallTimer = () => {
  callTimer = setInterval(() => {
    callDuration.value++
  }, 1000)
}

const toggleMute = () => {
  audioEnabled.value = !audioEnabled.value
  if (localStream) {
    localStream.getAudioTracks().forEach(track => {
      track.enabled = audioEnabled.value
    })
  }
}

const toggleVideo = () => {
  videoEnabled.value = !videoEnabled.value
  if (localStream) {
    localStream.getVideoTracks().forEach(track => {
      track.enabled = videoEnabled.value
    })
  }
}

const toggleSpeaker = () => {
  speakerEnabled.value = !speakerEnabled.value
  if (remoteVideoRef.value) {
    remoteVideoRef.value.muted = !speakerEnabled.value
  }
}

const switchCamera = async () => {
  if (!localStream) return

  const videoTrack = localStream.getVideoTracks()[0]
  if (!videoTrack) return

  try {
    // 获取当前摄像头的 facingMode
    const settings = videoTrack.getSettings()
    const newFacingMode = settings.facingMode === 'user' ? 'environment' : 'user'

    // 停止当前视频轨道
    videoTrack.stop()

    // 获取新的视频流
    const newStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: newFacingMode },
      audio: false
    })

    const newVideoTrack = newStream.getVideoTracks()[0]
    localStream.removeTrack(videoTrack)
    localStream.addTrack(newVideoTrack)

    if (localVideoRef.value) {
      localVideoRef.value.srcObject = localStream
    }
  } catch (error) {
    console.error('切换摄像头失败:', error)
  }
}

const toggleBeauty = () => {
  beautyEnabled.value = !beautyEnabled.value
  // 实际实现需要使用 Canvas 或 WebGL 进行美颜处理
  console.log('美颜:', beautyEnabled.value ? '开启' : '关闭')
}

const sendMessage = () => {
  showMoreOptions.value = false
  // TODO: 打开消息输入界面
}

const shareScreen = async () => {
  showMoreOptions.value = false
  try {
    const screenStream = await navigator.mediaDevices.getDisplayMedia({
      video: true
    })
    console.log('屏幕共享已启动')
    // TODO: 替换视频轨道
  } catch (error) {
    console.error('屏幕共享失败:', error)
  }
}

const reportProblem = () => {
  showMoreOptions.value = false
  // TODO: 打开问题反馈界面
}

// 监听可见性变化
watch(() => props.isVisible, (visible) => {
  if (visible) {
    if (props.isIncoming) {
      callStatus.value = 'incoming'
    } else {
      startCall()
    }
  } else {
    cleanup()
  }
})

// 生命周期
onMounted(() => {
  if (props.isVisible && !props.isIncoming) {
    startCall()
  } else if (props.isVisible && props.isIncoming) {
    callStatus.value = 'incoming'
  }
})

onUnmounted(() => {
  cleanup()
})
</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translate(-50%, 20px);
}
</style>
