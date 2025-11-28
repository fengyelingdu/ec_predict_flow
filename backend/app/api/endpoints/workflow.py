from fastapi import APIRouter, HTTPException, Query
from app.schemas.workflow import (
    DataDownloadRequest, FeatureCalculationRequest, LabelCalculationRequest, ModelTrainingRequest,
    ModelInterpretationRequest, ModelAnalysisRequest, BacktestConstructionRequest,
    BacktestExecutionRequest, TaskResponse, TaskStatusResponse
)
from app.tasks import (
    data_download, feature_calculation, label_calculation, model_training,
    model_interpretation, model_analysis, backtest_construction, backtest_execution
)
from app.services.data_file_service import DataFileService
from celery.result import AsyncResult
from typing import Optional

router = APIRouter()


@router.post("/data-download", response_model=TaskResponse)
async def start_data_download(request: DataDownloadRequest):
    task = data_download.download_kline_data.delay(
        symbol=request.symbol,
        start_date=request.start_date,
        end_date=request.end_date,
        interval=request.interval,
        proxy=request.proxy
    )
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message="Data download task started"
    )


@router.post("/feature-calculation", response_model=TaskResponse)
async def start_feature_calculation(request: FeatureCalculationRequest):
    task = feature_calculation.calculate_features.delay(
        data_file=request.data_file,
        alpha_types=request.alpha_types
    )
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message="Feature calculation task started"
    )


@router.post("/label-calculation", response_model=TaskResponse)
async def start_label_calculation(request: LabelCalculationRequest):
    task = label_calculation.calculate_labels.delay(
        data_file=request.data_file,
        window=request.window,
        look_forward=request.look_forward,
        label_type=request.label_type,
        filter_type=request.filter_type,
        threshold=request.threshold
    )
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message="Label calculation task started"
    )


@router.post("/model-training", response_model=TaskResponse)
async def start_model_training(request: ModelTrainingRequest):
    task = model_training.train_lightgbm_model.delay(
        features_file=request.features_file,
        labels_file=request.labels_file,
        num_boost_round=request.num_boost_round
    )
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message="Model training task started"
    )


@router.post("/model-interpretation", response_model=TaskResponse)
async def start_model_interpretation(request: ModelInterpretationRequest):
    task = model_interpretation.generate_shap_plots.delay(
        model_file=request.model_file
    )
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message="Model interpretation task started"
    )


@router.post("/model-analysis", response_model=TaskResponse)
async def start_model_analysis(request: ModelAnalysisRequest):
    task = model_analysis.analyze_model_with_surrogate.delay(
        model_file=request.model_file,
        selected_features=request.selected_features,
        max_depth=request.max_depth,
        min_samples_split=request.min_samples_split
    )
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message="Model analysis task started"
    )


@router.post("/backtest-construction", response_model=TaskResponse)
async def start_backtest_construction(request: BacktestConstructionRequest):
    task = backtest_construction.run_backtest_with_rules.delay(
        features_file=request.features_file,
        decision_rules=request.decision_rules,
        backtest_type=request.backtest_type,
        filter_type=request.filter_type,
        look_forward_bars=request.look_forward_bars,
        win_profit=request.win_profit,
        loss_cost=request.loss_cost,
        initial_balance=request.initial_balance
    )
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message="Backtest construction task started"
    )


@router.post("/backtest-execution", response_model=TaskResponse)
async def start_backtest_execution(request: BacktestExecutionRequest):
    task = backtest_execution.run_backtest.delay(
        strategy_config=request.strategy_config,
        data_file=request.data_file
    )
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message="Backtest execution task started"
    )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id)

    status_map = {
        "PENDING": "pending",
        "STARTED": "running",
        "PROGRESS": "running",
        "SUCCESS": "success",
        "FAILURE": "failure",
        "RETRY": "running",
        "REVOKED": "failure"
    }

    # 获取任务信息
    info = task_result.info if task_result.info else {}

    response = TaskStatusResponse(
        task_id=task_id,
        status=status_map.get(task_result.state, "pending"),
        progress=info.get('progress') if isinstance(info, dict) else None,
        result=task_result.result if task_result.successful() else (info if isinstance(info, dict) else None),
        error=str(task_result.info) if task_result.failed() else None
    )

    return response


