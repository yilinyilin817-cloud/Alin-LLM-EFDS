<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import apiService from '@/services/api'

const router = useRouter()
const { currentUser, logout } = useAuth()

const activeTab = ref('models')
const isLoading = ref(false)

const tabs = [
  { id: 'models', name: '模型配置', icon: '🤖' },
  { id: 'users', name: '用户管理', icon: '👥' },
  { id: 'settings', name: '系统设置', icon: '⚙️' },
  { id: 'logs', name: '操作日志', icon: '📋' },
]

const users = ref<any[]>([])
const logs = ref<any[]>([])
const systemSettings = ref({
  llm_model: 'gpt-3.5-turbo',
  embedding_model: 'shibing624/text2vec-base-chinese',
  rag_top_k: 5,
  similarity_threshold: 0.7,
  max_tokens: 2048,
  temperature: 0.7,
})

const modelProviders = ref<any[]>([])
const supportedProviders = ref<any>({ third_party: [], local: [] })
const showProviderModal = ref(false)
const editingProvider = ref<any>(null)
const providerForm = ref({
  name: '',
  provider_type: 'third_party',
  provider_name: '',
  api_base: '',
  api_key: '',
  model_name: '',
  temperature: 0.7,
  max_tokens: 2048,
  is_default: false,
  is_active: true,
})
const providerFilter = ref('all')
const testingProviderId = ref<number | null>(null)
const testResult = ref<{ success: boolean; message: string } | null>(null)

const filteredProviders = computed(() => {
  if (providerFilter.value === 'all') return modelProviders.value
  return modelProviders.value.filter((p: any) => p.provider_type === providerFilter.value)
})

const currentProviderOptions = computed(() => {
  if (providerForm.value.provider_type === 'third_party') {
    return supportedProviders.value.third_party || []
  }
  return supportedProviders.value.local || []
})

const showAddUserModal = ref(false)
const showEditUserModal = ref(false)
const showResetPasswordModal = ref(false)
const selectedUser = ref<any>(null)
const newUser = ref({ username: '', email: '', password: '' })
const newPassword = ref('')
const errorMessage = ref('')
const successMessage = ref('')

const fetchModelProviders = async () => {
  isLoading.value = true
  try {
    const result = await apiService.getModelProviders()
    if (result.data) {
      modelProviders.value = result.data
    }
  } finally {
    isLoading.value = false
  }
}

const fetchSupportedProviders = async () => {
  const result = await apiService.getSupportedProviders()
  if (result.data) {
    supportedProviders.value = result.data
  }
}

const openCreateProviderModal = () => {
  editingProvider.value = null
  providerForm.value = {
    name: '',
    provider_type: 'third_party',
    provider_name: '',
    api_base: '',
    api_key: '',
    model_name: '',
    temperature: 0.7,
    max_tokens: 2048,
    is_default: false,
    is_active: true,
  }
  showProviderModal.value = true
}

const openEditProviderModal = (provider: any) => {
  editingProvider.value = provider
  providerForm.value = {
    name: provider.name,
    provider_type: provider.provider_type,
    provider_name: provider.provider_name,
    api_base: provider.api_base,
    api_key: '',
    model_name: provider.model_name,
    temperature: provider.temperature,
    max_tokens: provider.max_tokens,
    is_default: provider.is_default,
    is_active: provider.is_active,
  }
  showProviderModal.value = true
}

const onProviderTypeChange = () => {
  providerForm.value.provider_name = ''
  providerForm.value.api_base = ''
}

const onProviderNameChange = () => {
  const option = currentProviderOptions.value.find((o: any) => o.name === providerForm.value.provider_name)
  if (option) {
    providerForm.value.api_base = option.default_base
  }
}

const handleSaveProvider = async () => {
  errorMessage.value = ''
  if (!providerForm.value.name || !providerForm.value.provider_name || !providerForm.value.api_base || !providerForm.value.model_name) {
    errorMessage.value = '请填写所有必填字段'
    return
  }

  const data: any = { ...providerForm.value }
  if (editingProvider.value && !data.api_key) {
    delete data.api_key
  }

  let result
  if (editingProvider.value) {
    result = await apiService.updateModelProvider(editingProvider.value.id, data)
  } else {
    result = await apiService.createModelProvider(data)
  }

  if (result.error) {
    errorMessage.value = result.error
  } else {
    successMessage.value = editingProvider.value ? '模型配置已更新' : '模型配置已创建'
    showProviderModal.value = false
    await fetchModelProviders()
    setTimeout(() => { successMessage.value = '' }, 3000)
  }
}

