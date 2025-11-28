from app.core.celery_app import celery_app
from celery import Task
from celery.exceptions import Ignore
import pandas as pd
import numpy as np
import os
import pickle
import lightgbm as lgb
from app.core.config import settings


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery_app.task(bind=True, base=CallbackTask)
def train_lightgbm_model(self, features_file: str, labels_file: str, num_boost_round: int = 500):
    """
    训练LightGBM模型
    :param features_file: 特征文件名
    :param labels_file: 标签文件名
    :param num_boost_round: boosting迭代次数，默认500
    """
    try:
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': '正在加载数据...', 'message': '读取特征和标签文件'})

        # 读取特征文件
        features_path = os.path.join(settings.PROCESSED_DATA_DIR, features_file)
        if not os.path.exists(features_path):
            raise Exception(f"特征文件不存在: {features_file}")

        # 读取标签文件
        labels_path = os.path.join(settings.PROCESSED_DATA_DIR, labels_file)
        if not os.path.exists(labels_path):
            raise Exception(f"标签文件不存在: {labels_file}")

        features_df = pd.read_pickle(features_path)
        labels_df = pd.read_pickle(labels_path)

        self.update_state(state='PROGRESS', meta={
            'progress': 10,
            'status': '数据加载完成',
            'message': f'特征: {len(features_df)} 行, 标签: {len(labels_df)} 行'
        })

        # 对齐数据 - 使用datetime列进行merge
        if 'datetime' in features_df.columns and 'datetime' in labels_df.columns:
            # 为避免'datetime'同时出现在index和columns，统一重置索引，并只保留一份'datetime'列
            features_df_reset = features_df.reset_index() if 'datetime' not in features_df.columns else features_df.copy()
            labels_df_reset = labels_df.reset_index() if 'datetime' not in labels_df.columns else labels_df.copy()

            # 如果reset_index后'datetime'也出现在columns和index，drop掉多余的列
            if 'datetime' in features_df_reset.index.names:
                # 修复“cannot insert datetime, already exists”错误，使用drop=True避免重复'datetime'列
                features_df_reset = features_df_reset.reset_index(drop=True)

            # 如同时有'datetime'在列和重置后出现'datetime'重复列，只保留一个'datetime'
            if features_df_reset.columns.duplicated().any():
                features_df_reset = features_df_reset.loc[:, ~features_df_reset.columns.duplicated()]

            merged_df = pd.merge(features_df_reset, labels_df_reset, on='datetime', how='inner')
        else:
            # 如果没有datetime列，假设索引对齐
            merged_df = features_df.copy()
            merged_df['label'] = labels_df['label'].values[:len(features_df)]

        self.update_state(state='PROGRESS', meta={
            'progress': 20,
            'status': '数据对齐完成',
            'message': f'合并后数据: {len(merged_df)} 行'
        })

        # 过滤掉标签为NaN的行
        merged_df = merged_df.dropna(subset=['label'])

        self.update_state(state='PROGRESS', meta={
            'progress': 25,
            'status': '数据清洗完成',
            'message': f'有效样本: {len(merged_df)} 行'
        })

        # 提取特征列（排除datetime、OHLCV基础列、label）
        exclude_cols = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'label']
        feature_cols = [col for col in merged_df.columns if col not in exclude_cols]

        X = merged_df[feature_cols].values
        y = merged_df['label'].values

        self.update_state(state='PROGRESS', meta={
            'progress': 30,
            'status': '准备训练数据',
            'message': f'特征数: {len(feature_cols)}, 样本数: {len(X)}'
        })

        # 创建LightGBM数据集
        lgb_train = lgb.Dataset(X, label=y)

        self.update_state(state='PROGRESS', meta={
            'progress': 35,
            'status': '开始训练模型...',
            'message': f'使用LightGBM, 迭代次数: {num_boost_round}'
        })

        # 设置参数
        params = {
            'objective': 'regression',
            'metric': 'l2',
            'verbosity': -1,
            'num_threads': 4,
        }

        # 训练模型（带进度回调）
        progress_callback_data = {'current': 0, 'total': num_boost_round}

        def progress_callback(env):
            progress_callback_data['current'] = env.iteration
            progress_percent = 35 + (env.iteration / num_boost_round) * 50
            self.update_state(state='PROGRESS', meta={
                'progress': progress_percent,
                'status': '模型训练中...',
                'message': f'迭代: {env.iteration}/{num_boost_round}'
            })

        gbm = lgb.train(
            params,
            lgb_train,
            num_boost_round=num_boost_round,
            callbacks=[progress_callback]
        )

        self.update_state(state='PROGRESS', meta={
            'progress': 85,
            'status': '模型训练完成',
            'message': '正在计算特征重要性...'
        })

        # 计算特征重要性
        imp_lgb = pd.Series(gbm.feature_importance(importance_type='gain'), index=feature_cols)
        imp_lgb = imp_lgb.sort_values(ascending=False)
        top20_importance = imp_lgb.head(20).to_dict()

        self.update_state(state='PROGRESS', meta={
            'progress': 90,
            'status': '正在保存模型...',
            'message': '保存模型和元数据'
        })

        # 构建模型文件名
        # 从特征文件中提取基础名称
        base_name = features_file.replace('_features', '').replace('.pkl', '')
        # 移除alpha类型后缀
        for alpha_type in ['_alpha158', '_alpha216', '_alpha101', '_alpha191','_alpha_ch']:
            base_name = base_name.replace(alpha_type, '')

        model_filename = f"{base_name}_model_lgb.pkl"
        model_path = os.path.join(settings.MODELS_DIR, model_filename)

        # 保存模型和元数据
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

        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)

        self.update_state(state='PROGRESS', meta={
            'progress': 100,
            'status': '完成！',
            'message': '模型训练和保存完成'
        })

        # 返回结果
        return {
            "status": "success",
            "model_file": model_filename,
            "model_path": model_path,
            "features_file": features_file,
            "labels_file": labels_file,
            "num_features": int(len(feature_cols)),
            "train_samples": int(len(X)),
            "num_boost_round": int(num_boost_round),
            "top20_importance": {k: float(v) for k, v in top20_importance.items()},
            "message": "模型训练成功"
        }

    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()

        print(f"[ERROR] 模型训练任务失败: {error_msg}")
        print(f"[ERROR] 错误堆栈:\n{error_trace}")

        self.update_state(state='FAILURE', meta={
            'status': 'error',
            'message': error_msg,
            'traceback': error_trace
        })

        raise Ignore()

