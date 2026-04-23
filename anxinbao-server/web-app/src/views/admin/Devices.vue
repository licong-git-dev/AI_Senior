<template>
  <div>
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">设备管理</h1>
      <div class="flex gap-2">
        <button class="px-4 py-2 bg-white border border-gray-200 rounded-lg flex items-center hover:bg-gray-50">
          <svg class="w-5 h-5 mr-2 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          刷新状态
        </button>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg flex items-center" @click="showAddModal = true">
          <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          添加设备
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-xl p-5 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">设备总数</p>
            <p class="text-3xl font-bold text-gray-800 mt-1">{{ stats.total }}</p>
          </div>
          <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-5 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">在线设备</p>
            <p class="text-3xl font-bold text-green-600 mt-1">{{ stats.online }}</p>
          </div>
          <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728m-9.9-2.829a5 5 0 010-7.07m7.072 0a5 5 0 010 7.07M13 12a1 1 0 11-2 0 1 1 0 012 0z" />
            </svg>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-5 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">离线设备</p>
            <p class="text-3xl font-bold text-gray-600 mt-1">{{ stats.offline }}</p>
          </div>
          <div class="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" />
            </svg>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-5 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">电量告警</p>
            <p class="text-3xl font-bold text-red-600 mt-1">{{ stats.lowBattery }}</p>
          </div>
          <div class="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="bg-white rounded-xl p-4 shadow-sm mb-6">
      <div class="flex flex-wrap gap-4">
        <div class="flex-1 min-w-[200px]">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索设备ID/名称..."
            class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <select v-model="filterType" class="px-4 py-2 border border-gray-200 rounded-lg">
          <option value="all">全部类型</option>
          <option value="watch">智能手表</option>
          <option value="bp_monitor">血压计</option>
          <option value="glucose_monitor">血糖仪</option>
          <option value="sos_button">SOS按钮</option>
          <option value="camera">摄像头</option>
        </select>
        <select v-model="filterStatus" class="px-4 py-2 border border-gray-200 rounded-lg">
          <option value="all">全部状态</option>
          <option value="online">在线</option>
          <option value="offline">离线</option>
        </select>
        <button class="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50" @click="resetFilters">
          重置
        </button>
      </div>
    </div>

    <!-- 设备列表 -->
    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">设备信息</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">类型</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">绑定用户</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">状态</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">电量</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">最后同步</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="device in filteredDevices" :key="device.id" class="hover:bg-gray-50">
              <td class="px-4 py-4">
                <div class="flex items-center">
                  <div :class="[
                    'w-10 h-10 rounded-xl flex items-center justify-center mr-3',
                    getDeviceIconBg(device.type)
                  ]">
                    <component :is="getDeviceIcon(device.type)" :class="['w-5 h-5', getDeviceIconColor(device.type)]" />
                  </div>
                  <div>
                    <p class="font-medium text-gray-800">{{ device.name }}</p>
                    <p class="text-sm text-gray-500">{{ device.deviceId }}</p>
                  </div>
                </div>
              </td>
              <td class="px-4 py-4">
                <span class="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm">{{ device.typeText }}</span>
              </td>
              <td class="px-4 py-4">
                <div v-if="device.user">
                  <p class="text-gray-800">{{ device.user.name }}</p>
                  <p class="text-sm text-gray-500">{{ device.user.phone }}</p>
                </div>
                <span v-else class="text-gray-400">未绑定</span>
              </td>
              <td class="px-4 py-4">
                <div class="flex items-center">
                  <span :class="[
                    'w-2 h-2 rounded-full mr-2',
                    device.status === 'online' ? 'bg-green-500' : 'bg-gray-400'
                  ]"></span>
                  <span :class="device.status === 'online' ? 'text-green-600' : 'text-gray-500'">
                    {{ device.status === 'online' ? '在线' : '离线' }}
                  </span>
                </div>
              </td>
              <td class="px-4 py-4">
                <div class="flex items-center">
                  <div class="w-16 h-2 bg-gray-200 rounded-full mr-2">
                    <div
                      :class="[
                        'h-full rounded-full',
                        device.battery > 50 ? 'bg-green-500' : device.battery > 20 ? 'bg-yellow-500' : 'bg-red-500'
                      ]"
                      :style="{ width: device.battery + '%' }"
                    ></div>
                  </div>
                  <span :class="[
                    'text-sm',
                    device.battery > 50 ? 'text-green-600' : device.battery > 20 ? 'text-yellow-600' : 'text-red-600'
                  ]">{{ device.battery }}%</span>
                </div>
              </td>
              <td class="px-4 py-4 text-gray-600 text-sm">{{ device.lastSync }}</td>
              <td class="px-4 py-4">
                <div class="flex items-center space-x-2">
                  <button class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg" title="查看详情" @click="viewDevice(device)">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  <button class="p-2 text-green-600 hover:bg-green-50 rounded-lg" title="编辑" @click="editDevice(device)">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button class="p-2 text-red-600 hover:bg-red-50 rounded-lg" title="解绑" @click="unbindDevice(device)">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="p-4 border-t border-gray-100 flex items-center justify-between">
        <span class="text-sm text-gray-500">共 {{ filteredDevices.length }} 台设备</span>
        <div class="flex items-center space-x-2">
          <button class="px-3 py-1 border border-gray-200 rounded text-sm text-gray-600 hover:bg-gray-50">上一页</button>
          <button class="px-3 py-1 bg-primary-500 text-white rounded text-sm">1</button>
          <button class="px-3 py-1 border border-gray-200 rounded text-sm text-gray-600 hover:bg-gray-50">2</button>
          <button class="px-3 py-1 border border-gray-200 rounded text-sm text-gray-600 hover:bg-gray-50">下一页</button>
        </div>
      </div>
    </div>

    <!-- 添加设备弹窗 -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="bg-white rounded-2xl w-full max-w-md mx-4 p-6">
        <h2 class="text-xl font-bold text-gray-800 mb-6">添加新设备</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">设备ID</label>
            <input v-model="newDevice.deviceId" type="text" placeholder="请输入设备ID" class="w-full px-4 py-2 border border-gray-200 rounded-lg" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">设备名称</label>
            <input v-model="newDevice.name" type="text" placeholder="请输入设备名称" class="w-full px-4 py-2 border border-gray-200 rounded-lg" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">设备类型</label>
            <select v-model="newDevice.type" class="w-full px-4 py-2 border border-gray-200 rounded-lg">
              <option value="">请选择</option>
              <option value="watch">智能手表</option>
              <option value="bp_monitor">血压计</option>
              <option value="glucose_monitor">血糖仪</option>
              <option value="sos_button">SOS按钮</option>
              <option value="camera">摄像头</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">绑定用户手机号（可选）</label>
            <input v-model="newDevice.userPhone" type="text" placeholder="请输入用户手机号" class="w-full px-4 py-2 border border-gray-200 rounded-lg" />
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button class="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg" @click="showAddModal = false">取消</button>
          <button class="px-4 py-2 bg-primary-500 text-white rounded-lg" @click="addDevice">确认添加</button>
        </div>
      </div>
    </div>

    <!-- 设备详情弹窗 -->
    <div v-if="showDetailModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="bg-white rounded-2xl w-full max-w-lg mx-4 p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-gray-800">设备详情</h2>
          <button class="p-2 hover:bg-gray-100 rounded-lg" @click="showDetailModal = false">
            <svg class="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div v-if="selectedDevice" class="space-y-4">
          <div class="flex items-center p-4 bg-gray-50 rounded-xl">
            <div :class="['w-16 h-16 rounded-xl flex items-center justify-center mr-4', getDeviceIconBg(selectedDevice.type)]">
              <component :is="getDeviceIcon(selectedDevice.type)" :class="['w-8 h-8', getDeviceIconColor(selectedDevice.type)]" />
            </div>
            <div>
              <p class="text-xl font-bold text-gray-800">{{ selectedDevice.name }}</p>
              <p class="text-gray-500">{{ selectedDevice.deviceId }}</p>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="p-3 bg-gray-50 rounded-lg">
              <p class="text-sm text-gray-500">设备类型</p>
              <p class="font-medium text-gray-800">{{ selectedDevice.typeText }}</p>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg">
              <p class="text-sm text-gray-500">当前状态</p>
              <p :class="['font-medium', selectedDevice.status === 'online' ? 'text-green-600' : 'text-gray-600']">
                {{ selectedDevice.status === 'online' ? '在线' : '离线' }}
              </p>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg">
              <p class="text-sm text-gray-500">电量</p>
              <p class="font-medium text-gray-800">{{ selectedDevice.battery }}%</p>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg">
              <p class="text-sm text-gray-500">固件版本</p>
              <p class="font-medium text-gray-800">{{ selectedDevice.firmware || 'v1.0.0' }}</p>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg col-span-2">
              <p class="text-sm text-gray-500">绑定用户</p>
              <p class="font-medium text-gray-800">{{ selectedDevice.user?.name || '未绑定' }}</p>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg col-span-2">
              <p class="text-sm text-gray-500">最后同步时间</p>
              <p class="font-medium text-gray-800">{{ selectedDevice.lastSync }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, h } from 'vue'

