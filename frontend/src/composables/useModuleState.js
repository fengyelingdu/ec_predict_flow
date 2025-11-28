import { onBeforeUnmount, watch } from 'vue'
import { useModuleStatesStore } from '@/stores/moduleStates'

/**
 * 通用的模块状态持久化 composable
 * @param {string} moduleName - 模块名称
 * @param {object} stateRefs - 需要持久化的状态引用对象
 * @returns {object} - 包含保存和恢复状态的方法
 */
export function useModuleState(moduleName, stateRefs) {
  const moduleStore = useModuleStatesStore()

  // 获取对应模块的状态键名
  const stateKey = `${moduleName}State`

  // 保存状态到store
  const saveState = () => {
    const state = {}
    Object.keys(stateRefs).forEach(key => {
      const ref = stateRefs[key]
      // 深拷贝以避免引用问题
      state[key] = JSON.parse(JSON.stringify(ref.value))
    })

    const saveMethod = `save${moduleName.charAt(0).toUpperCase() + moduleName.slice(1)}State`
    if (typeof moduleStore[saveMethod] === 'function') {
      moduleStore[saveMethod](state)
    }
  }

  // 从store恢复状态
  const restoreState = () => {
    const savedState = moduleStore[stateKey]
    if (savedState) {
      Object.keys(stateRefs).forEach(key => {
        if (savedState[key] !== undefined) {
          // 深拷贝以避免引用问题
          stateRefs[key].value = JSON.parse(JSON.stringify(savedState[key]))
        }
      })
    }
  }

  // 组件卸载前自动保存状态
  onBeforeUnmount(() => {
    saveState()
  })

  return {
    saveState,
    restoreState
  }
}
