<template>
  <div class="data-download">
    <el-row :gutter="20">
      <!-- 左侧：下载表单 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <h2>数据下载</h2>
          </template>

          <el-form :model="form" label-width="120px">
            <el-form-item label="交易对">
              <el-input v-model="form.symbol" placeholder="ETHUSDT" />
            </el-form-item>

            <el-form-item label="K线周期">
              <el-select v-model="form.interval" placeholder="选择时间间隔">
                <el-option label="1分钟" value="1m" />
                <el-option label="5分钟" value="5m" />
                <el-option label="15分钟" value="15m" />
                <el-option label="30分钟" value="30m" />
                <el-option label="1小时" value="1h" />
                <el-option label="2小时" value="2h" />
                <el-option label="4小时" value="4h" />
                <el-option label="1天" value="1d" />
              </el-select>
            </el-form-item>

            <el-form-item label="开始日期">
              <el-date-picker
                v-model="form.startDate"
                type="date"
                placeholder="选择开始日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>

            <el-form-item label="结束日期">
              <el-date-picker
                v-model="form.endDate"
                type="date"
                placeholder="选择结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>

            <el-form-item label="代理设置">
              <el-input v-model="form.proxy" placeholder="http://127.0.0.1:10808 (可选)"/>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="startDownload" :loading="loading">
                开始下载
              </el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <div v-if="taskId" class="task-status">
            <h3>下载状态</h3>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="任务ID">{{ taskId }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="statusType">{{ taskStatus }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="进度" v-if="progress !== null">
                <el-progress :percentage="progress" :status="progressStatus" />
              </el-descriptions-item>
              <el-descriptions-item label="当前状态" v-if="statusMessage">
                {{ statusMessage }}
              </el-descriptions-item>
            </el-descriptions>

            <div v-if="result" class="result-info">
              <h4>下载结果</h4>
              <p>文件名: {{ result.filename }}</p>
              <p>数据行数: {{ result.total_rows }}</p>
              <p>开始时间: {{ result.start_time }}</p>
              <p>结束时间: {{ result.end_time }}</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：文件列表 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <h2>数据文件列表</h2>
              <el-button @click="loadFiles" :icon="Refresh" circle />
            </div>
          </template>

          <el-table :data="files" style="width: 100%" max-height="600">
            <el-table-column prop="filename" label="文件名" width="300" show-overflow-tooltip />
            <el-table-column prop="size_mb" label="大小(MB)" width="100" />
            <el-table-column prop="modified_time" label="修改时间" width="180" />
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button size="small" @click="previewFile(scope.row)">预览</el-button>
                <el-popconfirm
                  title="确定删除此文件吗?"
                  @confirm="deleteFile(scope.row.filename)"
                >
                  <template #reference>
                    <el-button size="small" type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
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

        <h4>数据预览 (前10行)</h4>
        <el-table :data="previewData.preview" style="width: 100%" max-height="400">
          <el-table-column
            v-for="col in previewData.columns"
            :key="col"
            :prop="col"
            :label="col"
            width="150"
          />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { workflowAPI } from '@/api/workflow'
import { useModuleStatesStore } from '@/stores/moduleStates'
import { useModuleState } from '@/composables/useModuleState'

const moduleStore = useModuleStatesStore()

// 从store恢复状态
const form = ref({ ...moduleStore.dataDownloadState.form })
const loading = ref(false)
const taskId = ref(moduleStore.dataDownloadState.taskId)
const taskStatus = ref(moduleStore.dataDownloadState.taskStatus)
const progress = ref(moduleStore.dataDownloadState.progress)
const statusMessage = ref(moduleStore.dataDownloadState.statusMessage)
const result = ref(moduleStore.dataDownloadState.result)
const files = ref([...moduleStore.dataDownloadState.files])
const previewDialogVisible = ref(moduleStore.dataDownloadState.previewDialogVisible)
const previewData = ref(moduleStore.dataDownloadState.previewData)

// 使用状态持久化
useModuleState('dataDownload', {
  form,
  taskId,
  taskStatus,
  progress,
  statusMessage,
  result,
  files,
  previewDialogVisible,
  previewData
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

const progressStatus = computed(() => {
  if (taskStatus.value === 'success') return 'success'
  if (taskStatus.value === 'failure') return 'exception'
  return undefined
})

onMounted(() => {
  // 设置默认日期
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  form.value.startDate = yesterday.toISOString().split('T')[0]
  form.value.endDate = today.toISOString().split('T')[0]
  form.value.proxy = 'http://127.0.0.1:10808'

  loadFiles()
})

const startDownload = async () => {
  if (!form.value.startDate || !form.value.endDate) {
    ElMessage.warning('请选择开始和结束日期')
    return
  }

  loading.value = true
  try {
    const response = await workflowAPI.startDataDownload({
      symbol: form.value.symbol,
      start_date: form.value.startDate,
      end_date: form.value.endDate,
      interval: form.value.interval,
      proxy: form.value.proxy || null
    })

    taskId.value = response.data.task_id
    taskStatus.value = response.data.status
    progress.value = 0
    result.value = null
    ElMessage.success('数据下载任务已启动')

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
        ElMessage.success('数据下载完成')
        loadFiles()
      } else if (response.data.status === 'failure') {
        clearInterval(interval)
        ElMessage.error('数据下载失败: ' + response.data.error)
      }
    } catch (error) {
      clearInterval(interval)
      ElMessage.error('查询任务状态失败')
    }
  }, 2000)
}

const loadFiles = async () => {
  try {
    const response = await workflowAPI.listDataFiles('raw')
    files.value = response.data.files
  } catch (error) {
    ElMessage.error('加载文件列表失败')
  }
}

const deleteFile = async (filename) => {
  try {
    await workflowAPI.deleteDataFile(filename, 'raw')
    ElMessage.success('文件删除成功')
    loadFiles()
  } catch (error) {
    ElMessage.error('删除文件失败')
  }
}

const previewFile = async (file) => {
  try {
    const response = await workflowAPI.previewDataFile(file.filename, 'raw')
    previewData.value = response.data
    previewDialogVisible.value = true
  } catch (error) {
    ElMessage.error('预览文件失败')
  }
}
</script>

<style scoped>
.data-download {
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

.result-info p {
  margin: 5px 0;
}
</style>
