<template>
  <div class="model-analysis">
    <el-row :gutter="20">
      <!-- 左侧：参数配置和任务控制 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <h2>模型分析 (代理模型)</h2>
          </template>

          <el-form :model="form" label-width="140px">
            <el-form-item label="模型文件">
              <el-select
                v-model="form.modelFile"
                placeholder="选择模型文件"
                filterable
                style="width: 100%"
                @change="loadShapMetadata"
              >
                <el-option
                  v-for="file in modelFiles"
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

            <el-form-item label="选择关键特征">
              <el-row :gutter="20" style="width: 100%;">
                <!-- 左侧：特征选择列表 -->
                <el-col :span="9" class="feature-selection-container">
                  <div v-if="shapTop20Features.length > 0" class="feature-selection">
                    <el-alert
                      :title="`已选择 ${form.selectedFeatures.length} 个特征 (建议不超过 12 个)`"
                      :type="form.selectedFeatures.length > 12 ? 'warning' : 'info'"
                      :closable="false"
                      style="margin-bottom: 10px;"
                    />
                    <el-checkbox-group v-model="form.selectedFeatures">
                      <div
                        v-for="(item, index) in shapTop20Features"
                        :key="index"
                        class="feature-item"
                        :class="{ 'feature-item-selected': form.selectedFeatures.includes(item.feature) }"
                        @click="selectFeatureForPlot(item.feature)"
                      >
                        <el-checkbox :label="item.feature" :disabled="isFeatureDisabled(item.feature)">
                          <span class="feature-rank">{{ index + 1 }}.</span>
                          <span class="feature-name">{{ item.feature }}</span>
                          <span class="feature-value">{{ item.value.toFixed(4) }}</span>
                        </el-checkbox>
                      </div>
                    </el-checkbox-group>
                  </div>
                  <div v-else class="feature-selection-empty">
                    <el-empty description="请先选择模型文件以加载特征列表"/>
                  </div>
                </el-col>

                <!-- 右侧：SHAP解释图显示 -->
                <el-col :span="15" class="plot-list">
                  <div class="feature-plot-display">
                    <div v-if="selectedFeatureForPlot && shapPlotsDir" class="plot-container">
                      <h4 style="margin-bottom: 10px;">{{ selectedFeatureForPlot }} - SHAP依赖图</h4>
                      <div class="plot-image-wrapper">
                        <img
                          :src="getFeaturePlotUrl(selectedFeatureForPlot)"
                          :alt="`${selectedFeatureForPlot} SHAP plot`"
                          class="feature-plot-image"
                          @error="handleImageError"
                        />
                      </div>
                    </div>
                    <el-empty
                      v-else
                      description="点击左侧特征查看对应的SHAP解释图"
                      :image-size="100"
                    />
                  </div>
                </el-col>
              </el-row>
            </el-form-item>

            <el-divider />

            <el-form-item label="决策树最大深度">
              <el-slider
                v-model="form.maxDepth"
                :min="2"
                :max="5"
                :marks="{ 2: '2', 3: '3', 4: '4', 5: '5' }"
                show-stops
              />
            </el-form-item>

            <el-form-item label="最小分裂样本数">
              <el-input-number
                v-model="form.minSamplesSplit"
                :min="50"
                :max="500"
                :step="50"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="startAnalysis"
                :loading="loading"
                :disabled="!form.modelFile || form.selectedFeatures.length === 0"
                :icon="TrendCharts"
              >
                训练代理模型
              </el-button>
              <el-button @click="loadModelFiles" :icon="Refresh">刷新模型列表</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 任务进度 -->
        <el-card v-if="taskId" style="margin-top: 20px;">
          <template #header>
            <h3>任务进度</h3>
          </template>
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
        </el-card>
      </el-col>

      <!-- 右侧：分析结果 -->
      <el-col :span="10">
        <el-card v-if="result">
          <template #header>
            <h3>分析结果</h3>
          </template>

          <el-descriptions :column="1" border style="margin-bottom: 20px;">
            <el-descriptions-item label="模型文件">{{ result.model_file }}</el-descriptions-item>
            <el-descriptions-item label="特征数量">{{ result.num_features }}</el-descriptions-item>
            <el-descriptions-item label="决策树深度">{{ result.tree_depth }}</el-descriptions-item>
            <el-descriptions-item label="训练准确率">
              {{ (result.train_accuracy * 100).toFixed(2) }}%
            </el-descriptions-item>
            <el-descriptions-item label="训练样本数">{{ result.total_samples }}</el-descriptions-item>
          </el-descriptions>

          <!-- 特征重要性 -->
          <h4>特征重要性</h4>
          <el-table
            :data="featureImportanceTableData"
            style="width: 100%; margin-bottom: 20px;"
            size="small"
            stripe
          >
            <el-table-column prop="rank" label="排名" width="60" />
            <el-table-column prop="feature" label="特征" show-overflow-tooltip />
            <el-table-column prop="importance" label="重要性" width="100">
              <template #default="scope">
                {{ scope.row.importance.toFixed(4) }}
              </template>
            </el-table-column>
          </el-table>

          <!-- 决策规则 -->
          <h4>决策规则 (Top {{ Math.min(20, result.decision_rules?.length || 0) }})</h4>
          <el-collapse v-if="result.decision_rules && result.decision_rules.length > 0">
            <el-collapse-item
              v-for="rule in result.decision_rules.slice(0, 20)"
              :key="rule.rule_id"
              :name="rule.rule_id"
            >
              <template #title>
                <div style="display: flex; align-items: center; width: 100%;">
                  <el-tag size="small" style="margin-right: 10px;">规则 {{ rule.rule_id }}</el-tag>
                  <span style="flex: 1; font-size: 12px; color: #606266;">
                    置信度: {{ (rule.confidence * 100).toFixed(1) }}% | 样本数: {{ rule.samples }}
                  </span>
                </div>
              </template>

              <div class="rule-detail">
                <p><strong>条件:</strong></p>
                <div class="rule-path">{{ rule.path }}</div>

                <el-divider />

                <p><strong>阈值:</strong></p>
                <el-table :data="rule.thresholds" size="small" style="margin-top: 10px;">
                  <el-table-column prop="feature" label="特征" />
                  <el-table-column prop="operator" label="操作符" width="80" />
                  <el-table-column prop="value" label="阈值" width="120">
                    <template #default="scope">
                      {{ scope.row.value.toFixed(4) }}
                    </template>
                  </el-table-column>
                </el-table>

                <el-divider />

                <p><strong>预测结果:</strong></p>
                <el-descriptions :column="2" size="small" border>
                  <el-descriptions-item label="预测类别">
                    <el-tag :type="rule.predicted_class === 1 ? 'success' : 'danger'">
                      {{ rule.predicted_class === 1 ? '正类' : '负类' }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="置信度">
                    {{ (rule.confidence * 100).toFixed(2) }}%
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </el-collapse-item>
          </el-collapse>

          <!-- 操作按钮 -->
          <div style="margin-top: 20px;">
            <el-button type="success" @click="goToBacktestConstruction" :icon="Setting">
              构建回测策略
            </el-button>
          </div>
        </el-card>

        <!-- 模型文件列表 -->
        <el-card :style="result ? 'margin-top: 20px;' : ''">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <h3>模型文件列表</h3>
              <el-button @click="loadModelFiles" :icon="Refresh" circle size="small" />
            </div>
          </template>

          <el-table :data="modelFiles" style="width: 100%;" max-height="400" size="small">
            <el-table-column prop="filename" label="模型文件" show-overflow-tooltip />
            <el-table-column prop="size_mb" label="大小(MB)" width="80" />
            <el-table-column label="操作" width="80">
              <template #default="scope">
                <el-button size="small" type="primary" @click="selectModel(scope.row)">
                  选择
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, TrendCharts, Setting } from '@element-plus/icons-vue'
import { workflowAPI } from '@/api/workflow'
import { useModuleStatesStore } from '@/stores/moduleStates'
import { useModuleState } from '@/composables/useModuleState'

