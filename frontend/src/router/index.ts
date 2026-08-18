import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ListeningView from '../views/ListeningView.vue'
import WritingView from '../views/WritingView.vue'

const router = createRouter({
  history: createWebHistory(),

  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/listening',
      name: 'listening',
      component: ListeningView
    },
    {
      path: '/writing',
      name: 'writing',
      component: WritingView
    }
  ]
})

export default router