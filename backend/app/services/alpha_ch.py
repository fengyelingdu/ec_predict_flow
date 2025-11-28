# -*- coding: utf-8 -*-
"""
特征列表.py

实现所有特征的计算函数，每个函数格式如下：
    def calculate_xxxxx(df, timeperiod=xxxx):
"""

import numpy as np
import pandas as pd

# -----------------------------
# 辅助函数：通用技术指标计算
# -----------------------------
def sma(series, period):
    return series.rolling(window=period, min_periods=period).mean()

def ema(series, period):
    return series.ewm(span=period, adjust=False, min_periods=period).mean()

def vwma(df, period):
    # volume weighted moving average
    pv = df['close'] * df['volume']
    return pv.rolling(window=period, min_periods=period).sum() / df['volume'].rolling(window=period, min_periods=period).sum()

def rsi(series, period):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # 使用EMA计算平均涨跌幅，符合标准RSI算法
    avg_gain = gain.ewm(span=period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(span=period, adjust=False, min_periods=period).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - (100 / (1 + rs))

def stoch(df, period=14, smoothK=3):
    # Stochastic oscillator %K and %D (信号)
    low_min = df['low'].rolling(window=period, min_periods=period).min()
    high_max = df['high'].rolling(window=period, min_periods=period).max()
    k = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-10)
    d = sma(k, smoothK)
    return k, d

def williams_r(df, period=14):
    high_max = df['high'].rolling(window=period, min_periods=period).max()
    low_min = df['low'].rolling(window=period, min_periods=period).min()
    wr = -100 * (high_max - df['close']) / (high_max - low_min + 1e-10)
    return wr

def cci(df, period=20):
    tp = (df['high'] + df['low'] + df['close']) / 3.0
    sma_tp = sma(tp, period)
    mad = tp.rolling(window=period, min_periods=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    return (tp - sma_tp) / (0.015 * mad + 1e-10)

def mfi(df, period=14):
    # Money Flow Index - 向量化实现
    typical_price = (df['high'] + df['low'] + df['close']) / 3.0
    money_flow = typical_price * df['volume']

    # 计算价格变化
    price_diff = typical_price.diff()

    # 使用np.where向量化计算正负资金流
    positive_flow = pd.Series(np.where(price_diff > 0, money_flow, 0), index=df.index)
    negative_flow = pd.Series(np.where(price_diff < 0, money_flow, 0), index=df.index)

    # 计算滚动和
    positive_mf = positive_flow.rolling(window=period, min_periods=period).sum()
    negative_mf = negative_flow.rolling(window=period, min_periods=period).sum()

    # 计算MFI
    mfi_value = 100 - (100 / (1 + positive_mf / (negative_mf + 1e-10)))
    return mfi_value

def momentum(series, period=10):
    return series.diff(period)

def roc(series, period=10):
    return series.diff(period) / (series.shift(period) + 1e-10) * 100

def bollinger_bands(series, period=20, num_std=2):
    mid = sma(series, period)
    std = series.rolling(window=period, min_periods=period).std()
    upper = mid + num_std*std
    lower = mid - num_std*std
    return upper, mid, lower

def atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=period).mean()

def macd(series, fastperiod=12, slowperiod=26, signalperiod=9):
    ema_fast = ema(series, fastperiod)
    ema_slow = ema(series, slowperiod)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signalperiod)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

# -----------------------------
# 1. 基信线特征
# -----------------------------
def calculate_open(df, timeperiod=None):
    return df['open']

def calculate_high(df, timeperiod=None):
    return df['high']

def calculate_low(df, timeperiod=None):
    return df['low']

def calculate_close(df, timeperiod=None):
    return df['close']

def calculate_volume(df, timeperiod=None):
    return df['volume']

# -----------------------------
# 2. 趋势类特征
# -----------------------------
# 移动平均线
def calculate_sma_20(df, timeperiod=20):
    return sma(df['close'], timeperiod)

def calculate_sma_50(df, timeperiod=50):
    return sma(df['close'], timeperiod)

def calculate_sma_60(df, timeperiod=60):
    return sma(df['close'], timeperiod)

def calculate_sma_100(df, timeperiod=100):
    return sma(df['close'], timeperiod)

def calculate_sma_200(df, timeperiod=200):
    return sma(df['close'], timeperiod)

def calculate_ema_20(df, timeperiod=20):
    return ema(df['close'], timeperiod)

def calculate_ema_50(df, timeperiod=50):
    return ema(df['close'], timeperiod)

def calculate_ema_100(df, timeperiod=100):
    return ema(df['close'], timeperiod)

def calculate_ema_200(df, timeperiod=200):
    return ema(df['close'], timeperiod)

# VWMA系列
def calculate_vwma_20(df, timeperiod=20):
    return vwma(df, timeperiod)

def calculate_vwma_50(df, timeperiod=50):
    return vwma(df, timeperiod)

def calculate_vwma_100(df, timeperiod=100):
    return vwma(df, timeperiod)

def calculate_vwma_200(df, timeperiod=200):
    return vwma(df, timeperiod)

def calculate_vwma_20_slope(df, timeperiod=20):
    vwma_series = calculate_vwma_20(df, timeperiod)
    # 简单使用一阶差分估计斜率
    return vwma_series.diff()

def calculate_vwma_50_slope(df, timeperiod=50):
    vwma_series = calculate_vwma_50(df, timeperiod)
    return vwma_series.diff()

def calculate_vwma_sma_divergence(df, timeperiod=20):
    # 计算 vwma 与 sma 的差异，默认周期20
    sma_series = sma(df['close'], timeperiod)
    vwma_series = calculate_vwma_20(df, timeperiod)
    return vwma_series - sma_series

