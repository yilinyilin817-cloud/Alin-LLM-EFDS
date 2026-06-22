<script setup lang="ts">
import { ref, computed } from 'vue'
import MobileNav from '@/components/MobileNav.vue'

interface FaultCase {
  id: number
  title: string
  device: string
  faultType: string
  severity: string
  status: string
  date: string
  phenomenon: string
  cause: string
  solution: string
}

const cases = ref<FaultCase[]>([
  {
    id: 1,
    title: '电机异常振动诊断',
    device: '三相异步电机',
    faultType: '机械故障',
    severity: 'high',
    status: 'resolved',
    date: '2024-01-15',
    phenomenon: '电机运行时出现异常振动，频率随转速变化，温度持续升高至85°C',
    cause: '轴承磨损导致转子不平衡',
    solution: '更换轴承，重新进行动平衡校正',
  },
  {
    id: 2,
    title: '液压系统压力不足',
    device: '液压泵站',
    faultType: '液压故障',
    severity: 'medium',
    status: 'resolved',
    date: '2024-01-14',
    phenomenon: '系统压力波动大，从25MPa降至18MPa，油温偏高',
    cause: '液压泵磨损，吸油管路有气泡',
    solution: '检修液压泵，排出管路空气',
  },
  {
    id: 3,
    title: 'PLC通信故障',
    device: '西门子S7-1200',
    faultType: '控制系统',
    severity: 'low',
    status: 'open',
    date: '2024-01-13',
    phenomenon: 'PLC与HMI通信中断，指示灯闪烁',
    cause: '通信模块参数设置错误',
    solution: '检查并重新配置通信参数',
  },
  {
    id: 4,
    title: '变频器频繁报警',
    device: 'ABB ACS880',
    faultType: '电气故障',
    severity: 'high',
    status: 'resolved',
    date: '2024-01-12',
    phenomenon: '变频器显示过电流故障代码F0001，报警频率约每2小时一次',
    cause: '电机电缆绝缘老化，输出侧接触器接触不良',
    solution: '更换电机电缆，检查接触器',
  },
  {
    id: 5,
    title: '传感器读数异常',
    device: '温度传感器',
    faultType: '传感器故障',
    severity: 'low',
    status: 'resolved',
    date: '2024-01-11',
    phenomenon: '温度显示在-20°C至150°C之间剧烈波动',
    cause: '传感器线路接触不良',
    solution: '紧固接线端子，更换传感器',
  },
])

const filterStatus = ref('all')
const filterSeverity = ref('all')
const searchQuery = ref('')
const selectedCase = ref<FaultCase | null>(null)

const filteredCases = computed(() => {
  return cases.value.filter(c => {
    const matchStatus = filterStatus.value === 'all' || c.status === filterStatus.value
    const matchSeverity = filterSeverity.value === 'all' || c.severity === filterSeverity.value
    const matchSearch = c.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                       c.device.toLowerCase().includes(searchQuery.value.toLowerCase())
    return matchStatus && matchSeverity && matchSearch
  })
})

