from app.core.celery_app import celery_app
from celery import Task
from celery.exceptions import Ignore
import os
import pickle
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import List, Dict, Any
from datetime import datetime, timedelta
from tqdm import tqdm
from ..services.calculate_indicator import calculate_RSI,calculate_fast_cti


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery_app.task(bind=True, base=CallbackTask)
def run_backtest_with_rules(
    self,
    features_file: str,
    decision_rules: List[Dict[str, Any]],
    look_forward_bars: int = 10,
    win_profit: float = 4.0,
    loss_cost: float = 5.0,
    initial_balance: float = 1000.0,
    backtest_type: str = 'long',
    filter_type: str = 'rsi'
):
    """
    使用决策规则执行回测

    参数:
        features_file: 特征数据文件名（包含特征的已处理数据文件）
        decision_rules: 决策规则列表，格式：
            [
                {
                    "rule_id": 1,
                    "thresholds": [
                        {"feature": "CNTP30", "operator": "<=", "value": 0.5},
                        {"feature": "IMIN240", "operator": ">", "value": 1.2}
                    ],
                    "predicted_class": 1,
                    "confidence": 0.75
                },
                ...
            ]
        look_forward_bars: 未来看多少根K线判断盈亏
        win_profit: 盈利金额
        loss_cost: 亏损金额
        initial_balance: 初始余额
        backtest_type: 回测类型，'long' 为开多单回测，'short' 为开空单回测
        filter_type: 过滤指标类型，'rsi' 或 'cti'
    """
    from app.core.config import settings

    self.update_state(state='PROGRESS', meta={'progress': 0, 'status': '开始回测...'})

    try:
        # 1. 加载特征数据
        self.update_state(state='PROGRESS', meta={'progress': 10, 'status': '加载特征数据...'})

        # 检查文件名是否包含 features，如果不包含，尝试查找对应的特征文件
        if 'features' not in features_file.lower():
            # 尝试自动找到对应的特征文件
            base_name = features_file.replace('.pkl', '')
            # 在 processed_data 目录中查找匹配的特征文件
            if os.path.exists(settings.PROCESSED_DATA_DIR):
                available_files = [f for f in os.listdir(settings.PROCESSED_DATA_DIR)
                                 if f.endswith('.pkl') and 'features' in f.lower() and base_name in f]

                if available_files:
                    # 找到匹配的特征文件，使用第一个
                    features_file = available_files[0]
                    self.update_state(state='PROGRESS', meta={
                        'progress': 5,
                        'status': '自动匹配特征文件',
                        'message': f'找到特征文件: {features_file}'
                    })
                else:
                    raise ValueError(
                        f"文件名不符合特征文件格式: {features_file}。\n"
                        f"特征文件名应包含 'features'。\n"
                        f"未能找到对应的特征文件，请确保已运行特征计算模块。"
                    )
            else:
                raise ValueError(f"processed_data 目录不存在")

        features_path = os.path.join(settings.PROCESSED_DATA_DIR, features_file)

        if not os.path.exists(features_path):
            # 列出目录中的文件以帮助调试
            available_files = []
            if os.path.exists(settings.PROCESSED_DATA_DIR):
                available_files = [f for f in os.listdir(settings.PROCESSED_DATA_DIR)
                                 if f.endswith('.pkl') and 'features' in f.lower()]

            error_msg = f"特征数据文件不存在: {features_file}\n"
            error_msg += f"查找路径: {features_path}\n"
            if available_files:
                error_msg += f"可用的特征文件: {', '.join(available_files[:5])}"
            else:
                error_msg += "目录中没有找到特征文件，请先运行特征计算模块"

            raise FileNotFoundError(error_msg)

        with open(features_path, 'rb') as f:
            df = pickle.load(f)

        if not isinstance(df, pd.DataFrame):
            raise ValueError("特征数据格式错误，应为DataFrame")

        self.update_state(state='PROGRESS', meta={
            'progress': 20,
            'status': '特征数据加载完成',
            'message': f'数据行数: {len(df)}'
        })

        # 2. 验证特征存在性
        self.update_state(state='PROGRESS', meta={'progress': 25, 'status': '验证特征...'})

        # 从决策规则中提取所需特征列表
        required_features = set()
        for rule in decision_rules:
            for threshold in rule.get('thresholds', []):
                required_features.add(threshold['feature'])

        # 检查特征是否存在
        missing_features = [f for f in required_features if f not in df.columns]

        if missing_features:
            raise ValueError(f"数据中缺少以下特征: {missing_features}。请确保选择的是包含特征的已处理数据文件。")

        self.update_state(state='PROGRESS', meta={
            'progress': 40,
            'status': '特征验证完成',
            'message': f'特征数: {len(required_features)}'
        })

        # 3. 生成开仓信号
        self.update_state(state='PROGRESS', meta={'progress': 50, 'status': '生成开仓信号...'})

        # 添加调试信息
        print(f"[DEBUG] 回测类型: {backtest_type}")
        print(f"[DEBUG] 决策规则数量: {len(decision_rules)}")
        for idx, rule in enumerate(decision_rules):
            print(f"[DEBUG] 规则 {idx+1}: predicted_class={rule.get('predicted_class')}, confidence={rule.get('confidence')}")
            print(f"[DEBUG] 规则 {idx+1} 阈值条件: {rule.get('thresholds')}")

        df['open_signal'] = generate_open_signal(df, decision_rules, backtest_type)

        signal_count = df['open_signal'].sum()
        print(f"[DEBUG] 生成的开仓信号数量: {signal_count}")

        self.update_state(state='PROGRESS', meta={
            'progress': 60,
            'status': '开仓信号生成完成',
            'message': f'信号数: {signal_count}'
        })

        # 4. 执行回测
        self.update_state(state='PROGRESS', meta={'progress': 65, 'status': '执行回测...'})

        results_df, trades_df, stats = backtest_strategy(
            df=df,
            look_forward_bars=look_forward_bars,
            win_profit=win_profit,
            loss_cost=loss_cost,
            initial_balance=initial_balance,
            backtest_type=backtest_type,
            filter_type=filter_type
        )

        self.update_state(state='PROGRESS', meta={
            'progress': 85,
            'status': '回测完成',
            'message': f'交易次数: {stats["total_trades"]}'
        })

        # 5. 生成资金曲线图
        self.update_state(state='PROGRESS', meta={'progress': 90, 'status': '生成资金曲线图...'})

        # 创建图表目录（包含回测类型和毫秒时间戳）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')  # 精确到微秒
        backtest_type_label = 'long' if backtest_type == 'long' else 'short'
        plots_dir = os.path.join(settings.PLOTS_DIR, f'backtest_{backtest_type_label}_{timestamp}')
        os.makedirs(plots_dir, exist_ok=True)

        print(f"[DEBUG] 创建回测图表目录: backtest_{backtest_type_label}_{timestamp}")
        print(f"[DEBUG] 完整路径: {plots_dir}")

        # 绘制资金曲线
        plt.figure(figsize=(12, 6))
        plt.plot(results_df.index, results_df['balance'], linewidth=2)
        plt.axhline(y=initial_balance, color='r', linestyle='--', label='Initial Balance')

        # 标题显示回测类型
        backtest_type_title = '开多单回测' if backtest_type == 'long' else '开空单回测'
        plt.title(f'Balance Curve ({backtest_type_title})', fontsize=14, fontweight='bold')
        plt.xlabel('Time')
        plt.ylabel('Balance')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        balance_curve_path = os.path.join(plots_dir, 'balance_curve.png')
        plt.savefig(balance_curve_path, dpi=150, bbox_inches='tight')
        plt.close()

        # 绘制交易分布图
        if len(trades_df) > 0:
            fig, axes = plt.subplots(2, 1, figsize=(12, 8))

            # 盈亏分布
            wins = trades_df[trades_df['is_win'] == True]
            losses = trades_df[trades_df['is_win'] == False]

            axes[0].scatter(wins.index, [1]*len(wins), c='green', marker='^',
                          s=50, alpha=0.6, label='Win')
            axes[0].scatter(losses.index, [0]*len(losses), c='red', marker='v',
                          s=50, alpha=0.6, label='Loss')
            axes[0].set_title(f'Trade Win/Loss Distribution ({backtest_type_title})', fontweight='bold')
            axes[0].set_ylabel('Win/Loss')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)

            # 累计盈亏
            trades_df['cumulative_pnl'] = 0.0
            cumulative = initial_balance
            for idx, row in trades_df.iterrows():
                if row['is_win']:
                    cumulative += row['win_profit']
                else:
                    cumulative -= row['loss_cost']
                trades_df.at[idx, 'cumulative_pnl'] = cumulative - initial_balance

            axes[1].plot(trades_df.index, trades_df['cumulative_pnl'], linewidth=2)
            axes[1].axhline(y=0, color='r', linestyle='--')
            axes[1].set_title('Cumulative P&L', fontweight='bold')
            axes[1].set_ylabel('P&L')
            axes[1].set_xlabel('Time')
            axes[1].grid(True, alpha=0.3)

            plt.tight_layout()
            trades_dist_path = os.path.join(plots_dir, 'trades_distribution.png')
            plt.savefig(trades_dist_path, dpi=150, bbox_inches='tight')
            plt.close()

        self.update_state(state='PROGRESS', meta={'progress': 95, 'status': '保存结果...'})

        # 保存结果数据
        results_file = os.path.join(plots_dir, 'backtest_results.pkl')
        with open(results_file, 'wb') as f:
            pickle.dump({
                'results_df': results_df,
                'trades_df': trades_df,
                'stats': stats,
                'parameters': {
                    'features_file': features_file,
                    'decision_rules': decision_rules,
                    'backtest_type': backtest_type,
                    'look_forward_bars': look_forward_bars,
                    'win_profit': win_profit,
                    'loss_cost': loss_cost,
                    'initial_balance': initial_balance
                }
            }, f)

        self.update_state(state='PROGRESS', meta={'progress': 100, 'status': '回测完成'})

        # 返回结果
        return {
            "status": "success",
            "stats": stats,
            "plots_dir": f'backtest_{backtest_type_label}_{timestamp}',
            "balance_curve": 'balance_curve.png',
            "trades_distribution": 'trades_distribution.png' if len(trades_df) > 0 else None,
            "backtest_type": backtest_type,
            "message": "回测成功完成"
        }

    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()

        print(f"[ERROR] 回测任务失败: {error_msg}")
        print(f"[ERROR] 错误堆栈:\n{error_trace}")

        self.update_state(state='FAILURE', meta={
            'status': 'error',
            'message': error_msg,
            'traceback': error_trace
        })

        raise Ignore()


