<template>
  <div class="model-training">
    <el-row :gutter="20">
      <!-- 左侧：训练表单 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <h2>模型训练</h2>
          </template>

          <el-form :model="form" label-width="120px">
            <el-form-item label="特征文件">
              <el-select
                v-model="form.featuresFile"
                placeholder="选择特征文件"
                filterable
                style="width: 100%"
                @change="onFeaturesFileChange"
              >
                <el-option
                  v-for="file in featuresFiles"
                  :key="file.filename"
                  :label="file.filename"
                  :value="file.filename"
                >
                  <span>{{ file.filename }}</span>
                  <span style="float: right; color: #8492a6; font-size: 13px">
                    {{ file.size_mb }}MB
                  </span>
                </el-option>
              </el-select>
            </el-form-item>

            <el-form-item label="标签文件">
              <el-select
                v-model="form.labelsFile"
                placeholder="选择标签文件"
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="file in labelsFiles"
                  :key="file.filename"
                  :label="file.filename"
                  :value="file.filename"
                >
                  <span>{{ file.filename }}</span>
                  <span style="float: right; color: #8492a6; font-size: 13px">
                    {{ file.size_mb }}MB
                  </span>
                </el-option>
              </el-select>
            </el-form-item>

            <el-form-item label="迭代次数">
              <el-input-number v-model="form.numBoostRound" :min="100" :max="2000" :step="100" />
              <span style="margin-left: 10px; color: #909399; font-size: 12px;">
                Boosting迭代次数，越大越精确但训练时间越长
              </span>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="startTraining"
                :loading="loading"
                :disabled="!form.featuresFile || !form.labelsFile"
              >
                开始训练
              </el-button>
              <el-button @click="loadProcessedFiles" :icon="Refresh">刷新文件列表</el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <div v-if="taskId" class="task-status">
            <h3>训练任务状态</h3>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="任务ID">{{ taskId }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="statusType">{{ taskStatus }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="进度" v-if="progress !== null">
                <el-progress :percentage="Math.round(progress)" />
              </el-descriptions-item>
              <el-descriptions-item label="当前状态" v-if="statusMessage">
                {{ statusMessage }}
              </el-descriptions-item>
            </el-descriptions>

            <div v-if="result" class="result-info">
              <h4>训练结果</h4>
              <el-descriptions :column="2" border style="margin-top: 10px;">
                <el-descriptions-item label="模型文件">{{ result.model_file }}</el-descriptions-item>
                <el-descriptions-item label="特征数量">{{ result.num_features }}</el-descriptions-item>
                <el-descriptions-item label="训练样本">{{ result.train_samples }}</el-descriptions-item>
                <el-descriptions-item label="迭代次数">{{ result.num_boost_round }}</el-descriptions-item>
              </el-descriptions>

              <div v-if="result.top20_importance" style="margin-top: 20px;">
                <h5>Top 20 特征重要性</h5>
                <el-table
                  :data="importanceTableData"
                  style="width: 100%"
                  max-height="400"
                  size="small"
                >
                  <el-table-column prop="rank" label="排名" width="60" />
                  <el-table-column prop="feature" label="特征" show-overflow-tooltip />
                  <el-table-column prop="importance" label="重要性" width="120">
                    <template #default="scope">
                      {{ scope.row.importance.toFixed(2) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="重要性条" width="200">
                    <template #default="scope">
                      <el-progress
                        :percentage="scope.row.percentage"
                        :show-text="false"
                        :stroke-width="12"
                      />
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <div style="margin-top: 20px;">
                <el-button type="primary" @click="goToInterpretation" :icon="TrendCharts">
                  进入SHAP解释
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：文件列表 -->
      <el-col :span="10">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="已处理数据文件" name="processed">
            <el-card>
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <h3>已处理数据文件</h3>
                  <el-button @click="loadProcessedFiles" :icon="Refresh" circle size="small" />
                </div>
              </template>

              <el-collapse v-model="activeCollapse">
                <el-collapse-item title="特征文件" name="features">
                  <el-table :data="featuresFiles" style="width: 100%" max-height="300" size="small">
                    <el-table-column prop="filename" label="文件名" show-overflow-tooltip />
                    <el-table-column prop="size_mb" label="大小(MB)" width="80" />
                  </el-table>
                </el-collapse-item>

                <el-collapse-item title="标签文件" name="labels">
                  <el-table :data="labelsFiles" style="width: 100%" max-height="300" size="small">
                    <el-table-column prop="filename" label="文件名" show-overflow-tooltip />
                    <el-table-column prop="size_mb" label="大小(MB)" width="80" />
                  </el-table>
                </el-collapse-item>
              </el-collapse>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="已训练模型" name="models">
            <el-card>
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <h3>已训练模型</h3>
                  <el-button @click="loadModelFiles" :icon="Refresh" circle size="small" />
                </div>
              </template>

              <el-table :data="modelFiles" style="width: 100%" max-height="500" size="small">
                <el-table-column prop="filename" label="模型文件" show-overflow-tooltip />
                <el-table-column prop="size_mb" label="大小(MB)" width="80" />
                <el-table-column prop="modified_time" label="训练时间" width="150" />
                <el-table-column label="操作" width="100">
                  <template #default="scope">
                    <el-button size="small" type="primary" @click="useModel(scope.row)">
                      使用
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-tab-pane>
        </el-tabs>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, TrendCharts } from '@element-plus/icons-vue'
import { workflowAPI } from '@/api/workflow'
import { useModuleStatesStore } from '@/stores/moduleStates'
import { useModuleState } from '@/composables/useModuleState'

const router = useRouter()
const moduleStore = useModuleStatesStore()

// 从store恢复状态
const form = ref({ ...moduleStore.modelTrainingState.form })
const loading = ref(false)
const taskId = ref(moduleStore.modelTrainingState.taskId)
const taskStatus = ref(moduleStore.modelTrainingState.taskStatus)
const progress = ref(moduleStore.modelTrainingState.progress)
const statusMessage = ref(moduleStore.modelTrainingState.statusMessage)
const result = ref(moduleStore.modelTrainingState.result)

const processedFiles = ref([...moduleStore.modelTrainingState.processedFiles])
const modelFiles = ref([...moduleStore.modelTrainingState.modelFiles])
const activeTab = ref(moduleStore.modelTrainingState.activeTab)
const activeCollapse = ref([...moduleStore.modelTrainingState.activeCollapse])

// 使用状态持久化
useModuleState('modelTraining', {
  form,
  taskId,
  taskStatus,
  progress,
  statusMessage,
  result,
  processedFiles,
  modelFiles,
  activeTab,
  activeCollapse
})

// 过滤特征文件
const featuresFiles = computed(() => {
  return processedFiles.value.filter(file => file.filename.includes('_features_'))
})

// 过滤标签文件
const labelsFiles = computed(() => {
  return processedFiles.value.filter(file => file.filename.includes('_labels_'))
})

// 格式化特征重要性为表格数据
const importanceTableData = computed(() => {
  if (!result.value?.top20_importance) return []

  const entries = Object.entries(result.value.top20_importance)
  const maxImportance = Math.max(...entries.map(([, v]) => v))

  return entries.map(([feature, importance], index) => ({
    rank: index + 1,
    feature,
    importance,
    percentage: (importance / maxImportance) * 100
  }))
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

onMounted(() => {
  loadProcessedFiles()
  loadModelFiles()
})

// 当选择特征文件时，尝试自动匹配标签文件
const onFeaturesFileChange = () => {
  if (!form.value.featuresFile) return

  // 从特征文件名中提取基础名称
  // 例如: ETHUSDT_2024-01-01_2024-12-31_features_alpha216.pkl
  // 提取: ETHUSDT_2024-01-01_2024-12-31
  const baseName = form.value.featuresFile
    .replace('_features', '')
    .replace(/_alpha\d+/, '')
    .replace('.pkl', '')

  // 尝试找到匹配的标签文件
  const matchedLabel = labelsFiles.value.find(file =>
    file.filename.startsWith(baseName) && file.filename.includes('_labels_')
  )

  if (matchedLabel) {
    form.value.labelsFile = matchedLabel.filename
    ElMessage.info(`自动匹配标签文件: ${matchedLabel.filename}`)
  }
}

const startTraining = async () => {
  if (!form.value.featuresFile) {
    ElMessage.warning('请选择特征文件')
    return
  }

  if (!form.value.labelsFile) {
    ElMessage.warning('请选择标签文件')
    return
  }

  loading.value = true
  try {
    const response = await workflowAPI.startModelTraining({
      features_file: form.value.featuresFile,
      labels_file: form.value.labelsFile,
      num_boost_round: form.value.numBoostRound
    })

    taskId.value = response.data.task_id
    taskStatus.value = response.data.status
    progress.value = 0
    statusMessage.value = ''
    result.value = null
    ElMessage.success('模型训练任务已启动')

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

      if (response.data.result) {
        progress.value = response.data.result.progress || progress.value
        statusMessage.value = response.data.result.status || ''
      }

      if (response.data.status === 'success') {
        result.value = response.data.result
        progress.value = 100
        clearInterval(interval)
        ElMessage.success('模型训练完成')
        loadModelFiles()  // 刷新模型列表
      } else if (response.data.status === 'failure') {
        clearInterval(interval)
        ElMessage.error('模型训练失败: ' + response.data.error)
      }
    } catch (error) {
      clearInterval(interval)
      ElMessage.error('查询任务状态失败')
    }
  }, 2000)
}

const loadProcessedFiles = async () => {
  try {
    const response = await workflowAPI.listDataFiles('processed')
    processedFiles.value = response.data.files
  } catch (error) {
    ElMessage.error('加载处理文件列表失败')
  }
}

const loadModelFiles = async () => {
  try {
    const response = await workflowAPI.listDataFiles('models')
    modelFiles.value = response.data.files || []
  } catch (error) {
    console.error('加载模型文件列表失败', error)
  }
}

const useModel = (model) => {
  // 跳转到模型解释页面
  router.push({
    name: 'ModelInterpretation',
    query: { model_file: model.filename }
  })
}

const goToInterpretation = () => {
  if (result.value?.model_file) {
    router.push({
      name: 'ModelInterpretation',
      query: { model_file: result.value.model_file }
    })
  }
}
</script>

<style scoped>
.model-training {
  padding: 20px;
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

.result-info h5 {
  margin-top: 15px;
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: bold;
}

.result-info p {
  margin: 5px 0;
}
</style>