# 趋势方向与强度
def calculate_trend_direction(df, timeperiod=14):
    # 简单判定：如果短期均线上穿长期均线则认为上升趋势，反之下降趋势
    # 使用timeperiod作为短期周期，长期周期为其2.5倍
    short_ema = ema(df['close'], timeperiod)
    long_ema = ema(df['close'], int(timeperiod * 2.5))
    return np.where(short_ema > long_ema, 1, -1)

def calculate_trend_strength_adx(df, timeperiod=14):
    # 使用ATR作为趋势强度的指标（注意：这不是真正的ADX）
    # 如需真正的ADX，需要实现+DI、-DI和DX的计算
    return atr(df, period=timeperiod)

def calculate_trend_consistency_20_60(df, short_period=20, long_period=60):
    # 计算20日和60日均线的方向是否一致
    sma_short = sma(df['close'], short_period)
    sma_long = sma(df['close'], long_period)
    consistency = (sma_short.diff() * sma_long.diff()) > 0
    return consistency.astype(int)

def calculate_trend_continuation_bullish(df, timeperiod=14):
    # 优化逻辑：如果价格上涨天数占比超过70%，认为趋势延续看涨
    returns = df['close'].pct_change()
    bullish_ratio = (returns > 0).rolling(window=timeperiod, min_periods=timeperiod).mean()
    return (bullish_ratio > 0.7).astype(int)

def calculate_trend_continuation_bearish(df, timeperiod=14):
    # 优化逻辑：如果价格下跌天数占比超过70%，认为趋势延续看跌
    returns = df['close'].pct_change()
    bearish_ratio = (returns < 0).rolling(window=timeperiod, min_periods=timeperiod).mean()
    return (bearish_ratio > 0.7).astype(int)

def calculate_trend_exhaustion_signal(df, timeperiod=14):
    # 使用简单的RSI极值判断消耗信号
    rsi_series = rsi(df['close'], period=timeperiod)
    # 当 RSI 超买（>70）或超卖 (<30) 时，认为有某种程度的消耗
    signal = np.where((rsi_series > 70) | (rsi_series < 30), 1, 0)
    return pd.Series(signal, index=df.index)

# -----------------------------
# 3. 能量类特征
# -----------------------------
# RSI系列
def calculate_rsi(df, timeperiod=14):
    return rsi(df['close'], timeperiod)

def calculate_rsi_7(df, timeperiod=7):
    return rsi(df['close'], timeperiod)

def calculate_rsi_3(df, timeperiod=3):
    return rsi(df['close'], timeperiod)

def calculate_rsi_14_3m(df, timeperiod=14):
    # “3m” 可理解为3个时间单位的平滑
    rsi_val = rsi(df['close'], period=14)
    return sma(rsi_val, 3)

def calculate_rsi_14_6m(df, timeperiod=14):
    # “6m” 平滑6期
    rsi_val = rsi(df['close'], period=14)
    return sma(rsi_val, 6)

# 其他能量指标
def calculate_stoch(df, period=14, smoothK=3):
    k, _ = stoch(df, period, smoothK)
    return k

def calculate_stoch_signal(df, period=14, smoothK=3):
    _, d = stoch(df, period, smoothK)
    return d

def calculate_williams_r(df, period=14):
    return williams_r(df, period)

def calculate_cci(df, period=20):
    return cci(df, period)

def calculate_mfi(df, period=14):
    return mfi(df, period)

def calculate_momentum(df, period=10):
    return momentum(df['close'], period)

def calculate_roc(df, period=10):
    return roc(df['close'], period)

# -----------------------------
# 4. 形态类特征
# -----------------------------
# 布林带系列
def calculate_bb_upper(df, timeperiod=20):
    upper, mid, lower = bollinger_bands(df['close'], period=timeperiod)
    return upper

def calculate_bb_middle(df, timeperiod=20):
    upper, mid, lower = bollinger_bands(df['close'], period=timeperiod)
    return mid

def calculate_bb_lower(df, timeperiod=20):
    upper, mid, lower = bollinger_bands(df['close'], period=timeperiod)
    return lower

def calculate_bb_width(df, timeperiod=20):
    upper = calculate_bb_upper(df, timeperiod)
    lower = calculate_bb_lower(df, timeperiod)
    mid = calculate_bb_middle(df, timeperiod)
    return (upper - lower) / (mid + 1e-10)

def calculate_bb_position(df, timeperiod=20):
    # 价格相对于布林带的位置
    lower = calculate_bb_lower(df, timeperiod)
    upper = calculate_bb_upper(df, timeperiod)
    return (df['close'] - lower) / (upper - lower + 1e-10)

def calculate_bb_squeeze(df, timeperiod=20, std_mult=2, threshold=0.05):
    # 判断布林带是否收窄
    bbw = calculate_bb_width(df, timeperiod)
    # 如果当日宽度低于阈值，则认为处于 squeeze 状态
    return (bbw < threshold).astype(int)

def calculate_bb_squeeze_strength(df, timeperiod=20):
    # 可定义为宽度与其均值的比值
    bbw = calculate_bb_width(df, timeperiod)
    return bbw / (sma(bbw, timeperiod) + 1e-10)

# K线形态基本特征
def calculate_body_size(df, timeperiod=None):
    # 实体大小
    return np.abs(df['close'] - df['open'])

def calculate_wick_ratio(df, timeperiod=None):
    # 上下影线比率，增加防护避免除零和极端值
    upper_wick = df['high'] - df[['open','close']].max(axis=1)
    lower_wick = df[['open','close']].min(axis=1) - df['low']
    # 使用np.where避免除以接近0的值，当下影线太小时返回一个上限值
    ratio = np.where(lower_wick > 0.001 * df['close'],
                     upper_wick / lower_wick,
                     np.where(upper_wick > 0, 100, 1))  # 上影线存在但下影线很小时返回100，否则返回1
    return pd.Series(ratio, index=df.index)

def calculate_high_low_range(df, timeperiod=None):
    return df['high'] - df['low']

def calculate_close_open_diff(df, timeperiod=None):
    return df['close'] - df['open']

