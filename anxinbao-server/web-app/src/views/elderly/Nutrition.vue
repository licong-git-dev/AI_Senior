<template>
  <div class="min-h-screen pb-20">
    <!-- 页头 -->
    <div class="page-header">
      <h1 class="page-title">营养管理</h1>
    </div>

    <!-- 今日营养概览 -->
    <div class="px-4 pt-4">
      <div class="card gradient-primary text-white">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p class="text-primary-100">今日摄入</p>
            <div class="text-4xl font-bold mt-1">{{ totalCalories }}</div>
            <p class="text-primary-100">/ {{ targetCalories }} 千卡</p>
          </div>
          <div class="w-24 h-24 relative">
            <svg viewBox="0 0 100 100" class="w-full h-full">
              <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="8"/>
              <circle cx="50" cy="50" r="40" fill="none" stroke="white" stroke-width="8"
                :stroke-dasharray="251.2" :stroke-dashoffset="251.2 * (1 - calorieProgress)" stroke-linecap="round"
                transform="rotate(-90 50 50)"/>
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-xl font-bold">{{ Math.round(calorieProgress * 100) }}%</span>
            </div>
          </div>
        </div>

        <!-- 三大营养素 -->
        <div class="grid grid-cols-3 gap-3">
          <div class="bg-white/20 rounded-xl p-3 text-center">
            <p class="text-xs text-white/80">碳水</p>
            <p class="text-lg font-bold">{{ nutrients.carbs }}g</p>
            <div class="w-full h-1 bg-white/30 rounded-full mt-1">
              <div class="h-full bg-white rounded-full" :style="{ width: (nutrients.carbs / 300 * 100) + '%' }"></div>
            </div>
          </div>
          <div class="bg-white/20 rounded-xl p-3 text-center">
            <p class="text-xs text-white/80">蛋白质</p>
            <p class="text-lg font-bold">{{ nutrients.protein }}g</p>
            <div class="w-full h-1 bg-white/30 rounded-full mt-1">
              <div class="h-full bg-white rounded-full" :style="{ width: (nutrients.protein / 60 * 100) + '%' }"></div>
            </div>
          </div>
          <div class="bg-white/20 rounded-xl p-3 text-center">
            <p class="text-xs text-white/80">脂肪</p>
            <p class="text-lg font-bold">{{ nutrients.fat }}g</p>
            <div class="w-full h-1 bg-white/30 rounded-full mt-1">
              <div class="h-full bg-white rounded-full" :style="{ width: (nutrients.fat / 60 * 100) + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 今日饮食记录 -->
    <div class="px-4 mt-4">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-800">今日饮食</h2>
          <button @click="showAddMealModal = true" class="text-primary-500">添加记录</button>
        </div>

        <div class="space-y-3">
          <div v-for="meal in todayMeals" :key="meal.id" class="bg-gray-50 rounded-xl p-4">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center">
                <span class="text-2xl mr-3">{{ meal.icon }}</span>
                <div>
                  <p class="font-medium text-gray-800">{{ meal.type }}</p>
                  <p class="text-xs text-gray-500">{{ meal.time }}</p>
                </div>
              </div>
              <div class="text-right">
                <p class="font-bold text-primary-600">{{ meal.calories }} 千卡</p>
              </div>
            </div>
            <div class="flex flex-wrap gap-2 mt-2">
              <span v-for="(food, i) in meal.foods" :key="i" class="px-2 py-1 bg-white rounded-full text-xs text-gray-600">
                {{ food }}
              </span>
            </div>
          </div>

          <div v-if="todayMeals.length === 0" class="text-center py-8 text-gray-400">
            <svg class="w-12 h-12 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <p>还没有记录，点击添加</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 饮水记录 -->
    <div class="px-4 mt-4">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-800">饮水记录</h2>
          <span class="text-sm text-gray-500">{{ waterIntake }} / {{ waterTarget }} ml</span>
        </div>

        <div class="flex justify-center gap-2 mb-4">
          <div v-for="i in 8" :key="i" class="flex flex-col items-center">
            <div
              :class="[
                'w-8 h-12 rounded-lg flex items-end justify-center overflow-hidden transition-all',
                i <= waterCups ? 'bg-blue-500' : 'bg-gray-200'
              ]"
            >
              <svg v-if="i <= waterCups" class="w-6 h-6 text-white mb-1" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2c-5.33 4.55-8 8.48-8 11.8 0 4.98 3.8 8.2 8 8.2s8-3.22 8-8.2c0-3.32-2.67-7.25-8-11.8z"/>
              </svg>
            </div>
          </div>
        </div>

        <div class="flex gap-3">
          <button
            v-for="amount in waterOptions"
            :key="amount"
            @click="addWater(amount)"
            class="flex-1 py-3 bg-blue-50 text-blue-600 rounded-xl font-medium hover:bg-blue-100"
          >
            +{{ amount }}ml
          </button>
        </div>
      </div>
    </div>

    <!-- 营养趋势 -->
    <div class="px-4 mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">7日营养趋势</h2>

        <div class="h-40 flex items-end justify-between gap-2">
          <div v-for="(day, i) in weekNutrition" :key="i" class="flex-1 flex flex-col items-center">
            <div class="w-full flex flex-col gap-0.5" :style="{ height: '120px' }">
              <div class="w-full bg-orange-400 rounded-t" :style="{ height: (day.fat / 60 * 40) + 'px' }"></div>
              <div class="w-full bg-red-400" :style="{ height: (day.protein / 60 * 40) + 'px' }"></div>
              <div class="w-full bg-yellow-400 rounded-b" :style="{ height: (day.carbs / 300 * 40) + 'px' }"></div>
            </div>
            <span class="text-xs text-gray-500 mt-2">{{ day.label }}</span>
          </div>
        </div>

        <div class="flex justify-center gap-6 mt-4">
          <div class="flex items-center">
            <div class="w-3 h-3 bg-yellow-400 rounded mr-2"></div>
            <span class="text-xs text-gray-600">碳水</span>
          </div>
          <div class="flex items-center">
            <div class="w-3 h-3 bg-red-400 rounded mr-2"></div>
            <span class="text-xs text-gray-600">蛋白质</span>
          </div>
          <div class="flex items-center">
            <div class="w-3 h-3 bg-orange-400 rounded mr-2"></div>
            <span class="text-xs text-gray-600">脂肪</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 营养素详情 -->
    <div class="px-4 mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">营养素摄入</h2>

        <div class="space-y-4">
          <div v-for="nutrient in nutrientDetails" :key="nutrient.name">
            <div class="flex items-center justify-between mb-1">
              <span class="text-gray-700">{{ nutrient.name }}</span>
              <span class="text-sm">
                <span :class="nutrient.current >= nutrient.target ? 'text-green-600' : 'text-gray-600'">
                  {{ nutrient.current }}{{ nutrient.unit }}
                </span>
                <span class="text-gray-400"> / {{ nutrient.target }}{{ nutrient.unit }}</span>
              </span>
            </div>
            <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                :class="['h-full rounded-full transition-all', nutrient.color]"
                :style="{ width: Math.min(nutrient.current / nutrient.target * 100, 100) + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 饮食建议 -->
    <div class="px-4 mt-4">
      <div class="card">
        <h2 class="text-lg font-bold text-gray-800 mb-4">饮食建议</h2>

        <div class="space-y-3">
          <div v-for="tip in dietTips" :key="tip.id" class="flex items-start p-3 bg-gray-50 rounded-xl">
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

    <!-- 推荐食谱 -->
    <div class="px-4 mt-4 mb-6">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-800">推荐食谱</h2>
          <button class="text-primary-500 text-sm">查看更多</button>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div
            v-for="recipe in recommendedRecipes"
            :key="recipe.id"
            @click="showRecipeDetail(recipe)"
            class="bg-gray-50 rounded-xl overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
          >
            <div class="h-24 bg-gradient-to-br from-orange-100 to-yellow-100 flex items-center justify-center">
              <span class="text-4xl">{{ recipe.emoji }}</span>
            </div>
            <div class="p-3">
              <p class="font-medium text-gray-800 text-sm">{{ recipe.name }}</p>
              <p class="text-xs text-gray-500 mt-1">{{ recipe.calories }} 千卡</p>
              <div class="flex gap-1 mt-2">
                <span v-for="tag in recipe.tags" :key="tag" class="px-1.5 py-0.5 bg-white rounded text-xs text-gray-500">
                  {{ tag }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加饮食记录弹窗 -->
    <div v-if="showAddMealModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-md max-h-[80vh] overflow-hidden">
        <div class="p-4 border-b flex items-center justify-between">
          <h3 class="text-lg font-bold">添加饮食记录</h3>
          <button @click="showAddMealModal = false" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-4 overflow-y-auto max-h-[60vh] space-y-4">
          <!-- 餐次选择 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">餐次</label>
            <div class="grid grid-cols-4 gap-2">
              <button
                v-for="type in mealTypes"
                :key="type.value"
                @click="newMeal.type = type.value"
                :class="[
                  'p-3 rounded-xl text-center transition-all',
                  newMeal.type === type.value ? 'bg-primary-500 text-white' : 'bg-gray-100'
                ]"
              >
                <span class="text-xl block">{{ type.icon }}</span>
                <span class="text-xs mt-1 block">{{ type.label }}</span>
              </button>
            </div>
          </div>

          <!-- 时间 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">用餐时间</label>
            <input type="time" v-model="newMeal.time" class="w-full p-3 bg-gray-50 rounded-xl border-none">
          </div>

          <!-- 食物搜索 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">添加食物</label>
            <input
              type="text"
              v-model="foodSearch"
              placeholder="搜索食物..."
              class="w-full p-3 bg-gray-50 rounded-xl border-none mb-2"
            >

            <!-- 常用食物 -->
            <div class="flex flex-wrap gap-2">
              <button
                v-for="food in commonFoods"
                :key="food.name"
                @click="addFood(food)"
                class="px-3 py-1.5 bg-gray-100 rounded-full text-sm hover:bg-primary-100"
              >
                {{ food.emoji }} {{ food.name }}
              </button>
            </div>
          </div>

          <!-- 已添加食物 -->
          <div v-if="newMeal.foods.length > 0">
            <label class="block text-sm font-medium text-gray-700 mb-2">已添加</label>
            <div class="space-y-2">
              <div
                v-for="(food, i) in newMeal.foods"
                :key="i"
                class="flex items-center justify-between p-3 bg-gray-50 rounded-xl"
              >
                <span>{{ food.emoji }} {{ food.name }}</span>
                <div class="flex items-center gap-3">
                  <span class="text-sm text-gray-500">{{ food.calories }}千卡</span>
                  <button @click="removeFood(i)" class="text-red-500">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 总热量 -->
          <div class="p-4 bg-primary-50 rounded-xl">
            <div class="flex items-center justify-between">
              <span class="text-gray-700">本餐总热量</span>
              <span class="text-2xl font-bold text-primary-600">{{ mealTotalCalories }} 千卡</span>
            </div>
          </div>
        </div>

        <div class="p-4 border-t">
          <button
            @click="saveMeal"
            :disabled="newMeal.foods.length === 0"
            class="w-full btn-primary disabled:opacity-50"
          >
            保存记录
          </button>
        </div>
      </div>
    </div>

    <!-- 食谱详情弹窗 -->
    <div v-if="showRecipeModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-md max-h-[80vh] overflow-hidden">
        <div class="p-4 border-b flex items-center justify-between">
          <h3 class="text-lg font-bold">{{ selectedRecipe?.name }}</h3>
          <button @click="showRecipeModal = false" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-4 overflow-y-auto max-h-[60vh]">
          <div class="h-40 bg-gradient-to-br from-orange-100 to-yellow-100 rounded-xl flex items-center justify-center mb-4">
            <span class="text-6xl">{{ selectedRecipe?.emoji }}</span>
          </div>

          <div class="grid grid-cols-3 gap-3 mb-4">
            <div class="text-center p-3 bg-orange-50 rounded-xl">
              <p class="text-xl font-bold text-orange-600">{{ selectedRecipe?.calories }}</p>
              <p class="text-xs text-orange-500">千卡</p>
            </div>
            <div class="text-center p-3 bg-blue-50 rounded-xl">
              <p class="text-xl font-bold text-blue-600">{{ selectedRecipe?.prepTime }}</p>
              <p class="text-xs text-blue-500">分钟</p>
            </div>
            <div class="text-center p-3 bg-green-50 rounded-xl">
              <p class="text-xl font-bold text-green-600">{{ selectedRecipe?.difficulty }}</p>
              <p class="text-xs text-green-500">难度</p>
            </div>
          </div>

          <div class="mb-4">
            <h4 class="font-medium text-gray-800 mb-2">食材</h4>
            <div class="flex flex-wrap gap-2">
              <span v-for="ing in selectedRecipe?.ingredients" :key="ing" class="px-3 py-1 bg-gray-100 rounded-full text-sm">
                {{ ing }}
              </span>
            </div>
          </div>

          <div>
            <h4 class="font-medium text-gray-800 mb-2">做法</h4>
            <ol class="space-y-2">
              <li v-for="(step, i) in selectedRecipe?.steps" :key="i" class="flex">
                <span class="w-6 h-6 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-sm mr-3 flex-shrink-0">
                  {{ i + 1 }}
                </span>
                <span class="text-gray-600 text-sm">{{ step }}</span>
              </li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// 目标值
