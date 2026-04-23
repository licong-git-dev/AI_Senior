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
    // 格式: [{ name: '周一', value: 85 }, ...]
  },
  title: String,
  color: {
    type: [String, Array],
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
  horizontal: {
    type: Boolean,
    default: false
  },
  showLabel: {
    type: Boolean,
    default: true
  },
  barWidth: {
    type: [Number, String],
    default: 'auto'
  }
})

const chartRef = ref(null)
let chart = null

const xAxisData = computed(() => props.data.map(item => item.name))
const seriesData = computed(() => props.data.map(item => item.value))

const barColors = computed(() => {
  if (Array.isArray(props.color)) {
    return props.color
  }
  return props.data.map(() => props.color)
})

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
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: { color: '#374151' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: props.title ? '15%' : '3%',
      containLabel: true
    },
    xAxis: {
      type: props.horizontal ? 'value' : 'category',
      data: props.horizontal ? undefined : xAxisData.value,
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisTick: { show: false },
      axisLabel: { color: '#9ca3af', fontSize: 12 },
      splitLine: props.horizontal ? { lineStyle: { color: '#f3f4f6', type: 'dashed' } } : undefined
    },
    yAxis: {
      type: props.horizontal ? 'category' : 'value',
      data: props.horizontal ? xAxisData.value : undefined,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: props.horizontal ? undefined : { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
      axisLabel: { color: '#9ca3af', fontSize: 12 }
    },
    series: [{
      type: 'bar',
      data: seriesData.value.map((value, index) => ({
        value,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(
            props.horizontal ? 0 : 0,
            props.horizontal ? 0 : 1,
            props.horizontal ? 1 : 0,
            props.horizontal ? 0 : 0,
            [
              { offset: 0, color: barColors.value[index % barColors.value.length] },
              { offset: 1, color: barColors.value[index % barColors.value.length] + 'aa' }
            ]
          ),
          borderRadius: props.horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]
        }
      })),
      barWidth: props.barWidth,
      label: props.showLabel ? {
        show: true,
        position: props.horizontal ? 'right' : 'top',
        color: '#6b7280',
        fontSize: 12
      } : undefined
    }]
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
