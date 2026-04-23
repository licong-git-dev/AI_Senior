<template>
  <div ref="chartRef" :style="{ width: width, height: height }"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
    // 格式: [{ date: '2024-01-01', value: 120 }, ...]
  },
  title: String,
  unit: {
    type: String,
    default: ''
  },
  color: {
    type: String,
    default: '#FF6B35'
  },
  width: {
    type: String,
    default: '100%'
  },
  height: {
    type: String,
    default: '200px'
  },
  showArea: {
    type: Boolean,
    default: true
  },
  smooth: {
    type: Boolean,
    default: true
  },
  normalRange: {
    type: Array,
    default: () => []
    // 格式: [min, max]
  }
})

const chartRef = ref(null)
let chart = null

const xAxisData = computed(() => props.data.map(item => item.date))
const seriesData = computed(() => props.data.map(item => item.value))

function initChart() {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)

  const option = {
    title: props.title ? {
      text: props.title,
      left: 'left',
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#374151'
      }
    } : undefined,
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#374151'
      },
      formatter: (params) => {
        const data = params[0]
        return `${data.name}<br/>${data.value}${props.unit}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: props.title ? '15%' : '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxisData.value,
      boundaryGap: false,
      axisLine: {
        lineStyle: { color: '#e5e7eb' }
      },
      axisTick: { show: false },
      axisLabel: {
        color: '#9ca3af',
        fontSize: 12
      }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: {
        lineStyle: { color: '#f3f4f6', type: 'dashed' }
      },
      axisLabel: {
        color: '#9ca3af',
        fontSize: 12,
        formatter: `{value}${props.unit}`
      }
    },
    series: [
      // 正常范围区域
      ...(props.normalRange.length === 2 ? [{
        type: 'line',
        data: new Array(xAxisData.value.length).fill(props.normalRange[1]),
        lineStyle: { opacity: 0 },
        areaStyle: { color: 'rgba(34, 197, 94, 0.1)' },
        symbol: 'none'
      }, {
        type: 'line',
        data: new Array(xAxisData.value.length).fill(props.normalRange[0]),
        lineStyle: { opacity: 0 },
        areaStyle: { color: '#fff' },
        symbol: 'none'
      }] : []),
      // 数据线
      {
        type: 'line',
        data: seriesData.value,
        smooth: props.smooth,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          color: props.color,
          width: 3
        },
        itemStyle: {
          color: props.color,
          borderColor: '#fff',
          borderWidth: 2
        },
        areaStyle: props.showArea ? {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: props.color + '40' },
            { offset: 1, color: props.color + '05' }
          ])
        } : undefined
      }
    ]
  }

  chart.setOption(option)
}

function handleResize() {
  chart?.resize()
}

watch(() => props.data, () => {
  if (chart) {
    initChart()
  }
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>
