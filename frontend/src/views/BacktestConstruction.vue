<template>
  <div class="backtest-construction">
    <el-row :gutter="20">
      <!-- 左侧：参数配置 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <h2>构建回测策略</h2>
          </template>

          <!-- 决策规则显示 -->
          <el-alert
            v-if="decisionRules.length > 0"
            :title="`已加载 ${decisionRules.length} 条决策规则`"
            type="success"
            :closable="false"
            style="margin-bottom: 20px;"
          />

          <el-form :model="form" label-width="140px">
            <!-- 特征数据文件选择 -->
            <el-form-item label="特征数据文件">
              <el-select
                v-model="form.featuresFile"
                placeholder="选择特征数据文件（文件名需包含 features）"
                filterable
                style="width: 100%;margin-bottom: 10px;"
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
              <el-button @click="loadFeaturesFiles" :icon="Refresh">刷新</el-button>
            </el-form-item>

            <el-alert
              v-if="form.featuresFile"
              :title="`已选择: ${form.featuresFile}`"
              :type="form.featuresFile.toLowerCase().includes('features') ? 'success' : 'error'"
              :closable="false"
              show-icon
              style="margin-bottom: 15px;"
            >
              <template v-if="!form.featuresFile.toLowerCase().includes('features')">
                <div style="color: #F56C6C">
                  警告：所选文件不包含 'features'，这可能不是特征文件！
                </div>
              </template>
            </el-alert>

            <el-divider content-position="left">回测参数</el-divider>

            <el-form-item label="回测类型">
              <el-radio-group v-model="form.backtestType">
                <el-radio label="long">开多单回测</el-radio>
                <el-radio label="short">开空单回测</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="过滤指标">
              <el-radio-group v-model="form.filterType">
                <el-radio label="rsi">RSI过滤</el-radio>
                <el-radio label="cti">CTI过滤</el-radio>
              </el-radio-group>
              <div style="margin-top: 5px; color: #909399; font-size: 13px;">
                <span v-if="form.backtestType === 'long' && form.filterType === 'rsi'">
                  开多单：RSI &lt; 30，价格上涨为盈利
                </span>
                <span v-if="form.backtestType === 'short' && form.filterType === 'rsi'">
                  开空单：RSI &gt; 70，价格下跌为盈利
                </span>
                <span v-if="form.backtestType === 'long' && form.filterType === 'cti'">
                  开多单：CTI &lt; -0.5，价格上涨为盈利
                </span>
                <span v-if="form.backtestType === 'short' && form.filterType === 'cti'">
                  开空单：CTI &gt; 0.5，价格下跌为盈利
                </span>
              </div>
            </el-form-item>

            <el-form-item label="未来K线数">
              <el-input-number
                v-model="form.lookForwardBars"
                :min="1"
                :max="100"
                :step="1"
              />
              <span style="margin-left: 10px; color: #909399; font-size: 13px">
                用于判断盈亏的未来K线根数
              </span>
            </el-form-item>

            <el-form-item label="盈利金额">
              <el-input-number
                v-model="form.winProfit"
                :min="0"
                :max="1000"
                :step="1"
              />
            </el-form-item>

            <el-form-item label="亏损金额">
              <el-input-number
                v-model="form.lossCost"
                :min="0"
                :max="1000"
                :step="1"
              />
            </el-form-item>

            <el-form-item label="初始余额">
              <el-input-number
                v-model="form.initialBalance"
                :min="0"
                :max="1000000"
                :step="100"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="startBacktest"
                :loading="loading"
                :disabled="!form.featuresFile || decisionRules.length === 0"
                :icon="TrendCharts"
              >
                开始回测
              </el-button>
              <el-button @click="goBack">返回模型分析</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 任务进度 -->
        <el-card v-if="taskId" style="margin-top: 20px;">
          <template #header>
            <h3>回测进度</h3>
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

        <!-- 决策规则详情 -->
        <el-card v-if="decisionRules.length > 0" style="margin-top: 20px;">
          <template #header>
            <h3>决策规则 ({{ decisionRules.length }} 条)</h3>
          </template>
          <el-collapse>
            <el-collapse-item
              v-for="rule in decisionRules.slice(0, 20)"
              :key="rule.rule_id"
              :name="rule.rule_id"
            >
              <template #title>
                <div style="display: flex; align-items: center; width: 100%;">
                  <el-tag size="small" style="margin-right: 10px;">规则 {{ rule.rule_id }}</el-tag>
                  <span style="flex: 1; font-size: 12px; color: #606266;">
                    置信度: {{ (rule.confidence * 100).toFixed(1) }}%
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
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>

      <!-- 右侧：回测结果 -->
      <el-col :span="10">
        <el-card v-if="result">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <h3>回测结果</h3>
              <el-tag :type="form.backtestType === 'long' ? 'success' : 'danger'" size="large">
                {{ form.backtestType === 'long' ? '开多单回测' : '开空单回测' }}
              </el-tag>
            </div>
          </template>

          <el-descriptions :column="1" border style="margin-bottom: 20px;">
            <el-descriptions-item label="总交易次数">{{ result.stats.total_trades }}</el-descriptions-item>
            <el-descriptions-item label="获胜次数">{{ result.stats.winning_trades }}</el-descriptions-item>
            <el-descriptions-item label="失败次数">{{ result.stats.losing_trades }}</el-descriptions-item>
            <el-descriptions-item label="胜率">
              <el-tag :type="result.stats.win_rate > 0.5 ? 'success' : 'danger'">
                {{ (result.stats.win_rate * 100).toFixed(2) }}%
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="初始余额">{{ result.stats.initial_balance.toFixed(2) }}</el-descriptions-item>
            <el-descriptions-item label="最终余额">{{ result.stats.final_balance.toFixed(2) }}</el-descriptions-item>
            <el-descriptions-item label="总收益">
              <span :style="{ color: result.stats.profit >= 0 ? '#67C23A' : '#F56C6C' }">
                {{ result.stats.profit.toFixed(2) }} ({{ (result.stats.profit_rate * 100).toFixed(2) }}%)
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="最大回撤">
              {{ (result.stats.max_drawdown * 100).toFixed(2) }}%
            </el-descriptions-item>
          </el-descriptions>

          <!-- 使用的决策规则 -->
          <div style="margin-top: 20px;">
            <h4>使用的决策规则 ({{ usedRules.length }} 条)</h4>
            <el-collapse style="margin-top: 10px;">
              <el-collapse-item
                v-for="rule in usedRules"
                :key="rule.rule_id"
                :name="rule.rule_id"
              >
                <template #title>
                  <div style="display: flex; align-items: center; width: 100%;">
                    <el-tag size="small" style="margin-right: 10px;">规则 {{ rule.rule_id }}</el-tag>
                    <span style="flex: 1; font-size: 12px; color: #606266;">
                      置信度: {{ (rule.confidence * 100).toFixed(1) }}%
                    </span>
                  </div>
                </template>
                <div class="rule-detail">
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
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>

          <!-- 资金曲线图 -->
          <div v-if="result.balance_curve" style="margin-top: 20px;">
            <h4>资金曲线</h4>
            <img
              :src="getImageUrl(result.plots_dir, result.balance_curve)"
              :key="result.plots_dir + result.balance_curve"
              style="width: 100%; border-radius: 4px;"
              alt="Balance Curve"
            />
          </div>

          <!-- 交易分布图 -->
          <div v-if="result.trades_distribution" style="margin-top: 20px;">
            <h4>交易分布</h4>
            <img
              :src="getImageUrl(result.plots_dir, result.trades_distribution)"
              :key="result.plots_dir + result.trades_distribution"
              style="width: 100%; border-radius: 4px;"
              alt="Trades Distribution"
            />
          </div>
        </el-card>

        <!-- 特征文件列表 -->
        <el-card :style="result ? 'margin-top: 20px;' : ''">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <h3>特征数据文件</h3>
              <el-button @click="loadFeaturesFiles" :icon="Refresh" circle size="small" />
            </div>
          </template>

          <el-table :data="featuresFiles" style="width: 100%;" max-height="300" size="small">
            <el-table-column prop="filename" label="文件名" show-overflow-tooltip />
            <el-table-column prop="size_mb" label="大小(MB)" width="80" />
            <el-table-column label="操作" width="80">
              <template #default="scope">
                <el-button size="small" type="primary" @click="selectFeaturesFile(scope.row)">
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
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, TrendCharts } from '@element-plus/icons-vue'
import { workflowAPI } from '@/api/workflow'
import { useModuleStatesStore } from '@/stores/moduleStates'
import { useModuleState } from '@/composables/useModuleState'

