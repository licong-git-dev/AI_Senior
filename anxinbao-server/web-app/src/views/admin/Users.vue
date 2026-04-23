<template>
  <div>
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">用户管理</h1>
      <button class="px-4 py-2 bg-primary-500 text-white rounded-lg flex items-center">
        <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        添加用户
      </button>
    </div>

    <!-- 筛选和搜索 -->
    <div class="bg-white rounded-xl p-4 shadow-sm mb-6">
      <div class="flex flex-wrap gap-4">
        <div class="flex-1 min-w-[200px]">
          <input
            type="text"
            v-model="searchQuery"
            placeholder="搜索用户名/手机号..."
            class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <select v-model="filterRole" class="px-4 py-2 border border-gray-200 rounded-lg">
          <option value="all">全部角色</option>
          <option value="elderly">老人</option>
          <option value="family">家属</option>
          <option value="admin">管理员</option>
        </select>
        <select v-model="filterStatus" class="px-4 py-2 border border-gray-200 rounded-lg">
          <option value="all">全部状态</option>
          <option value="active">正常</option>
          <option value="inactive">禁用</option>
        </select>
        <button class="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50">
          重置筛选
        </button>
      </div>
    </div>

    <!-- 用户列表 -->
    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">
                <input type="checkbox" class="rounded border-gray-300" />
              </th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">用户信息</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">角色</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">状态</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">注册时间</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">最后登录</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="user in filteredUsers" :key="user.id" class="hover:bg-gray-50">
              <td class="px-4 py-4">
                <input type="checkbox" class="rounded border-gray-300" />
              </td>
              <td class="px-4 py-4">
                <div class="flex items-center">
                  <div class="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-bold mr-3">
                    {{ user.name.charAt(0) }}
                  </div>
                  <div>
                    <p class="font-medium text-gray-800">{{ user.name }}</p>
                    <p class="text-sm text-gray-500">{{ user.phone }}</p>
                  </div>
                </div>
              </td>
              <td class="px-4 py-4">
                <span :class="[
                  'px-2 py-1 rounded text-xs',
                  user.role === 'elderly' ? 'bg-blue-100 text-blue-700' :
                  user.role === 'family' ? 'bg-green-100 text-green-700' : 'bg-purple-100 text-purple-700'
                ]">
                  {{ user.roleText }}
                </span>
              </td>
              <td class="px-4 py-4">
                <span :class="[
                  'px-2 py-1 rounded text-xs',
                  user.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                ]">
                  {{ user.status === 'active' ? '正常' : '禁用' }}
                </span>
              </td>
              <td class="px-4 py-4 text-gray-600">{{ user.registerTime }}</td>
              <td class="px-4 py-4 text-gray-600">{{ user.lastLogin }}</td>
              <td class="px-4 py-4">
                <div class="flex items-center space-x-2">
                  <button class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg" title="查看">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  <button class="p-2 text-green-600 hover:bg-green-50 rounded-lg" title="编辑">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button class="p-2 text-red-600 hover:bg-red-50 rounded-lg" title="禁用">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
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
        <span class="text-sm text-gray-500">共 {{ users.length }} 条记录</span>
        <div class="flex items-center space-x-2">
          <button class="px-3 py-1 border border-gray-200 rounded text-sm text-gray-600 hover:bg-gray-50">上一页</button>
          <button class="px-3 py-1 bg-primary-500 text-white rounded text-sm">1</button>
          <button class="px-3 py-1 border border-gray-200 rounded text-sm text-gray-600 hover:bg-gray-50">2</button>
          <button class="px-3 py-1 border border-gray-200 rounded text-sm text-gray-600 hover:bg-gray-50">3</button>
          <button class="px-3 py-1 border border-gray-200 rounded text-sm text-gray-600 hover:bg-gray-50">下一页</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const searchQuery = ref('')
const filterRole = ref('all')
const filterStatus = ref('all')

const users = ref([
  { id: 1, name: '王建国', phone: '13800138001', role: 'elderly', roleText: '老人', status: 'active', registerTime: '2024-01-15', lastLogin: '1小时前' },
  { id: 2, name: '李明', phone: '13900139001', role: 'family', roleText: '家属', status: 'active', registerTime: '2024-01-14', lastLogin: '2小时前' },
  { id: 3, name: '张芳', phone: '13600136001', role: 'elderly', roleText: '老人', status: 'active', registerTime: '2024-01-13', lastLogin: '3小时前' },
  { id: 4, name: '刘伟', phone: '13700137001', role: 'family', roleText: '家属', status: 'inactive', registerTime: '2024-01-12', lastLogin: '1天前' },
  { id: 5, name: '陈红', phone: '13500135001', role: 'elderly', roleText: '老人', status: 'active', registerTime: '2024-01-11', lastLogin: '5小时前' },
  { id: 6, name: '赵强', phone: '13400134001', role: 'admin', roleText: '管理员', status: 'active', registerTime: '2024-01-01', lastLogin: '刚刚' }
])

const filteredUsers = computed(() => {
  return users.value.filter(user => {
    if (filterRole.value !== 'all' && user.role !== filterRole.value) return false
    if (filterStatus.value !== 'all' && user.status !== filterStatus.value) return false
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      return user.name.toLowerCase().includes(query) || user.phone.includes(query)
    }
    return true
  })
})
</script>