def generate_open_signal(df: pd.DataFrame, decision_rules: List[Dict[str, Any]], backtest_type: str = 'long') -> pd.Series:
    """
    根据决策规则生成开仓信号

    规则之间是OR的关系（满足任意一条规则即可开仓）
    每条规则内的阈值条件是AND的关系（必须同时满足）

    参数:
        df: 数据DataFrame
        decision_rules: 决策规则列表
        backtest_type: 回测类型，'long' 为开多单回测（使用predicted_class=1的规则），
                      'short' 为开空单回测（使用predicted_class=0的规则）
    """
    # 初始化信号为False
    open_signal = pd.Series([False] * len(df), index=df.index)

    # 根据回测类型确定使用哪个预测类别
    target_class = 1 if backtest_type == 'long' else 0

    # 遍历每条规则
    for rule in decision_rules:
        # 根据回测类型选择对应的规则
        if rule.get('predicted_class', 1) != target_class:
            continue

        # 初始化当前规则的条件（全True）
        rule_condition = pd.Series([True] * len(df), index=df.index)

        # 应用规则中的所有阈值条件（AND关系）
        for threshold in rule.get('thresholds', []):
            feature = threshold['feature']
            operator = threshold['operator']
            value = threshold['value']

            if feature not in df.columns:
                continue

            # 根据操作符应用条件
            if operator == '<=':
                rule_condition &= (df[feature] <= value)
            elif operator == '>':
                rule_condition &= (df[feature] > value)
            elif operator == '<':
                rule_condition &= (df[feature] < value)
            elif operator == '>=':
                rule_condition &= (df[feature] >= value)
            elif operator == '==':
                rule_condition &= (df[feature] == value)
            elif operator == '!=':
                rule_condition &= (df[feature] != value)

        # 将当前规则的条件合并到总信号中（OR关系）
        open_signal |= rule_condition

    return open_signal