const router = useRouter()
const route = useRoute()
const moduleStore = useModuleStatesStore()

// 从store恢复状态
const form = ref({ ...moduleStore.modelAnalysisState.form })
const loading = ref(false)
const taskId = ref(moduleStore.modelAnalysisState.taskId)
const taskStatus = ref(moduleStore.modelAnalysisState.taskStatus)
const progress = ref(moduleStore.modelAnalysisState.progress)
const statusMessage = ref(moduleStore.modelAnalysisState.statusMessage)
const result = ref(moduleStore.modelAnalysisState.result)

const modelFiles = ref([...moduleStore.modelAnalysisState.modelFiles])
const shapTop20Features = ref([...moduleStore.modelAnalysisState.shapTop20Features])

// SHAP图表相关
const selectedFeatureForPlot = ref(moduleStore.modelAnalysisState.selectedFeatureForPlot || null)
const shapPlotsDir = ref(moduleStore.modelAnalysisState.shapPlotsDir || null)

// 使用状态持久化
useModuleState('modelAnalysis', {
  form,
  taskId,
  taskStatus,
  progress,
  statusMessage,
  result,
  modelFiles,
  shapTop20Features,
  selectedFeatureForPlot,
  shapPlotsDir
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

// 特征重要性表格数据
const featureImportanceTableData = computed(() => {
  if (!result.value?.feature_importance) return []

  return Object.entries(result.value.feature_importance)
    .sort(([, a], [, b]) => b - a)
    .map(([feature, importance], index) => ({
      rank: index + 1,
      feature,
      importance
    }))
})

// 判断特征是否应该禁用（当已选择数量达到8个且该特征未被选中时）
const isFeatureDisabled = (feature) => {
  return form.value.selectedFeatures.length >= 12 && !form.value.selectedFeatures.includes(feature)
}

onMounted(() => {
  loadModelFiles()

  // 如果路由参数中有 model_file，自动选择
  if (route.query.model_file) {
    form.value.modelFile = route.query.model_file
    loadShapMetadata()
  }
})

const loadModelFiles = async () => {
  try {
    const response = await workflowAPI.listDataFiles('models')
    modelFiles.value = response.data.files || []
  } catch (error) {
    ElMessage.error('加载模型文件列表失败')
  }
}

const loadShapMetadata = async () => {
  if (!form.value.modelFile) return

  try {
    // 从模型文件名推断对应的 SHAP 图表目录
    // 格式: ETHUSDT_BINANCE_2025-11-01_00_00_00_2025-11-02_00_00_00_model_lgb.pkl
    // -> ETHUSDT_BINANCE_2025-11-01_00_00_00_2025-11-02_00_00_00_shap
    const baseName = form.value.modelFile.replace('_model_lgb.pkl', '')
    const plotsDir = `${baseName}_shap`

    // 先检查 plots 目录列表，确认该目录是否存在
    const plotsDirsResponse = await workflowAPI.listDataFiles('plots')
    const availableDirs = plotsDirsResponse.data.files || []

    const targetDir = availableDirs.find(dir => dir.dirname === plotsDir)

    if (!targetDir) {
      ElMessage.warning(`未找到对应的 SHAP 图表目录 (${plotsDir})，请先运行模型解释`)
      shapTop20Features.value = []
      shapPlotsDir.value = null
      selectedFeatureForPlot.value = null
      return
    }

    // 加载 SHAP 图表目录的元数据
    const response = await workflowAPI.getPlotFiles(plotsDir)

    if (response.data.metadata && response.data.metadata.shap_importance) {
      // 将 SHAP 重要性转换为数组格式
      shapTop20Features.value = Object.entries(response.data.metadata.shap_importance).map(
        ([feature, value]) => ({
          feature,
          value
        })
      )

      // 保存图表目录名
      shapPlotsDir.value = plotsDir

      // 清空之前的选择
      form.value.selectedFeatures = []
      selectedFeatureForPlot.value = null

      ElMessage.success(`已加载 ${shapTop20Features.value.length} 个 SHAP 特征`)
    } else {
      ElMessage.warning('SHAP 特征数据格式不正确，请重新运行模型解释')
      shapTop20Features.value = []
      shapPlotsDir.value = null
      selectedFeatureForPlot.value = null
    }
  } catch (error) {
    console.error('加载 SHAP 特征数据失败:', error)
    ElMessage.error('加载 SHAP 特征数据失败: ' + (error.response?.data?.detail || error.message))
    shapTop20Features.value = []
    shapPlotsDir.value = null
    selectedFeatureForPlot.value = null
  }
}

// 选择特征以显示对应的SHAP图
const selectFeatureForPlot = (feature) => {
  selectedFeatureForPlot.value = feature
}

// 获取特征对应的SHAP图URL
const getFeaturePlotUrl = (feature) => {
  if (!shapPlotsDir.value || !feature) return null

  // SHAP dependence plot 文件命名格式: 03_feature_{feature}.png，前缀为两位排序号
  const idx = shapTop20Features.value.findIndex(f => f.feature === feature)
  const orderStr = idx >= 0 ? String(idx + 1).padStart(2, '0') : '00'
  const plotFileName = `${orderStr}_${feature}.png`
  return `/static/plots/${shapPlotsDir.value}/${plotFileName}`
}

// 处理图片加载错误
const handleImageError = (event) => {
  console.error('SHAP图片加载失败:', event.target.src)
  ElMessage.warning(`无法加载特征 "${selectedFeatureForPlot.value}" 的SHAP图，请确认图片文件存在`)
}

const selectModel = (model) => {
  form.value.modelFile = model.filename
  loadShapMetadata()
  ElMessage.info(`已选择模型: ${model.filename}`)
}

const startAnalysis = async () => {
  if (!form.value.modelFile) {
    ElMessage.warning('请选择模型文件')
    return
  }

  if (form.value.selectedFeatures.length === 0) {
    ElMessage.warning('请至少选择一个特征')
    return
  }

  if (form.value.selectedFeatures.length > 12) {
    ElMessage.warning('建议选择的特征数量不超过 12 个')
    return
  }

  loading.value = true
  try {
    const response = await workflowAPI.startModelAnalysis({
      model_file: form.value.modelFile,
      selected_features: form.value.selectedFeatures,
      max_depth: form.value.maxDepth,
      min_samples_split: form.value.minSamplesSplit
    })

    taskId.value = response.data.task_id
    taskStatus.value = response.data.status
    progress.value = 0
    statusMessage.value = ''
    result.value = null
    ElMessage.success('模型分析任务已启动')

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
        ElMessage.success('模型分析完成')
      } else if (response.data.status === 'failure') {
        clearInterval(interval)
        ElMessage.error('模型分析失败: ' + response.data.error)
      }
    } catch (error) {
      clearInterval(interval)
      ElMessage.error('查询任务状态失败')
    }
  }, 2000)
}