const targetCalories = ref(1800)
const waterTarget = ref(2000)

// 今日营养数据
const nutrients = ref({
  carbs: 180,
  protein: 45,
  fat: 40
})

const totalCalories = computed(() => {
  return todayMeals.value.reduce((sum, meal) => sum + meal.calories, 0)
})

const calorieProgress = computed(() => {
  return Math.min(totalCalories.value / targetCalories.value, 1)
})

// 今日饮食
const todayMeals = ref([
  {
    id: 1,
    type: '早餐',
    icon: '🌅',
    time: '07:30',
    calories: 350,
    foods: ['牛奶', '鸡蛋', '全麦面包', '苹果']
  },
  {
    id: 2,
    type: '午餐',
    icon: '☀️',
    time: '12:00',
    calories: 580,
    foods: ['米饭', '清炒时蔬', '红烧鱼', '紫菜汤']
  },
  {
    id: 3,
    type: '下午茶',
    icon: '🍵',
    time: '15:30',
    calories: 120,
    foods: ['绿茶', '坚果']
  }
])

// 饮水
const waterIntake = ref(1200)
const waterCups = computed(() => Math.floor(waterIntake.value / 250))
const waterOptions = [150, 250, 500]

const addWater = (amount) => {
  waterIntake.value = Math.min(waterIntake.value + amount, waterTarget.value + 500)
}

