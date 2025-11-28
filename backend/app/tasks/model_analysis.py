from app.core.celery_app import celery_app
from celery import Task
from celery.exceptions import Ignore
import os
import pickle
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier, _tree
from typing import List, Dict, Any


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery_app.task(bind=True, base=CallbackTask)
def analyze_model_with_surrogate(
    self,
    model_file: str,
    selected_features: List[str],
    max_depth: int = 3,
    min_samples_split: int = 100
):
    """
    使用代理模型（决策树）对选定的关键特征进行分析，提取阈值

    参数:
        model_file: 原始模型文件名（用于获取对应的数据）
        selected_features: 用户选择的关键特征列表（一般不多于8个）
        max_depth: 决策树最大深度（默认3层）
        min_samples_split: 节点分裂所需的最小样本数
    """
    from app.core.config import settings

    self.update_state(state='PROGRESS', meta={'progress': 0, 'status': '开始分析...'})

    try:
        # 1. 加载原始模型和数据
        self.update_state(state='PROGRESS', meta={'progress': 10, 'status': '加载模型和数据...'})

        model_path = os.path.join(settings.MODELS_DIR, model_file)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_file}")

        # 加载模型文件，从中读取特征和标签文件信息
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        # 从模型数据中获取特征和标签文件名
        features_file = model_data.get('features_file')
        labels_file = model_data.get('labels_file')

        if not features_file:
            raise ValueError("Model file does not contain features_file information")

        # 加载特征和标签数据
        features_path = os.path.join(settings.PROCESSED_DATA_DIR, features_file)
        if not os.path.exists(features_path):
            raise FileNotFoundError(f"Features file not found: {features_file}")

        features_df = pd.read_pickle(features_path)

        # 如果有标签文件，也加载
        if labels_file:
            labels_path = os.path.join(settings.PROCESSED_DATA_DIR, labels_file)
            if os.path.exists(labels_path):
                labels_df = pd.read_pickle(labels_path)

                # 对齐特征和标签数据
                if 'datetime' in features_df.columns and 'datetime' in labels_df.columns:
                    features_df_reset = features_df.reset_index() if 'datetime' not in features_df.columns else features_df.copy()
                    labels_df_reset = labels_df.reset_index() if 'datetime' not in labels_df.columns else labels_df.copy()

                    if 'datetime' in features_df_reset.index.names:
                        features_df_reset = features_df_reset.reset_index(drop=True)

                    if features_df_reset.columns.duplicated().any():
                        features_df_reset = features_df_reset.loc[:, ~features_df_reset.columns.duplicated()]

                    df = pd.merge(features_df_reset, labels_df_reset, on='datetime', how='inner')
                else:
                    df = features_df.copy()
                    df['label'] = labels_df['label'].values[:len(features_df)]
            else:
                # 如果标签文件不存在，假设特征文件中已包含label列
                df = features_df.copy()
        else:
            # 如果模型数据中没有labels_file信息，假设特征文件中已包含label列
            df = features_df.copy()

        # 确保选择的特征存在
        missing_features = [f for f in selected_features if f not in df.columns]
        if missing_features:
            raise ValueError(f"Features not found in data: {missing_features}")

        # 2. 准备训练数据
        self.update_state(state='PROGRESS', meta={'progress': 30, 'status': '准备训练数据...'})

        # 假设标签列名为 'label'
        if 'label' not in df.columns:
            raise ValueError("Label column not found in data")

        X = df[selected_features].copy()
        y = df['label'].copy()

        # 处理缺失值和无穷值
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(X.median())

        # 移除标签为NaN的行
        valid_mask = ~y.isna()
        X = X[valid_mask]
        y = y[valid_mask]

        # 确保标签是二元分类（0/1）
        unique_labels = y.unique()
        self.update_state(state='PROGRESS', meta={
            'progress': 35,
            'status': '检查标签类型...',
            'message': f'唯一标签值: {len(unique_labels)} 个'
        })

        # 如果标签是连续值，需要转换为二元分类
        if len(unique_labels) > 2:
            # 使用中位数作为阈值进行二值化
            threshold = y.median()
            y = (y > threshold).astype(int)
            self.update_state(state='PROGRESS', meta={
                'progress': 40,
                'status': '标签已二值化',
                'message': f'使用阈值: {threshold:.4f}'
            })
        else:
            # 确保标签是整数类型（即使已经是0/1，也可能是浮点数）
            y = y.astype(int)
            self.update_state(state='PROGRESS', meta={
                'progress': 40,
                'status': '标签类型已转换',
                'message': f'标签值: {sorted(y.unique().tolist())}'
            })

        # 3. 训练决策树代理模型
        self.update_state(state='PROGRESS', meta={'progress': 50, 'status': f'训练决策树（深度={max_depth}）...'})

        dt_model = DecisionTreeClassifier(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=50,
            random_state=42
        )

        dt_model.fit(X, y)

        # 4. 从决策树提取规则和阈值
        self.update_state(state='PROGRESS', meta={'progress': 70, 'status': '提取决策规则...'})

        rules = extract_decision_rules(dt_model, selected_features, X, y)

        # 5. 计算模型性能指标
        self.update_state(state='PROGRESS', meta={'progress': 85, 'status': '计算性能指标...'})

        train_accuracy = dt_model.score(X, y)

        # 计算每个特征的重要性
        feature_importance = dict(zip(selected_features, dt_model.feature_importances_))

        # 6. 保存结果
        self.update_state(state='PROGRESS', meta={'progress': 95, 'status': '保存分析结果...'})

        result = {
            "status": "success",
            "model_file": model_file,
            "features_file": features_file,  # 添加特征文件名
            "selected_features": selected_features,
            "num_features": len(selected_features),
            "tree_depth": max_depth,
            "train_accuracy": float(train_accuracy),
            "feature_importance": {k: float(v) for k, v in feature_importance.items()},
            "decision_rules": rules,
            "total_samples": len(X),
            "message": f"成功训练代理模型，提取了 {len(rules)} 条决策规则"
        }

        # 保存结果到文件
        base_name = model_file.replace('_model_lgb.pkl', '')
        result_file = f'{base_name}_surrogate_model.pkl'
        result_path = os.path.join(settings.MODELS_DIR, result_file)
        with open(result_path, 'wb') as f:
            pickle.dump({
                'model': dt_model,
                'features': selected_features,
                'rules': rules,
                'metadata': result
            }, f)

        self.update_state(state='PROGRESS', meta={'progress': 100, 'status': '分析完成'})

        return result

    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()

        print(f"[ERROR] 模型分析任务失败: {error_msg}")
        print(f"[ERROR] 错误堆栈:\n{error_trace}")

        self.update_state(state='FAILURE', meta={
            'status': 'error',
            'message': error_msg,
            'traceback': error_trace
        })

        raise Ignore()


