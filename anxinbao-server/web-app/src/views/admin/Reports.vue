<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-800">数据报表</h1>
      <button
        @click="showGenerateModal = true"
        class="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        生成报表
      </button>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white rounded-xl shadow-sm p-5">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">本月报表</p>
            <p class="text-2xl font-bold text-gray-800 mt-1">{{ stats.monthlyCount }}</p>
          </div>
          <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
            <svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm p-5">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">健康报表</p>
            <p class="text-2xl font-bold text-green-600 mt-1">{{ stats.healthReports }}</p>
          </div>
          <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
            <svg class="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm p-5">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">设备报表</p>
            <p class="text-2xl font-bold text-purple-600 mt-1">{{ stats.deviceReports }}</p>
          </div>
          <div class="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
            <svg class="w-6 h-6 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm p-5">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">告警报表</p>
            <p class="text-2xl font-bold text-orange-600 mt-1">{{ stats.alertReports }}</p>
          </div>
          <div class="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
            <svg class="w-6 h-6 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 快速报表 -->
    <div class="bg-white rounded-xl shadow-sm p-6">
      <h2 class="text-lg font-semibold text-gray-800 mb-4">快速生成</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <button
          v-for="quick in quickReports"
          :key="quick.type"
          @click="generateQuickReport(quick)"
          class="flex flex-col items-center gap-3 p-4 border-2 border-dashed border-gray-200 rounded-xl hover:border-primary-300 hover:bg-primary-50 transition-all group"
        >
          <div :class="['w-12 h-12 rounded-full flex items-center justify-center', quick.bgColor]">
            <component :is="quick.icon" :class="['w-6 h-6', quick.iconColor]" />
          </div>
          <div class="text-center">
            <p class="font-medium text-gray-800 group-hover:text-primary-600">{{ quick.name }}</p>
            <p class="text-xs text-gray-500">{{ quick.desc }}</p>
          </div>
        </button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="bg-white rounded-xl shadow-sm p-4">
      <div class="flex flex-wrap items-center gap-4">
        <div class="flex-1 min-w-[200px]">
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索报表名称..."
            class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <select
          v-model="filterType"
          class="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
        >
          <option value="">全部类型</option>
          <option value="health">健康报表</option>
          <option value="device">设备报表</option>
          <option value="alert">告警报表</option>
          <option value="user">用户报表</option>
        </select>
        <select
          v-model="filterStatus"
          class="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
        >
          <option value="">全部状态</option>
          <option value="completed">已完成</option>
          <option value="processing">生成中</option>
          <option value="failed">失败</option>
        </select>
        <input
          v-model="filterDate"
          type="date"
          class="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
        />
      </div>
    </div>

    <!-- 报表列表 -->
    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-4 text-left text-sm font-semibold text-gray-600">报表名称</th>
              <th class="px-6 py-4 text-left text-sm font-semibold text-gray-600">类型</th>
              <th class="px-6 py-4 text-left text-sm font-semibold text-gray-600">数据范围</th>
              <th class="px-6 py-4 text-left text-sm font-semibold text-gray-600">格式</th>
              <th class="px-6 py-4 text-left text-sm font-semibold text-gray-600">状态</th>
              <th class="px-6 py-4 text-left text-sm font-semibold text-gray-600">创建时间</th>
              <th class="px-6 py-4 text-left text-sm font-semibold text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="report in filteredReports" :key="report.id" class="hover:bg-gray-50">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div :class="['w-10 h-10 rounded-lg flex items-center justify-center', getTypeColor(report.type).bg]">
                    <svg :class="['w-5 h-5', getTypeColor(report.type).icon]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <p class="font-medium text-gray-800">{{ report.name }}</p>
                    <p class="text-sm text-gray-500">{{ report.description }}</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <span :class="['px-3 py-1 rounded-full text-sm font-medium', getTypeColor(report.type).badge]">
                  {{ getTypeName(report.type) }}
                </span>
              </td>
              <td class="px-6 py-4 text-gray-600">
                {{ report.dateRange }}
              </td>
              <td class="px-6 py-4">
                <span class="flex items-center gap-2 text-gray-600">
                  <component :is="getFormatIcon(report.format)" class="w-5 h-5" />
                  {{ report.format.toUpperCase() }}
                </span>
              </td>
              <td class="px-6 py-4">
                <span :class="['px-3 py-1 rounded-full text-sm font-medium', getStatusColor(report.status)]">
                  {{ getStatusName(report.status) }}
                </span>
              </td>
              <td class="px-6 py-4 text-gray-600">
                {{ formatDateTime(report.createdAt) }}
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <button
                    v-if="report.status === 'completed'"
                    @click="downloadReport(report)"
                    class="p-2 text-blue-500 hover:bg-blue-50 rounded-lg transition-colors"
                    title="下载"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </button>
                  <button
                    @click="previewReport(report)"
                    class="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
                    title="预览"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  <button
                    v-if="report.status === 'failed'"
                    @click="retryReport(report)"
                    class="p-2 text-orange-500 hover:bg-orange-50 rounded-lg transition-colors"
                    title="重试"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </button>
                  <button
                    @click="deleteReport(report)"
                    class="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    title="删除"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredReports.length === 0">
              <td colspan="7" class="px-6 py-12 text-center text-gray-500">
                <svg class="w-12 h-12 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                暂无报表数据
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 生成报表弹窗 -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showGenerateModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="fixed inset-0 bg-black/50" @click="showGenerateModal = false"></div>
          <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div class="p-6 border-b border-gray-100">
              <h3 class="text-xl font-semibold text-gray-800">生成报表</h3>
              <button
                @click="showGenerateModal = false"
                class="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div class="p-6 space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">报表名称</label>
                <input
                  v-model="newReport.name"
                  type="text"
                  placeholder="请输入报表名称"
                  class="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">报表类型</label>
                <select
                  v-model="newReport.type"
                  class="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  <option value="health">健康数据报表</option>
                  <option value="device">设备状态报表</option>
                  <option value="alert">告警统计报表</option>
                  <option value="user">用户活跃报表</option>
                </select>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">开始日期</label>
                  <input
                    v-model="newReport.startDate"
                    type="date"
                    class="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">结束日期</label>
                  <input
                    v-model="newReport.endDate"
                    type="date"
                    class="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">导出格式</label>
                <div class="flex gap-4">
                  <label
                    v-for="format in formats"
                    :key="format.value"
                    :class="[
                      'flex-1 flex items-center justify-center gap-2 p-3 border-2 rounded-lg cursor-pointer transition-all',
                      newReport.format === format.value
                        ? 'border-primary-500 bg-primary-50 text-primary-600'
                        : 'border-gray-200 hover:border-gray-300'
                    ]"
                  >
                    <input
                      v-model="newReport.format"
                      type="radio"
                      :value="format.value"
                      class="hidden"
                    />
                    <component :is="format.icon" class="w-5 h-5" />
                    <span class="font-medium">{{ format.label }}</span>
                  </label>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">数据筛选（可选）</label>
                <div class="space-y-2">
                  <label class="flex items-center gap-2">
                    <input v-model="newReport.includeCharts" type="checkbox" class="rounded text-primary-500" />
                    <span class="text-gray-600">包含图表</span>
                  </label>
                  <label class="flex items-center gap-2">
                    <input v-model="newReport.includeDetails" type="checkbox" class="rounded text-primary-500" />
                    <span class="text-gray-600">包含明细数据</span>
                  </label>
                  <label class="flex items-center gap-2">
                    <input v-model="newReport.includeSummary" type="checkbox" class="rounded text-primary-500" />
                    <span class="text-gray-600">包含统计摘要</span>
                  </label>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">备注说明</label>
                <textarea
                  v-model="newReport.description"
                  rows="3"
                  placeholder="可选填写报表说明..."
                  class="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 resize-none"
                ></textarea>
              </div>
            </div>
            <div class="p-6 border-t border-gray-100 flex justify-end gap-3">
              <button
                @click="showGenerateModal = false"
                class="px-6 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                @click="submitGenerateReport"
                :disabled="generating"
                class="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                <svg v-if="generating" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
                {{ generating ? '生成中...' : '开始生成' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 预览弹窗 -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showPreviewModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="fixed inset-0 bg-black/50" @click="showPreviewModal = false"></div>
          <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
            <div class="p-6 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h3 class="text-xl font-semibold text-gray-800">{{ previewReport?.name }}</h3>
                <p class="text-sm text-gray-500 mt-1">{{ previewReport?.dateRange }}</p>
              </div>
              <div class="flex items-center gap-2">
                <button
                  v-if="previewReport?.status === 'completed'"
                  @click="downloadReport(previewReport)"
                  class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors flex items-center gap-2"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  下载报表
                </button>
                <button
                  @click="showPreviewModal = false"
                  class="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div class="flex-1 overflow-y-auto p-6">
              <!-- 预览内容 -->
              <div v-if="previewReport?.status === 'processing'" class="text-center py-12">
                <svg class="w-16 h-16 mx-auto text-primary-500 animate-spin mb-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
                <p class="text-gray-500">报表正在生成中，请稍候...</p>
              </div>
              <div v-else-if="previewReport?.status === 'failed'" class="text-center py-12">
                <svg class="w-16 h-16 mx-auto text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p class="text-red-500 font-medium">报表生成失败</p>
                <p class="text-gray-500 mt-2">{{ previewReport?.error || '请重试或联系管理员' }}</p>
              </div>
              <div v-else class="space-y-6">
                <!-- 报表摘要 -->
                <div class="grid grid-cols-3 gap-4">
                  <div class="bg-gray-50 rounded-lg p-4 text-center">
                    <p class="text-2xl font-bold text-gray-800">{{ previewReport?.summary?.totalRecords || 0 }}</p>
                    <p class="text-sm text-gray-500">总记录数</p>
                  </div>
                  <div class="bg-gray-50 rounded-lg p-4 text-center">
                    <p class="text-2xl font-bold text-green-600">{{ previewReport?.summary?.normalCount || 0 }}</p>
                    <p class="text-sm text-gray-500">正常</p>
                  </div>
                  <div class="bg-gray-50 rounded-lg p-4 text-center">
                    <p class="text-2xl font-bold text-red-600">{{ previewReport?.summary?.abnormalCount || 0 }}</p>
                    <p class="text-sm text-gray-500">异常</p>
                  </div>
                </div>
                <!-- 图表预览区 -->
                <div class="border border-gray-200 rounded-lg p-4">
                  <h4 class="font-medium text-gray-800 mb-4">数据趋势</h4>
                  <div class="h-64 bg-gray-50 rounded flex items-center justify-center text-gray-400">
                    图表预览区域
                  </div>
                </div>
                <!-- 数据表格预览 -->
                <div class="border border-gray-200 rounded-lg overflow-hidden">
                  <h4 class="font-medium text-gray-800 p-4 border-b border-gray-200">数据明细（前10条）</h4>
                  <table class="w-full">
                    <thead class="bg-gray-50">
                      <tr>
                        <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">时间</th>
                        <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">用户</th>
                        <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">数据</th>
                        <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">状态</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
                      <tr v-for="(row, idx) in previewReport?.previewData || []" :key="idx">
                        <td class="px-4 py-3 text-gray-600">{{ row.time }}</td>
                        <td class="px-4 py-3 text-gray-800">{{ row.user }}</td>
                        <td class="px-4 py-3 text-gray-600">{{ row.data }}</td>
                        <td class="px-4 py-3">
                          <span :class="row.status === 'normal' ? 'text-green-600' : 'text-red-600'">
                            {{ row.status === 'normal' ? '正常' : '异常' }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'

// 图标组件
const IconPdf = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zm-2.5 9.5a1.5 1.5 0 110 3 1.5 1.5 0 010-3z' })
    ])
  }
}

