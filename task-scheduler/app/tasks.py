"""
Celery 任务定义
"""
import os
import json
import time
import traceback
from datetime import datetime
from typing import Dict, Any

from app.worker import app, redis_client
from app.crawler_adapter import CrawlerAdapter

# 从 data-layer 导入
from data_layer import get_db as get_db_session, CrawlerTask, TradeData
from data_layer.database import DatabaseSession
from sqlalchemy import text

# 数据库连接配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/phone_parts_db")
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")


@app.task(bind=True, max_retries=3)
def run_crawler(self, task_id: int, script_id: int, script_name: str, 
                script_code: str, **kwargs):
    """
    执行爬虫任务
    """
    start_time = time.time()
    logs = []
    
    def log(message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        logs.append(log_entry)
        print(log_entry)
    
    try:
        log(f"开始执行爬虫任务: {script_name}")
        
        # 使用上下文管理器
        with DatabaseSession() as session:
            session.execute(text("""
                UPDATE crawler_tasks 
                SET status = 'running', started_at = NOW()
                WHERE id = :task_id
            """), {"task_id": task_id})
        
        # 创建爬虫适配器并执行
        adapter = CrawlerAdapter(
            script_code=script_code,
            hs_codes=kwargs.get("hs_codes") or "851762,851770",
            periods=kwargs.get("periods") or "2022,2023,2024",
            partners=kwargs.get("partners")
        )
        
        log("初始化爬虫...")
        results = adapter.run(log_callback=log)
        
        log(f"爬虫执行完成，获取 {len(results)} 条记录")
        
        new_count = 0
        updated_count = 0
        
        with DatabaseSession() as session:
            for record in results:
                try:
                    existing = session.execute(text("""
                        SELECT id FROM trade_data 
                        WHERE year = :year AND hs_code = :hs_code AND trade_partner = :partner
                    """), {
                        "year": record["year"],
                        "hs_code": record["hs_code"],
                        "partner": record["trade_partner"]
                    }).fetchone()
                    
                    if existing:
                        session.execute(text("""
                            UPDATE trade_data SET
                                hs_description = :hs_description,
                                export_quantity = :export_quantity,
                                quantity_unit = :quantity_unit,
                                export_value_usd = :export_value_usd,
                                unit_value_usd = :unit_value_usd,
                                trade_mode = :trade_mode,
                                data_source = :data_source,
                                crawled_at = :crawled_at,
                                updated_at = NOW()
                            WHERE id = :id
                        """), {**record, "id": existing[0]})
                        updated_count += 1
                    else:
                        session.execute(text("""
                            INSERT INTO trade_data (
                                year, hs_code, hs_description, trade_partner,
                                export_quantity, quantity_unit, export_value_usd,
                                unit_value_usd, trade_mode, data_source, status,
                                crawled_at, created_at
                            ) VALUES (
                                :year, :hs_code, :hs_description, :trade_partner,
                                :export_quantity, :quantity_unit, :export_value_usd,
                                :unit_value_usd, :trade_mode, :data_source, 'confirmed',
                                :crawled_at, NOW()
                            )
                        """), record)
                        new_count += 1
                    
                except Exception as e:
                    log(f"保存记录失败: {str(e)}")
        
        duration = round(time.time() - start_time, 2)
        
        with DatabaseSession() as session:
            session.execute(text("""
                UPDATE crawler_tasks SET
                    status = 'success',
                    completed_at = NOW(),
                    duration_seconds = :duration,
                    total_records = :total,
                    new_records = :new_count,
                    updated_records = :updated_count,
                    logs = :logs
                WHERE id = :task_id
            """), {
                "task_id": task_id,
                "duration": duration,
                "total": len(results),
                "new_count": new_count,
                "updated_count": updated_count,
                "logs": "\n".join(logs)
            })
        
        log(f"任务完成，耗时 {duration} 秒")
        
        return {
            "task_id": task_id,
            "status": "success",
            "total_records": len(results),
            "new_records": new_count,
            "updated_records": updated_count,
            "duration": duration
        }
        
    except Exception as exc:
        error_msg = str(exc)
        error_trace = traceback.format_exc()
        log(f"任务执行失败: {error_msg}")
        log(f"错误堆栈: {error_trace}")
        
        try:
            with DatabaseSession() as session:
                session.execute(text("""
                    UPDATE crawler_tasks SET
                        status = 'failed',
                        completed_at = NOW(),
                        error_message = :error,
                        logs = :logs
                    WHERE id = :task_id
                """), {
                    "task_id": task_id,
                    "error": error_msg[:1000],
                    "logs": "\n".join(logs)
                })
        except Exception as e:
            print(f"更新失败状态失败: {str(e)}")
        
        raise self.retry(exc=exc, countdown=60)


@app.task
def process_crawler_result(task_id: int, result: Dict[str, Any]):
    """处理爬虫结果"""
    print(f"处理爬虫结果: task_id={task_id}, result={result}")
    return result


@app.task
def poll_redis_queue():
    """轮询Redis队列中的任务"""
    try:
        print("开始轮询队列...")
        task_data = redis_client.brpop("crawler_tasks", timeout=5)
        print(f"从队列获取数据: {task_data}")
        
        if task_data and len(task_data) == 2:
            _, task_json = task_data
            print(f"任务JSON: {task_json}")
            
            if not task_json:
                print("任务数据为空，跳过")
                return
            
            try:
                task_info = json.loads(task_json)
                print(f"解析后的任务信息: {task_info}")
                
                run_crawler.delay(
                    task_id=task_info["task_id"],
                    script_id=task_info["script_id"],
                    script_name=task_info["script_name"],
                    script_code=task_info["script_code"],
                    hs_codes=task_info.get("hs_codes"),
                    periods=task_info.get("periods"),
                    partners=task_info.get("partners"),
                    params=task_info.get("params", {})
                )
                print(f"任务 {task_info['task_id']} 已提交执行")
            except json.JSONDecodeError as je:
                print(f"JSON解析错误: {je}, 原始数据: {repr(task_json)}")
        else:
            print("队列无任务或超时")
            
    except Exception as e:
        print(f"轮询队列失败: {str(e)}")
        import traceback
        traceback.print_exc()
