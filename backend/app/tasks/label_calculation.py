from app.core.celery_app import celery_app
from celery import Task
from celery.exceptions import Ignore
import pandas as pd
import numpy as np
import os
from app.core.config import settings
from app.services.label_processor import calculate_label_with_filter


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery_app.task(bind=True, base=CallbackTask)
def calculate_labels(self, data_file: str, window: int = 29, look_forward: int = 10, label_type: str = 'up', filter_type: str = 'rsi', threshold: float = None):
    """
    计算标签
    :param data_file: 原始数据文件名（不含路径），从raw目录读取
    :param window: 标签计算窗口，默认29
    :param look_forward: 预测未来多少个周期，默认10
    :param label_type: 标签类型，'up'上涨或'down'下跌
    :param filter_type: 过滤类型，'rsi'或'cti'
    :param threshold: 过滤阈值，如果为None则使用默认值
    """
    try:
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': '正在加载数据...', 'message': '读取pkl文件'})

        # 读取原始数据文件
        data_path = os.path.join(settings.RAW_DATA_DIR, data_file)
        if not os.path.exists(data_path):
            raise Exception(f"数据文件不存在: {data_file}")

        df = pd.read_pickle(data_path)
        self.update_state(state='PROGRESS', meta={'progress': 10, 'status': '数据加载完成', 'message': f'共 {len(df)} 行数据'})

        # 确保有必要的列（至少要有close价格）
        if 'close' not in df.columns:
            raise Exception("特征文件中缺少'close'列，无法计算标签")

        self.update_state(state='PROGRESS', meta={
            'progress': 20,
            'status': '正在计算标签...',
            'message': f'窗口: {window}, 预测周期: {look_forward}, 类型: {label_type}, 过滤: {filter_type}, 阈值: {threshold}'
        })

        # 计算标签
        labels = calculate_label_with_filter(df, window=window, look_forward=look_forward, label_type=label_type, filter_type=filter_type, threshold=threshold)

        # 重要：使用.values来赋值，避免索引不匹配导致的行数翻倍问题
        df['label'] = labels.values

        self.update_state(state='PROGRESS', meta={
            'progress': 60,
            'status': '标签计算完成',
            'message': '正在统计标签信息...'
        })

        # 计算标签统计
        label_stats = {
            'total_samples': int(len(df)),
            'non_nan_labels': int(df['label'].notna().sum()),
            'label_mean': float(df['label'].mean()) if df['label'].notna().sum() > 0 else 0.0,
            'label_std': float(df['label'].std()) if df['label'].notna().sum() > 0 else 0.0,
            'positive_ratio': float((df['label'] > 0.5).sum() / df['label'].notna().sum()) if df['label'].notna().sum() > 0 else 0.0
        }

        self.update_state(state='PROGRESS', meta={
            'progress': 70,
            'status': '正在保存标签文件...',
            'message': f'非空标签数: {label_stats["non_nan_labels"]}'
        })

        # 构建标签文件名
        # 从 data_file 中提取基础名称
        # 例如: ETHUSDT_BINANCE_2024-01-01_00_00_00_2024-12-31_23_59_59.pkl
        # 转换为: ETHUSDT_BINANCE_2024-01-01_00_00_00_2024-12-31_23_59_59_labels_w29_f10.pkl
        base_name = data_file.replace('.pkl', '')

        labels_filename = f"{base_name}_labels_w{window}_f{look_forward}.pkl"
        labels_path = os.path.join(settings.PROCESSED_DATA_DIR, labels_filename)

        # 保存标签文件（包含datetime和label列）
        cols_to_save = []
        if 'datetime' in df.columns:
            cols_to_save.append('datetime')
        elif isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            if 'datetime' not in df.columns:
                df.rename(columns={'index': 'datetime'}, inplace=True)
            cols_to_save.append('datetime')

        cols_to_save.append('label')
        labels_df = df[cols_to_save].copy()

        labels_df.to_pickle(labels_path)

        self.update_state(state='PROGRESS', meta={
            'progress': 90,
            'status': '标签文件保存完成',
            'message': f'文件: {labels_filename}'
        })

        self.update_state(state='PROGRESS', meta={'progress': 100, 'status': '完成！', 'message': '标签计算完成'})

        # 返回结果
        return {
            "status": "success",
            "labels_file": labels_filename,
            "labels_path": labels_path,
            "data_file": data_file,
            "window": int(window),
            "look_forward": int(look_forward),
            "label_stats": label_stats,
            "total_rows": int(len(df)),
            "message": "标签计算成功"
        }

    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()

        print(f"[ERROR] 标签计算任务失败: {error_msg}")
        print(f"[ERROR] 错误堆栈:\n{error_trace}")

        self.update_state(state='FAILURE', meta={
            'status': 'error',
            'message': error_msg,
            'traceback': error_trace
        })

        raise Ignore()
