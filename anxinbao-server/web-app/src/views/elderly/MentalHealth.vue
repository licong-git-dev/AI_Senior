<template>
  <div class="min-h-screen pb-20">
    <!-- 页头 -->
    <div class="page-header">
      <h1 class="page-title">心理健康</h1>
    </div>

    <!-- 心理健康评分 -->
    <div class="px-4 pt-4">
      <div class="card gradient-primary text-white">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-primary-100">心理健康指数</p>
            <div class="text-5xl font-bold mt-2">{{ mentalScore }}</div>
            <p class="text-primary-100 mt-1">{{ mentalStatus }}</p>
          </div>
          <div class="w-24 h-24 relative">
            <svg viewBox="0 0 100 100" class="w-full h-full">
              <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="8"/>
              <circle cx="50" cy="50" r="40" fill="none" stroke="white" stroke-width="8"
                :stroke-dasharray="251.2" :stroke-dashoffset="251.2 * (1 - mentalScore / 100)" stroke-linecap="round"
                transform="rotate(-90 50 50)"/>
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 今日心情 -->
    <div class="px-4 mt-4">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-800">今日心情</h2>
          <span class="text-sm text-gray-500">{{ todayDate }}</span>
        </div>

        <div class="flex justify-around">
          <button
            v-for="mood in moods"
            :key="mood.value"
            @click="selectMood(mood.value)"
            :class="[
              'flex flex-col items-center p-3 rounded-xl transition-all',
              selectedMood === mood.value ? 'bg-primary-100 ring-2 ring-primary-500' : 'hover:bg-gray-50'
            ]"
          >
            <span class="text-3xl">{{ mood.emoji }}</span>
            <span :class="['text-sm mt-2', selectedMood === mood.value ? 'text-primary-600 font-medium' : 'text-gray-600']">
              {{ mood.label }}
            </span>
          </button>
        </div>

        <div v-if="selectedMood" class="mt-4 p-3 bg-primary-50 rounded-xl">
          <p class="text-primary-700 text-center">已记录今日心情: {{ getMoodLabel(selectedMood) }}</p>
        </div>
      </div>
    </div>

    <!-- 心情记录 -->
    <div class="px-4 mt-4">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-800">心情日记</h2>
          <button @click="showDiaryModal = true" class="text-primary-500">写日记</button>
        </div>

        <textarea
          v-model="quickNote"
          placeholder="今天有什么想说的吗..."
          class="w-full p-3 bg-gray-50 rounded-xl border-none resize-none text-gray-700 placeholder-gray-400 focus:ring-2 focus:ring-primary-200"
          rows="3"
        ></textarea>

        <button
          @click="saveQuickNote"
          :disabled="!quickNote.trim()"
          class="mt-3 w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          保存记录
        </button>
      </div>
    </div>

    <!-- 心理评估 -->
    <div class="px-4 mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">心理评估问卷</h2>

        <div class="space-y-3">
          <div
            v-for="assessment in assessments"
            :key="assessment.id"
            @click="startAssessment(assessment)"
            class="flex items-center p-4 bg-gray-50 rounded-xl cursor-pointer hover:bg-gray-100 transition-colors"
          >
            <div :class="['w-12 h-12 rounded-full flex items-center justify-center mr-4', assessment.bgColor]">
              <svg class="w-6 h-6" :class="assessment.iconColor" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="assessment.icon" />
              </svg>
            </div>
            <div class="flex-1">
              <p class="font-medium text-gray-800">{{ assessment.title }}</p>
              <p class="text-sm text-gray-500">{{ assessment.description }}</p>
            </div>
            <div class="text-right">
              <span v-if="assessment.lastScore !== null" :class="['text-lg font-bold', getScoreColor(assessment.lastScore, assessment.maxScore)]">
                {{ assessment.lastScore }}/{{ assessment.maxScore }}
              </span>
              <p class="text-xs text-gray-400">{{ assessment.lastDate || '尚未评估' }}</p>
            </div>
            <svg class="w-5 h-5 text-gray-400 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 睡眠质量 -->
    <div class="px-4 mt-4">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-800">睡眠质量</h2>
          <button @click="showSleepModal = true" class="text-primary-500">记录睡眠</button>
        </div>

        <div class="grid grid-cols-3 gap-4 mb-4">
          <div class="text-center p-3 bg-blue-50 rounded-xl">
            <p class="text-2xl font-bold text-blue-600">{{ sleepData.duration }}</p>
            <p class="text-xs text-blue-500 mt-1">睡眠时长</p>
          </div>
          <div class="text-center p-3 bg-purple-50 rounded-xl">
            <p class="text-2xl font-bold text-purple-600">{{ sleepData.quality }}</p>
            <p class="text-xs text-purple-500 mt-1">睡眠质量</p>
          </div>
          <div class="text-center p-3 bg-indigo-50 rounded-xl">
            <p class="text-2xl font-bold text-indigo-600">{{ sleepData.wakeups }}</p>
            <p class="text-xs text-indigo-500 mt-1">夜醒次数</p>
          </div>
        </div>

        <!-- 睡眠趋势 -->
        <div class="h-24 flex items-end justify-between gap-1">
          <div v-for="(day, i) in sleepTrend" :key="i" class="flex-1 flex flex-col items-center">
            <div class="w-full bg-blue-100 rounded-t" :style="{ height: (day.hours / 10 * 100) + '%' }"></div>
            <span class="text-xs text-gray-500 mt-1">{{ day.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 社交互动 -->
    <div class="px-4 mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">社交互动</h2>

        <div class="grid grid-cols-2 gap-4">
          <div class="p-4 bg-green-50 rounded-xl">
            <div class="flex items-center">
              <svg class="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <div class="ml-3">
                <p class="text-2xl font-bold text-green-600">{{ socialData.familyCalls }}</p>
                <p class="text-xs text-green-500">本周家人通话</p>
              </div>
            </div>
          </div>
          <div class="p-4 bg-orange-50 rounded-xl">
            <div class="flex items-center">
              <svg class="w-8 h-8 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <div class="ml-3">
                <p class="text-2xl font-bold text-orange-600">{{ socialData.messages }}</p>
                <p class="text-xs text-orange-500">本周发送消息</p>
              </div>
            </div>
          </div>
          <div class="p-4 bg-purple-50 rounded-xl">
            <div class="flex items-center">
              <svg class="w-8 h-8 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <div class="ml-3">
                <p class="text-2xl font-bold text-purple-600">{{ socialData.videoCalls }}</p>
                <p class="text-xs text-purple-500">本周视频通话</p>
              </div>
            </div>
          </div>
          <div class="p-4 bg-teal-50 rounded-xl">
            <div class="flex items-center">
              <svg class="w-8 h-8 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <div class="ml-3">
                <p class="text-2xl font-bold text-teal-600">{{ socialData.activities }}</p>
                <p class="text-xs text-teal-500">本周社区活动</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 放松练习 -->
    <div class="px-4 mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">放松练习</h2>

        <div class="space-y-3">
          <div
            v-for="exercise in relaxExercises"
            :key="exercise.id"
            @click="startRelaxExercise(exercise)"
            class="flex items-center p-4 bg-gray-50 rounded-xl cursor-pointer hover:bg-gray-100"
          >
            <div :class="['w-14 h-14 rounded-xl flex items-center justify-center mr-4', exercise.bgColor]">
              <span class="text-2xl">{{ exercise.emoji }}</span>
            </div>
            <div class="flex-1">
              <p class="font-medium text-gray-800">{{ exercise.title }}</p>
              <p class="text-sm text-gray-500">{{ exercise.duration }}</p>
            </div>
            <svg class="w-8 h-8 text-primary-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 心理健康建议 -->
    <div class="px-4 mt-4 mb-6">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">心理健康建议</h2>
        <div class="space-y-3">
          <div v-for="tip in mentalHealthTips" :key="tip.id" class="flex items-start p-3 bg-gray-50 rounded-xl">
            <div :class="['w-10 h-10 rounded-full flex items-center justify-center mr-3 flex-shrink-0', tip.bgColor]">
              <span class="text-lg">{{ tip.emoji }}</span>
            </div>
            <div>
              <p class="font-medium text-gray-800">{{ tip.title }}</p>
              <p class="text-sm text-gray-500 mt-1">{{ tip.content }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 评估问卷弹窗 -->
    <div v-if="showAssessmentModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-md max-h-[80vh] overflow-hidden">
        <div class="p-4 border-b flex items-center justify-between">
          <h3 class="text-lg font-bold">{{ currentAssessment?.title }}</h3>
          <button @click="closeAssessment" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-4 overflow-y-auto max-h-[60vh]">
          <!-- 进度条 -->
          <div class="mb-6">
            <div class="flex justify-between text-sm text-gray-500 mb-2">
              <span>问题 {{ currentQuestionIndex + 1 }} / {{ currentQuestions.length }}</span>
              <span>{{ Math.round((currentQuestionIndex + 1) / currentQuestions.length * 100) }}%</span>
            </div>
            <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div class="h-full bg-primary-500 rounded-full transition-all"
                :style="{ width: ((currentQuestionIndex + 1) / currentQuestions.length * 100) + '%' }"></div>
            </div>
          </div>

          <!-- 当前问题 -->
          <div v-if="currentQuestion">
            <p class="text-lg font-medium text-gray-800 mb-4">{{ currentQuestion.text }}</p>

            <div class="space-y-3">
              <button
                v-for="option in currentQuestion.options"
                :key="option.value"
                @click="selectAnswer(option.value)"
                :class="[
                  'w-full p-4 rounded-xl text-left transition-all border-2',
                  answers[currentQuestionIndex] === option.value
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-primary-200'
                ]"
              >
                <span :class="answers[currentQuestionIndex] === option.value ? 'text-primary-700' : 'text-gray-700'">
                  {{ option.label }}
                </span>
              </button>
            </div>
          </div>

          <!-- 结果页面 -->
          <div v-else-if="assessmentComplete" class="text-center py-6">
            <div class="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-10 h-10 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h4 class="text-xl font-bold text-gray-800 mb-2">评估完成</h4>
            <p class="text-gray-500 mb-4">您的评分: {{ assessmentScore }} / {{ currentAssessment?.maxScore }}</p>
            <div :class="['inline-block px-4 py-2 rounded-full text-sm font-medium', getResultClass(assessmentScore, currentAssessment?.maxScore)]">
              {{ getResultText(assessmentScore, currentAssessment?.maxScore) }}
            </div>
          </div>
        </div>

        <div class="p-4 border-t flex gap-3">
          <button
            v-if="currentQuestionIndex > 0 && !assessmentComplete"
            @click="prevQuestion"
            class="flex-1 btn-secondary"
          >
            上一题
          </button>
          <button
            v-if="!assessmentComplete"
            @click="nextQuestion"
            :disabled="answers[currentQuestionIndex] === undefined"
            class="flex-1 btn-primary disabled:opacity-50"
          >
            {{ currentQuestionIndex === currentQuestions.length - 1 ? '提交' : '下一题' }}
          </button>
          <button
            v-else
            @click="closeAssessment"
            class="flex-1 btn-primary"
          >
            完成
          </button>
        </div>
      </div>
    </div>

    <!-- 睡眠记录弹窗 -->
    <div v-if="showSleepModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-md">
        <div class="p-4 border-b flex items-center justify-between">
          <h3 class="text-lg font-bold">记录睡眠</h3>
          <button @click="showSleepModal = false" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-4 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">入睡时间</label>
            <input type="time" v-model="sleepRecord.bedtime" class="w-full p-3 bg-gray-50 rounded-xl border-none">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">起床时间</label>
            <input type="time" v-model="sleepRecord.wakeup" class="w-full p-3 bg-gray-50 rounded-xl border-none">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">睡眠质量</label>
            <div class="flex gap-2">
              <button
                v-for="q in [1,2,3,4,5]"
                :key="q"
                @click="sleepRecord.quality = q"
                :class="[
                  'flex-1 p-3 rounded-xl text-center transition-all',
                  sleepRecord.quality === q ? 'bg-primary-500 text-white' : 'bg-gray-100 text-gray-600'
                ]"
              >
                {{ q }}
              </button>
            </div>
            <div class="flex justify-between text-xs text-gray-400 mt-1">
              <span>很差</span>
              <span>很好</span>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">夜醒次数</label>
            <div class="flex items-center gap-4">
              <button
                @click="sleepRecord.wakeups = Math.max(0, sleepRecord.wakeups - 1)"
                class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center"
              >-</button>
              <span class="text-2xl font-bold">{{ sleepRecord.wakeups }}</span>
              <button
                @click="sleepRecord.wakeups++"
                class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center"
              >+</button>
            </div>
          </div>
        </div>

        <div class="p-4 border-t">
          <button @click="saveSleepRecord" class="w-full btn-primary">保存记录</button>
        </div>
      </div>
    </div>

    <!-- 放松练习弹窗 -->
    <div v-if="showRelaxModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-md">
        <div class="p-4 border-b flex items-center justify-between">
          <h3 class="text-lg font-bold">{{ currentRelaxExercise?.title }}</h3>
          <button @click="showRelaxModal = false" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-6 text-center">
          <div class="text-6xl mb-4">{{ currentRelaxExercise?.emoji }}</div>

          <!-- 呼吸练习动画 -->
          <div v-if="relaxTimer > 0" class="mb-6">
            <div class="w-32 h-32 mx-auto rounded-full bg-primary-100 flex items-center justify-center animate-pulse">
              <span class="text-2xl font-bold text-primary-600">{{ breathPhase }}</span>
            </div>
            <p class="text-lg text-gray-600 mt-4">{{ breathInstruction }}</p>
            <p class="text-3xl font-bold text-primary-600 mt-2">{{ formatTime(relaxTimer) }}</p>
          </div>

          <div v-else class="mb-6">
            <p class="text-gray-600">{{ currentRelaxExercise?.instruction }}</p>
          </div>

          <button
            v-if="!isRelaxing"
            @click="startRelaxTimer"
            class="btn-primary px-8"
          >
            开始练习
          </button>
          <button
            v-else
            @click="stopRelaxTimer"
            class="btn-secondary px-8"
          >
            结束练习
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'

// 日期
const todayDate = computed(() => {
  const date = new Date()
  return `${date.getMonth() + 1}月${date.getDate()}日`
})

// 心理健康评分
const mentalScore = ref(78)
const mentalStatus = computed(() => {
  if (mentalScore.value >= 80) return '状态良好'
  if (mentalScore.value >= 60) return '状态一般'
  if (mentalScore.value >= 40) return '需要关注'
  return '建议咨询专业人士'
})

// 心情选择
const moods = [
  { value: 'happy', emoji: '😊', label: '开心' },
  { value: 'calm', emoji: '😌', label: '平静' },
  { value: 'tired', emoji: '😔', label: '疲惫' },
  { value: 'anxious', emoji: '😰', label: '焦虑' },
  { value: 'sad', emoji: '😢', label: '难过' }
]
const selectedMood = ref(null)
const quickNote = ref('')

const selectMood = (mood) => {
  selectedMood.value = mood
}

const getMoodLabel = (value) => {
  return moods.find(m => m.value === value)?.label || ''
}

const saveQuickNote = () => {
  if (quickNote.value.trim()) {
    // TODO: 保存到后端
    console.log('保存心情日记:', quickNote.value)
    quickNote.value = ''
    alert('记录已保存')
  }
}

// 心理评估
const assessments = ref([
  {
    id: 'phq9',
    title: 'PHQ-9 抑郁筛查',
    description: '9个问题快速评估抑郁倾向',
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    bgColor: 'bg-blue-100',
    iconColor: 'text-blue-600',
    lastScore: 5,
    maxScore: 27,
    lastDate: '3天前'
  },
  {
    id: 'gad7',
    title: 'GAD-7 焦虑筛查',
    description: '7个问题快速评估焦虑水平',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
    bgColor: 'bg-yellow-100',
    iconColor: 'text-yellow-600',
    lastScore: 4,
    maxScore: 21,
    lastDate: '5天前'
  },
  {
    id: 'loneliness',
    title: '孤独感评估',
    description: '评估社交孤独程度',
    icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z',
    bgColor: 'bg-purple-100',
    iconColor: 'text-purple-600',
    lastScore: null,
    maxScore: 20,
    lastDate: null
  }
])

// 问卷数据
const phq9Questions = [
  { text: '做事时提不起劲或没有兴趣', options: [
    { value: 0, label: '完全不会' },
    { value: 1, label: '好几天' },
    { value: 2, label: '一半以上的天数' },
    { value: 3, label: '几乎每天' }
  ]},
  { text: '感到心情低落、沮丧或绝望', options: [
    { value: 0, label: '完全不会' },
    { value: 1, label: '好几天' },
    { value: 2, label: '一半以上的天数' },
    { value: 3, label: '几乎每天' }
  ]},
  { text: '入睡困难、睡不安稳或睡眠过多', options: [
    { value: 0, label: '完全不会' },
    { value: 1, label: '好几天' },
    { value: 2, label: '一半以上的天数' },
    { value: 3, label: '几乎每天' }
  ]},
  { text: '感觉疲倦或没有活力', options: [
    { value: 0, label: '完全不会' },
    { value: 1, label: '好几天' },
    { value: 2, label: '一半以上的天数' },
    { value: 3, label: '几乎每天' }
  ]},
  { text: '食欲不振或吃太多', options: [
    { value: 0, label: '完全不会' },
    { value: 1, label: '好几天' },
    { value: 2, label: '一半以上的天数' },
    { value: 3, label: '几乎每天' }
  ]}
]

const showAssessmentModal = ref(false)
const currentAssessment = ref(null)
const currentQuestions = ref([])
const currentQuestionIndex = ref(0)
const answers = ref([])
const assessmentComplete = ref(false)
const assessmentScore = ref(0)

const currentQuestion = computed(() => currentQuestions.value[currentQuestionIndex.value])

const startAssessment = (assessment) => {
  currentAssessment.value = assessment
  currentQuestions.value = phq9Questions // 简化：使用相同问题
  currentQuestionIndex.value = 0
  answers.value = []
  assessmentComplete.value = false
  showAssessmentModal.value = true
}

const selectAnswer = (value) => {
  answers.value[currentQuestionIndex.value] = value
}

const nextQuestion = () => {
  if (currentQuestionIndex.value < currentQuestions.value.length - 1) {
    currentQuestionIndex.value++
  } else {
    // 计算得分
    assessmentScore.value = answers.value.reduce((sum, val) => sum + val, 0)
    assessmentComplete.value = true
  }
}

const prevQuestion = () => {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
  }
}

