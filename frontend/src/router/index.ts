import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/pages/HomePage.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomePage,
    meta: { requiresAuth: true },
  },
  {
    path: '/diagnosis',
    name: 'diagnosis',
    component: () => import('@/pages/DiagnosisPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/knowledge',
    name: 'knowledge',
    component: () => import('@/pages/KnowledgePage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/cases',
    name: 'cases',
    component: () => import('@/pages/CasesPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/devices',
    name: 'devices',
    component: () => import('@/pages/DevicesPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/issues',
    name: 'issues',
    component: () => import('@/pages/IssuesPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('@/pages/ChatPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/chat/:id',
    name: 'chat-detail',
    component: () => import('@/pages/ChatPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/system',
    name: 'system',
    component: () => import('@/pages/SystemPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { guest: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    next({ name: 'login' })
  } else if (to.meta.guest && token) {
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