def calculate_price_reversal(df, timeperiod=5):
    # 简单实现：若收盘价低于过去5日最低或高于过去5日最高，则产生反转信号
    rolling_low = df['low'].rolling(window=timeperiod, min_periods=timeperiod).min().shift(1)
    rolling_high = df['high'].rolling(window=timeperiod, min_periods=timeperiod).max().shift(1)
    signal = np.where( (df['close'] <= rolling_low) | (df['close'] >= rolling_high), 1, 0)
    return pd.Series(signal, index=df.index)

def calculate_key_reversal_candle(df, timeperiod=None):
    # 实现示例：返回一个标志，若当前K线实体与前一日实体符号反转且长度较大，则认为是关键反转
    body = calculate_body_size(df)
    prev_body = body.shift(1)
    reversal = ((df['close'] - df['open']) * (df['open'].shift(1) - df['close'].shift(1)) < 0) & (body > prev_body)
    return reversal.astype(int)

# 以下“石没形态”留作扩展
def calculate_stone_pattern(df, timeperiod=None):
    # 此处未定义明确逻辑，返回全0
    return pd.Series(0, index=df.index)

# -----------------------------
# 5. 成交量类特征
# -----------------------------
def calculate_volume_sma(df, timeperiod=20):
    return sma(df['volume'], timeperiod)

def calculate_volume_ratio(df, timeperiod=20):
    # 当前成交量与均值比
    vol_mean = sma(df['volume'], timeperiod)
    return df['volume'] / (vol_mean + 1e-10)

def calculate_vpt(df, timeperiod=None):
    # Volume Price Trend - 向量化实现
    price_change = df['close'].pct_change().fillna(0)
    vpt = (df['volume'] * price_change).cumsum()
    return vpt

def calculate_volume_contracting(df, timeperiod=20):
    # 若当前成交量低于过去20天均值，认为成交量收缩，返回1，否则0
    vol_mean = calculate_volume_sma(df, timeperiod)
    return (df['volume'] < vol_mean).astype(int)

def calculate_vwap(df, timeperiod=20):
    # VWAP: volume weighted average price (滚动窗口版本)
    pv = (df['close'] * df['volume']).rolling(window=timeperiod, min_periods=timeperiod).sum()
    vol_sum = df['volume'].rolling(window=timeperiod, min_periods=timeperiod).sum()
    return pv / (vol_sum + 1e-10)

def calculate_price_vwap_diff(df, timeperiod=20):
    vwap_series = calculate_vwap(df, timeperiod)
    return df['close'] - vwap_series

def calculate_above_vwap(df, timeperiod=20):
    # 如果收盘价高于 VWAP 返回1，否则0
    vwap_series = calculate_vwap(df, timeperiod)
    return (df['close'] > vwap_series).astype(int)

# -----------------------------
# 6. 波动率类特征
# -----------------------------
def calculate_atr(df, timeperiod=14):
    return atr(df, timeperiod)

def calculate_volatility(df, timeperiod=20):
    # 用每日对数收益率的标准差年化（此处不做年化处理，仅作为短期波动率指标）
    log_ret = np.log(df['close'] / df['close'].shift(1))
    return log_ret.rolling(window=timeperiod, min_periods=timeperiod).std()

def calculate_price_change(df, timeperiod=1):
    return df['close'].diff(timeperiod)

def calculate_price_change_5(df, timeperiod=5):
    return df['close'].diff(5)

def calculate_price_change_10(df, timeperiod=10):
    return df['close'].diff(10)

# -----------------------------
# 7. 支撑压力类特征 (示例实现)
# -----------------------------
def calculate_distance_to_resistance(df, timeperiod=20):
    # 计算过去 timeperiod 天的最高价，与当前收盘价的差距比例
    resistance = df['high'].rolling(window=timeperiod, min_periods=timeperiod).max()
    return (resistance - df['close']) / (df['close'] + 1e-10)

def calculate_is_near_support(df, timeperiod=20, threshold=0.03):
    support = df['low'].rolling(window=timeperiod, min_periods=timeperiod).min()
    return (np.abs(df['close'] - support) / df['close'] < threshold).astype(int)

def calculate_is_near_resistance(df, timeperiod=20, threshold=0.03):
    resistance = df['high'].rolling(window=timeperiod, min_periods=timeperiod).max()
    return (np.abs(resistance - df['close']) / df['close'] < threshold).astype(int)

def calculate_distance_to_1000_level(df, level=1000):
    return np.abs(df['close'] - level)

def calculate_psychological_level_warning(df, level=1000, threshold=0.02):
    # 当价格接近心理价位时发出警告
    return (np.abs(df['close'] - level) / level < threshold).astype(int)

def calculate_resistance_dist_ratio(df, timeperiod=20):
    # 比例 = (Resistance - close) / ATR
    resistance = df['high'].rolling(window=timeperiod, min_periods=timeperiod).max()
    atr_value = calculate_atr(df, timeperiod=14)
    return (resistance - df['close']) / (atr_value + 1e-10)

def calculate_break_resistance(df, timeperiod=20):
    # 如果当天收盘价突破过去timeperiod天最高，则认为突破
    resistance = df['high'].rolling(window=timeperiod, min_periods=timeperiod).max().shift(1)
    return (df['close'] > resistance).astype(int)

def calculate_below_resistance(df, timeperiod=20):
    resistance = df['high'].rolling(window=timeperiod, min_periods=timeperiod).max().shift(1)
    return (df['close'] < resistance).astype(int)

# -----------------------------
# 8. 时间流动性类特征
# -----------------------------
def calculate_is_weekend(df, timeperiod=None):
    # 假设 df.index 为 datetime 类型
    return pd.Series(df.index.weekday >= 5, index=df.index).astype(int)

