<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiService from '@/services/api'

interface Issue {
  id: number
  device_id: number | null
  title: string
  description: string
  issue_type: string
  severity: string
  priority: string
  status: string
  reporter_name: string
  reporter_department: string | null
  assignee_name: string | null
  assignee_department: string | null
  location: string | null
  progress_percent: number
  due_date: string | null
  resolved_at: string | null
  created_at: string
  progress_logs: ProgressLog[]
}

interface ProgressLog {
  id: number
  issue_id: number
  user_name: string
  user_department: string | null
  progress_note: string
  progress_percent: number | null
  status: string | null
  action_taken: string | null
  hours_spent: number
  created_at: string
}

interface Device {
  id: number
  name: string
  model: string
}

interface DepartmentStats {
  department: string
  total: number
  open: number
  in_progress: number
  resolved: number
  avg_progress: number
}

const issues = ref<Issue[]>([])
const devices = ref<Device[]>([])
const departments = ref<string[]>([])
const departmentStats = ref<DepartmentStats[]>([])
const issuesByDepartment = ref<Record<string, any[]>>({})
const loading = ref(false)
const filterStatus = ref('all')
const filterSeverity = ref('all')
const filterDepartment = ref('all')
const searchQuery = ref('')
const selectedIssue = ref<Issue | null>(null)
const showCreateModal = ref(false)
const showProgressModal = ref(false)
const showDepartmentView = ref(false)
const isSubmitting = ref(false)
const submitSuccess = ref(false)
const activeTab = ref<'list' | 'department'>('list')

const newIssue = ref({
  device_id: null as number | null,
  title: '',
  description: '',
  issue_type: 'equipment',
  severity: 'medium',
  priority: 'normal',
  reporter_name: '',
  reporter_department: '',
  assignee_name: '',
  assignee_department: '',
  location: '',
  due_date: '',
})

const newProgress = ref({
  user_name: '',
  user_department: '',
  progress_note: '',
  progress_percent: 0,
  status: '',
  action_taken: '',
  hours_spent: 0,
})

const issueTypes = [
  { value: 'equipment', label: '设备故障' },
  { value: 'process', label: '工艺问题' },
  { value: 'safety', label: '安全隐患' },
  { value: 'quality', label: '质量问题' },
  { value: 'environment', label: '环境问题' },
  { value: 'other', label: '其他' },
]

