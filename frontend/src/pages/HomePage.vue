<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import MobileNav from '@/components/MobileNav.vue'

const router = useRouter()
const { currentUser, isAuthenticated, logout } = useAuth()

const showUserMenu = ref(false)

const handleLogout = () => {
  logout()
  showUserMenu.value = false
  router.push('/login')
}

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

const closeUserMenu = () => {
  showUserMenu.value = false
}

const features = ref([
  {
    title: '智能诊断',
    description: '基于AI的设备故障智能诊断，快速定位问题',
    icon: '🔍',
    path: '/diagnosis',
  },
  {
    title: '知识库',
    description: '设备维护知识库，支持文档上传与智能检索',
    icon: '📚',
    path: '/knowledge',
  },
  {
    title: '案例管理',
    description: '历史故障案例管理，经验积累与复用',
    icon: '📋',
    path: '/cases',
  },
  {
    title: '设备档案',
    description: '设备信息管理，维护记录追踪',
    icon: '🏭',
    path: '/devices',
  },
  {
    title: '智能问答',
    description: 'AI助手实时对话，专业问题解答',
    icon: '💬',
    path: '/chat',
  },
  {
    title: '系统管理',
    description: '用户权限管理，系统配置',
    icon: '⚙️',
    path: '/system',
  },
])

const recentCases = ref([
  { id: 1, title: '电机异常振动诊断', device: '三相异步电机', severity: 'high', date: '2024-01-15' },
  { id: 2, title: '液压系统压力不足', device: '液压泵站', severity: 'medium', date: '2024-01-14' },
  { id: 3, title: 'PLC通信故障', device: '西门子S7-1200', severity: 'low', date: '2024-01-13' },
])

const hotQuestions = ref([
  '电机运行时出现异常振动和温度升高',
  '液压系统压力不稳定',
  '变频器频繁报警',
  'PLC程序运行异常',
])

const navigateTo = (path: string) => {
  router.push(path)
}

const getSeverityColor = (severity: string) => {
  const colors: Record<string, string> = {
    high: 'bg-red-100 text-red-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-green-100 text-green-800',
  }
  return colors[severity] || 'bg-gray-100 text-gray-800'
}

