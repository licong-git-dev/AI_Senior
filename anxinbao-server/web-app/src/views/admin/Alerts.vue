<template>
  <div>
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">告警管理</h1>
        <p class="text-gray-500 mt-1">实时监控和处理系统告警</p>
      </div>
      <div class="flex gap-2">
        <button
          @click="refreshAlerts"
          :class="['px-4 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 flex items-center', refreshing && 'opacity-50']"
          :disabled="refreshing"
        >
          <svg :class="['w-5 h-5 mr-2', refreshing && 'animate-spin']" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          刷新
        </button>
        <button @click="exportAlerts" class="px-4 py-2 bg-primary-500 text-white rounded-lg flex items-center">
          <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          导出报告
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      <div class="bg-white rounded-xl p-4 shadow-sm border-l-4 border-gray-400">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">全部告警</p>
            <p class="text-2xl font-bold text-gray-800 mt-1">{{ stats.total }}</p>
          </div>
          <div class="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm border-l-4 border-red-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">紧急告警</p>
            <p class="text-2xl font-bold text-red-600 mt-1">{{ stats.critical }}</p>
          </div>
          <div class="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm border-l-4 border-yellow-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">待处理</p>
            <p class="text-2xl font-bold text-yellow-600 mt-1">{{ stats.pending }}</p>
          </div>
          <div class="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm border-l-4 border-blue-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">处理中</p>
            <p class="text-2xl font-bold text-blue-600 mt-1">{{ stats.handling }}</p>
          </div>
          <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm border-l-4 border-green-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">已解决</p>
            <p class="text-2xl font-bold text-green-600 mt-1">{{ stats.resolved }}</p>
          </div>
          <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选和搜索 -->
    <div class="bg-white rounded-xl p-4 shadow-sm mb-6">
      <div class="flex flex-wrap gap-4">
        <div class="flex-1 min-w-[200px]">
          <input
            type="text"
            v-model="filters.keyword"
            placeholder="搜索告警标题/用户名..."
            class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <select v-model="filters.type" class="px-4 py-2 border border-gray-200 rounded-lg">
          <option value="all">全部类型</option>
          <option value="health">健康异常</option>
          <option value="medication">用药提醒</option>
          <option value="device">设备告警</option>
          <option value="sos">SOS求助</option>
          <option value="fence">电子围栏</option>
        </select>
        <select v-model="filters.level" class="px-4 py-2 border border-gray-200 rounded-lg">
          <option value="all">全部级别</option>
          <option value="critical">紧急</option>
          <option value="high">高</option>
          <option value="medium">中</option>
          <option value="low">低</option>
        </select>
        <select v-model="filters.status" class="px-4 py-2 border border-gray-200 rounded-lg">
          <option value="all">全部状态</option>
          <option value="pending">待处理</option>
          <option value="handling">处理中</option>
          <option value="resolved">已解决</option>
          <option value="ignored">已忽略</option>
        </select>
        <input
          type="date"
          v-model="filters.startDate"
          class="px-4 py-2 border border-gray-200 rounded-lg"
        />
        <span class="flex items-center text-gray-400">至</span>
        <input
          type="date"
          v-model="filters.endDate"
          class="px-4 py-2 border border-gray-200 rounded-lg"
        />
        <button @click="resetFilters" class="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50">
          重置
        </button>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedAlerts.length > 0" class="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4 flex items-center justify-between">
      <span class="text-blue-700">已选择 {{ selectedAlerts.length }} 条告警</span>
      <div class="flex gap-2">
        <button @click="batchHandle('handling')" class="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm">
          批量处理
        </button>
        <button @click="batchHandle('resolved')" class="px-4 py-2 bg-green-500 text-white rounded-lg text-sm">
          批量解决
        </button>
        <button @click="batchHandle('ignored')" class="px-4 py-2 bg-gray-500 text-white rounded-lg text-sm">
          批量忽略
        </button>
        <button @click="selectedAlerts = []" class="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm">
          取消选择
        </button>
      </div>
    </div>

    <!-- 告警列表 -->
    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500 w-10">
                <input
                  type="checkbox"
                  class="rounded border-gray-300"
                  :checked="isAllSelected"
                  @change="toggleSelectAll"
                />
              </th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">级别</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">告警信息</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">用户</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">类型</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">状态</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">时间</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="alert in filteredAlerts"
              :key="alert.id"
              :class="['hover:bg-gray-50', alert.level === 'critical' && 'bg-red-50']"
            >
              <td class="px-4 py-4">
                <input
                  type="checkbox"
                  class="rounded border-gray-300"
                  :checked="selectedAlerts.includes(alert.id)"
                  @change="toggleSelect(alert.id)"
                />
              </td>
              <td class="px-4 py-4">
                <span :class="[
                  'inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium',
                  levelStyles[alert.level]
                ]">
                  <span :class="['w-2 h-2 rounded-full mr-1.5', levelDotStyles[alert.level]]"></span>
                  {{ levelTexts[alert.level] }}
                </span>
              </td>
              <td class="px-4 py-4">
                <div class="max-w-xs">
                  <p class="font-medium text-gray-800 truncate">{{ alert.title }}</p>
                  <p class="text-sm text-gray-500 truncate mt-1">{{ alert.content }}</p>
                </div>
              </td>
              <td class="px-4 py-4">
                <div class="flex items-center">
                  <div class="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 text-sm font-bold mr-2">
                    {{ alert.userName?.charAt(0) || '?' }}
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-800">{{ alert.userName }}</p>
                    <p class="text-xs text-gray-500">{{ alert.userPhone }}</p>
                  </div>
                </div>
              </td>
              <td class="px-4 py-4">
                <span :class="[
                  'px-2 py-1 rounded text-xs',
                  typeStyles[alert.alertType]
                ]">
                  {{ typeTexts[alert.alertType] }}
                </span>
              </td>
              <td class="px-4 py-4">
                <span :class="[
                  'px-2 py-1 rounded text-xs',
                  statusStyles[alert.status]
                ]">
                  {{ statusTexts[alert.status] }}
                </span>
              </td>
              <td class="px-4 py-4 text-sm text-gray-600">
                <p>{{ formatTime(alert.createdAt) }}</p>
                <p v-if="alert.handledAt" class="text-xs text-gray-400 mt-1">
                  处理于 {{ formatTime(alert.handledAt) }}
                </p>
              </td>
              <td class="px-4 py-4">
                <div class="flex items-center space-x-1">
                  <button
                    @click="viewDetail(alert)"
                    class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                    title="查看详情"
                  >
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  <button
                    v-if="alert.status === 'pending'"
                    @click="handleAlert(alert, 'handling')"
                    class="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg"
                    title="开始处理"
                  >
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </button>
                  <button
                    v-if="['pending', 'handling'].includes(alert.status)"
                    @click="handleAlert(alert, 'resolved')"
                    class="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                    title="标记已解决"
                  >
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </button>
                  <button
                    v-if="alert.status === 'pending'"
                    @click="handleAlert(alert, 'ignored')"
                    class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                    title="忽略"
                  >
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredAlerts.length === 0">
              <td colspan="8" class="px-4 py-12 text-center text-gray-500">
                <svg class="w-12 h-12 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <p>暂无符合条件的告警</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="p-4 border-t border-gray-100 flex items-center justify-between">
        <span class="text-sm text-gray-500">
          共 {{ filteredAlerts.length }} 条记录，显示 {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, filteredAlerts.length) }} 条
        </span>
        <div class="flex items-center space-x-2">
          <button
            @click="currentPage--"
            :disabled="currentPage === 1"
            class="px-3 py-1 border border-gray-200 rounded text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            上一页
          </button>
          <template v-for="page in visiblePages" :key="page">
            <button
              v-if="page !== '...'"
              @click="currentPage = page"
              :class="[
                'px-3 py-1 rounded text-sm',
                currentPage === page
                  ? 'bg-primary-500 text-white'
                  : 'border border-gray-200 text-gray-600 hover:bg-gray-50'
              ]"
            >
              {{ page }}
            </button>
            <span v-else class="px-2 text-gray-400">...</span>
          </template>
          <button
            @click="currentPage++"
            :disabled="currentPage === totalPages"
            class="px-3 py-1 border border-gray-200 rounded text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- 告警详情模态框 -->
    <div
      v-if="showDetailModal"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="showDetailModal = false"
    >
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"></div>
        <div class="relative bg-white rounded-2xl shadow-xl max-w-2xl w-full mx-auto z-10">
          <!-- 模态框头部 -->
          <div class="flex items-center justify-between p-6 border-b border-gray-100">
            <div class="flex items-center">
              <span :class="[
                'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium mr-3',
                levelStyles[selectedAlert?.level]
              ]">
                {{ levelTexts[selectedAlert?.level] }}
              </span>
              <h3 class="text-lg font-bold text-gray-800">告警详情</h3>
            </div>
            <button @click="showDetailModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- 模态框内容 -->
          <div class="p-6">
            <div class="space-y-6">
              <!-- 告警标题 -->
              <div>
                <h4 class="text-xl font-bold text-gray-800">{{ selectedAlert?.title }}</h4>
                <p class="text-gray-600 mt-2">{{ selectedAlert?.content }}</p>
              </div>

              <!-- 告警信息 -->
              <div class="grid grid-cols-2 gap-4">
                <div class="bg-gray-50 rounded-xl p-4">
                  <p class="text-sm text-gray-500 mb-1">告警类型</p>
                  <span :class="['px-2 py-1 rounded text-sm', typeStyles[selectedAlert?.alertType]]">
                    {{ typeTexts[selectedAlert?.alertType] }}
                  </span>
                </div>
                <div class="bg-gray-50 rounded-xl p-4">
                  <p class="text-sm text-gray-500 mb-1">当前状态</p>
                  <span :class="['px-2 py-1 rounded text-sm', statusStyles[selectedAlert?.status]]">
                    {{ statusTexts[selectedAlert?.status] }}
                  </span>
                </div>
                <div class="bg-gray-50 rounded-xl p-4">
                  <p class="text-sm text-gray-500 mb-1">触发时间</p>
                  <p class="text-gray-800 font-medium">{{ formatDateTime(selectedAlert?.createdAt) }}</p>
                </div>
                <div class="bg-gray-50 rounded-xl p-4">
                  <p class="text-sm text-gray-500 mb-1">处理时间</p>
                  <p class="text-gray-800 font-medium">
                    {{ selectedAlert?.handledAt ? formatDateTime(selectedAlert.handledAt) : '未处理' }}
                  </p>
                </div>
              </div>

              <!-- 关联用户 -->
              <div class="bg-gray-50 rounded-xl p-4">
                <p class="text-sm text-gray-500 mb-3">关联用户</p>
                <div class="flex items-center">
                  <div class="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-bold mr-4">
                    {{ selectedAlert?.userName?.charAt(0) || '?' }}
                  </div>
                  <div>
                    <p class="font-medium text-gray-800">{{ selectedAlert?.userName }}</p>
                    <p class="text-sm text-gray-500">{{ selectedAlert?.userPhone }}</p>
                  </div>
                  <button class="ml-auto px-4 py-2 text-primary-600 border border-primary-200 rounded-lg hover:bg-primary-50">
                    查看用户
                  </button>
                </div>
              </div>

              <!-- 处理记录 -->
              <div v-if="selectedAlert?.handleHistory?.length > 0">
                <p class="text-sm text-gray-500 mb-3">处理记录</p>
                <div class="space-y-3">
                  <div
                    v-for="(record, index) in selectedAlert.handleHistory"
                    :key="index"
                    class="flex items-start"
                  >
                    <div class="w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3"></div>
                    <div>
                      <p class="text-gray-800">{{ record.action }}</p>
                      <p class="text-sm text-gray-500">{{ record.operator }} · {{ formatDateTime(record.time) }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 处理备注 -->
              <div>
                <label class="text-sm text-gray-500 mb-2 block">处理备注</label>
                <textarea
                  v-model="handleNote"
                  rows="3"
                  placeholder="请输入处理备注..."
                  class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                ></textarea>
              </div>
            </div>
          </div>

          <!-- 模态框底部 -->
          <div class="flex items-center justify-end gap-3 p-6 border-t border-gray-100">
            <button
              @click="showDetailModal = false"
              class="px-6 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50"
            >
              关闭
            </button>
            <button
              v-if="selectedAlert?.status === 'pending'"
              @click="handleSelectedAlert('handling')"
              class="px-6 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600"
            >
              开始处理
            </button>
            <button
              v-if="['pending', 'handling'].includes(selectedAlert?.status)"
              @click="handleSelectedAlert('resolved')"
              class="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
            >
              标记已解决
            </button>
            <button
              v-if="selectedAlert?.status === 'pending'"
              @click="handleSelectedAlert('ignored')"
              class="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
            >
              忽略
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

// 筛选条件
const filters = ref({
  keyword: '',
  type: 'all',
  level: 'all',
  status: 'all',
  startDate: '',
  endDate: ''
})

// 分页
const currentPage = ref(1)
const pageSize = ref(10)

// 选择
const selectedAlerts = ref([])

// 刷新状态
const refreshing = ref(false)

// 模态框
const showDetailModal = ref(false)
const selectedAlert = ref(null)
const handleNote = ref('')

// 样式映射
const levelStyles = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-blue-100 text-blue-700'
}