const IconExcel = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM8 13h2v2H8v-2zm0 4h2v2H8v-2zm4-4h4v2h-4v-2zm0 4h4v2h-4v-2z' })
    ])
  }
}

const IconCsv = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM7 14h2v1H7v-1zm0 2h2v1H7v-1zm4-2h2v1h-2v-1zm0 2h2v1h-2v-1zm4-2h2v1h-2v-1zm0 2h2v1h-2v-1z' })
    ])
  }
}

const IconHealth = {
  render() {
    return h('svg', { class: 'w-6 h-6', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z' })
    ])
  }
}

const IconDevice = {
  render() {
    return h('svg', { class: 'w-6 h-6', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z' })
    ])
  }
}

const IconAlert = {
  render() {
    return h('svg', { class: 'w-6 h-6', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' })
    ])
  }
}

const IconUser = {
  render() {
    return h('svg', { class: 'w-6 h-6', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z' })
    ])
  }
}

// 状态
const searchKeyword = ref('')
const filterType = ref('')
const filterStatus = ref('')
const filterDate = ref('')
const showGenerateModal = ref(false)
const showPreviewModal = ref(false)
const generating = ref(false)
const previewReport = ref(null)

// 统计数据
const stats = ref({
  monthlyCount: 24,
  healthReports: 12,
  deviceReports: 6,
  alertReports: 6
})

