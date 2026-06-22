<script setup lang="ts">
import { ref, reactive, computed, nextTick, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import apiService from '@/services/api'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  knowledgeRefs?: KnowledgeRef[]
}

interface KnowledgeRef {
  index: number
  content: string
  score: number
  document_id?: number
}

interface Conversation {
  id: number
  title: string
  updatedAt: Date
  messages: ChatMessage[]
}

const route = useRoute()

const sidebarOpen = ref(true)
const inputText = ref('')
const isTyping = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)
const useKnowledge = ref(true)
const activeModelProviderId = ref<number | undefined>(undefined)
const modelProviders = ref<any[]>([])

const conversations = reactive<Conversation[]>([])
const activeConversationId = ref<number | null>(null)

const activeConversation = computed(() => {
  return conversations.find((c) => c.id === activeConversationId.value)
})

const sortedConversations = computed(() => {
  return [...conversations].sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime())
})

const loadConversations = async () => {
  const result = await apiService.getConversations()
  if (result.data) {
    conversations.splice(0, conversations.length)
    for (const c of result.data) {
      conversations.push({
        id: c.id,
        title: c.title || '新对话',
        updatedAt: new Date(c.updated_at || c.created_at),
        messages: [],
      })
    }
    if (conversations.length > 0 && !activeConversationId.value) {
      activeConversationId.value = conversations[0].id
      await loadMessages(conversations[0].id)
    }
  }
}

const loadMessages = async (conversationId: number) => {
  const result = await apiService.getMessages(conversationId)
  if (result.data) {
    const conv = conversations.find((c) => c.id === conversationId)
    if (conv) {
      conv.messages = result.data.map((m: any) => {
        let refs: KnowledgeRef[] = []
        if (m.metadata) {
          try {
            const meta = typeof m.metadata === 'string' ? JSON.parse(m.metadata) : m.metadata
            refs = meta.knowledge_refs || []
          } catch {}
        }
        return {
          id: String(m.id),
          role: m.role,
          content: m.content,
          timestamp: new Date(m.created_at),
          knowledgeRefs: refs.length > 0 ? refs : undefined,
        }
      })
    }
  }
}

const loadModelProviders = async () => {
  const result = await apiService.getActiveModelProviders()
  if (result.data) {
    modelProviders.value = result.data
    const defaultProvider = result.data.find((p: any) => p.is_default)
    if (defaultProvider) {
      activeModelProviderId.value = defaultProvider.id
    }
  }
}

const selectConversation = async (id: number) => {
  activeConversationId.value = id
  const conv = conversations.find((c) => c.id === id)
  if (conv && conv.messages.length === 0) {
    await loadMessages(id)
  }
  nextTick(() => scrollToBottom())
}

const createNewConversation = async () => {
  const result = await apiService.createConversation('新对话', activeModelProviderId.value)
  if (result.data) {
    const newConv: Conversation = {
      id: result.data.id,
      title: '新对话',
      updatedAt: new Date(),
      messages: [],
    }
    conversations.unshift(newConv)
    activeConversationId.value = newConv.id
  }
}

const deleteConversation = async (id: number) => {
  const result = await apiService.deleteConversation(id)
  if (!result.error) {
    const index = conversations.findIndex((c) => c.id === id)
    if (index !== -1) {
      conversations.splice(index, 1)
    }
    if (activeConversationId.value === id) {
      if (conversations.length > 0) {
        activeConversationId.value = conversations[0].id
        await loadMessages(conversations[0].id)
      } else {
        activeConversationId.value = null
      }
    }
  }
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || isTyping.value || !activeConversationId.value) return

  const userMsg: ChatMessage = {
    id: String(Date.now()),
    role: 'user',
    content: text,
    timestamp: new Date(),
  }

  if (!activeConversation.value) return
  activeConversation.value.messages.push(userMsg)
  activeConversation.value.updatedAt = new Date()

  if (activeConversation.value.title === '新对话') {
    activeConversation.value.title = text.slice(0, 20) + (text.length > 20 ? '...' : '')
    apiService.updateConversation(activeConversation.value.id, activeConversation.value.title)
  }

  inputText.value = ''
  nextTick(() => scrollToBottom())

  isTyping.value = true

  const assistantMsg: ChatMessage = {
    id: String(Date.now() + 1),
    role: 'assistant',
    content: '',
    timestamp: new Date(),
  }
  activeConversation.value.messages.push(assistantMsg)

  try {
    const response = await apiService.streamMessage(
      activeConversationId.value,
      text,
      useKnowledge.value,
      activeModelProviderId.value
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      assistantMsg.content = `请求失败: ${errorData.detail || response.status}`
      isTyping.value = false
      return
    }

    const reader = response.body?.getReader()
    if (!reader) {
      assistantMsg.content = '无法读取响应流'
      isTyping.value = false
      return
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const jsonStr = line.slice(6).trim()
        if (!jsonStr) continue

        try {
          const data = JSON.parse(jsonStr)
          if (data.type === 'content') {
            assistantMsg.content += data.content
            nextTick(() => scrollToBottom())
          } else if (data.type === 'knowledge_refs') {
            assistantMsg.knowledgeRefs = data.refs
          } else if (data.type === 'done') {
            assistantMsg.id = String(data.message_id || assistantMsg.id)
          }
        } catch {}
      }
    }
  } catch (error: any) {
    assistantMsg.content = `连接错误: ${error.message || '请检查后端服务是否启动'}`
  } finally {
    isTyping.value = false
    activeConversation.value.updatedAt = new Date()
    nextTick(() => scrollToBottom())
  }
}

