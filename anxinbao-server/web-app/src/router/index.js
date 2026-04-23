/**
 * 安心宝 - 路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@stores/user'

// 布局组件
const ElderlyLayout = () => import('@/layouts/ElderlyLayout.vue')
const FamilyLayout = () => import('@/layouts/FamilyLayout.vue')
const AdminLayout = () => import('@/layouts/AdminLayout.vue')

// 公共页面
const Login = () => import('@views/auth/Login.vue')
const Register = () => import('@views/auth/Register.vue')

// 老人端页面
const ElderlyHome = () => import('@views/elderly/Home.vue')
const ElderlyHealth = () => import('@views/elderly/Health.vue')
const ElderlyChat = () => import('@views/elderly/Chat.vue')
const ElderlyEmergency = () => import('@views/elderly/Emergency.vue')
const ElderlyProfile = () => import('@views/elderly/Profile.vue')
const ElderlyMedication = () => import('@views/elderly/Medication.vue')
const ElderlyEntertainment = () => import('@views/elderly/Entertainment.vue')
const ElderlyCommunity = () => import('@views/elderly/Community.vue')

// 家属端页面
const FamilyDashboard = () => import('@views/family/Dashboard.vue')
const FamilyMonitor = () => import('@views/family/Monitor.vue')
const FamilyHealth = () => import('@views/family/Health.vue')
const FamilyAlerts = () => import('@views/family/Alerts.vue')
const FamilyMessages = () => import('@views/family/Messages.vue')
const FamilySettings = () => import('@views/family/Settings.vue')

// 管理后台页面
const AdminDashboard = () => import('@views/admin/Dashboard.vue')
const AdminUsers = () => import('@views/admin/Users.vue')
const AdminAlerts = () => import('@views/admin/Alerts.vue')
const AdminDevices = () => import('@views/admin/Devices.vue')
const AdminReports = () => import('@views/admin/Reports.vue')
const AdminSettings = () => import('@views/admin/Settings.vue')

const routes = [
  // 公共路由
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { guest: true, title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { guest: true, title: '注册' }
  },

  // 老人端路由
  {
    path: '/',
    component: ElderlyLayout,
    meta: { requiresAuth: true, role: 'elderly' },
    children: [
      {
        path: '',
        name: 'ElderlyHome',
        component: ElderlyHome,
        meta: { title: '首页' }
      },
      {
        path: 'health',
        name: 'ElderlyHealth',
        component: ElderlyHealth,
        meta: { title: '健康管理' }
      },
      {
        path: 'chat',
        name: 'ElderlyChat',
        component: ElderlyChat,
        meta: { title: '智能聊天' }
      },
      {
        path: 'emergency',
        name: 'ElderlyEmergency',
        component: ElderlyEmergency,
        meta: { title: '紧急求助' }
      },
      {
        path: 'profile',
        name: 'ElderlyProfile',
        component: ElderlyProfile,
        meta: { title: '我的' }
      },
      {
        path: 'medication',
        name: 'ElderlyMedication',
        component: ElderlyMedication,
        meta: { title: '用药提醒' }
      },
      {
        path: 'entertainment',
        name: 'ElderlyEntertainment',
        component: ElderlyEntertainment,
        meta: { title: '娱乐休闲' }
      },
      {
        path: 'community',
        name: 'ElderlyCommunity',
        component: ElderlyCommunity,
        meta: { title: '社区活动' }
      }
    ]
  },

  // 家属端路由
  {
    path: '/family',
    component: FamilyLayout,
    meta: { requiresAuth: true, role: 'family' },
    children: [
      {
        path: '',
        name: 'FamilyDashboard',
        component: FamilyDashboard,
        meta: { title: '家属首页' }
      },
      {
        path: 'monitor',
        name: 'FamilyMonitor',
        component: FamilyMonitor,
        meta: { title: '实时监护' }
      },
      {
        path: 'health',
        name: 'FamilyHealth',
        component: FamilyHealth,
        meta: { title: '健康数据' }
      },
      {
        path: 'alerts',
        name: 'FamilyAlerts',
        component: FamilyAlerts,
        meta: { title: '告警记录' }
      },
      {
        path: 'messages',
        name: 'FamilyMessages',
        component: FamilyMessages,
        meta: { title: '消息中心' }
      },
      {
        path: 'settings',
        name: 'FamilySettings',
        component: FamilySettings,
        meta: { title: '设置' }
      }
    ]
  },

  // 管理后台路由
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: AdminDashboard,
        meta: { title: '管理首页' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: AdminUsers,
        meta: { title: '用户管理' }
      },
      {
        path: 'alerts',
        name: 'AdminAlerts',
        component: AdminAlerts,
        meta: { title: '告警管理' }
      },
      {
        path: 'devices',
        name: 'AdminDevices',
        component: AdminDevices,
        meta: { title: '设备管理' }
      },
      {
        path: 'reports',
        name: 'AdminReports',
        component: AdminReports,
        meta: { title: '数据报表' }
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: AdminSettings,
        meta: { title: '系统设置' }
      }
    ]
  },

  // 404页面
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@views/NotFound.vue'),
    meta: { title: '页面未找到' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  }
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 安心宝` : '安心宝'

  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      return next({ name: 'Login', query: { redirect: to.fullPath } })
    }

    // 检查角色权限
    if (to.meta.role && userStore.userRole !== to.meta.role) {
      // 根据角色重定向到对应首页
      const roleRoutes = {
        elderly: 'ElderlyHome',
        family: 'FamilyDashboard',
        admin: 'AdminDashboard'
      }
      return next({ name: roleRoutes[userStore.userRole] || 'Login' })
    }
  }

  // 已登录用户访问登录页面
  if (to.meta.guest && userStore.isLoggedIn) {
    const roleRoutes = {
      elderly: 'ElderlyHome',
      family: 'FamilyDashboard',
      admin: 'AdminDashboard'
    }
    return next({ name: roleRoutes[userStore.userRole] || 'ElderlyHome' })
  }

  next()
})

export default router