# 数据文件管理接口
@router.get("/data-files")
async def list_data_files(directory: Optional[str] = Query(None, description="raw, processed, models, or plots")):
    """列出数据文件"""
    from app.core.config import settings
    import os

    dir_path = None
    if directory == "processed":
        dir_path = settings.PROCESSED_DATA_DIR
    elif directory == "models":
        dir_path = settings.MODELS_DIR
    elif directory == "plots":
        dir_path = settings.PLOTS_DIR
        # 对于 plots 目录，返回子目录列表（每个模型的 SHAP 图表目录）
        if os.path.exists(dir_path):
            subdirs = []
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isdir(item_path):
                    # 统计该目录下的图片数量
                    plot_files = [f for f in os.listdir(item_path) if f.endswith('.png')]
                    subdirs.append({
                        "dirname": item,
                        "plot_count": len(plot_files),
                        "path": item_path
                    })
            return {"files": subdirs, "total": len(subdirs)}
        else:
            return {"files": [], "total": 0}
    else:
        dir_path = settings.RAW_DATA_DIR

    files = DataFileService.list_data_files(dir_path)
    return {"files": files, "total": len(files)}


@router.delete("/data-files/{filename}")
async def delete_data_file(filename: str, directory: Optional[str] = Query("raw")):
    """删除数据文件"""
    from app.core.config import settings

    dir_path = None
    if directory == "processed":
        dir_path = settings.PROCESSED_DATA_DIR
    elif directory == "models":
        dir_path = settings.MODELS_DIR
    else:
        dir_path = settings.RAW_DATA_DIR

    success = DataFileService.delete_data_file(filename, dir_path)
    if success:
        return {"message": f"File {filename} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found or cannot be deleted")


@router.get("/data-files/{filename}/preview")
async def preview_data_file(filename: str, directory: Optional[str] = Query("raw"), rows: int = Query(10)):
    """预览数据文件"""
    from app.core.config import settings

    dir_path = None
    if directory == "processed":
        dir_path = settings.PROCESSED_DATA_DIR
    else:
        dir_path = settings.RAW_DATA_DIR

    try:
        preview = DataFileService.preview_data_file(filename, dir_path, rows)
        return preview
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plots/{dirname}/files")
async def get_plot_files(dirname: str):
    """获取特定 SHAP 目录下的所有图片文件"""
    from app.core.config import settings
    import os

    plots_dir = os.path.join(settings.PLOTS_DIR, dirname)

    if not os.path.exists(plots_dir):
        raise HTTPException(status_code=404, detail="Plots directory not found")

    # 读取该目录下的所有图片文件
    plot_files = []
    for filename in sorted(os.listdir(plots_dir)):
        if filename.endswith('.png'):
            plot_files.append(filename)

    # 尝试读取元数据
    metadata = None
    metadata_path = os.path.join(plots_dir, 'shap_metadata.pkl')
    if os.path.exists(metadata_path):
        try:
            import pickle
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
        except Exception as e:
            print(f"Error loading metadata: {e}")

    return {
        "dirname": dirname,
        "plot_files": plot_files,
        "total_plots": len(plot_files),
        "metadata": metadata
    }


@router.delete("/plots/{dirname}")
async def delete_plot_directory(dirname: str):
    """删除指定的 SHAP 图表目录"""
    from app.core.config import settings

    success = DataFileService.delete_directory(dirname, settings.PLOTS_DIR)
    if success:
        return {"message": f"Plot directory {dirname} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Directory not found or cannot be deleted")