// 7日营养趋势
const weekNutrition = ref([
  { label: '周一', carbs: 200, protein: 50, fat: 45 },
  { label: '周二', carbs: 180, protein: 55, fat: 40 },
  { label: '周三', carbs: 220, protein: 48, fat: 50 },
  { label: '周四', carbs: 190, protein: 52, fat: 42 },
  { label: '周五', carbs: 210, protein: 45, fat: 48 },
  { label: '周六', carbs: 230, protein: 58, fat: 55 },
  { label: '周日', carbs: 180, protein: 45, fat: 40 }
])

// 营养素详情
const nutrientDetails = ref([
  { name: '膳食纤维', current: 18, target: 25, unit: 'g', color: 'bg-green-500' },
  { name: '维生素C', current: 65, target: 100, unit: 'mg', color: 'bg-orange-500' },
  { name: '钙', current: 600, target: 1000, unit: 'mg', color: 'bg-blue-500' },
  { name: '铁', current: 12, target: 15, unit: 'mg', color: 'bg-red-500' },
  { name: '钾', current: 2800, target: 3500, unit: 'mg', color: 'bg-purple-500' }
])

// 饮食建议
const dietTips = ref([
  {
    id: 1,
    title: '增加蔬菜摄入',
    content: '今日蔬菜摄入不足，建议晚餐多吃绿叶蔬菜。',
    emoji: '🥬',
    bgColor: 'bg-green-100'
  },
  {
    id: 2,
    title: '注意补钙',
    content: '钙摄入偏低，建议喝杯牛奶或吃些豆制品。',
    emoji: '🥛',
    bgColor: 'bg-blue-100'
  },
  {
    id: 3,
    title: '控制盐分',
    content: '保持清淡饮食，每日盐分摄入不超过6克。',
    emoji: '🧂',
    bgColor: 'bg-yellow-100'
  }
])