// 导出格式
const formats = [
  { value: 'pdf', label: 'PDF', icon: IconPdf },
  { value: 'xlsx', label: 'Excel', icon: IconExcel },
  { value: 'csv', label: 'CSV', icon: IconCsv }
]

// 快速报表
const quickReports = [
  { type: 'health_weekly', name: '周健康报表', desc: '最近7天', icon: IconHealth, bgColor: 'bg-green-100', iconColor: 'text-green-500' },
  { type: 'device_status', name: '设备状态', desc: '当前状态', icon: IconDevice, bgColor: 'bg-purple-100', iconColor: 'text-purple-500' },
  { type: 'alert_monthly', name: '月告警统计', desc: '最近30天', icon: IconAlert, bgColor: 'bg-orange-100', iconColor: 'text-orange-500' },
  { type: 'user_active', name: '用户活跃', desc: '最近7天', icon: IconUser, bgColor: 'bg-blue-100', iconColor: 'text-blue-500' }
]

// 新报表表单
const newReport = ref({
  name: '',
  type: 'health',
  startDate: '',
  endDate: '',
  format: 'pdf',
  includeCharts: true,
  includeDetails: true,
  includeSummary: true,
  description: ''
})

// 报表列表
const reports = ref([
  {
    id: 1,
    name: '2024年1月健康数据报表',
    description: '包含所有用户的血压、心率等健康数据',
    type: 'health',
    dateRange: '2024-01-01 至 2024-01-31',
    format: 'pdf',
    status: 'completed',
    createdAt: '2024-01-31 18:00:00',
    fileUrl: '/reports/health_202401.pdf',
    summary: { totalRecords: 1250, normalCount: 1100, abnormalCount: 150 },
    previewData: [
      { time: '2024-01-31 08:00', user: '张大爷', data: '血压 120/80 mmHg', status: 'normal' },
      { time: '2024-01-31 08:15', user: '李奶奶', data: '心率 75 次/分', status: 'normal' },
      { time: '2024-01-31 09:00', user: '王大爷', data: '血压 150/95 mmHg', status: 'abnormal' }
    ]
  },
  {
    id: 2,
    name: '设备在线状态报表',
    description: '全部设备的在线率和电量统计',
    type: 'device',
    dateRange: '2024-01-15 至 2024-01-31',
    format: 'xlsx',
    status: 'completed',
    createdAt: '2024-01-31 12:00:00',
    fileUrl: '/reports/device_status.xlsx',
    summary: { totalRecords: 85, normalCount: 72, abnormalCount: 13 },
    previewData: [
      { time: '2024-01-31', user: '张大爷', data: '智能手表 在线', status: 'normal' },
      { time: '2024-01-31', user: '李奶奶', data: '血压仪 离线', status: 'abnormal' }
    ]
  },
  {
    id: 3,
    name: '告警处理统计报表',
    description: '本月告警的响应和处理情况',
    type: 'alert',
    dateRange: '2024-01-01 至 2024-01-31',
    format: 'pdf',
    status: 'processing',
    createdAt: '2024-01-31 10:00:00'
  },
  {
    id: 4,
    name: '用户活跃度报表',
    description: '用户登录和功能使用统计',
    type: 'user',
    dateRange: '2024-01-01 至 2024-01-15',
    format: 'csv',
    status: 'failed',
    createdAt: '2024-01-15 16:00:00',
    error: '数据源连接超时'
  }
])

