const API_BASE_URL = 'http://localhost:8000'

interface ApiResponse<T> {
  data?: T
  error?: string
}

class ApiService {
  private token: string | null = null

  setToken(token: string) {
    this.token = token
    localStorage.setItem('token', token)
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('token')
    }
    return this.token
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const headers: HeadersInit = {
      ...options.headers,
    }

    const token = this.getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json'
    }

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        return { error: errorData.detail || `请求失败: ${response.status}` }
      }

      const data = await response.json()
      return { data }
    } catch (error) {
      return { error: `网络错误: ${error}` }
    }
  }

  async login(username: string, password: string) {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)

    return this.request<{ access_token: string; token_type: string }>(
      '/api/users/login',
      {
        method: 'POST',
        body: formData.toString(),
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      }
    )
  }

  async register(username: string, email: string, password: string) {
    return this.request('/api/users/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    })
  }

  async getCurrentUser() {
    return this.request<{ id: number; username: string; email: string; is_active: boolean; role: string }>(
      '/api/users/me'
    )
  }

  clearToken() {
    this.token = null
    localStorage.removeItem('token')
  }

  async getDocuments(skip = 0, limit = 100) {
    return this.request<{ documents: any[]; total: number }>(
      `/api/knowledge/documents?skip=${skip}&limit=${limit}`
    )
  }

  async getDocument(docId: number) {
    return this.request<any>(`/api/knowledge/documents/${docId}`)
  }

  async getDocumentContent(docId: number) {
    return this.request<{ id: number; content: string; title: string; encoding?: string }>(
      `/api/knowledge/documents/${docId}/content`
    )
  }

  async updateDocumentContent(docId: number, content: string) {
    return this.request<any>(`/api/knowledge/documents/${docId}/content`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    })
  }

  async updateDocument(docId: number, data: { title?: string; content?: string }) {
    return this.request<any>(`/api/knowledge/documents/${docId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async uploadDocument(file: File, title?: string) {
    const formData = new FormData()
    formData.append('file', file)
    if (title) {
      formData.append('title', title)
    }

    return this.request<any>('/api/knowledge/upload', {
      method: 'POST',
      body: formData,
    })
  }

  async deleteDocument(docId: number) {
    return this.request(`/api/knowledge/documents/${docId}`, {
      method: 'DELETE',
    })
  }

  async reprocessDocument(docId: number) {
    return this.request<any>(`/api/knowledge/documents/${docId}/reprocess`, {
      method: 'POST',
    })
  }

  async searchDocuments(query: string) {
    return this.request<{ documents: any[] }>(
      `/api/knowledge/search?query=${encodeURIComponent(query)}`
    )
  }

  async diagnose(faultPhenomenon: string, deviceId?: number) {
    return this.request<any>('/api/diagnosis/diagnose', {
      method: 'POST',
      body: JSON.stringify({
        fault_phenomenon: faultPhenomenon,
        device_id: deviceId,
      }),
    })
  }

  async chat(query: string, conversationId?: number) {
    return this.request<{ conversation_id: number; response: string }>(
      '/api/diagnosis/chat',
      {
        method: 'POST',
        body: JSON.stringify({
          query,
          conversation_id: conversationId,
        }),
      }
    )
  }

  async createConversation(title?: string, modelProviderId?: number) {
    return this.request<any>('/api/chat/conversations', {
      method: 'POST',
      body: JSON.stringify({ title, model_provider_id: modelProviderId }),
    })
  }

  async getConversations() {
    return this.request<any[]>('/api/chat/conversations')
  }

  async getMessages(conversationId: number) {
    return this.request<any[]>(`/api/chat/conversations/${conversationId}/messages`)
  }

  async sendMessage(conversationId: number, content: string, useKnowledge = true, modelProviderId?: number) {
    return this.request<any>(`/api/chat/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, use_knowledge: useKnowledge, model_provider_id: modelProviderId }),
    })
  }

  async streamMessage(conversationId: number, content: string, useKnowledge = true, modelProviderId?: number): Promise<Response> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    const token = this.getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return fetch(`${API_BASE_URL}/api/chat/conversations/${conversationId}/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ content, use_knowledge: useKnowledge, model_provider_id: modelProviderId }),
    })
  }

  async deleteConversation(conversationId: number) {
    return this.request(`/api/chat/conversations/${conversationId}`, {
      method: 'DELETE',
    })
  }

  async updateConversation(conversationId: number, title: string) {
    return this.request<any>(`/api/chat/conversations/${conversationId}`, {
      method: 'PUT',
      body: JSON.stringify({ title }),
    })
  }

  async createDevice(deviceData: any) {
    return this.request<any>('/api/devices/', {
      method: 'POST',
      body: JSON.stringify(deviceData),
    })
  }

  async getDevices(skip = 0, limit = 100) {
    return this.request<any[]>(`/api/devices/?skip=${skip}&limit=${limit}`)
  }

  async getDevice(deviceId: number) {
    return this.request<any>(`/api/devices/${deviceId}`)
  }

  async updateDevice(deviceId: number, deviceData: any) {
    return this.request<any>(`/api/devices/${deviceId}`, {
      method: 'PUT',
      body: JSON.stringify(deviceData),
    })
  }

  async deleteDevice(deviceId: number) {
    return this.request(`/api/devices/${deviceId}`, {
      method: 'DELETE',
    })
  }

  async getDeviceStats() {
    return this.request<any>('/api/devices/stats/summary')
  }

  async getMaintenanceRecords(deviceId: number, skip = 0, limit = 50) {
    return this.request<any[]>(`/api/maintenance/device/${deviceId}?skip=${skip}&limit=${limit}`)
  }

  async createMaintenanceRecord(data: any) {
    return this.request<any>('/api/maintenance/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateMaintenanceRecord(recordId: number, data: any) {
    return this.request<any>(`/api/maintenance/${recordId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteMaintenanceRecord(recordId: number) {
    return this.request(`/api/maintenance/${recordId}`, {
      method: 'DELETE',
    })
  }

  async getIssues(skip = 0, limit = 50, status?: string, severity?: string, department?: string) {
    let url = `/api/issues/?skip=${skip}&limit=${limit}`
    if (status) url += `&status=${status}`
    if (severity) url += `&severity=${severity}`
    if (department) url += `&department=${department}`
    return this.request<any[]>(url)
  }

  async getDeviceIssues(deviceId: number) {
    return this.request<any[]>(`/api/issues/device/${deviceId}`)
  }

  async getIssue(issueId: number) {
    return this.request<any>(`/api/issues/${issueId}`)
  }

  async createIssue(data: any) {
    return this.request<any>('/api/issues/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateIssue(issueId: number, data: any) {
    return this.request<any>(`/api/issues/${issueId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteIssue(issueId: number) {
    return this.request(`/api/issues/${issueId}`, {
      method: 'DELETE',
    })
  }

  async addIssueProgress(issueId: number, data: any) {
    return this.request<any>(`/api/issues/${issueId}/progress`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getIssueProgress(issueId: number) {
    return this.request<any[]>(`/api/issues/${issueId}/progress`)
  }

  async getIssueStats() {
    return this.request<any>('/api/issues/stats/summary')
  }

  async getDepartments() {
    return this.request<string[]>('/api/issues/departments')
  }

  async getDepartmentStats() {
    return this.request<any[]>('/api/issues/department-stats')
  }

  async getIssuesByDepartment() {
    return this.request<any>('/api/issues/by-department')
  }

  async getUsers(skip = 0, limit = 100) {
    return this.request<any[]>(`/api/users/list?skip=${skip}&limit=${limit}`)
  }

  async updateUser(userId: number, data: { email?: string; role?: string; is_active?: boolean }) {
    return this.request<any>(`/api/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteUser(userId: number) {
    return this.request(`/api/users/${userId}`, {
      method: 'DELETE',
    })
  }

  async updateUserPassword(userId: number, newPassword: string) {
    return this.request(`/api/users/${userId}/password`, {
      method: 'PUT',
      body: JSON.stringify({ new_password: newPassword }),
    })
  }

  async getSystemSettings() {
    return this.request<any>('/api/system/settings')
  }

  async updateSystemSettings(settings: any) {
    return this.request<any>('/api/system/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    })
  }

  async getOperationLogs(skip = 0, limit = 50) {
    return this.request<any[]>(`/api/system/logs?skip=${skip}&limit=${limit}`)
  }

  async getModelProviders() {
    return this.request<any[]>('/api/models/')
  }

  async getActiveModelProviders() {
    return this.request<any[]>('/api/models/active')
  }

  async getModelProvider(providerId: number) {
    return this.request<any>(`/api/models/${providerId}`)
  }

  async createModelProvider(data: any) {
    return this.request<any>('/api/models/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateModelProvider(providerId: number, data: any) {
    return this.request<any>(`/api/models/${providerId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteModelProvider(providerId: number) {
    return this.request(`/api/models/${providerId}`, {
      method: 'DELETE',
    })
  }

  async toggleModelProvider(providerId: number) {
    return this.request<any>(`/api/models/${providerId}/toggle`, {
      method: 'POST',
    })
  }

  async setDefaultModelProvider(providerId: number) {
    return this.request<any>(`/api/models/${providerId}/set-default`, {
      method: 'POST',
    })
  }

  async getSupportedProviders() {
    return this.request<any>('/api/models/providers/supported')
  }

  async searchKnowledge(query: string) {
    return this.request<any>(`/api/knowledge/search?query=${encodeURIComponent(query)}`)
  }
}

export const apiService = new ApiService()
export default apiService
