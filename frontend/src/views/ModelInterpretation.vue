<template>
  <div class="model-interpretation">
    <el-row :gutter="20">
      <!-- 左侧：模型选择和任务控制 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <h2>模型解释 (SHAP)</h2>
          </template>

          <el-form :model="form" label-width="120px">
            <el-form-item label="模型文件">
              <el-select
                v-model="form.modelFile"
                placeholder="选择模型文件"
                filterable
                style="width: 100%"
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

            <el-form-item>
              <el-button
                type="primary"
                @click="startInterpretation"
                :loading="loading"
                :disabled="!form.modelFile"
                :icon="TrendCharts"
              >
                生成SHAP解释图
              </el-button>
              <el-button @click="loadModelFiles" :icon="Refresh">刷新模型列表</el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <!-- 任务进度 -->
          <div v-if="taskId" class="task-status">
            <h3>任务进度</h3>
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
              <el-descriptions-item label="详细信息" v-if="detailMessage">
                {{ detailMessage }}
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 结果展示 -->
          <div v-if="result" class="result-info">
            <h4>SHAP 解释结果</h4>
            <el-descriptions :column="2" border style="margin-top: 10px;">
              <el-descriptions-item label="模型文件">{{ result.model_file }}</el-descriptions-item>
              <el-descriptions-item label="生成图表数">{{ result.total_plots }}</el-descriptions-item>
              <el-descriptions-item label="图表目录" :span="2">
                {{ result.plots_dir }}
              </el-descriptions-item>
            </el-descriptions>

            <!-- SHAP 和相关性 Top 20 对比 -->
            <el-row :gutter="20" style="margin-top: 20px;">
              <el-col :span="12">
                <h5>SHAP 重要性 Top 20</h5>
                <el-table
                  :data="shapTop20TableData"
                  style="width: 100%"
                  max-height="400"
                  size="small"
                  stripe
                >
                  <el-table-column prop="rank" label="排名" width="60" />
                  <el-table-column prop="feature" label="特征" show-overflow-tooltip />
                  <el-table-column prop="value" label="重要性" width="100">
                    <template #default="scope">
                      {{ scope.row.value.toFixed(4) }}
                    </template>
                  </el-table-column>
                </el-table>
              </el-col>

              <el-col :span="12">
                <h5>皮尔逊相关性 Top 20</h5>
                <el-table
                  :data="corrTop20TableData"
                  style="width: 100%"
                  max-height="400"
                  size="small"
                  stripe
                >
                  <el-table-column prop="rank" label="排名" width="60" />
                  <el-table-column prop="feature" label="特征" show-overflow-tooltip />
                  <el-table-column prop="value" label="相关系数" width="100">
                    <template #default="scope">
                      {{ scope.row.value.toFixed(4) }}
                    </template>
                  </el-table-column>
                </el-table>
              </el-col>
            </el-row>

            <!-- 操作按钮 -->
            <div style="margin-top: 20px;">
              <el-button type="primary" @click="showPlotsDialog = true" :icon="Picture">
                查看SHAP图表
              </el-button>
              <el-button type="success" @click="goToModelAnalysis" :icon="ChatDotRound">
                进入模型分析
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：模型和图表文件列表 -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <h3>模型文件列表</h3>
              <el-button @click="loadModelFiles" :icon="Refresh" circle size="small" />
            </div>
          </template>

          <el-table :data="modelFiles" style="width: 100%" max-height="600" size="small">
            <el-table-column prop="filename" label="模型文件" show-overflow-tooltip />
            <el-table-column prop="size_mb" label="大小(MB)" width="80" />
            <el-table-column prop="modified_time" label="训练时间" width="150" />
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button size="small" type="primary" @click="selectModel(scope.row)">
                  选择
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  :icon="Delete"
                  @click="deleteModel(scope.row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 已生成的SHAP图表目录 -->
        <el-card style="margin-top: 20px;" v-if="shapPlotsDirs.length > 0">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <h3>已生成的SHAP解释</h3>
              <div>
                <el-button @click="clearAllPlots" type="danger" size="small" style="margin-right: 8px;">
                  一键清空
                </el-button>
                <el-button @click="loadShapPlotsDirs" :icon="Refresh" circle size="small" />
              </div>
            </div>
          </template>

          <el-table :data="shapPlotsDirs" style="width: 100%" max-height="300" size="small">
            <el-table-column prop="dirname" label="解释目录" show-overflow-tooltip />
            <el-table-column prop="plot_count" label="图表数" width="80" />
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button size="small" type="primary" @click="viewShapPlots(scope.row)">
                  查看
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  :icon="Delete"
                  @click="deletePlotDir(scope.row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- SHAP图表查看对话框 -->
    <el-dialog
      v-model="showPlotsDialog"
      title="SHAP 解释图表"
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
    >
      <div v-if="currentPlotFiles.length > 0">
        <!-- 视图切换按钮 -->
        <div class="view-mode-switcher">
          <el-radio-group v-model="viewMode" size="default">
            <el-radio-button value="list">
              <el-icon><List /></el-icon>
              <span style="margin-left: 5px;">列表视图</span>
            </el-radio-button>
            <el-radio-button value="grid">
              <el-icon><Grid /></el-icon>
              <span style="margin-left: 5px;">网格视图 (4x3)</span>
            </el-radio-button>
          </el-radio-group>
        </div>

        <!-- 列表视图 -->
        <div v-if="viewMode === 'list'" class="plots-viewer">
        <!-- 图表列表 -->
        <div class="plots-list">
          <el-scrollbar height="70vh">
            <div
              v-for="(plotFile, index) in currentPlotFiles"
              :key="index"
              class="plot-item"
              :class="{ active: selectedPlotIndex === index }"
              @click="selectedPlotIndex = index"
            >
              <span class="plot-name">{{ plotFile }}</span>
            </div>
          </el-scrollbar>
        </div>

        <!-- 图片显示区 -->
        <div class="plot-display">
          <div class="plot-toolbar">
            <el-button
              :disabled="selectedPlotIndex === 0"
              @click="selectedPlotIndex--"
              :icon="ArrowLeft"
            >
              上一张
            </el-button>
            <span class="plot-counter">
              {{ selectedPlotIndex + 1 }} / {{ currentPlotFiles.length }}
            </span>
            <el-button
              :disabled="selectedPlotIndex === currentPlotFiles.length - 1"
              @click="selectedPlotIndex++"
              :icon="ArrowRight"
            >
              下一张
            </el-button>
          </div>
          <div class="plot-image-container">
            <img
              v-if="currentPlotImageUrl"
              :src="currentPlotImageUrl"
              :alt="currentPlotFiles[selectedPlotIndex]"
              class="plot-image"
            />
            <el-empty v-else description="图片加载中..." />
          </div>
        </div>
      </div>

      <!-- 网格视图 -->
      <div v-if="viewMode === 'grid'" class="plots-grid-viewer">
        <!-- 图片网格 4x3 -->
        <div class="plots-grid">
          <div
            v-for="(plotFile, index) in pagedPlotFiles"
            :key="index"
            class="grid-item"
            @click="selectedPlotIndex = (currentPage - 1) * pageSize + index; viewMode = 'list'"
          >
            <img
              :src="getPlotImageUrl(plotFile)"
              :alt="plotFile"
              class="grid-image"
            />
            <div class="grid-image-name">{{ plotFile }}</div>
          </div>
        </div>

        <!-- 分页器 -->
        <div class="grid-pagination">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="currentPlotFiles.length"
            layout="prev, pager, next, total"
          />
        </div>
      </div>
    </div>
      <el-empty v-else description="暂无图表" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, TrendCharts, Picture, ChatDotRound, ArrowLeft, ArrowRight, Delete, List, Grid } from '@element-plus/icons-vue'
