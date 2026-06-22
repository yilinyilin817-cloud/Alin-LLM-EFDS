<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const route = useRoute()
const isOpen = ref(false)
const { currentUser, isAuthenticated, logout } = useAuth()

const navItems = [
  { path: '/', label: '首页', icon: '🏠' },
  { path: '/diagnosis', label: '智能诊断', icon: '🔍' },
  { path: '/knowledge', label: '知识库', icon: '📚' },
  { path: '/chat', label: '智能问答', icon: '💬' },
  { path: '/cases', label: '案例管理', icon: '📋' },
  { path: '/devices', label: '设备档案', icon: '🏭' },
  { path: '/system', label: '系统管理', icon: '⚙️' },
]

const toggleMenu = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
}

const navigateTo = (path: string) => {
  router.push(path)
  isOpen.value = false
  document.body.style.overflow = ''
}

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <div class="md:hidden">
    <button
      @click="toggleMenu"
      class="p-2 text-slate-600 hover:text-blue-600 transition-colors"
      aria-label="菜单"
    >
      <svg v-if="!isOpen" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
      <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <Transition name="slide">
      <div v-if="isOpen" class="fixed inset-0 z-50">
        <div class="absolute inset-0 bg-black/50" @click="toggleMenu"></div>
        
        <div class="absolute right-0 top-0 h-full w-72 bg-white shadow-xl">
          <div class="p-4 border-b border-slate-200">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                  <span class="text-white text-sm">🔧</span>
                </div>
                <span class="font-bold text-slate-900">LLM-EFDS</span>
              </div>
              <button @click="toggleMenu" class="p-2 text-slate-400 hover:text-slate-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <nav class="p-4">
            <div class="space-y-2">
              <button
                v-for="item in navItems"
                :key="item.path"
                @click="navigateTo(item.path)"
                class="w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all text-left"
                :class="isActive(item.path) 
                  ? 'bg-blue-50 text-blue-600' 
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'"
              >
                <span class="text-xl">{{ item.icon }}</span>
                <span class="font-medium">{{ item.label }}</span>
                <svg 
                  v-if="isActive(item.path)" 
                  class="w-4 h-4 ml-auto" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </nav>

          <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-200">
            <div v-if="isAuthenticated" class="space-y-3">
              <div class="flex items-center gap-3 px-2">
                <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-full flex items-center justify-center">
                  <span class="text-white text-base font-medium">{{ currentUser?.username?.charAt(0).toUpperCase() }}</span>
                </div>
                <div>
                  <p class="text-sm font-semibold text-slate-900">{{ currentUser?.username }}</p>
                  <p class="text-xs text-slate-500">{{ currentUser?.role === 'admin' ? '管理员' : '普通用户' }}</p>
                </div>
              </div>
              <button
                @click="logout(); navigateTo('/login')"
                class="w-full px-4 py-2.5 bg-red-50 text-red-600 font-medium rounded-lg hover:bg-red-100 transition-colors text-sm"
              >
                退出登录
              </button>
            </div>
            <button
              v-else
              @click="navigateTo('/login')"
              class="w-full px-4 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              登录 / 注册
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
}

.slide-enter-from .absolute.right-0,
.slide-leave-to .absolute.right-0 {
  transform: translateX(100%);
}
</style>