const closeAssessment = () => {
  showAssessmentModal.value = false
  currentAssessment.value = null
}

const getScoreColor = (score, maxScore) => {
  const ratio = score / maxScore
  if (ratio <= 0.3) return 'text-green-600'
  if (ratio <= 0.6) return 'text-yellow-600'
  return 'text-red-600'
}

const getResultClass = (score, maxScore) => {
  const ratio = score / maxScore
  if (ratio <= 0.3) return 'bg-green-100 text-green-700'
  if (ratio <= 0.6) return 'bg-yellow-100 text-yellow-700'
  return 'bg-red-100 text-red-700'
}

const getResultText = (score, maxScore) => {
  const ratio = score / maxScore
  if (ratio <= 0.3) return '状态良好，继续保持'
  if (ratio <= 0.6) return '轻度症状，建议关注'
  return '建议咨询专业人士'
}

// 睡眠数据
const sleepData = ref({
  duration: '7h32m',
  quality: '良好',
  wakeups: '1次'
})

const sleepTrend = ref([
  { label: '一', hours: 6.5 },
  { label: '二', hours: 7.0 },
  { label: '三', hours: 6.0 },
  { label: '四', hours: 7.5 },
  { label: '五', hours: 8.0 },
  { label: '六', hours: 7.2 },
  { label: '日', hours: 7.5 }
])

