import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../pages/HomePage.vue'
import WorkflowPage from '../pages/WorkflowPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomePage,
    },
    {
      path: '/workflow',
      name: 'workflow',
      component: WorkflowPage,
    },
  ],
})

export default router
