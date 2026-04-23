/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // 老年友好的配色方案
      colors: {
        // 主色调 - 温暖的橙色系
        primary: {
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316',  // 主色
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12',
        },
        // 辅助色 - 舒适的绿色
        secondary: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',  // 辅助色
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        // 安全/紧急 - 醒目的红色
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',  // 警告色
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        // 健康状态颜色
        health: {
          normal: '#22c55e',
          warning: '#f59e0b',
          danger: '#ef4444',
          info: '#3b82f6',
        },
        // 背景色 - 柔和舒适
        surface: {
          light: '#fafafa',
          DEFAULT: '#f5f5f5',
          dark: '#e5e5e5',
        }
      },
      // 老年友好的字体大小
      fontSize: {
        'xs': ['0.875rem', { lineHeight: '1.25rem' }],     // 14px
        'sm': ['1rem', { lineHeight: '1.5rem' }],          // 16px
        'base': ['1.125rem', { lineHeight: '1.75rem' }],   // 18px - 默认
        'lg': ['1.25rem', { lineHeight: '1.875rem' }],     // 20px
        'xl': ['1.5rem', { lineHeight: '2rem' }],          // 24px
        '2xl': ['1.75rem', { lineHeight: '2.25rem' }],     // 28px
        '3xl': ['2rem', { lineHeight: '2.5rem' }],         // 32px
        '4xl': ['2.5rem', { lineHeight: '3rem' }],         // 40px
        '5xl': ['3rem', { lineHeight: '3.5rem' }],         // 48px
      },
      // 间距 - 更大的触摸目标
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      // 圆角
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      },
      // 阴影
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'card': '0 4px 20px -2px rgba(0, 0, 0, 0.1)',
      },
      // 动画
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-gentle': 'bounce 2s infinite',
      },
      // 最小高度 - 确保触摸目标足够大
      minHeight: {
        'touch': '48px',  // 最小触摸目标
        'button': '56px', // 按钮最小高度
      },
      // 最小宽度
      minWidth: {
        'touch': '48px',
        'button': '120px',
      }
    },
  },
  plugins: [],
  // 暗色模式支持
  darkMode: 'class',
}
