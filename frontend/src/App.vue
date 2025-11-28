<template>
  <div id="app">
    <el-container class="layout-container">
      <el-header class="header">
        <div class="header-content">
          <h1>EC Predict Flow</h1>
          <span class="subtitle">事件合约预测工作流</span>
        </div>
      </el-header>
      <el-container>
        <el-aside width="200px" class="sidebar">
          <el-menu
            :default-active="$route.path"
            router
            class="el-menu-vertical"
          >
            <el-menu-item index="/">
              <el-icon><HomeFilled /></el-icon>
              <span>工作流概览</span>
            </el-menu-item>
            <el-menu-item index="/data-download">
              <el-icon><Download /></el-icon>
              <span>数据下载</span>
            </el-menu-item>
            <el-menu-item index="/feature-calculation">
              <el-icon><Operation /></el-icon>
              <span>特征计算</span>
            </el-menu-item>
            <el-menu-item index="/model-training">
              <el-icon><TrendCharts /></el-icon>
              <span>模型训练</span>
            </el-menu-item>
            <el-menu-item index="/model-interpretation">
              <el-icon><PieChart /></el-icon>
              <span>模型解释</span>
            </el-menu-item>
            <el-menu-item index="/model-analysis">
              <el-icon><ChatDotRound /></el-icon>
              <span>模型分析</span>
            </el-menu-item>
            <el-menu-item index="/backtest-construction">
              <el-icon><Setting /></el-icon>
              <span>构建回测</span>
            </el-menu-item>
            <el-menu-item index="/backtest-execution" style="display: none;">
              <el-icon><DataAnalysis /></el-icon>
              <span>执行回测</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  height: 100vh;
}

.layout-container {
  height: 100vh;
}

.header {
  background: #3398f7;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content h1 {
  font-size: 24px;
  margin-right: 20px;
}

.header-content .subtitle {
  font-size: 14px;
  opacity: 0.9;
}

.sidebar {
  background-color: #f5f7fa;
  border-right: 1px solid #e4e7ed;
}

.main-content {
  background-color: #ffffff;
  padding: 20px;
  overflow-y: auto;
}

.el-menu {
  border-right: none;
}
</style>
