<template>
  <div class="workflow-overview">
    <el-card class="header-card">
      <h2>工作流概览</h2>
      <p>事件合约预测完整工作流程</p>
    </el-card>

    <el-row :gutter="20" class="workflow-steps">
      <el-col class="step-col" :span="6" v-for="(step, index) in workflowSteps" :key="index">
        <el-card class="step-card" :class="{ active: currentStep === index }">
          <div class="step-number">{{ index + 1 }}</div>
          <h3>{{ step.title }}</h3>
          <p>{{ step.description }}</p>
          <el-button
            type="primary"
            size="small"
            @click="navigateToStep(step.route)"
          >
            进入模块
          </el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="workflow-status" style="display:none">
      <h3>工作流状态</h3>
      <el-steps :active="currentStep" align-center>
        <el-step
          v-for="(step, index) in workflowSteps"
          :key="index"
          :title="step.title"
          :status="getStepStatus(index)"
        />
      </el-steps>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore } from '@/stores/workflow'

const router = useRouter()
const workflowStore = useWorkflowStore()

const currentStep = ref(0)

const workflowSteps = [
  {
    title: '数据下载',
    description: '下载K线数据并保存为pkl格式',
    route: '/data-download'
  },
  {
    title: '特征计算',
    description: '计算Alpha216特征和标签',
    route: '/feature-calculation'
  },
  {
    title: '模型训练',
    description: '使用LightGBM训练预测模型',
    route: '/model-training'
  },
  {
    title: '模型解释',
    description: '使用SHAP生成特征解释图',
    route: '/model-interpretation'
  },
  {
    title: '模型分析',
    description: '使用代理模型筛选关键特征和阈值',
    route: '/model-analysis'
  },
  {
    title: '构建回测',
    description: '根据特征构建回测策略',
    route: '/backtest-construction'
  },
  //{
  //  title: '执行回测',
  //  description: '执行回测并生成报告',
  //  route: '/backtest-execution'
  //}
]

const navigateToStep = (route) => {
  router.push(route)
}

const getStepStatus = (index) => {
  if (index < currentStep.value) return 'success'
  if (index === currentStep.value) return 'process'
  return 'wait'
}
</script>

<style scoped>
.workflow-overview {
  padding: 20px;
}

.header-card {
  margin-bottom: 30px;
  text-align: center;
}

.header-card h2 {
  margin-bottom: 10px;
  color: #303133;
}

.workflow-steps {
  margin-bottom: 30px;
}
.step-col {
  padding: 10px 0;
}

.step-card {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  height: 100%;
}

.step-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.step-card.active {
  border-color: #409eff;
}

.step-number {
  width: 40px;
  height: 40px;
  line-height: 40px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  margin: 0 auto 15px;
  font-size: 20px;
  font-weight: bold;
}

.step-card h3 {
  margin: 15px 0 10px;
  color: #303133;
}

.step-card p {
  color: #909399;
  margin-bottom: 15px;
  min-height: 40px;
}

.workflow-status {
  margin-top: 30px;
}

.workflow-status h3 {
  margin-bottom: 20px;
  text-align: center;
}
</style>