const handleDeleteProvider = async (providerId: number) => {
  if (!confirm('确定要删除该模型配置吗？')) return

  const result = await apiService.deleteModelProvider(providerId)
  if (result.error) {
    errorMessage.value = result.error
  } else {
    successMessage.value = '模型配置已删除'
    await fetchModelProviders()
    setTimeout(() => { successMessage.value = '' }, 3000)
  }
}

const handleToggleProvider = async (providerId: number) => {
  const result = await apiService.toggleModelProvider(providerId)
  if (result.error) {
    errorMessage.value = result.error
  } else {
    await fetchModelProviders()
  }
}

const handleSetDefault = async (providerId: number) => {
  const result = await apiService.setDefaultModelProvider(providerId)
  if (result.error) {
    errorMessage.value = result.error
  } else {
    successMessage.value = '已设置为默认模型'
    await fetchModelProviders()
    setTimeout(() => { successMessage.value = '' }, 3000)
  }
}

const handleTestProvider = async (provider: any) => {
  testingProviderId.value = provider.id
  testResult.value = null
  try {
    const result = await apiService.sendMessage(0, '你好，请简单介绍一下自己。', false, provider.id)
    if (result.error) {
      testResult.value = { success: false, message: result.error }
    } else {
      testResult.value = { success: true, message: '模型连接测试成功！' }
    }
  } catch (e: any) {
    testResult.value = { success: false, message: `测试失败: ${e.message}` }
  } finally {
    setTimeout(() => {
      testingProviderId.value = null
      testResult.value = null
    }, 5000)
  }
}

const fetchUsers = async () => {
  isLoading.value = true
  try {
    const result = await apiService.getUsers()
    if (result.data) {
      users.value = result.data
    }
  } finally {
    isLoading.value = false
  }
}

const fetchLogs = async () => {
  isLoading.value = true
  try {
    const result = await apiService.getOperationLogs()
    if (result.data) {
      logs.value = result.data
    }
  } finally {
    isLoading.value = false
  }
}

const fetchSettings = async () => {
  isLoading.value = true
  try {
    const result = await apiService.getSystemSettings()
    if (result.data) {
      systemSettings.value = result.data
    }
  } finally {
    isLoading.value = false
  }
}

const handleAddUser = async () => {
  errorMessage.value = ''
  if (!newUser.value.username || !newUser.value.email || !newUser.value.password) {
    errorMessage.value = '请填写所有必填字段'
    return
  }
  if (newUser.value.password.length < 6) {
    errorMessage.value = '密码长度至少6位'
    return
  }

  const result = await apiService.register(newUser.value.username, newUser.value.email, newUser.value.password)
  if (result.error) {
    errorMessage.value = result.error
  } else {
    successMessage.value = '用户添加成功'
    showAddUserModal.value = false
    newUser.value = { username: '', email: '', password: '' }
    await fetchUsers()
    setTimeout(() => { successMessage.value = '' }, 3000)
  }
}

const handleEditUser = async () => {
  if (!selectedUser.value) return
  errorMessage.value = ''

  const result = await apiService.updateUser(selectedUser.value.id, {
    email: selectedUser.value.email,
    role: selectedUser.value.role,
    is_active: selectedUser.value.is_active,
  })
  if (result.error) {
    errorMessage.value = result.error
  } else {
    successMessage.value = '用户信息已更新'
    showEditUserModal.value = false
    await fetchUsers()
    setTimeout(() => { successMessage.value = '' }, 3000)
  }
}

const handleDeleteUser = async (userId: number) => {
  if (!confirm('确定要删除该用户吗？此操作不可撤销。')) return

  const result = await apiService.deleteUser(userId)
  if (result.error) {
    errorMessage.value = result.error
  } else {
    successMessage.value = '用户已删除'
    await fetchUsers()
    setTimeout(() => { successMessage.value = '' }, 3000)
  }
}

const handleResetPassword = async () => {
  if (!selectedUser.value || !newPassword.value) return
  if (newPassword.value.length < 6) {
    errorMessage.value = '密码长度至少6位'
    return
  }

  const result = await apiService.updateUserPassword(selectedUser.value.id, newPassword.value)
  if (result.error) {
    errorMessage.value = result.error
  } else {
    successMessage.value = '密码已重置'
    showResetPasswordModal.value = false
    newPassword.value = ''
    setTimeout(() => { successMessage.value = '' }, 3000)
  }
}