def calculate_weekend_liquidity_risk(df, timeperiod=None):
    # 例：如果为周末，成交量较小，则流动性风险高
    vol_threshold = df['volume'].rolling(window=5, min_periods=1).mean() * 0.5
    is_weekend = calculate_is_weekend(df)
    risk = (is_weekend & (df['volume'] < vol_threshold)).astype(int)
    return risk

# -----------------------------
# 9. 货波那契类特征
# -----------------------------
def calculate_dist_to_fib_236(df, timeperiod=None):
    # 计算当前价格到 Fib 23.6% 水平的距离：用历史区间的价格范围加权计算
    hi = df['high'].rolling(window=60, min_periods=60).max()
    lo = df['low'].rolling(window=60, min_periods=60).min()
    level = lo + 0.236*(hi - lo)
    return (df['close'] - level) / (df['close'] + 1e-10)

def calculate_dist_to_fib_382(df, timeperiod=None):
    hi = df['high'].rolling(window=60, min_periods=60).max()
    lo = df['low'].rolling(window=60, min_periods=60).min()
    level = lo + 0.382*(hi - lo)
    return (df['close'] - level) / (df['close'] + 1e-10)

def calculate_dist_to_fib_500(df, timeperiod=None):
    hi = df['high'].rolling(window=60, min_periods=60).max()
    lo = df['low'].rolling(window=60, min_periods=60).min()
    level = lo + 0.500*(hi - lo)
    return (df['close'] - level) / (df['close'] + 1e-10)

def calculate_dist_to_fib_618(df, timeperiod=None):
    hi = df['high'].rolling(window=60, min_periods=60).max()
    lo = df['low'].rolling(window=60, min_periods=60).min()
    level = lo + 0.618*(hi - lo)
    return (df['close'] - level) / (df['close'] + 1e-10)

def calculate_dist_to_fib_786(df, timeperiod=None):
    hi = df['high'].rolling(window=60, min_periods=60).max()
    lo = df['low'].rolling(window=60, min_periods=60).min()
    level = lo + 0.786*(hi - lo)
    return (df['close'] - level) / (df['close'] + 1e-10)

def calculate_is_near_fib_236(df, timeperiod=None, threshold=0.02):
    dist = calculate_dist_to_fib_236(df)
    return (np.abs(dist) < threshold).astype(int)

def calculate_is_near_fib_382(df, timeperiod=None, threshold=0.02):
    dist = calculate_dist_to_fib_382(df)
    return (np.abs(dist) < threshold).astype(int)

def calculate_is_near_fib_500(df, timeperiod=None, threshold=0.02):
    dist = calculate_dist_to_fib_500(df)
    return (np.abs(dist) < threshold).astype(int)

def calculate_is_near_fib_618(df, timeperiod=None, threshold=0.02):
    dist = calculate_dist_to_fib_618(df)
    return (np.abs(dist) < threshold).astype(int)

def calculate_is_near_fib_786(df, timeperiod=None, threshold=0.02):
    dist = calculate_dist_to_fib_786(df)
    return (np.abs(dist) < threshold).astype(int)

def calculate_fib_zone(df, timeperiod=None):
    # 返回 fib 区间的编码，例如 0-低位、1-中位、2-高位，直接返回整数避免category类型问题
    pos = calculate_fib_relative_pos(df)
    # 使用np.select避免category类型
    conditions = [pos <= 0.33, (pos > 0.33) & (pos <= 0.66), pos > 0.66]
    choices = [0, 1, 2]
    zone = np.select(conditions, choices, default=1)
    return pd.Series(zone, index=df.index)

def calculate_fib_relative_pos(df, timeperiod=None):
    # 计算当前价格在过去区间内的位置(0~1)
    hi = df['high'].rolling(window=60, min_periods=60).max()
    lo = df['low'].rolling(window=60, min_periods=60).min()
    return (df['close'] - lo) / (hi - lo + 1e-10)

# -----------------------------
# 10. 市场结构类特征
# -----------------------------
def calculate_sideways_score(df, timeperiod=20):
    # 侧向行情得分：价格波动较小得分高。例：价格标准差的倒数
    std = df['close'].rolling(window=timeperiod, min_periods=timeperiod).std()
    return 1 / (std + 1e-10)

# -----------------------------
# 11. 反转信号类特征
# -----------------------------
def calculate_bearish_divergence_rsi(df, timeperiod=14):
    # 改进逻辑：检测价格创新高但RSI未创新高的背离
    rsi_series = calculate_rsi(df, timeperiod)

    # 寻找价格和RSI的局部高点
    price_peak = (df['close'] > df['close'].shift(1)) & (df['close'] > df['close'].shift(-1))
    rsi_peak = (rsi_series > rsi_series.shift(1)) & (rsi_series > rsi_series.shift(-1))

    # 计算滚动窗口内的最高价和最高RSI
    price_high = df['close'].rolling(window=timeperiod, min_periods=timeperiod).max()
    rsi_high = rsi_series.rolling(window=timeperiod, min_periods=timeperiod).max()

    # 当前价格接近历史高点，但RSI远低于历史高点时产生背离信号
    divergence = (df['close'] >= price_high * 0.98) & (rsi_series < rsi_high * 0.95)
    return divergence.astype(int)

def calculate_bullish_divergence_rsi(df, timeperiod=14):
    # 改进逻辑：检测价格创新低但RSI未创新低的背离
    rsi_series = calculate_rsi(df, timeperiod)

    # 计算滚动窗口内的最低价和最低RSI
    price_low = df['close'].rolling(window=timeperiod, min_periods=timeperiod).min()
    rsi_low = rsi_series.rolling(window=timeperiod, min_periods=timeperiod).min()

    # 当前价格接近历史低点，但RSI远高于历史低点时产生背离信号
    divergence = (df['close'] <= price_low * 1.02) & (rsi_series > rsi_low * 1.05)
    return divergence.astype(int)

