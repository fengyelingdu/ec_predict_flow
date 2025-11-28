from app.core.celery_app import celery_app
from celery import Task
from celery.exceptions import Ignore
import pandas as pd
import numpy as np
import os
import sys
from app.core.config import settings

# 将services目录添加到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery_app.task(bind=True, base=CallbackTask)
def calculate_features(self, data_file: str, alpha_types: list):
    """
    计算特征（不包括标签）
    :param data_file: 数据文件名（不含路径）
    :param alpha_types: alpha类型列表，如 ['alpha158', 'alpha216']
    """
    try:
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': '正在加载数据...', 'message': '读取pkl文件'})

        # 读取数据文件
        data_path = os.path.join(settings.RAW_DATA_DIR, data_file)
        if not os.path.exists(data_path):
            raise Exception(f"数据文件不存在: {data_file}")

        df = pd.read_pickle(data_path)
        self.update_state(state='PROGRESS', meta={'progress': 5, 'status': '数据加载完成', 'message': f'共 {len(df)} 行数据'})

        # 导入处理器
        from ..services.data_processor import DataProcessor

        # 初始化处理器
        processor = DataProcessor(df)

        total_features = 0
        feature_counts = {}

        # 计算选中的特征
        progress_per_alpha = 40 / len(alpha_types) if alpha_types else 40

        for idx, alpha_type in enumerate(alpha_types):
            base_progress = 10 + idx * progress_per_alpha

            self.update_state(state='PROGRESS', meta={
                'progress': base_progress,
                'status': f'正在计算 {alpha_type} 特征...',
                'message': f'特征类型: {alpha_type}'
            })

            if alpha_type == 'alpha158':
                processor.generate_features_alpha158()
                feature_counts['alpha158'] = 158
            elif alpha_type == 'alpha216':
                processor.generate_features_alpha216()
                feature_counts['alpha216'] = 216
            elif alpha_type == 'alpha101':
                processor.generate_features_alpha101()
                feature_counts['alpha101'] = 101
            elif alpha_type == 'alpha191':
                processor.generate_features_alpha191()
                feature_counts['alpha191'] = 191
            elif alpha_type == 'alpha_ch':
                processor.generate_features_alpha_ch()
                feature_counts['alpha_ch'] = 178   
            else:
                raise Exception(f"不支持的alpha类型: {alpha_type}")

            self.update_state(state='PROGRESS', meta={
                'progress': base_progress + progress_per_alpha * 0.9,
                'status': f'{alpha_type} 特征计算完成',
                'message': f'已生成特征'
            })

        total_features = len(processor.feature_columns)

        self.update_state(state='PROGRESS', meta={
            'progress': 70,
            'status': '正在清理数据...',
            'message': f'共 {total_features} 个特征'
        })

        # 清理数据（去除NaN）
        #processed_df = processor.df.dropna()
        processed_df = processor.df

        self.update_state(state='PROGRESS', meta={
            'progress': 80,
            'status': '正在保存文件...',
            'message': f'有效数据: {len(processed_df)} 行'
        })

        # 构建文件名
        base_name = data_file.replace('.pkl', '')
        alpha_suffix = '_'.join(sorted(alpha_types))

        # 保存特征文件
        features_filename = f"{base_name}_features_{alpha_suffix}.pkl"
        features_path = os.path.join(settings.PROCESSED_DATA_DIR, features_filename)

        # 保存特征列、基础OHLCV列和datetime
        feature_cols = processor.feature_columns.copy()
        base_cols = ['open', 'high', 'low', 'close', 'volume']

        # 构建要保存的列
        cols_to_save = []
        if 'datetime' in processed_df.columns:
            cols_to_save.append('datetime')

        # 添加基础OHLCV列（如果存在）
        for col in base_cols:
            if col in processed_df.columns:
                cols_to_save.append(col)

        # 添加特征列
        cols_to_save.extend(feature_cols)

        # 只保存存在的列
        cols_to_save = [col for col in cols_to_save if col in processed_df.columns]
        features_df = processed_df[cols_to_save].copy()

        # 如果索引是datetime，也保留
        if isinstance(processed_df.index, pd.DatetimeIndex) and 'datetime' not in features_df.columns:
            features_df['datetime'] = processed_df.index

        features_df.to_pickle(features_path)

        self.update_state(state='PROGRESS', meta={
            'progress': 95,
            'status': '特征文件保存完成',
            'message': f'文件: {features_filename}'
        })

        self.update_state(state='PROGRESS', meta={'progress': 100, 'status': '完成！', 'message': '特征计算完成'})

        # 返回结果，确保所有numpy/pandas类型都转换为Python原生类型
        return {
            "status": "success",
            "features_file": features_filename,
            "features_path": features_path,
            "total_features": int(total_features),
            "feature_counts": feature_counts,
            "alpha_types": alpha_types,
            "total_rows": int(len(df)),
            "valid_rows": int(len(processed_df)),
            "message": "特征计算成功"
        }

    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()

        print(f"[ERROR] 特征计算任务失败: {error_msg}")
        print(f"[ERROR] 错误堆栈:\n{error_trace}")

        self.update_state(state='FAILURE', meta={
            'status': 'error',
            'message': error_msg,
            'traceback': error_trace
        })

        raise Ignore()
