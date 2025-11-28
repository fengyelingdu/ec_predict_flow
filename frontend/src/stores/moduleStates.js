import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useModuleStatesStore = defineStore('moduleStates', () => {
  // 数据下载模块状态
  const dataDownloadState = ref({
    form: {
      symbol: 'ETHUSDT',
      startDate: '',
      endDate: '',
      interval: '1m',
      proxy: 'http://127.0.0.1:10808'
    },
    taskId: '',
    taskStatus: '',
    progress: null,
    statusMessage: '',
    result: null,
    files: [],
    previewDialogVisible: false,
    previewData: null
  })

  // 特征计算模块状态
  const featureCalculationState = ref({
    featureForm: {
      dataFile: '',
      alphaTypes: ['alpha158']
    },
    labelForm: {
      dataFile: '',
      window: 9,
      lookForward: 10
    },
    featureTaskId: '',
    featureTaskStatus: '',
    featureProgress: null,
    featureStatusMessage: '',
    featureResult: null,
    labelTaskId: '',
    labelTaskStatus: '',
    labelProgress: null,
    labelStatusMessage: '',
    labelResult: null,
    rawFiles: [],
    processedFiles: [],
    activeTab: 'raw',
    previewDialogVisible: false,
    previewData: null,
    calculatedAlphas: {}
  })

  // 模型训练模块状态
  const modelTrainingState = ref({
    form: {
      featuresFile: '',
      labelsFile: '',
      numBoostRound: 500
    },
    taskId: '',
    taskStatus: '',
    progress: null,
    statusMessage: '',
    result: null,
    processedFiles: [],
    modelFiles: [],
    activeTab: 'processed',
    activeCollapse: ['features', 'labels']
  })

  // 模型解释模块状态
  const modelInterpretationState = ref({
    form: {
      modelFile: ''
    },
    taskId: '',
    taskStatus: '',
    progress: null,
    statusMessage: '',
    detailMessage: '',
    result: null,
    modelFiles: [],
    shapPlotsDirs: [],
    showPlotsDialog: false,
    currentPlotFiles: [],
    selectedPlotIndex: 0,
    viewMode: 'list',
    currentPage: 1
  })

  // 模型分析模块状态
  const modelAnalysisState = ref({
    form: {
      modelFile: '',
      selectedFeatures: [],
      maxDepth: 3,
      minSamplesSplit: 100
    },
    taskId: '',
    taskStatus: '',
    progress: null,
    statusMessage: '',
    result: null,
    modelFiles: [],
    shapTop20Features: []
  })

  // 构建回测模块状态
  const backtestConstructionState = ref({
    form: {
      featuresFile: '',
      backtestType: 'long',
      lookForwardBars: 10,
      winProfit: 4,
      lossCost: 5,
      initialBalance: 1000
    },
    taskId: '',
    taskStatus: '',
    progress: null,
    statusMessage: '',
    result: null,
    featuresFiles: [],
    decisionRules: []
  })

  // 执行回测模块状态
  const backtestExecutionState = ref({
    form: {
      dataFile: '',
      strategyConfig: '{}'
    },
    taskId: '',
    taskStatus: '',
    result: null
  })

  // 保存各模块状态的函数
  function saveDataDownloadState(state) {
    dataDownloadState.value = { ...dataDownloadState.value, ...state }
  }

  function saveFeatureCalculationState(state) {
    featureCalculationState.value = { ...featureCalculationState.value, ...state }
  }

  function saveModelTrainingState(state) {
    modelTrainingState.value = { ...modelTrainingState.value, ...state }
  }

  function saveModelInterpretationState(state) {
    modelInterpretationState.value = { ...modelInterpretationState.value, ...state }
  }

  function saveModelAnalysisState(state) {
    modelAnalysisState.value = { ...modelAnalysisState.value, ...state }
  }

  function saveBacktestConstructionState(state) {
    backtestConstructionState.value = { ...backtestConstructionState.value, ...state }
  }

  function saveBacktestExecutionState(state) {
    backtestExecutionState.value = { ...backtestExecutionState.value, ...state }
  }

  // 重置各模块状态的函数
  function resetDataDownloadState() {
    dataDownloadState.value = {
      form: {
        symbol: 'ETHUSDT',
        startDate: '',
        endDate: '',
        interval: '1m',
        proxy: 'http://127.0.0.1:10808'
      },
      taskId: '',
      taskStatus: '',
      progress: null,
      statusMessage: '',
      result: null,
      files: [],
      previewDialogVisible: false,
      previewData: null
    }
  }

  function resetAllStates() {
    resetDataDownloadState()
    // 可以添加其他模块的重置函数
  }

  return {
    // 状态
    dataDownloadState,
    featureCalculationState,
    modelTrainingState,
    modelInterpretationState,
    modelAnalysisState,
    backtestConstructionState,
    backtestExecutionState,

    // 保存状态的方法
    saveDataDownloadState,
    saveFeatureCalculationState,
    saveModelTrainingState,
    saveModelInterpretationState,
    saveModelAnalysisState,
    saveBacktestConstructionState,
    saveBacktestExecutionState,

    // 重置状态的方法
    resetDataDownloadState,
    resetAllStates
  }
})