def calculate_bearish_divergence_macd(df, fastperiod=12, slowperiod=26, signalperiod=9):
    # 改进逻辑：检测价格创新高但MACD未创新高的背离
    macd_line, signal_line, _ = macd(df['close'], fastperiod, slowperiod, signalperiod)

    # 计算滚动窗口内的最高价和最高MACD
    price_high = df['close'].rolling(window=20, min_periods=20).max()
    macd_high = macd_line.rolling(window=20, min_periods=20).max()

    # 当前价格接近历史高点，但MACD远低于历史高点时产生背离信号
    divergence = (df['close'] >= price_high * 0.98) & (macd_line < macd_high * 0.95)
    return divergence.astype(int)

def calculate_bullish_divergence_macd(df, fastperiod=12, slowperiod=26, signalperiod=9):
    # 改进逻辑：检测价格创新低但MACD未创新低的背离
    macd_line, signal_line, _ = macd(df['close'], fastperiod, slowperiod, signalperiod)

    # 计算滚动窗口内的最低价和最低MACD
    price_low = df['close'].rolling(window=20, min_periods=20).min()
    macd_low = macd_line.rolling(window=20, min_periods=20).min()

    # 当前价格接近历史低点，但MACD远高于历史低点时产生背离信号
    divergence = (df['close'] <= price_low * 1.02) & (macd_line > macd_low * 1.05)
    return divergence.astype(int)

def calculate_rsi_overbought_reversal(df, timeperiod=14):
    rsi_series = calculate_rsi(df, timeperiod)
    # 当 RSI 超过80，认为存在回调可能
    return (rsi_series > 80).astype(int)

def calculate_reversal_risk_sell_score(df, timeperiod=14):
    # 结合 RSI 和价格回调风险
    reversal_risk = calculate_rsi_overbought_reversal(df, timeperiod)
    price_drop = df['close'].pct_change().rolling(window=3, min_periods=3).min() < -0.03
    return (reversal_risk & price_drop).astype(int)

def calculate_reversal_risk_buy_score(df, timeperiod=14):
    rsi_series = calculate_rsi(df, timeperiod)
    # RSI 过低，多空风险
    reversal_risk = (rsi_series < 20).astype(int)
    price_increase = df['close'].pct_change().rolling(window=3, min_periods=3).max() > 0.03
    return (reversal_risk & price_increase).astype(int)

# -----------------------------
# 12. 回调信号类特征
# -----------------------------
def calculate_pullback_signal(df, timeperiod=5):
    # 示例：若价格从近期高点回落超过一定百分比，则信号为1
    recent_high = df['high'].rolling(window=timeperiod, min_periods=timeperiod).max().shift(1)
    pullback = (recent_high - df['close']) / (recent_high + 1e-10) > 0.03
    return pullback.astype(int)

# -----------------------------
# 13. 突破信号类特征
# -----------------------------
def calculate_volatility_breakout(df, timeperiod=20):
    # 如果今日收盘价大于过去 timeperiod 的最高或者低于最低, 则认为发生突破
    past_high = df['high'].rolling(window=timeperiod, min_periods=timeperiod).max().shift(1)
    past_low = df['low'].rolling(window=timeperiod, min_periods=timeperiod).min().shift(1)
    breakout = ((df['close'] > past_high) | (df['close'] < past_low)).astype(int)
    return breakout

# -----------------------------
# 14. 苏压信号类特征
# -----------------------------
# 此处bb_squeeze已在布林带处实现，仅补充一个别名
def calculate_bb_squeeze_signal(df, timeperiod=20, threshold=0.05):
    return calculate_bb_squeeze(df, timeperiod, threshold=threshold)

# -----------------------------
# 15. 极端信号类特征
# -----------------------------
def calculate_volume_climax_buy(df, timeperiod=20):
    # 当成交量远大于均值且价格上升，认为买入高潮
    vol_ratio = calculate_volume_ratio(df, timeperiod)
    bullish = (df['close'].pct_change() > 0)
    climax = (vol_ratio > 2) & bullish
    return climax.astype(int)

# -----------------------------
# 16. 早期信号类特征
# -----------------------------
def calculate_early_momentum_sell_score(df, timeperiod=5):
    # 当短期价格趋势由正转负，给出卖信号
    momentum_val = df['close'].diff(timeperiod)
    previous_momentum = momentum_val.shift(1)
    score = ((previous_momentum > 0) & (momentum_val < 0)).astype(int)
    return score

def calculate_early_momentum_buy_score(df, timeperiod=5):
    momentum_val = df['close'].diff(timeperiod)
    previous_momentum = momentum_val.shift(1)
    score = ((previous_momentum < 0) & (momentum_val > 0)).astype(int)
    return score

# -----------------------------
# 17. 价格位置类特征
# -----------------------------
def calculate_price_position(df, timeperiod=20):
    # 价格在区间内的位置，用分位数计算
    rolling_min = df['low'].rolling(window=timeperiod, min_periods=timeperiod).min()
    rolling_max = df['high'].rolling(window=timeperiod, min_periods=timeperiod).max()
    return (df['close'] - rolling_min) / (rolling_max - rolling_min + 1e-10)

def calculate_ema_spread_velocity(df, short_period=20, long_period=50):
    ema_short = ema(df['close'], short_period)
    ema_long = ema(df['close'], long_period)
    spread = ema_short - ema_long
    return spread.diff()

# -----------------------------
# 19. 斐波那契交互
# -----------------------------
def calculate_fib_zone_distance(df, timeperiod=None):
    # 返回 fib_zone 与收盘价的距离，简化计算避免类型转换问题
    fib_zone = calculate_fib_zone(df)
    # fib_zone现在是整数0/1/2，直接使用map映射
    zone_value = fib_zone.map({0: 0.33, 1: 0.5, 2: 0.66})
    return df['close'] - (zone_value * df['close'])

