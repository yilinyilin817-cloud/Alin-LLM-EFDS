<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiService from '@/services/api'
import MobileNav from '@/components/MobileNav.vue'

interface Device {
  id: number
  name: string
  model: string
  manufacturer: string
  category: string
  location: string
  status: string
  installation_date: string
  description: string
  created_at: string
  updated_at: string
}

interface MaintenanceRecord {
  id: number
  device_id: number
  maintenance_type: string
  title: string
  content: string
  technician: string
  cost: number
  parts_replaced: string
  next_maintenance_date: string
  status: string
  created_at: string
}

const devices = ref<Device[]>([])
const loading = ref(false)
const searchQuery = ref('')
const filterCategory = ref('all')
const selectedDevice = ref<Device | null>(null)
const showAddModal = ref(false)
const showEditModal = ref(false)
const showMaintenanceModal = ref(false)
const showAddMaintenanceModal = ref(false)
const isSubmitting = ref(false)
const submitSuccess = ref(false)
const maintenanceRecords = ref<MaintenanceRecord[]>([])
const maintenanceLoading = ref(false)

const editForm = ref({
  name: '',
  model: '',
  manufacturer: '',
  category: '',
  location: '',
  status: '',
  description: '',
})

const newDevice = ref({
  name: '',
  model: '',
  manufacturer: '',
  category: '',
  location: '',
  installation_date: '',
  description: '',
})

const newMaintenance = ref({
  maintenance_type: 'routine',
  title: '',
  content: '',
  technician: '',
  cost: 0,
  parts_replaced: '',
  next_maintenance_date: '',
})

const deviceCategories = [
  '电动机', '液压设备', '控制系统', '电气传动', '空压机',
  '暖通设备', '传感器', '传动设备', '检测设备', '其他',
]

const maintenanceTypes = [
  { value: 'routine', label: '例行保养' },
  { value: 'repair', label: '故障维修' },
  { value: 'inspection', label: '定期检查' },
  { value: 'upgrade', label: '升级改造' },
  { value: 'emergency', label: '紧急维修' },
]

const categories = computed(() => {
  const cats = new Set(devices.value.map(d => d.category))
  return ['all', ...Array.from(cats)]
})

const filteredDevices = computed(() => {
  return devices.value.filter(d => {
    const matchCategory = filterCategory.value === 'all' || d.category === filterCategory.value
    const matchSearch = d.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                       d.model.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                       d.manufacturer.toLowerCase().includes(searchQuery.value.toLowerCase())
    return matchCategory && matchSearch
  })
})

const stats = computed(() => ({
  total: devices.value.length,
  normal: devices.value.filter(d => d.status === 'normal').length,
  warning: devices.value.filter(d => d.status === 'warning').length,
  fault: devices.value.filter(d => d.status === 'fault').length,
}))

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    normal: 'bg-emerald-100 text-emerald-800',
    warning: 'bg-yellow-100 text-yellow-800',
    fault: 'bg-red-100 text-red-800',
  }
  return colors[status] || 'bg-gray-100 text-gray-800'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = { normal: '正常', warning: '预警', fault: '故障' }
  return texts[status] || status
}

const getStatusIcon = (status: string) => {
  const icons: Record<string, string> = { normal: '✓', warning: '!', fault: '✕' }
  return icons[status] || '?'
}

const getMaintenanceTypeLabel = (type: string) => {
  const found = maintenanceTypes.find(t => t.value === type)
  return found ? found.label : type
}

const getMaintenanceTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    routine: 'bg-blue-100 text-blue-800',
    repair: 'bg-red-100 text-red-800',
    inspection: 'bg-green-100 text-green-800',
    upgrade: 'bg-purple-100 text-purple-800',
    emergency: 'bg-orange-100 text-orange-800',
  }
  return colors[type] || 'bg-gray-100 text-gray-800'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const fetchDevices = async () => {
  loading.value = true
  const res = await apiService.getDevices()
  if (res.data) {
    devices.value = res.data
  }
  loading.value = false
}

const openDeviceDetail = async (device: Device) => {
  const res = await apiService.getDevice(device.id)
  if (res.data) {
    selectedDevice.value = res.data
  } else {
    selectedDevice.value = device
  }
}

const closeDetail = () => {
  selectedDevice.value = null
}

const openAddModal = () => {
  resetAddForm()
  showAddModal.value = true
}

const closeAddModal = () => {
  showAddModal.value = false
  resetAddForm()
}

const resetAddForm = () => {
  newDevice.value = {
    name: '', model: '', manufacturer: '', category: '',
    location: '', installation_date: '', description: '',
  }
  submitSuccess.value = false
}

