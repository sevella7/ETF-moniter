"""
获取深交所ETF规模数据
数据来源: https://www.szse.cn/market/fundlist/etf/index.html
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from typing import List, Dict, Any


def fetch_szse_etf_data() -> List[Dict[str, Any]]:
    """
    获取深交所全部ETF的规模数据

    Returns:
        List of dicts with keys: code, name, total_amount (亿元)
    """
    url = "https://www.szse.cn/api/report/ShowReport/data"
    params = {
        "SHOWTYPE": "JSON",
        "CATALOGID": "1351_ss",  # ETF列表
        "TABKEY": "tab1",
        "txtQuery": "",
        "_": int(time.time() * 1000),
    }
    headers = {
        "Referer": "https://www.szse.cn/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    all_etfs = []

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        data = response.json()

        for item in data:
            if isinstance(item, dict) and "data" in item:
                records = item["data"]
                for record in records:
                    # 深交所ETF数据结构
                    code = record.get("code", "") or record.get("证券代码", "")
                    name = record.get("name", "") or record.get("证券简称", "")
                    # 规模字段名可能不同，尝试多个可能的字段
                    amount = (
                        record.get("totalAmount", "") or
                        record.get("规模", "") or
                        record.get("fundManager", "") or
                        "0"
                    )

                    # 清理规模数据
                    try:
                        if isinstance(amount, str):
                            amount = float(amount.replace(",", "").replace("亿元", ""))
                        else:
                            amount = float(amount) if amount else 0
                    except:
                        amount = 0

                    if code and name:
                        all_etfs.append({
                            "code": code,
                            "name": name,
                            "total_amount": amount
                        })

        print(f"深交所ETF数据获取完成，共 {len(all_etfs)} 只")
        return all_etfs

    except Exception as e:
        print(f"获取深交所ETF数据失败: {e}")
        return []


def fetch_szse_etf_from_page() -> List[Dict[str, Any]]:
    """
    从深交所ETF列表页面获取数据（备选方案）
    """
    url = "https://www.szse.cn/market/fundlist/etf/index.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, "lxml")

        etfs = []
        # 尝试找到ETF列表表格
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows[1:]:  # 跳过表头
                cols = row.find_all("td")
                if len(cols) >= 2:
                    code = cols[0].get_text(strip=True)
                    name = cols[1].get_text(strip=True)
                    if code and name and code.isdigit():
                        etfs.append({
                            "code": code,
                            "name": name,
                            "total_amount": 0  # 页面可能不显示规模
                        })

        if etfs:
            print(f"深交所ETF页面数据获取完成，共 {len(etfs)} 只")
        return etfs
    except Exception as e:
        print(f"从深交所页面获取ETF数据失败: {e}")
        return []


if __name__ == "__main__":
    import json
    data = fetch_szse_etf_data()
    print(json.dumps(data[:5], ensure_ascii=False, indent=2))