import { workflowAPI } from '@/api/workflow'
import { useModuleStatesStore } from '@/stores/moduleStates'
import { useModuleState } from '@/composables/useModuleState'

const router = useRouter()
const route = useRoute()
const moduleStore = useModuleStatesStore()

// 从store恢复状态
const form = ref({ ...moduleStore.modelInterpretationState.form })
const loading = ref(false)
const taskId = ref(moduleStore.modelInterpretationState.taskId)
const taskStatus = ref(moduleStore.modelInterpretationState.taskStatus)
const progress = ref(moduleStore.modelInterpretationState.progress)
const statusMessage = ref(moduleStore.modelInterpretationState.statusMessage)
const detailMessage = ref(moduleStore.modelInterpretationState.detailMessage)
const result = ref(moduleStore.modelInterpretationState.result)

const modelFiles = ref([...moduleStore.modelInterpretationState.modelFiles])
const shapPlotsDirs = ref([...moduleStore.modelInterpretationState.shapPlotsDirs])

// 图表查看相关
const showPlotsDialog = ref(moduleStore.modelInterpretationState.showPlotsDialog)
const currentPlotFiles = ref([...moduleStore.modelInterpretationState.currentPlotFiles])
const selectedPlotIndex = ref(moduleStore.modelInterpretationState.selectedPlotIndex)
const viewMode = ref(moduleStore.modelInterpretationState.viewMode)
const currentPage = ref(moduleStore.modelInterpretationState.currentPage)
const pageSize = 12 // 4x3 网格，每页12张图