const levelDotStyles = {
  critical: 'bg-red-500 animate-pulse',
  high: 'bg-orange-500',
  medium: 'bg-yellow-500',
  low: 'bg-blue-500'
}

const levelTexts = {
  critical: '紧急',
  high: '高',
  medium: '中',
  low: '低'
}

const typeStyles = {
  health: 'bg-red-100 text-red-700',
  medication: 'bg-purple-100 text-purple-700',
  device: 'bg-blue-100 text-blue-700',
  sos: 'bg-red-100 text-red-700',
  fence: 'bg-green-100 text-green-700'
}

const typeTexts = {
  health: '健康异常',
  medication: '用药提醒',
  device: '设备告警',
  sos: 'SOS求助',
  fence: '电子围栏'
}

const statusStyles = {
  pending: 'bg-red-100 text-red-600',
  handling: 'bg-yellow-100 text-yellow-600',
  resolved: 'bg-green-100 text-green-600',
  ignored: 'bg-gray-100 text-gray-600'
}

const statusTexts = {
  pending: '待处理',
  handling: '处理中',
  resolved: '已解决',
  ignored: '已忽略'
}

// 模拟告警数据
const alerts = ref([
  {
    id: 1,
    title: 'SOS紧急求助',
    content: '用户触发了SOS紧急求助按钮，请立即响应！',
    alertType: 'sos',
    level: 'critical',
    status: 'pending',
    userName: '王建国',
    userPhone: '138****8001',
    userId: 1,
    createdAt: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
    handledAt: null,
    handleHistory: []
  },
  {
    id: 2,
    title: '血压异常偏高',
    content: '用户血压读数160/100mmHg，超出正常范围，建议关注。',
    alertType: 'health',
    level: 'high',
    status: 'handling',
    userName: '张芳',
    userPhone: '136****8002',
    userId: 2,
    createdAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    handledAt: new Date(Date.now() - 20 * 60 * 1000).toISOString(),
    handleHistory: [
      { action: '开始处理告警', operator: '管理员', time: new Date(Date.now() - 20 * 60 * 1000).toISOString() }
    ]
  },
  {
    id: 3,
    title: '心率过速告警',
    content: '检测到心率异常：115次/分钟，持续时间超过10分钟。',
    alertType: 'health',
    level: 'high',
    status: 'pending',
    userName: '李红',
    userPhone: '137****8003',
    userId: 3,
    createdAt: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
    handledAt: null,
    handleHistory: []
  },
  {
    id: 4,
    title: '设备离线超过2小时',
    content: '智能手表设备已离线超过2小时，请检查设备状态。',
    alertType: 'device',
    level: 'medium',
    status: 'resolved',
    userName: '刘强',
    userPhone: '139****8004',
    userId: 4,
    createdAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    handledAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    handleHistory: [
      { action: '开始处理告警', operator: '管理员', time: new Date(Date.now() - 2.5 * 60 * 60 * 1000).toISOString() },
      { action: '已联系用户，设备已重新上线', operator: '管理员', time: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() }
    ]
  },
  {
    id: 5,
    title: '漏服药物提醒',
    content: '用户今日降压药已超时未服用，请提醒。',
    alertType: 'medication',
    level: 'medium',
    status: 'pending',
    userName: '陈明',
    userPhone: '135****8005',
    userId: 5,
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    handledAt: null,
    handleHistory: []
  },
  {
    id: 6,
    title: '电子围栏越界',
    content: '用户已离开设定的安全区域（家庭周围3公里），当前位置：XX市XX区。',
    alertType: 'fence',
    level: 'high',
    status: 'resolved',
    userName: '赵大爷',
    userPhone: '133****8006',
    userId: 6,
    createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    handledAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    handleHistory: [
      { action: '已联系家属确认，用户外出看望亲友', operator: '管理员', time: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString() }
    ]
  },
  {
    id: 7,
    title: '设备电量不足',
    content: '血压仪设备电量仅剩10%，请及时充电。',
    alertType: 'device',
    level: 'low',
    status: 'ignored',
    userName: '孙阿姨',
    userPhone: '131****8007',
    userId: 7,
    createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    handledAt: new Date(Date.now() - 23 * 60 * 60 * 1000).toISOString(),
    handleHistory: [
      { action: '已忽略：用户已自行充电', operator: '管理员', time: new Date(Date.now() - 23 * 60 * 60 * 1000).toISOString() }
    ]
  },
  {
    id: 8,
    title: '血糖偏高提醒',
    content: '餐后血糖读数11.2mmol/L，略高于正常范围。',
    alertType: 'health',
    level: 'medium',
    status: 'pending',
    userName: '周奶奶',
    userPhone: '132****8008',
    userId: 8,
    createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    handledAt: null,
    handleHistory: []
  }
])