const searchQuery = ref('')
const filterType = ref('all')
const filterStatus = ref('all')
const showAddModal = ref(false)
const showDetailModal = ref(false)
const selectedDevice = ref(null)

const newDevice = ref({
  deviceId: '',
  name: '',
  type: '',
  userPhone: ''
})

const stats = ref({
  total: 156,
  online: 142,
  offline: 14,
  lowBattery: 8
})

const devices = ref([
  { id: 1, deviceId: 'AX-W-10001', name: '王爷爷的手表', type: 'watch', typeText: '智能手表', status: 'online', battery: 85, lastSync: '2分钟前', user: { name: '王建国', phone: '138****8001' } },
  { id: 2, deviceId: 'AX-BP-20001', name: '王爷爷血压计', type: 'bp_monitor', typeText: '血压计', status: 'online', battery: 62, lastSync: '30分钟前', user: { name: '王建国', phone: '138****8001' } },
  { id: 3, deviceId: 'AX-W-10002', name: '李奶奶的手表', type: 'watch', typeText: '智能手表', status: 'online', battery: 45, lastSync: '5分钟前', user: { name: '李芳', phone: '139****8002' } },
  { id: 4, deviceId: 'AX-SOS-30001', name: 'SOS紧急按钮', type: 'sos_button', typeText: 'SOS按钮', status: 'online', battery: 92, lastSync: '1小时前', user: { name: '李芳', phone: '139****8002' } },
  { id: 5, deviceId: 'AX-W-10003', name: '张爷爷的手表', type: 'watch', typeText: '智能手表', status: 'offline', battery: 15, lastSync: '2天前', user: { name: '张强', phone: '136****8003' } },
  { id: 6, deviceId: 'AX-GL-40001', name: '血糖仪', type: 'glucose_monitor', typeText: '血糖仪', status: 'online', battery: 78, lastSync: '1小时前', user: { name: '王建国', phone: '138****8001' } },
  { id: 7, deviceId: 'AX-CAM-50001', name: '客厅摄像头', type: 'camera', typeText: '摄像头', status: 'online', battery: 100, lastSync: '刚刚', user: { name: '李芳', phone: '139****8002' } },
  { id: 8, deviceId: 'AX-W-10004', name: '未绑定手表', type: 'watch', typeText: '智能手表', status: 'offline', battery: 0, lastSync: '从未', user: null }
])