// 推荐食谱
const recommendedRecipes = ref([
  {
    id: 1,
    name: '清蒸鲈鱼',
    emoji: '🐟',
    calories: 180,
    prepTime: 20,
    difficulty: '简单',
    tags: ['高蛋白', '低脂'],
    ingredients: ['鲈鱼', '葱姜', '蒸鱼豉油', '香菜'],
    steps: [
      '鲈鱼处理干净，两面划刀',
      '铺上葱姜丝，上锅蒸8分钟',
      '淋上热油和蒸鱼豉油',
      '撒上香菜即可'
    ]
  },
  {
    id: 2,
    name: '番茄蛋花汤',
    emoji: '🍅',
    calories: 85,
    prepTime: 15,
    difficulty: '简单',
    tags: ['维生素', '开胃'],
    ingredients: ['番茄', '鸡蛋', '葱花', '盐'],
    steps: [
      '番茄切块，鸡蛋打散',
      '油热后下番茄翻炒',
      '加水煮开后淋入蛋液',
      '加盐调味，撒葱花'
    ]
  },
  {
    id: 3,
    name: '蒜蓉西兰花',
    emoji: '🥦',
    calories: 65,
    prepTime: 10,
    difficulty: '简单',
    tags: ['高纤维', '抗氧化'],
    ingredients: ['西兰花', '蒜末', '盐', '生抽'],
    steps: [
      '西兰花切小朵焯水',
      '热油爆香蒜末',
      '放入西兰花翻炒',
      '加盐和生抽调味'
    ]
  },
  {
    id: 4,
    name: '小米南瓜粥',
    emoji: '🎃',
    calories: 120,
    prepTime: 40,
    difficulty: '简单',
    tags: ['养胃', '易消化'],
    ingredients: ['小米', '南瓜', '枸杞'],
    steps: [
      '小米洗净，南瓜切块',
      '加水大火煮开',
      '转小火煮30分钟',
      '加入枸杞即可'
    ]
  }
])

