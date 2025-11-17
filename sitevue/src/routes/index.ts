import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Task from '../views/Task.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home
    },
    {
      path: '/task',
      name: 'Task',
      component: Task
    }
  ]
})

export default router