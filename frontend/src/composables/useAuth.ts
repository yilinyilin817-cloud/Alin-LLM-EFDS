import { ref, computed } from 'vue'
import apiService from '@/services/api'

interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  role: string
}

const currentUser = ref<User | null>(null)
const token = ref<string | null>(localStorage.getItem('token'))
const isLoading = ref(false)

export function useAuth() {
  const isAuthenticated = computed(() => !!token.value)

  const login = async (username: string, password: string) => {
    const result = await apiService.login(username, password)
    if (result.error) {
      return { error: result.error }
    }
    if (result.data) {
      token.value = result.data.access_token
      apiService.setToken(result.data.access_token)
      await fetchCurrentUser()
    }
    return { data: result.data }
  }

  const register = async (username: string, email: string, password: string) => {
    const result = await apiService.register(username, email, password)
    if (result.error) {
      return { error: result.error }
    }
    return { data: result.data }
  }

  const fetchCurrentUser = async () => {
    if (!token.value) return
    isLoading.value = true
    try {
      const result = await apiService.getCurrentUser()
      if (result.data) {
        currentUser.value = result.data as User
      } else if (result.error) {
        logout()
      }
    } finally {
      isLoading.value = false
    }
  }

  const logout = () => {
    token.value = null
    currentUser.value = null
    apiService.clearToken()
  }

  const initAuth = async () => {
    if (token.value) {
      apiService.setToken(token.value)
      await fetchCurrentUser()
    }
  }

  return {
    currentUser,
    token,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    fetchCurrentUser,
    initAuth,
  }
}