const severityLevels = [
  { value: 'critical', label: '紧急', color: 'bg-red-100 text-red-800 border-red-200' },
  { value: 'high', label: '高', color: 'bg-orange-100 text-orange-800 border-orange-200' },
  { value: 'medium', label: '中', color: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
  { value: 'low', label: '低', color: 'bg-green-100 text-green-800 border-green-200' },
]

const priorityLevels = [
  { value: 'urgent', label: '紧急' },
  { value: 'high', label: '高' },
  { value: 'normal', label: '普通' },
  { value: 'low', label: '低' },
]

const statusOptions = [
  { value: 'open', label: '待处理', color: 'bg-blue-100 text-blue-800' },
  { value: 'in_progress', label: '处理中', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'resolved', label: '已解决', color: 'bg-emerald-100 text-emerald-800' },
  { value: 'closed', label: '已关闭', color: 'bg-gray-100 text-gray-800' },
]

const filteredIssues = computed(() => {
  return issues.value.filter(i => {
    const matchStatus = filterStatus.value === 'all' || i.status === filterStatus.value
    const matchSeverity = filterSeverity.value === 'all' || i.severity === filterSeverity.value
    const matchDepartment = filterDepartment.value === 'all' ||
      i.reporter_department === filterDepartment.value ||
      i.assignee_department === filterDepartment.value
    const matchSearch = i.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                       i.reporter_name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                       (i.assignee_name && i.assignee_name.toLowerCase().includes(searchQuery.value.toLowerCase()))
    return matchStatus && matchSeverity && matchDepartment && matchSearch
  })
})

const stats = computed(() => ({
  total: issues.value.length,
  open: issues.value.filter(i => i.status === 'open').length,
  in_progress: issues.value.filter(i => i.status === 'in_progress').length,
  resolved: issues.value.filter(i => i.status === 'resolved').length,
  critical: issues.value.filter(i => i.severity === 'critical' && i.status !== 'resolved').length,
  overdue: issues.value.filter(i => i.due_date && new Date(i.due_date) < new Date() && i.status !== 'resolved').length,
}))

const getSeverityColor = (severity: string) => {
  const found = severityLevels.find(s => s.value === severity)
  return found ? found.color : 'bg-gray-100 text-gray-800'
}

const getSeverityLabel = (severity: string) => {
  const found = severityLevels.find(s => s.value === severity)
  return found ? found.label : severity
}

const getStatusColor = (status: string) => {
  const found = statusOptions.find(s => s.value === status)
  return found ? found.color : 'bg-gray-100 text-gray-800'
}

const getStatusLabel = (status: string) => {
  const found = statusOptions.find(s => s.value === status)
  return found ? found.label : status
}

const getPriorityLabel = (priority: string) => {
  const found = priorityLevels.find(p => p.value === priority)
  return found ? found.label : priority
}

const getIssueTypeLabel = (type: string) => {
  const found = issueTypes.find(t => t.value === type)
  return found ? found.label : type
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatDateShort = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const isOverdue = (dueDate: string | null) => {
  if (!dueDate) return false
  return new Date(dueDate) < new Date()
}

const getDaysUntilDue = (dueDate: string | null) => {
  if (!dueDate) return null
  const days = Math.ceil((new Date(dueDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
  return days
}

const fetchIssues = async () => {
  loading.value = true
  const res = await apiService.getIssues()
  if (res.data) {
    issues.value = res.data
  }
  loading.value = false
}

const fetchDevices = async () => {
  const res = await apiService.getDevices(0, 200)
  if (res.data) {
    devices.value = res.data
  }
}

const fetchDepartments = async () => {
  const res = await apiService.getDepartments()
  if (res.data) {
    departments.value = res.data
  }
}

const fetchDepartmentStats = async () => {
  const res = await apiService.getDepartmentStats()
  if (res.data) {
    departmentStats.value = res.data
  }
}

const fetchIssuesByDepartment = async () => {
  const res = await apiService.getIssuesByDepartment()
  if (res.data) {
    issuesByDepartment.value = res.data
  }
}

const openCreateModal = () => {
  resetCreateForm()
  showCreateModal.value = true
}

const closeCreateModal = () => {
  showCreateModal.value = false
  resetCreateForm()
}

const resetCreateForm = () => {
  newIssue.value = {
    device_id: null,
    title: '',
    description: '',
    issue_type: 'equipment',
    severity: 'medium',
    priority: 'normal',
    reporter_name: '',
    reporter_department: '',
    assignee_name: '',
    assignee_department: '',
    location: '',
    due_date: '',
  }
  submitSuccess.value = false
}

const createIssue = async () => {
  if (!newIssue.value.title || !newIssue.value.description || !newIssue.value.reporter_name) {
    alert('请填写必填字段：问题标题、问题描述、上报人')
    return
  }
  isSubmitting.value = true
  const res = await apiService.createIssue(newIssue.value)
  if (res.data) {
    submitSuccess.value = true
    await fetchIssues()
    await fetchDepartments()
    await fetchDepartmentStats()
    setTimeout(() => closeCreateModal(), 1500)
  } else {
    alert(res.error || '提交失败')
  }
  isSubmitting.value = false
}

const openIssueDetail = async (issue: Issue) => {
  const res = await apiService.getIssue(issue.id)
  if (res.data) {
    selectedIssue.value = res.data
  } else {
    selectedIssue.value = issue
  }
}

const closeIssueDetail = () => {
  selectedIssue.value = null
}

const openProgressModal = (issue: Issue) => {
  selectedIssue.value = issue
  newProgress.value = {
    user_name: '',
    user_department: '',
    progress_note: '',
    progress_percent: issue.progress_percent,
    status: '',
    action_taken: '',
    hours_spent: 0,
  }
  showProgressModal.value = true
}

const closeProgressModal = () => {
  showProgressModal.value = false
}

const addProgress = async () => {
  if (!selectedIssue.value || !newProgress.value.user_name || !newProgress.value.progress_note) {
    alert('请填写处理人和进度说明')
    return
  }
  isSubmitting.value = true
  const progressData: any = {
    user_name: newProgress.value.user_name,
    user_department: newProgress.value.user_department,
    progress_note: newProgress.value.progress_note,
    action_taken: newProgress.value.action_taken,
    hours_spent: newProgress.value.hours_spent,
  }
  if (newProgress.value.progress_percent > 0) {
    progressData.progress_percent = newProgress.value.progress_percent
  }
  if (newProgress.value.status) {
    progressData.status = newProgress.value.status
  }
  const res = await apiService.addIssueProgress(selectedIssue.value.id, progressData)
  if (res.data) {
    const issueRes = await apiService.getIssue(selectedIssue.value.id)
    if (issueRes.data) {
      selectedIssue.value = issueRes.data
    }
    await fetchIssues()
    closeProgressModal()
  } else {
    alert(res.error || '提交失败')
  }
  isSubmitting.value = false
}

const updateIssueStatus = async (issueId: number, status: string) => {
  const res = await apiService.updateIssue(issueId, { status })
  if (res.data) {
    if (selectedIssue.value?.id === issueId) {
      selectedIssue.value = res.data
    }
    await fetchIssues()
    await fetchDepartmentStats()
  }
}

const updateIssueAssignee = async (issueId: number, assigneeName: string, assigneeDept: string) => {
  const res = await apiService.updateIssue(issueId, {
    assignee_name: assigneeName,
    assignee_department: assigneeDept,
  })
  if (res.data) {
    if (selectedIssue.value?.id === issueId) {
      selectedIssue.value = res.data
    }
    await fetchIssues()
    await fetchDepartments()
    await fetchDepartmentStats()
  }
}

const deleteIssue = async (issueId: number) => {
  if (!confirm('确定要删除该问题工单吗？')) return
  const res = await apiService.deleteIssue(issueId)
  if (!res.error) {
    selectedIssue.value = null
    await fetchIssues()
    await fetchDepartmentStats()
  }
}

const switchTab = async (tab: 'list' | 'department') => {
  activeTab.value = tab
  if (tab === 'department') {
    await fetchDepartmentStats()
    await fetchIssuesByDepartment()
  }
}

onMounted(() => {
  fetchIssues()
  fetchDevices()
  fetchDepartments()
  fetchDepartmentStats()
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
                <p class="text-xs text-slate-500">问题上报与追踪</p>
              </div>
            </router-link>
          </div>
          <nav class="hidden md:flex items-center gap-6">
            <router-link to="/" class="text-sm font-medium text-slate-600 hover:text-blue-600">首页</router-link>
            <router-link to="/devices" class="text-sm font-medium text-slate-600 hover:text-blue-600">设备档案</router-link>
            <router-link to="/issues" class="text-sm font-medium text-blue-600">问题上报</router-link>
            <router-link to="/diagnosis" class="text-sm font-medium text-slate-600 hover:text-blue-600">智能诊断</router-link>
            <router-link to="/knowledge" class="text-sm font-medium text-slate-600 hover:text-blue-600">知识库</router-link>
            <router-link to="/chat" class="text-sm font-medium text-slate-600 hover:text-blue-600">智能问答</router-link>
          </nav>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-slate-900">问题上报与工作进度追踪</h2>
        <p class="text-sm text-slate-600 mt-1">上报设备问题，追踪处理进度，记录修复过程，多部门协作</p>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
        <div class="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <p class="text-2xl font-bold text-slate-900">{{ stats.total }}</p>
          <p class="text-xs text-slate-500">问题总数</p>
        </div>
        <div class="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <p class="text-2xl font-bold text-blue-600">{{ stats.open }}</p>
          <p class="text-xs text-slate-500">待处理</p>
        </div>
        <div class="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <p class="text-2xl font-bold text-yellow-600">{{ stats.in_progress }}</p>
          <p class="text-xs text-slate-500">处理中</p>
        </div>
        <div class="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <p class="text-2xl font-bold text-emerald-600">{{ stats.resolved }}</p>
          <p class="text-xs text-slate-500">已解决</p>
        </div>
        <div class="bg-white rounded-xl p-4 border border-red-200 shadow-sm">
          <p class="text-2xl font-bold text-red-600">{{ stats.critical }}</p>
          <p class="text-xs text-slate-500">紧急未处理</p>
        </div>
        <div class="bg-white rounded-xl p-4 border border-orange-200 shadow-sm">
          <p class="text-2xl font-bold text-orange-600">{{ stats.overdue }}</p>
          <p class="text-xs text-slate-500">已逾期</p>
        </div>
      </div>

      <div class="flex gap-2 mb-6">
        <button
          @click="switchTab('list')"
          :class="activeTab === 'list' ? 'bg-blue-600 text-white' : 'bg-white text-slate-700 border border-slate-200'"
          class="px-4 py-2 text-sm font-medium rounded-lg transition-colors"
        >
          问题列表
        </button>
        <button
          @click="switchTab('department')"
          :class="activeTab === 'department' ? 'bg-blue-600 text-white' : 'bg-white text-slate-700 border border-slate-200'"
          class="px-4 py-2 text-sm font-medium rounded-lg transition-colors"
        >
          部门分组视图
        </button>
      </div>

      <template v-if="activeTab === 'list'">
        <div class="bg-white rounded-xl p-6 border border-slate-200 shadow-sm mb-6">
          <div class="flex flex-wrap items-center gap-4">
            <div class="flex-1 min-w-[200px]">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="搜索问题标题、上报人、负责人..."
                class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-slate-600">状态:</span>
              <select v-model="filterStatus" class="px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="all">全部</option>
                <option v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-slate-600">严重度:</span>
              <select v-model="filterSeverity" class="px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="all">全部</option>
                <option v-for="s in severityLevels" :key="s.value" :value="s.value">{{ s.label }}</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-slate-600">部门:</span>
              <select v-model="filterDepartment" class="px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="all">全部</option>
                <option v-for="d in departments" :key="d" :value="d">{{ d }}</option>
              </select>
            </div>
            <button
              @click="openCreateModal"
              class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <span>+</span> 上报问题
            </button>
          </div>
        </div>

        <div v-if="loading" class="text-center py-12">
          <div class="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
          <p class="text-slate-500 mt-3">加载中...</p>
        </div>

        <div v-else-if="filteredIssues.length === 0" class="text-center py-12 bg-white rounded-xl border border-slate-200">
          <span class="text-4xl mb-4 block">📋</span>
          <p class="text-slate-500">暂无问题工单</p>
          <button @click="openCreateModal" class="mt-3 text-blue-600 text-sm hover:underline">上报第一个问题</button>
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="issue in filteredIssues"
            :key="issue.id"
            @click="openIssueDetail(issue)"
            class="bg-white rounded-xl p-5 border border-slate-200 shadow-sm hover:shadow-md hover:border-blue-300 transition-all cursor-pointer"
          >
            <div class="flex items-start justify-between mb-3">
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                  <span :class="['px-2 py-1 text-xs font-medium rounded-full border', getSeverityColor(issue.severity)]">
                    {{ getSeverityLabel(issue.severity) }}
                  </span>
                  <span :class="['px-2 py-1 text-xs font-medium rounded-full', getStatusColor(issue.status)]">
                    {{ getStatusLabel(issue.status) }}
                  </span>
                  <span class="px-2 py-1 text-xs bg-slate-100 text-slate-600 rounded-full">
                    {{ getIssueTypeLabel(issue.issue_type) }}
                  </span>
                  <span v-if="issue.assignee_department" class="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">
                    {{ issue.assignee_department }}
                  </span>
                  <span v-if="issue.due_date && isOverdue(issue.due_date) && issue.status !== 'resolved'" class="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full">
                    已逾期
                  </span>
                </div>
                <h3 class="font-semibold text-slate-900 text-lg">{{ issue.title }}</h3>
                <p class="text-sm text-slate-500 mt-1 line-clamp-2">{{ issue.description }}</p>
              </div>
              <div class="text-right ml-4 flex-shrink-0">
                <div class="w-16 h-16 relative">
                  <svg class="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                    <path class="text-slate-200" stroke="currentColor" stroke-width="3" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                    <path class="text-blue-600" stroke="currentColor" stroke-width="3" fill="none" :stroke-dasharray="`${issue.progress_percent}, 100`" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  </svg>
                  <span class="absolute inset-0 flex items-center justify-center text-sm font-bold text-slate-700">{{ issue.progress_percent }}%</span>
                </div>
              </div>
            </div>
            <div class="flex items-center justify-between pt-3 border-t border-slate-100">
              <div class="flex items-center gap-4 text-xs text-slate-500">
                <span>上报人: {{ issue.reporter_name }}{{ issue.reporter_department ? ` (${issue.reporter_department})` : '' }}</span>
                <span v-if="issue.assignee_name">负责人: {{ issue.assignee_name }}</span>
                <span>{{ formatDateShort(issue.created_at) }}</span>
                <span v-if="issue.due_date" :class="isOverdue(issue.due_date) ? 'text-red-500' : ''">
                  截止: {{ formatDateShort(issue.due_date) }}
                </span>
              </div>
              <button
                @click.stop="openProgressModal(issue)"
                class="text-xs text-blue-600 hover:text-blue-800 font-medium"
              >
                更新进度
              </button>
            </div>
          </div>
        </div>
      </template>

      <template v-else>
        <div class="mb-6">
          <h3 class="text-lg font-semibold text-slate-900 mb-4">部门任务统计</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="dept in departmentStats"
              :key="dept.department"
              class="bg-white rounded-xl p-5 border border-slate-200 shadow-sm"
            >
              <div class="flex items-center justify-between mb-4">
                <h4 class="font-semibold text-slate-900">{{ dept.department }}</h4>
                <span class="text-sm text-slate-500">共 {{ dept.total }} 项</span>
              </div>
              <div class="grid grid-cols-3 gap-3 mb-4">
                <div class="text-center">
                  <p class="text-lg font-bold text-blue-600">{{ dept.open }}</p>
                  <p class="text-xs text-slate-500">待处理</p>
                </div>
                <div class="text-center">
                  <p class="text-lg font-bold text-yellow-600">{{ dept.in_progress }}</p>
                  <p class="text-xs text-slate-500">处理中</p>
                </div>
                <div class="text-center">
                  <p class="text-lg font-bold text-emerald-600">{{ dept.resolved }}</p>
                  <p class="text-xs text-slate-500">已解决</p>
                </div>
              </div>
              <div>
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs text-slate-500">平均进度</span>
                  <span class="text-xs font-medium text-blue-600">{{ dept.avg_progress }}%</span>
                </div>
                <div class="w-full bg-slate-200 rounded-full h-2">
                  <div class="bg-blue-600 h-2 rounded-full transition-all" :style="{ width: dept.avg_progress + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div>
          <h3 class="text-lg font-semibold text-slate-900 mb-4">按部门分组的任务列表</h3>
          <div class="space-y-6">
            <div
              v-for="(deptIssues, deptName) in issuesByDepartment"
              :key="deptName"
              class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden"
            >
              <div class="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <h4 class="font-semibold text-slate-900">{{ deptName }}</h4>
                <span class="text-sm text-slate-500">{{ deptIssues.length }} 项任务</span>
              </div>
              <div class="divide-y divide-slate-100">
                <div
                  v-for="issue in deptIssues"
                  :key="issue.id"
                  @click="openIssueDetail(issue as Issue)"
                  class="px-6 py-4 hover:bg-slate-50 cursor-pointer transition-colors"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                      <span :class="['px-2 py-1 text-xs font-medium rounded-full border', getSeverityColor(issue.severity)]">
                        {{ getSeverityLabel(issue.severity) }}
                      </span>
                      <span :class="['px-2 py-1 text-xs font-medium rounded-full', getStatusColor(issue.status)]">
                        {{ getStatusLabel(issue.status) }}
                      </span>
                      <span class="font-medium text-slate-900">{{ issue.title }}</span>
                    </div>
                    <div class="flex items-center gap-4">
                      <span v-if="issue.assignee_name" class="text-sm text-slate-500">{{ issue.assignee_name }}</span>
                      <div class="w-20 bg-slate-200 rounded-full h-2">
                        <div class="bg-blue-600 h-2 rounded-full" :style="{ width: issue.progress_percent + '%' }"></div>
                      </div>
                      <span class="text-sm font-medium text-slate-700 w-10 text-right">{{ issue.progress_percent }}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </main>

    <div
      v-if="selectedIssue && !showProgressModal"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="closeIssueDetail"
    >
      <div class="bg-white rounded-xl max-w-4xl w-full max-h-[85vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
          <h3 class="text-lg font-semibold text-slate-900">问题详情 #{{ selectedIssue.id }}</h3>
          <div class="flex items-center gap-3">
            <button @click="deleteIssue(selectedIssue.id)" class="text-sm text-red-500 hover:text-red-700">删除</button>
            <button @click="closeIssueDetail" class="text-slate-400 hover:text-slate-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        <div class="p-6 space-y-6">
          <div>
            <div class="flex items-center gap-3 mb-3">
              <span :class="['px-2 py-1 text-xs font-medium rounded-full border', getSeverityColor(selectedIssue.severity)]">
                {{ getSeverityLabel(selectedIssue.severity) }}
              </span>
              <span :class="['px-2 py-1 text-xs font-medium rounded-full', getStatusColor(selectedIssue.status)]">
                {{ getStatusLabel(selectedIssue.status) }}
              </span>
              <span class="px-2 py-1 text-xs bg-slate-100 text-slate-600 rounded-full">
                {{ getIssueTypeLabel(selectedIssue.issue_type) }}
              </span>
              <span class="text-xs text-slate-400">优先级: {{ getPriorityLabel(selectedIssue.priority) }}</span>
            </div>
            <h2 class="text-xl font-bold text-slate-900 mb-2">{{ selectedIssue.title }}</h2>
            <p class="text-sm text-slate-600 bg-slate-50 p-4 rounded-lg whitespace-pre-wrap">{{ selectedIssue.description }}</p>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p class="text-xs text-slate-400 mb-1">上报人</p>
              <p class="text-sm font-medium text-slate-900">{{ selectedIssue.reporter_name }}</p>
              <p v-if="selectedIssue.reporter_department" class="text-xs text-slate-500">{{ selectedIssue.reporter_department }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 mb-1">负责人/部门</p>
              <p class="text-sm font-medium text-slate-900">{{ selectedIssue.assignee_name || '待分配' }}</p>
              <p v-if="selectedIssue.assignee_department" class="text-xs text-slate-500">{{ selectedIssue.assignee_department }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 mb-1">上报时间</p>
              <p class="text-sm font-medium text-slate-900">{{ formatDate(selectedIssue.created_at) }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 mb-1">截止/完成时间</p>
              <p class="text-sm font-medium" :class="selectedIssue.due_date && isOverdue(selectedIssue.due_date) && selectedIssue.status !== 'resolved' ? 'text-red-600' : 'text-slate-900'">
                {{ selectedIssue.resolved_at ? formatDate(selectedIssue.resolved_at) : (selectedIssue.due_date ? formatDate(selectedIssue.due_date) : '无截止日期') }}
              </p>
              <p v-if="selectedIssue.due_date && !selectedIssue.resolved_at" class="text-xs" :class="isOverdue(selectedIssue.due_date) ? 'text-red-500' : 'text-slate-500'">
                {{ isOverdue(selectedIssue.due_date) ? `已逾期 ${Math.abs(getDaysUntilDue(selectedIssue.due_date) || 0)} 天` : `剩余 ${getDaysUntilDue(selectedIssue.due_date)} 天` }}
              </p>
            </div>
          </div>

          <div>
            <div class="flex items-center justify-between mb-2">
              <h4 class="text-sm font-medium text-slate-700">处理进度</h4>
              <span class="text-sm font-bold text-blue-600">{{ selectedIssue.progress_percent }}%</span>
            </div>
            <div class="w-full bg-slate-200 rounded-full h-3">
              <div class="bg-blue-600 h-3 rounded-full transition-all" :style="{ width: selectedIssue.progress_percent + '%' }"></div>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <button
              @click="openProgressModal(selectedIssue)"
              class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              更新进度
            </button>
            <select
              @change="updateIssueStatus(selectedIssue.id, ($event.target as HTMLSelectElement).value)"
              :value="selectedIssue.status"
              class="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
            </select>
          </div>

          <div>
            <h4 class="text-sm font-medium text-slate-700 mb-3">进度记录时间线</h4>
            <div v-if="!selectedIssue.progress_logs || selectedIssue.progress_logs.length === 0" class="text-center py-6 text-slate-400 text-sm bg-slate-50 rounded-lg">
              暂无进度记录，点击"更新进度"添加第一条记录
            </div>
            <div v-else class="relative">
              <div class="absolute left-8 top-0 bottom-0 w-0.5 bg-slate-200"></div>
              <div class="space-y-6">
                <div
                  v-for="(log, index) in selectedIssue.progress_logs"
                  :key="log.id"
                  class="relative pl-16"
                >
                  <div class="absolute left-6 top-2 w-5 h-5 rounded-full bg-blue-600 border-4 border-white shadow-sm z-10"></div>
                  <div class="bg-slate-50 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-2">
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-semibold text-slate-900">{{ log.user_name }}</span>
                        <span v-if="log.user_department" class="text-xs text-slate-500">({{ log.user_department }})</span>
                      </div>
                      <span class="text-xs text-slate-400">{{ formatDate(log.created_at) }}</span>
                    </div>
                    <p class="text-sm text-slate-700 mb-2">{{ log.progress_note }}</p>
                    <div v-if="log.action_taken" class="text-sm text-slate-600 bg-white p-2 rounded mb-2">
                      <span class="font-medium">采取措施:</span> {{ log.action_taken }}
                    </div>
                    <div class="flex items-center gap-4 text-xs text-slate-500">
                      <span v-if="log.progress_percent !== null" class="flex items-center gap-1">
                        <span class="w-2 h-2 bg-blue-500 rounded-full"></span>
                        进度: {{ log.progress_percent }}%
                      </span>
                      <span v-if="log.status" class="flex items-center gap-1">
                        <span class="w-2 h-2 bg-green-500 rounded-full"></span>
                        状态: {{ getStatusLabel(log.status) }}
                      </span>
                      <span v-if="log.hours_spent > 0" class="flex items-center gap-1">
                        <span class="w-2 h-2 bg-orange-500 rounded-full"></span>
                        工时: {{ log.hours_spent }}h
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="showProgressModal"
      class="fixed inset-0 bg-black/60 z-[60] flex items-center justify-center p-4"
      @click.self="closeProgressModal"
    >
      <div class="bg-white rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
          <h3 class="text-lg font-semibold text-slate-900">更新工作进度</h3>
          <button @click="closeProgressModal" class="text-slate-400 hover:text-slate-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-6">
          <div v-if="selectedIssue" class="mb-4 p-3 bg-slate-50 rounded-lg">
            <p class="text-sm font-medium text-slate-900">{{ selectedIssue.title }}</p>
            <p class="text-xs text-slate-500 mt-1">当前进度: {{ selectedIssue.progress_percent }}%</p>
          </div>
          <form @submit.prevent="addProgress" class="space-y-5">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">处理人 <span class="text-red-500">*</span></label>
                <input v-model="newProgress.user_name" type="text" placeholder="处理人姓名" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">所属部门</label>
                <select v-model="newProgress.user_department" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option value="">选择部门</option>
                  <option v-for="d in departments" :key="d" :value="d">{{ d }}</option>
                </select>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">进度说明 <span class="text-red-500">*</span></label>
              <textarea v-model="newProgress.progress_note" rows="3" placeholder="描述当前处理进展..." class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none" required></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">采取措施</label>
              <textarea v-model="newProgress.action_taken" rows="2" placeholder="描述已采取的具体措施..." class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">进度百分比 ({{ newProgress.progress_percent }}%)</label>
              <input v-model.number="newProgress.progress_percent" type="range" min="0" max="100" step="5" class="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer" />
              <div class="flex justify-between text-xs text-slate-400 mt-1">
                <span>0%</span><span>50%</span><span>100%</span>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">更新状态</label>
                <select v-model="newProgress.status" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option value="">不更新</option>
                  <option v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">投入工时 (小时)</label>
                <input v-model.number="newProgress.hours_spent" type="number" min="0" step="0.5" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
            </div>
            <div class="flex gap-3 pt-4 border-t border-slate-200">
              <button type="button" @click="closeProgressModal" class="flex-1 px-4 py-2.5 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors">取消</button>
              <button type="submit" :disabled="isSubmitting" class="flex-1 px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50">
                {{ isSubmitting ? '提交中...' : '提交进度' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="closeCreateModal"
    >
      <div class="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
          <h3 class="text-lg font-semibold text-slate-900">上报问题</h3>
          <button @click="closeCreateModal" class="text-slate-400 hover:text-slate-600">
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
            <p class="text-lg font-semibold text-slate-900">问题上报成功！</p>
            <p class="text-sm text-slate-500 mt-1">工单已创建，等待处理</p>
          </div>
          <form v-else @submit.prevent="createIssue" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="md:col-span-2">
                <label class="block text-sm font-medium text-slate-700 mb-2">问题标题 <span class="text-red-500">*</span></label>
                <input v-model="newIssue.title" type="text" placeholder="简要描述问题" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">问题类型 <span class="text-red-500">*</span></label>
                <select v-model="newIssue.issue_type" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option v-for="t in issueTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">关联设备</label>
                <select v-model="newIssue.device_id" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option :value="null">无关联设备</option>
                  <option v-for="d in devices" :key="d.id" :value="d.id">{{ d.name }} ({{ d.model }})</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">严重程度 <span class="text-red-500">*</span></label>
                <select v-model="newIssue.severity" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option v-for="s in severityLevels" :key="s.value" :value="s.value">{{ s.label }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">优先级</label>
                <select v-model="newIssue.priority" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option v-for="p in priorityLevels" :key="p.value" :value="p.value">{{ p.label }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">上报人 <span class="text-red-500">*</span></label>
                <input v-model="newIssue.reporter_name" type="text" placeholder="上报人姓名" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">上报人部门</label>
                <select v-model="newIssue.reporter_department" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option value="">选择部门</option>
                  <option v-for="d in departments" :key="d" :value="d">{{ d }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">指派负责人</label>
                <input v-model="newIssue.assignee_name" type="text" placeholder="负责人姓名" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">负责部门</label>
                <select v-model="newIssue.assignee_department" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option value="">选择部门</option>
                  <option v-for="d in departments" :key="d" :value="d">{{ d }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">问题位置</label>
                <input v-model="newIssue.location" type="text" placeholder="问题发生位置" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">截止日期</label>
                <input v-model="newIssue.due_date" type="date" class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">问题描述 <span class="text-red-500">*</span></label>
              <textarea v-model="newIssue.description" rows="5" placeholder="详细描述问题现象、发生条件、影响范围等..." class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none" required></textarea>
            </div>
            <div class="flex gap-3 pt-4 border-t border-slate-200">
              <button type="button" @click="closeCreateModal" class="flex-1 px-4 py-2.5 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors">取消</button>
              <button type="submit" :disabled="isSubmitting" class="flex-1 px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
                <svg v-if="isSubmitting" class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>{{ isSubmitting ? '提交中...' : '提交问题' }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