const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatDate = (date: Date): string => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  if (diff < 86400000 && now.getDate() === date.getDate()) return '今天'
  if (diff < 172800000) return '昨天'
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const formatMessageContent = (content: string): string => {
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/`(.+?)`/g, '<code class="px-1.5 py-0.5 bg-slate-100 text-blue-700 rounded text-sm font-mono">$1</code>')

  html = html.replace(/^### (.+)$/gm, '<h3 class="text-base font-bold text-slate-800 mt-4 mb-2">$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2 class="text-lg font-bold text-slate-800 mt-4 mb-2">$1</h2>')

  html = html.replace(/^&gt; (.+)$/gm, '<blockquote class="border-l-4 border-blue-400 pl-4 py-2 my-2 bg-blue-50 rounded-r-lg text-sm text-slate-700 italic">$1</blockquote>')

  html = html.replace(/^\| (.+) \|$/gm, (match) => {
    const cells = match
      .replace(/^\| /, '')
      .replace(/ \|$/, '')
      .split(' | ')
    const row = cells.map((c) => `<td class="px-3 py-2 border border-slate-200">${c.trim()}</td>`).join('')
    return `<tr>${row}</tr>`
  })
  html = html.replace(/(<tr>.*<\/tr>\n?)+/g, (match) => {
    return `<table class="w-full border-collapse my-3 text-sm"><tbody>${match}</tbody></table>`
  })

  html = html.replace(/^(\d+)\. (.+)$/gm, '<div class="flex gap-2 my-1"><span class="font-semibold text-blue-600 min-w-[1.25rem]">$1.</span><span>$2</span></div>')
  html = html.replace(/^- (.+)$/gm, '<div class="flex gap-2 my-1"><span class="text-blue-400 min-w-[1rem]">•</span><span>$1</span></div>')

  html = html.replace(/\n\n/g, '</p><p class="my-2">')
  html = html.replace(/\n/g, '<br>')

  return `<p>${html}</p>`
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

watch(inputText, () => {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 120) + 'px'
  }
})

