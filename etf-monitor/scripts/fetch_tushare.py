"""
使用Tushare获取ETF数据
数据来源: Tushare (需要注册获取token)
"""

import os
import pandas as pd
from typing import List, Dict, Any
import warnings
import time
warnings.filterwarnings("ignore")


def get_tushare_api():
    """获取Tushare API实例"""
    import tushare as ts
    token = os.environ.get("TUSHARE_TOKEN", "")
    if token:
        ts.set_token(token)
    return ts.pro_api()


def fetch_tushare_etf_data(date: str = None) -> tuple:
    """
    使用Tushare获取全部ETF数据（上交所 + 深交所）

    Args:
        date: 日期，格式YYYY-MM-DD，默认为最新

    Returns:
        (sse_etfs, szse_etfs)
    """
    pro = get_tushare_api()

    sse_etfs = []
    szse_etfs = []

    try:
        # 获取所有上市ETF基础信息
        df = pro.etf_basic(list_status='L', fields='ts_code,name,exchange,list_date')

        if df is None or df.empty:
            print("Tushare返回空ETF数据")
            return [], []

        # 遍历ETF获取规模数据
        for _, row in df.iterrows():
            ts_code = row['ts_code']
            name = row['name']
            exchange = row['exchange']

            # 根据交易所选择代码前缀
            if exchange == 'SSE':
                code = ts_code.replace('.SH', '')
                sse_etfs.append({
                    "code": code,
                    "name": name,
                    "total_amount": 0  # Tushare免费接口不提供规模数据
                })
            elif exchange == 'SZSE':
                code = ts_code.replace('.SZ', '')
                szse_etfs.append({
                    "code": code,
                    "name": name,
                    "total_amount": 0  # Tushare免费接口不提供规模数据
                })

            time.sleep(0.1)  # 避免请求过快

        print(f"Tushare ETF数据获取完成: 上交所{len(sse_etfs)}只, 深交所{len(szse_etfs)}只")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Tushare获取ETF数据失败: {e}")

    return sse_etfs, szse_etfs


def fetch_all_tushare_etf(date: str = None) -> tuple:
    """
    获取全部Tushare ETF数据（上交所 + 深交所）

    Args:
        date: 日期，格式YYYY-MM-DD

    Returns:
        (sse_etfs, szse_etfs)
    """
    return fetch_tushare_etf_data(date)


if __name__ == "__main__":
    import json
    print("=== 测试Tushare ETF ===")
    sse, szse = fetch_tushare_etf_data()
    print(f"\n上交所ETF: {len(sse)}只")
    print(json.dumps(sse[:3], ensure_ascii=False, indent=2))
    print(f"\n深交所ETF: {len(szse)}只")
    print(json.dumps(szse[:3], ensure_ascii=False, indent=2))