// 使用状态持久化
useModuleState('modelInterpretation', {
  form,
  taskId,
  taskStatus,
  progress,
  statusMessage,
  detailMessage,
  result,
  modelFiles,
  shapPlotsDirs,
  showPlotsDialog,
  currentPlotFiles,
  selectedPlotIndex,
  viewMode,
  currentPage
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

// SHAP Top 20 表格数据
const shapTop20TableData = computed(() => {
  if (!result.value?.shap_importance) return []

  return Object.entries(result.value.shap_importance).map(([feature, value], index) => ({
    rank: index + 1,
    feature,
    value
  }))
})

// 相关性 Top 20 表格数据
const corrTop20TableData = computed(() => {
  if (!result.value?.correlation) return []

  return Object.entries(result.value.correlation).map(([feature, value], index) => ({
    rank: index + 1,
    feature,
    value
  }))
})

// 当前图片 URL
const currentPlotImageUrl = computed(() => {
  if (!result.value || currentPlotFiles.value.length === 0) return null

  const plotFile = currentPlotFiles.value[selectedPlotIndex.value]

  // 优先使用 plots_dir_name（仅目录名），如果没有则从完整路径提取
  let dirName = result.value.plots_dir_name
  if (!dirName && result.value.plots_dir) {
    // 兼容旧版本：从完整路径中提取目录名
    dirName = result.value.plots_dir.split('\\').pop().split('/').pop()
  }

  if (!dirName) return null

  return `/static/plots/${dirName}/${plotFile}`
})

// 网格模式：总页数
const totalPages = computed(() => {
  return Math.ceil(currentPlotFiles.value.length / pageSize)
})

// 网格模式：当前页的图片列表
const pagedPlotFiles = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return currentPlotFiles.value.slice(start, end)
})

// 获取指定图片的 URL
const getPlotImageUrl = (plotFile) => {
  if (!result.value) return null

  let dirName = result.value.plots_dir_name
  if (!dirName && result.value.plots_dir) {
    dirName = result.value.plots_dir.split('\\').pop().split('/').pop()
  }

  if (!dirName) return null

  return `/static/plots/${dirName}/${plotFile}`
}

onMounted(() => {
  loadModelFiles()
  loadShapPlotsDirs()

  // 如果路由参数中有 model_file，自动选择
  if (route.query.model_file) {
    form.value.modelFile = route.query.model_file
  }
})

// 监听 result 变化，更新当前图表文件列表
watch(result, (newResult) => {
  if (newResult?.plot_files) {
    currentPlotFiles.value = newResult.plot_files
    selectedPlotIndex.value = 0
    currentPage.value = 1
    viewMode.value = 'list'
  }
})

const startInterpretation = async () => {
  if (!form.value.modelFile) {
    ElMessage.warning('请选择模型文件')
    return
  }

  loading.value = true
  try {
    const response = await workflowAPI.startModelInterpretation({
      model_file: form.value.modelFile
    })

    taskId.value = response.data.task_id
    taskStatus.value = response.data.status
    progress.value = 0
    statusMessage.value = ''
    detailMessage.value = ''
    result.value = null
    ElMessage.success('SHAP解释任务已启动')

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
        detailMessage.value = response.data.result.message || ''
      }

      if (response.data.status === 'success') {
        result.value = response.data.result
        progress.value = 100
        clearInterval(interval)
        ElMessage.success('SHAP解释完成')
        loadShapPlotsDirs() // 刷新图表目录列表
      } else if (response.data.status === 'failure') {
        clearInterval(interval)
        ElMessage.error('SHAP解释失败: ' + response.data.error)
      }
    } catch (error) {
      clearInterval(interval)
      ElMessage.error('查询任务状态失败')
    }
  }, 2000)
}

const loadModelFiles = async () => {
  try {
    const response = await workflowAPI.listDataFiles('models')
    modelFiles.value = response.data.files || []
  } catch (error) {
    ElMessage.error('加载模型文件列表失败')
  }
}

