"""
清理Redis中的Celery数据

运行此脚本可以清除Redis中损坏的Celery任务结果，
解决 "Exception information must include the exception type" 错误
"""
import redis
from app.core.config import settings

def clear_celery_data():
    """清理所有Celery相关的Redis数据"""
    try:
        # 连接到Redis
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)

        print("正在连接到Redis...")
        r.ping()
        print("✓ Redis连接成功")

        # 获取所有Celery相关的key
        celery_keys = []

        # Celery的key通常以这些前缀开始
        patterns = [
            'celery-task-meta-*',  # 任务结果
            '_kombu.*',             # Kombu消息队列
            'unacked*',             # 未确认的消息
        ]

        print("\n正在扫描Celery相关的keys...")
        for pattern in patterns:
            keys = r.keys(pattern)
            celery_keys.extend(keys)
            print(f"  找到 {len(keys)} 个 {pattern} keys")

        if not celery_keys:
            print("\n✓ Redis中没有Celery数据需要清理")
            return

        print(f"\n总共找到 {len(celery_keys)} 个Celery相关的keys")

        # 确认清理
        response = input("\n是否清理这些keys? (yes/no): ")
        if response.lower() != 'yes':
            print("已取消清理")
            return

        # 删除keys
        print("\n正在清理...")
        deleted = 0
        for key in celery_keys:
            try:
                r.delete(key)
                deleted += 1
                if deleted % 10 == 0:
                    print(f"  已清理 {deleted}/{len(celery_keys)} keys...")
            except Exception as e:
                print(f"  删除 {key} 失败: {e}")

        print(f"\n✓ 成功清理 {deleted} 个keys")
        print("\n现在可以重新启动Celery worker了！")

    except redis.ConnectionError:
        print("✗ 无法连接到Redis，请确保Redis服务正在运行")
        print(f"  Redis URL: {settings.REDIS_URL}")
    except Exception as e:
        print(f"✗ 发生错误: {e}")

def clear_specific_task(task_id: str):
    """清理特定任务的结果"""
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        key = f'celery-task-meta-{task_id}'

        if r.exists(key):
            r.delete(key)
            print(f"✓ 已删除任务 {task_id} 的结果")
        else:
            print(f"任务 {task_id} 的结果不存在")
    except Exception as e:
        print(f"✗ 发生错误: {e}")

def show_redis_info():
    """显示Redis信息"""
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.ping()

        print("=== Redis 信息 ===")
        info = r.info()
        print(f"Redis版本: {info.get('redis_version', 'N/A')}")
        print(f"已用内存: {info.get('used_memory_human', 'N/A')}")
        print(f"连接的客户端: {info.get('connected_clients', 'N/A')}")

        # 统计Celery keys
        celery_keys = r.keys('celery-task-meta-*')
        print(f"\nCelery任务结果数: {len(celery_keys)}")

        if celery_keys:
            print("\n最近的任务IDs:")
            for key in celery_keys[:5]:
                task_id = key.replace('celery-task-meta-', '')
                print(f"  - {task_id}")
            if len(celery_keys) > 5:
                print(f"  ... 还有 {len(celery_keys) - 5} 个")

    except redis.ConnectionError:
        print("✗ 无法连接到Redis")
    except Exception as e:
        print(f"✗ 发生错误: {e}")

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Celery Redis 清理工具")
    print("=" * 60)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "info":
            show_redis_info()
        elif command == "clear":
            clear_celery_data()
        elif command == "clear-task" and len(sys.argv) > 2:
            task_id = sys.argv[2]
            clear_specific_task(task_id)
        else:
            print("用法:")
            print("  python clear_redis.py info          - 显示Redis信息")
            print("  python clear_redis.py clear         - 清理所有Celery数据")
            print("  python clear_redis.py clear-task ID - 清理特定任务")
    else:
        print("\n1. 显示Redis信息")
        print("2. 清理所有Celery数据")
        print("3. 清理特定任务")
        print("4. 退出")

        choice = input("\n请选择操作 (1-4): ")

        if choice == "1":
            show_redis_info()
        elif choice == "2":
            clear_celery_data()
        elif choice == "3":
            task_id = input("请输入任务ID: ")
            clear_specific_task(task_id)
        elif choice == "4":
            print("退出")
        else:
            print("无效的选择")
