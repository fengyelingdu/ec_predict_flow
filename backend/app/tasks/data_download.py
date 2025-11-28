from app.core.celery_app import celery_app
from celery import Task
from celery.exceptions import Ignore
from binance.um_futures import UMFutures
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from app.core.config import settings


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery_app.task(bind=True, base=CallbackTask)
def download_kline_data(self, symbol: str, start_date: str, end_date: str, interval: str = "1m", proxy: str = None):
    """
    下载K线数据
    参考 history_kline_downloader.py 的逻辑
    """
    try:
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': '正在初始化...', 'message': '连接到Binance API'})

        # 初始化Binance客户端
        proxies = None
        if proxy:
            proxies = {'https': proxy}
        elif settings.BINANCE_PROXY:
            proxies = {'https': settings.BINANCE_PROXY}

        client = UMFutures(proxies=proxies)

        # 解析日期
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        self.update_state(state='PROGRESS', meta={
            'progress': 5,
            'status': '开始下载数据...',
            'message': f'下载 {symbol} {interval} K线数据'
        })

        # 下载数据
        all_data = []
        limit = 1000
        current_start = start_dt
        start_timestamp = start_dt.timestamp()
        end_timestamp = end_dt.timestamp()
        total_duration = end_timestamp - start_timestamp
        interval_delta = get_interval_delta(interval)

        batch_count = 0

        while current_start < end_dt:
            batch_count += 1
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "startTime": int(current_start.timestamp() * 1000),
                "endTime": int(end_dt.timestamp() * 1000)
            }

            try:
                klines = client.klines(**params)
                time.sleep(0.25)

                self.update_state(state='PROGRESS', meta={
                    'progress': min(95, 10 + (batch_count * 5)),
                    'status': f'正在下载第 {batch_count} 批数据...',
                    'message': f'成功获取 {len(klines)} 条K线数据'
                })

            except Exception as e:
                raise Exception(f"请求Binance API错误: {str(e)}")

            if not klines:
                break

            all_data.extend(klines)

            # 更新下载起始时间
            last_time = int(klines[-1][0]) / 1000
            current_start = datetime.fromtimestamp(last_time) + interval_delta

            # 计算进度
            progress_percent = ((last_time - start_timestamp) / total_duration) * 90
            progress_percent = min(95, 10 + progress_percent)

            current_time_str = datetime.fromtimestamp(last_time).strftime("%Y-%m-%d %H:%M:%S")
            self.update_state(state='PROGRESS', meta={
                'progress': progress_percent,
                'status': f'下载中... 当前: {current_time_str}',
                'message': f'已获取 {len(all_data)} 条数据'
            })

            if len(klines) < limit:
                break

        if not all_data:
            raise Exception("未获取到任何数据")

        self.update_state(state='PROGRESS', meta={
            'progress': 96,
            'status': '正在处理数据...',
            'message': f'共下载 {len(all_data)} 条K线数据'
        })

        # 转换为DataFrame
        df = pd.DataFrame(all_data, columns=[
            'datetime', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
            'taker_buy_quote_volume', 'ignore'
        ])

        # 转换时间戳
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df['datetime'] = df['datetime'].dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')

        # 转换数值类型
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)

        self.update_state(state='PROGRESS', meta={
            'progress': 98,
            'status': '正在保存文件...',
            'message': '保存为pkl格式'
        })

        # 保存文件
        start_datetime = start_dt.strftime("%Y-%m-%d_%H_%M_%S")
        end_datetime = end_dt.strftime("%Y-%m-%d_%H_%M_%S")
        exchange = "BINANCE"
        filename = f"{symbol}_{exchange}_{start_datetime}_{end_datetime}.pkl"
        filepath = os.path.join(settings.RAW_DATA_DIR, filename)

        df.to_pickle(filepath)

        self.update_state(state='PROGRESS', meta={
            'progress': 100,
            'status': '下载完成！',
            'message': f'文件已保存: {filename}'
        })

        return {
            "status": "success",
            "filename": filename,
            "filepath": filepath,
            "total_rows": int(len(df)),  # 转换为Python int
            "start_time": str(df['datetime'].min()),
            "end_time": str(df['datetime'].max()),
            "message": "数据下载成功"
        }

    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()

        print(f"[ERROR] 数据下载任务失败: {error_msg}")
        print(f"[ERROR] 错误堆栈:\n{error_trace}")

        self.update_state(state='FAILURE', meta={
            'status': 'error',
            'message': error_msg,
            'traceback': error_trace
        })

        raise Ignore()


def get_interval_delta(interval: str) -> timedelta:
    """根据周期字符串返回对应的 timedelta 对象"""
    if interval.endswith("m"):
        try:
            minutes = int(interval[:-1])
            return timedelta(minutes=minutes)
        except:
            return timedelta(minutes=1)
    elif interval.endswith("h"):
        try:
            hours = int(interval[:-1])
            return timedelta(hours=hours)
        except:
            return timedelta(hours=1)
    elif interval.endswith("d"):
        try:
            days = int(interval[:-1])
            return timedelta(days=days)
        except:
            return timedelta(days=1)
    elif interval.endswith("w"):
        try:
            weeks = int(interval[:-1])
            return timedelta(weeks=weeks)
        except:
            return timedelta(weeks=1)
    else:
        return timedelta(minutes=1)
