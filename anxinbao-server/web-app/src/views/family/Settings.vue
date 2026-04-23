<template>
  <div class="max-w-4xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">设置</h1>

    <!-- 设置导航标签 -->
    <div class="bg-white rounded-xl shadow-sm mb-6">
      <div class="flex border-b border-gray-100">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          @click="activeTab = tab.value"
          :class="[
            'flex-1 py-4 text-center font-medium transition-colors relative',
            activeTab === tab.value
              ? 'text-primary-600'
              : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          {{ tab.label }}
          <span
            v-if="activeTab === tab.value"
            class="absolute bottom-0 left-1/4 right-1/4 h-0.5 bg-primary-500 rounded-full"
          ></span>
        </button>
      </div>
    </div>

    <!-- 个人资料 -->
    <div v-show="activeTab === 'profile'" class="space-y-6">
      <!-- 头像 -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <h2 class="font-bold text-gray-800 mb-4">个人信息</h2>
        <div class="flex items-center mb-6">
          <div class="relative">
            <div class="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 text-2xl font-bold">
              {{ userInfo.name?.charAt(0) || '用' }}
            </div>
            <label class="absolute bottom-0 right-0 w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center cursor-pointer shadow-lg hover:bg-primary-600">
              <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <input type="file" accept="image/*" class="hidden" @change="uploadAvatar" />
            </label>
          </div>
          <div class="ml-6">
            <p class="text-lg font-bold text-gray-800">{{ userInfo.name }}</p>
            <p class="text-gray-500">{{ userInfo.phone }}</p>
            <p class="text-sm text-gray-400 mt-1">注册于 {{ userInfo.registerDate }}</p>
          </div>
        </div>

        <!-- 基本信息表单 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-gray-600 mb-1">姓名</label>
            <input
              v-model="userInfo.name"
              type="text"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">性别</label>
            <select
              v-model="userInfo.gender"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">请选择</option>
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">与老人关系</label>
            <select
              v-model="userInfo.relation"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="son">儿子</option>
              <option value="daughter">女儿</option>
              <option value="spouse">配偶</option>
              <option value="grandchild">孙子/孙女</option>
              <option value="other">其他</option>
            </select>
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">联系邮箱</label>
            <input
              v-model="userInfo.email"
              type="email"
              placeholder="用于接收健康报告"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        <div class="mt-6 flex justify-end">
          <button
            @click="saveProfile"
            class="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
          >
            保存修改
          </button>
        </div>
      </div>

      <!-- 绑定的老人 -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-bold text-gray-800">关联的老人</h2>
          <button class="text-primary-600 text-sm hover:text-primary-700">
            + 添加老人
          </button>
        </div>
        <div class="space-y-3">
          <div
            v-for="elderly in boundElderly"
            :key="elderly.id"
            class="flex items-center justify-between p-4 bg-gray-50 rounded-xl"
          >
            <div class="flex items-center">
              <div class="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-bold mr-4">
                {{ elderly.name.charAt(0) }}
              </div>
              <div>
                <p class="font-medium text-gray-800">{{ elderly.name }}</p>
                <p class="text-sm text-gray-500">{{ elderly.phone }} · {{ elderly.relation }}</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span :class="[
                'px-2 py-1 rounded text-xs',
                elderly.status === 'online' ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600'
              ]">
                {{ elderly.status === 'online' ? '在线' : '离线' }}
              </span>
              <button class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 通知设置 -->
    <div v-show="activeTab === 'notification'" class="space-y-6">
      <!-- 通知方式 -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <h2 class="font-bold text-gray-800 mb-4">通知方式</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
            <div class="flex items-center">
              <div class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center mr-4">
                <svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <div>
                <p class="font-medium text-gray-800">APP推送通知</p>
                <p class="text-sm text-gray-500">通过手机APP接收即时通知</p>
              </div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="notifications.push" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
            <div class="flex items-center">
              <div class="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center mr-4">
                <svg class="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <div>
                <p class="font-medium text-gray-800">短信通知</p>
                <p class="text-sm text-gray-500">通过短信接收重要告警</p>
              </div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="notifications.sms" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
            <div class="flex items-center">
              <div class="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center mr-4">
                <svg class="w-5 h-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <p class="font-medium text-gray-800">邮件通知</p>
                <p class="text-sm text-gray-500">通过邮件接收健康报告</p>
              </div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="notifications.email" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
            <div class="flex items-center">
              <div class="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center mr-4">
                <svg class="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
              </div>
              <div>
                <p class="font-medium text-gray-800">电话通知</p>
                <p class="text-sm text-gray-500">紧急情况电话通知（仅SOS）</p>
              </div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="notifications.phone" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>
        </div>
      </div>

      <!-- 通知类型 -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <h2 class="font-bold text-gray-800 mb-4">通知类型</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-800">紧急告警通知</p>
              <p class="text-sm text-gray-500">SOS求助、跌倒检测、离开安全区域</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="notificationTypes.emergency" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-800">健康异常通知</p>
              <p class="text-sm text-gray-500">血压、心率、血糖异常提醒</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="notificationTypes.health" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-800">用药提醒通知</p>
              <p class="text-sm text-gray-500">服药完成、漏服药物提醒</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="notificationTypes.medication" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-800">设备状态通知</p>
              <p class="text-sm text-gray-500">设备离线、低电量提醒</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="notificationTypes.device" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-800">日常健康报告</p>
              <p class="text-sm text-gray-500">每日、每周健康数据汇总</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="notificationTypes.report" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>
        </div>
      </div>

      <!-- 免打扰设置 -->
      <div class="bg-white rounded-xl shadow-sm p-6">
        <h2 class="font-bold text-gray-800 mb-4">免打扰设置</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-800">开启免打扰</p>
              <p class="text-sm text-gray-500">在指定时间段内不接收非紧急通知</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="doNotDisturb.enabled" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div v-if="doNotDisturb.enabled" class="flex items-center gap-4 pt-2">
            <div class="flex-1">
              <label class="block text-sm text-gray-600 mb-1">开始时间</label>
              <input
                v-model="doNotDisturb.startTime"
                type="time"
                class="w-full px-4 py-2 border border-gray-200 rounded-lg"
              />
            </div>
            <div class="flex-1">
              <label class="block text-sm text-gray-600 mb-1">结束时间</label>
              <input
                v-model="doNotDisturb.endTime"
                type="time"
                class="w-full px-4 py-2 border border-gray-200 rounded-lg"
              />
            </div>
          </div>

          <p v-if="doNotDisturb.enabled" class="text-sm text-yellow-600 bg-yellow-50 p-3 rounded-lg">
            注意：紧急告警（SOS、跌倒检测）不受免打扰限制
          </p>
        </div>
      </div>
    </div>

    <!-- 隐私设置 -->
    <div v-show="activeTab === 'privacy'" class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm p-6">
        <h2 class="font-bold text-gray-800 mb-4">数据隐私</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-800">位置信息共享</p>
              <p class="text-sm text-gray-500">允许老人查看您的位置</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="privacy.shareLocation" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-800">健康数据分析</p>
              <p class="text-sm text-gray-500">允许使用匿名数据改进服务</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="privacy.dataAnalytics" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-800">在线状态显示</p>
              <p class="text-sm text-gray-500">向其他家属显示您的在线状态</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="privacy.showOnline" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm p-6">
        <h2 class="font-bold text-gray-800 mb-4">账号安全</h2>
        <div class="space-y-3">
          <button
            @click="showPasswordModal = true"
            class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <div class="flex items-center">
              <svg class="w-5 h-5 text-gray-500 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span class="text-gray-800">修改密码</span>
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <button
            @click="showPhoneModal = true"
            class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <div class="flex items-center">
              <svg class="w-5 h-5 text-gray-500 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <span class="text-gray-800">更换手机号</span>
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <button class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
            <div class="flex items-center">
              <svg class="w-5 h-5 text-gray-500 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span class="text-gray-800">登录设备管理</span>
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm p-6">
        <h2 class="font-bold text-gray-800 mb-4">数据管理</h2>
        <div class="space-y-3">
          <button class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
            <div class="flex items-center">
              <svg class="w-5 h-5 text-gray-500 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span class="text-gray-800">导出我的数据</span>
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <button class="w-full flex items-center justify-between px-4 py-3 bg-red-50 rounded-xl hover:bg-red-100 transition-colors text-red-600">
            <div class="flex items-center">
              <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <span>注销账号</span>
            </div>
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 其他设置 -->
    <div v-show="activeTab === 'other'" class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm p-6">
        <h2 class="font-bold text-gray-800 mb-4">应用设置</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-800">语言</p>
              <p class="text-sm text-gray-500">选择应用显示语言</p>
            </div>
            <select
              v-model="appSettings.language"
              class="px-4 py-2 border border-gray-200 rounded-lg"
            >
              <option value="zh-CN">简体中文</option>
              <option value="zh-TW">繁體中文</option>
              <option value="en-US">English</option>
            </select>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-800">深色模式</p>
              <p class="text-sm text-gray-500">开启深色主题</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="appSettings.darkMode" class="sr-only peer" />
              <div class="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-800">字体大小</p>
              <p class="text-sm text-gray-500">调整应用字体大小</p>
            </div>
            <select
              v-model="appSettings.fontSize"
              class="px-4 py-2 border border-gray-200 rounded-lg"
            >
              <option value="small">小</option>
              <option value="medium">中</option>
              <option value="large">大</option>
            </select>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm p-6">
        <h2 class="font-bold text-gray-800 mb-4">关于</h2>
        <div class="space-y-3">
          <div class="flex items-center justify-between py-2">
            <span class="text-gray-600">版本号</span>
            <span class="text-gray-800">v1.0.0</span>
          </div>
          <div class="flex items-center justify-between py-2">
            <span class="text-gray-600">更新日期</span>
            <span class="text-gray-800">2024-01-15</span>
          </div>
          <button class="w-full py-3 text-primary-600 hover:bg-primary-50 rounded-lg transition-colors">
            检查更新
          </button>
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm p-6">
        <h2 class="font-bold text-gray-800 mb-4">帮助与反馈</h2>
        <div class="space-y-3">
          <button class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
            <span class="text-gray-800">常见问题</span>
            <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          <button class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
            <span class="text-gray-800">联系客服</span>
            <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          <button class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
            <span class="text-gray-800">意见反馈</span>
            <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          <button class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
            <span class="text-gray-800">用户协议</span>
            <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          <button class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
            <span class="text-gray-800">隐私政策</span>
            <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <!-- 退出登录 -->
      <button
        @click="logout"
        class="w-full py-4 bg-white rounded-xl shadow-sm text-red-600 font-medium hover:bg-red-50 transition-colors"
      >
        退出登录
      </button>
    </div>

    <!-- 修改密码弹窗 -->
    <div v-if="showPasswordModal" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="fixed inset-0 bg-black bg-opacity-50" @click="showPasswordModal = false"></div>
      <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-4">修改密码</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-600 mb-1">当前密码</label>
            <input
              v-model="passwordForm.oldPassword"
              type="password"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">新密码</label>
            <input
              v-model="passwordForm.newPassword"
              type="password"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">确认新密码</label>
            <input
              v-model="passwordForm.confirmPassword"
              type="password"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
        <div class="flex gap-3 mt-6">
          <button
            @click="showPasswordModal = false"
            class="flex-1 py-2 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50"
          >
            取消
          </button>
          <button
            @click="changePassword"
            class="flex-1 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
          >
            确认修改
          </button>
        </div>
      </div>
    </div>

    <!-- 更换手机号弹窗 -->
    <div v-if="showPhoneModal" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="fixed inset-0 bg-black bg-opacity-50" @click="showPhoneModal = false"></div>
      <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-4">更换手机号</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-600 mb-1">新手机号</label>
            <input
              v-model="phoneForm.newPhone"
              type="tel"
              placeholder="请输入新手机号"
              class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">验证码</label>
            <div class="flex gap-3">
              <input
                v-model="phoneForm.code"
                type="text"
                placeholder="请输入验证码"
                class="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
              <button
                @click="sendCode"
                :disabled="countdown > 0"
                class="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 disabled:opacity-50"
              >
                {{ countdown > 0 ? `${countdown}s` : '发送验证码' }}
              </button>
            </div>
          </div>
        </div>
        <div class="flex gap-3 mt-6">
          <button
            @click="showPhoneModal = false"
            class="flex-1 py-2 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50"
          >
            取消
          </button>
          <button
            @click="changePhone"
            class="flex-1 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
          >
            确认更换
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 当前标签
const activeTab = ref('profile')
const tabs = [
  { value: 'profile', label: '个人资料' },
  { value: 'notification', label: '通知设置' },
  { value: 'privacy', label: '隐私安全' },
  { value: 'other', label: '其他' }
]