onMounted(async () => {
  await loadModelProviders()
  await loadConversations()
  nextTick(() => scrollToBottom())
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex flex-col">
    <header class="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-50 flex-shrink-0">
      <div class="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <router-link to="/" class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                <span class="text-white text-xl">🔧</span>
              </div>
              <div>
                <h1 class="text-xl font-bold text-slate-900">LLM-EFDS</h1>
                <p class="text-xs text-slate-500">智能问答助手</p>
              </div>
            </router-link>
          </div>
          <nav class="hidden md:flex items-center gap-6">
            <router-link to="/" class="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">首页</router-link>
            <router-link to="/diagnosis" class="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">智能诊断</router-link>
            <router-link to="/knowledge" class="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">知识库</router-link>
            <router-link to="/chat" class="text-sm font-medium text-blue-600">智能问答</router-link>
          </nav>
          <button
            @click="sidebarOpen = !sidebarOpen"
            class="md:hidden p-2 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <svg class="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>
    </header>

    <div class="flex-1 flex overflow-hidden max-w-[1600px] mx-auto w-full">
      <aside
        :class="[
          'bg-white border-r border-slate-200 flex flex-col flex-shrink-0 transition-all duration-300',
          sidebarOpen ? 'w-80' : 'w-0 overflow-hidden',
          'hidden md:flex',
        ]"
      >
        <div class="p-4 border-b border-slate-100">
          <button
            @click="createNewConversation"
            class="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all shadow-sm text-sm font-medium"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            新建对话
          </button>
        </div>

        <div class="flex-1 overflow-y-auto py-2">
          <div
            v-for="conv in sortedConversations"
            :key="conv.id"
            @click="selectConversation(conv.id)"
            :class="[
              'group px-4 py-3 cursor-pointer transition-all mx-2 rounded-lg mb-1',
              conv.id === activeConversationId
                ? 'bg-blue-50 border border-blue-200'
                : 'hover:bg-slate-50 border border-transparent',
            ]"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="flex-1 min-w-0">
                <p
                  :class="[
                    'text-sm font-medium truncate',
                    conv.id === activeConversationId ? 'text-blue-700' : 'text-slate-800',
                  ]"
                >
                  {{ conv.title }}
                </p>
              </div>
              <div class="flex items-center gap-1 flex-shrink-0">
                <span class="text-xs text-slate-400">{{ formatDate(conv.updatedAt) }}</span>
                <button
                  @click.stop="deleteConversation(conv.id)"
                  class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-50 hover:text-red-500 text-slate-300 transition-all"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <div v-if="conversations.length === 0" class="px-4 py-8 text-center">
            <p class="text-sm text-slate-400">暂无对话记录</p>
            <p class="text-xs text-slate-300 mt-1">点击上方按钮开始新对话</p>
          </div>
        </div>
      </aside>

      <div class="flex-1 flex flex-col min-w-0">
        <div class="bg-white/60 backdrop-blur-sm border-b border-slate-200 px-6 py-3 flex items-center justify-between flex-shrink-0">
          <div class="flex items-center gap-3">
            <button
              @click="sidebarOpen = !sidebarOpen"
              class="hidden md:flex p-1.5 rounded-lg hover:bg-slate-100 transition-colors text-slate-400 hover:text-slate-600"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h8m-8 6h16" />
              </svg>
            </button>
            <div>
              <h2 class="text-base font-semibold text-slate-800">{{ activeConversation?.title || '智能问答' }}</h2>
              <p class="text-xs text-slate-400">AI故障诊断助手 · 随时为您解答</p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <select
              v-if="modelProviders.length > 0"
              v-model="activeModelProviderId"
              class="px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option :value="undefined">默认模型</option>
              <option v-for="p in modelProviders" :key="p.id" :value="p.id">{{ p.name }} ({{ p.model_name }})</option>
            </select>
            <label class="flex items-center gap-1.5 text-xs text-slate-500 cursor-pointer">
              <input type="checkbox" v-model="useKnowledge" class="w-3.5 h-3.5 text-blue-600 rounded" />
              知识库
            </label>
            <span class="flex items-center gap-1.5 text-xs text-green-600 bg-green-50 px-2.5 py-1 rounded-full">
              <span class="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
              在线
            </span>
          </div>
        </div>

        <div ref="messagesContainer" class="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          <div v-if="!activeConversation || activeConversation.messages.length === 0" class="flex flex-col items-center justify-center h-full text-center">
            <div class="w-20 h-20 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl flex items-center justify-center mb-6">
              <span class="text-4xl">🤖</span>
            </div>
            <h3 class="text-xl font-bold text-slate-800 mb-2">欢迎使用智能问答助手</h3>
            <p class="text-sm text-slate-500 max-w-md mb-8">
              我是基于大语言模型的设备故障诊断助手，可以帮您分析设备故障原因、提供维修建议。回答将结合知识库内容给出专业建议。
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
              <button
                v-for="hint in [
                  '电机运行时异常振动怎么办？',
                  '液压系统压力不足如何排查？',
                  '变频器频繁报警的原因',
                  'PLC通信故障诊断方法',
                ]"
                :key="hint"
                @click="inputText = hint"
                class="text-left px-4 py-3 bg-white border border-slate-200 rounded-xl hover:border-blue-300 hover:shadow-sm transition-all text-sm text-slate-600 hover:text-blue-600"
              >
                <span class="text-blue-400 mr-1">💡</span>
                {{ hint }}
              </button>
            </div>
          </div>

          <template v-if="activeConversation">
            <template v-for="msg in activeConversation.messages" :key="msg.id">
              <div v-if="msg.role === 'user'" class="flex justify-end gap-3">
                <div class="max-w-[75%]">
                  <div class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-3 rounded-2xl rounded-br-md shadow-sm">
                    <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ msg.content }}</p>
                  </div>
                  <p class="text-xs text-slate-400 mt-1.5 text-right">{{ formatTime(msg.timestamp) }}</p>
                </div>
                <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <span class="text-white text-sm font-medium">U</span>
                </div>
              </div>

              <div v-else class="flex gap-3">
                <div class="w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <span class="text-white text-sm">🤖</span>
                </div>
                <div class="max-w-[80%]">
                  <div class="bg-white border border-slate-200 px-5 py-4 rounded-2xl rounded-bl-md shadow-sm">
                    <div v-if="!msg.content && isTyping && msg === activeConversation.messages[activeConversation.messages.length - 1]" class="flex items-center gap-2">
                      <div class="flex gap-1">
                        <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                        <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                        <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
                      </div>
                      <span class="text-xs text-slate-400 ml-1">AI正在分析中...</span>
                    </div>
                    <div v-else class="text-sm text-slate-700 leading-relaxed chat-content" v-html="formatMessageContent(msg.content)"></div>

                    <div v-if="msg.knowledgeRefs && msg.knowledgeRefs.length > 0" class="mt-3 pt-3 border-t border-slate-100">
                      <p class="text-xs font-medium text-slate-500 mb-2">📚 知识库参考</p>
                      <div class="space-y-1.5">
                        <div
                          v-for="ref in msg.knowledgeRefs"
                          :key="ref.index"
                          class="text-xs bg-slate-50 rounded-lg px-3 py-2"
                        >
                          <div class="flex items-center justify-between mb-1">
                            <span class="font-medium text-slate-600">参考{{ ref.index }}</span>
                            <span class="text-blue-600 font-mono">相似度: {{ (ref.score * 100).toFixed(1) }}%</span>
                          </div>
                          <p class="text-slate-500 line-clamp-2">{{ ref.content }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <p class="text-xs text-slate-400 mt-1.5">{{ formatTime(msg.timestamp) }}</p>
                </div>
              </div>
            </template>
          </template>
        </div>

        <div class="bg-white/80 backdrop-blur-sm border-t border-slate-200 px-6 py-4 flex-shrink-0">
          <div class="flex items-end gap-3 max-w-4xl mx-auto">
            <div class="flex-1 relative">
              <textarea
                ref="inputRef"
                v-model="inputText"
                @keydown="handleKeydown"
                rows="1"
                placeholder="描述设备故障现象，按 Enter 发送，Shift+Enter 换行..."
                :disabled="!activeConversation"
                class="w-full px-4 py-3 pr-12 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm text-slate-700 placeholder-slate-400 transition-all disabled:opacity-50"
                style="max-height: 120px"
              ></textarea>
            </div>
            <button
              @click="sendMessage"
              :disabled="!inputText.trim() || isTyping || !activeConversation"
              class="p-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
            >
              <svg v-if="!isTyping" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
              <svg v-else class="w-5 h-5 animate-spin" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </button>
          </div>
          <p class="text-xs text-slate-400 text-center mt-2">
            AI 助手可能会产生不准确的信息，请结合实际情况判断。重要决策请咨询专业人员。
          </p>
        </div>
      </div>
    </div>

    <div
      v-if="sidebarOpen"
      class="fixed inset-0 bg-black/30 z-40 md:hidden"
      @click="sidebarOpen = false"
    ></div>
    <transition name="slide">
      <aside
        v-if="sidebarOpen"
        class="fixed top-0 left-0 bottom-0 w-80 bg-white z-50 flex flex-col shadow-xl md:hidden"
      >
        <div class="p-4 border-b border-slate-100 flex items-center justify-between">
          <h3 class="text-base font-semibold text-slate-800">对话历史</h3>
          <button @click="sidebarOpen = false" class="p-1.5 rounded-lg hover:bg-slate-100 transition-colors">
            <svg class="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-4 border-b border-slate-100">
          <button
            @click="createNewConversation(); sidebarOpen = false"
            class="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all text-sm font-medium"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            新建对话
          </button>
        </div>

        <div class="flex-1 overflow-y-auto py-2">
          <div
            v-for="conv in sortedConversations"
            :key="conv.id"
            @click="selectConversation(conv.id); sidebarOpen = false"
            :class="[
              'group px-4 py-3 cursor-pointer transition-all mx-2 rounded-lg mb-1',
              conv.id === activeConversationId
                ? 'bg-blue-50 border border-blue-200'
                : 'hover:bg-slate-50 border border-transparent',
            ]"
          >
            <p :class="['text-sm font-medium truncate', conv.id === activeConversationId ? 'text-blue-700' : 'text-slate-800']">
              {{ conv.title }}
            </p>
          </div>
        </div>
      </aside>
    </transition>
  </div>
</template>

<style scoped>
.chat-content :deep(p) {
  margin: 0.375rem 0;
}

.chat-content :deep(strong) {
  font-weight: 600;
  color: #1e293b;
}

.chat-content :deep(h2),
.chat-content :deep(h3) {
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.chat-content :deep(blockquote) {
  margin: 0.5rem 0;
}

.chat-content :deep(code) {
  font-size: 0.8125rem;
}

.chat-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.75rem 0;
}

.chat-content :deep(td) {
  padding: 0.375rem 0.75rem;
  border: 1px solid #e2e8f0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%);
}

textarea {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 transparent;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background-color: #94a3b8;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
