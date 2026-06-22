<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiService from '@/services/api'
import MobileNav from '@/components/MobileNav.vue'

interface Document {
  id: number
  title: string
  file_type: string
  content?: string
  encoding?: string
  chunk_count: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  error_message?: string
  created_at: string
  updated_at?: string
}

const searchQuery = ref('')
const isDragging = ref(false)
const activeFilter = ref<'all' | Document['status']>('all')
const isLoading = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const showSearchModal = ref(false)
const searchText = ref('')
const searchResults = ref<any[]>([])
const isSearching = ref(false)
const selectedDoc = ref<Document | null>(null)
const showPreview = ref(false)
const showEditor = ref(false)
const editingContent = ref('')
const editingTitle = ref('')
const isSaving = ref(false)
const isLoadingContent = ref(false)
const selectedDocEncoding = ref('utf-8')

const documents = ref<Document[]>([])

const loadDocuments = async () => {
  isLoading.value = true
  const result = await apiService.getDocuments()
  if (result.data) {
    documents.value = result.data.documents || []
  }
  isLoading.value = false
}

onMounted(() => {
  loadDocuments()
})

const filterCounts = computed(() => ({
  all: documents.value.length,
  pending: documents.value.filter((d) => d.status === 'pending').length,
  processing: documents.value.filter((d) => d.status === 'processing').length,
  completed: documents.value.filter((d) => d.status === 'completed').length,
  failed: documents.value.filter((d) => d.status === 'failed').length,
}))

const filteredDocuments = computed(() => {
  let list = documents.value
  if (activeFilter.value !== 'all') {
    list = list.filter((d) => d.status === activeFilter.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter((d) => d.title.toLowerCase().includes(q))
  }
  return list
})

const totalChunks = computed(() =>
  documents.value.reduce((sum, d) => sum + (d.chunk_count || 0), 0)
)
const indexedCount = computed(
  () => documents.value.filter((d) => d.status === 'completed').length
)

const statusConfig: Record<string, { label: string; bg: string; text: string; dot: string }> = {
  pending: {
    label: '待处理',
    bg: 'bg-slate-100',
    text: 'text-slate-700',
    dot: 'bg-slate-400',
  },
  processing: {
    label: '处理中',
    bg: 'bg-blue-100',
    text: 'text-blue-700',
    dot: 'bg-blue-500',
  },
  completed: {
    label: '已完成',
    bg: 'bg-emerald-100',
    text: 'text-emerald-700',
    dot: 'bg-emerald-500',
  },
  failed: {
    label: '失败',
    bg: 'bg-red-100',
    text: 'text-red-700',
    dot: 'bg-red-500',
  },
}

const fileTypeIcons: Record<string, string> = {
  '.pdf': '📄',
  '.docx': '📝',
  '.doc': '📝',
  '.xlsx': '📊',
  '.xls': '📊',
  '.csv': '📊',
  '.txt': '📃',
  '.md': '📋',
}

const encodingLabels: Record<string, string> = {
  'utf-8': 'UTF-8',
  'utf8': 'UTF-8',
  'gbk': 'GBK',
  'gb2312': 'GB2312',
  'utf-16': 'UTF-16',
  'utf16': 'UTF-16',
  'ascii': 'ASCII',
}

const editableFileTypes = ['.txt', '.csv', '.md']

const getFileIcon = (fileType: string) => {
  return fileTypeIcons[fileType] || '📄'
}

const isEditable = (fileType: string) => {
  return editableFileTypes.includes(fileType)
}

const getEncodingLabel = (encoding?: string) => {
  if (!encoding) return 'UTF-8'
  return encodingLabels[encoding.toLowerCase()] || encoding.toUpperCase()
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const onDragOver = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = true
}
const onDragLeave = () => {
  isDragging.value = false
}
const onDrop = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files?.length) handleFiles(files)
}
const onFileSelect = (e: Event) => {
  const input = e.target as HTMLInputElement
  if (input.files?.length) handleFiles(input.files)
}