const getSeverityColor = (severity: string) => {
  const colors: Record<string, string> = {
    high: 'bg-red-100 text-red-800 border-red-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-green-100 text-green-800 border-green-200',
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

const getStatusColor = (status: string) => {
  return status === 'resolved' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
}

const getStatusText = (status: string) => {
  return status === 'resolved' ? '已解决' : '处理中'
}

const openCaseDetail = (c: FaultCase) => {
  selectedCase.value = c
}

const closeDetail = () => {
  selectedCase.value = null
}
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
                <p class="text-xs text-slate-500 hidden sm:block">案例管理</p>
              </div>
            </router-link>
          </div>
          <nav class="hidden md:flex items-center gap-6">
            <router-link to="/" class="text-sm font-medium text-slate-600 hover:text-blue-600">首页</router-link>
            <router-link to="/diagnosis" class="text-sm font-medium text-slate-600 hover:text-blue-600">智能诊断</router-link>
            <router-link to="/knowledge" class="text-sm font-medium text-slate-600 hover:text-blue-600">知识库</router-link>
            <router-link to="/chat" class="text-sm font-medium text-slate-600 hover:text-blue-600">智能问答</router-link>
          </nav>
          <MobileNav />
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-slate-900">故障案例管理</h2>
        <p class="text-sm text-slate-600 mt-1">查看和管理历史故障案例，积累维护经验</p>
      </div>

      <div class="bg-white rounded-xl p-6 border border-slate-200 shadow-sm mb-6">
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex-1 min-w-[200px]">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索案例..."
              class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div class="flex items-center gap-2">
            <span class="text-sm text-slate-600">状态:</span>
            <div class="flex gap-2">
              <button
                @click="filterStatus = 'all'"
                :class="filterStatus === 'all' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
                class="px-3 py-1.5 text-sm rounded-lg transition-colors whitespace-nowrap"
              >
                全部
              </button>
              <button
                @click="filterStatus = 'resolved'"
                :class="filterStatus === 'resolved' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
                class="px-3 py-1.5 text-sm rounded-lg transition-colors whitespace-nowrap"
              >
                已解决
              </button>
              <button
                @click="filterStatus = 'open'"
                :class="filterStatus === 'open' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
                class="px-3 py-1.5 text-sm rounded-lg transition-colors whitespace-nowrap"
              >
                处理中
              </button>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <span class="text-sm text-slate-600">严重度:</span>
            <div class="flex gap-2">
              <button
                @click="filterSeverity = 'all'"
                :class="filterSeverity === 'all' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
                class="px-3 py-1.5 text-sm rounded-lg transition-colors whitespace-nowrap"
              >
                全部
              </button>
              <button
                @click="filterSeverity = 'high'"
                :class="filterSeverity === 'high' ? 'bg-red-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
                class="px-3 py-1.5 text-sm rounded-lg transition-colors whitespace-nowrap"
              >
                高
              </button>
              <button
                @click="filterSeverity = 'medium'"
                :class="filterSeverity === 'medium' ? 'bg-yellow-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
                class="px-3 py-1.5 text-sm rounded-lg transition-colors whitespace-nowrap"
              >
                中
              </button>
              <button
                @click="filterSeverity = 'low'"
                :class="filterSeverity === 'low' ? 'bg-green-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
                class="px-3 py-1.5 text-sm rounded-lg transition-colors whitespace-nowrap"
              >
                低
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-slate-50 border-b border-slate-200">
              <tr>
                <th class="px-2 sm:px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">案例标题</th>
                <th class="px-2 sm:px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">设备</th>
                <th class="px-2 sm:px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">故障类型</th>
                <th class="px-2 sm:px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">严重度</th>
                <th class="px-2 sm:px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">状态</th>
                <th class="px-2 sm:px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">日期</th>
                <th class="px-2 sm:px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr
                v-for="c in filteredCases"
                :key="c.id"
                class="hover:bg-slate-50 transition-colors cursor-pointer"
                @click="openCaseDetail(c)"
              >
                <td class="px-2 sm:px-6 py-4">
                  <p class="text-sm font-medium text-slate-900">{{ c.title }}</p>
                </td>
                <td class="px-2 sm:px-6 py-4">
                  <p class="text-sm text-slate-600">{{ c.device }}</p>
                </td>
                <td class="px-2 sm:px-6 py-4">
                  <span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">{{ c.faultType }}</span>
                </td>
                <td class="px-2 sm:px-6 py-4">
                  <span :class="['px-2 py-1 text-xs font-medium rounded-full border', getSeverityColor(c.severity)]">
                    {{ getSeverityText(c.severity) }}
                  </span>
                </td>
                <td class="px-2 sm:px-6 py-4">
                  <span :class="['px-2 py-1 text-xs font-medium rounded-full', getStatusColor(c.status)]">
                    {{ getStatusText(c.status) }}
                  </span>
                </td>
                <td class="px-2 sm:px-6 py-4">
                  <p class="text-sm text-slate-600">{{ c.date }}</p>
                </td>
                <td class="px-2 sm:px-6 py-4">
                  <button
                    @click.stop="openCaseDetail(c)"
                    class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    查看详情
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>

    <div
      v-if="selectedCase"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="closeDetail"
    >
      <div class="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-slate-900">{{ selectedCase.title }}</h3>
          <button @click="closeDetail" class="text-slate-400 hover:text-slate-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-6 space-y-6">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-slate-500 mb-1">设备</p>
              <p class="text-sm font-medium text-slate-900">{{ selectedCase.device }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-500 mb-1">故障类型</p>
              <p class="text-sm font-medium text-slate-900">{{ selectedCase.faultType }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-500 mb-1">严重度</p>
              <span :class="['px-2 py-1 text-xs font-medium rounded-full border', getSeverityColor(selectedCase.severity)]">
                {{ getSeverityText(selectedCase.severity) }}
              </span>
            </div>
            <div>
              <p class="text-xs text-slate-500 mb-1">状态</p>
              <span :class="['px-2 py-1 text-xs font-medium rounded-full', getStatusColor(selectedCase.status)]">
                {{ getStatusText(selectedCase.status) }}
              </span>
            </div>
          </div>

          <div>
            <h4 class="text-sm font-medium text-slate-700 mb-2">故障现象</h4>
            <p class="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg">{{ selectedCase.phenomenon }}</p>
          </div>

          <div>
            <h4 class="text-sm font-medium text-slate-700 mb-2">故障原因</h4>
            <p class="text-sm text-slate-600 bg-red-50 p-3 rounded-lg">{{ selectedCase.cause }}</p>
          </div>

          <div>
            <h4 class="text-sm font-medium text-slate-700 mb-2">解决方案</h4>
            <p class="text-sm text-slate-600 bg-green-50 p-3 rounded-lg">{{ selectedCase.solution }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