// 计算属性：筛选后的报表
const filteredReports = computed(() => {
  return reports.value.filter(report => {
    if (searchKeyword.value && !report.name.includes(searchKeyword.value)) return false
    if (filterType.value && report.type !== filterType.value) return false
    if (filterStatus.value && report.status !== filterStatus.value) return false
    return true
  })
})

// 获取类型颜色
function getTypeColor(type) {
  const colors = {
    health: { bg: 'bg-green-100', icon: 'text-green-500', badge: 'bg-green-100 text-green-700' },
    device: { bg: 'bg-purple-100', icon: 'text-purple-500', badge: 'bg-purple-100 text-purple-700' },
    alert: { bg: 'bg-orange-100', icon: 'text-orange-500', badge: 'bg-orange-100 text-orange-700' },
    user: { bg: 'bg-blue-100', icon: 'text-blue-500', badge: 'bg-blue-100 text-blue-700' }
  }
  return colors[type] || colors.health
}

// 获取类型名称
function getTypeName(type) {
  const names = {
    health: '健康报表',
    device: '设备报表',
    alert: '告警报表',
    user: '用户报表'
  }
  return names[type] || type
}

// 获取状态颜色
function getStatusColor(status) {
  const colors = {
    completed: 'bg-green-100 text-green-700',
    processing: 'bg-blue-100 text-blue-700',
    failed: 'bg-red-100 text-red-700'
  }
  return colors[status] || 'bg-gray-100 text-gray-700'
}