@router.get("/labels/preview")
async def preview_label_data(
    data_file: str = Query(..., description="数据文件名"),
    label_file: str = Query(..., description="标签文件名"),
    offset: int = Query(0, description="起始位置"),
    limit: int = Query(100, description="返回的K线数量")
):
    """预览标签文件的K线和标签数据（从数据文件读取OHLCV，从标签文件读取标签）"""
    from app.core.config import settings
    import pandas as pd
    import os

    # 读取数据文件（OHLCV）
    data_file_path = os.path.join(settings.RAW_DATA_DIR, data_file)
    if not os.path.exists(data_file_path):
        raise HTTPException(status_code=404, detail=f"Data file not found: {data_file}")

    # 读取标签文件
    label_file_path = os.path.join(settings.PROCESSED_DATA_DIR, label_file)
    if not os.path.exists(label_file_path):
        raise HTTPException(status_code=404, detail=f"Label file not found: {label_file}")

    try:
        # 读取数据文件
        data_df = pd.read_pickle(data_file_path)

        # 确保数据文件有必要的列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in data_df.columns]
        if missing_cols:
            raise HTTPException(status_code=400, detail=f"Missing required columns in data file: {missing_cols}")

        # 读取标签文件
        label_df = pd.read_pickle(label_file_path)

        # 检查是否有标签列
        label_col = None
        for col in label_df.columns:
            if 'label' in col.lower():
                label_col = col
                break

        if label_col is None:
            raise HTTPException(status_code=400, detail="No label column found in label file")

        # 确保两个文件都有datetime信息
        if 'datetime' in data_df.columns:
            data_df = data_df.set_index('datetime')
        if 'datetime' in label_df.columns:
            label_df = label_df.set_index('datetime')

        # 确保索引是DatetimeIndex
        if not isinstance(data_df.index, pd.DatetimeIndex):
            raise HTTPException(status_code=400, detail="Data file must have datetime index or column")
        if not isinstance(label_df.index, pd.DatetimeIndex):
            raise HTTPException(status_code=400, detail="Label file must have datetime index or column")

        # 合并数据（基于时间戳）
        merged_df = data_df[required_cols].join(label_df[[label_col]], how='inner')

        # 获取总行数
        total_rows = len(merged_df)

        if total_rows == 0:
            raise HTTPException(status_code=400, detail="No matching timestamps between data file and label file")

        # 应用偏移和限制
        end_idx = min(offset + limit, total_rows)
        df_slice = merged_df.iloc[offset:end_idx].copy()

        # 准备返回数据
        kline_data = []
        for idx, row in df_slice.iterrows():
            # 转换时间戳为字符串
            if isinstance(idx, pd.Timestamp):
                time_str = idx.strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_str = str(idx)

            # 获取标签值
            label_value = row[label_col]
            # 处理NaN值
            if pd.isna(label_value):
                label_value = None
            else:
                label_value = float(label_value)

            kline_data.append({
                'datetime': time_str,
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume']),
                'label': label_value
            })

        # 计算标签统计信息
        label_series = merged_df[label_col].dropna()
        label_stats = {
            'total_samples': int(total_rows),
            'non_nan_labels': int(label_series.count()),
            'label_mean': float(label_series.mean()) if len(label_series) > 0 else None,
            'label_std': float(label_series.std()) if len(label_series) > 0 else None,
            'label_min': float(label_series.min()) if len(label_series) > 0 else None,
            'label_max': float(label_series.max()) if len(label_series) > 0 else None,
            'positive_count': int((label_series > 0).sum()),
            'negative_count': int((label_series < 0).sum()),
            'zero_count': int((label_series == 0).sum())
        }

        return {
            'data_file': data_file,
            'label_file': label_file,
            'total_rows': total_rows,
            'offset': offset,
            'limit': limit,
            'returned_rows': len(kline_data),
            'label_column': label_col,
            'kline_data': kline_data,
            'label_stats': label_stats
        }

    except Exception as e:
        import traceback
        print(f"Error previewing label data: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