// 统计数据
const stats = computed(() => {
  const total = alerts.value.length
  const critical = alerts.value.filter(a => a.level === 'critical').length
  const pending = alerts.value.filter(a => a.status === 'pending').length
  const handling = alerts.value.filter(a => a.status === 'handling').length
  const resolved = alerts.value.filter(a => a.status === 'resolved').length

  return { total, critical, pending, handling, resolved }
})

// 筛选后的告警
const filteredAlerts = computed(() => {
  return alerts.value.filter(alert => {
    // 关键词筛选
    if (filters.value.keyword) {
      const keyword = filters.value.keyword.toLowerCase()
      if (!alert.title.toLowerCase().includes(keyword) &&
          !alert.userName.toLowerCase().includes(keyword)) {
        return false
      }
    }

    // 类型筛选
    if (filters.value.type !== 'all' && alert.alertType !== filters.value.type) {
      return false
    }

    // 级别筛选
    if (filters.value.level !== 'all' && alert.level !== filters.value.level) {
      return false
    }

    // 状态筛选
    if (filters.value.status !== 'all' && alert.status !== filters.value.status) {
      return false
    }

    // 日期筛选
    if (filters.value.startDate) {
      const startDate = new Date(filters.value.startDate)
      const alertDate = new Date(alert.createdAt)
      if (alertDate < startDate) return false
    }

    if (filters.value.endDate) {
      const endDate = new Date(filters.value.endDate)
      endDate.setHours(23, 59, 59, 999)
      const alertDate = new Date(alert.createdAt)
      if (alertDate > endDate) return false
    }

    return true
  })
})