const goToBacktestConstruction = () => {
  if (result.value) {
    router.push({
      name: 'BacktestConstruction',
      query: {
        model_file: result.value.model_file,
        features_file: result.value.features_file,  // 传递特征文件名
        analysis_result: JSON.stringify({
          features: result.value.selected_features,
          rules: result.value.decision_rules
        })
      }
    })
  }
}
</script>

<style scoped>
.model-analysis {
  padding: 20px;
}
.feature-selection-container{
  width: 100%;
}
.feature-selection {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 15px;
  max-height: 500px;
  overflow-y: auto;
  width: 100%;
}

.feature-selection-empty {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 15px;
  min-height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.feature-item {
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background-color 0.3s;
}

.feature-item:hover {
  background-color: #f5f7fa;
}

.feature-item-selected {
  background-color: #ecf5ff;
}

.feature-item:last-child {
  border-bottom: none;
}

.feature-rank {
  display: inline-block;
  width: 30px;
  color: #909399;
  font-size: 13px;
}

.feature-name {
  flex: 1;
  font-size: 14px;
}

.feature-value {
  float: right;
  color: #409eff;
  font-size: 13px;
  font-weight: bold;
}

.rule-detail {
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.rule-path {
  padding: 10px;
  background-color: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  word-break: break-all;
  margin-top: 5px;
}

h4 {
  margin-top: 15px;
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: bold;
}
.plot-list{
  display: flex;
  width: 100%;
}
/* SHAP图表显示区域 */
.feature-plot-display {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 15px;
  min-height: 500px;
  max-height: 500px;
  overflow-y: auto;
  background-color: #fafafa;
  width: 100%;
}

.plot-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.plot-image-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
  overflow: auto;
}

.feature-plot-image {
  max-width: 100%;
  max-height: 450px;
  object-fit: contain;
  border-radius: 4px;
}
</style>