const handleFiles = async (files: FileList) => {
  const allowedTypes = ['.pdf', '.doc', '.docx', '.xlsx', '.xls', '.csv', '.txt', '.md']

  for (const file of Array.from(files)) {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()

    if (!allowedTypes.includes(ext)) {
      alert(`不支持的文件格式: ${ext}`)
      continue
    }

    if (file.size > 50 * 1024 * 1024) {
      alert(`文件 ${file.name} 超过50MB限制`)
      continue
    }

    isUploading.value = true
    uploadProgress.value = 0

    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)

    const result = await apiService.uploadDocument(file)

    clearInterval(progressInterval)
    uploadProgress.value = 100

    if (result.error) {
      alert(`上传失败: ${result.error}`)
    } else {
      await loadDocuments()
    }

    setTimeout(() => {
      isUploading.value = false
      uploadProgress.value = 0
    }, 1000)
  }
}

const triggerFileInput = () => {
  const input = document.getElementById('file-upload') as HTMLInputElement
  input?.click()
}

const removeDocument = async (id: number) => {
  if (!confirm('确定要删除这个文档吗？')) return

  const result = await apiService.deleteDocument(id)
  if (result.error) {
    alert(`删除失败: ${result.error}`)
  } else {
    await loadDocuments()
  }
}

const reprocessDocument = async (id: number) => {
  const result = await apiService.reprocessDocument(id)
  if (result.error) {
    alert(`重新处理失败: ${result.error}`)
  } else {
    await loadDocuments()
  }
}

const openSearch = () => {
  showSearchModal.value = true
  searchText.value = ''
  searchResults.value = []
}

const performSearch = async () => {
  if (!searchText.value.trim()) return

  isSearching.value = true
  const result = await apiService.searchDocuments(searchText.value)

  if (result.data) {
    searchResults.value = result.data.documents || []
  }
  isSearching.value = false
}

const previewDocument = async (doc: Document) => {
  selectedDoc.value = doc
  showPreview.value = true
  selectedDocEncoding.value = doc.encoding || 'utf-8'

  if (!doc.content) {
    isLoadingContent.value = true
    const result = await apiService.getDocumentContent(doc.id)
    if (result.data) {
      selectedDoc.value = { ...doc, content: result.data.content }
      selectedDocEncoding.value = result.data.encoding || 'utf-8'
    }
    isLoadingContent.value = false
  }
}

const closePreview = () => {
  showPreview.value = false
  selectedDoc.value = null
}

const openEditor = async (doc: Document) => {
  selectedDoc.value = doc
  editingTitle.value = doc.title
  editingContent.value = doc.content || ''
  showEditor.value = true
  selectedDocEncoding.value = doc.encoding || 'utf-8'

  if (!doc.content) {
    isLoadingContent.value = true
    const result = await apiService.getDocumentContent(doc.id)
    if (result.data) {
      editingContent.value = result.data.content
      selectedDoc.value = { ...doc, content: result.data.content }
      selectedDocEncoding.value = result.data.encoding || 'utf-8'
    }
    isLoadingContent.value = false
  }
}

const closeEditor = () => {
  showEditor.value = false
  selectedDoc.value = null
  editingContent.value = ''
  editingTitle.value = ''
}

