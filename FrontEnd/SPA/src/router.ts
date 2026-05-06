import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import HomePage from './pages/HomePage.vue'
import WorkflowPage from './pages/WorkflowPage.vue'
import ExecutePage from './pages/ExecutePage.vue'
import ExecutionDetail from './pages/ExecutionDetail.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: HomePage,
  },
  {
    path: '/execute',
    name: 'execute',
    component: ExecutePage,
  },
  {
    path: '/execute/:id',
    name: 'execution',
    component: ExecutionDetail,
  },
  {
    path: '/workflow',
    name: 'workflow',
    component: WorkflowPage,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