def calculate_is_near_fib_break(df, timeperiod=20, threshold=0.02):
    # 如果价格突破了 fib zone 边界
    fib_pos = calculate_fib_relative_pos(df)
    near_lower = (np.abs(fib_pos - 0.33) < threshold)
    near_upper = (np.abs(fib_pos - 0.66) < threshold)
    return (near_lower | near_upper).astype(int)

def calculate_fib_level_volume(df, timeperiod=20):
    # 体现在斐波那契水平附近的成交量异常（示例逻辑）
    fib_pos = calculate_fib_relative_pos(df)
    vol = df['volume']
    return vol * (1 + np.abs(fib_pos - 0.5))

def calculate_fib_trend_alignment(df, timeperiod=20):
    # 如果 fib 相对位置与整体趋势方向一致，则返回1，否则0（示例）
    fib_rel = calculate_fib_relative_pos(df)
    trend = calculate_trend_direction(df)
    # 简单：价格越高时，认为上升趋势
    alignment = np.where((fib_rel > 0.5) & (trend > 0), 1, np.where((fib_rel <= 0.5) & (trend < 0), 1, 0))
    return pd.Series(alignment, index=df.index)

def calculate_fib_reversal_risk(df, timeperiod=20):
    # 如果价格处在 fib zone 边缘且出现偏离，则反转风险高
    near_break = calculate_is_near_fib_break(df, timeperiod)
    rsi_val = calculate_rsi(df)
    risk = near_break & (rsi_val > 70)
    return risk.astype(int)

# -----------------------------
# 20. 交叉信号类特征
# -----------------------------
def calculate_bb_upper_reversal(df, timeperiod=20):
    # 如果价格从布林上轨回调，即认为出现上轨反转信号
    bb_upper = calculate_bb_upper(df, timeperiod)
    signal = (df['close'].shift(1) >= bb_upper.shift(1)) & (df['close'] < bb_upper.shift(1))
    return signal.astype(int)

def calculate_bb_lower_reversal(df, timeperiod=20):
    bb_lower = calculate_bb_lower(df, timeperiod)
    signal = (df['close'].shift(1) <= bb_lower.shift(1)) & (df['close'] > bb_lower.shift(1))
    return signal.astype(int)

# -----------------------------
# 21. 其他重要特征
# -----------------------------
def calculate_rsi_change(df, timeperiod=1):
    rsi_series = calculate_rsi(df, timeperiod=14)
    return rsi_series.diff(timeperiod)

def calculate_bb_width_ema(df, timeperiod=20, ema_period=10):
    bbw = calculate_bb_width(df, timeperiod)
    return ema(bbw, ema_period)

# -----------------------------
# 22. 差分特征
# -----------------------------
# 价格差分特征
def calculate_price_diff_1(df, timeperiod=None):
    return df['close'].diff(1)

def calculate_price_diff_3(df, timeperiod=None):
    return df['close'].diff(3)

def calculate_price_diff_5(df, timeperiod=None):
    return df['close'].diff(5)

def calculate_price_diff_10(df, timeperiod=None):
    return df['close'].diff(10)

def calculate_price_diff_15(df, timeperiod=None):
    return df['close'].diff(15)

# 成交量差分特征
def calculate_volume_diff_1(df, timeperiod=None):
    return df['volume'].diff(1)

def calculate_volume_diff_3(df, timeperiod=None):
    return df['volume'].diff(3)

def calculate_volume_diff_5(df, timeperiod=None):
    return df['volume'].diff(5)

def calculate_volume_diff_15(df, timeperiod=None):
    return df['volume'].diff(15)

# 技术指标差分特征: RSI
def calculate_rsi_diff_1(df, timeperiod=14):
    return calculate_rsi(df, timeperiod).diff(1)

def calculate_rsi_diff_3(df, timeperiod=14):
    return calculate_rsi(df, timeperiod).diff(3)

def calculate_rsi_diff_5(df, timeperiod=14):
    return calculate_rsi(df, timeperiod).diff(5)

def calculate_rsi_diff_15(df, timeperiod=14):
    return calculate_rsi(df, timeperiod).diff(15)

# 技术指标差分特征: MACD
def calculate_macd_diff_1(df, fastperiod=12, slowperiod=26, signalperiod=9):
    macd_line, _, _ = macd(df['close'], fastperiod, slowperiod, signalperiod)
    return macd_line.diff(1)

def calculate_macd_diff_3(df, fastperiod=12, slowperiod=26, signalperiod=9):
    macd_line, _, _ = macd(df['close'], fastperiod, slowperiod, signalperiod)
    return macd_line.diff(3)

def calculate_macd_diff_5(df, fastperiod=12, slowperiod=26, signalperiod=9):
    macd_line, _, _ = macd(df['close'], fastperiod, slowperiod, signalperiod)
    return macd_line.diff(5)

def calculate_macd_diff_15(df, fastperiod=12, slowperiod=26, signalperiod=9):
    macd_line, _, _ = macd(df['close'], fastperiod, slowperiod, signalperiod)
    return macd_line.diff(15)

# 技术指标差分特征: MACD Hist
def calculate_macd_hist_diff_1(df, fastperiod=12, slowperiod=26, signalperiod=9):
    _, _, hist = macd(df['close'], fastperiod, slowperiod, signalperiod)
    return hist.diff(1)

def calculate_macd_hist_diff_3(df, fastperiod=12, slowperiod=26, signalperiod=9):
    _, _, hist = macd(df['close'], fastperiod, slowperiod, signalperiod)
    return hist.diff(3)

def calculate_macd_hist_diff_5(df, fastperiod=12, slowperiod=26, signalperiod=9):
    _, _, hist = macd(df['close'], fastperiod, slowperiod, signalperiod)
    return hist.diff(5)

def calculate_macd_hist_diff_15(df, fastperiod=12, slowperiod=26, signalperiod=9):
    _, _, hist = macd(df['close'], fastperiod, slowperiod, signalperiod)
    return hist.diff(15)

