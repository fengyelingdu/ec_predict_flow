from app.core.celery_app import celery_app
from celery import Task


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery_app.task(bind=True, base=CallbackTask)
def run_backtest(self, strategy_config: dict, data_file: str):
    self.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Loading data...'})

    # TODO: 实现回测执行逻辑
    # 参考backtest_ECTI_martin_vercor.py中的回测流程

    self.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'Backtest completed'})

    return {
        "status": "success",
        "results": {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "total_trades": 0
        },
        "report_file": "../data/processed/backtest_report.html",
        "message": "Backtest completed successfully"
    }