const getSeverityText = (severity: string) => {
  const texts: Record<string, string> = {
    high: '高',
    medium: '中',
    low: '低',
  }
  return texts[severity] || severity
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50" @click="closeUserMenu">
    <header class="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
              <span class="text-white text-xl">🔧</span>
            </div>
            <div>
              <h1 class="text-xl font-bold text-slate-900">LLM-EFDS</h1>
              <p class="text-xs text-slate-500 hidden sm:block">基于大模型的设备故障诊断系统</p>
            </div>
          </div>
          
          <nav class="hidden md:flex items-center gap-6">
            <router-link to="/" class="text-sm font-medium text-blue-600">首页</router-link>
            <router-link to="/diagnosis" class="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">智能诊断</router-link>
            <router-link to="/knowledge" class="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">知识库</router-link>
            <router-link to="/chat" class="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">智能问答</router-link>
            <div v-if="isAuthenticated" class="relative">
              <button
                @click.stop="toggleUserMenu"
                class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-full flex items-center justify-center">
                  <span class="text-white text-sm font-medium">{{ currentUser?.username?.charAt(0).toUpperCase() }}</span>
                </div>
                <span class="text-sm font-medium text-slate-700">{{ currentUser?.username }}</span>
                <svg class="w-4 h-4 text-slate-400 transition-transform" :class="{ 'rotate-180': showUserMenu }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <Transition name="dropdown">
                <div
                  v-if="showUserMenu"
                  @click.stop
                  class="absolute right-0 mt-2 w-56 bg-white rounded-xl border border-slate-200 shadow-lg py-2 z-50"
                >
                  <div class="px-4 py-3 border-b border-slate-100">
                    <p class="text-sm font-semibold text-slate-900">{{ currentUser?.username }}</p>
                    <p class="text-xs text-slate-500 mt-0.5">{{ currentUser?.email }}</p>
                    <span class="inline-block mt-1.5 px-2 py-0.5 text-xs font-medium rounded-full"
                      :class="currentUser?.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'"
                    >
                      {{ currentUser?.role === 'admin' ? '管理员' : '普通用户' }}
                    </span>
                  </div>
                  <div class="py-1">
                    <router-link
                      to="/system"
                      @click="closeUserMenu"
                      class="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                    >
                      <span class="text-base">⚙️</span>
                      系统管理
                    </router-link>
                  </div>
                  <div class="border-t border-slate-100 pt-1">
                    <button
                      @click="handleLogout"
                      class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
                    >
                      <span class="text-base">🚪</span>
                      退出登录
                    </button>
                  </div>
                </div>
              </Transition>
            </div>
            <router-link
              v-else
              to="/login"
              class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >登录</router-link>
          </nav>

          <MobileNav />
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      <section class="text-center mb-10 sm:mb-16">
        <h2 class="text-3xl sm:text-4xl font-bold text-slate-900 mb-3 sm:mb-4">
          智能设备故障诊断
        </h2>
        <p class="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto mb-6 sm:mb-8 px-4">
          基于大语言模型和RAG技术，提供专业的设备故障诊断服务。
          快速定位故障原因，提供维修建议，积累维护经验。
        </p>
        <div class="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4 px-4">
          <button
            @click="navigateTo('/diagnosis')"
            class="w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg shadow-blue-500/25"
          >
            开始诊断
          </button>
          <button
            @click="navigateTo('/chat')"
            class="w-full sm:w-auto px-6 py-3 bg-white text-slate-700 font-medium rounded-lg border border-slate-200 hover:border-blue-300 hover:text-blue-600 transition-all"
          >
            智能问答
          </button>
        </div>
      </section>

      <section class="mb-10 sm:mb-16">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          <div
            v-for="feature in features"
            :key="feature.title"
            @click="navigateTo(feature.path)"
            class="bg-white rounded-xl p-5 sm:p-6 border border-slate-200 hover:border-blue-300 hover:shadow-lg transition-all cursor-pointer group"
          >
            <div class="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-100 transition-colors">
              <span class="text-2xl">{{ feature.icon }}</span>
            </div>
            <h3 class="text-lg font-semibold text-slate-900 mb-2">{{ feature.title }}</h3>
            <p class="text-sm text-slate-600">{{ feature.description }}</p>
          </div>
        </div>
      </section>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">
        <section class="bg-white rounded-xl p-5 sm:p-6 border border-slate-200">
          <h3 class="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <span class="text-blue-600">📋</span>
            最近故障案例
          </h3>
          <div class="space-y-3 sm:space-y-4">
            <div
              v-for="case_ in recentCases"
              :key="case_.id"
              class="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
              @click="navigateTo('/cases')"
            >
              <div class="min-w-0 flex-1 mr-3">
                <p class="font-medium text-slate-900 truncate">{{ case_.title }}</p>
                <p class="text-sm text-slate-500">{{ case_.device }} · {{ case_.date }}</p>
              </div>
              <span
                :class="getSeverityColor(case_.severity)"
                class="px-2 py-1 text-xs font-medium rounded-full shrink-0"
              >
                {{ getSeverityText(case_.severity) }}
              </span>
            </div>
          </div>
        </section>

        <section class="bg-white rounded-xl p-5 sm:p-6 border border-slate-200">
          <h3 class="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <span class="text-orange-600">🔥</span>
            热门问题
          </h3>
          <div class="space-y-3">
            <div
              v-for="(question, index) in hotQuestions"
              :key="index"
              class="flex items-center gap-3 p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
              @click="navigateTo('/diagnosis')"
            >
              <span class="w-6 h-6 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-xs font-bold shrink-0">
                {{ index + 1 }}
              </span>
              <p class="text-sm text-slate-700">{{ question }}</p>
            </div>
          </div>
        </section>
      </div>
    </main>

    <footer class="bg-white border-t border-slate-200 mt-12 sm:mt-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <div class="text-center text-sm text-slate-500">
          <p>LLM-EFDS - 基于大模型的设备故障诊断系统</p>
          <p class="mt-1">Powered by Vue 3 + FastAPI + RAG</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