const filteredDevices = computed(() => {
  return devices.value.filter(device => {
    if (filterType.value !== 'all' && device.type !== filterType.value) return false
    if (filterStatus.value !== 'all' && device.status !== filterStatus.value) return false
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      return device.name.toLowerCase().includes(query) ||
             device.deviceId.toLowerCase().includes(query) ||
             device.user?.name.toLowerCase().includes(query)
    }
    return true
  })
})

// 设备图标组件
const WatchIcon = { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' })
])}

const BpIcon = { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z' })
])}

const GlucoseIcon = { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z' })
])}

const SosIcon = { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9' })
])}

const CameraIcon = { render: () => h('svg', { fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z' })
])}

function getDeviceIcon(type) {
  const icons = {
    watch: WatchIcon,
    bp_monitor: BpIcon,
    glucose_monitor: GlucoseIcon,
    sos_button: SosIcon,
    camera: CameraIcon
  }
  return icons[type] || WatchIcon
}

function getDeviceIconBg(type) {
  const colors = {
    watch: 'bg-blue-100',
    bp_monitor: 'bg-red-100',
    glucose_monitor: 'bg-purple-100',
    sos_button: 'bg-orange-100',
    camera: 'bg-green-100'
  }
  return colors[type] || 'bg-gray-100'
}

function getDeviceIconColor(type) {
  const colors = {
    watch: 'text-blue-600',
    bp_monitor: 'text-red-600',
    glucose_monitor: 'text-purple-600',
    sos_button: 'text-orange-600',
    camera: 'text-green-600'
  }
  return colors[type] || 'text-gray-600'
}

function resetFilters() {
  searchQuery.value = ''
  filterType.value = 'all'
  filterStatus.value = 'all'
}

function viewDevice(device) {
  selectedDevice.value = device
  showDetailModal.value = true
}

function editDevice(device) {
  window.$toast?.info('编辑设备功能开发中')
}

function unbindDevice(device) {
  if (confirm(`确定要解绑设备 ${device.name} 吗？`)) {
    window.$toast?.success('设备已解绑')
  }
}

function addDevice() {
  if (!newDevice.value.deviceId || !newDevice.value.name || !newDevice.value.type) {
    window.$toast?.error('请填写完整信息')
    return
  }
  window.$toast?.success('设备添加成功')
  showAddModal.value = false
  newDevice.value = { deviceId: '', name: '', type: '', userPhone: '' }
}
</script>