const handleSaveSettings = async () => {
  errorMessage.value = ''
  const result = await apiService.updateSystemSettings(systemSettings.value)
  if (result.error) {
    errorMessage.value = result.error
  } else {
    successMessage.value = '设置已保存'
    setTimeout(() => { successMessage.value = '' }, 3000)
  }
}

const handleResetSettings = async () => {
  systemSettings.value = {
    llm_model: 'gpt-3.5-turbo',
    embedding_model: 'shibing624/text2vec-base-chinese',
    rag_top_k: 5,
    similarity_threshold: 0.7,
    max_tokens: 2048,
    temperature: 0.7,
  }
}

const openEditModal = (user: any) => {
  selectedUser.value = { ...user }
  showEditUserModal.value = true
}

const openResetPasswordModal = (user: any) => {
  selectedUser.value = user
  newPassword.value = ''
  showResetPasswordModal.value = true
}

const handleLogout = () => {
  logout()
  router.push('/login')
}

const getRoleColor = (role: string) => {
  return role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
}

const getStatusColor = (is_active: boolean) => {
  return is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-800'
}

const getProviderTypeLabel = (type: string) => {
  return type === 'third_party' ? '第三方服务' : '本地部署'
}

const getProviderTypeColor = (type: string) => {
  return type === 'third_party' ? 'bg-blue-100 text-blue-800' : 'bg-emerald-100 text-emerald-800'
}

const getProviderLabel = (name: string) => {
  const all = [...(supportedProviders.value.third_party || []), ...(supportedProviders.value.local || [])]
  const found = all.find((p: any) => p.name === name)
  return found ? found.label : name
}

