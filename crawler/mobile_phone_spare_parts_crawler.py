#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手机维修配件外贸出货数据爬虫
功能：从UN Comtrade获取中国出口手机维修配件的年度数据
HS编码：851762（手机/通信设备）、851770（手机零件）
作者：Matrix Agent
"""

import requests
import pandas as pd
import time
import os
from datetime import datetime

# ==================== 配置参数 ====================
class Config:
    """爬虫配置参数"""
    
    # UN Comtrade 公开预览 API 地址（A=年度数据，比月度数据可用性更高）
    API_URL = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
    
    # 手机维修配件相关HS编码（HS2017+修订后的有效编码）
    HS_CODES = {
        "851762": "手机/通信终端设备",
        "851770": "电话机零件（含手机配件、排线、接口等）",
    }
    
    # 中国 Reporter Code (UN Comtrade中使用)
    CHINA_CODE = "156"
    
    # 查询年份列表（UN Comtrade月度数据延迟6-12个月，用年度数据更可靠）
    PERIODS = ["2022", "2023", "2024"]
    
    # 主要贸易伙伴（进口国）
    PARTNERS = {
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
    
    # 请求头
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }
    
    # 请求间隔（秒）
    REQUEST_DELAY = 2
    
    # 输出目录
    OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_FILE = os.path.join(OUTPUT_DIR, "手机维修配件外贸出货数据.csv")


class UNComtradeCrawler:
    """UN Comtrade数据爬虫类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(Config.HEADERS)
        self.results = []
        
    def build_request_params(self, hs_code, period, partner="0"):
        """
        构建API请求参数
        
        Args:
            hs_code: HS编码
            period: 时间周期（如202501）
            partner: 贸易伙伴代码，0表示全球
            
        Returns:
            dict: 请求参数字典
        """
        return {
            "flowCode": "X",
            "reporterCode": Config.CHINA_CODE,
            "period": period,
            "partnerCode": partner,
            "cmdCode": hs_code,
        }
    
    def fetch_data(self, hs_code, period, partner="0", max_retries=3):
        """
        获取单条数据
        
        Args:
            hs_code: HS编码
            period: 时间周期
            partner: 贸易伙伴代码
            max_retries: 最大重试次数
            
        Returns:
            dict or None: 返回数据或None
        """
        params = self.build_request_params(hs_code, period, partner)
        
        for attempt in range(max_retries):
            try:
                print(f"  正在获取 {hs_code} - {period} - {partner} ...")
                response = self.session.get(
                    Config.API_URL, 
                    params=params, 
                    timeout=30
                )
                
                if response.status_code == 429:
                    # 请求过于频繁，等待更长时间
                    wait_time = (attempt + 1) * 5
                    print(f"  ⏳ 请求过于频繁，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                else:
                    response.raise_for_status()
                    content_type = (response.headers.get("Content-Type") or "").lower()
                    body = response.text.strip()
                    if "json" not in content_type and not body.startswith("{"):
                        print(f"  ❌ 接口返回非JSON内容: {body[:120].replace(chr(10), ' ')}")
                        return None

                    data = response.json()
                    if data.get("error"):
                        print(f"  ❌ 接口错误: {data['error']}")
                        return None

                    records = data.get("data") or []
                    if records:
                        return records[0]

                    print(f"  ⚠ {hs_code} {period} 无数据")
                    return None
                    
            except requests.exceptions.Timeout:
                print(f"  ⏳ 请求超时，重试 {attempt + 1}/{max_retries}")
                time.sleep(2)
            except requests.exceptions.RequestException as e:
                print(f"  ❌ 请求失败: {str(e)[:80]}")
                time.sleep(2)
            except Exception as e:
                print(f"  ❌ 错误: {str(e)}")
                time.sleep(2)
                
        return None
    
    def process_record(self, record, hs_code, period, partner_name):
        """
        处理单条记录
        
        Args:
            record: API返回的原始记录
            hs_code: HS编码
            period: 时间周期
            partner_name: 贸易伙伴名称
            
        Returns:
            dict: 处理后的数据
        """
        if not record:
            return None
            
        # 提取数据
        try:
            return {
                "年份": period[:4],
                "HS编码": hs_code,
                "HS编码描述": Config.HS_CODES.get(hs_code, ""),
                "贸易伙伴": partner_name,
                "出口数量": record.get("qty", ""),
                "数量单位": record.get("qtyUnitAbbr", ""),
                "出口金额_美元": record.get("primaryValue", 0),
                "单价值_美元": round(record.get("primaryValue", 0) / record.get("qty", 1), 4) if record.get("qty") and record.get("qty") != 0 else 0,
                "贸易方式": record.get("customsDesc", ""),
                "数据来源": "UN Comtrade",
                "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"  ❌ 数据处理错误: {str(e)}")
            return None
    
    def run_crawler(self):
        """
        运行爬虫主程序
        """
        print("=" * 60)
        print("手机维修配件外贸出货数据爬虫")
        print("目标：获取中国手机维修配件出口数据")
        print("=" * 60)
        
        # 创建输出目录
        if not os.path.exists(Config.OUTPUT_DIR):
            os.makedirs(Config.OUTPUT_DIR)
        
        for hs_code in Config.HS_CODES:
            print(f"\n📦 正在处理 HS编码: {hs_code}")
            
            for period in Config.PERIODS:
                # 获取全球数据
                record = self.fetch_data(hs_code, period, "0")
                if record:
                    processed = self.process_record(record, hs_code, period, "全球")
                    if processed:
                        self.results.append(processed)
                        print(f"  ✅ 获取全球数据成功: {processed['出口金额_美元']:,.0f} 美元")
                
                # 延时
                time.sleep(Config.REQUEST_DELAY)
                
                # 获取主要贸易伙伴数据
                for partner_code, partner_name in Config.PARTNERS.items():
                    if partner_code == "0":
                        continue
                        
                    record = self.fetch_data(hs_code, period, partner_code)
                    if record:
                        processed = self.process_record(record, hs_code, period, partner_name)
                        if processed:
                            self.results.append(processed)
                            print(f"  ✅ 获取 {partner_name} 数据成功")
                    
                    time.sleep(Config.REQUEST_DELAY)
        
        # 保存数据
        if self.results:
            self.save_data()
        else:
            print("\n⚠ 未获取到任何数据")
            
        return self.results
    
    def save_data(self):
        """
        保存数据到CSV文件
        """
        try:
            df = pd.DataFrame(self.results)
            
            # 按年份、HS编码排序
            df = df.sort_values(by=["年份", "HS编码", "贸易伙伴"])
            
            # 保存到CSV
            df.to_csv(Config.OUTPUT_FILE, index=False, encoding="utf-8-sig")
            
            print("\n" + "=" * 60)
            print("✅ 数据抓取完成！")
            print(f"📁 数据已保存至: {Config.OUTPUT_FILE}")
            print(f"📊 总记录数: {len(self.results)}")
            print("=" * 60)
            
            # 显示数据摘要
            print("\n📈 数据摘要:")
            print(df.groupby(["HS编码", "贸易伙伴"])["出口金额_美元"].agg(["sum", "count"]))
            
        except Exception as e:
            print(f"\n❌ 数据保存失败: {str(e)}")


def main():
    """
    主函数
    """
    print("\n" + "=" * 60)
    print("       手机维修配件外贸出货数据爬虫 v1.0")
    print("=" * 60)
    print("""
🔧 功能说明：
   1. 从UN Comtrade获取中国手机维修配件出口数据（2022-2024年度）
   2. 支持的HS编码：851762（手机/通信终端）、851770（电话机零件）
   3. 数据包含：出口金额、数量、单价、主要贸易伙伴等

📝 注意：
   - 使用公开预览API，无需订阅密钥
   - 年度数据比月度数据可用性更高
   - 如需更细粒度数据，建议申请API订阅密钥
    """)
    
    crawler = UNComtradeCrawler()
    crawler.run_crawler()

    print("\n" + "=" * 60)
    print("程序执行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