const loadShapPlotsDirs = async () => {
  try {
    const response = await workflowAPI.listDataFiles('plots')
    shapPlotsDirs.value = response.data.files || []
  } catch (error) {
    console.error('加载SHAP图表目录失败', error)
  }
}

const selectModel = (model) => {
  form.value.modelFile = model.filename
  ElMessage.info(`已选择模型: ${model.filename}`)
}

const viewShapPlots = async (plotsDir) => {
  try {
    const response = await workflowAPI.getPlotFiles(plotsDir.dirname)
    currentPlotFiles.value = response.data.plot_files
    selectedPlotIndex.value = 0

    // 设置当前的 plots_dir_name，用于生成图片 URL
    if (!result.value) {
      result.value = {}
    }
    result.value.plots_dir_name = plotsDir.dirname
    result.value.plots_dir = plotsDir.path

    // 如果有元数据，也可以加载
    if (response.data.metadata) {
      result.value.shap_importance = response.data.metadata.shap_importance
      result.value.correlation = response.data.metadata.correlation
      result.value.model_file = response.data.metadata.model_file
      result.value.total_plots = response.data.metadata.total_plots
    }

    showPlotsDialog.value = true
    ElMessage.success(`已加载 ${response.data.total_plots} 张图表`)
  } catch (error) {
    ElMessage.error('加载图表列表失败: ' + error.message)
  }
}

const goToModelAnalysis = () => {
  if (result.value?.model_file) {
    router.push({
      name: 'ModelAnalysis',
      query: { model_file: result.value.model_file }
    })
  }
}

const deleteModel = async (model) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型文件 "${model.filename}" 吗？此操作不可恢复！`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await workflowAPI.deleteDataFile(model.filename, 'models')
    ElMessage.success('模型文件删除成功')
    loadModelFiles() // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除模型文件失败: ' + (error.message || error))
    }
  }
}

const deletePlotDir = async (plotsDir) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除SHAP解释目录 "${plotsDir.dirname}" 吗？此操作将删除该目录下的所有图表文件，不可恢复！`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await workflowAPI.deletePlotDirectory(plotsDir.dirname)
    ElMessage.success('SHAP解释目录删除成功')
    loadShapPlotsDirs() // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除SHAP解释目录失败: ' + (error.message || error))
    }
  }
}

const clearAllPlots = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要清空所有SHAP解释目录吗？此操作将删除 ${shapPlotsDirs.value.length} 个目录及其所有图表文件，不可恢复！`,
      '清空确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const deletePromises = shapPlotsDirs.value.map(dir =>
      workflowAPI.deletePlotDirectory(dir.dirname)
    )

    await Promise.all(deletePromises)
    ElMessage.success('所有SHAP解释目录已清空')
    loadShapPlotsDirs() // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清空SHAP解释目录失败: ' + (error.message || error))
    }
  }
}
</script>

<style scoped>
.model-interpretation {
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
  font-size: 16px;
  font-weight: bold;
}

.result-info h5 {
  margin-top: 15px;
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: bold;
}

/* 图表查看器样式 */
.plots-viewer {
  display: flex;
  gap: 20px;
  height: 70vh;
}

.plots-list {
  width: 250px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.plot-item {
  padding: 12px;
  cursor: pointer;
  border-bottom: 1px solid #ebeef5;
  transition: all 0.3s;
}

.plot-item:hover {
  background-color: #f5f7fa;
}

.plot-item.active {
  background-color: #409eff;
  color: white;
}

.plot-name {
  font-size: 13px;
  word-break: break-all;
}

.plot-display {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.plot-toolbar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.plot-counter {
  font-size: 14px;
  font-weight: bold;
  color: #606266;
}

.plot-image-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #fff;
  overflow: auto;
}

.plot-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

/* 视图切换按钮样式 */
.view-mode-switcher {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
}

/* 网格视图样式 */
.plots-grid-viewer {
  width: 100%;
}

.plots-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 20px;
  min-height: 65vh;
}

.grid-item {
  position: relative;
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
  background-color: #fff;
  display: flex;
  flex-direction: column;
  height: 24vh;
}

.grid-item:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  transform: translateY(-2px);
}

.grid-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  flex: 1;
  padding: 8px;
}

.grid-image-name {
  padding: 8px;
  background-color: #f5f7fa;
  font-size: 12px;
  text-align: center;
  color: #606266;
  word-break: break-all;
  border-top: 1px solid #dcdfe6;
  max-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.grid-pagination {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}
</style>