// 获取状态名称
function getStatusName(status) {
  const names = {
    completed: '已完成',
    processing: '生成中',
    failed: '失败'
  }
  return names[status] || status
}

// 获取格式图标
function getFormatIcon(format) {
  const icons = {
    pdf: IconPdf,
    xlsx: IconExcel,
    csv: IconCsv
  }
  return icons[format] || IconPdf
}

// 格式化日期时间
function formatDateTime(datetime) {
  if (!datetime) return '-'
  return datetime.replace('T', ' ').substring(0, 16)
}

// 生成快速报表
function generateQuickReport(quick) {
  const today = new Date()
  const dates = {
    health_weekly: { start: new Date(today - 7 * 24 * 60 * 60 * 1000), end: today },
    device_status: { start: today, end: today },
    alert_monthly: { start: new Date(today - 30 * 24 * 60 * 60 * 1000), end: today },
    user_active: { start: new Date(today - 7 * 24 * 60 * 60 * 1000), end: today }
  }

  const typeMap = {
    health_weekly: 'health',
    device_status: 'device',
    alert_monthly: 'alert',
    user_active: 'user'
  }

  const range = dates[quick.type]
  newReport.value = {
    name: `${quick.name}_${today.toISOString().split('T')[0]}`,
    type: typeMap[quick.type],
    startDate: range.start.toISOString().split('T')[0],
    endDate: range.end.toISOString().split('T')[0],
    format: 'pdf',
    includeCharts: true,
    includeDetails: true,
    includeSummary: true,
    description: `自动生成的${quick.name}`
  }
  showGenerateModal.value = true
}

// 提交生成报表
async function submitGenerateReport() {
  if (!newReport.value.name || !newReport.value.startDate || !newReport.value.endDate) {
    alert('请填写完整信息')
    return
  }

  generating.value = true

  // 模拟API调用
  await new Promise(resolve => setTimeout(resolve, 1500))

  const report = {
    id: Date.now(),
    name: newReport.value.name,
    description: newReport.value.description || `${getTypeName(newReport.value.type)}`,
    type: newReport.value.type,
    dateRange: `${newReport.value.startDate} 至 ${newReport.value.endDate}`,
    format: newReport.value.format,
    status: 'processing',
    createdAt: new Date().toISOString()
  }

  reports.value.unshift(report)

  // 模拟报表生成完成
  setTimeout(() => {
    const idx = reports.value.findIndex(r => r.id === report.id)
    if (idx !== -1) {
      reports.value[idx].status = 'completed'
      reports.value[idx].summary = { totalRecords: 100, normalCount: 85, abnormalCount: 15 }
      reports.value[idx].previewData = [
        { time: newReport.value.startDate, user: '示例用户', data: '示例数据', status: 'normal' }
      ]
    }
  }, 3000)

  generating.value = false
  showGenerateModal.value = false

  // 重置表单
  newReport.value = {
    name: '',
    type: 'health',
    startDate: '',
    endDate: '',
    format: 'pdf',
    includeCharts: true,
    includeDetails: true,
    includeSummary: true,
    description: ''
  }
}

// 预览报表
function previewReport(report) {
  previewReport.value = report
  showPreviewModal.value = true
}

// 下载报表
function downloadReport(report) {
  if (report.fileUrl) {
    // 模拟下载
    const link = document.createElement('a')
    link.href = report.fileUrl
    link.download = `${report.name}.${report.format}`
    link.click()
  } else {
    alert('报表文件准备中，请稍后重试')
  }
}

// 重试报表
async function retryReport(report) {
  report.status = 'processing'

  // 模拟重新生成
  await new Promise(resolve => setTimeout(resolve, 2000))

  report.status = 'completed'
  report.error = null
  report.summary = { totalRecords: 50, normalCount: 45, abnormalCount: 5 }
}

// 删除报表
function deleteReport(report) {
  if (confirm(`确定要删除报表"${report.name}"吗？`)) {
    const idx = reports.value.findIndex(r => r.id === report.id)
    if (idx !== -1) {
      reports.value.splice(idx, 1)
    }
  }
}

// 初始化默认日期
onMounted(() => {
  const today = new Date()
  const lastMonth = new Date(today)
  lastMonth.setMonth(lastMonth.getMonth() - 1)

  newReport.value.startDate = lastMonth.toISOString().split('T')[0]
  newReport.value.endDate = today.toISOString().split('T')[0]
})
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .relative,
.modal-leave-active .relative {
  transition: transform 0.3s ease;
}

.modal-enter-from .relative,
.modal-leave-to .relative {
  transform: scale(0.95);
}
</style>
