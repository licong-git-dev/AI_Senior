<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-800">系统设置</h1>
      <button
        @click="saveAllSettings"
        :disabled="saving"
        class="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50"
      >
        <svg v-if="saving" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
        <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        {{ saving ? '保存中...' : '保存设置' }}
      </button>
    </div>

    <!-- 设置标签页 -->
    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <div class="border-b border-gray-100">
        <nav class="flex -mb-px">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            :class="[
              'flex items-center gap-2 px-6 py-4 border-b-2 font-medium transition-colors',
              activeTab === tab.key
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            <component :is="tab.icon" class="w-5 h-5" />
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- 基本设置 -->
      <div v-show="activeTab === 'basic'" class="p-6 space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">系统名称</label>
            <input
              v-model="settings.basic.systemName"
              type="text"
              class="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">系统版本</label>
            <input
              :value="settings.basic.version"
              type="text"
              disabled
              class="w-full px-4 py-3 border border-gray-200 rounded-lg bg-gray-50 text-gray-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">联系邮箱</label>
            <input
              v-model="settings.basic.contactEmail"
              type="email"
              class="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">客服电话</label>
            <input
              v-model="settings.basic.supportPhone"
              type="text"
              class="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">系统公告</label>
          <textarea
            v-model="settings.basic.announcement"
            rows="3"
            placeholder="输入系统公告内容，用户登录后会看到..."
            class="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 resize-none"
          ></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">维护模式</label>
          <div class="flex items-center gap-4">
            <label class="relative inline-flex items-center cursor-pointer">
              <input v-model="settings.basic.maintenanceMode" type="checkbox" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
            <span class="text-gray-600">{{ settings.basic.maintenanceMode ? '已开启' : '已关闭' }}</span>
          </div>
          <p class="text-sm text-gray-500 mt-2">开启后，普通用户将无法访问系统</p>
        </div>
      </div>

      <!-- 通知设置 -->
      <div v-show="activeTab === 'notification'" class="p-6 space-y-6">
        <div class="bg-blue-50 rounded-lg p-4 flex items-start gap-3">
          <svg class="w-5 h-5 text-blue-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p class="font-medium text-blue-700">通知渠道配置</p>
            <p class="text-sm text-blue-600">配置系统发送通知的渠道和规则，确保紧急告警能及时送达</p>
          </div>
        </div>

        <!-- 短信通知 -->
        <div class="border border-gray-200 rounded-lg p-5">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <div>
                <h3 class="font-semibold text-gray-800">短信通知</h3>
                <p class="text-sm text-gray-500">通过短信发送告警通知</p>
              </div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input v-model="settings.notification.sms.enabled" type="checkbox" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>
          <div v-show="settings.notification.sms.enabled" class="space-y-4 pl-13">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm text-gray-600 mb-1">API Key</label>
                <input
                  v-model="settings.notification.sms.apiKey"
                  type="password"
                  placeholder="输入短信服务API Key"
                  class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label class="block text-sm text-gray-600 mb-1">签名</label>
                <input
                  v-model="settings.notification.sms.signature"
                  type="text"
                  placeholder="短信签名"
                  class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                />
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-600 mb-2">触发条件</label>
              <div class="flex flex-wrap gap-2">
                <label v-for="trigger in smsTriggers" :key="trigger.value" class="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded-lg">
                  <input
                    v-model="settings.notification.sms.triggers"
                    type="checkbox"
                    :value="trigger.value"
                    class="rounded text-primary-500"
                  />
                  <span class="text-sm text-gray-700">{{ trigger.label }}</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- 推送通知 -->
        <div class="border border-gray-200 rounded-lg p-5">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <div>
                <h3 class="font-semibold text-gray-800">APP推送</h3>
                <p class="text-sm text-gray-500">通过APP推送告警通知</p>
              </div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input v-model="settings.notification.push.enabled" type="checkbox" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>
          <div v-show="settings.notification.push.enabled" class="space-y-4 pl-13">
            <div>
              <label class="block text-sm text-gray-600 mb-2">推送内容模板</label>
              <textarea
                v-model="settings.notification.push.template"
                rows="2"
                placeholder="使用 {name} {type} {time} 等变量"
                class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none"
              ></textarea>
            </div>
            <div class="flex items-center gap-4">
              <label class="flex items-center gap-2">
                <input v-model="settings.notification.push.sound" type="checkbox" class="rounded text-primary-500" />
                <span class="text-sm text-gray-700">启用提示音</span>
              </label>
              <label class="flex items-center gap-2">
                <input v-model="settings.notification.push.vibrate" type="checkbox" class="rounded text-primary-500" />
                <span class="text-sm text-gray-700">启用振动</span>
              </label>
            </div>
          </div>
        </div>

        <!-- 邮件通知 -->
        <div class="border border-gray-200 rounded-lg p-5">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h3 class="font-semibold text-gray-800">邮件通知</h3>
                <p class="text-sm text-gray-500">通过邮件发送告警报告</p>
              </div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input v-model="settings.notification.email.enabled" type="checkbox" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>
          <div v-show="settings.notification.email.enabled" class="space-y-4 pl-13">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm text-gray-600 mb-1">SMTP服务器</label>
                <input
                  v-model="settings.notification.email.smtpHost"
                  type="text"
                  placeholder="smtp.example.com"
                  class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label class="block text-sm text-gray-600 mb-1">端口</label>
                <input
                  v-model="settings.notification.email.smtpPort"
                  type="number"
                  placeholder="587"
                  class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label class="block text-sm text-gray-600 mb-1">发件邮箱</label>
                <input
                  v-model="settings.notification.email.fromEmail"
                  type="email"
                  placeholder="noreply@anxinbao.com"
                  class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label class="block text-sm text-gray-600 mb-1">邮箱密码</label>
                <input
                  v-model="settings.notification.email.password"
                  type="password"
                  placeholder="邮箱密码或授权码"
                  class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 告警阈值 -->
      <div v-show="activeTab === 'threshold'" class="p-6 space-y-6">
        <div class="bg-orange-50 rounded-lg p-4 flex items-start gap-3">
          <svg class="w-5 h-5 text-orange-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div>
            <p class="font-medium text-orange-700">健康数据告警阈值</p>
            <p class="text-sm text-orange-600">当健康数据超出设定范围时，系统将自动触发告警</p>
          </div>
        </div>

        <!-- 血压阈值 -->
        <div class="border border-gray-200 rounded-lg p-5">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-800">血压阈值</h3>
              <p class="text-sm text-gray-500">设置血压告警的上下限值</p>
            </div>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label class="block text-sm text-gray-600 mb-1">收缩压下限</label>
              <div class="relative">
                <input
                  v-model.number="settings.threshold.bloodPressure.systolicMin"
                  type="number"
                  class="w-full px-3 py-2 pr-12 border border-gray-200 rounded-lg text-sm"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">mmHg</span>
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-600 mb-1">收缩压上限</label>
              <div class="relative">
                <input
                  v-model.number="settings.threshold.bloodPressure.systolicMax"
                  type="number"
                  class="w-full px-3 py-2 pr-12 border border-gray-200 rounded-lg text-sm"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">mmHg</span>
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-600 mb-1">舒张压下限</label>
              <div class="relative">
                <input
                  v-model.number="settings.threshold.bloodPressure.diastolicMin"
                  type="number"
                  class="w-full px-3 py-2 pr-12 border border-gray-200 rounded-lg text-sm"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">mmHg</span>
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-600 mb-1">舒张压上限</label>
              <div class="relative">
                <input
                  v-model.number="settings.threshold.bloodPressure.diastolicMax"
                  type="number"
                  class="w-full px-3 py-2 pr-12 border border-gray-200 rounded-lg text-sm"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">mmHg</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 心率阈值 -->
        <div class="border border-gray-200 rounded-lg p-5">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 bg-pink-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-pink-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-800">心率阈值</h3>
              <p class="text-sm text-gray-500">设置心率告警的上下限值</p>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm text-gray-600 mb-1">心率下限</label>
              <div class="relative">
                <input
                  v-model.number="settings.threshold.heartRate.min"
                  type="number"
                  class="w-full px-3 py-2 pr-16 border border-gray-200 rounded-lg text-sm"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">次/分</span>
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-600 mb-1">心率上限</label>
              <div class="relative">
                <input
                  v-model.number="settings.threshold.heartRate.max"
                  type="number"
                  class="w-full px-3 py-2 pr-16 border border-gray-200 rounded-lg text-sm"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">次/分</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 血糖阈值 -->
        <div class="border border-gray-200 rounded-lg p-5">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-800">血糖阈值</h3>
              <p class="text-sm text-gray-500">设置血糖告警的上下限值</p>
            </div>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label class="block text-sm text-gray-600 mb-1">空腹血糖下限</label>
              <div class="relative">
                <input
                  v-model.number="settings.threshold.bloodSugar.fastingMin"
                  type="number"
                  step="0.1"
                  class="w-full px-3 py-2 pr-16 border border-gray-200 rounded-lg text-sm"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">mmol/L</span>
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-600 mb-1">空腹血糖上限</label>
              <div class="relative">
                <input
                  v-model.number="settings.threshold.bloodSugar.fastingMax"
                  type="number"
                  step="0.1"
                  class="w-full px-3 py-2 pr-16 border border-gray-200 rounded-lg text-sm"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">mmol/L</span>
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-600 mb-1">餐后血糖下限</label>
              <div class="relative">
                <input
                  v-model.number="settings.threshold.bloodSugar.postprandialMin"
                  type="number"
                  step="0.1"
                  class="w-full px-3 py-2 pr-16 border border-gray-200 rounded-lg text-sm"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">mmol/L</span>
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-600 mb-1">餐后血糖上限</label>
              <div class="relative">
                <input
                  v-model.number="settings.threshold.bloodSugar.postprandialMax"
                  type="number"
                  step="0.1"
                  class="w-full px-3 py-2 pr-16 border border-gray-200 rounded-lg text-sm"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">mmol/L</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 体温阈值 -->
        <div class="border border-gray-200 rounded-lg p-5">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 bg-cyan-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-800">体温阈值</h3>
              <p class="text-sm text-gray-500">设置体温告警的上下限值</p>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm text-gray-600 mb-1">体温下限</label>
              <div class="relative">
                <input
                  v-model.number="settings.threshold.temperature.min"
                  type="number"
                  step="0.1"
                  class="w-full px-3 py-2 pr-8 border border-gray-200 rounded-lg text-sm"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">°C</span>
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-600 mb-1">体温上限</label>
              <div class="relative">
                <input
                  v-model.number="settings.threshold.temperature.max"
                  type="number"
                  step="0.1"
                  class="w-full px-3 py-2 pr-8 border border-gray-200 rounded-lg text-sm"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">°C</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 安全设置 -->
      <div v-show="activeTab === 'security'" class="p-6 space-y-6">
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <p class="font-medium text-gray-800">强制密码复杂度</p>
              <p class="text-sm text-gray-500">要求密码包含字母、数字和特殊字符，长度至少8位</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input v-model="settings.security.passwordComplexity" type="checkbox" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <p class="font-medium text-gray-800">登录验证码</p>
              <p class="text-sm text-gray-500">登录时需要输入图形验证码</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input v-model="settings.security.loginCaptcha" type="checkbox" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <p class="font-medium text-gray-800">登录失败锁定</p>
              <p class="text-sm text-gray-500">连续登录失败5次后，账号将被锁定30分钟</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input v-model="settings.security.loginLock" type="checkbox" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div class="p-4 border border-gray-200 rounded-lg">
            <div class="flex items-center justify-between mb-4">
              <div>
                <p class="font-medium text-gray-800">会话超时时间</p>
                <p class="text-sm text-gray-500">用户无操作后自动登出的时间</p>
              </div>
            </div>
            <select
              v-model="settings.security.sessionTimeout"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg"
            >
              <option :value="15">15分钟</option>
              <option :value="30">30分钟</option>
              <option :value="60">1小时</option>
              <option :value="120">2小时</option>
              <option :value="480">8小时</option>
              <option :value="1440">24小时</option>
            </select>
          </div>

          <div class="p-4 border border-gray-200 rounded-lg">
            <div class="flex items-center justify-between mb-4">
              <div>
                <p class="font-medium text-gray-800">密码有效期</p>
                <p class="text-sm text-gray-500">密码到期后需要强制修改</p>
              </div>
            </div>
            <select
              v-model="settings.security.passwordExpiry"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg"
            >
              <option :value="0">永不过期</option>
              <option :value="30">30天</option>
              <option :value="60">60天</option>
              <option :value="90">90天</option>
              <option :value="180">180天</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 数据设置 -->
      <div v-show="activeTab === 'data'" class="p-6 space-y-6">
        <div class="space-y-4">
          <div class="p-4 border border-gray-200 rounded-lg">
            <div class="flex items-center justify-between mb-4">
              <div>
                <p class="font-medium text-gray-800">数据保留期限</p>
                <p class="text-sm text-gray-500">超过期限的历史数据将被自动清理</p>
              </div>
            </div>
            <select
              v-model="settings.data.retentionDays"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg"
            >
              <option :value="90">90天</option>
              <option :value="180">180天</option>
              <option :value="365">1年</option>
              <option :value="730">2年</option>
              <option :value="1095">3年</option>
              <option :value="0">永久保留</option>
            </select>
          </div>

          <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <p class="font-medium text-gray-800">自动备份</p>
              <p class="text-sm text-gray-500">每日自动备份数据库</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input v-model="settings.data.autoBackup" type="checkbox" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div v-show="settings.data.autoBackup" class="p-4 border border-gray-200 rounded-lg">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm text-gray-600 mb-2">备份时间</label>
                <input
                  v-model="settings.data.backupTime"
                  type="time"
                  class="w-full px-4 py-2 border border-gray-200 rounded-lg"
                />
              </div>
              <div>
                <label class="block text-sm text-gray-600 mb-2">保留备份数</label>
                <input
                  v-model.number="settings.data.backupRetentionCount"
                  type="number"
                  min="1"
                  max="30"
                  class="w-full px-4 py-2 border border-gray-200 rounded-lg"
                />
              </div>
            </div>
          </div>

          <div class="p-4 border border-gray-200 rounded-lg">
            <div class="flex items-center justify-between mb-4">
              <div>
                <p class="font-medium text-gray-800">手动备份</p>
                <p class="text-sm text-gray-500">立即创建一个数据库备份</p>
              </div>
              <button
                @click="createBackup"
                :disabled="backingUp"
                class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                <svg v-if="backingUp" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
                {{ backingUp ? '备份中...' : '立即备份' }}
              </button>
            </div>
            <div v-if="lastBackup" class="text-sm text-gray-500">
              上次备份: {{ lastBackup }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, h } from 'vue'