def extract_decision_rules(tree_model: DecisionTreeClassifier, feature_names: List[str], X: pd.DataFrame, y: pd.Series) -> List[Dict[str, Any]]:
    """
    从训练好的决策树中提取决策规则和阈值

    返回格式:
    [
        {
            "rule_id": 1,
            "path": "feature1 <= 0.5 AND feature2 > 1.2",
            "features_used": ["feature1", "feature2"],
            "thresholds": [{"feature": "feature1", "operator": "<=", "value": 0.5}, ...],
            "samples": 1000,
            "class_distribution": {"0": 400, "1": 600},
            "predicted_class": 1,
            "confidence": 0.6
        },
        ...
    ]
    """
    tree = tree_model.tree_
    rules = []

    def recurse(node, path_conditions, path_features, path_thresholds):
        """递归遍历决策树"""
        # 如果是叶节点
        if tree.feature[node] == _tree.TREE_UNDEFINED:
            # 提取该叶节点的统计信息
            samples = tree.n_node_samples[node]
            value = tree.value[node][0]

            # 类别分布
            class_dist = {str(i): int(v) for i, v in enumerate(value)}
            predicted_class = int(np.argmax(value))
            confidence = float(value[predicted_class] / samples)

            # 只保留样本数较多的规则
            if samples >= 50:  # 至少50个样本
                rule = {
                    "rule_id": len(rules) + 1,
                    "path": " AND ".join(path_conditions) if path_conditions else "root",
                    "features_used": list(set(path_features)),
                    "thresholds": path_thresholds.copy(),
                    "samples": int(samples),
                    "class_distribution": class_dist,
                    "predicted_class": predicted_class,
                    "confidence": confidence
                }
                rules.append(rule)
            return

        # 获取当前节点的特征和阈值
        feature_idx = tree.feature[node]
        feature_name = feature_names[feature_idx]
        threshold = float(tree.threshold[node])

        # 左子树 (<=)
        left_condition = f"{feature_name} <= {threshold:.4f}"
        left_threshold = {
            "feature": feature_name,
            "operator": "<=",
            "value": threshold
        }
        recurse(
            tree.children_left[node],
            path_conditions + [left_condition],
            path_features + [feature_name],
            path_thresholds + [left_threshold]
        )

        # 右子树 (>)
        right_condition = f"{feature_name} > {threshold:.4f}"
        right_threshold = {
            "feature": feature_name,
            "operator": ">",
            "value": threshold
        }
        recurse(
            tree.children_right[node],
            path_conditions + [right_condition],
            path_features + [feature_name],
            path_thresholds + [right_threshold]
        )

    # 从根节点开始遍历
    recurse(0, [], [], [])

    # 按置信度排序
    rules.sort(key=lambda x: x['confidence'], reverse=True)

    return rules
