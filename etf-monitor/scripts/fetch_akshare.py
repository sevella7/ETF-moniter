"""
使用AkShare获取ETF数据
数据来源: AkShare (东方财富)
"""

import akshare as ak
import pandas as pd
from typing import List, Dict, Any
import warnings
import time
warnings.filterwarnings("ignore")


def fetch_akshare_etf_sse(date: str = None) -> List[Dict[str, Any]]:
    """
    使用AkShare获取上交所ETF规模数据

    Args:
        date: 日期，格式YYYYMMDD，默认为最新

    Returns:
        List of dicts with keys: code, name, total_amount (亿元)
    """
    try:
        # 不传date参数，让AkShare内部处理默认日期
        if date:
            df = ak.fund_etf_scale_sse(date=date)
        else:
            df = ak.fund_etf_scale_sse()

        # 检查返回数据是否有效
        if df is None or (hasattr(df, 'empty') and df.empty):
            print("AkShare上交所ETF返回空数据")
            return []

        etfs = []

        for _, row in df.iterrows():
            code = str(row.get("基金代码", "")).strip()
            name = str(row.get("基金简称", "")).strip()
            # 基金份额转换为亿份
            shares = float(row.get("基金份额", 0) or 0)
            total_amount = shares / 10000  # 转换为亿份

            if code and name:
                etfs.append({
                    "code": code,
                    "name": name,
                    "total_amount": round(total_amount, 4)
                })

        print(f"AkShare上交所ETF数据获取完成，共 {len(etfs)} 只")
        return etfs
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"AkShare获取上交所ETF失败: {e}")
        return []


def fetch_akshare_etf_szse() -> List[Dict[str, Any]]:
    """
    使用AkShare获取深交所ETF规模数据

    Returns:
        List of dicts with keys: code, name, total_amount (亿元)
    """
    try:
        df = ak.fund_etf_scale_szse()
        etfs = []

        for _, row in df.iterrows():
            code = str(row.get("基金代码", "")).strip()
            name = str(row.get("基金简称", "")).strip()
            # 基金份额转换为亿份
            shares = float(row.get("基金份额", 0) or 0)
            total_amount = shares / 10000  # 转换为亿份

            if code and name:
                etfs.append({
                    "code": code,
                    "name": name,
                    "total_amount": round(total_amount, 4)
                })

        print(f"AkShare深交所ETF数据获取完成，共 {len(etfs)} 只")
        return etfs
    except Exception as e:
        print(f"AkShare获取深交所ETF失败: {e}")
        return []


def fetch_akshare_etf_spot() -> List[Dict[str, Any]]:
    """
    使用AkShare获取东方财富ETF实时数据（包含规模）
    这是更全面的实时数据源

    Returns:
        List of dicts with keys: code, name, total_amount (亿元)
    """
    try:
        df = ak.fund_etf_spot_em()
        etfs = []

        for _, row in df.iterrows():
            code = str(row.get("代码", "")).strip()
            name = str(row.get("名称", "")).strip()
            # 规模字段：可能有不同的列名
            total = (
                row.get("规模", 0) or
                row.get("基金规模", 0) or
                row.get("总规模", 0) or
                0
            )

            try:
                total_amount = float(total) if total else 0
            except:
                total_amount = 0

            if code and name:
                etfs.append({
                    "code": code,
                    "name": name,
                    "total_amount": round(total_amount, 4)
                })

        print(f"AkShare ETF实时数据获取完成，共 {len(etfs)} 只")
        return etfs
    except Exception as e:
        print(f"AkShare获取ETF实时数据失败: {e}")
        return []


def fetch_all_akshare_etf(date: str = None) -> tuple:
    """
    获取全部AkShare ETF数据（上交所 + 深交所）

    Args:
        date: 日期，格式YYYYMMDD

    Returns:
        (sse_etfs, szse_etfs)
    """
    sse_etfs = fetch_akshare_etf_sse(date)
    time.sleep(0.5)  # 避免请求过快
    szse_etfs = fetch_akshare_etf_szse()

    return sse_etfs, szse_etfs


if __name__ == "__main__":
    import json
    print("=== 测试上交所ETF ===")
    data = fetch_akshare_etf_sse()
    print(json.dumps(data[:3], ensure_ascii=False, indent=2))

    print("\n=== 测试深交所ETF ===")
    data = fetch_akshare_etf_szse()
    print(json.dumps(data[:3], ensure_ascii=False, indent=2))
