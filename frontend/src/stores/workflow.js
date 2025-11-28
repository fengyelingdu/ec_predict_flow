import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWorkflowStore = defineStore('workflow', () => {
  const currentStage = ref('data-download')
  const tasks = ref({
    dataDownload: null,
    featureCalculation: null,
    modelTraining: null,
    modelInterpretation: null,
    llmAnalysis: null,
    backtestConstruction: null,
    backtestExecution: null
  })

  const stageResults = ref({
    dataDownload: null,
    featureCalculation: null,
    modelTraining: null,
    modelInterpretation: null,
    llmAnalysis: null,
    backtestConstruction: null,
    backtestExecution: null
  })

  function setCurrentStage(stage) {
    currentStage.value = stage
  }

  function setTaskId(stage, taskId) {
    tasks.value[stage] = taskId
  }

  function setStageResult(stage, result) {
    stageResults.value[stage] = result
  }

  function clearWorkflow() {
    tasks.value = {
      dataDownload: null,
      featureCalculation: null,
      modelTraining: null,
      modelInterpretation: null,
      llmAnalysis: null,
      backtestConstruction: null,
      backtestExecution: null
    }
    stageResults.value = {
      dataDownload: null,
      featureCalculation: null,
      modelTraining: null,
      modelInterpretation: null,
      llmAnalysis: null,
      backtestConstruction: null,
      backtestExecution: null
    }
  }

  return {
    currentStage,
    tasks,
    stageResults,
    setCurrentStage,
    setTaskId,
    setStageResult,
    clearWorkflow
  }
})
