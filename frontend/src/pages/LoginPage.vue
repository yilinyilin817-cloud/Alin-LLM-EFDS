<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { login, register, isAuthenticated } = useAuth()

const isLogin = ref(true)
const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

if (isAuthenticated.value) {
  router.push('/')
}

const toggleMode = () => {
  isLogin.value = !isLogin.value
  errorMessage.value = ''
  successMessage.value = ''
}

const handleSubmit = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  if (!username.value || !password.value) {
    errorMessage.value = '请填写用户名和密码'
    return
  }

  if (!isLogin.value) {
    if (!email.value) {
      errorMessage.value = '请填写邮箱'
      return
    }
    if (password.value !== confirmPassword.value) {
      errorMessage.value = '两次密码输入不一致'
      return
    }
    if (password.value.length < 6) {
      errorMessage.value = '密码长度至少6位'
      return
    }
  }

  isLoading.value = true

  try {
    if (isLogin.value) {
      const result = await login(username.value, password.value)
      if (result.error) {
        errorMessage.value = result.error
      } else {
        router.push('/')
      }
    } else {
      const result = await register(username.value, email.value, password.value)
      if (result.error) {
        errorMessage.value = result.error
      } else {
        successMessage.value = '注册成功！请登录'
        isLogin.value = true
        password.value = ''
        confirmPassword.value = ''
      }
    }
  } catch (err: any) {
    errorMessage.value = err.message || '操作失败，请重试'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4 sm:p-6">
    <div class="w-full max-w-sm sm:max-w-md">
      <div class="text-center mb-6 sm:mb-8">
        <router-link to="/" class="inline-flex items-center gap-3 mb-4">
          <div class="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
            <span class="text-white text-xl sm:text-2xl">🔧</span>
          </div>
        </router-link>
        <h1 class="text-xl sm:text-2xl font-bold text-slate-900">LLM-EFDS</h1>
        <p class="text-xs sm:text-sm text-slate-600 mt-1">基于大模型的设备故障诊断系统</p>
      </div>

      <div class="bg-white rounded-xl sm:rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-lg sm:shadow-xl">
        <div class="text-center mb-5 sm:mb-6">
          <h2 class="text-lg sm:text-xl font-semibold text-slate-900">
            {{ isLogin ? '欢迎回来' : '创建账户' }}
          </h2>
          <p class="text-xs sm:text-sm text-slate-500 mt-1">
            {{ isLogin ? '登录您的账户继续使用' : '注册新账户开始使用' }}
          </p>
        </div>

        <div v-if="errorMessage" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-sm text-red-600">{{ errorMessage }}</p>
        </div>

        <div v-if="successMessage" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p class="text-sm text-green-600">{{ successMessage }}</p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-3 sm:space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5 sm:mb-2">
              用户名
            </label>
            <input
              v-model="username"
              type="text"
              placeholder="请输入用户名"
              class="w-full px-3 sm:px-4 py-2.5 sm:py-3 text-sm sm:text-base border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>

          <div v-if="!isLogin">
            <label class="block text-sm font-medium text-slate-700 mb-1.5 sm:mb-2">
              邮箱
            </label>
            <input
              v-model="email"
              type="email"
              placeholder="请输入邮箱"
              class="w-full px-3 sm:px-4 py-2.5 sm:py-3 text-sm sm:text-base border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5 sm:mb-2">
              密码
            </label>
            <input
              v-model="password"
              type="password"
              placeholder="请输入密码"
              class="w-full px-3 sm:px-4 py-2.5 sm:py-3 text-sm sm:text-base border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>

          <div v-if="!isLogin">
            <label class="block text-sm font-medium text-slate-700 mb-1.5 sm:mb-2">
              确认密码
            </label>
            <input
              v-model="confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              class="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>

          <div v-if="isLogin" class="flex items-center justify-end">
            <a href="#" class="text-sm text-blue-600 hover:text-blue-700">忘记密码？</a>
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <svg v-if="isLoading" class="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span v-if="isLoading">处理中...</span>
            <span v-else>{{ isLogin ? '登录' : '注册' }}</span>
          </button>
        </form>

        <div class="mt-6 text-center">
          <p class="text-sm text-slate-600">
            {{ isLogin ? '还没有账户？' : '已有账户？' }}
            <button
              @click="toggleMode"
              class="text-blue-600 hover:text-blue-700 font-medium ml-1"
            >
              {{ isLogin ? '立即注册' : '立即登录' }}
            </button>
          </p>
        </div>

        <div class="mt-6 pt-6 border-t border-slate-200">
          <p class="text-xs text-slate-500 text-center mb-4">其他登录方式</p>
          <div class="flex gap-4 justify-center">
            <button class="w-12 h-12 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors flex items-center justify-center">
              <span class="text-xl">🔵</span>
            </button>
            <button class="w-12 h-12 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors flex items-center justify-center">
              <span class="text-xl">🟢</span>
            </button>
            <button class="w-12 h-12 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors flex items-center justify-center">
              <span class="text-xl">🟡</span>
            </button>
          </div>
        </div>
      </div>

      <p class="text-center text-sm text-slate-500 mt-6">
        <router-link to="/" class="text-blue-600 hover:text-blue-700">返回首页</router-link>
      </p>
    </div>
  </div>
</template>
