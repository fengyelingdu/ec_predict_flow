# EC Predict Flow 技术文档

## 文档信息

- **版本**: 2.1 (Opus 4.5 深度分析 + V1.0 内容整合版)
- **生成日期**: 2025-11-28
- **项目类型**: 事件合约预测工作流系统 (量化交易平台)
- **文档字数**: 约 15,000+ 字

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [技术栈详解](#3-技术栈详解)
4. [工作流程设计](#4-工作流程设计)
5. [后端核心模块](#5-后端核心模块)
6. [工作流任务详解](#6-工作流任务详解)
7. [特征工程系统](#7-特征工程系统)
8. [机器学习管道](#8-机器学习管道)
9. [回测引擎](#9-回测引擎)
10. [前端架构](#10-前端架构)
11. [API接口规范](#11-api接口规范)
12. [数据流设计](#12-数据流设计)
13. [部署与运维](#13-部署与运维)
14. [常见问题解答](#14-常见问题解答)
15. [开发指南](#15-开发指南)

---

## 1. 项目概述

### 1.1 项目简介

EC Predict Flow 是一个完整的量化交易工作流平台，专注于加密货币事件合约的预测和回测。系统采用前后端分离架构，使用机器学习技术（LightGBM）进行价格趋势预测，并通过SHAP进行模型可解释性分析，最终构建回测策略验证交易信号的有效性。

### 1.2 核心价值

| 特性 | 描述 |
|------|------|
| **端到端流程** | 数据下载 → 特征计算 → 标签生成 → 模型训练 → 模型解释 → 策略回测 |
| **专业特征库** | 集成 Alpha158/216/101/191 等专业量化因子库 |
| **可解释AI** | 基于 SHAP 的模型解释和代理决策树提取 |
| **灵活回测** | 支持多空双向策略、自定义盈亏参数、RSI/CTI 过滤 |

### 1.3 工作流程图

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   数据下载   │───▶│   特征计算   │───▶│   标签计算   │
│  Binance    │    │ Alpha系列   │    │ RSI/CTI过滤 │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
        ┌─────────────────────────────────────┘
        ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   模型训练   │───▶│   模型解释   │───▶│   模型分析   │
│  LightGBM   │    │    SHAP     │    │  代理决策树  │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
        ┌─────────────────────────────────────┘
        ▼
┌─────────────┐
│   构建回测   │
│  策略执行    │
└─────────────┘
```

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                             │
│  Vue 3 + Element Plus + ECharts (http://localhost:5173)    │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/REST API
┌─────────────────────▼───────────────────────────────────────┐
│                     API网关层                                │
│  FastAPI (http://localhost:8000/api/v1)                    │
│  - CORS中间件                                               │
│  - 静态文件服务 (/static/plots)                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼─────────┐     ┌──────────▼──────────┐
│  Celery Worker  │     │   Redis Broker      │
│  (异步任务执行)   │◄────┤   (任务队列)        │
└───────┬─────────┘     └─────────────────────┘
        │
        │ 调用服务层
        │
┌───────▼──────────────────────────────────────────────────────┐
│                       业务逻辑层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 数据下载服务  │  │ 特征工程服务  │  │ 标签处理服务  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 模型训练服务  │  │ SHAP解释服务 │  │ 回测执行服务  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────┬──────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────┐
│                       数据持久层                              │
│  data/raw/        - 原始K线数据 (.pkl)                       │
│  data/processed/  - 特征和标签数据 (.pkl)                    │
│  data/models/     - 训练的模型文件 (.pkl)                    │
│  data/plots/      - SHAP图表和回测图表 (.png)                │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
EC_Predict_Flow/
├── backend/                          # 后端服务
│   ├── app/
│   │   ├── api/endpoints/workflow.py # 18个API端点
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic配置管理
│   │   │   └── celery_app.py         # Celery应用配置
│   │   ├── schemas/workflow.py       # 请求/响应模型
│   │   ├── services/
│   │   │   ├── data_processor.py     # 特征工程核心 (Alpha158/216)
│   │   │   ├── label_processor.py    # 标签生成器
│   │   │   ├── calculate_indicator.py # 技术指标 (RSI/CTI等)
│   │   │   ├── alphas101.py          # Alpha101因子库
│   │   │   ├── alphas191.py          # Alpha191因子库
│   │   │   ├── alpha_ch.py           # 中国市场因子
│   │   │   └── data_file_service.py  # 文件管理服务
│   │   ├── tasks/                    # 8个Celery异步任务
│   │   │   ├── data_download.py      # 任务1: K线下载
│   │   │   ├── feature_calculation.py # 任务2: 特征计算
│   │   │   ├── label_calculation.py  # 任务3: 标签生成
│   │   │   ├── model_training.py     # 任务4: 模型训练
│   │   │   ├── model_interpretation.py # 任务5: SHAP解释
│   │   │   ├── model_analysis.py     # 任务6: 代理模型
│   │   │   ├── backtest_construction.py # 任务7: 回测执行
│   │   │   └── backtest_execution.py # 任务8: (预留)
│   │   └── main.py                   # FastAPI入口
│   ├── data/                         # 数据目录(运行时创建)
│   └── requirements.txt
│
├── frontend/                         # 前端应用
│   ├── src/
│   │   ├── api/workflow.js           # API封装
│   │   ├── composables/useModuleState.js # 状态持久化
│   │   ├── router/index.js           # 8个路由
│   │   ├── stores/                   # Pinia状态管理
│   │   ├── views/                    # 8个页面组件
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
│
├── docs/                             # 文档目录
├── CLAUDE.md                         # AI助手配置
└── README.md
```

---

## 3. 技术栈详解

### 3.1 后端技术栈

```
Python 3.x
├── Web框架: FastAPI 0.104.1
├── 异步任务: Celery 5.3.4 + Redis 5.0.1
├── 数据处理: Pandas 2.1.3 + NumPy 1.26.2
├── 机器学习: LightGBM 4.1.0 + scikit-learn 1.3.2
├── 模型解释: SHAP 0.43.0
├── 技术指标: TA-Lib 0.4.28
├── 数据源: binance-futures-connector 3.3.1
└── 可视化: Matplotlib 3.8.2
```

| 组件 | 版本 | 用途 |
|------|------|------|
| **FastAPI** | 0.104.1 | 现代高性能异步Web框架 |
| **Celery** | 5.3.4 | 分布式任务队列 |
| **Redis** | 5.0.1 | 消息代理 & 结果后端 |
| **Pydantic** | 2.5.0 | 数据验证 & 设置管理 |
| **LightGBM** | 4.1.0 | 梯度提升树模型 |
| **SHAP** | 0.43.0 | 模型可解释性 |
| **Pandas** | 2.1.3 | 数据处理 |
| **NumPy** | 1.26.2 | 数值计算 |
| **TA-Lib** | 0.4.28 | 技术指标库 |
| **scikit-learn** | 1.3.2 | 机器学习工具 |
| **Matplotlib** | 3.8.2 | 图表生成 |
| **binance-futures-connector** | 3.3.1 | Binance期货API |

### 3.2 前端技术栈

```
Vue 3 生态
├── 构建工具: Vite 5.0 (超快的开发服务器)
├── UI框架: Element Plus 2.5.0 (组件库)
├── 状态管理: Pinia 2.1.7 (Vue 3官方推荐)
├── 路由: Vue Router 4.2.5 (SPA路由)
├── 图表: ECharts 6.0.0 (数据可视化)
└── HTTP客户端: Axios 1.6.2 (API调用)
```

### 3.3 Celery配置详解

```python
# app/core/celery_app.py 关键配置
celery_app.conf.update(
    # 序列化配置
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 时区配置
    timezone="UTC",
    enable_utc=True,

    # 任务追踪
    task_track_started=True,

    # 超时配置
    task_time_limit=3600,          # 硬超时1小时
    task_soft_time_limit=3300,     # 软超时55分钟

    # 可靠性配置
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # 结果缓存
    result_expires=3600,           # 结果保留1小时
    result_extended=True,

    # Worker配置
    worker_max_tasks_per_child=1000,  # 防止内存泄漏

    # 重试配置
    task_autoretry_for=(Exception,),
    task_retry_kwargs={'max_retries': 0}  # 不自动重试
)
```

---

## 4. 工作流程设计

### 4.1 完整工作流程

系统包含7个按顺序执行的模块，每个模块的输出是下一个模块的输入：

```
1. 数据下载 (Data Download)
   ↓ 输出: 原始K线数据文件 (ETHUSDT_BINANCE_2024-01-01_*.pkl)

2. 特征计算 (Feature Calculation)
   ↓ 输出: 特征数据文件 (*_features_alpha158.pkl)

3. 标签计算 (Label Calculation)
   ↓ 输出: 标签数据文件 (*_labels_w29_f10.pkl)

4. 模型训练 (Model Training)
   ↓ 输出: LightGBM模型文件 (*_model_lgb.pkl)

5. 模型解释 (Model Interpretation)
   ↓ 输出: SHAP可视化图表目录 (*_shap/)

6. 模型分析 (Model Analysis)
   ↓ 输出: 决策规则 (decision_rules JSON)

7. 构建回测 (Backtest Construction)
   ↓ 输出: 回测结果和资金曲线图 (backtest_long_*/)
```

### 4.2 异步任务机制

**Celery任务生命周期**：

```
1. 前端发起请求
   POST /api/v1/workflow/data-download
   ↓
2. FastAPI创建Celery任务
   task = download_kline_data.delay(...)
   返回 task_id
   ↓
3. 前端轮询任务状态
   GET /api/v1/workflow/task/{task_id}
   每500ms-2000ms查询一次
   ↓
4. Celery Worker执行任务
   - PENDING: 等待执行
   - PROGRESS: 执行中 (带进度百分比)
   - SUCCESS: 执行成功
   - FAILURE: 执行失败
   ↓
5. 返回最终结果
   result: {status, file_path, statistics, ...}
```

**任务状态更新示例**：

```python
# 任务内部更新进度
self.update_state(
    state='PROGRESS',
    meta={
        'progress': 50,              # 0-100
        'status': '正在下载数据...',
        'message': '已下载 5000/10000 条'
    }
)
```

### 4.3 数据流转设计

**文件命名规范**：
```python
# 原始数据
"ETHUSDT_BINANCE_2024-01-01_00_00_00_2024-12-31_23_59_59.pkl"

# 特征文件
"ETHUSDT_BINANCE_2024-01-01_00_00_00_2024-12-31_23_59_59_features_alpha158.pkl"

# 标签文件
"ETHUSDT_BINANCE_2024-01-01_00_00_00_2024-12-31_23_59_59_labels_w29_f10.pkl"

# 模型文件
"ETHUSDT_BINANCE_2024-01-01_00_00_00_2024-12-31_23_59_59_model_lgb.pkl"
```

**数据结构设计**：

```python
# 原始数据结构
{
    'datetime': DatetimeIndex,
    'open': float,
    'high': float,
    'low': float,
    'close': float,
    'volume': float,
    'symbol': str,
    'exchange': str,
    'interval': str
}

# 特征数据结构（在原始数据基础上添加）
{
    # 原始OHLCV列...
    'feature_KMID': float,
    'feature_KLEN': float,
    'feature_ROC5': float,
    'feature_MA10': float,
    # ... 总计158-216个特征列
}

# 标签数据结构
{
    'datetime': DatetimeIndex,
    'label': float  # 0到1之间的连续值
}
```

---

## 5. 后端核心模块

### 5.1 配置管理 (config.py)

使用 **Pydantic Settings** 进行环境变量管理：

```python
class Settings(BaseSettings):
    # 项目信息
    PROJECT_NAME: str = "EC Predict Flow"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Redis和Celery配置
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # API密钥（可选）
    ANTHROPIC_API_KEY: Optional[str] = None
    BINANCE_PROXY: Optional[str] = None

    # 数据目录路径（自动创建）
    BASE_DIR: str = os.path.dirname(...)
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    RAW_DATA_DIR: str = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR: str = os.path.join(DATA_DIR, "processed")
    MODELS_DIR: str = os.path.join(DATA_DIR, "models")
    PLOTS_DIR: str = os.path.join(DATA_DIR, "plots")

    class Config:
        env_file = ".env"
        case_sensitive = True
```

### 5.2 请求模型 (schemas/workflow.py)

系统定义了8个请求模型，对应工作流的各个阶段：

| 模型 | 关键参数 |
|------|----------|
| `DataDownloadRequest` | symbol, start_date, end_date, interval, proxy |
| `FeatureCalculationRequest` | data_file, alpha_types |
| `LabelCalculationRequest` | data_file, window, look_forward, label_type, filter_type, threshold |
| `ModelTrainingRequest` | features_file, labels_file, num_boost_round |
| `ModelInterpretationRequest` | model_file |
| `ModelAnalysisRequest` | model_file, selected_features, max_depth, min_samples_split |
| `BacktestConstructionRequest` | features_file, decision_rules, backtest_type, filter_type, win_profit, loss_cost |
| `BacktestExecutionRequest` | strategy_config, data_file |

### 5.3 API端点概览

系统提供18个REST API端点：

**任务提交端点** (POST):
- `/data-download` - 启动数据下载
- `/feature-calculation` - 启动特征计算
- `/label-calculation` - 启动标签计算
- `/model-training` - 启动模型训练
- `/model-interpretation` - 启动SHAP解释
- `/model-analysis` - 启动代理模型分析
- `/backtest-construction` - 启动回测构建
- `/backtest-execution` - 启动回测执行

**状态查询端点** (GET):
- `/task/{task_id}` - 获取任务状态

**文件管理端点**:
- `GET /data-files` - 列出数据文件
- `DELETE /data-files/{filename}` - 删除文件
- `GET /data-files/{filename}/preview` - 预览文件
- `GET /plots/{dirname}/files` - 获取SHAP图表列表
- `DELETE /plots/{dirname}` - 删除图表目录
- `GET /labels/preview` - 预览标签数据

---

## 6. 工作流任务详解

### 6.1 任务1: 数据下载 (data_download.py)

**功能**: 从Binance期货API下载K线数据

**API接口**:
```python
POST /api/v1/workflow/data-download

# 请求体
{
    "symbol": "ETHUSDT",           # 交易对
    "start_date": "2024-01-01",    # 开始日期
    "end_date": "2024-01-31",      # 结束日期
    "interval": "1m",              # 时间间隔
    "proxy": "http://127.0.0.1:7890"  # 可选代理
}
```

**核心实现逻辑**:

```python
@celery_app.task(bind=True, base=CallbackTask)
def download_kline_data(self, symbol, start_date, end_date, interval, proxy):
    # 1. 初始化Binance客户端
    proxies = {'https': proxy} if proxy else None
    client = UMFutures(proxies=proxies)

    # 2. 解析日期范围
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # 3. 分批下载数据（每次最多1000根K线）
    all_data = []
    limit = 1000
    current_start = start_dt

    while current_start < end_dt:
        # 调用Binance API
        klines = client.klines(
            symbol=symbol,
            interval=interval,
            startTime=int(current_start.timestamp() * 1000),
            limit=limit
        )

        all_data.extend(klines)

        # 更新进度
        progress = calculate_progress(current_start, start_dt, end_dt)
        self.update_state(state='PROGRESS', meta={
            'progress': progress,
            'status': '正在下载...',
            'message': f'已下载 {len(all_data)} 条数据'
        })

        # 更新起始时间
        current_start = datetime.fromtimestamp(klines[-1][0] / 1000)
        time.sleep(0.5)  # 避免触发限流

    # 4. 转换为DataFrame并保存
    df = pd.DataFrame(all_data, columns=[...])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.to_pickle(filepath)

    return {
        "status": "success",
        "filename": filename,
        "total_rows": len(df),
        "start_time": df['datetime'].min().isoformat(),
        "end_time": df['datetime'].max().isoformat()
    }
```

**关键技术点**:
1. **限流处理**：每次请求后等待0.5秒，避免触发Binance API限流
2. **代理支持**：支持通过HTTP代理访问API（处理网络限制）
3. **增量下载**：自动处理时间范围分段，每次最多1000条
4. **时区转换**：时间戳转换为北京时间 (Asia/Shanghai)

**支持的时间周期**: `1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w`

---

### 6.2 任务2: 特征计算 (feature_calculation.py)

**功能**: 计算量价技术指标特征

**API接口**:
```python
POST /api/v1/workflow/feature-calculation

{
    "data_file": "ETHUSDT_BINANCE_2024-01-01_2024-01-31.pkl",
    "alpha_types": ["alpha158", "alpha216"]  # 可选多种
}
```

**支持的Alpha类型**:

| Alpha类型 | 特征数量 | 窗口参数 |
|-----------|----------|----------|
| alpha158 | 158 | [5, 10, 20, 30, 60] |
| alpha216 | 216 | [5, 10, 20, 30, 60, 120, 240] |
| alpha101 | 101 | WorldQuant Alpha因子 |
| alpha191 | 191 | Alpha191因子 |
| alpha_ch | ~178 | 中国市场特色因子 |

---

### 6.3 任务3: 标签计算 (label_calculation.py)

**功能**: 生成预测标签

**API接口**:
```python
POST /api/v1/workflow/label-calculation

{
    "data_file": "ETHUSDT_BINANCE_2024-01-01_2024-01-31.pkl",
    "window": 29,              # 标签窗口（奇数）
    "look_forward": 10,        # 预测周期
    "label_type": "up",        # "up"上涨 或 "down"下跌
    "filter_type": "rsi",      # "rsi" 或 "cti"
    "threshold": 30            # 过滤阈值（可选）
}
```

**标签生成算法**:

```python
def calculate_label_with_filter(df, window=29, look_forward=10,
                                 label_type='up', filter_type='rsi',
                                 threshold=None):
    """
    生成标签的3个步骤：
    1. 计算过滤指标
    2. 预计算所有K线的涨跌标签
    3. 在窗口内统计涨跌比例
    """

    # 步骤1: 计算过滤指标
    if filter_type == 'rsi':
        df['filter_indicator'] = calculate_RSI(df, 14)  # 14周期RSI
        if label_type == 'up':
            threshold = threshold or 30  # 超卖区域
            filter_condition = df['filter_indicator'] < threshold
        else:  # down
            threshold = threshold or 70  # 超买区域
            filter_condition = df['filter_indicator'] > threshold
    else:  # cti
        df['filter_indicator'] = calculate_fast_cti(df)
        if label_type == 'up':
            threshold = threshold or -0.5
            filter_condition = df['filter_indicator'] < threshold
        else:
            threshold = threshold or 0.5
            filter_condition = df['filter_indicator'] > threshold

    # 步骤2: 预计算涨跌标签
    rise_tag = np.full(len(df), np.nan)
    for i in range(len(df)):
        if i + look_forward < len(df):
            close_now = df['close'].iloc[i]
            close_future = df['close'].iloc[i + look_forward]

            if label_type == 'up':
                # 未来上涨为1，下跌为0
                rise_tag[i] = 1 if (close_future - close_now) > 0 else 0
            else:  # down
                # 未来下跌为1，上涨为0
                rise_tag[i] = 1 if (close_now - close_future) > 0 else 0

    # 步骤3: 在窗口内统计比例
    df['Label'] = np.nan
    half_w = window // 2

    for i in range(len(df)):
        if filter_condition.iloc[i]:  # 满足过滤条件
            start = max(0, i - half_w)
            end = min(len(df), i + half_w + 1)

            window_rise_tag = rise_tag[start:end]
            valid_count = np.sum(~np.isnan(window_rise_tag))

            if valid_count > 0:
                ratio = np.nansum(window_rise_tag == 1) / valid_count
                df.loc[i, 'Label'] = ratio
        else:
            df.loc[i, 'Label'] = np.nan

    return df['Label']
```

**过滤指标计算代码**:

```python
def calculate_RSI(df, period=14):
    """
    相对强弱指标，范围0-100
    - RSI < 30: 超卖（适合做多）
    - RSI > 70: 超买（适合做空）
    """
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_fast_cti(df):
    """
    相关趋势指标，范围-1到1
    - CTI < -0.5: 强烈下跌趋势（适合做多）
    - CTI > 0.5: 强烈上涨趋势（适合做空）
    使用Numba加速
    """
    close = df['close']
    cti = close.rolling(window=20).corr(pd.Series(range(20)))
    return cti
```

**过滤条件默认值**:
| 类型 | 上涨标签 | 下跌标签 |
|------|----------|----------|
| RSI | < 30 | > 70 |
| CTI | < -0.5 | > 0.5 |

**标签值示例**:

假设window=29, look_forward=10, label_type='up':

| 时间 | close | RSI | 过滤条件 | 未来10根涨跌 | 窗口内比例 | Label |
|------|-------|-----|----------|-------------|-----------|-------|
| t0 | 100 | 25 | True | 1,0,1,1,0... | 12/29≈0.41 | 0.41 |
| t1 | 101 | 28 | True | 0,1,1,0,1... | 15/29≈0.52 | 0.52 |
| t2 | 102 | 45 | False | 1,1,0,1,0... | - | NaN |
| t3 | 103 | 22 | True | 1,1,1,1,1... | 20/29≈0.69 | 0.69 |

**标签含义**：
- 0.7 表示窗口内70%的K线未来会上涨（强烈看涨信号）
- 0.3 表示窗口内30%的K线未来会上涨（弱看涨信号）
- NaN 表示不满足过滤条件，不参与训练

---

### 6.4 任务4: 模型训练 (model_training.py)

**功能**: 使用LightGBM训练预测模型

**API接口**:
```python
POST /api/v1/workflow/model-training

{
    "features_file": "ETHUSDT_..._features_alpha158.pkl",
    "labels_file": "ETHUSDT_..._labels_w29_f10.pkl",
    "num_boost_round": 500
}
```

**核心实现逻辑**:

```python
@celery_app.task(bind=True, base=CallbackTask)
def train_lightgbm_model(self, features_file, labels_file, num_boost_round=500):
    # 1. 加载特征和标签文件
    features_df = pd.read_pickle(features_path)
    labels_df = pd.read_pickle(labels_path)

    # 2. 对齐数据（基于datetime列merge）
    merged_df = pd.merge(features_df, labels_df, on='datetime', how='inner')

    # 3. 过滤掉标签为NaN的行
    merged_df = merged_df.dropna(subset=['label'])

    # 4. 提取特征矩阵和标签向量
    exclude_cols = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'label']
    feature_cols = [col for col in merged_df.columns if col not in exclude_cols]

    X = merged_df[feature_cols].values
    y = merged_df['label'].values

    # 5. 创建LightGBM数据集
    lgb_train = lgb.Dataset(X, label=y)

    # 6. 设置训练参数
    params = {
        'objective': 'regression',  # 回归任务
        'metric': 'l2',             # 均方误差
        'verbosity': -1,
        'num_threads': 4,
    }

    # 7. 训练模型（带进度回调）
    def progress_callback(env):
        progress_percent = 35 + (env.iteration / num_boost_round) * 50
        self.update_state(state='PROGRESS', meta={...})

    gbm = lgb.train(params, lgb_train, num_boost_round=num_boost_round,
                    callbacks=[progress_callback])

    # 8. 计算特征重要性
    imp_lgb = pd.Series(
        gbm.feature_importance(importance_type='gain'),
        index=feature_cols
    ).sort_values(ascending=False)

    # 9. 保存模型和元数据
    model_data = {
        'model': gbm,
        'feature_cols': feature_cols,
        'feature_importance': imp_lgb.to_dict(),
        'features_file': features_file,
        'labels_file': labels_file,
        'num_boost_round': num_boost_round,
        'params': params,
        'train_samples': int(len(X)),
        'num_features': int(len(feature_cols))
    }
    pickle.dump(model_data, open(model_path, 'wb'))

    return {...}
```

**LightGBM参数说明**:

| 参数 | 值 | 说明 |
|------|-----|------|
| objective | regression | 回归任务（预测0-1的连续标签） |
| metric | l2 | 损失函数（均方误差） |
| num_boost_round | 500 | 决策树数量（boosting迭代次数） |
| num_threads | 4 | 并行线程数 |

**数据对齐策略**:
- 特征文件和标签文件通过datetime列进行内连接（inner join）
- 只删除label为NaN的行，特征中的NaN保留
- LightGBM可以自动处理特征中的NaN值

---

### 6.5 任务5: 模型解释 (model_interpretation.py)

**功能**: 使用SHAP生成模型可解释性图表

**核心实现逻辑**:

```python
@celery_app.task(bind=True, base=CallbackTask)
def generate_shap_plots(self, model_file):
    # 1. 加载模型和数据
    model_data = pickle.load(open(model_path, 'rb'))
    gbm = model_data['model']
    feature_cols = model_data['feature_cols']

    # 2. 重新加载训练数据
    merged_df = pd.merge(features_df, labels_df, on='datetime', how='inner')
    X = merged_df[feature_cols].values

    # 3. 创建SHAP explainer
    explainer = shap.TreeExplainer(gbm)

    # 4. 计算SHAP值（最耗时步骤）
    shap_values = explainer.shap_values(X)

    # 5. 生成summary bar plot（全局重要性）
    shap.summary_plot(shap_values, X, feature_names=feature_cols,
                      plot_type="bar", max_display=20, show=False)
    plt.savefig(f'{plots_dir}/00_summary_bar.png')

    # 6. 生成summary dot plot（特征影响分布）
    shap.summary_plot(shap_values, X, feature_names=feature_cols,
                      max_display=20, show=False)
    plt.savefig(f'{plots_dir}/00_summary_dot.png')

    # 7. 计算Top特征（SHAP + 相关性）
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    shap_order = np.argsort(mean_abs_shap)[::-1]
    top20_features_shap = [feature_cols[i] for i in shap_order[:20]]

    # 8. 为每个Top特征生成dependence plot
    for idx, feat in enumerate(all_top_features):
        shap.dependence_plot(feature_idx, shap_values, X,
                            feature_names=feature_cols, show=False)
        plt.savefig(f'{plots_dir}/{idx+1:02d}_{feat}.png')

    return {...}
```

**SHAP图表类型详解**:

**1. Summary Bar Plot（特征重要性条形图）**：
- X轴：mean(|SHAP value|) - 平均绝对SHAP值
- Y轴：特征名称（Top 20）
- 解释：特征对模型输出的平均影响程度

**2. Summary Dot Plot（特征影响分布图）**：
- X轴：SHAP value（正值=增加预测，负值=减少预测）
- Y轴：特征名称（Top 20）
- 颜色：特征值（红=高，蓝=低）
- 每个点代表一个样本
- 解释：可以看出特征值与预测影响的关系

**3. Dependence Plot（特征依赖图）**：
- X轴：特征值
- Y轴：SHAP value
- 颜色：自动选择的交互特征
- 解释：特征值如何影响预测，以及与其他特征的交互

**SHAP值解释示例**:

```python
base_value = 0.5           # 模型基准预测（所有样本的平均标签）
feature_CNTP30 = -0.15    # SHAP值为负，减少预测
feature_MA10 = 0.08       # SHAP值为正，增加预测
feature_RSI = 0.03        # 轻微增加预测

# 最终预测 = base_value + sum(shap_values)
prediction = 0.5 + (-0.15 + 0.08 + 0.03 + ...) = 0.46
```

**解释**：
- 基准预测是0.5（50%上涨概率）
- CNTP30特征使预测降低0.15（表示上涨概率减少）
- 最终预测0.46（46%上涨概率）

---

### 6.6 任务6: 模型分析 (model_analysis.py)

**功能**: 使用决策树代理模型提取规则

**API接口**:
```python
POST /api/v1/workflow/model-analysis

{
    "model_file": "ETHUSDT_..._model_lgb.pkl",
    "selected_features": [
        "feature_CNTP30",
        "feature_IMIN240",
        "feature_MA10"
    ],
    "max_depth": 3,
    "min_samples_split": 100
}
```

**代理模型训练流程**:

```python
@celery_app.task(bind=True, base=CallbackTask)
def analyze_model_with_surrogate(self, model_file, selected_features,
                                  max_depth=3, min_samples_split=100):
    # 1. 加载原始模型和数据
    model_data = pickle.load(open(model_path, 'rb'))

    # 2. 提取选定特征和标签
    X = df[selected_features].copy()
    y = df['label'].copy()

    # 3. 处理缺失值和无穷值
    X = X.replace([np.inf, -np.inf], np.nan).fillna(X.median())

    # 4. 标签二值化（如果是连续值）
    if len(y.unique()) > 2:
        threshold = y.median()
        y = (y > threshold).astype(int)

    # 5. 训练决策树代理模型
    dt_model = DecisionTreeClassifier(
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=50,
        random_state=42
    )
    dt_model.fit(X, y)

    # 6. 从决策树提取规则
    rules = extract_decision_rules(dt_model, selected_features, X, y)

    return {...}
```

**决策规则提取算法**:

```python
def extract_decision_rules(tree_model, feature_names, X, y):
    """从决策树中提取所有叶节点的决策路径和统计信息"""
    tree = tree_model.tree_
    rules = []

    def recurse(node, path_conditions, path_thresholds):
        # 判断是否为叶节点
        if tree.feature[node] == _tree.TREE_UNDEFINED:
            samples = tree.n_node_samples[node]
            value = tree.value[node][0]
            class_dist = {"0": int(value[0]), "1": int(value[1])}
            predicted_class = int(np.argmax(value))
            confidence = float(value[predicted_class] / samples)

            if samples >= 50:
                rule = {
                    "rule_id": len(rules) + 1,
                    "path": " AND ".join(path_conditions),
                    "thresholds": path_thresholds.copy(),
                    "samples": int(samples),
                    "class_distribution": class_dist,
                    "predicted_class": predicted_class,
                    "confidence": confidence
                }
                rules.append(rule)
            return

        # 获取当前节点的分裂特征和阈值
        feature_idx = tree.feature[node]
        feature_name = feature_names[feature_idx]
        threshold = float(tree.threshold[node])

        # 左子树 (<=)
        left_condition = f"{feature_name} <= {threshold:.4f}"
        left_threshold = {"feature": feature_name, "operator": "<=", "value": threshold}
        recurse(tree.children_left[node],
                path_conditions + [left_condition],
                path_thresholds + [left_threshold])

        # 右子树 (>)
        right_condition = f"{feature_name} > {threshold:.4f}"
        right_threshold = {"feature": feature_name, "operator": ">", "value": threshold}
        recurse(tree.children_right[node],
                path_conditions + [right_condition],
                path_thresholds + [right_threshold])

    recurse(0, [], [])
    rules.sort(key=lambda x: x['confidence'], reverse=True)
    return rules
```

**决策规则示例**:

```json
{
  "rule_id": 1,
  "path": "feature_CNTP30 <= 0.5234 AND feature_IMIN240 > 0.3456",
  "thresholds": [
    {"feature": "feature_CNTP30", "operator": "<=", "value": 0.5234},
    {"feature": "feature_IMIN240", "operator": ">", "value": 0.3456}
  ],
  "samples": 1523,
  "class_distribution": {"0": 412, "1": 1111},
  "predicted_class": 1,
  "confidence": 0.73
}
```

**解释**：
- 当CNTP30 <= 0.5234 且 IMIN240 > 0.3456时
- 有1523个样本满足此条件
- 其中73%的样本标签为1（看涨）
- 因此预测类别为1，置信度73%

---

### 6.7 任务7: 回测构建 (backtest_construction.py)

**功能**: 基于决策规则执行回测

**API接口**:
```python
POST /api/v1/workflow/backtest-construction

{
    "features_file": "ETHUSDT_..._features_alpha158.pkl",
    "decision_rules": [...],
    "backtest_type": "long",
    "filter_type": "rsi",
    "look_forward_bars": 10,
    "win_profit": 4.0,
    "loss_cost": 5.0,
    "initial_balance": 1000.0
}
```

**开仓信号生成算法**:

```python
def generate_open_signal(df, decision_rules, backtest_type='long'):
    """
    根据决策规则生成开仓信号

    规则之间: OR关系（满足任意一条即可开仓）
    规则内部: AND关系（所有阈值条件必须同时满足）
    """
    open_signal = pd.Series([False] * len(df), index=df.index)
    target_class = 1 if backtest_type == 'long' else 0

    for rule in decision_rules:
        if rule.get('predicted_class', 1) != target_class:
            continue

        rule_condition = pd.Series([True] * len(df), index=df.index)

        for threshold in rule.get('thresholds', []):
            feature = threshold['feature']
            operator = threshold['operator']
            value = threshold['value']

            if feature not in df.columns:
                continue

            if operator == '<=':
                rule_condition &= (df[feature] <= value)
            elif operator == '>':
                rule_condition &= (df[feature] > value)
            elif operator == '<':
                rule_condition &= (df[feature] < value)
            elif operator == '>=':
                rule_condition &= (df[feature] >= value)

        open_signal |= rule_condition

    return open_signal
```

**回测指标说明**:

| 指标 | 说明 | 计算公式 |
|------|------|----------|
| total_trades | 总交易次数 | len(trades) |
| winning_trades | 盈利交易次数 | sum(is_win == True) |
| losing_trades | 亏损交易次数 | sum(is_win == False) |
| win_rate | 胜率 | winning_trades / total_trades |
| profit | 总盈亏 | final_balance - initial_balance |
| profit_rate | 收益率 | profit / initial_balance |
| max_drawdown | 最大回撤 | max((peak - current) / peak) |

**回测类型说明**：
- **long（做多）**：预测价格上涨，未来价格 > 入场价格为盈利
- **short（做空）**：预测价格下跌，未来价格 < 入场价格为盈利

**关键参数**:
- `look_forward_bars`: 持仓周期 (默认10根K线)
- `win_profit`: 盈利金额 (默认4.0)
- `loss_cost`: 亏损金额 (默认5.0)
- `order_interval`: 最小订单间隔 (30分钟)

**输出图表**:
1. **balance_curve.png**: 资金曲线
2. **trades_distribution.png**: 交易分布图

---

## 7. 特征工程系统

### 7.1 Alpha158因子详解

Alpha158是Qlib中的标准158因子集，分为三大类：

#### 7.1.1 KBar因子 (9个)

| 因子名 | 公式 | 含义 |
|--------|------|------|
| KMID | (close-open)/open | K线实体中心位置 |
| KLEN | (high-low)/open | K线长度 |
| KMID2 | (close-open)/(high-low) | 实体/影线比 |
| KUP | (high-max(open,close))/open | 上影线比例 |
| KUP2 | (high-max(open,close))/(high-low) | 上影线/总长比 |
| KLOW | (min(open,close)-low)/open | 下影线比例 |
| KLOW2 | (min(open,close)-low)/(high-low) | 下影线/总长比 |
| KSFT | (2*close-high-low)/open | 重心偏移 |
| KSFT2 | (2*close-high-low)/(high-low) | 标准化重心偏移 |

#### 7.1.2 Price因子 (4个)

| 因子名 | 公式 |
|--------|------|
| PRICE_OPEN0 | open/close |
| PRICE_HIGH0 | high/close |
| PRICE_LOW0 | low/close |
| PRICE_CLOSE0 | close/close (=1) |

#### 7.1.3 Rolling因子 (29组 × 5窗口 = 145个)

窗口大小: [5, 10, 20, 30, 60]

| 因子组 | 含义 |
|--------|------|
| ROC | 动量指标 (Rate of Change) |
| MA | 移动平均 |
| STD | 波动率 (标准差) |
| BETA | 线性回归斜率 |
| RSQR | 线性回归R² |
| RESI | 线性回归残差 |
| MAX | 区间最高价 |
| LOW | 区间最低价 |
| QTLU | 0.8分位数 |
| QTLD | 0.2分位数 |
| RANK | 百分位排名 |
| RSV | 随机指标 |
| IMAX | 最高价位置 |
| IMIN | 最低价位置 |
| IMXD | 极值位置差 |
| CORR | 量价相关性 |
| CORD | 收益量相关 |
| CNTP | 上涨比例 |
| CNTN | 下跌比例 |
| CNTD | 涨跌差 |
| SUMP | 上涨强度 |
| SUMN | 下跌强度 |
| SUMD | 强度差 |
| VMA | 成交量均值 |
| VSTD | 成交量波动 |
| WVMA | 加权波动率 |
| VSUMP | 放量比例 |
| VSUMN | 缩量比例 |
| VSUMD | 量能差 |

### 7.2 Alpha216因子

Alpha216是Alpha158的扩展版本，窗口从5个扩展到7个：

**窗口大小**: [5, 10, 20, 30, 60, 120, 240]

总计: 9 + 4 + 29×7 = **216个因子**

### 7.3 技术指标计算 (calculate_indicator.py)

| 函数 | 用途 |
|------|------|
| `calculate_RSI` | RSI相对强弱指标 (14周期) |
| `calculate_fast_cti` | CTI相关趋势指标 (Numba加速) |
| `calculate_EWO` | Elliott Wave Oscillator |
| `calculate_bollinger_bands` | 布林带 |
| `calculate_vwap` | 成交量加权平均价 |
| `calculate_vwapb` | VWAP带 |
| `calculate_IMIN` | 最低价位置 |
| `calculate_KLEN` | K线长度 |

---

## 8. 机器学习管道

### 8.1 模型训练流程

```
┌──────────────┐
│ 加载特征文件  │
└──────┬───────┘
       │
┌──────▼───────┐
│ 加载标签文件  │
└──────┬───────┘
       │
┌──────▼───────┐
│ 数据对齐(时间)│  pd.merge(..., on='datetime')
└──────┬───────┘
       │
┌──────▼───────┐
│ 过滤NaN标签  │  dropna(subset=['label'])
└──────┬───────┘
       │
┌──────▼───────┐
│ 提取特征矩阵  │  排除: datetime, OHLCV, label
└──────┬───────┘
       │
┌──────▼───────┐
│ 创建LGB数据集│  lgb.Dataset(X, label=y)
└──────┬───────┘
       │
┌──────▼───────┐
│ 训练模型     │  带进度回调
└──────┬───────┘
       │
┌──────▼───────┐
│ 计算特征重要性│  importance_type='gain'
└──────┬───────┘
       │
┌──────▼───────┐
│ 保存模型元数据│  pickle.dump
└──────────────┘
```

### 8.2 SHAP解释流程

```python
# 1. 创建TreeExplainer
explainer = shap.TreeExplainer(gbm)

# 2. 计算SHAP值 (最耗时)
shap_values = explainer.shap_values(X)

# 3. 生成Summary Plot (Bar + Dot)
shap.summary_plot(shap_values, X, feature_names=feature_cols)

# 4. 生成Dependence Plot (每个Top特征)
shap.dependence_plot(feature_idx, shap_values, X)
```

### 8.3 代理模型分析

**决策树参数**:
```python
dt_model = DecisionTreeClassifier(
    max_depth=3,              # 最大深度 (可配置)
    min_samples_split=100,    # 分裂最小样本
    min_samples_leaf=50,      # 叶节点最小样本
    random_state=42
)
```

---

## 9. 回测引擎

### 9.1 信号生成

```python
def generate_open_signal(df, decision_rules, backtest_type):
    """
    规则间: OR关系
    规则内: AND关系
    """
    target_class = 1 if backtest_type == 'long' else 0

    for rule in decision_rules:
        if rule['predicted_class'] != target_class:
            continue

        rule_condition = True
        for threshold in rule['thresholds']:
            rule_condition &= apply_condition(df, threshold)

        open_signal |= rule_condition

    return open_signal
```

### 9.2 回测执行

**过滤条件**:
| 类型 | 做多条件 | 做空条件 |
|------|----------|----------|
| RSI | RSI < 30 | RSI > 70 |
| CTI | CTI < -0.5 | CTI > 0.5 |

---

## 10. 前端架构

### 10.1 技术栈与项目结构

```
Vue 3 Composition API
├── 构建工具: Vite 5.0 (超快的开发服务器)
├── UI框架: Element Plus 2.5.0 (组件库)
├── 状态管理: Pinia 2.1.7 (Vue 3官方推荐)
├── 路由: Vue Router 4.2.5 (SPA路由)
├── 图表: ECharts 6.0.0 (数据可视化)
└── HTTP客户端: Axios 1.6.2 (API调用)
```

### 10.2 路由配置

| 路径 | 组件 | 功能 |
|------|------|------|
| `/` | WorkflowOverview | 工作流概览 |
| `/data-download` | DataDownload | 数据下载 |
| `/feature-calculation` | FeatureCalculation | 特征计算 |
| `/model-training` | ModelTraining | 模型训练 |
| `/model-interpretation` | ModelInterpretation | 模型解释 |
| `/model-analysis` | ModelAnalysis | 模型分析 |
| `/backtest-construction` | BacktestConstruction | 构建回测 |
| `/backtest-execution` | BacktestExecution | 执行回测 |

### 10.3 状态管理 (Pinia)

```javascript
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
  const stageResults = ref({...})

  return { currentStage, tasks, stageResults, ... }
})
```

### 10.4 任务状态轮询

```javascript
const pollTaskStatus = async () => {
  const interval = setInterval(async () => {
    const response = await workflowAPI.getTaskStatus(taskId.value)
    taskStatus.value = response.data.status

    if (response.data.status === 'success') {
      result.value = response.data.result
      clearInterval(interval)
    } else if (response.data.status === 'failure') {
      clearInterval(interval)
    }
  }, 2000)
}
```

---

## 11. API接口规范

### 11.1 通用响应格式

**任务提交响应**:
```json
{
  "task_id": "abc123...",
  "status": "pending",
  "message": "Task started"
}
```

**任务状态响应**:
```json
{
  "task_id": "abc123...",
  "status": "running|success|failure",
  "progress": 50.0,
  "result": {...},
  "error": null
}
```

### 11.2 状态映射

| Celery状态 | API状态 |
|------------|---------|
| PENDING | pending |
| STARTED | running |
| PROGRESS | running |
| SUCCESS | success |
| FAILURE | failure |
| RETRY | running |
| REVOKED | failure |

### 11.3 详细接口示例

#### POST /api/v1/workflow/data-download

```json
{
  "symbol": "ETHUSDT",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "interval": "1m",
  "proxy": "http://127.0.0.1:10808"
}
```

#### POST /api/v1/workflow/backtest-construction

```json
{
  "features_file": "..._features_alpha216.pkl",
  "decision_rules": [
    {
      "rule_id": 1,
      "thresholds": [
        {"feature": "feature_CNTP30", "operator": "<=", "value": 0.5}
      ],
      "predicted_class": 1,
      "confidence": 0.75
    }
  ],
  "backtest_type": "long",
  "filter_type": "rsi",
  "look_forward_bars": 10,
  "win_profit": 4.0,
  "loss_cost": 5.0,
  "initial_balance": 1000.0
}
```

---

## 12. 数据流设计

### 12.1 文件命名规范

| 阶段 | 文件名模式 | 存储目录 |
|------|------------|----------|
| 原始数据 | `{SYMBOL}_{EXCHANGE}_{START}_{END}.pkl` | data/raw/ |
| 特征数据 | `{BASE}_features_{ALPHA}.pkl` | data/processed/ |
| 标签数据 | `{BASE}_labels_w{W}_f{F}.pkl` | data/processed/ |
| 模型文件 | `{BASE}_model_lgb.pkl` | data/models/ |
| SHAP目录 | `{BASE}_shap/` | data/plots/ |
| 回测目录 | `backtest_{TYPE}_{TIMESTAMP}/` | data/plots/ |

### 12.2 数据格式

**Pickle文件结构**:
- 所有数据文件使用 Pandas DataFrame
- 时间索引使用 DatetimeIndex
- 时区: Asia/Shanghai

**模型文件结构**:
```python
{
  'model': LGBMModel,
  'feature_cols': List[str],
  'feature_importance': Dict[str, float],
  'features_file': str,
  'labels_file': str,
  'params': Dict,
  ...
}
```

---

## 13. 部署与运维

### 13.1 环境要求

**硬件要求**：
- CPU: 4核及以上
- 内存: 8GB及以上
- 硬盘: 20GB可用空间

**软件要求**：
- Python: 3.9 - 3.11
- Node.js: 16.x 或 18.x
- Redis: 5.x 或更高版本
- Git: 2.x

### 13.2 后端部署

```bash
# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate     # Windows

# 2. 安装依赖
cd backend
pip install -r requirements.txt

# 3. 安装TA-Lib (Windows)
# 下载: https://github.com/cgohlke/talib-build/releases
pip install TA_Lib-0.4.28-cp311-cp311-win_amd64.whl

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 5. 启动Redis
redis-server

# 6. 启动Celery Worker (Windows必须使用solo池)
celery -A app.core.celery_app worker --loglevel=info --pool=solo

# 7. 启动FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 13.3 前端部署

```bash
cd frontend
npm install
npm run dev      # 开发模式
npm run build    # 生产构建
```

### 13.4 验证部署

```bash
# 检查Redis连接
redis-cli ping
# 应返回: PONG

# 访问API文档
# 打开浏览器: http://localhost:8000/docs

# 访问前端页面
# 打开浏览器: http://localhost:5173
```

---

## 14. 常见问题解答

### 14.1 安装与配置问题

**Q1: TA-Lib安装失败怎么办？**

A: Windows系统需要下载预编译的whl文件：
```bash
# 1. 访问 https://github.com/cgohlke/talib-build/releases
# 2. 下载对应Python版本的whl文件，如:
#    TA_Lib-0.4.28-cp311-cp311-win_amd64.whl (Python 3.11, 64位)
# 3. 安装
pip install TA_Lib-0.4.28-cp311-cp311-win_amd64.whl
```

**Q2: Redis连接失败？**

A: 检查Redis是否正在运行：
```bash
# 检查连接
redis-cli ping
# 应返回: PONG

# 如果未运行，启动Redis
# Linux: sudo systemctl start redis
# Mac: brew services start redis
```

**Q3: Celery Worker无法启动？**

A: Windows系统必须使用 `--pool=solo` 参数：
```bash
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

### 14.2 运行时问题

**Q4: 任务一直处于PENDING状态？**

A: 可能原因：
1. Celery Worker未启动
2. Redis连接失败
3. 任务队列阻塞

解决方法：
```bash
# 1. 检查Celery Worker进程
ps aux | grep celery

# 2. 清理Redis缓存
cd backend
python clear_redis.py

# 3. 重启Celery Worker
```

**Q5: 特征计算内存溢出？**

A: 建议：
1. 减少数据量（缩短时间范围）
2. 分批计算特征
3. 增加系统内存
4. 只选择必要的Alpha因子类型

**Q6: SHAP计算非常慢？**

A: SHAP值计算是CPU密集型操作，优化方法：
1. 使用采样数据（如random_state采样10%）
2. 减少特征数量
3. 使用更少的CPU核心避免竞争
4. 耐心等待（通常需要5-15分钟）

### 14.3 数据问题

**Q7: Binance API访问超时？**

A: 使用代理：
```python
# 在.env文件中配置
BINANCE_PROXY=http://127.0.0.1:7890

# 或在前端界面中填写代理地址
```

**Q8: 特征和标签文件无法对齐？**

A: 检查datetime列：
- 确保两个文件的datetime格式一致
- 检查时区设置
- 验证时间戳是否重叠

**Q9: 回测结果不合理（胜率过高/过低）？**

A: 可能原因：
1. 过拟合：训练数据和回测数据相同
2. 未来数据泄露：特征计算使用了未来信息
3. 过滤条件过于严格/宽松
4. 决策规则不适用于当前市场

---

## 15. 开发指南

### 15.1 添加新的Alpha因子

1. 在 `data_processor.py` 中添加新方法
2. 在 `feature_calculation.py` 中注册
3. 在 `schemas/workflow.py` 中更新验证

### 15.2 扩展API端点

1. 在 `schemas/workflow.py` 中定义请求模型
2. 在 `tasks/` 中创建Celery任务
3. 在 `endpoints/workflow.py` 中添加路由
4. 在 `celery_app.py` 的 `include` 列表中注册任务

### 15.3 调试技巧

```python
# 直接调用Celery任务 (Python REPL)
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

---

## 快速命令参考

```bash
# 后端启动
cd backend
redis-server                                                    # 启动Redis
celery -A app.core.celery_app worker --loglevel=info --pool=solo  # Worker
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000       # FastAPI

# 前端启动
cd frontend
npm run dev

# 清理Redis
python clear_redis.py

# 访问地址
# 前端: http://localhost:5173
# API Docs: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

---

**文档结束**

> 本文档由 Claude Opus 4.5 深度分析生成，整合 V1.0 和 V2.0 精华内容
> 版本: 2.1
> 生成时间: 2025-11-28
