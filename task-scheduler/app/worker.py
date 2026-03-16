"""
Celery Worker 配置
"""
import os
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
import redis

# 从环境变量获取配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 创建Celery应用
app = Celery(
    "crawler_scheduler",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]
)

# Celery配置
app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区配置
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务结果过期时间
    result_expires=3600 * 24,  # 24小时
    
    # 任务路由
    task_routes={
        "app.tasks.run_crawler": {"queue": "crawler"},
        "app.tasks.process_crawler_result": {"queue": "default"},
    },
    
    # 任务默认配置
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    
    # Worker配置
    worker_prefetch_multiplier=1,  # 每次只获取一个任务
    worker_max_tasks_per_child=50,  # 每个worker处理50个任务后重启
    
    # Beat调度器配置
    beat_schedule_filename="/tmp/celerybeat-schedule",
    beat_scheduler="celery.beat.PersistentScheduler",
    
    # 定时任务调度
    beat_schedule={
        "poll-crawler-queue": {
            "task": "app.tasks.poll_redis_queue",
            "schedule": 5.0,  # 每5秒轮询一次
        },
    },
)

# Redis客户端（用于队列监听）
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **extras):
    """任务开始前的处理"""
    print(f"[Task {task_id}] 开始执行: {task.name}")


@task_postrun.connect
def task_postrun_handler(task_id, task, args, kwargs, retval, state, **extras):
    """任务完成后的处理"""
    print(f"[Task {task_id}] 执行完成: {task.name}, 状态: {state}")


@task_failure.connect
def task_failure_handler(task_id, exception, args, kwargs, traceback, einfo, **extras):
    """任务失败处理"""
    print(f"[Task {task_id}] 执行失败: {exception}")


if __name__ == "__main__":
    app.start()