const showRecipeModal = ref(false)
const selectedRecipe = ref(null)

const showRecipeDetail = (recipe) => {
  selectedRecipe.value = recipe
  showRecipeModal.value = true
}

// 添加饮食记录
const showAddMealModal = ref(false)
const foodSearch = ref('')
const mealTypes = [
  { value: 'breakfast', label: '早餐', icon: '🌅' },
  { value: 'lunch', label: '午餐', icon: '☀️' },
  { value: 'dinner', label: '晚餐', icon: '🌙' },
  { value: 'snack', label: '加餐', icon: '🍵' }
]

const commonFoods = [
  { name: '米饭', emoji: '🍚', calories: 130 },
  { name: '面条', emoji: '🍜', calories: 150 },
  { name: '鸡蛋', emoji: '🥚', calories: 78 },
  { name: '牛奶', emoji: '🥛', calories: 65 },
  { name: '苹果', emoji: '🍎', calories: 52 },
  { name: '香蕉', emoji: '🍌', calories: 89 },
  { name: '鸡胸肉', emoji: '🍗', calories: 165 },
  { name: '青菜', emoji: '🥬', calories: 15 },
  { name: '豆腐', emoji: '🧈', calories: 76 },
  { name: '鱼', emoji: '🐟', calories: 120 }
]

const newMeal = ref({
  type: 'breakfast',
  time: '08:00',
  foods: []
})

const mealTotalCalories = computed(() => {
  return newMeal.value.foods.reduce((sum, food) => sum + food.calories, 0)
})

const addFood = (food) => {
  newMeal.value.foods.push({ ...food })
}

const removeFood = (index) => {
  newMeal.value.foods.splice(index, 1)
}

const saveMeal = () => {
  if (newMeal.value.foods.length === 0) return

  const mealType = mealTypes.find(t => t.value === newMeal.value.type)
  todayMeals.value.push({
    id: Date.now(),
    type: mealType.label,
    icon: mealType.icon,
    time: newMeal.value.time,
    calories: mealTotalCalories.value,
    foods: newMeal.value.foods.map(f => f.name)
  })

  // 重置表单
  newMeal.value = {
    type: 'breakfast',
    time: '08:00',
    foods: []
  }
  showAddMealModal.value = false
}
</script>