const router = useRouter()
const route = useRoute()
const moduleStore = useModuleStatesStore()

// 从store恢复状态
const form = ref({
  ...moduleStore.backtestConstructionState.form,
  filterType: moduleStore.backtestConstructionState.form.filterType || 'rsi'
})
const loading = ref(false)
const taskId = ref(moduleStore.backtestConstructionState.taskId)
const taskStatus = ref(moduleStore.backtestConstructionState.taskStatus)
const progress = ref(moduleStore.backtestConstructionState.progress)
const statusMessage = ref(moduleStore.backtestConstructionState.statusMessage)
const result = ref(moduleStore.backtestConstructionState.result)

const featuresFiles = ref([...moduleStore.backtestConstructionState.featuresFiles])
const decisionRules = ref([...moduleStore.backtestConstructionState.decisionRules])

// 使用状态持久化
useModuleState('backtestConstruction', {
  form,
  taskId,
  taskStatus,
  progress,
  statusMessage,
  result,
  featuresFiles,
  decisionRules
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

const usedRules = computed(() => {
  const targetClass = form.value.backtestType === 'long' ? 1 : 0
  return decisionRules.value.filter(rule => rule.predicted_class === targetClass)
})

onMounted(() => {
  loadFeaturesFiles()

  // 从路由参数中获取分析结果
  if (route.query.analysis_result) {
    try {
      const analysisResult = JSON.parse(route.query.analysis_result)
      decisionRules.value = analysisResult.rules || []
      ElMessage.success(`已加载 ${decisionRules.value.length} 条决策规则`)
    } catch (error) {
      ElMessage.error('解析分析结果失败')
    }
  }

  // 从路由参数中获取特征文件名
  if (route.query.features_file) {
    console.log('从路由参数获取特征文件名:', route.query.features_file)
    form.value.featuresFile = route.query.features_file

    // 验证文件名是否包含 features
    if (route.query.features_file.toLowerCase().includes('features')) {
      ElMessage.info(`已自动选择特征文件: ${route.query.features_file}`)
    } else {
      ElMessage.warning(`路由参数中的文件名不是特征文件: ${route.query.features_file}，请手动选择`)
      form.value.featuresFile = ''  // 清空错误的文件名
    }
  }
})

const loadFeaturesFiles = async () => {
  try {
    const response = await workflowAPI.listDataFiles('processed')
    // 只显示特征文件（文件名包含 features 的）
    featuresFiles.value = (response.data.files || []).filter(file =>
      file.filename.toLowerCase().includes('features')
    )

    if (featuresFiles.value.length === 0) {
      ElMessage.warning('未找到特征文件，请先运行特征计算模块')
    }
  } catch (error) {
    ElMessage.error('加载特征文件列表失败')
  }
}

const selectFeaturesFile = (file) => {
  form.value.featuresFile = file.filename
  ElMessage.info(`已选择: ${file.filename}`)
}

const startBacktest = async () => {
  if (!form.value.featuresFile) {
    ElMessage.warning('请选择特征数据文件')
    return
  }

  // 验证是否为特征文件
  if (!form.value.featuresFile.toLowerCase().includes('features')) {
    ElMessage.error('请选择特征文件（文件名应包含 features）')
    return
  }

  if (decisionRules.value.length === 0) {
    ElMessage.warning('没有决策规则，无法进行回测')
    return
  }

  loading.value = true
  try {
    console.log('发送回测请求，特征文件:', form.value.featuresFile)
    console.log('决策规则数量:', decisionRules.value.length)
    if (decisionRules.value.length > 0) {
      console.log('第一条规则:', JSON.stringify(decisionRules.value[0], null, 2))
    }

    const response = await workflowAPI.startBacktestConstruction({
      features_file: form.value.featuresFile,
      decision_rules: decisionRules.value,
      backtest_type: form.value.backtestType,
      filter_type: form.value.filterType,
      look_forward_bars: form.value.lookForwardBars,
      win_profit: form.value.winProfit,
      loss_cost: form.value.lossCost,
      initial_balance: form.value.initialBalance
    })

    taskId.value = response.data.task_id
    taskStatus.value = response.data.status
    progress.value = 0
    statusMessage.value = ''
    result.value = null
    ElMessage.success('回测任务已启动')

    pollTaskStatus()
  } catch (error) {
    ElMessage.error('启动回测任务失败: ' + error.message)
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
        statusMessage.value = response.data.result.status || response.data.result.message || ''
      }

      if (response.data.status === 'success') {
        result.value = response.data.result
        progress.value = 100
        clearInterval(interval)
        console.log('回测完成，结果目录:', response.data.result.plots_dir)
        console.log('回测类型:', response.data.result.backtest_type || form.value.backtestType)
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

const getImageUrl = (plotsDir, filename) => {
  // 添加时间戳参数避免浏览器缓存
  const timestamp = new Date().getTime()
  return `http://localhost:8000/static/plots/${plotsDir}/${filename}?t=${timestamp}`
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.backtest-construction {
  padding: 20px;
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
</style>
