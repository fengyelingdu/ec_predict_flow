from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "event_contract_workflow",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.data_download",
        "app.tasks.feature_calculation",
        "app.tasks.label_calculation",
        "app.tasks.model_training",
        "app.tasks.model_interpretation",
        "app.tasks.model_analysis",
        "app.tasks.backtest_construction",
        "app.tasks.backtest_execution",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    # 改进的异常处理配置
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # 结果过期时间（秒）
    result_expires=3600,
    # 任务结果扩展配置
    result_extended=True,
    # 任务失败不退出 worker
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    # worker 在任务失败后继续运行
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    # 任务失败后不传播异常到 worker
    task_eager_propagates=False,
    # 关键配置：任务失败后不重启 worker pool
    worker_pool_restarts=True,
    # 任务失败后的重试配置
    task_autoretry_for=(Exception,),
    task_retry_kwargs={'max_retries': 0},  # 不自动重试，让任务直接失败
    # 确保任务异常不会导致 worker 崩溃
    task_default_retry_delay=0,
)