const addDevice = async () => {
  if (!newDevice.value.name || !newDevice.value.model || !newDevice.value.category) {
    alert('请填写必填字段：设备名称、设备型号、设备类别')
    return
  }
  isSubmitting.value = true
  const res = await apiService.createDevice(newDevice.value)
  if (res.data) {
    submitSuccess.value = true
    await fetchDevices()
    setTimeout(() => closeAddModal(), 1500)
  } else {
    alert(res.error || '添加失败')
  }
  isSubmitting.value = false
}

const openEditModal = (device: Device) => {
  editForm.value = {
    name: device.name,
    model: device.model,
    manufacturer: device.manufacturer || '',
    category: device.category || '',
    location: device.location || '',
    status: device.status,
    description: device.description || '',
  }
  showEditModal.value = true
}

const closeEditModal = () => {
  showEditModal.value = false
}

const updateDevice = async () => {
  if (!selectedDevice.value) return
  isSubmitting.value = true
  const res = await apiService.updateDevice(selectedDevice.value.id, editForm.value)
  if (res.data) {
    selectedDevice.value = res.data
    await fetchDevices()
    closeEditModal()
  } else {
    alert(res.error || '更新失败')
  }
  isSubmitting.value = false
}

const deleteDevice = async (deviceId: number) => {
  if (!confirm('确定要删除该设备吗？')) return
  const res = await apiService.deleteDevice(deviceId)
  if (!res.error) {
    selectedDevice.value = null
    await fetchDevices()
  } else {
    alert(res.error || '删除失败')
  }
}

const openMaintenanceModal = async (device: Device) => {
  selectedDevice.value = device
  showMaintenanceModal.value = true
  maintenanceLoading.value = true
  const res = await apiService.getMaintenanceRecords(device.id)
  if (res.data) {
    maintenanceRecords.value = res.data
  }
  maintenanceLoading.value = false
}

const closeMaintenanceModal = () => {
  showMaintenanceModal.value = false
  maintenanceRecords.value = []
}

const openAddMaintenanceModal = () => {
  newMaintenance.value = {
    maintenance_type: 'routine',
    title: '',
    content: '',
    technician: '',
    cost: 0,
    parts_replaced: '',
    next_maintenance_date: '',
  }
  showAddMaintenanceModal.value = true
}

const closeAddMaintenanceModal = () => {
  showAddMaintenanceModal.value = false
}

const addMaintenanceRecord = async () => {
  if (!selectedDevice.value || !newMaintenance.value.title) {
    alert('请填写维护标题')
    return
  }
  isSubmitting.value = true
  const res = await apiService.createMaintenanceRecord({
    device_id: selectedDevice.value.id,
    ...newMaintenance.value,
  })
  if (res.data) {
    const refreshRes = await apiService.getMaintenanceRecords(selectedDevice.value.id)
    if (refreshRes.data) {
      maintenanceRecords.value = refreshRes.data
    }
    closeAddMaintenanceModal()
  } else {
    alert(res.error || '添加失败')
  }
  isSubmitting.value = false
}

const deleteMaintenanceRecord = async (recordId: number) => {
  if (!confirm('确定要删除该维护记录吗？')) return
  const res = await apiService.deleteMaintenanceRecord(recordId)
  if (!res.error && selectedDevice.value) {
    const refreshRes = await apiService.getMaintenanceRecords(selectedDevice.value.id)
    if (refreshRes.data) {
      maintenanceRecords.value = refreshRes.data
    }
  }
}

