# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

EC Predict Flow 是一个事件合约预测工作流系统,提供从数据获取到策略回测的完整量化交易工作流程。系统采用前后端分离架构,使用异步任务队列处理长时间运行的机器学习和回测任务。

## 核心技术栈

- **后端**: Python + FastAPI + Celery + Redis
- **前端**: Vue 3 + Vite + Element Plus + Pinia
- **机器学习**: LightGBM + SHAP
- **数据处理**: Pandas + NumPy + TA-Lib
- **数据源**: Binance Futures API

## 开发环境设置

### 后端启动流程

```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 配置环境变量 (创建 .env 文件)
# 必需配置:
# - REDIS_URL (默认: redis://localhost:6379/0)
# - CELERY_BROKER_URL (默认: redis://localhost:6379/0)
# 可选配置:
# - ANTHROPIC_API_KEY (用于模型分析中的LLM功能)
# - BINANCE_PROXY (如需代理访问Binance API)

# 3. 启动 Redis (必须先启动)
redis-server

# 4. 启动 Celery Worker (Windows 使用 --pool=solo)
celery -A app.core.celery_app worker --loglevel=info --pool=solo

# 5. 启动 FastAPI 服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# 或使用: python run.py
```

### 前端启动流程

```bash
cd frontend
npm install
npm run dev
# 访问: http://localhost:5173
```

### API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目架构

### 工作流程顺序

系统包含6个主要模块,必须按以下顺序执行:

1. **数据下载** - 从Binance下载K线数据
2. **特征计算** - 计算量价特征因子
3. **标签计算** - 为涨跌事件设置真实值标签 (在特征计算后进行)
4. **模型训练** - 使用LightGBM训练预测模型
5. **模型解释** - 使用SHAP生成特征重要性可视化
6. **模型分析** - 使用代理模型筛选关键特征和阈值
7. **构建回测** - 根据特征阈值构建并执行回测策略

### 后端目录结构

```
backend/
├── app/
│   ├── api/endpoints/          # API路由
│   │   └── workflow.py         # 主工作流API端点
│   ├── core/                   # 核心配置
│   │   ├── config.py          # 环境变量和路径配置
│   │   └── celery_app.py      # Celery配置和任务注册
│   ├── tasks/                  # Celery异步任务
│   │   ├── data_download.py           # 任务1: K线数据下载
│   │   ├── feature_calculation.py     # 任务2: 特征计算
│   │   ├── label_calculation.py       # 任务3: 标签计算
│   │   ├── model_training.py          # 任务4: 模型训练
│   │   ├── model_interpretation.py    # 任务5: SHAP解释
│   │   ├── model_analysis.py          # 任务6: 代理模型分析
│   │   └── backtest_construction.py   # 任务7: 回测构建
│   ├── services/               # 业务逻辑层
│   │   ├── data_processor.py          # 特征工程 (Alpha158因子)
│   │   ├── label_processor.py         # 标签生成逻辑
│   │   ├── alpha_ch.py                # 中国市场Alpha因子
│   │   ├── alphas101.py               # WorldQuant Alpha101因子
│   │   ├── alphas191.py               # Alpha191因子
│   │   ├── calculate_indicator.py     # 技术指标计算
│   │   └── data_file_service.py       # 文件管理服务
│   ├── schemas/                # Pydantic数据模型
│   │   └── workflow.py         # API请求/响应模型
│   └── main.py                 # FastAPI应用入口
├── data/                       # 数据目录 (运行时自动创建)
│   ├── raw/                   # 原始K线数据 (.pkl)
│   ├── processed/             # 处理后的特征/标签 (.pkl)
│   ├── models/                # 训练的模型文件 (.txt)
│   └── plots/                 # SHAP可视化图表 (.png)
└── run.py                      # 快速启动脚本
```

### 前端目录结构

```
frontend/
├── src/
│   ├── views/                  # 页面组件 (对应7个工作流步骤)
│   ├── api/                    # API调用封装
│   ├── stores/                 # Pinia状态管理
│   ├── composables/            # Vue组合式函数
│   └── router/                 # 路由配置
└── vite.config.js
```

## 关键技术要点

### 异步任务处理

- 所有长时间运行的任务都通过Celery异步执行
- 任务状态追踪: `PENDING` -> `PROGRESS` -> `SUCCESS`/`FAILURE`
- 获取任务状态: `GET /api/v1/workflow/task/{task_id}`
- Windows环境必须使用 `--pool=solo` 参数运行Celery

### 数据流转

