"""
爬虫适配器
适配 crawler/mobile_phone_spare_parts_crawler.py 脚本
"""
import os
import sys
import json
import requests
import pandas as pd
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable


class CrawlerAdapter:
    """
    爬虫适配器
    将现有的爬虫脚本集成到调度服务中
    """
    
    def __init__(
        self,
        script_code: Optional[str] = None,
        hs_codes: str = "851762,851770",
        periods: str = "2022,2023,2024",
        partners: Optional[str] = None
    ):
        self.script_code = script_code
        # 处理 None 值，使用默认值
        hs_codes = hs_codes or "851762,851770"
        periods = periods or "2022,2023,2024"
        self.hs_codes = [code.strip() for code in hs_codes.split(",")]
        self.periods = [p.strip() for p in periods.split(",")]
        
        # 解析贸易伙伴配置
        self.partners = {
            "0": "全球",
            "840": "美国",
            "356": "印度",
            "704": "越南",
            "410": "韩国",
            "392": "日本",
            "276": "德国",
            "826": "英国",
            "76": "巴西",
            "643": "俄罗斯",
        }
        if partners:
            try:
                self.partners = json.loads(partners)
            except:
                pass
        
        # API配置
        self.api_url = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
        self.china_code = "156"
        self.request_delay = 2
        
        # HS编码描述
        self.hs_descriptions = {
            "851762": "手机/通信终端设备",
            "851770": "电话机零件（含手机配件、排线、接口等）",
        }
        
        # 请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
        }
    
    def build_params(self, hs_code: str, period: str, partner: str = "0") -> Dict:
        """构建请求参数"""
        return {
            "flowCode": "X",
            "reporterCode": self.china_code,
            "period": period,
            "partnerCode": partner,
            "cmdCode": hs_code,
        }
    
    def fetch_data(
        self,
        hs_code: str,
        period: str,
        partner: str = "0",
        max_retries: int = 3,
        log_callback: Optional[Callable] = None
    ) -> Optional[Dict]:
        """获取单条数据"""
        params = self.build_params(hs_code, period, partner)
        partner_name = self.partners.get(partner, "未知")
        
        for attempt in range(max_retries):
            try:
                msg = f"获取数据: HS={hs_code}, 年份={period}, 伙伴={partner_name}"
                if log_callback:
                    log_callback(msg)
                
                response = requests.get(
                    self.api_url,
                    params=params,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 429:
                    wait_time = (attempt + 1) * 5
                    if log_callback:
                        log_callback(f"请求过于频繁，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                content_type = (response.headers.get("Content-Type") or "").lower()
                body = response.text.strip()
                
                if "json" not in content_type and not body.startswith("{"):
                    if log_callback:
                        log_callback(f"接口返回非JSON内容: {body[:120]}")
                    return None
                
                data = response.json()
                
                if data.get("error"):
                    if log_callback:
                        log_callback(f"接口错误: {data['error']}")
                    return None
                
                records = data.get("data") or []
                if records:
                    return records[0]
                
                if log_callback:
                    log_callback(f"{hs_code} {period} 无数据")
                return None
                
            except requests.exceptions.Timeout:
                if log_callback:
                    log_callback(f"请求超时，重试 {attempt + 1}/{max_retries}")
                time.sleep(2)
            except requests.exceptions.RequestException as e:
                if log_callback:
                    log_callback(f"请求失败: {str(e)[:80]}")
                time.sleep(2)
            except Exception as e:
                if log_callback:
                    log_callback(f"错误: {str(e)}")
                time.sleep(2)
        
        return None
    
    def process_record(
        self,
        record: Dict,
        hs_code: str,
        period: str,
        partner_name: str
    ) -> Optional[Dict]:
        """处理单条记录"""
        if not record:
            return None
        
        try:
            export_value = record.get("primaryValue", 0) or 0
            export_qty = record.get("qty", 0) or 0
            
            # 计算单价
            if export_qty and export_qty != 0:
                unit_value = round(export_value / export_qty, 4)
            else:
                unit_value = 0
            
            return {
                "year": int(period[:4]),
                "hs_code": hs_code,
                "hs_description": self.hs_descriptions.get(hs_code, ""),
                "trade_partner": partner_name,
                "export_quantity": float(export_qty) if export_qty else None,
                "quantity_unit": record.get("qtyUnitAbbr", ""),
                "export_value_usd": float(export_value),
                "unit_value_usd": float(unit_value),
                "trade_mode": record.get("customsDesc", ""),
                "data_source": "UN Comtrade",
                "crawled_at": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"数据处理错误: {str(e)}")
            return None
    
    def run(self, log_callback: Optional[Callable] = None) -> List[Dict]:
        """
        运行爬虫
        
        Returns:
            List[Dict]: 处理后的数据记录列表
        """
        if log_callback:
            log_callback("=" * 60)
            log_callback("开始执行 UN Comtrade 爬虫")
            log_callback("=" * 60)
        
        results = []
        
        for hs_code in self.hs_codes:
            if log_callback:
                log_callback(f"\n处理 HS编码: {hs_code}")
            
            for period in self.periods:
                # 获取全球数据
                record = self.fetch_data(hs_code, period, "0", log_callback=log_callback)
                if record:
                    processed = self.process_record(record, hs_code, period, "全球")
                    if processed:
                        results.append(processed)
                        if log_callback:
                            log_callback(f"获取全球数据成功: {processed['export_value_usd']:,.0f} 美元")
                
                time.sleep(self.request_delay)
                
                # 获取主要贸易伙伴数据
                for partner_code, partner_name in self.partners.items():
                    if partner_code == "0":
                        continue
                    
                    record = self.fetch_data(
                        hs_code, period, partner_code,
                        log_callback=log_callback
                    )
                    if record:
                        processed = self.process_record(
                            record, hs_code, period, partner_name
                        )
                        if processed:
                            results.append(processed)
                            if log_callback:
                                log_callback(f"获取 {partner_name} 数据成功")
                    
                    time.sleep(self.request_delay)
        
        if log_callback:
            log_callback(f"\n爬虫执行完成，共获取 {len(results)} 条记录")
        
        return results
