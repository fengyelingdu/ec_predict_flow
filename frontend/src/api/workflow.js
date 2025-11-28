import axios from 'axios'

const API_BASE_URL = '/api/v1/workflow'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const workflowAPI = {
  startDataDownload(params) {
    return api.post('/data-download', params)
  },

  startFeatureCalculation(params) {
    return api.post('/feature-calculation', params)
  },

  startLabelCalculation(params) {
    return api.post('/label-calculation', params)
  },

  startModelTraining(params) {
    return api.post('/model-training', params)
  },

  startModelInterpretation(params) {
    return api.post('/model-interpretation', params)
  },

  startModelAnalysis(params) {
    return api.post('/model-analysis', params)
  },

  startBacktestConstruction(params) {
    return api.post('/backtest-construction', params)
  },

  startBacktestExecution(params) {
    return api.post('/backtest-execution', params)
  },

  getTaskStatus(taskId) {
    return api.get(`/task/${taskId}`)
  },

  // 数据文件管理接口
  listDataFiles(directory = 'raw') {
    return api.get('/data-files', { params: { directory } })
  },

  deleteDataFile(filename, directory = 'raw') {
    return api.delete(`/data-files/${filename}`, { params: { directory } })
  },

  previewDataFile(filename, directory = 'raw', rows = 10) {
    return api.get(`/data-files/${filename}/preview`, { params: { directory, rows } })
  },

  // 获取 SHAP 图表目录下的文件列表
  getPlotFiles(dirname) {
    return api.get(`/plots/${dirname}/files`)
  },

  // 删除 SHAP 图表目录
  deletePlotDirectory(dirname) {
    return api.delete(`/plots/${dirname}`)
  },

  // 预览标签文件的K线和标签数据
  previewLabelData(dataFile, labelFile, offset = 0, limit = 100) {
    return api.get('/labels/preview', { params: { data_file: dataFile, label_file: labelFile, offset, limit } })
  }
}

export default workflowAPI
