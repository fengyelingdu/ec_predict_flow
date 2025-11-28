<template>
  <div class="backtest-execution">
    <el-card>
      <template #header>
        <h2>执行回测</h2>
      </template>

      <el-form :model="form" label-width="120px">
        <el-form-item label="数据文件">
          <el-input v-model="form.dataFile" placeholder="输入数据文件路径" />
        </el-form-item>

        <el-form-item label="策略配置">
          <el-input
            v-model="form.strategyConfig"
            type="textarea"
            :rows="6"
            placeholder="输入策略配置JSON"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="executeBacktest" :loading="loading">
            执行回测
          </el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <div v-if="taskId" class="task-status">
        <h3>任务状态</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">{{ taskId }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType">{{ taskStatus }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="result" class="result-info">
          <h4>回测结果</h4>
          <el-descriptions :column="2" border style="margin-top: 10px;">
            <el-descriptions-item label="总收益率">
              {{ (result.results?.total_return * 100).toFixed(2) }}%
            </el-descriptions-item>
            <el-descriptions-item label="夏普比率">
              {{ result.results?.sharpe_ratio?.toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="最大回撤">
              {{ (result.results?.max_drawdown * 100).toFixed(2) }}%
            </el-descriptions-item>
            <el-descriptions-item label="胜率">
              {{ (result.results?.win_rate * 100).toFixed(2) }}%
            </el-descriptions-item>
            <el-descriptions-item label="总交易次数">
              {{ result.results?.total_trades }}
            </el-descriptions-item>
          </el-descriptions>
          <p style="margin-top: 15px;">报告文件: {{ result.report_file }}</p>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { workflowAPI } from '@/api/workflow'
import { useModuleStatesStore } from '@/stores/moduleStates'
import { useModuleState } from '@/composables/useModuleState'

const moduleStore = useModuleStatesStore()

// 从store恢复状态
const form = ref({ ...moduleStore.backtestExecutionState.form })
const loading = ref(false)
const taskId = ref(moduleStore.backtestExecutionState.taskId)
const taskStatus = ref(moduleStore.backtestExecutionState.taskStatus)
const result = ref(moduleStore.backtestExecutionState.result)

// 使用状态持久化
useModuleState('backtestExecution', {
  form,
  taskId,
  taskStatus,
  result
})

const statusType = computed(() => {
  const statusMap = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failure: 'danger'
  }
  return statusMap[taskStatus.value] || 'info'
})

const executeBacktest = async () => {
  loading.value = true
  try {
    let strategyConfig = {}
    try {
      strategyConfig = JSON.parse(form.value.strategyConfig)
    } catch (e) {
      ElMessage.error('策略配置JSON格式错误')
      loading.value = false
      return
    }

    const response = await workflowAPI.startBacktestExecution({
      strategy_config: strategyConfig,
      data_file: form.value.dataFile
    })

    taskId.value = response.data.task_id
    taskStatus.value = response.data.status
    ElMessage.success('回测任务已启动')

    pollTaskStatus()
  } catch (error) {
    ElMessage.error('启动任务失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const pollTaskStatus = async () => {
  const interval = setInterval(async () => {
    try {
      const response = await workflowAPI.getTaskStatus(taskId.value)
      taskStatus.value = response.data.status

      if (response.data.status === 'success') {
        result.value = response.data.result
        clearInterval(interval)
        ElMessage.success('回测完成')
      } else if (response.data.status === 'failure') {
        clearInterval(interval)
        ElMessage.error('回测失败: ' + response.data.error)
      }
    } catch (error) {
      clearInterval(interval)
      ElMessage.error('查询任务状态失败')
    }
  }, 2000)
}
</script>

<style scoped>
.backtest-execution {
  max-width: 1000px;
}

.task-status {
  margin-top: 20px;
}

.result-info {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.result-info h4 {
  margin-bottom: 10px;
}

.result-info p {
  margin: 5px 0;
}
</style>