# 均线差分特征: sma_20
def calculate_sma_20_diff_1(df, timeperiod=20):
    return calculate_sma_20(df, timeperiod).diff(1)

def calculate_sma_20_diff_3(df, timeperiod=20):
    return calculate_sma_20(df, timeperiod).diff(3)

def calculate_sma_20_diff_5(df, timeperiod=20):
    return calculate_sma_20(df, timeperiod).diff(5)

# 均线差分特征: ema_20
def calculate_ema_20_diff_1(df, timeperiod=20):
    return calculate_ema_20(df, timeperiod).diff(1)

def calculate_ema_20_diff_3(df, timeperiod=20):
    return calculate_ema_20(df, timeperiod).diff(3)

def calculate_ema_20_diff_5(df, timeperiod=20):
    return calculate_ema_20(df, timeperiod).diff(5)

def calculate_ema_20_diff_15(df, timeperiod=20):
    return calculate_ema_20(df, timeperiod).diff(15)

# 均线差分特征: vwma_20
def calculate_vwma_20_diff_1(df, timeperiod=20):
    return calculate_vwma_20(df, timeperiod).diff(1)

def calculate_vwma_20_diff_3(df, timeperiod=20):
    return calculate_vwma_20(df, timeperiod).diff(3)

def calculate_vwma_20_diff_5(df, timeperiod=20):
    return calculate_vwma_20(df, timeperiod).diff(5)

def calculate_vwma_20_diff_15(df, timeperiod=20):
    return calculate_vwma_20(df, timeperiod).diff(15)

# 布林带差分特征: bb_upper
def calculate_bb_upper_diff_1(df, timeperiod=20):
    return calculate_bb_upper(df, timeperiod).diff(1)

def calculate_bb_upper_diff_3(df, timeperiod=20):
    return calculate_bb_upper(df, timeperiod).diff(3)

def calculate_bb_upper_diff_5(df, timeperiod=20):
    return calculate_bb_upper(df, timeperiod).diff(5)

def calculate_bb_upper_diff_15(df, timeperiod=20):
    return calculate_bb_upper(df, timeperiod).diff(15)

# 布林带差分特征: bb_lower
def calculate_bb_lower_diff_1(df, timeperiod=20):
    return calculate_bb_lower(df, timeperiod).diff(1)

def calculate_bb_lower_diff_3(df, timeperiod=20):
    return calculate_bb_lower(df, timeperiod).diff(3)

def calculate_bb_lower_diff_5(df, timeperiod=20):
    return calculate_bb_lower(df, timeperiod).diff(5)

def calculate_bb_lower_diff_15(df, timeperiod=20):
    return calculate_bb_lower(df, timeperiod).diff(15)

# 布林带差分特征: bb_width
def calculate_bb_width_diff_1(df, timeperiod=20):
    return calculate_bb_width(df, timeperiod).diff(1)

def calculate_bb_width_diff_3(df, timeperiod=20):
    return calculate_bb_width(df, timeperiod).diff(3)

def calculate_bb_width_diff_5(df, timeperiod=20):
    return calculate_bb_width(df, timeperiod).diff(5)

def calculate_bb_width_diff_15(df, timeperiod=20):
    return calculate_bb_width(df, timeperiod).diff(15)

# ATR差分特征
def calculate_atr_diff_1(df, timeperiod=14):
    return calculate_atr(df, timeperiod).diff(1)

def calculate_atr_diff_3(df, timeperiod=14):
    return calculate_atr(df, timeperiod).diff(3)

def calculate_atr_diff_5(df, timeperiod=14):
    return calculate_atr(df, timeperiod).diff(5)

def calculate_atr_diff_15(df, timeperiod=14):
    return calculate_atr(df, timeperiod).diff(15)

# KDJ差分特征
# 使用随机震荡指标(Stochastic)作为KDJ的K和D值
def calculate_k(df, timeperiod=14):
    # 使用Stochastic %K作为KDJ的K值
    k, _ = stoch(df, period=timeperiod, smoothK=3)
    return k

def calculate_d(df, timeperiod=14):
    # 使用Stochastic %D作为KDJ的D值
    _, d = stoch(df, period=timeperiod, smoothK=3)
    return d

def calculate_k_diff_1(df, timeperiod=14):
    return calculate_k(df, timeperiod).diff(1)

def calculate_k_diff_3(df, timeperiod=14):
    return calculate_k(df, timeperiod).diff(3)

def calculate_k_diff_5(df, timeperiod=14):
    return calculate_k(df, timeperiod).diff(5)

def calculate_d_diff_1(df, timeperiod=14):
    return calculate_d(df, timeperiod).diff(1)

def calculate_d_diff_3(df, timeperiod=14):
    return calculate_d(df, timeperiod).diff(3)

def calculate_d_diff_5(df, timeperiod=14):
    return calculate_d(df, timeperiod).diff(5)

# 价格相对位置差分（以 bb_position 举例）
def calculate_bb_relative_pos(df, timeperiod=20):
    return calculate_bb_position(df, timeperiod)

def calculate_bb_relative_pos_diff_1(df, timeperiod=20):
    return calculate_bb_relative_pos(df, timeperiod).diff(1)

def calculate_bb_relative_pos_diff_3(df, timeperiod=20):
    return calculate_bb_relative_pos(df, timeperiod).diff(3)

def calculate_bb_relative_pos_diff_5(df, timeperiod=20):
    return calculate_bb_relative_pos(df, timeperiod).diff(5)

def calculate_bb_relative_pos_diff_15(df, timeperiod=20):
    return calculate_bb_relative_pos(df, timeperiod).diff(15)

# 波动率差分
def calculate_volatility_diff_1(df, timeperiod=20):
    return calculate_volatility(df, timeperiod).diff(1)

def calculate_volatility_diff_3(df, timeperiod=20):
    return calculate_volatility(df, timeperiod).diff(3)

