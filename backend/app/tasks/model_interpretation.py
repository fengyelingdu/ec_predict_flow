from app.core.celery_app import celery_app
from celery import Task
from celery.exceptions import Ignore
import pandas as pd
import numpy as np
import os
import pickle
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import shap
from app.core.config import settings


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery_app.task(bind=True, base=CallbackTask)
def generate_shap_plots(self, model_file: str):
    """
    使用SHAP生成模型解释图
    :param model_file: 模型文件名
    """
    try:
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': '正在加载模型...', 'message': '读取模型文件'})

        # 读取模型文件
        model_path = os.path.join(settings.MODELS_DIR, model_file)
        if not os.path.exists(model_path):
            raise Exception(f"模型文件不存在: {model_file}")

        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        gbm = model_data['model']
        feature_cols = model_data['feature_cols']
        features_file = model_data['features_file']
        labels_file = model_data['labels_file']

        self.update_state(state='PROGRESS', meta={
            'progress': 10,
            'status': '模型加载完成',
            'message': f'特征数: {len(feature_cols)}'
        })

        # 读取特征数据
        features_path = os.path.join(settings.PROCESSED_DATA_DIR, features_file)
        labels_path = os.path.join(settings.PROCESSED_DATA_DIR, labels_file)

        features_df = pd.read_pickle(features_path)
        labels_df = pd.read_pickle(labels_path)

        # 对齐数据
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
            merged_df = features_df.copy()
            merged_df['label'] = labels_df['label'].values[:len(features_df)]

        merged_df = merged_df.dropna(subset=['label'])

        X = merged_df[feature_cols].values
        y = merged_df['label'].values

        self.update_state(state='PROGRESS', meta={
            'progress': 20,
            'status': '数据加载完成',
            'message': f'样本数: {len(X)}'
        })

        # 创建SHAP explainer
        self.update_state(state='PROGRESS', meta={
            'progress': 25,
            'status': '正在初始化SHAP...',
            'message': '创建TreeExplainer'
        })

        explainer = shap.TreeExplainer(gbm)

        self.update_state(state='PROGRESS', meta={
            'progress': 30,
            'status': '正在计算SHAP值...',
            'message': '这可能需要几分钟...'
        })

        shap_values = explainer.shap_values(X)

        self.update_state(state='PROGRESS', meta={
            'progress': 50,
            'status': 'SHAP值计算完成',
            'message': '正在生成summary plot...'
        })

        # 创建输出目录
        base_name = model_file.replace('_model_lgb.pkl', '')
        plots_dir = os.path.join(settings.PLOTS_DIR, f'{base_name}_shap')
        os.makedirs(plots_dir, exist_ok=True)

        # 清除目录中已有文件
        for file in os.listdir(plots_dir):
            file_path = os.path.join(plots_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # 生成summary plots
        # 1. Bar plot (全局重要性)
        plt.figure(figsize=(10, 8))
        shap.summary_plot(shap_values, X, feature_names=feature_cols, plot_type="bar", max_display=20, show=False)
        bar_plot_path = os.path.join(plots_dir, '00_summary_bar.png')
        plt.savefig(bar_plot_path, bbox_inches='tight', dpi=150)
        plt.close()

        self.update_state(state='PROGRESS', meta={
            'progress': 55,
            'status': '生成summary dot plot...',
            'message': '特征影响分布图'
        })

        # 2. Dot plot (特征影响分布)
        plt.figure(figsize=(10, 8))
        shap.summary_plot(shap_values, X, feature_names=feature_cols, max_display=20, show=False)
        dot_plot_path = os.path.join(plots_dir, '00_summary_dot.png')
        plt.savefig(dot_plot_path, bbox_inches='tight', dpi=150)
        plt.close()

        self.update_state(state='PROGRESS', meta={
            'progress': 60,
            'status': '正在计算特征重要性...',
            'message': 'SHAP和皮尔逊相关性'
        })

        # 获取SHAP重要性前20特征
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        shap_order = np.argsort(mean_abs_shap)[::-1]
        top20_features_shap = [feature_cols[i] for i in shap_order[:20]]

        # 计算皮尔逊相关系数
        corrs = pd.Series({col: np.corrcoef(merged_df[col].values, y)[0, 1]
                          for col in feature_cols if col in merged_df.columns})
        corrs_abs = corrs.abs().sort_values(ascending=False)
        top20_features_corr = corrs_abs.head(20).index.tolist()

        # 合并两者，SHAP优先
        all_top_features = top20_features_shap.copy()
        for f in top20_features_corr:
            if f not in all_top_features:
                all_top_features.append(f)

        self.update_state(state='PROGRESS', meta={
            'progress': 65,
            'status': '正在生成dependence plots...',
            'message': f'共 {len(all_top_features)} 个特征'
        })

        # 生成dependence plots
        plot_files = []
        total_features = len(all_top_features)

        for idx, feat in enumerate(all_top_features):
            # 更新进度
            progress_percent = 65 + ((idx + 1) / total_features) * 30
            self.update_state(state='PROGRESS', meta={
                'progress': progress_percent,
                'status': f'生成dependence plot: {idx+1}/{total_features}',
                'message': f'特征: {feat}'
            })

            try:
                plt.figure(figsize=(10, 6))
                feature_idx = feature_cols.index(feat)
                shap.dependence_plot(feature_idx, shap_values, X, feature_names=feature_cols, show=False)
                plt.title(f"{idx+1:02d}_{feat}")

                save_path = os.path.join(plots_dir, f"{idx+1:02d}_{feat}.png")
                plt.savefig(save_path, bbox_inches="tight", dpi=150)
                plt.close()

                plot_files.append(f"{idx+1:02d}_{feat}.png")
            except Exception as e:
                print(f"Error generating plot for {feat}: {e}")
                plt.close()
                continue

        self.update_state(state='PROGRESS', meta={
            'progress': 95,
            'status': '正在保存元数据...',
            'message': '保存特征重要性信息'
        })

        # 保存SHAP重要性和相关性信息
        shap_importance = {feature_cols[i]: float(mean_abs_shap[i]) for i in range(len(feature_cols))}
        shap_importance_sorted = dict(sorted(shap_importance.items(), key=lambda x: x[1], reverse=True))

        metadata = {
            'model_file': model_file,
            'plots_dir': plots_dir,
            'total_plots': len(plot_files),
            'plot_files': plot_files,
            'shap_top20': top20_features_shap,
            'corr_top20': top20_features_corr,
            'all_top_features': all_top_features,
            'shap_importance': {k: float(v) for k, v in list(shap_importance_sorted.items())[:20]},
            'correlation': {k: float(v) for k, v in corrs_abs.head(20).items()}
        }

        metadata_path = os.path.join(plots_dir, 'shap_metadata.pkl')
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)

        self.update_state(state='PROGRESS', meta={
            'progress': 100,
            'status': '完成！',
            'message': 'SHAP分析完成'
        })

        # 返回结果
        return {
            "status": "success",
            "model_file": model_file,
            "plots_dir": plots_dir,
            "plots_dir_name": f'{base_name}_shap',  # 仅目录名，用于前端访问静态文件
            "total_plots": int(len(plot_files)),
            "plot_files": plot_files,
            "shap_top20": top20_features_shap,
            "corr_top20": top20_features_corr,
            "shap_importance": {k: float(v) for k, v in list(shap_importance_sorted.items())[:20]},
            "correlation": {k: float(v) for k, v in corrs_abs.head(20).items()},
            "message": "SHAP分析成功"
        }

    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()

        print(f"[ERROR] 模型解释任务失败: {error_msg}")
        print(f"[ERROR] 错误堆栈:\n{error_trace}")

        self.update_state(state='FAILURE', meta={
            'status': 'error',
            'message': error_msg,
            'traceback': error_trace
        })

        raise Ignore()
