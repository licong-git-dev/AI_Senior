<template>
  <div class="min-h-screen pb-20">
    <!-- 页头 -->
    <div class="page-header">
      <h1 class="page-title">运动康复</h1>
    </div>

    <!-- 今日运动概览 -->
    <div class="px-4 pt-4">
      <div class="card gradient-primary text-white">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-primary-100">今日运动</p>
            <div class="text-5xl font-bold mt-2">{{ todayStats.steps.toLocaleString() }}</div>
            <p class="text-primary-100 mt-1">步 · 目标 {{ todayStats.goalSteps.toLocaleString() }} 步</p>
          </div>
          <div class="w-24 h-24 relative">
            <svg viewBox="0 0 100 100" class="w-full h-full">
              <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="8"/>
              <circle
                cx="50" cy="50" r="40"
                fill="none"
                stroke="white"
                stroke-width="8"
                :stroke-dasharray="251.2"
                :stroke-dashoffset="251.2 * (1 - stepsProgress)"
                stroke-linecap="round"
                transform="rotate(-90 50 50)"
              />
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-xl font-bold">{{ Math.round(stepsProgress * 100) }}%</span>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-4 mt-6 pt-4 border-t border-white/20">
          <div class="text-center">
            <p class="text-3xl font-bold">{{ todayStats.distance }}</p>
            <p class="text-primary-100 text-sm">公里</p>
          </div>
          <div class="text-center">
            <p class="text-3xl font-bold">{{ todayStats.calories }}</p>
            <p class="text-primary-100 text-sm">千卡</p>
          </div>
          <div class="text-center">
            <p class="text-3xl font-bold">{{ todayStats.activeMinutes }}</p>
            <p class="text-primary-100 text-sm">分钟</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 康复训练计划 -->
    <div class="px-4 mt-4">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-800">今日训练计划</h2>
          <span class="text-sm text-gray-500">{{ completedExercises }}/{{ exercises.length }} 已完成</span>
        </div>

        <div class="space-y-3">
          <div
            v-for="exercise in exercises"
            :key="exercise.id"
            :class="[
              'p-4 rounded-xl border-2 transition-all',
              exercise.completed
                ? 'bg-green-50 border-green-200'
                : 'bg-gray-50 border-transparent'
            ]"
          >
            <div class="flex items-center">
              <div :class="[
                'w-12 h-12 rounded-xl flex items-center justify-center mr-4 flex-shrink-0',
                exercise.completed ? 'bg-green-100' : 'bg-primary-100'
              ]">
                <svg v-if="exercise.completed" class="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                <svg v-else class="w-6 h-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="exercise.icon" />
                </svg>
              </div>

              <div class="flex-1">
                <h3 :class="['font-medium', exercise.completed ? 'text-green-700' : 'text-gray-800']">
                  {{ exercise.name }}
                </h3>
                <p class="text-sm text-gray-500 mt-1">
                  {{ exercise.duration }}分钟 · {{ exercise.intensity }}
                </p>
              </div>

              <button
                v-if="!exercise.completed"
                @click="startExercise(exercise)"
                class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm"
              >
                开始
              </button>
              <span v-else class="text-green-600 text-sm font-medium">
                已完成
              </span>
            </div>

            <!-- 训练详情 -->
            <div v-if="exercise.tips" class="mt-3 pt-3 border-t border-gray-200">
              <p class="text-xs text-gray-500">{{ exercise.tips }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 康复进度 -->
    <div class="px-4 mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">康复进度</h2>

        <div class="space-y-4">
          <div v-for="goal in rehabilitationGoals" :key="goal.id">
            <div class="flex items-center justify-between mb-2">
              <span class="text-gray-700">{{ goal.name }}</span>
              <span class="text-sm text-gray-500">{{ goal.current }}/{{ goal.target }} {{ goal.unit }}</span>
            </div>
            <div class="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="goal.color"
                :style="{ width: `${(goal.current / goal.target) * 100}%` }"
              ></div>
            </div>
          </div>
        </div>

        <div class="mt-6 p-4 bg-blue-50 rounded-xl">
          <div class="flex items-start">
            <svg class="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p class="text-blue-800 font-medium">康复建议</p>
              <p class="text-blue-700 text-sm mt-1">{{ rehabilitationAdvice }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 7日运动趋势 -->
    <div class="px-4 mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">7日运动趋势</h2>
        <div class="h-40 flex items-end justify-between gap-2">
          <div v-for="(day, i) in weeklyData" :key="i" class="flex-1 flex flex-col items-center">
            <div
              class="w-full bg-primary-500 rounded-t transition-all duration-300"
              :style="{ height: `${(day.steps / maxSteps) * 100}%` }"
            ></div>
            <span class="text-xs text-gray-500 mt-2">{{ day.label }}</span>
            <span class="text-xs text-gray-400">{{ (day.steps / 1000).toFixed(1) }}k</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 推荐运动 -->
    <div class="px-4 mt-4 mb-6">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">推荐运动</h2>
        <div class="grid grid-cols-2 gap-3">
          <div
            v-for="item in recommendedExercises"
            :key="item.id"
            @click="viewExerciseDetail(item)"
            class="bg-gray-50 rounded-xl p-4 cursor-pointer hover:bg-gray-100 transition-colors"
          >
            <div :class="['w-12 h-12 rounded-xl flex items-center justify-center mb-3', item.bgColor]">
              <svg :class="['w-6 h-6', item.iconColor]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="item.icon" />
              </svg>
            </div>
            <h3 class="font-medium text-gray-800">{{ item.name }}</h3>
            <p class="text-sm text-gray-500 mt-1">{{ item.description }}</p>
            <div class="flex items-center mt-2 text-xs text-gray-400">
              <span>{{ item.duration }}分钟</span>
              <span class="mx-2">·</span>
              <span>{{ item.calories }}千卡</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 运动详情弹窗 -->
    <div v-if="showExerciseModal" class="fixed inset-0 z-50 flex items-end justify-center">
      <div class="fixed inset-0 bg-black/50" @click="showExerciseModal = false"></div>
      <div class="relative bg-white rounded-t-3xl w-full max-h-[80vh] overflow-y-auto">
        <div class="sticky top-0 bg-white p-4 border-b border-gray-100">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-bold text-gray-800">{{ currentExercise?.name }}</h3>
            <button @click="showExerciseModal = false" class="p-2 text-gray-400">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div class="p-4">
          <!-- 运动信息 -->
          <div class="flex items-center justify-around py-4">
            <div class="text-center">
              <p class="text-2xl font-bold text-primary-600">{{ currentExercise?.duration }}</p>
              <p class="text-sm text-gray-500">分钟</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-primary-600">{{ currentExercise?.calories }}</p>
              <p class="text-sm text-gray-500">千卡</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-primary-600">{{ currentExercise?.intensity }}</p>
              <p class="text-sm text-gray-500">强度</p>
            </div>
          </div>

          <!-- 运动步骤 -->
          <div class="mt-4">
            <h4 class="font-medium text-gray-800 mb-3">运动步骤</h4>
            <div class="space-y-3">
              <div
                v-for="(step, index) in currentExercise?.steps"
                :key="index"
                class="flex items-start p-3 bg-gray-50 rounded-xl"
              >
                <div class="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center mr-3 flex-shrink-0 text-primary-600 font-bold">
                  {{ index + 1 }}
                </div>
                <div>
                  <p class="text-gray-800">{{ step }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- 注意事项 -->
          <div class="mt-6 p-4 bg-yellow-50 rounded-xl">
            <h4 class="font-medium text-yellow-800 mb-2">注意事项</h4>
            <ul class="text-sm text-yellow-700 space-y-1">
              <li>· 运动前做好热身准备</li>
              <li>· 如感到不适请立即停止</li>
              <li>· 保持呼吸均匀</li>
              <li>· 运动后适当补充水分</li>
            </ul>
          </div>

          <!-- 开始按钮 -->
          <button
            @click="startExerciseSession"
            class="w-full mt-6 py-4 bg-primary-500 text-white rounded-xl font-medium text-lg"
          >
            开始运动
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// 今日统计
const todayStats = ref({
  steps: 5680,
  goalSteps: 8000,
  distance: 3.8,
  calories: 186,
  activeMinutes: 45
})

// 步数进度
const stepsProgress = computed(() => {
  return Math.min(todayStats.value.steps / todayStats.value.goalSteps, 1)
})

// 今日训练计划
const exercises = ref([
  {
    id: 1,
    name: '晨间拉伸',
    duration: 10,
    intensity: '低强度',
    completed: true,
    icon: 'M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4',
    tips: '轻柔拉伸，唤醒身体，注意动作缓慢'
  },
  {
    id: 2,
    name: '散步',
    duration: 30,
    intensity: '低强度',
    completed: true,
    icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    tips: '保持匀速，可以在公园或小区内进行'
  },
  {
    id: 3,
    name: '太极养生操',
    duration: 15,
    intensity: '低强度',
    completed: false,
    icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z',
    tips: '动作缓慢，配合呼吸，适合午后进行'
  },
  {
    id: 4,
    name: '手指操',
    duration: 5,
    intensity: '低强度',
    completed: false,
    icon: 'M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11',
    tips: '锻炼手指灵活性，预防关节僵硬'
  }
])

// 已完成数量
const completedExercises = computed(() => {
  return exercises.value.filter(e => e.completed).length
})

// 康复目标
const rehabilitationGoals = ref([
  { id: 1, name: '每日步数', current: 5680, target: 8000, unit: '步', color: 'bg-blue-500' },
  { id: 2, name: '活动时间', current: 45, target: 60, unit: '分钟', color: 'bg-green-500' },
  { id: 3, name: '训练完成', current: 2, target: 4, unit: '项', color: 'bg-purple-500' },
  { id: 4, name: '本周运动', current: 5, target: 7, unit: '天', color: 'bg-orange-500' }
])

// 康复建议
const rehabilitationAdvice = ref('您的康复进度良好！建议今天完成剩余的太极养生操和手指操训练，保持运动习惯。')

// 7日数据
const weeklyData = ref([
  { label: '周一', steps: 6200 },
  { label: '周二', steps: 5800 },
  { label: '周三', steps: 7100 },
  { label: '周四', steps: 4500 },
  { label: '周五', steps: 6800 },
  { label: '周六', steps: 5200 },
  { label: '今天', steps: 5680 }
])

const maxSteps = computed(() => {
  return Math.max(...weeklyData.value.map(d => d.steps))
})

// 推荐运动
const recommendedExercises = ref([
  {
    id: 1,
    name: '八段锦',
    description: '传统养生功法',
    duration: 15,
    calories: 50,
    intensity: '低',
    bgColor: 'bg-blue-100',
    iconColor: 'text-blue-600',
    icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z',
    steps: [
      '双手托天理三焦',
      '左右开弓似射雕',
      '调理脾胃须单举',
      '五劳七伤往后瞧',
      '摇头摆尾去心火',
      '两手攀足固肾腰',
      '攒拳怒目增气力',
      '背后七颠百病消'
    ]
  },
  {
    id: 2,
    name: '椅子瑜伽',
    description: '坐姿轻柔运动',
    duration: 20,
    calories: 40,
    intensity: '低',
    bgColor: 'bg-green-100',
    iconColor: 'text-green-600',
    icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
    steps: [
      '坐在椅子上，挺直腰背',
      '双手放在膝盖上，深呼吸',
      '缓慢转动头部，左右各5次',
      '双臂向上伸展，保持10秒',
      '身体前倾，双手触脚尖',
      '坐姿扭转，左右交替',
      '腿部抬起伸展',
      '深呼吸放松结束'
    ]
  },
  {
    id: 3,
    name: '关节保健操',
    description: '保护关节健康',
    duration: 10,
    calories: 30,
    intensity: '低',
    bgColor: 'bg-purple-100',
    iconColor: 'text-purple-600',
    icon: 'M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11',
    steps: [
      '手腕旋转，顺时针逆时针各10次',
      '手指张合练习，重复20次',
      '肩部画圈，前后各10次',
      '膝关节屈伸，左右各15次',
      '踝关节旋转，左右各10次',
      '颈部轻柔转动'
    ]
  },
  {
    id: 4,
    name: '呼吸训练',
    description: '增强肺活量',
    duration: 10,
    calories: 20,
    intensity: '低',
    bgColor: 'bg-cyan-100',
    iconColor: 'text-cyan-600',
    icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    steps: [
      '找一个安静舒适的位置坐下',
      '闭上眼睛，放松全身',
      '用鼻子缓慢吸气，数到4',
      '屏住呼吸，数到4',
      '用嘴巴缓慢呼气，数到6',
      '重复以上步骤10-15次',
      '练习腹式呼吸',
      '结束后静坐片刻'
    ]
  }
])

// 弹窗控制
const showExerciseModal = ref(false)
const currentExercise = ref(null)

// 方法
function startExercise(exercise) {
  const index = exercises.value.findIndex(e => e.id === exercise.id)
  if (index > -1) {
    exercises.value[index].completed = true
  }
}

function viewExerciseDetail(item) {
  currentExercise.value = item
  showExerciseModal.value = true
}

function startExerciseSession() {
  showExerciseModal.value = false
  alert(`开始${currentExercise.value.name}训练！`)
}
</script>

<style scoped>
.gradient-primary {
  background: linear-gradient(135deg, #FF6B35 0%, #f97316 100%);
}

.page-header {
  @apply bg-white px-4 py-4 shadow-sm;
}

.page-title {
  @apply text-xl font-bold text-gray-800;
}

.card {
  @apply bg-white rounded-2xl p-4 shadow-sm;
}
</style>
