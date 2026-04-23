<template>
  <div ref="chartRef" :style="{ width: width, height: height }"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  value: {
    type: Number,
    default: 0
  },
  max: {
    type: Number,
    default: 100
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
  bgColor: {
    type: String,
    default: '#f3f4f6'
  },
  width: {
    type: String,
    default: '100%'
  },
  height: {
    type: String,
    default: '200px'
  },
  lineWidth: {
    type: Number,
    default: 12
  },
  showValue: {
    type: Boolean,
    default: true
  },
  status: {
    type: String,
    default: ''
  }
})

const chartRef = ref(null)
let chart = null

const percentage = computed(() => Math.round((props.value / props.max) * 100))

function initChart() {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)

  const option = {
    series: [
      // 背景环
      {
        type: 'pie',
        radius: ['70%', `${70 + props.lineWidth}%`],
        center: ['50%', '50%'],
        silent: true,
        label: { show: false },
        data: [{ value: 100, itemStyle: { color: props.bgColor } }]
      },
      // 数据环
      {
        type: 'pie',
        radius: ['70%', `${70 + props.lineWidth}%`],
        center: ['50%', '50%'],
        startAngle: 90,
        silent: true,
        label: { show: false },
        data: [
          {
            value: props.value,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: props.color },
                { offset: 1, color: props.color + 'cc' }
              ]),
              borderRadius: 10
            }
          },
          {
            value: props.max - props.value,
            itemStyle: { color: 'transparent' }
          }
        ]
      }
    ],
    graphic: props.showValue ? [
      {
        type: 'group',
        left: 'center',
        top: 'center',
        children: [
          {
            type: 'text',
            style: {
              text: `${props.value}${props.unit}`,
              fontSize: 28,
              fontWeight: 'bold',
              fill: '#374151',
              textAlign: 'center'
            },
            left: 'center',
            top: -15
          },
          ...(props.title ? [{
            type: 'text',
            style: {
              text: props.title,
              fontSize: 14,
              fill: '#9ca3af',
              textAlign: 'center'
            },
            left: 'center',
            top: 20
          }] : []),
          ...(props.status ? [{
            type: 'text',
            style: {
              text: props.status,
              fontSize: 12,
              fill: props.color,
              textAlign: 'center'
            },
            left: 'center',
            top: props.title ? 42 : 20
          }] : [])
        ]
      }
    ] : []
  }

  chart.setOption(option)
}

function handleResize() {
  chart?.resize()
}

watch([() => props.value, () => props.max], () => {
  if (chart) {
    initChart()
  }
})

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>
