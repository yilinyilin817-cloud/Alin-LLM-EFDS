<script setup lang="ts">
import { ref } from 'vue'
import MobileNav from '@/components/MobileNav.vue'

const faultPhenomenon = ref('')
const isDiagnosing = ref(false)
const diagnosisResult = ref<any>(null)

const examplePhenomena = [
  '电机运行时出现异常振动和温度升高',
  '液压系统压力不稳定，油温偏高',
  '变频器频繁报警，显示过电流故障',
  'PLC程序运行异常，输出不稳定',
]

const diagnose = async () => {
  if (!faultPhenomenon.value.trim()) return

  isDiagnosing.value = true
  diagnosisResult.value = null

  await new Promise(resolve => setTimeout(resolve, 2000))

  diagnosisResult.value = {
    possible_causes: [
      '轴承磨损或损坏',
      '转子不平衡',
      '润滑不足或润滑脂变质',
      '电机安装不当，地脚松动',
      '负载过大或机械卡涩',
    ],
    repair_suggestions: [
      '检查轴承状况，必要时更换轴承',
      '进行动平衡校正',
      '更换润滑脂，确保润滑充分',
      '检查并紧固地脚螺栓',
      '检查负载情况，排除机械故障',
    ],
    preventive_measures: [
      '建立定期巡检制度',
      '制定设备润滑保养计划',
      '安装振动监测传感器',
      '定期进行设备状态检测',
    ],
    severity: 'high',
    similar_cases: [
      { content: '某型号三相异步电机运行3个月后出现异常振动，经检查为轴承磨损导致', score: 0.92 },
      { content: '液压泵站电机温度异常升高，原因为润滑脂干涸', score: 0.87 },
    ],
  }

  isDiagnosing.value = false
}

const selectExample = (example: string) => {
  faultPhenomenon.value = example
}

const getSeverityColor = (severity: string) => {
  const colors: Record<string, string> = {
    high: 'bg-red-100 text-red-800 border-red-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-green-100 text-green-800 border-green-200',
  }
  return colors[severity] || 'bg-gray-100 text-gray-800 border-gray-200'
}