// 分页相关
const totalPages = computed(() => Math.ceil(filteredAlerts.value.length / pageSize.value))

const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = currentPage.value

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    if (current <= 3) {
      pages.push(1, 2, 3, 4, '...', total)
    } else if (current >= total - 2) {
      pages.push(1, '...', total - 3, total - 2, total - 1, total)
    } else {
      pages.push(1, '...', current - 1, current, current + 1, '...', total)
    }
  }

  return pages
})

const isAllSelected = computed(() => {
  return filteredAlerts.value.length > 0 &&
         filteredAlerts.value.every(a => selectedAlerts.value.includes(a.id))
})

// 方法
function resetFilters() {
  filters.value = {
    keyword: '',
    type: 'all',
    level: 'all',
    status: 'all',
    startDate: '',
    endDate: ''
  }
  currentPage.value = 1
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedAlerts.value = []
  } else {
    selectedAlerts.value = filteredAlerts.value.map(a => a.id)
  }
}

function toggleSelect(id) {
  const index = selectedAlerts.value.indexOf(id)
  if (index > -1) {
    selectedAlerts.value.splice(index, 1)
  } else {
    selectedAlerts.value.push(id)
  }
}

function viewDetail(alert) {
  selectedAlert.value = alert
  handleNote.value = ''
  showDetailModal.value = true
}