// 图标组件
const IconBasic = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' }),
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z' })
    ])
  }
}

const IconNotification = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9' })
    ])
  }
}

const IconThreshold = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' })
    ])
  }
}

const IconSecurity = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' })
    ])
  }
}

const IconData = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4' })
    ])
  }
}

// 状态
const activeTab = ref('basic')
const saving = ref(false)
const backingUp = ref(false)
const lastBackup = ref('2024-01-31 03:00:00')

// 标签页
const tabs = [
  { key: 'basic', label: '基本设置', icon: IconBasic },
  { key: 'notification', label: '通知设置', icon: IconNotification },
  { key: 'threshold', label: '告警阈值', icon: IconThreshold },
  { key: 'security', label: '安全设置', icon: IconSecurity },
  { key: 'data', label: '数据管理', icon: IconData }
]

// 短信触发条件
const smsTriggers = [
  { value: 'sos', label: 'SOS紧急求助' },
  { value: 'health_critical', label: '健康数据严重异常' },
  { value: 'device_offline', label: '设备长时间离线' },
  { value: 'medication_missed', label: '漏服药物提醒' }
]

// 设置数据
const settings = reactive({
  basic: {
    systemName: '安心宝',
    version: 'v1.0.0',
    contactEmail: 'support@anxinbao.com',
    supportPhone: '400-800-1234',
    announcement: '',
    maintenanceMode: false
  },
  notification: {
    sms: {
      enabled: true,
      apiKey: '',
      signature: '安心宝',
      triggers: ['sos', 'health_critical']
    },
    push: {
      enabled: true,
      template: '{name}的{type}数据异常，请及时关注！',
      sound: true,
      vibrate: true
    },
    email: {
      enabled: false,
      smtpHost: '',
      smtpPort: 587,
      fromEmail: '',
      password: ''
    }
  },
  threshold: {
    bloodPressure: {
      systolicMin: 90,
      systolicMax: 140,
      diastolicMin: 60,
      diastolicMax: 90
    },
    heartRate: {
      min: 60,
      max: 100
    },
    bloodSugar: {
      fastingMin: 3.9,
      fastingMax: 6.1,
      postprandialMin: 4.4,
      postprandialMax: 7.8
    },
    temperature: {
      min: 36.0,
      max: 37.3
    }
  },
  security: {
    passwordComplexity: true,
    loginCaptcha: false,
    loginLock: true,
    sessionTimeout: 60,
    passwordExpiry: 90
  },
  data: {
    retentionDays: 365,
    autoBackup: true,
    backupTime: '03:00',
    backupRetentionCount: 7
  }
})

// 保存所有设置
async function saveAllSettings() {
  saving.value = true

  // 模拟API调用
  await new Promise(resolve => setTimeout(resolve, 1500))

  saving.value = false
  alert('设置已保存')
}

// 创建备份
async function createBackup() {
  backingUp.value = true

  // 模拟备份
  await new Promise(resolve => setTimeout(resolve, 3000))

  lastBackup.value = new Date().toLocaleString('zh-CN')
  backingUp.value = false
  alert('备份创建成功')
}
</script>

<style scoped>
.pl-13 {
  padding-left: 3.25rem;
}
</style>