const getSeverityText = (severity: string) => {
  const texts: Record<string, string> = {
    high: '高风险',
    medium: '中风险',
    low: '低风险',
  }
  return texts[severity] || severity
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
                <p class="text-xs text-slate-500 hidden sm:block">智能故障诊断</p>
              </div>
            </router-link>
          </div>
          <nav class="hidden md:flex items-center gap-6">
            <router-link to="/" class="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">首页</router-link>
            <router-link to="/diagnosis" class="text-sm font-medium text-blue-600">智能诊断</router-link>
            <router-link to="/knowledge" class="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">知识库</router-link>
            <router-link to="/chat" class="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">智能问答</router-link>
          </nav>

          <MobileNav />
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
        <div class="lg:col-span-2">
          <div class="bg-white rounded-xl p-4 sm:p-6 border border-slate-200 shadow-sm">
            <h2 class="text-base sm:text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <span class="text-blue-600">🔍</span>
              故障现象描述
            </h2>

            <div class="mb-4">
              <label class="block text-sm font-medium text-slate-700 mb-2">
                请详细描述设备故障现象
              </label>
              <textarea
                v-model="faultPhenomenon"
                rows="4"
                class="w-full px-3 sm:px-4 py-2 sm:py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm sm:text-base"
                placeholder="例如：电机运行时出现异常振动，温度持续升高，伴有异常噪音..."
              ></textarea>
            </div>

            <div class="mb-4 sm:mb-6">
              <p class="text-xs sm:text-sm text-slate-500 mb-2">示例故障现象：</p>
              <div class="flex flex-wrap gap-1.5 sm:gap-2">
                <button
                  v-for="example in examplePhenomena"
                  :key="example"
                  @click="selectExample(example)"
                  class="px-2 sm:px-3 py-1 sm:py-1.5 text-xs bg-slate-100 text-slate-600 rounded-full hover:bg-blue-100 hover:text-blue-600 transition-colors"
                >
                  {{ example }}
                </button>
              </div>
            </div>

            <button
              @click="diagnose"
              :disabled="!faultPhenomenon.trim() || isDiagnosing"
              class="w-full py-2.5 sm:py-3 text-sm sm:text-base bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="isDiagnosing" class="flex items-center justify-center gap-2">
                <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                正在诊断中...
              </span>
              <span v-else>开始智能诊断</span>
            </button>
          </div>

          <div v-if="diagnosisResult" class="mt-4 sm:mt-6 bg-white rounded-xl p-4 sm:p-6 border border-slate-200 shadow-sm">
            <div class="flex items-center justify-between mb-4 sm:mb-6">
              <h2 class="text-base sm:text-lg font-semibold text-slate-900 flex items-center gap-2">
                <span class="text-green-600">📊</span>
                诊断结果
              </h2>
              <span
                :class="getSeverityColor(diagnosisResult.severity)"
                class="px-2 sm:px-3 py-1 text-xs sm:text-sm font-medium rounded-full border"
              >
                {{ getSeverityText(diagnosisResult.severity) }}
              </span>
            </div>

            <div class="space-y-4 sm:space-y-6">
              <div>
                <h3 class="text-sm font-semibold text-slate-700 mb-2 sm:mb-3 flex items-center gap-2">
                  <span class="w-5 h-5 bg-red-100 text-red-600 rounded flex items-center justify-center text-xs">!</span>
                  可能的故障原因
                </h3>
                <div class="space-y-2">
                  <div
                    v-for="(cause, index) in diagnosisResult.possible_causes"
                    :key="index"
                    class="flex items-start gap-2 sm:gap-3 p-2 sm:p-3 bg-red-50 rounded-lg"
                  >
                    <span class="w-5 h-5 sm:w-6 sm:h-6 bg-red-200 text-red-700 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                      {{ index + 1 }}
                    </span>
                    <p class="text-xs sm:text-sm text-slate-700">{{ cause }}</p>
                  </div>
                </div>
              </div>

              <div>
                <h3 class="text-sm font-semibold text-slate-700 mb-2 sm:mb-3 flex items-center gap-2">
                  <span class="w-5 h-5 bg-blue-100 text-blue-600 rounded flex items-center justify-center text-xs">🔧</span>
                  维修建议
                </h3>
                <div class="space-y-2">
                  <div
                    v-for="(suggestion, index) in diagnosisResult.repair_suggestions"
                    :key="index"
                    class="flex items-start gap-2 sm:gap-3 p-2 sm:p-3 bg-blue-50 rounded-lg"
                  >
                    <span class="w-5 h-5 sm:w-6 sm:h-6 bg-blue-200 text-blue-700 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                      {{ index + 1 }}
                    </span>
                    <p class="text-xs sm:text-sm text-slate-700">{{ suggestion }}</p>
                  </div>
                </div>
              </div>

              <div>
                <h3 class="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                  <span class="w-5 h-5 bg-green-100 text-green-600 rounded flex items-center justify-center text-xs">🛡️</span>
                  预防措施
                </h3>
                <div class="space-y-2">
                  <div
                    v-for="(measure, index) in diagnosisResult.preventive_measures"
                    :key="index"
                    class="flex items-start gap-3 p-3 bg-green-50 rounded-lg"
                  >
                    <span class="w-6 h-6 bg-green-200 text-green-700 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                      {{ index + 1 }}
                    </span>
                    <p class="text-sm text-slate-700">{{ measure }}</p>
                  </div>
                </div>
              </div>

              <div v-if="diagnosisResult.similar_cases?.length">
                <h3 class="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                  <span class="w-5 h-5 bg-purple-100 text-purple-600 rounded flex items-center justify-center text-xs">📚</span>
                  相似案例
                </h3>
                <div class="space-y-2">
                  <div
                    v-for="(case_, index) in diagnosisResult.similar_cases"
                    :key="index"
                    class="p-3 bg-purple-50 rounded-lg"
                  >
                    <p class="text-sm text-slate-700 mb-1">{{ case_.content }}</p>
                    <p class="text-xs text-purple-600">相似度：{{ (case_.score * 100).toFixed(1) }}%</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="lg:col-span-1">
          <div class="bg-white rounded-xl p-4 sm:p-6 border border-slate-200 shadow-sm lg:sticky lg:top-24">
            <h3 class="text-base sm:text-lg font-semibold text-slate-900 mb-3 sm:mb-4 flex items-center gap-2">
              <span class="text-indigo-600">💡</span>
              诊断提示
            </h3>

            <div class="space-y-3 sm:space-y-4">
              <div class="p-3 sm:p-4 bg-indigo-50 rounded-lg">
                <h4 class="text-sm font-medium text-indigo-800 mb-2">如何描述故障现象？</h4>
                <ul class="text-xs text-indigo-700 space-y-1">
                  <li>• 描述故障发生的时间和频率</li>
                  <li>• 说明设备运行状态和环境</li>
                  <li>• 记录异常声音、振动、温度等</li>
                  <li>• 提供设备型号和使用年限</li>
                </ul>
              </div>

              <div class="p-3 sm:p-4 bg-amber-50 rounded-lg">
                <h4 class="text-sm font-medium text-amber-800 mb-2">常见故障类型</h4>
                <div class="flex flex-wrap gap-1.5 sm:gap-2 mt-2">
                  <span class="px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded">机械故障</span>
                  <span class="px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded">电气故障</span>
                  <span class="px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded">液压故障</span>
                  <span class="px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded">控制系统</span>
                  <span class="px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded">传感器故障</span>
                </div>
              </div>

              <div class="p-4 bg-green-50 rounded-lg">
                <h4 class="text-sm font-medium text-green-800 mb-2">诊断流程</h4>
                <ol class="text-xs text-green-700 space-y-1">
                  <li>1. 输入故障现象描述</li>
                  <li>2. AI分析可能原因</li>
                  <li>3. 获取维修建议</li>
                  <li>4. 查看相似案例</li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