def calculate_volatility_diff_5(df, timeperiod=20):
    return calculate_volatility(df, timeperiod).diff(5)

def calculate_volatility_diff_15(df, timeperiod=20):
    return calculate_volatility(df, timeperiod).diff(15)


featrues= [
#== 重新组织的特征池
# === 1. 基信线特征 ===
'open', 'high', 'low', 'close', 'volume',
# === 2. 趋势类特征 ==
# 移动平均线
'sma_20','sma_50','sma_60', 'sma_100', 'sma_200',
'ema_20', 'ema_50','ema_100','ema_200',

# VWma_特征
'vwma_20', 'vwma_50', 'vwma_100', 'vwma_200',
'vwma_20_slope', 'vwma_50_slope',
'vwma_sma_divergence',
# 趋势方向
'trend_direction', 'trend_strength_adx', 'trend_consistency_20_60',
'trend_continuation_bullish', 'trend_continuation_bearish',
'trend_exhaustion_signal',
# === 3. 能量类特征 ===
# RSI系列
'rsi', 'rsi_7', 'rsi_3', 'rsi_14_3m', 'rsi_14_6m',
# 其他能量指标
'stoch', 'stoch_signal', 'williams_r', 'cci', 'mfi',
'momentum', 'roc',

# === 4. 形态类特征 ===
# 布林带
'bb_upper', 'bb_lower', 'bb_middle', 'bb_width', 'bb_position',
'bb_squeeze', 'bb_squeeze_strength',
# K线形态
'body_size', 'wick_ratio', 'high_low_range', 'close_open_diff',
'price_reversal', 'key_reversal_candle',
# 石没形态

# === 5. 成交量类特征=#=
'volume_sma', 'volume_ratio', 'vpt', 'volume_contracting',
'vwap', 'price_vwap_diff', 'above_vwap',

# === 6. 波动率类特征 ===
'atr', 'volatility', 'price_change', 'price_change_5', 'price_change_10',
# === 7. 支撑压力类待征 ===
'distance_to_resistance', 'is_near_support', 'is_near_resistance',
'distance_to_1000_level', 'psychological_level_warning',
'resistance_dist_ratio', 'break_resistance', 'below_resistance',
# === 8.时间流动性类特征 ===
'is_weekend', 'weekend_liquidity_risk',
# === 9. 货波那契类符征 ===
'dist_to_fib_236', 'dist_to_fib_382', 'dist_to_fib_500', 'dist_to_fib_618', 'dist_to_fib_786',
'is_near_fib_236', 'is_near_fib_382', 'is_near_fib_500', 'is_near_fib_618', 'is_near_fib_786',
'fib_zone', 'fib_relative_pos',
# === 10. 市场结构类特征 ===
'sideways_score',
# === 11. 反转信号类待征 ===
'bearish_divergence_rsi', 'bullish_divergence_rsi',
'bearish_divergence_macd', 'bullish_divergence_macd',
'rsi_overbought_reversal',
'reversal_risk_sell_score',

'reversal_risk_buy_score',

# === 12. 回调信号类特征 ===
'pullback_signal',
# === 13. 突破信号类特征 ===
'volatility_breakout',
# === 14.苏压信号类特征 ===
# === 15. 极端信号类特征 ===
'volume_climax_buy',
# === 16. 早期信号类特征 ===
'early_momentum_sell_score', 'early_momentum_buy_score',
# === 17. 价格位置类特征 ===
'price_position', 'ema_spread_velocity',

# ====19.斐波那契交互===
'fib_zone_distance', 'is_near_fib_break', 'fib_level_volume',
'fib_trend_alignment', 'fib_reversal_risk',

# === 20. 交叉信号类特征 ===
'bb_upper_reversal', 'bb_lower_reversal',

# === 21. 其他重要特征 ===
'rsi_change', 'bb_width_ema',

# === 22. 差分特征===
# 价格差分特征
'price_diff_1', 'price_diff_3', 'price_diff_5', 'price_diff_10','price_diff_15',
# 成交量差外特征
'volume_diff_1', 'volume_diff_3', 'volume_diff_5', 'volume_diff_15',
# 技术指标差分特征
'rsi_diff_1', 'rsi_diff_3', 'rsi_diff_5','rsi_diff_15',
'macd_diff_1', 'macd_diff_3', 'macd_diff_5', 'macd_diff_15',
'macd_hist_diff_1', 'macd_hist_diff_3', 'macd_hist_diff_5', 'macd_hist_diff_15',

# 均线差分行征
'sma_20_diff_1', 'sma_20_diff_3', 'sma_20_diff_5',
'ema_20_diff_1', 'ema_20_diff_3', 'ema_20_diff_5', 'ema_20_diff_15',
'vwma_20_diff_1', 'vwma_20_diff_3', 'vwma_20_diff_5', 'vwma_20_diff_15',
# 布林带差分特征
'bb_upper_diff_1', 'bb_upper_diff_3', 'bb_upper_diff_5', 'bb_upper_diff_15',
'bb_lower_diff_1', 'bb_lower_diff_3', 'bb_lower_diff_5','bb_lower_diff_15',
'bb_width_diff_1', 'bb_width_diff_3', 'bb_width_diff_5', 'bb_width_diff_15',
# ATR差分特征
'atr_diff_1', 'atr_diff_3', 'atr_diff_5','atr_diff_15',
# KDJ差分特征
'k_diff_1', 'k_diff_3', 'k_diff_5',
'd_diff_1', 'd_diff_3', 'd_diff_5',
# 价格相对位置差分
'bb_relative_pos_diff_1', 'bb_relative_pos_diff_3', 'bb_relative_pos_diff_5', 'bb_relative_pos_diff_15',
# 波动率差分
'volatility_diff_1', 'volatility_diff_3', 'volatility_diff_5', 'volatility_diff_15']