// 用户信息
const userInfo = ref({
  name: '王先生',
  phone: '138****8003',
  email: 'wang@example.com',
  gender: 'male',
  relation: 'son',
  registerDate: '2024-01-01'
})

// 绑定的老人
const boundElderly = ref([
  { id: 1, name: '张大爷', phone: '138****8001', relation: '父亲', status: 'online' },
  { id: 2, name: '李奶奶', phone: '138****8002', relation: '母亲', status: 'offline' }
])

// 通知方式
const notifications = ref({
  push: true,
  sms: true,
  email: false,
  phone: true
})

// 通知类型
const notificationTypes = ref({
  emergency: true,
  health: true,
  medication: true,
  device: false,
  report: false
})

// 免打扰设置
const doNotDisturb = ref({
  enabled: false,
  startTime: '22:00',
  endTime: '07:00'
})

// 隐私设置
const privacy = ref({
  shareLocation: true,
  dataAnalytics: true,
  showOnline: true
})

// 应用设置
const appSettings = ref({
  language: 'zh-CN',
  darkMode: false,
  fontSize: 'medium'
})

// 弹窗控制
const showPasswordModal = ref(false)
const showPhoneModal = ref(false)

// 修改密码表单
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 更换手机号表单
const phoneForm = ref({
  newPhone: '',
  code: ''
})

// 验证码倒计时
const countdown = ref(0)

// 方法
function uploadAvatar(event) {
  const file = event.target.files[0]
  if (file) {
    // TODO: 上传头像
    console.log('上传头像:', file.name)
  }
}

function saveProfile() {
  // TODO: 保存个人资料
  alert('保存成功')
}

function changePassword() {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    alert('两次密码输入不一致')
    return
  }
  // TODO: 调用API修改密码
  alert('密码修改成功')
  showPasswordModal.value = false
  passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
}

function sendCode() {
  if (!phoneForm.value.newPhone) {
    alert('请输入手机号')
    return
  }
  // TODO: 发送验证码
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer)
    }
  }, 1000)
}

function changePhone() {
  if (!phoneForm.value.newPhone || !phoneForm.value.code) {
    alert('请填写完整信息')
    return
  }
  // TODO: 调用API更换手机号
  alert('手机号更换成功')
  showPhoneModal.value = false
  phoneForm.value = { newPhone: '', code: '' }
}

function logout() {
  if (confirm('确定要退出登录吗？')) {
    userStore.logout()
    router.push('/login')
  }
}
</script>