function handleAlert(alert, newStatus) {
  const index = alerts.value.findIndex(a => a.id === alert.id)
  if (index > -1) {
    alerts.value[index].status = newStatus
    alerts.value[index].handledAt = new Date().toISOString()

    const actionText = {
      handling: '开始处理告警',
      resolved: '已解决告警',
      ignored: '已忽略告警'
    }

    alerts.value[index].handleHistory.push({
      action: actionText[newStatus],
      operator: '管理员',
      time: new Date().toISOString()
    })
  }
}

function handleSelectedAlert(newStatus) {
  if (selectedAlert.value) {
    handleAlert(selectedAlert.value, newStatus)

    if (handleNote.value) {
      const index = alerts.value.findIndex(a => a.id === selectedAlert.value.id)
      if (index > -1) {
        alerts.value[index].handleHistory.push({
          action: `备注：${handleNote.value}`,
          operator: '管理员',
          time: new Date().toISOString()
        })
      }
    }

    showDetailModal.value = false
  }
}

function batchHandle(newStatus) {
  selectedAlerts.value.forEach(id => {
    const alert = alerts.value.find(a => a.id === id)
    if (alert && (alert.status === 'pending' || (newStatus === 'resolved' && alert.status === 'handling'))) {
      handleAlert(alert, newStatus)
    }
  })
  selectedAlerts.value = []
}

async function refreshAlerts() {
  refreshing.value = true
  // 模拟API调用
  await new Promise(resolve => setTimeout(resolve, 1000))
  refreshing.value = false
}

function exportAlerts() {
  // 模拟导出功能
  const data = filteredAlerts.value.map(a => ({
    级别: levelTexts[a.level],
    标题: a.title,
    类型: typeTexts[a.alertType],
    状态: statusTexts[a.status],
    用户: a.userName,
    时间: formatDateTime(a.createdAt)
  }))

  console.log('导出数据:', data)
  alert('告警数据已导出到控制台')
}

function formatTime(dateString) {
  if (!dateString) return ''

  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`

  return date.toLocaleDateString('zh-CN')
}

function formatDateTime(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 自动刷新
let refreshTimer = null

onMounted(() => {
  // 每30秒自动刷新一次
  refreshTimer = setInterval(() => {
    refreshAlerts()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>