const saveDocument = async () => {
  if (!selectedDoc.value) return

  isSaving.value = true
  const result = await apiService.updateDocument(selectedDoc.value.id, {
    title: editingTitle.value,
    content: editingContent.value,
  })

  if (result.error) {
    alert(`保存失败: ${result.error}`)
  } else {
    alert('保存成功！')
    await loadDocuments()
    closeEditor()
  }
  isSaving.value = false
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
                <p class="text-xs text-slate-500 hidden sm:block">知识库管理</p>
              </div>
            </router-link>
          </div>
          <nav class="hidden md:flex items-center gap-6">
            <router-link to="/" class="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">首页</router-link>
            <router-link to="/diagnosis" class="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">智能诊断</router-link>
            <router-link to="/knowledge" class="text-sm font-medium text-blue-600">知识库</router-link>
            <router-link to="/chat" class="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">智能问答</router-link>
          </nav>

          <MobileNav />
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
      <section class="mb-6 sm:mb-10">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 class="text-2xl sm:text-3xl font-bold text-slate-900 mb-2">知识库管理</h2>
            <p class="text-sm sm:text-base text-slate-600">
              上传设备维护文档，系统将自动解析并构建向量索引，用于智能诊断检索。
            </p>
          </div>
          <button
            @click="openSearch"
            class="w-full sm:w-auto px-4 py-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors flex items-center justify-center gap-2"
          >
            <span>🔍</span>
            检索测试
          </button>
        </div>
      </section>

      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
        <div class="bg-white rounded-xl p-5 border border-slate-200 flex items-center gap-4">
          <div class="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
            <span class="text-2xl">📚</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-slate-900">{{ documents.length }}</p>
            <p class="text-xs text-slate-500">文档总数</p>
          </div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-slate-200 flex items-center gap-4">
          <div class="w-12 h-12 bg-emerald-50 rounded-lg flex items-center justify-center">
            <span class="text-2xl">✅</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-slate-900">{{ indexedCount }}</p>
            <p class="text-xs text-slate-500">已索引</p>
          </div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-slate-200 flex items-center gap-4">
          <div class="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center">
            <span class="text-2xl">🧩</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-slate-900">{{ totalChunks }}</p>
            <p class="text-xs text-slate-500">文本块数</p>
          </div>
        </div>
        <div class="bg-white rounded-xl p-5 border border-slate-200 flex items-center gap-4">
          <div class="w-12 h-12 bg-amber-50 rounded-lg flex items-center justify-center">
            <span class="text-2xl">⏳</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-slate-900">{{ filterCounts.processing + filterCounts.pending }}</p>
            <p class="text-xs text-slate-500">处理中</p>
          </div>
        </div>
      </div>

      <section
        class="mb-6 sm:mb-8 bg-white rounded-xl border-2 border-dashed transition-all relative"
        :class="isDragging ? 'border-blue-400 bg-blue-50/50' : 'border-slate-300'"
        @dragover="onDragOver"
        @dragleave="onDragLeave"
        @drop="onDrop"
      >
        <div
          class="flex flex-col items-center justify-center py-8 sm:py-12 cursor-pointer px-4"
          @click="triggerFileInput"
        >
          <div
            class="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl flex items-center justify-center mb-3 sm:mb-4 transition-colors"
            :class="isDragging ? 'bg-blue-100' : 'bg-slate-100'"
          >
            <span class="text-2xl sm:text-3xl">{{ isDragging ? '📥' : '📤' }}</span>
          </div>
          <p class="text-base sm:text-lg font-medium text-slate-700 mb-1">
            {{ isDragging ? '松开即可上传文件' : '拖拽文件到此处上传' }}
          </p>
          <p class="text-xs sm:text-sm text-slate-500 mb-3 sm:mb-4 text-center">
            支持 PDF、DOCX、XLSX、CSV、TXT、MD 格式，自动检测编码
          </p>
          <button
            class="w-full sm:w-auto px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-medium rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg shadow-blue-500/25"
            @click.stop="triggerFileInput"
            :disabled="isUploading"
          >
            {{ isUploading ? '上传中...' : '选择文件' }}
          </button>
          <input
            id="file-upload"
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.xlsx,.xls,.csv,.txt,.md"
            class="hidden"
            @change="onFileSelect"
          />
        </div>

        <div v-if="isUploading" class="absolute bottom-0 left-0 right-0 px-4 sm:px-6 pb-3 sm:pb-4">
          <div class="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>上传进度</span>
            <span>{{ uploadProgress }}%</span>
          </div>
          <div class="h-2 bg-slate-200 rounded-full overflow-hidden">
            <div
              class="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-300"
              :style="{ width: uploadProgress + '%' }"
            ></div>
          </div>
        </div>
      </section>

      <section class="bg-white rounded-xl border border-slate-200">
        <div class="p-4 sm:p-5 border-b border-slate-200">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
            <div class="flex items-center gap-2">
              <h3 class="text-base sm:text-lg font-semibold text-slate-900 flex items-center gap-2">
                <span class="text-blue-600">📋</span>
                文档列表
              </h3>
              <span class="text-xs sm:text-sm text-slate-400">（{{ filteredDocuments.length }} 项）</span>
            </div>
            <div class="relative">
              <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">🔍</span>
              <input
                v-model="searchQuery"
                type="text"
                placeholder="搜索文档..."
                class="w-full sm:w-64 pl-10 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400 transition-all"
              />
            </div>
          </div>

          <div class="flex flex-wrap gap-1.5 sm:gap-2 mt-3 sm:mt-4 overflow-x-auto pb-1">
            <button
              v-for="filter in (['all', 'pending', 'processing', 'completed', 'failed'] as const)"
              :key="filter"
              class="px-2.5 sm:px-3 py-1 sm:py-1.5 text-xs font-medium rounded-lg transition-all whitespace-nowrap"
              :class="
                activeFilter === filter
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              "
              @click="activeFilter = filter"
            >
              <template v-if="filter === 'all'">全部 ({{ filterCounts.all }})</template>
              <template v-else-if="filter === 'pending'">待处理 ({{ filterCounts.pending }})</template>
              <template v-else-if="filter === 'processing'">处理中 ({{ filterCounts.processing }})</template>
              <template v-else-if="filter === 'completed'">已完成 ({{ filterCounts.completed }})</template>
              <template v-else>失败 ({{ filterCounts.failed }})</template>
            </button>
          </div>
        </div>

        <div v-if="isLoading" class="py-16 text-center">
          <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p class="text-slate-500 text-sm">加载中...</p>
        </div>

        <div v-else-if="filteredDocuments.length === 0" class="py-16 text-center">
          <span class="text-4xl mb-4 block">📭</span>
          <p class="text-slate-500 text-sm">暂无匹配的文档</p>
        </div>

        <div v-else class="divide-y divide-slate-100">
          <div
            v-for="doc in filteredDocuments"
            :key="doc.id"
            class="flex items-start sm:items-center gap-3 sm:gap-4 px-4 sm:px-5 py-3 sm:py-4 hover:bg-slate-50/60 transition-colors"
          >
            <div class="w-9 h-9 sm:w-10 sm:h-10 bg-blue-50 rounded-lg flex items-center justify-center shrink-0">
              <span class="text-lg sm:text-xl">{{ getFileIcon(doc.file_type) }}</span>
            </div>

            <div class="flex-1 min-w-0">
              <div class="flex flex-wrap items-center gap-1.5 sm:gap-2 mb-1">
                <p class="text-sm font-medium text-slate-900 truncate max-w-[200px] sm:max-w-none">{{ doc.title }}</p>
                <span
                  class="inline-flex items-center gap-1 px-1.5 sm:px-2 py-0.5 text-xs font-medium rounded-full"
                  :class="[statusConfig[doc.status]?.bg, statusConfig[doc.status]?.text]"
                >
                  <span
                    class="w-1.5 h-1.5 rounded-full"
                    :class="statusConfig[doc.status]?.dot"
                  ></span>
                  {{ statusConfig[doc.status]?.label }}
                </span>
                <span v-if="doc.encoding" class="px-1.5 py-0.5 text-xs bg-slate-100 text-slate-500 rounded hidden sm:inline-block">
                  {{ getEncodingLabel(doc.encoding) }}
                </span>
              </div>
              <div class="flex items-center gap-2 sm:gap-3 text-xs text-slate-500">
                <span>{{ doc.file_type }}</span>
                <span class="hidden sm:inline">{{ formatDate(doc.created_at) }}</span>
                <span v-if="doc.chunk_count > 0">{{ doc.chunk_count }}块</span>
              </div>
              <div v-if="doc.status === 'failed' && doc.error_message" class="mt-1 text-xs text-red-500 truncate">
                {{ doc.error_message }}
              </div>
            </div>

            <div class="flex items-center gap-0.5 sm:gap-1 shrink-0">
              <button
                class="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                title="查看详情"
                @click="previewDocument(doc)"
              >
                👁️
              </button>
              <button
                v-if="isEditable(doc.file_type)"
                class="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                title="编辑内容"
                @click="openEditor(doc)"
              >
                ✏️
              </button>
              <button
                v-if="doc.status === 'failed'"
                class="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                title="重新处理"
                @click="reprocessDocument(doc.id)"
              >
                🔄
              </button>
              <button
                class="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="删除文档"
                @click="removeDocument(doc.id)"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>
      </section>
    </main>

    <div
      v-if="showSearchModal"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="showSearchModal = false"
    >
      <div class="bg-white rounded-xl max-w-3xl w-full max-h-[80vh] overflow-hidden">
        <div class="border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-slate-900">知识库检索测试</h3>
          <button @click="showSearchModal = false" class="text-slate-400 hover:text-slate-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-6">
          <div class="flex gap-3 mb-6">
            <input
              v-model="searchText"
              type="text"
              placeholder="输入关键词测试检索效果..."
              class="flex-1 px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              @keyup.enter="performSearch"
            />
            <button
              @click="performSearch"
              :disabled="isSearching || !searchText.trim()"
              class="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {{ isSearching ? '检索中...' : '检索' }}
            </button>
          </div>

          <div v-if="isSearching" class="text-center py-8">
            <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p class="text-slate-500">正在检索知识库...</p>
          </div>

          <div v-else-if="searchResults.length > 0">
            <p class="text-sm text-slate-500 mb-4">找到 {{ searchResults.length }} 条相关结果</p>
            <div class="space-y-3 max-h-[400px] overflow-y-auto">
              <div
                v-for="(result, index) in searchResults"
                :key="index"
                class="p-4 bg-slate-50 rounded-lg"
              >
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs text-slate-400">文档ID: {{ result.document_id }}</span>
                  <span class="text-xs text-blue-600">相似度: {{ (result.score * 100).toFixed(1) }}%</span>
                </div>
                <p class="text-sm text-slate-700">{{ result.content }}</p>
              </div>
            </div>
          </div>

          <div v-else-if="searchText && !isSearching" class="text-center py-8">
            <span class="text-4xl mb-4 block">🔍</span>
            <p class="text-slate-500">未找到相关结果</p>
          </div>

          <div v-else class="text-center py-8">
            <span class="text-4xl mb-4 block">💡</span>
            <p class="text-slate-500">输入关键词测试知识库检索效果</p>
            <p class="text-xs text-slate-400 mt-2">例如：电机故障、轴承磨损、液压系统</p>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="showPreview && selectedDoc"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="closePreview"
    >
      <div class="bg-white rounded-xl max-w-4xl w-full max-h-[85vh] overflow-hidden flex flex-col">
        <div class="border-b border-slate-200 px-6 py-4 flex items-center justify-between shrink-0">
          <h3 class="text-lg font-semibold text-slate-900">文档详情</h3>
          <div class="flex items-center gap-2">
            <button
              v-if="isEditable(selectedDoc.file_type)"
              @click="closePreview(); openEditor(selectedDoc)"
              class="px-3 py-1.5 bg-green-100 text-green-700 text-sm rounded-lg hover:bg-green-200 transition-colors flex items-center gap-1"
            >
              ✏️ 编辑
            </button>
            <button @click="closePreview" class="text-slate-400 hover:text-slate-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto p-6">
          <div class="flex items-center gap-4 mb-6">
            <div class="w-16 h-16 bg-blue-50 rounded-xl flex items-center justify-center">
              <span class="text-3xl">{{ getFileIcon(selectedDoc.file_type) }}</span>
            </div>
            <div>
              <p class="text-xl font-semibold text-slate-900">{{ selectedDoc.title }}</p>
              <p class="text-sm text-slate-500">{{ selectedDoc.file_type }}</p>
            </div>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div>
              <p class="text-xs text-slate-500 mb-1">状态</p>
              <span
                class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full"
                :class="[statusConfig[selectedDoc.status]?.bg, statusConfig[selectedDoc.status]?.text]"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="statusConfig[selectedDoc.status]?.dot"></span>
                {{ statusConfig[selectedDoc.status]?.label }}
              </span>
            </div>
            <div>
              <p class="text-xs text-slate-500 mb-1">编码格式</p>
              <span class="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-700 rounded-full">
                {{ getEncodingLabel(selectedDocEncoding) }}
              </span>
            </div>
            <div>
              <p class="text-xs text-slate-500 mb-1">文本块数</p>
              <p class="text-sm font-medium text-slate-900">{{ selectedDoc.chunk_count }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-500 mb-1">上传时间</p>
              <p class="text-sm font-medium text-slate-900">{{ formatDate(selectedDoc.created_at) }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-500 mb-1">文档ID</p>
              <p class="text-sm font-medium text-slate-900">DOC-{{ String(selectedDoc.id).padStart(4, '0') }}</p>
            </div>
          </div>

          <div v-if="selectedDoc.status === 'failed' && selectedDoc.error_message" class="mb-6">
            <p class="text-xs text-slate-500 mb-2">错误信息</p>
            <p class="text-sm text-red-600 bg-red-50 p-3 rounded-lg">{{ selectedDoc.error_message }}</p>
          </div>

          <div>
            <div class="flex items-center justify-between mb-2">
              <p class="text-sm font-medium text-slate-700">文档内容</p>
              <div class="flex items-center gap-2">
                <span v-if="selectedDocEncoding" class="text-xs text-slate-400">编码: {{ getEncodingLabel(selectedDocEncoding) }}</span>
                <span v-if="isLoadingContent" class="text-xs text-blue-500">加载中...</span>
              </div>
            </div>
            <div v-if="isLoadingContent" class="bg-slate-50 p-4 rounded-lg">
              <div class="animate-pulse space-y-2">
                <div class="h-4 bg-slate-200 rounded w-3/4"></div>
                <div class="h-4 bg-slate-200 rounded w-1/2"></div>
                <div class="h-4 bg-slate-200 rounded w-5/6"></div>
              </div>
            </div>
            <pre v-else class="bg-slate-50 p-4 rounded-lg text-sm text-slate-700 whitespace-pre-wrap font-mono max-h-[300px] overflow-y-auto">{{ selectedDoc.content || '暂无内容' }}</pre>
          </div>
        </div>

        <div class="border-t border-slate-200 px-6 py-4 flex justify-end gap-3 shrink-0">
          <button
            v-if="selectedDoc.status === 'failed'"
            @click="reprocessDocument(selectedDoc.id); closePreview()"
            class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            重新处理
          </button>
          <button
            @click="removeDocument(selectedDoc.id); closePreview()"
            class="px-4 py-2 bg-red-100 text-red-700 text-sm font-medium rounded-lg hover:bg-red-200 transition-colors"
          >
            删除文档
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showEditor && selectedDoc"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="closeEditor"
    >
      <div class="bg-white rounded-xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div class="border-b border-slate-200 px-6 py-4 flex items-center justify-between shrink-0">
          <h3 class="text-lg font-semibold text-slate-900">编辑文档</h3>
          <button @click="closeEditor" class="text-slate-400 hover:text-slate-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6">
          <div class="mb-4">
            <label class="block text-sm font-medium text-slate-700 mb-2">文档标题</label>
            <input
              v-model="editingTitle"
              type="text"
              class="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="请输入文档标题"
            />
          </div>

          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="block text-sm font-medium text-slate-700">文档内容</label>
              <span class="text-xs text-slate-400">编码: {{ getEncodingLabel(selectedDocEncoding) }}</span>
            </div>
            <div v-if="isLoadingContent" class="bg-slate-50 p-4 rounded-lg">
              <div class="animate-pulse space-y-2">
                <div class="h-4 bg-slate-200 rounded w-3/4"></div>
                <div class="h-4 bg-slate-200 rounded w-1/2"></div>
                <div class="h-4 bg-slate-200 rounded w-5/6"></div>
              </div>
            </div>
            <textarea
              v-else
              v-model="editingContent"
              rows="20"
              class="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm resize-y"
              placeholder="请输入文档内容..."
            ></textarea>
          </div>

          <div class="mt-2 flex items-center justify-between text-xs text-slate-500">
            <span>字符数: {{ editingContent.length }}</span>
            <span>保存后将转换为UTF-8编码</span>
          </div>
        </div>

        <div class="border-t border-slate-200 px-6 py-4 flex justify-end gap-3 shrink-0">
          <button
            @click="closeEditor"
            class="px-4 py-2 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors"
          >
            取消
          </button>
          <button
            @click="saveDocument"
            :disabled="isSaving"
            class="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <span v-if="isSaving" class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
            {{ isSaving ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>
    </div>

    <footer class="bg-white border-t border-slate-200 mt-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="text-center text-sm text-slate-500">
          <p>LLM-EFDS - 基于大模型的设备故障诊断系统</p>
          <p class="mt-1">Powered by Vue 3 + FastAPI + RAG</p>
        </div>
      </div>
    </footer>
  </div>
</template>
