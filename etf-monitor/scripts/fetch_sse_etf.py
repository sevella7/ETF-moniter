"""
获取上交所ETF规模数据
数据来源: https://www.sse.com.cn/market/funddata/volumn/etfvolumn/
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from typing import List, Dict, Any


def fetch_sse_etf_data() -> List[Dict[str, Any]]:
    """
    获取上交所全部ETF的规模数据

    Returns:
        List of dicts with keys: code, name, total_amount (亿元)
    """
    url = "https://query.sse.com.cn/marketdata/MarketDataQuery"
    params = {
        "jsonCallBack": "jsonpCallback",
        "sqlId": "COMMON_SSE_ZQPZ_GP_GPLB_MCJS_SSGSFX_L",
        "isPagination": "true",
        "pageHelp.pageSize": "1000",
        "pageHelp.pageNo": "1",
    }
    headers = {
        "Referer": "https://www.sse.com.cn/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    all_etfs = []
    page = 1

    while True:
        params["pageHelp.pageNo"] = str(page)
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.encoding = "utf-8"

            # 解析JSONP格式
            text = response.text
            # jsonpCallback({...})
            start = text.find("(") + 1
            end = text.rfind(")")
            if start > 0 and end > start:
                data = json.loads(text[start:end])
            else:
                data = json.loads(text)

            records = data.get("result", [])
            if not records:
                break

            for record in records:
                # 过滤ETF类型
                if record.get("PRODUCT_TYPE") != "16":  # 16 = ETF
                    continue

                all_etfs.append({
                    "code": record.get("SECURITIES_CODE", ""),
                    "name": record.get("SECURITIES_NAME", ""),
                    "total_amount": float(record.get("TOTAL_AMOUNT", 0) or 0) / 100000000  # 转换为亿元
                })

            # 检查是否还有下一页
            if len(records) < 1000:
                break
            page += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"获取上交所ETF数据失败 (页{page}): {e}")
            break

    print(f"上交所ETF数据获取完成，共 {len(all_etfs)} 只")
    return all_etfs


def fetch_sse_etf_from_page() -> List[Dict[str, Any]]:
    """
    从上交所ETF列表页面获取数据（备选方案）
    """
    url = "https://www.sse.com.cn/market/funddata/volumn/etfvolumn/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, "lxml")

        etfs = []
        table = soup.find("table", {"class": "etf-table"})
        if table:
            rows = table.find_all("tr")
            for row in rows[1:]:  # 跳过表头
                cols = row.find_all("td")
                if len(cols) >= 3:
                    code = cols[0].get_text(strip=True)
                    name = cols[1].get_text(strip=True)
                    amount = cols[2].get_text(strip=True)
                    try:
                        amount = float(amount.replace(",", "").replace("亿元", ""))
                    except:
                        amount = 0
                    etfs.append({
                        "code": code,
                        "name": name,
                        "total_amount": amount
                    })
        print(f"上交所ETF页面数据获取完成，共 {len(etfs)} 只")
        return etfs
    except Exception as e:
        print(f"从上交所页面获取ETF数据失败: {e}")
        return []


if __name__ == "__main__":
    import json
    data = fetch_sse_etf_data()
    print(json.dumps(data[:5], ensure_ascii=False, indent=2))
