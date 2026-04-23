<template>
  <div>
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">健康数据</h1>
      <button @click="exportReport" class="px-4 py-2 bg-primary-500 text-white rounded-lg flex items-center hover:bg-primary-600 transition-colors">
        <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        导出报告
      </button>
    </div>

    <!-- 老人选择 & 时间范围 -->
    <div class="flex flex-wrap gap-4 mb-6">
      <select v-model="selectedElder" class="px-4 py-2 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500">
        <option v-for="elder in elders" :key="elder.id" :value="elder.id">{{ elder.name }}</option>
      </select>
      <select v-model="timeRange" class="px-4 py-2 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500">
        <option value="7">最近7天</option>
        <option value="30">最近30天</option>
        <option value="90">最近3个月</option>
      </select>
    </div>

    <!-- 健康评分和指标卡片 -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-6">
      <!-- 健康评分仪表盘 -->
      <div class="bg-white rounded-xl p-5 shadow-sm">
        <h3 class="text-sm text-gray-500 mb-2">综合健康评分</h3>
        <GaugeChart
          :value="healthScore"
          :max="100"
          :segments="[
            { from: 0, to: 60, color: '#ef4444' },
            { from: 60, to: 80, color: '#f59e0b' },
            { from: 80, to: 100, color: '#10b981' }
          ]"
          :height="160"
        />
        <div class="text-center mt-2">
          <span :class="[
            'px-3 py-1 rounded-full text-sm font-medium',
            healthScore >= 80 ? 'bg-green-100 text-green-700' :
            healthScore >= 60 ? 'bg-yellow-100 text-yellow-700' :
            'bg-red-100 text-red-700'
          ]">
            {{ healthScore >= 80 ? '健康良好' : healthScore >= 60 ? '需要关注' : '需要干预' }}
          </span>
        </div>
      </div>

      <!-- 健康指标卡片 -->
      <div v-for="metric in healthMetrics" :key="metric.type" class="bg-white rounded-xl p-5 shadow-sm">
        <div class="flex items-center justify-between mb-3">
          <span class="text-gray-500">{{ metric.label }}</span>
          <span :class="[
            'px-2 py-1 rounded text-xs',
            metric.trend === 'up' ? 'bg-red-100 text-red-600' :
            metric.trend === 'down' ? 'bg-green-100 text-green-600' :
            'bg-gray-100 text-gray-600'
          ]">
            {{ metric.trendText }}
          </span>
        </div>
        <div class="flex items-baseline">
          <span class="text-3xl font-bold text-gray-800">{{ metric.value }}</span>
          <span class="text-gray-400 ml-2">{{ metric.unit }}</span>
        </div>
        <div class="mt-3 flex items-center text-sm">
          <span class="text-gray-500">正常范围：</span>
          <span class="text-gray-700">{{ metric.normalRange }}</span>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <!-- 血压趋势 -->
      <div class="bg-white rounded-xl p-6 shadow-sm">
        <h3 class="font-bold text-gray-800 mb-4">血压趋势</h3>
        <LineChart
          :data="bpLineChartData"
          :height="280"
          :showNormalRange="true"
          :normalRange="{ min: 90, max: 140 }"
        />
      </div>

      <!-- 心率趋势 -->
      <div class="bg-white rounded-xl p-6 shadow-sm">
        <h3 class="font-bold text-gray-800 mb-4">心率趋势</h3>
        <LineChart
          :data="hrLineChartData"
          :height="280"
          :showNormalRange="true"
          :normalRange="{ min: 60, max: 100 }"
        />
      </div>

      <!-- 血糖趋势 -->
      <div class="bg-white rounded-xl p-6 shadow-sm">
        <h3 class="font-bold text-gray-800 mb-4">血糖趋势</h3>
        <BarChart
          :data="bsBarChartData"
          :height="280"
        />
      </div>

      <!-- 健康指标分布 -->
      <div class="bg-white rounded-xl p-6 shadow-sm">
        <h3 class="font-bold text-gray-800 mb-4">测量状态分布</h3>
        <PieChart
          :data="statusPieData"
          :height="280"
        />
      </div>
    </div>

    <!-- 健康记录列表 -->
    <div class="bg-white rounded-xl shadow-sm">
      <div class="p-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="font-bold text-gray-800">健康记录</h3>
        <div class="flex gap-2">
          <button
            v-for="tab in recordTabs"
            :key="tab.value"
            :class="[
              'px-3 py-1 rounded-lg text-sm transition-colors',
              activeTab === tab.value ? 'bg-primary-100 text-primary-600' : 'text-gray-600 hover:bg-gray-100'
            ]"
            @click="activeTab = tab.value"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">时间</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">类型</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">数值</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">状态</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">备注</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="record in filteredRecords" :key="record.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 text-gray-800">{{ record.time }}</td>
              <td class="px-4 py-3">
                <span class="flex items-center gap-2">
                  <span :class="[
                    'w-2 h-2 rounded-full',
                    record.type === '血压' ? 'bg-red-400' :
                    record.type === '心率' ? 'bg-blue-400' :
                    'bg-amber-400'
                  ]"></span>
                  {{ record.type }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-800 font-medium">{{ record.value }}</td>
              <td class="px-4 py-3">
                <span :class="[
                  'px-2 py-1 rounded text-xs',
                  record.status === 'normal' ? 'bg-green-100 text-green-700' :
                  record.status === 'warning' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                ]">
                  {{ record.statusText }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-500">{{ record.note || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="p-4 border-t border-gray-100 flex items-center justify-between">
        <span class="text-sm text-gray-500">共 {{ filteredRecords.length }} 条记录</span>
        <div class="flex gap-2">
          <button
            @click="currentPage > 1 && currentPage--"
            :disabled="currentPage === 1"
            class="px-3 py-1 border border-gray-200 rounded text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50"
          >
            上一页
          </button>
          <span class="px-3 py-1 text-sm text-gray-600">{{ currentPage }} / {{ totalPages }}</span>
          <button
            @click="currentPage < totalPages && currentPage++"
            :disabled="currentPage === totalPages"
            class="px-3 py-1 border border-gray-200 rounded text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import LineChart from '@/components/charts/LineChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import GaugeChart from '@/components/charts/GaugeChart.vue'

const selectedElder = ref(1)
const timeRange = ref('7')
const activeTab = ref('all')
const currentPage = ref(1)
const pageSize = 10

const elders = ref([
  { id: 1, name: '王爷爷' },
  { id: 2, name: '李奶奶' }
])

const recordTabs = [
  { value: 'all', label: '全部' },
  { value: 'bp', label: '血压' },
  { value: 'hr', label: '心率' },
  { value: 'bs', label: '血糖' }
]

// 综合健康评分
const healthScore = ref(85)

// 健康指标
const healthMetrics = ref([
  { type: 'bp', label: '平均血压', value: '128/84', unit: 'mmHg', normalRange: '90-140/60-90', trend: 'stable', trendText: '稳定' },
  { type: 'hr', label: '平均心率', value: '73', unit: '次/分', normalRange: '60-100', trend: 'stable', trendText: '稳定' },
  { type: 'bs', label: '平均血糖', value: '5.8', unit: 'mmol/L', normalRange: '3.9-6.1', trend: 'up', trendText: '偏高' },
  { type: 'weight', label: '体重', value: '65.2', unit: 'kg', normalRange: '55-75', trend: 'down', trendText: '下降' }
])

// 血压折线图数据
const bpLineChartData = computed(() => ({
  xAxis: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  series: [
    {
      name: '收缩压',
      data: [125, 130, 128, 135, 126, 129, 125],
      color: '#ef4444'
    },
    {
      name: '舒张压',
      data: [82, 85, 83, 88, 81, 84, 82],
      color: '#f97316'
    }
  ]
}))

// 心率折线图数据
const hrLineChartData = computed(() => ({
  xAxis: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  series: [
    {
      name: '心率',
      data: [72, 75, 70, 78, 73, 71, 72],
      color: '#3b82f6'
    }
  ]
}))

// 血糖柱状图数据
const bsBarChartData = computed(() => ({
  xAxis: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  series: [
    {
      name: '空腹血糖',
      data: [5.6, 5.8, 5.5, 6.2, 5.7, 5.4, 5.8],
      color: '#f59e0b'
    },
    {
      name: '餐后血糖',
      data: [7.2, 7.5, 7.0, 8.1, 7.3, 7.1, 7.4],
      color: '#fbbf24'
    }
  ]
}))

// 测量状态分布饼图数据
const statusPieData = computed(() => ({
  series: [
    { name: '正常', value: 42, color: '#10b981' },
    { name: '偏高', value: 8, color: '#f59e0b' },
    { name: '偏低', value: 3, color: '#3b82f6' },
    { name: '异常', value: 2, color: '#ef4444' }
  ]
}))

// 健康记录
const healthRecords = ref([
  { id: 1, time: '今天 08:30', type: '血压', value: '125/82 mmHg', status: 'normal', statusText: '正常', note: '' },
  { id: 2, time: '今天 08:30', type: '心率', value: '72 次/分', status: 'normal', statusText: '正常', note: '' },
  { id: 3, time: '今天 07:00', type: '血糖', value: '6.2 mmol/L', status: 'warning', statusText: '偏高', note: '空腹血糖' },
  { id: 4, time: '昨天 20:30', type: '血压', value: '130/85 mmHg', status: 'normal', statusText: '正常', note: '' },
  { id: 5, time: '昨天 08:30', type: '血压', value: '128/84 mmHg', status: 'normal', statusText: '正常', note: '' },
  { id: 6, time: '昨天 07:00', type: '血糖', value: '5.6 mmol/L', status: 'normal', statusText: '正常', note: '空腹血糖' },
  { id: 7, time: '前天 20:30', type: '心率', value: '78 次/分', status: 'normal', statusText: '正常', note: '' },
  { id: 8, time: '前天 08:30', type: '血压', value: '135/88 mmHg', status: 'warning', statusText: '偏高', note: '运动后' },
  { id: 9, time: '前天 07:00', type: '血糖', value: '5.5 mmol/L', status: 'normal', statusText: '正常', note: '空腹血糖' },
  { id: 10, time: '3天前 08:30', type: '血压', value: '126/81 mmHg', status: 'normal', statusText: '正常', note: '' }
])

// 筛选后的记录
const filteredRecords = computed(() => {
  let records = healthRecords.value
  if (activeTab.value !== 'all') {
    const typeMap = { bp: '血压', hr: '心率', bs: '血糖' }
    records = records.filter(r => r.type === typeMap[activeTab.value])
  }
  return records
})

// 总页数
const totalPages = computed(() => Math.ceil(filteredRecords.value.length / pageSize) || 1)

// 监听筛选变化重置页码
watch([activeTab, selectedElder, timeRange], () => {
  currentPage.value = 1
})

// 导出报告
function exportReport() {
  // 模拟导出
  alert('报告导出功能开发中...')
}
</script>
