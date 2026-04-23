declare module 'echarts-for-react' {
  import { EChartsOption } from 'echarts'
  import React from 'react'

  export interface ReactEChartsProps {
    option: EChartsOption
    style?: React.CSSProperties
    notMerge?: boolean
    lazyUpdate?: boolean
    theme?: string | object
    onChartReady?: (instance: any) => void
    onEvents?: Record<string, Function>
    opts?: {
      devicePixelRatio?: number
      renderer?: 'canvas' | 'svg'
      width?: number | string
      height?: number | string
    }
  }

  export default class ReactECharts extends React.Component<ReactEChartsProps> {}
}