def backtest_strategy(
    df: pd.DataFrame,
    look_forward_bars: int = 10,
    win_profit: float = 4.0,
    loss_cost: float = 5.0,
    initial_balance: float = 1000.0,
    backtest_type: str = 'long',
    filter_type: str = 'rsi'
) -> tuple:
    """
    执行回测策略（简化版，只做首次开仓）

    参数:
        df: 数据DataFrame
        look_forward_bars: 未来看多少根K线判断盈亏
        win_profit: 盈利金额
        loss_cost: 亏损金额
        initial_balance: 初始余额
        backtest_type: 回测类型，'long' 为开多单回测，'short' 为开空单回测
        filter_type: 过滤指标类型，'rsi' 或 'cti'

    返回:
        results_df: 每根K线的余额记录
        trades_df: 交易记录
        stats: 统计信息
    """
    results = []
    trades = []
    current_balance = initial_balance

    # 最小订单间隔（分钟）
    order_interval = 30
    last_order_time = None

    # 确保索引是datetime类型
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')
        else:
            raise ValueError("数据必须包含datetime列或datetime索引")

    # 遍历K线数据
    total_bars = len(df) - look_forward_bars
    print(f"[DEBUG] 开始回测，回测类型: {backtest_type}")
    print(f"[DEBUG] 总K线数: {len(df)}, 可回测K线数: {total_bars}")
    print(f"[DEBUG] 开仓信号总数: {df['open_signal'].sum()}")

    # 计算过滤指标
    if filter_type == 'rsi':
        df['filter_indicator'] = calculate_RSI(df, 14)
    else:  # cti
        df['filter_indicator'] = calculate_fast_cti(df)

    for i in range(0, len(df) - look_forward_bars):
        row = df.iloc[i]
        current_time = df.index[i]

        # 检查是否满足订单间隔
        can_order = True
        if last_order_time is not None:
            time_diff = (current_time - last_order_time).total_seconds() / 60
            if time_diff < order_interval:
                can_order = False

        # 根据回测类型和过滤指标类型判断过滤条件
        if filter_type == 'rsi':
            if backtest_type == 'long':
                filter_condition = row['filter_indicator'] < 30
            else:  # short
                filter_condition = row['filter_indicator'] > 70
        else:  # cti
            if backtest_type == 'long':
                filter_condition = row['filter_indicator'] < -0.5
            else:  # short
                filter_condition = row['filter_indicator'] > 0.5

        # 处理开仓信号
        if row['open_signal'] and can_order and filter_condition:
            entry_price = row['close']
            future_price = df.iloc[i + look_forward_bars]['close']

            # 根据回测类型判断盈亏
            if backtest_type == 'long':
                # 开多单：未来价格上涨为盈利
                is_win = future_price > entry_price
            else:  # short
                # 开空单：未来价格下跌为盈利
                is_win = future_price < entry_price

            trade_info = {
                'datetime': current_time,
                'entry_price': entry_price,
                'future_price': future_price,
                'is_win': is_win,
                'win_profit': win_profit,
                'loss_cost': loss_cost,
                'balance_before': current_balance,
                'backtest_type': backtest_type
            }

            # 更新余额
            if is_win:
                current_balance += win_profit
            else:
                current_balance -= loss_cost

            trade_info['balance_after'] = current_balance
            trades.append(trade_info)

            # 更新最后订单时间
            last_order_time = current_time

            # 输出前几笔交易的调试信息
            if len(trades) <= 5:
                position_type = "多单" if backtest_type == 'long' else "空单"
                print(f"[DEBUG] 交易 {len(trades)} ({position_type}): 时间={current_time}, 入场={entry_price:.2f}, 未来={future_price:.2f}, 盈亏={'盈利' if is_win else '亏损'}")

        # 记录当前余额
        results.append({
            'datetime': current_time,
            'balance': current_balance
        })

    print(f"[DEBUG] 回测完成，总交易数: {len(trades)}")

    # 转换为DataFrame
    results_df = pd.DataFrame(results).set_index('datetime')
    trades_df = pd.DataFrame(trades)
    if len(trades_df) > 0:
        trades_df = trades_df.set_index('datetime')

    # 计算统计信息
    total_trades = len(trades)
    winning_trades = sum(1 for trade in trades if trade['is_win'])
    losing_trades = total_trades - winning_trades
    win_rate = winning_trades / total_trades if total_trades > 0 else 0

    # 计算最大回撤
    max_balance = initial_balance
    max_drawdown = 0
    for balance in results_df['balance']:
        if balance > max_balance:
            max_balance = balance
        drawdown = (max_balance - balance) / max_balance if max_balance > 0 else 0
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    stats = {
        'total_trades': int(total_trades),
        'winning_trades': int(winning_trades),
        'losing_trades': int(losing_trades),
        'win_rate': float(win_rate),
        'initial_balance': float(initial_balance),
        'final_balance': float(current_balance),
        'profit': float(current_balance - initial_balance),
        'profit_rate': float((current_balance - initial_balance) / initial_balance) if initial_balance > 0 else 0,
        'max_drawdown': float(max_drawdown)
    }

    return results_df, trades_df, stats