const showSleepModal = ref(false)
const sleepRecord = ref({
  bedtime: '22:00',
  wakeup: '06:30',
  quality: 3,
  wakeups: 1
})

const saveSleepRecord = () => {
  // TODO: 保存到后端
  console.log('保存睡眠记录:', sleepRecord.value)
  showSleepModal.value = false
  alert('睡眠记录已保存')
}

// 社交数据
const socialData = ref({
  familyCalls: 5,
  messages: 23,
  videoCalls: 2,
  activities: 1
})

// 放松练习
const relaxExercises = ref([
  {
    id: 'breathing',
    title: '深呼吸放松',
    duration: '5分钟',
    emoji: '🌬️',
    bgColor: 'bg-blue-100',
    instruction: '通过深呼吸练习帮助您放松身心，缓解紧张情绪。'
  },
  {
    id: 'meditation',
    title: '冥想放松',
    duration: '10分钟',
    emoji: '🧘',
    bgColor: 'bg-purple-100',
    instruction: '闭上眼睛，专注于呼吸，让思绪平静下来。'
  },
  {
    id: 'muscle',
    title: '肌肉放松',
    duration: '8分钟',
    emoji: '💪',
    bgColor: 'bg-green-100',
    instruction: '依次收紧和放松各个肌肉群，释放身体紧张。'
  }
])

