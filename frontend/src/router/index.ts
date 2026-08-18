import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ListeningView from '../views/ListeningView.vue'
import ListeningExamView from '../views/listening/ListeningExamView.vue'
import ListeningReviewView from '../views/listening/ListeningReviewView.vue'
import ListeningMistakesView from '../views/listening/ListeningMistakesView.vue'
import ListeningProfileView from '../views/listening/ListeningProfileView.vue'
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
      path: '/listening/exams/:examId',
      name: 'listening-exam',
      component: ListeningExamView
    },
    {
      path: '/listening/review/:attemptId',
      name: 'listening-review',
      component: ListeningReviewView
    },
    {
      path: '/listening/mistakes',
      name: 'listening-mistakes',
      component: ListeningMistakesView
    },
    {
      path: '/listening/profile',
      name: 'listening-profile',
      component: ListeningProfileView
    },
    {
      path: '/writing',
      name: 'writing',
      component: WritingView
    }
  ]
})

export default router