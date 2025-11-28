import { createRouter, createWebHistory } from 'vue-router'
import WorkflowOverview from '../views/WorkflowOverview.vue'
import DataDownload from '../views/DataDownload.vue'
import FeatureCalculation from '../views/FeatureCalculation.vue'
import ModelTraining from '../views/ModelTraining.vue'
import ModelInterpretation from '../views/ModelInterpretation.vue'
import ModelAnalysis from '../views/ModelAnalysis.vue'
import BacktestConstruction from '../views/BacktestConstruction.vue'
import BacktestExecution from '../views/BacktestExecution.vue'

const routes = [
  {
    path: '/',
    name: 'WorkflowOverview',
    component: WorkflowOverview
  },
  {
    path: '/data-download',
    name: 'DataDownload',
    component: DataDownload
  },
  {
    path: '/feature-calculation',
    name: 'FeatureCalculation',
    component: FeatureCalculation
  },
  {
    path: '/model-training',
    name: 'ModelTraining',
    component: ModelTraining
  },
  {
    path: '/model-interpretation',
    name: 'ModelInterpretation',
    component: ModelInterpretation
  },
  {
    path: '/model-analysis',
    name: 'ModelAnalysis',
    component: ModelAnalysis
  },
  {
    path: '/backtest-construction',
    name: 'BacktestConstruction',
    component: BacktestConstruction
  },
  {
    path: '/backtest-execution',
    name: 'BacktestExecution',
    component: BacktestExecution
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