const showRelaxModal = ref(false)
const currentRelaxExercise = ref(null)
const relaxTimer = ref(0)
const isRelaxing = ref(false)
const breathPhase = ref('')
const breathInstruction = ref('')
let timerInterval = null
let breathInterval = null

const startRelaxExercise = (exercise) => {
  currentRelaxExercise.value = exercise
  showRelaxModal.value = true
  relaxTimer.value = 0
  isRelaxing.value = false
}

const startRelaxTimer = () => {
  relaxTimer.value = 60 * 5 // 5分钟
  isRelaxing.value = true

  // 呼吸节奏：吸气4秒-保持4秒-呼气4秒
  let phase = 0
  const phases = [
    { name: '吸气', instruction: '慢慢吸气...', duration: 4 },
    { name: '保持', instruction: '保持呼吸...', duration: 4 },
    { name: '呼气', instruction: '慢慢呼气...', duration: 4 }
  ]

  const updateBreath = () => {
    const current = phases[phase % 3]
    breathPhase.value = current.name
    breathInstruction.value = current.instruction
    phase++
  }

  updateBreath()
  breathInterval = setInterval(updateBreath, 4000)

  timerInterval = setInterval(() => {
    relaxTimer.value--
    if (relaxTimer.value <= 0) {
      stopRelaxTimer()
    }
  }, 1000)
}

const stopRelaxTimer = () => {
  isRelaxing.value = false
  if (timerInterval) clearInterval(timerInterval)
  if (breathInterval) clearInterval(breathInterval)
  relaxTimer.value = 0
}

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
  if (breathInterval) clearInterval(breathInterval)
})

// 心理健康建议
const mentalHealthTips = ref([
  {
    id: 1,
    title: '保持社交联系',
    content: '每天与家人或朋友交流，可以有效预防孤独感。',
    emoji: '👨‍👩‍👧‍👦',
    bgColor: 'bg-green-100'
  },
  {
    id: 2,
    title: '规律作息',
    content: '保持固定的睡眠时间，有助于情绪稳定。',
    emoji: '🌙',
    bgColor: 'bg-blue-100'
  },
  {
    id: 3,
    title: '适度运动',
    content: '每天散步30分钟，可以改善心情。',
    emoji: '🚶',
    bgColor: 'bg-orange-100'
  },
  {
    id: 4,
    title: '培养兴趣爱好',
    content: '参与喜欢的活动，保持积极心态。',
    emoji: '🎨',
    bgColor: 'bg-purple-100'
  }
])

// 日记弹窗
const showDiaryModal = ref(false)
</script>
