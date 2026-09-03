import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ListeningView from '../views/ListeningView.vue'
import ListeningExamView from '../views/listening/ListeningExamView.vue'
import ListeningReviewView from '../views/listening/ListeningReviewView.vue'
import ListeningMistakesView from '../views/listening/ListeningMistakesView.vue'
import ListeningProfileView from '../views/listening/ListeningProfileView.vue'
import ListeningExpressionsView from '../views/listening/ListeningExpressionsView.vue'
import ExpressionTrainView from '../views/listening/ExpressionTrainView.vue'
import TeacherExpressionsView from '../views/listening/TeacherExpressionsView.vue'
import TeacherExpressionDetailView from '../views/listening/TeacherExpressionDetailView.vue'
import TeacherCorpusView from '../views/listening/TeacherCorpusView.vue'
import TeacherCorpusAssetView from '../views/listening/TeacherCorpusAssetView.vue'
import CorpusClipsView from '../views/listening/CorpusClipsView.vue'
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
      path: '/listening/v2/exams/:examId',
      name: 'listening-exam-v2',
      component: () => import('../views/listening/ListeningExamV2View.vue')
    },
    {
      path: '/listening/v2/practice/:materialId',
      name: 'listening-practice-v2',
      component: () => import('../views/listening/ListeningPracticeV2View.vue')
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
      path: '/listening/corpus',
      name: 'listening-corpus',
      component: CorpusClipsView
    },
    {
      path: '/listening/expressions',
      name: 'listening-expressions',
      component: ListeningExpressionsView
    },
    {
      path: '/listening/expressions/:expressionId',
      name: 'expression-train',
      component: ExpressionTrainView
    },
    {
      path: '/listening/teacher/expressions',
      name: 'teacher-expressions',
      component: TeacherExpressionsView
    },
    {
      path: '/listening/teacher/expressions/:expressionId',
      name: 'teacher-expression-detail',
      component: TeacherExpressionDetailView
    },
    {
      path: '/listening/teacher/corpus',
      name: 'teacher-corpus',
      component: TeacherCorpusView
    },
    {
      path: '/listening/teacher/corpus/:assetId',
      name: 'teacher-corpus-asset',
      component: TeacherCorpusAssetView
    },
    {
      path: '/listening/lexicon',
      name: 'listening-lexicon',
      component: () => import('../views/listening/AuralLexiconView.vue')
    },
    {
      path: '/listening/pacing/:examId',
      name: 'listening-strict-pacing',
      component: () => import('../views/listening/ListeningStrictPacingView.vue')
    },
    {
      path: '/listening/stem-bank',
      name: 'listening-stem-bank',
      component: () => import('../views/listening/StemBankView.vue')
    },
    {
      path: '/listening/dashboard',
      name: 'listening-dashboard',
      component: () => import('../views/listening/ListeningDashboardView.vue')
    },
    {
      path: '/writing',
      name: 'writing',
      component: WritingView
    }
  ]
})

export default router