onMounted(() => {
  fetchDevices()
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
                <p class="text-xs text-slate-500">设备档案</p>
              </div>
            </router-link>
          </div>
          <nav class="hidden md:flex items-center gap-6">
            <router-link to="/" class="text-sm font-medium text-slate-600 hover:text-blue-600">首页</router-link>
            <router-link to="/devices" class="text-sm font-medium text-blue-600">设备档案</router-link>
            <router-link to="/diagnosis" class="text-sm font-medium text-slate-600 hover:text-blue-600">智能诊断</router-link>
            <router-link to="/knowledge" class="text-sm font-medium text-slate-600 hover:text-blue-600">知识库</router-link>
            <router-link to="/chat" class="text-sm font-medium text-slate-600 hover:text-blue-600">智能问答</router-link>
          </nav>

          <MobileNav />
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
      <div class="mb-4 sm:mb-6">
        <h2 class="text-xl sm:text-2xl font-bold text-slate-900">设备档案管理</h2>
        <p class="text-xs sm:text-sm text-slate-600 mt-1">管理设备基本信息，运行状态和维护记录</p>
      </div>

      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-4 sm:mb-6">
        <div class="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <span class="text-blue-600 text-xl">🏭</span>
            </div>
            <div>
              <p class="text-2xl font-bold text-slate-900">{{ stats.total }}</p>
              <p class="text-xs text-slate-500">设备总数</p>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
              <span class="text-emerald-600 text-xl">✓</span>
            </div>
            <div>
              <p class="text-2xl font-bold text-slate-900">{{ stats.normal }}</p>
              <p class="text-xs text-slate-500">正常运行</p>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
              <span class="text-yellow-600 text-xl">!</span>
            </div>
            <div>
              <p class="text-2xl font-bold text-slate-900">{{ stats.warning }}</p>
              <p class="text-xs text-slate-500">预警设备</p>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <span class="text-red-600 text-xl">✕</span>
            </div>
            <div>
              <p class="text-2xl font-bold text-slate-900">{{ stats.fault }}</p>
              <p class="text-xs text-slate-500">故障设备</p>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl p-6 border border-slate-200 shadow-sm mb-6">
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex-1 min-w-[200px]">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索设备名称、型号、厂商..."
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm text-slate-600">类别:</span>
            <select
              v-model="filterCategory"
              class="px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option v-for="cat in categories" :key="cat" :value="cat">
                {{ cat === 'all' ? '全部类别' : cat }}
              </option>
            </select>
          </div>
          <button
            @click="openAddModal"
            class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <span>+</span> 添加设备
          </button>
        </div>
      </div>

      <div v-if="loading" class="text-center py-12">
        <div class="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
        <p class="text-slate-500 mt-3">加载中...</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="device in filteredDevices"
          :key="device.id"
          @click="openDeviceDetail(device)"
          class="bg-white rounded-xl p-5 border border-slate-200 shadow-sm hover:shadow-lg hover:border-blue-300 transition-all cursor-pointer"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center">
                <span class="text-2xl">⚙️</span>
              </div>
              <div>
                <h3 class="font-semibold text-slate-900">{{ device.name }}</h3>
                <p class="text-xs text-slate-500">{{ device.model }}</p>
              </div>
            </div>
            <span :class="['px-2 py-1 text-xs font-medium rounded-full flex items-center gap-1', getStatusColor(device.status)]">
              {{ getStatusIcon(device.status) }} {{ getStatusText(device.status) }}
            </span>
          </div>
          <div class="space-y-2 text-sm">
            <div class="flex items-center gap-2 text-slate-600">
              <span class="text-slate-400">厂商:</span>
              <span>{{ device.manufacturer || '-' }}</span>
            </div>
            <div class="flex items-center gap-2 text-slate-600">
              <span class="text-slate-400">位置:</span>
              <span>{{ device.location || '-' }}</span>
            </div>
            <div class="flex items-center gap-2 text-slate-600">
              <span class="text-slate-400">类别:</span>
              <span class="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">{{ device.category }}</span>
            </div>
          </div>
          <div class="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
            <p class="text-xs text-slate-500">安装日期: {{ formatDate(device.installation_date) }}</p>
            <button
              @click.stop="openMaintenanceModal(device)"
              class="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              维护记录
            </button>
          </div>
        </div>
      </div>

      <div v-if="!loading && filteredDevices.length === 0" class="text-center py-12 bg-white rounded-xl border border-slate-200">
        <span class="text-4xl mb-4 block">📭</span>
        <p class="text-slate-500">没有找到匹配的设备</p>
      </div>
    </main>

    <div
      v-if="selectedDevice && !showMaintenanceModal && !showEditModal"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="closeDetail"
    >
      <div class="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-slate-900">{{ selectedDevice.name }}</h3>
          <button @click="closeDetail" class="text-slate-400 hover:text-slate-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-6 space-y-6">
          <div class="flex items-center gap-4 mb-4">
            <div class="w-16 h-16 bg-slate-100 rounded-xl flex items-center justify-center">
              <span class="text-3xl">⚙️</span>
            </div>
            <div>
              <p class="text-xl font-semibold text-slate-900">{{ selectedDevice.model }}</p>
              <p class="text-sm text-slate-500">{{ selectedDevice.manufacturer || '-' }}</p>
              <span :class="['mt-2 px-2 py-1 text-xs font-medium rounded-full inline-flex items-center gap-1', getStatusColor(selectedDevice.status)]">
                {{ getStatusIcon(selectedDevice.status) }} {{ getStatusText(selectedDevice.status) }}
              </span>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-slate-500 mb-1">设备类别</p>
              <p class="text-sm font-medium text-slate-900">{{ selectedDevice.category }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-500 mb-1">安装位置</p>
              <p class="text-sm font-medium text-slate-900">{{ selectedDevice.location || '-' }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-500 mb-1">安装日期</p>
              <p class="text-sm font-medium text-slate-900">{{ formatDate(selectedDevice.installation_date) }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-500 mb-1">设备编号</p>
              <p class="text-sm font-medium text-slate-900">DEV-{{ String(selectedDevice.id).padStart(4, '0') }}</p>
            </div>
          </div>
          <div>
            <h4 class="text-sm font-medium text-slate-700 mb-2">设备描述</h4>
            <p class="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg">{{ selectedDevice.description || '暂无描述' }}</p>
          </div>
          <div class="flex gap-3 pt-4 border-t border-slate-200">
            <button
              @click="openEditModal(selectedDevice)"
              class="flex-1 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              编辑信息
            </button>
            <button
              @click="openMaintenanceModal(selectedDevice)"
              class="flex-1 px-4 py-2 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors"
            >
              查看维护记录
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="showEditModal"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="closeEditModal"
    >
      <div class="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
          <h3 class="text-lg font-semibold text-slate-900">编辑设备信息</h3>
          <button @click="closeEditModal" class="text-slate-400 hover:text-slate-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-6">
          <form @submit.prevent="updateDevice" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">设备名称 <span class="text-red-500">*</span></label>
                <input v-model="editForm.name" type="text" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">设备型号 <span class="text-red-500">*</span></label>
                <input v-model="editForm.model" type="text" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">设备类别</label>
                <select v-model="editForm.category" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option v-for="cat in deviceCategories" :key="cat" :value="cat">{{ cat }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">生产厂商</label>
                <input v-model="editForm.manufacturer" type="text" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">安装位置</label>
                <input v-model="editForm.location" type="text" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">运行状态</label>
                <select v-model="editForm.status" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option value="normal">正常</option>
                  <option value="warning">预警</option>
                  <option value="fault">故障</option>
                </select>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">设备描述</label>
              <textarea v-model="editForm.description" rows="4" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"></textarea>
            </div>
            <div class="flex gap-3 pt-4 border-t border-slate-200">
              <button type="button" @click="closeEditModal" class="flex-1 px-4 py-2.5 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors">取消</button>
              <button type="submit" :disabled="isSubmitting" class="flex-1 px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
                <svg v-if="isSubmitting" class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>{{ isSubmitting ? '保存中...' : '保存修改' }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div
      v-if="showMaintenanceModal"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="closeMaintenanceModal"
    >
      <div class="bg-white rounded-xl max-w-3xl w-full max-h-[85vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h3 class="text-lg font-semibold text-slate-900">维护记录</h3>
            <p class="text-xs text-slate-500 mt-1">{{ selectedDevice?.name }} - {{ selectedDevice?.model }}</p>
          </div>
          <div class="flex items-center gap-3">
            <button
              @click="openAddMaintenanceModal"
              class="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-1"
            >
              <span>+</span> 新增记录
            </button>
            <button @click="closeMaintenanceModal" class="text-slate-400 hover:text-slate-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        <div class="p-6">
          <div v-if="maintenanceLoading" class="text-center py-8">
            <div class="animate-spin h-6 w-6 border-4 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
            <p class="text-slate-500 mt-2 text-sm">加载中...</p>
          </div>
          <div v-else-if="maintenanceRecords.length === 0" class="text-center py-8">
            <span class="text-3xl block mb-3">📋</span>
            <p class="text-slate-500">暂无维护记录</p>
            <button @click="openAddMaintenanceModal" class="mt-3 text-blue-600 text-sm hover:underline">添加第一条记录</button>
          </div>
          <div v-else class="space-y-4">
            <div
              v-for="record in maintenanceRecords"
              :key="record.id"
              class="border border-slate-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
            >
              <div class="flex items-start justify-between mb-3">
                <div class="flex items-center gap-3">
                  <span :class="['px-2 py-1 text-xs font-medium rounded-full', getMaintenanceTypeColor(record.maintenance_type)]">
                    {{ getMaintenanceTypeLabel(record.maintenance_type) }}
                  </span>
                  <h4 class="font-medium text-slate-900">{{ record.title }}</h4>
                </div>
                <button @click="deleteMaintenanceRecord(record.id)" class="text-slate-400 hover:text-red-500 transition-colors">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
              <p v-if="record.content" class="text-sm text-slate-600 mb-3">{{ record.content }}</p>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div>
                  <p class="text-slate-400">维护人员</p>
                  <p class="text-slate-700 font-medium">{{ record.technician || '-' }}</p>
                </div>
                <div>
                  <p class="text-slate-400">维护费用</p>
                  <p class="text-slate-700 font-medium">¥{{ record.cost || 0 }}</p>
                </div>
                <div>
                  <p class="text-slate-400">维护日期</p>
                  <p class="text-slate-700 font-medium">{{ formatDate(record.created_at) }}</p>
                </div>
                <div>
                  <p class="text-slate-400">下次维护</p>
                  <p class="text-slate-700 font-medium">{{ formatDate(record.next_maintenance_date) }}</p>
                </div>
              </div>
              <div v-if="record.parts_replaced" class="mt-3 pt-3 border-t border-slate-100">
                <p class="text-xs text-slate-400 mb-1">更换部件</p>
                <p class="text-sm text-slate-600">{{ record.parts_replaced }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="showAddMaintenanceModal"
      class="fixed inset-0 bg-black/60 z-[60] flex items-center justify-center p-4"
      @click.self="closeAddMaintenanceModal"
    >
      <div class="bg-white rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
          <h3 class="text-lg font-semibold text-slate-900">新增维护记录</h3>
          <button @click="closeAddMaintenanceModal" class="text-slate-400 hover:text-slate-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-6">
          <form @submit.prevent="addMaintenanceRecord" class="space-y-5">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">维护类型 <span class="text-red-500">*</span></label>
              <select v-model="newMaintenance.maintenance_type" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option v-for="t in maintenanceTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">维护标题 <span class="text-red-500">*</span></label>
              <input v-model="newMaintenance.title" type="text" placeholder="简要描述本次维护" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">维护详情</label>
              <textarea v-model="newMaintenance.content" rows="3" placeholder="详细描述维护内容和过程..." class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"></textarea>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">维护人员</label>
                <input v-model="newMaintenance.technician" type="text" placeholder="维护人员姓名" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">维护费用 (元)</label>
                <input v-model.number="newMaintenance.cost" type="number" min="0" step="0.01" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">更换部件</label>
              <input v-model="newMaintenance.parts_replaced" type="text" placeholder="列出更换的部件名称" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">下次维护日期</label>
              <input v-model="newMaintenance.next_maintenance_date" type="date" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            </div>
            <div class="flex gap-3 pt-4 border-t border-slate-200">
              <button type="button" @click="closeAddMaintenanceModal" class="flex-1 px-4 py-2.5 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors">取消</button>
              <button type="submit" :disabled="isSubmitting" class="flex-1 px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50">
                {{ isSubmitting ? '提交中...' : '确认添加' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div
      v-if="showAddModal"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="closeAddModal"
    >
      <div class="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
          <h3 class="text-lg font-semibold text-slate-900">添加新设备</h3>
          <button @click="closeAddModal" class="text-slate-400 hover:text-slate-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-6">
          <div v-if="submitSuccess" class="text-center py-8">
            <div class="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p class="text-lg font-semibold text-slate-900">设备添加成功！</p>
            <p class="text-sm text-slate-500 mt-1">新设备已添加到系统中</p>
          </div>
          <form v-else @submit.prevent="addDevice" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">设备名称 <span class="text-red-500">*</span></label>
                <input v-model="newDevice.name" type="text" placeholder="请输入设备名称" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">设备型号 <span class="text-red-500">*</span></label>
                <input v-model="newDevice.model" type="text" placeholder="请输入设备型号" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">设备类别 <span class="text-red-500">*</span></label>
                <select v-model="newDevice.category" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required>
                  <option value="" disabled>请选择设备类别</option>
                  <option v-for="cat in deviceCategories" :key="cat" :value="cat">{{ cat }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">生产厂商</label>
                <input v-model="newDevice.manufacturer" type="text" placeholder="请输入生产厂商" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">安装位置</label>
                <input v-model="newDevice.location" type="text" placeholder="请输入安装位置" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">安装日期</label>
                <input v-model="newDevice.installation_date" type="date" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">设备描述</label>
              <textarea v-model="newDevice.description" rows="4" placeholder="请输入设备描述信息..." class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"></textarea>
            </div>
            <div class="flex items-center gap-2 text-sm text-slate-500 bg-slate-50 p-3 rounded-lg">
              <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>新添加的设备初始状态为"正常"</span>
            </div>
            <div class="flex gap-3 pt-4 border-t border-slate-200">
              <button type="button" @click="closeAddModal" class="flex-1 px-4 py-2.5 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors">取消</button>
              <button type="submit" :disabled="isSubmitting" class="flex-1 px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                <svg v-if="isSubmitting" class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>{{ isSubmitting ? '添加中...' : '确认添加' }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
