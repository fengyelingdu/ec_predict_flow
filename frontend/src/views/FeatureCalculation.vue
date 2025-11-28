<template>
  <div class="feature-calculation">
    <el-row :gutter="20">
      <!-- 左侧：计算表单 -->
      <el-col :span="12">
        <!-- 特征计算卡片 -->
        <el-card class="calculation-card">
          <template #header>
            <h2>特征计算</h2>
          </template>

          <el-form :model="featureForm" label-width="120px">
            <el-form-item label="数据文件">
              <el-select
                v-model="featureForm.dataFile"
                placeholder="选择数据文件"
                filterable
                style="width: 100%"
                @change="onDataFileChange"
              >
                <el-option
                  v-for="file in rawFiles"
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

            <el-form-item label="Alpha类型">
              <el-checkbox-group v-model="featureForm.alphaTypes">
                <el-checkbox label="alpha158" :disabled="isAlphaCalculated('alpha158')">
                  Alpha158 (158个特征)
                  <el-tag v-if="isAlphaCalculated('alpha158')" type="success" size="small" style="margin-left: 5px;">
                    已计算
                  </el-tag>
                </el-checkbox>
                <el-checkbox label="alpha216" :disabled="isAlphaCalculated('alpha216')">
                  Alpha216 (216个特征)
                  <el-tag v-if="isAlphaCalculated('alpha216')" type="success" size="small" style="margin-left: 5px;">
                    已计算
                  </el-tag>
                </el-checkbox>
                <el-checkbox label="alpha101" :disabled="isAlphaCalculated('alpha101')">
                  Alpha101 (101个特征)
                  <el-tag v-if="isAlphaCalculated('alpha101')" type="success" size="small" style="margin-left: 5px;">
                    已计算
                  </el-tag>
                </el-checkbox>
                <el-checkbox label="alpha191" :disabled="isAlphaCalculated('alpha191')">
                  Alpha191 (191个特征)
                  <el-tag v-if="isAlphaCalculated('alpha191')" type="success" size="small" style="margin-left: 5px;">
                    已计算
                  </el-tag>
                </el-checkbox>
                <el-checkbox label="alpha_ch" :disabled="isAlphaCalculated('alpha_ch')">
                  Alpha_ch (178个特征)
                  <el-tag v-if="isAlphaCalculated('alpha_ch')" type="success" size="small" style="margin-left: 5px;">
                    已计算
                  </el-tag>
                </el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="startFeatureCalculation"
                :loading="featureLoading"
                :disabled="featureForm.alphaTypes.length === 0"
              >
                计算特征
              </el-button>
              <el-button @click="loadRawFiles" :icon="Refresh">刷新文件列表</el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <div v-if="featureTaskId" class="task-status">
            <h3>特征计算任务状态</h3>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="任务ID">{{ featureTaskId }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(featureTaskStatus)">{{ featureTaskStatus }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="进度" v-if="featureProgress !== null">
                <el-progress :percentage="Math.round(featureProgress)" />
              </el-descriptions-item>
              <el-descriptions-item label="当前状态" v-if="featureStatusMessage">
                {{ featureStatusMessage }}
              </el-descriptions-item>
            </el-descriptions>

            <div v-if="featureResult" class="result-info">
              <h4>计算结果</h4>
              <el-descriptions :column="2" border style="margin-top: 10px;">
                <el-descriptions-item label="特征文件">{{ featureResult.features_file }}</el-descriptions-item>
                <el-descriptions-item label="特征数量">{{ featureResult.total_features }}</el-descriptions-item>
                <el-descriptions-item label="Alpha类型">{{ featureResult.alpha_types?.join(', ') }}</el-descriptions-item>
                <el-descriptions-item label="原始数据行数">{{ featureResult.total_rows }}</el-descriptions-item>
                <el-descriptions-item label="有效数据行数" :span="2">{{ featureResult.valid_rows }}</el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-card>

        <!-- 标签计算卡片 -->
        <el-card class="calculation-card" style="margin-top: 20px;">
          <template #header>
            <h2>标签计算</h2>
          </template>

          <el-form :model="labelForm" label-width="120px">
            <el-form-item label="数据文件">
              <el-select
                v-model="labelForm.dataFile"
                placeholder="选择数据文件"
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="file in rawFiles"
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

            <el-form-item label="标签类型">
              <el-radio-group v-model="labelForm.labelType">
                <el-radio label="up">上涨标签</el-radio>
                <el-radio label="down">下跌标签</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="过滤指标">
              <el-radio-group v-model="labelForm.filterType">
                <el-radio label="rsi">RSI过滤</el-radio>
                <el-radio label="cti">CTI过滤</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="过滤阈值">
              <div v-if="labelForm.filterType === 'rsi'">
                <div style="margin-bottom: 10px;">
                  <span style="margin-right: 10px;">上涨标签阈值 (RSI &lt;):</span>
                  <el-input-number
                    v-model="labelForm.rsiUpThreshold"
                    :min="0"
                    :max="100"
                    :step="1"
                    style="width: 120px;"
                  />
                </div>
                <div>
                  <span style="margin-right: 10px;">下跌标签阈值 (RSI &gt;):</span>
                  <el-input-number
                    v-model="labelForm.rsiDownThreshold"
                    :min="0"
                    :max="100"
                    :step="1"
                    style="width: 120px;"
                  />
                </div>
              </div>
              <div v-else>
                <div style="margin-bottom: 10px;">
                  <span style="margin-right: 10px;">上涨标签阈值 (CTI &lt;):</span>
                  <el-input-number
                    v-model="labelForm.ctiUpThreshold"
                    :min="-1"
                    :max="1"
                    :step="0.1"
                    :precision="1"
                    style="width: 120px;"
                  />
                </div>
                <div>
                  <span style="margin-right: 10px;">下跌标签阈值 (CTI &gt;):</span>
                  <el-input-number
                    v-model="labelForm.ctiDownThreshold"
                    :min="-1"
                    :max="1"
                    :step="0.1"
                    :precision="1"
                    style="width: 120px;"
                  />
                </div>
              </div>
              <div style="margin-top: 5px; color: #909399; font-size: 12px;">
                <span v-if="labelForm.labelType === 'up' && labelForm.filterType === 'rsi'">
                  当前设置: RSI &lt; {{ labelForm.rsiUpThreshold }}
                </span>
                <span v-if="labelForm.labelType === 'down' && labelForm.filterType === 'rsi'">
                  当前设置: RSI &gt; {{ labelForm.rsiDownThreshold }}
                </span>
                <span v-if="labelForm.labelType === 'up' && labelForm.filterType === 'cti'">
                  当前设置: CTI &lt; {{ labelForm.ctiUpThreshold }}
                </span>
                <span v-if="labelForm.labelType === 'down' && labelForm.filterType === 'cti'">
                  当前设置: CTI &gt; {{ labelForm.ctiDownThreshold }}
                </span>
              </div>
            </el-form-item>

            <el-form-item label="标签窗口">
              <el-input-number v-model="labelForm.window" :min="5" :max="100" :step="2" />
              <span style="margin-left: 10px; color: #909399; font-size: 12px;">
                用于计算标签的滑动窗口大小（建议奇数）
              </span>
            </el-form-item>

            <el-form-item label="预测周期">
              <el-input-number v-model="labelForm.lookForward" :min="1" :max="60" />
              <span style="margin-left: 10px; color: #909399; font-size: 12px;">
                预测未来多少个K线周期
              </span>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="startLabelCalculation"
                :loading="labelLoading"
                :disabled="!labelForm.dataFile"
              >
                计算标签
              </el-button>
              <el-button @click="loadRawFiles" :icon="Refresh">刷新文件列表</el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <div v-if="labelTaskId" class="task-status">
            <h3>标签计算任务状态</h3>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="任务ID">{{ labelTaskId }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(labelTaskStatus)">{{ labelTaskStatus }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="进度" v-if="labelProgress !== null">
                <el-progress :percentage="Math.round(labelProgress)" />
              </el-descriptions-item>
              <el-descriptions-item label="当前状态" v-if="labelStatusMessage">
                {{ labelStatusMessage }}
              </el-descriptions-item>
            </el-descriptions>

            <div v-if="labelResult" class="result-info">
              <h4>计算结果</h4>
              <el-descriptions :column="2" border style="margin-top: 10px;">
                <el-descriptions-item label="标签文件">{{ labelResult.labels_file }}</el-descriptions-item>
                <el-descriptions-item label="基于数据文件">{{ labelResult.data_file }}</el-descriptions-item>
                <el-descriptions-item label="标签窗口">{{ labelResult.window }}</el-descriptions-item>
                <el-descriptions-item label="预测周期">{{ labelResult.look_forward }}</el-descriptions-item>
              </el-descriptions>

              <div v-if="labelResult.label_stats" style="margin-top: 10px;">
                <h5>标签统计</h5>
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="总样本数">
                    {{ labelResult.label_stats.total_samples }}
                  </el-descriptions-item>
                  <el-descriptions-item label="非空标签数">
                    {{ labelResult.label_stats.non_nan_labels }}
                  </el-descriptions-item>
                  <el-descriptions-item label="标签均值">
                    {{ labelResult.label_stats.label_mean?.toFixed(4) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="标签标准差">
                    {{ labelResult.label_stats.label_std?.toFixed(4) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="正样本比例" :span="2">
                    {{ (labelResult.label_stats.positive_ratio * 100).toFixed(2) }}%
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
          </div>
        </el-card>
        <!-- 标签预览部分 -->
        <el-card class="calculation-card" style="margin-top: 20px;">
          <template #header>
            <h2>标签预览</h2>
          </template>
          <el-form :model="labelPreviewForm" label-width="120px">
              <el-form-item label="数据文件">
                <el-select
                  v-model="labelPreviewForm.dataFile"
                  placeholder="选择数据文件（OHLCV）"
                  filterable
                  style="width: 100%"
                >
                  <el-option
                    v-for="file in rawFiles"
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
                  v-model="labelPreviewForm.labelFile"
                  placeholder="选择标签文件"
                  filterable
                  style="width: 100%"
                >
                  <el-option
                    v-for="file in labelFiles"
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
                  @click="openLabelPreview"
                  :disabled="!labelPreviewForm.dataFile || !labelPreviewForm.labelFile"
                >
                  预览标签
                </el-button>
              </el-form-item>
            </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：文件列表 -->
      <el-col :span="12">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="原始数据文件" name="raw">
            <el-card>
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <h3>原始数据文件</h3>
                  <el-button @click="loadRawFiles" :icon="Refresh" circle size="small" />
                </div>
              </template>

              <el-table :data="rawFiles" style="width: 100%" max-height="500">
                <el-table-column prop="filename" label="文件名" width="300" show-overflow-tooltip />
                <el-table-column prop="size_mb" label="大小(MB)" width="100" />
                <el-table-column prop="modified_time" label="修改时间" width="180" />
                <el-table-column label="操作" width="150">
                  <template #default="scope">
                    <el-button size="small" @click="previewFile(scope.row, 'raw')">预览</el-button>
                    <el-popconfirm
                      title="确定删除此文件吗?"
                      @confirm="deleteFile(scope.row.filename, 'raw')"
                    >
                      <template #reference>
                        <el-button size="small" type="danger">删除</el-button>
                      </template>
                    </el-popconfirm>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="处理后数据文件" name="processed">
            <el-card>
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <h3>处理后数据文件</h3>
                  <el-button @click="loadProcessedFiles" :icon="Refresh" circle size="small" />
                </div>
              </template>

              <el-table :data="processedFiles" style="width: 100%" max-height="500">
                <el-table-column prop="filename" label="文件名" width="300" show-overflow-tooltip />
                <el-table-column prop="size_mb" label="大小(MB)" width="100" />
                <el-table-column prop="modified_time" label="修改时间" width="180" />
                <el-table-column label="操作" width="150">
                  <template #default="scope">
                    <el-button size="small" @click="previewFile(scope.row, 'processed')">预览</el-button>
                    <el-popconfirm
                      title="确定删除此文件吗?"
                      @confirm="deleteFile(scope.row.filename, 'processed')"
                    >
                      <template #reference>
                        <el-button size="small" type="danger">删除</el-button>
                      </template>
                    </el-popconfirm>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-tab-pane>
        </el-tabs>
      </el-col>
    </el-row>

    <!-- 预览对话框 -->
    <el-dialog v-model="previewDialogVisible" title="数据预览" width="80%">
      <div v-if="previewData">
        <el-descriptions :column="2" border style="margin-bottom: 20px;">
          <el-descriptions-item label="文件名">{{ previewData.filename }}</el-descriptions-item>
          <el-descriptions-item label="有效数据行数">{{ previewData.total_rows }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ previewData.stats?.start_time }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ previewData.stats?.end_time }}</el-descriptions-item>
        </el-descriptions>

        <h4>列信息 (共{{ previewData.columns?.length }}列)</h4>
        <div style="max-height: 100px; overflow-y: auto; margin-bottom: 20px;">
          <el-tag v-for="col in previewData.columns" :key="col" style="margin: 3px;">
            {{ col }}
          </el-tag>
        </div>

        <h4>数据预览 (前10行，显示前10列)</h4>
        <el-table :data="previewData.preview" style="width: 100%" max-height="400">
          <el-table-column
            v-for="col in previewData.columns.slice(0, 10)"
            :key="col"
            :prop="col"
            :label="col"
            width="150"
          />
        </el-table>
      </div>
    </el-dialog>

    <!-- 标签预览对话框 -->
    <el-dialog
      v-model="labelPreviewDialogVisible"
      title="标签预览 - K线图表"
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
    >
      <div v-if="labelPreviewData">
        <!-- 统计信息 -->
        <el-descriptions :column="4" border style="margin-bottom: 20px;" size="small">
          <el-descriptions-item label="文件名" :span="2">{{ labelPreviewData.filename }}</el-descriptions-item>
          <el-descriptions-item label="标签列">{{ labelPreviewData.label_column }}</el-descriptions-item>
          <el-descriptions-item label="总行数">{{ labelPreviewData.total_rows }}</el-descriptions-item>
          <el-descriptions-item label="非空标签数">{{ labelPreviewData.label_stats?.non_nan_labels }}</el-descriptions-item>
          <el-descriptions-item label="正样本数">{{ labelPreviewData.label_stats?.positive_count }}</el-descriptions-item>
          <el-descriptions-item label="负样本数">{{ labelPreviewData.label_stats?.negative_count }}</el-descriptions-item>
          <el-descriptions-item label="零样本数">{{ labelPreviewData.label_stats?.zero_count }}</el-descriptions-item>
          <el-descriptions-item label="标签均值">{{ labelPreviewData.label_stats?.label_mean?.toFixed(4) }}</el-descriptions-item>
          <el-descriptions-item label="标签标准差">{{ labelPreviewData.label_stats?.label_std?.toFixed(4) }}</el-descriptions-item>
          <el-descriptions-item label="标签最小值">{{ labelPreviewData.label_stats?.label_min?.toFixed(4) }}</el-descriptions-item>
          <el-descriptions-item label="标签最大值">{{ labelPreviewData.label_stats?.label_max?.toFixed(4) }}</el-descriptions-item>
        </el-descriptions>

        <!-- 翻页控制 -->
        <div style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <el-button
              @click="prevPage"
              :disabled="currentOffset === 0"
              :icon="ArrowLeft"
            >
              上一页
            </el-button>
            <el-button
              @click="nextPage"
              :disabled="currentOffset + pageSize >= labelPreviewData.total_rows"
              :icon="ArrowRight"
            >
              下一页
            </el-button>
            <span style="margin-left: 20px;">
              显示: {{ currentOffset + 1 }} - {{ Math.min(currentOffset + pageSize, labelPreviewData.total_rows) }} / {{ labelPreviewData.total_rows }}
            </span>
          </div>
          <div>
            <span style="margin-right: 10px;">每页K线数:</span>
            <el-input-number
              v-model="pageSize"
              :min="50"
              :max="500"
              :step="50"
              @change="loadLabelPreviewData"
              style="width: 120px;"
            />
          </div>
        </div>

        <!-- K线图表 -->
        <div ref="chartContainer" style="width: 100%; height: 600px;"></div>
      </div>
      <div v-else style="text-align: center; padding: 40px;">
        <el-icon :size="40" class="is-loading"><Loading /></el-icon>
        <p style="margin-top: 20px;">加载中...</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, ArrowLeft, ArrowRight, Loading } from '@element-plus/icons-vue'
import { workflowAPI } from '@/api/workflow'
import { useModuleStatesStore } from '@/stores/moduleStates'
import { useModuleState } from '@/composables/useModuleState'
import * as echarts from 'echarts'

const moduleStore = useModuleStatesStore()

// 从store恢复状态
const featureForm = ref({ ...moduleStore.featureCalculationState.featureForm })
const labelForm = ref({
  dataFile: moduleStore.featureCalculationState.labelForm.dataFile || '',
  window: moduleStore.featureCalculationState.labelForm.window || 29,
  lookForward: moduleStore.featureCalculationState.labelForm.lookForward || 10,
  labelType: moduleStore.featureCalculationState.labelForm.labelType || 'up',
  filterType: moduleStore.featureCalculationState.labelForm.filterType || 'rsi',
  rsiUpThreshold: moduleStore.featureCalculationState.labelForm.rsiUpThreshold || 30,
  rsiDownThreshold: moduleStore.featureCalculationState.labelForm.rsiDownThreshold || 70,
  ctiUpThreshold: moduleStore.featureCalculationState.labelForm.ctiUpThreshold || -0.5,
  ctiDownThreshold: moduleStore.featureCalculationState.labelForm.ctiDownThreshold || 0.5
})

// 特征计算任务状态
const featureLoading = ref(false)
const featureTaskId = ref(moduleStore.featureCalculationState.featureTaskId)
const featureTaskStatus = ref(moduleStore.featureCalculationState.featureTaskStatus)
const featureProgress = ref(moduleStore.featureCalculationState.featureProgress)
const featureStatusMessage = ref(moduleStore.featureCalculationState.featureStatusMessage)
const featureResult = ref(moduleStore.featureCalculationState.featureResult)

// 标签计算任务状态
const labelLoading = ref(false)
const labelTaskId = ref(moduleStore.featureCalculationState.labelTaskId)
const labelTaskStatus = ref(moduleStore.featureCalculationState.labelTaskStatus)
const labelProgress = ref(moduleStore.featureCalculationState.labelProgress)
const labelStatusMessage = ref(moduleStore.featureCalculationState.labelStatusMessage)
const labelResult = ref(moduleStore.featureCalculationState.labelResult)

// 文件列表
const rawFiles = ref([...moduleStore.featureCalculationState.rawFiles])
const processedFiles = ref([...moduleStore.featureCalculationState.processedFiles])
const activeTab = ref(moduleStore.featureCalculationState.activeTab)
const previewDialogVisible = ref(moduleStore.featureCalculationState.previewDialogVisible)
const previewData = ref(moduleStore.featureCalculationState.previewData)
const calculatedAlphas = ref({ ...moduleStore.featureCalculationState.calculatedAlphas })

// 标签预览相关状态
const labelPreviewForm = ref({
  dataFile: '',
  labelFile: ''
})
const labelPreviewDialogVisible = ref(false)
const labelPreviewData = ref(null)
const currentOffset = ref(0)
const pageSize = ref(300)
const chartContainer = ref(null)
let chartInstance = null

// 计算标签文件列表（从处理后的文件中筛选出包含label的文件）
const labelFiles = computed(() => {
  return processedFiles.value.filter(file =>
    file.filename.toLowerCase().includes('label')
  )
})

// 使用状态持久化
useModuleState('featureCalculation', {
  featureForm,
  labelForm,
  featureTaskId,
  featureTaskStatus,
  featureProgress,
  featureStatusMessage,
  featureResult,
  labelTaskId,
  labelTaskStatus,
  labelProgress,
  labelStatusMessage,
  labelResult,
  rawFiles,
  processedFiles,
  activeTab,
  previewDialogVisible,
  previewData,
  calculatedAlphas
})

onMounted(() => {
  loadRawFiles()
  loadProcessedFiles()
})
// 状态类型映射
const getStatusType = (status) => {
  const statusMap = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failure: 'danger'
  }
  return statusMap[status] || 'info'
}

onMounted(() => {
  loadRawFiles()
  loadProcessedFiles()
})

// 检查某个alpha类型是否已计算
const isAlphaCalculated = (alphaType) => {
  if (!featureForm.value.dataFile) return false
  return calculatedAlphas.value[alphaType] || false
}

// 当数据文件改变时，检测已计算的alpha类型
const onDataFileChange = () => {
  checkCalculatedAlphas()
}

// 检测已计算的alpha类型
const checkCalculatedAlphas = () => {
  if (!featureForm.value.dataFile) {
    calculatedAlphas.value = {}
    return
  }

  const baseName = featureForm.value.dataFile.replace('.pkl', '')
  const alphaTypes = ['alpha158', 'alpha216', 'alpha101', 'alpha191','alpha_ch']
  const calculated = {}

  alphaTypes.forEach(alphaType => {
    const exists = processedFiles.value.some(file => {
      return file.filename.includes(baseName) &&
             file.filename.includes('features') &&
             file.filename.includes(alphaType)
    })
    calculated[alphaType] = exists
  })

  calculatedAlphas.value = calculated
  featureForm.value.alphaTypes = featureForm.value.alphaTypes.filter(type => !calculated[type])
}

// 开始特征计算
const startFeatureCalculation = async () => {
  if (!featureForm.value.dataFile) {
    ElMessage.warning('请选择数据文件')
    return
  }

  if (featureForm.value.alphaTypes.length === 0) {
    ElMessage.warning('请至少选择一种Alpha类型')
    return
  }

  featureLoading.value = true
  try {
    const response = await workflowAPI.startFeatureCalculation({
      data_file: featureForm.value.dataFile,
      alpha_types: featureForm.value.alphaTypes
    })

    featureTaskId.value = response.data.task_id
    featureTaskStatus.value = response.data.status
    featureProgress.value = 0
    featureStatusMessage.value = ''
    featureResult.value = null
    ElMessage.success('特征计算任务已启动')

    pollTaskStatus('feature')
  } catch (error) {
    ElMessage.error('启动任务失败: ' + error.message)
  } finally {
    featureLoading.value = false
  }
}

// 开始标签计算
const startLabelCalculation = async () => {
  if (!labelForm.value.dataFile) {
    ElMessage.warning('请选择数据文件')
    return
  }

  labelLoading.value = true
  try {
    // 根据过滤类型和标签类型选择对应的阈值
    let threshold
    if (labelForm.value.filterType === 'rsi') {
      threshold = labelForm.value.labelType === 'up'
        ? labelForm.value.rsiUpThreshold
        : labelForm.value.rsiDownThreshold
    } else {
      threshold = labelForm.value.labelType === 'up'
        ? labelForm.value.ctiUpThreshold
        : labelForm.value.ctiDownThreshold
    }

    const response = await workflowAPI.startLabelCalculation({
      data_file: labelForm.value.dataFile,
      window: labelForm.value.window,
      look_forward: labelForm.value.lookForward,
      label_type: labelForm.value.labelType,
      filter_type: labelForm.value.filterType,
      threshold: threshold
    })

    labelTaskId.value = response.data.task_id
    labelTaskStatus.value = response.data.status
    labelProgress.value = 0
    labelStatusMessage.value = ''
    labelResult.value = null
    ElMessage.success('标签计算任务已启动')

    pollTaskStatus('label')
  } catch (error) {
    ElMessage.error('启动任务失败: ' + error.message)
  } finally {
    labelLoading.value = false
  }
}

// 轮询任务状态
const pollTaskStatus = async (taskType) => {
  const taskId = taskType === 'feature' ? featureTaskId.value : labelTaskId.value

  const interval = setInterval(async () => {
    try {
      const response = await workflowAPI.getTaskStatus(taskId)

      if (taskType === 'feature') {
        featureTaskStatus.value = response.data.status

        if (response.data.result) {
          featureProgress.value = response.data.result.progress || featureProgress.value
          featureStatusMessage.value = response.data.result.status || ''
        }

        if (response.data.status === 'success') {
          featureResult.value = response.data.result
          featureProgress.value = 100
          clearInterval(interval)
          ElMessage.success('特征计算完成')
          loadProcessedFiles()
          setTimeout(() => checkCalculatedAlphas(), 1000)
        } else if (response.data.status === 'failure') {
          clearInterval(interval)
          ElMessage.error('特征计算失败: ' + response.data.error)
        }
      } else {
        labelTaskStatus.value = response.data.status

        if (response.data.result) {
          labelProgress.value = response.data.result.progress || labelProgress.value
          labelStatusMessage.value = response.data.result.status || ''
        }

        if (response.data.status === 'success') {
          labelResult.value = response.data.result
          labelProgress.value = 100
          clearInterval(interval)
          ElMessage.success('标签计算完成')
          loadProcessedFiles()
        } else if (response.data.status === 'failure') {
          clearInterval(interval)
          ElMessage.error('标签计算失败: ' + response.data.error)
        }
      }
    } catch (error) {
      clearInterval(interval)
      ElMessage.error('查询任务状态失败')
    }
  }, 2000)
}

const loadRawFiles = async () => {
  try {
    const response = await workflowAPI.listDataFiles('raw')
    rawFiles.value = response.data.files
  } catch (error) {
    ElMessage.error('加载原始文件列表失败')
  }
}

const loadProcessedFiles = async () => {
  try {
    const response = await workflowAPI.listDataFiles('processed')
    processedFiles.value = response.data.files
    checkCalculatedAlphas()
  } catch (error) {
    ElMessage.error('加载处理文件列表失败')
  }
}

const deleteFile = async (filename, directory) => {
  try {
    await workflowAPI.deleteDataFile(filename, directory)
    ElMessage.success('文件删除成功')
    if (directory === 'raw') {
      loadRawFiles()
    } else {
      loadProcessedFiles()
      checkCalculatedAlphas()
    }
  } catch (error) {
    ElMessage.error('删除文件失败')
  }
}

const previewFile = async (file, directory) => {
  try {
    const response = await workflowAPI.previewDataFile(file.filename, directory)
    previewData.value = response.data
    previewDialogVisible.value = true
  } catch (error) {
    ElMessage.error('预览文件失败')
  }
}

// 打开标签预览
const openLabelPreview = async () => {
  if (!labelPreviewForm.value.dataFile) {
    ElMessage.warning('请选择数据文件')
    return
  }
  if (!labelPreviewForm.value.labelFile) {
    ElMessage.warning('请选择标签文件')
    return
  }

  labelPreviewDialogVisible.value = true
  currentOffset.value = 0
  labelPreviewData.value = null

  await nextTick()
  await loadLabelPreviewData()
}

// 加载标签预览数据
const loadLabelPreviewData = async () => {
  try {
    const response = await workflowAPI.previewLabelData(
      labelPreviewForm.value.dataFile,
      labelPreviewForm.value.labelFile,
      currentOffset.value,
      pageSize.value
    )
    labelPreviewData.value = response.data

    await nextTick()
    renderChart()
  } catch (error) {
    ElMessage.error('加载标签预览数据失败: ' + error.message)
  }
}

// 渲染K线图表
const renderChart = () => {
  if (!chartContainer.value || !labelPreviewData.value) return

  // 销毁旧的图表实例
  if (chartInstance) {
    chartInstance.dispose()
  }

  // 创建新的图表实例
  chartInstance = echarts.init(chartContainer.value)

  const klineData = labelPreviewData.value.kline_data

  // 准备数据
  const dates = klineData.map(item => item.datetime)
  const ohlcData = klineData.map(item => [item.open, item.close, item.low, item.high])
  const volumes = klineData.map(item => item.volume)
  const labels = klineData.map(item => item.label)

  // 准备标签标记数据
  const positiveLabels = []
  const negativeLabels = []
  const zeroLabels = []

  klineData.forEach((item, index) => {
    if (item.label !== null && item.label !== undefined) {
      // 根据标签正负值决定显示位置
      let yPosition
      if (item.label > 0) {
        // 正标签显示在K线上方（最高价上方一点点）
        yPosition = item.high * 1.005
      } else if (item.label < 0) {
        // 负标签显示在K线下方（最低价下方一点点）
        yPosition = item.low * 0.995
      } else {
        // 零标签显示在收盘价位置
        yPosition = item.close
      }

      const markData = {
        xAxis: index,
        yAxis: yPosition,
        value: item.label.toFixed(4),
        label: item.label
      }

      if (item.label > 0) {
        positiveLabels.push(markData)
      } else if (item.label < 0) {
        negativeLabels.push(markData)
      } else {
        zeroLabels.push(markData)
      }
    }
  })

  // 配置图表选项
  const option = {
    animation: false,
    legend: {
      data: ['K线', '成交量', '正标签', '负标签', '零标签'],
      top: 0
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function (params) {
        const dataIndex = params[0].dataIndex
        const kline = klineData[dataIndex]
        let html = `<div style="font-size: 12px;">
          <div><strong>${kline.datetime}</strong></div>
          <div>开: ${kline.open.toFixed(4)}</div>
          <div>高: ${kline.high.toFixed(4)}</div>
          <div>低: ${kline.low.toFixed(4)}</div>
          <div>收: ${kline.close.toFixed(4)}</div>
          <div>量: ${kline.volume.toFixed(2)}</div>`

        if (kline.label !== null && kline.label !== undefined) {
          const labelColor = kline.label > 0 ? '#67C23A' : kline.label < 0 ? '#F56C6C' : '#909399'
          html += `<div style="color: ${labelColor}; font-weight: bold;">标签: ${kline.label.toFixed(4)}</div>`
        } else {
          html += `<div style="color: #909399;">标签: 无</div>`
        }

        html += '</div>'
        return html
      }
    },
    axisPointer: {
      link: [{ xAxisIndex: 'all' }]
    },
    grid: [
      {
        left: '10%',
        right: '8%',
        top: '12%',
        height: '50%'
      },
      {
        left: '10%',
        right: '8%',
        top: '68%',
        height: '18%'
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        boundaryGap: true,
        axisLine: { onZero: false },
        splitLine: { show: false },
        axisLabel: {
          show: true,
          interval: Math.floor(dates.length / 10),
          rotate: 45
        },
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        boundaryGap: true,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      }
    ],
    yAxis: [
      {
        scale: true,
        splitArea: {
          show: true
        }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 0,
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        bottom: '2%',
        start: 0,
        end: 100
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: ohlcData,
        itemStyle: {
          color: '#ef232a',
          color0: '#14b143',
          borderColor: '#ef232a',
          borderColor0: '#14b143'
        },
        markPoint: {
          symbol: 'roundRect',
          symbolSize: [50, 20],
          label: {
            show: true,
            formatter: '{c}',
            fontSize: 11,
            color: '#fff',
            fontWeight: 'bold'
          },
          data: [
            ...positiveLabels.map(item => ({
              coord: [item.xAxis, item.yAxis],
              value: item.value,
              itemStyle: {
                color: '#67C23A',
                borderColor: '#fff',
                borderWidth: 1
              }
            })),
            ...negativeLabels.map(item => ({
              coord: [item.xAxis, item.yAxis],
              value: item.value,
              itemStyle: {
                color: '#F56C6C',
                borderColor: '#fff',
                borderWidth: 1
              }
            })),
            ...zeroLabels.map(item => ({
              coord: [item.xAxis, item.yAxis],
              value: item.value,
              itemStyle: {
                color: '#909399',
                borderColor: '#fff',
                borderWidth: 1
              }
            }))
          ]
        }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: function (params) {
            const index = params.dataIndex
            return ohlcData[index][1] >= ohlcData[index][0] ? '#ef232a' : '#14b143'
          }
        }
      }
    ]
  }

  chartInstance.setOption(option)

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
}

// 处理窗口大小变化
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 上一页
const prevPage = async () => {
  if (currentOffset.value > 0) {
    currentOffset.value = Math.max(0, currentOffset.value - pageSize.value)
    await loadLabelPreviewData()
  }
}

// 下一页
const nextPage = async () => {
  if (currentOffset.value + pageSize.value < labelPreviewData.value.total_rows) {
    currentOffset.value += pageSize.value
    await loadLabelPreviewData()
  }
}

// 组件卸载时清理
onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.feature-calculation {
  padding: 20px;
}

.calculation-card {
  margin-bottom: 20px;
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
}

.result-info p {
  margin: 5px 0;
}

:deep(.el-checkbox) {
  display: block;
  margin: 10px 0;
}
</style>