1. 原始数据存储为 Pickle 格式 (`.pkl`), 包含 DatetimeIndex
2. 特征计算后包含 `feature_*` 列
3. 标签计算后包含 `label_*` 列
4. 模型文件为 LightGBM 文本格式 (`.txt`)
5. SHAP图表存储在 `data/plots/{model_name}/` 目录

### 特征工程

- **Alpha158**: 158个技术指标因子 (KBar, Price, Rolling)
- **Alpha101**: WorldQuant 101个Alpha因子
- **Alpha191**: 191个Alpha因子
- **Alpha_CH**: 中国市场特色因子
- 可通过 `alpha_types` 参数选择计算哪些因子类型

### 标签生成

- 支持回归标签 (`label_type: regression`) 和分类标签 (`label_type: classification`)
- 可选过滤器: `ewm` (指数加权移动), `ma` (移动平均), `none`
- `window`: 计算标签的回溯窗口
- `look_forward`: 前瞻周期 (预测未来N个bar的收益)

### 模型训练

- 使用 LightGBM 进行二分类/回归
- 自动处理特征-标签对齐
- 删除非特征列 (datetime, open, high, low, close, volume等)
- 输出包含: 训练准确率, 验证准确率, 特征重要性

### SHAP解释

- 生成 summary_plot, waterfall_plot, force_plot
- 计算每个特征的SHAP值分布
- 结果存储在 `data/plots/{timestamp}_shap/`

### 回测系统

- 基于规则的回测引擎 (decision_rules)
- 支持多种回测类型: `long` (做多), `short` (做空), `both` (双向)
- 可配置盈亏参数: `win_profit`, `loss_cost`
- 输出包含: 总收益率, 夏普比率, 最大回撤, 交易次数等

## 常用开发命令

### 清理Redis缓存

```bash
cd backend
python clear_redis.py
```

### 调试单个Celery任务

```python
# 在Python REPL中
from app.tasks.data_download import download_kline_data
result = download_kline_data.delay(
    symbol="ETHUSDT",
    start_date="2024-01-01",
    end_date="2024-01-31",
    interval="1m"
)
print(result.status)
print(result.result)
```

### 检查数据文件

```bash
# 列出原始数据
GET /api/v1/workflow/data-files?directory=raw

# 预览文件
GET /api/v1/workflow/data-files/{filename}/preview?directory=raw&rows=10

# 删除文件
DELETE /api/v1/workflow/data-files/{filename}?directory=raw
```

## 配置说明

### 环境变量 (.env)

```bash
# Redis配置
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API密钥 (可选)
ANTHROPIC_API_KEY=sk-xxx

# Binance代理 (可选)
BINANCE_PROXY=http://127.0.0.1:7890
```

### Celery任务配置 (app/core/celery_app.py)

- `task_time_limit`: 3600秒 (1小时)
- `task_soft_time_limit`: 3300秒
- `result_expires`: 3600秒 (结果缓存1小时)
- `worker_max_tasks_per_child`: 1000 (防止内存泄漏)

## 故障排查

### Celery Worker无法启动

- 确保Redis已启动: `redis-cli ping` 应返回 `PONG`
- Windows系统必须使用: `celery -A app.core.celery_app worker --pool=solo`
- 检查端口占用: `netstat -ano | findstr 6379`

### 任务卡在PENDING状态

- 检查Celery Worker是否运行
- 查看Worker日志中的错误信息
- 使用 `clear_redis.py` 清理过期任务

### 数据文件路径错误

- 所有数据文件使用相对文件名 (不含路径)
- 系统自动将文件放入对应目录:
  - 原始数据 -> `data/raw/`
  - 特征/标签 -> `data/processed/`
  - 模型 -> `data/models/`
  - 图表 -> `data/plots/`

### TA-Lib安装失败

- Windows: 需先安装编译好的wheel文件
- 下载地址: https://github.com/cgohlke/talib-build/releases
- 安装: `pip install TA_Lib-0.4.28-cp311-cp311-win_amd64.whl`

## 注意事项

1. **任务顺序依赖**: 必须按照工作流顺序执行,后续任务依赖前序任务的输出文件
2. **文件命名**: 生成的文件名包含时间戳,确保任务间文件名匹配
3. **内存管理**: 大数据集处理时注意Pandas DataFrame内存占用
4. **异步通信**: 前端轮询任务状态 (建议500ms间隔)
5. **CORS配置**: 开发环境允许 localhost:5173 和 localhost:3000
6. **静态文件**: SHAP图表通过 `/static/plots/` 路由访问