onMounted(async () => {
  await fetchSupportedProviders()
  await fetchModelProviders()
  await fetchUsers()
  await fetchSettings()
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
    <header class="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <router-link to="/" class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                <span class="text-white text-xl">🔧</span>
              </div>
              <div>
                <h1 class="text-xl font-bold text-slate-900">LLM-EFDS</h1>
                <p class="text-xs text-slate-500">系统管理</p>
              </div>
            </router-link>
          </div>
          <nav class="hidden md:flex items-center gap-6">
            <router-link to="/" class="text-sm font-medium text-slate-600 hover:text-blue-600">首页</router-link>
            <router-link to="/diagnosis" class="text-sm font-medium text-slate-600 hover:text-blue-600">智能诊断</router-link>
            <router-link to="/knowledge" class="text-sm font-medium text-slate-600 hover:text-blue-600">知识库</router-link>
            <router-link to="/chat" class="text-sm font-medium text-slate-600 hover:text-blue-600">智能问答</router-link>
            <div class="flex items-center gap-3">
              <span class="text-sm text-slate-600">{{ currentUser?.username }}</span>
              <button
                @click="handleLogout"
                class="px-4 py-2 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors"
              >
                退出
              </button>
            </div>
          </nav>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-slate-900">系统管理</h2>
        <p class="text-sm text-slate-600 mt-1">管理模型配置、系统用户、参数设置和操作日志</p>
      </div>

      <div v-if="errorMessage" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
        <p class="text-sm text-red-600">{{ errorMessage }}</p>
      </div>

      <div v-if="successMessage" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
        <p class="text-sm text-green-600">{{ successMessage }}</p>
      </div>

      <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="border-b border-slate-200">
          <nav class="flex">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id; if (tab.id === 'logs') fetchLogs()"
              :class="[
                'px-6 py-4 text-sm font-medium border-b-2 transition-colors',
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
              ]"
            >
              <span class="mr-2">{{ tab.icon }}</span>
              {{ tab.name }}
            </button>
          </nav>
        </div>

        <div class="p-6">
          <!-- 模型配置 Tab -->
          <div v-if="activeTab === 'models'">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-lg font-semibold text-slate-900">模型提供商配置</h3>
                <p class="text-sm text-slate-500 mt-1">管理第三方API服务和本地部署模型，配置后可在智能问答和诊断中使用</p>
              </div>
              <button
                @click="openCreateProviderModal"
                class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                添加模型
              </button>
            </div>

            <div class="flex gap-2 mb-4">
              <button
                @click="providerFilter = 'all'"
                :class="['px-3 py-1.5 text-xs font-medium rounded-full transition-colors', providerFilter === 'all' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200']"
              >
                全部 ({{ modelProviders.length }})
              </button>
              <button
                @click="providerFilter = 'third_party'"
                :class="['px-3 py-1.5 text-xs font-medium rounded-full transition-colors', providerFilter === 'third_party' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200']"
              >
                第三方服务 ({{ modelProviders.filter((p: any) => p.provider_type === 'third_party').length }})
              </button>
              <button
                @click="providerFilter = 'local'"
                :class="['px-3 py-1.5 text-xs font-medium rounded-full transition-colors', providerFilter === 'local' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200']"
              >
                本地部署 ({{ modelProviders.filter((p: any) => p.provider_type === 'local').length }})
              </button>
            </div>

            <div v-if="isLoading" class="text-center py-8">
              <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p class="mt-2 text-sm text-slate-600">加载中...</p>
            </div>

            <div v-else-if="filteredProviders.length === 0" class="text-center py-12 bg-slate-50 rounded-xl">
              <div class="text-4xl mb-3">🤖</div>
              <p class="text-sm text-slate-500 mb-2">暂无模型配置</p>
              <p class="text-xs text-slate-400">点击上方"添加模型"按钮配置您的第一个AI模型</p>
            </div>

            <div v-else class="space-y-3">
              <div
                v-for="provider in filteredProviders"
                :key="provider.id"
                :class="[
                  'border rounded-xl p-4 transition-all hover:shadow-md',
                  provider.is_default ? 'border-blue-300 bg-blue-50/30' : 'border-slate-200 bg-white',
                  !provider.is_active ? 'opacity-60' : ''
                ]"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                      <h4 class="text-base font-semibold text-slate-900">{{ provider.name }}</h4>
                      <span v-if="provider.is_default" class="px-2 py-0.5 text-xs font-medium bg-blue-600 text-white rounded-full">默认</span>
                      <span :class="['px-2 py-0.5 text-xs font-medium rounded-full', getProviderTypeColor(provider.provider_type)]">
                        {{ getProviderTypeLabel(provider.provider_type) }}
                      </span>
                      <span v-if="!provider.is_active" class="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">已禁用</span>
                    </div>
                    <div class="flex items-center gap-4 text-sm text-slate-500">
                      <span>服务商: {{ getProviderLabel(provider.provider_name) }}</span>
                      <span>模型: <code class="px-1.5 py-0.5 bg-slate-100 rounded text-xs">{{ provider.model_name }}</code></span>
                      <span>API: <code class="px-1.5 py-0.5 bg-slate-100 rounded text-xs">{{ provider.api_base }}</code></span>
                    </div>
                    <div class="flex items-center gap-4 mt-1 text-xs text-slate-400">
                      <span>Temperature: {{ provider.temperature }}</span>
                      <span>Max Tokens: {{ provider.max_tokens }}</span>
                      <span>API Key: {{ provider.api_key || '未设置' }}</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 ml-4 flex-shrink-0">
                    <button
                      @click="handleSetDefault(provider.id)"
                      :disabled="provider.is_default"
                      :class="[
                        'px-3 py-1.5 text-xs font-medium rounded-lg transition-colors',
                        provider.is_default ? 'bg-blue-100 text-blue-400 cursor-not-allowed' : 'bg-slate-100 text-slate-600 hover:bg-blue-50 hover:text-blue-600'
                      ]"
                    >
                      {{ provider.is_default ? '默认' : '设为默认' }}
                    </button>
                    <button
                      @click="handleToggleProvider(provider.id)"
                      :class="[
                        'px-3 py-1.5 text-xs font-medium rounded-lg transition-colors',
                        provider.is_active ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                      ]"
                    >
                      {{ provider.is_active ? '已启用' : '已禁用' }}
                    </button>
                    <button
                      @click="openEditProviderModal(provider)"
                      class="px-3 py-1.5 text-xs font-medium bg-slate-100 text-slate-600 rounded-lg hover:bg-blue-50 hover:text-blue-600 transition-colors"
                    >
                      编辑
                    </button>
                    <button
                      @click="handleDeleteProvider(provider.id)"
                      class="px-3 py-1.5 text-xs font-medium bg-slate-100 text-slate-600 rounded-lg hover:bg-red-50 hover:text-red-600 transition-colors"
                    >
                      删除
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 用户管理 Tab -->
          <div v-if="activeTab === 'users'">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-slate-900">用户列表</h3>
              <button
                @click="showAddUserModal = true"
                class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                添加用户
              </button>
            </div>

            <div v-if="isLoading" class="text-center py-8">
              <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p class="mt-2 text-sm text-slate-600">加载中...</p>
            </div>

            <div v-else class="overflow-x-auto">
              <table class="w-full">
                <thead class="bg-slate-50">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">用户名</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">邮箱</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">角色</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">状态</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">操作</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-200">
                  <tr v-for="user in users" :key="user.id" class="hover:bg-slate-50">
                    <td class="px-4 py-3 text-sm font-medium text-slate-900">{{ user.username }}</td>
                    <td class="px-4 py-3 text-sm text-slate-600">{{ user.email }}</td>
                    <td class="px-4 py-3">
                      <span :class="['px-2 py-1 text-xs font-medium rounded-full', getRoleColor(user.role)]">
                        {{ user.role === 'admin' ? '管理员' : '普通用户' }}
                      </span>
                    </td>
                    <td class="px-4 py-3">
                      <span :class="['px-2 py-1 text-xs font-medium rounded-full', getStatusColor(user.is_active)]">
                        {{ user.is_active ? '活跃' : '未激活' }}
                      </span>
                    </td>
                    <td class="px-4 py-3">
                      <button @click="openEditModal(user)" class="text-blue-600 hover:text-blue-800 text-sm mr-3">编辑</button>
                      <button @click="openResetPasswordModal(user)" class="text-orange-600 hover:text-orange-800 text-sm mr-3">重置密码</button>
                      <button v-if="user.id !== currentUser?.id" @click="handleDeleteUser(user.id)" class="text-red-600 hover:text-red-800 text-sm">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 系统设置 Tab -->
          <div v-if="activeTab === 'settings'">
            <h3 class="text-lg font-semibold text-slate-900 mb-4">RAG 参数配置</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">RAG检索数量 (TOP K)</label>
                <input v-model.number="systemSettings.rag_top_k" type="number" min="1" max="20" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">相似度阈值</label>
                <input v-model.number="systemSettings.similarity_threshold" type="number" min="0" max="1" step="0.1" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
            </div>
            <div class="mt-6 flex gap-3">
              <button @click="handleSaveSettings" class="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">保存配置</button>
              <button @click="handleResetSettings" class="px-6 py-2 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors">恢复默认</button>
            </div>
          </div>

          <!-- 操作日志 Tab -->
          <div v-if="activeTab === 'logs'">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-slate-900">操作日志</h3>
            </div>
            <div v-if="isLoading" class="text-center py-8">
              <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p class="mt-2 text-sm text-slate-600">加载中...</p>
            </div>
            <div v-else-if="logs.length === 0" class="text-center py-8">
              <p class="text-sm text-slate-500">暂无操作日志</p>
            </div>
            <div v-else class="overflow-x-auto">
              <table class="w-full">
                <thead class="bg-slate-50">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">用户</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">操作</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">详情</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">IP地址</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">时间</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-200">
                  <tr v-for="log in logs" :key="log.id" class="hover:bg-slate-50">
                    <td class="px-4 py-3 text-sm font-medium text-slate-900">{{ log.user }}</td>
                    <td class="px-4 py-3 text-sm text-slate-600">{{ log.action }}</td>
                    <td class="px-4 py-3 text-sm text-slate-500 max-w-xs truncate">{{ log.detail }}</td>
                    <td class="px-4 py-3 text-sm text-slate-600 font-mono">{{ log.ip }}</td>
                    <td class="px-4 py-3 text-sm text-slate-600">{{ log.time }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 添加/编辑模型配置弹窗 -->
    <div v-if="showProviderModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <h3 class="text-lg font-semibold text-slate-900 mb-4">{{ editingProvider ? '编辑模型配置' : '添加模型配置' }}</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">配置名称 <span class="text-red-500">*</span></label>
              <input v-model="providerForm.name" type="text" class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm" placeholder="如: DeepSeek V3 生产环境" />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">接入类型 <span class="text-red-500">*</span></label>
              <div class="flex gap-3">
                <button
                  @click="providerForm.provider_type = 'third_party'; onProviderTypeChange()"
                  :class="['flex-1 px-4 py-2.5 text-sm font-medium rounded-lg border-2 transition-all', providerForm.provider_type === 'third_party' ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 text-slate-600 hover:border-slate-300']"
                >
                  🌐 第三方服务商
                </button>
                <button
                  @click="providerForm.provider_type = 'local'; onProviderTypeChange()"
                  :class="['flex-1 px-4 py-2.5 text-sm font-medium rounded-lg border-2 transition-all', providerForm.provider_type === 'local' ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-slate-200 text-slate-600 hover:border-slate-300']"
                >
                  🖥️ 本地部署
                </button>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">服务提供商 <span class="text-red-500">*</span></label>
              <select v-model="providerForm.provider_name" @change="onProviderNameChange" class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm">
                <option value="">请选择</option>
                <option v-for="opt in currentProviderOptions" :key="opt.name" :value="opt.name">{{ opt.label }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">API Base URL <span class="text-red-500">*</span></label>
              <input v-model="providerForm.api_base" type="text" class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm font-mono" placeholder="https://api.example.com/v1" />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">API Key</label>
              <input v-model="providerForm.api_key" type="password" class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm" :placeholder="editingProvider ? '留空则不修改' : '请输入API Key（本地模型可留空）'" />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1.5">模型名称 <span class="text-red-500">*</span></label>
              <input v-model="providerForm.model_name" type="text" class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm font-mono" placeholder="如: deepseek-chat, qwen-plus, llama3" />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1.5">Temperature</label>
                <input v-model.number="providerForm.temperature" type="number" min="0" max="2" step="0.1" class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1.5">Max Tokens</label>
                <input v-model.number="providerForm.max_tokens" type="number" min="100" max="32000" class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm" />
              </div>
            </div>
            <div class="flex items-center gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="providerForm.is_default" class="w-4 h-4 text-blue-600 rounded" />
                <span class="text-sm text-slate-700">设为默认模型</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="providerForm.is_active" class="w-4 h-4 text-blue-600 rounded" />
                <span class="text-sm text-slate-700">启用</span>
              </label>
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-6 pt-4 border-t border-slate-100">
            <button @click="showProviderModal = false" class="px-4 py-2 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200">取消</button>
            <button @click="handleSaveProvider" class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700">{{ editingProvider ? '保存修改' : '创建配置' }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加用户弹窗 -->
    <div v-if="showAddUserModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold text-slate-900 mb-4">添加用户</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">用户名</label>
            <input v-model="newUser.username" type="text" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="请输入用户名" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">邮箱</label>
            <input v-model="newUser.email" type="email" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="请输入邮箱" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">密码</label>
            <input v-model="newUser.password" type="password" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="请输入密码（至少6位）" />
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showAddUserModal = false" class="px-4 py-2 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200">取消</button>
          <button @click="handleAddUser" class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700">添加</button>
        </div>
      </div>
    </div>

    <!-- 编辑用户弹窗 -->
    <div v-if="showEditUserModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold text-slate-900 mb-4">编辑用户</h3>
        <div v-if="selectedUser" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">用户名</label>
            <input :value="selectedUser.username" type="text" disabled class="w-full px-4 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-500" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">邮箱</label>
            <input v-model="selectedUser.email" type="email" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">角色</label>
            <select v-model="selectedUser.role" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">状态</label>
            <select v-model="selectedUser.is_active" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
              <option :value="true">活跃</option>
              <option :value="false">未激活</option>
            </select>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showEditUserModal = false" class="px-4 py-2 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200">取消</button>
          <button @click="handleEditUser" class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700">保存</button>
        </div>
      </div>
    </div>

    <!-- 重置密码弹窗 -->
    <div v-if="showResetPasswordModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold text-slate-900 mb-4">重置密码</h3>
        <p class="text-sm text-slate-600 mb-4">为用户 <strong>{{ selectedUser?.username }}</strong> 设置新密码</p>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">新密码</label>
          <input v-model="newPassword" type="password" class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="请输入新密码（至少6位）" />
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showResetPasswordModal = false" class="px-4 py-2 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200">取消</button>
          <button @click="handleResetPassword" class="px-4 py-2 bg-orange-600 text-white text-sm font-medium rounded-lg hover:bg-orange-700">重置</button>
        </div>
      </div>
    </div>
  </div>
</template>
