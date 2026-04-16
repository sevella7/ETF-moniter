#!/usr/bin/env python3
"""
ETF规模监控主入口脚本

用法:
    python scripts/run_monitor.py                    # 监控今日
    python scripts/run_monitor.py --date 2026-04-05  # 指定日期
    python scripts/run_monitor.py --dry-run          # 仅获取数据，不发送通知
"""

import argparse
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fetch_tushare import fetch_all_tushare_etf
from scripts.storage import save_etf_data, load_etf_data
from scripts.comparator import run_comparison, format_alert_message
from scripts.notifier import send_alert


def get_date_str(date_arg: str = None) -> str:
    """获取日期字符串"""
    if date_arg:
        return date_arg
    return datetime.now().strftime("%Y-%m-%d")


def fetch_all_etf_data(date_str: str = None) -> tuple:
    """
    获取全部ETF数据

    Returns:
        (sse_etfs, szse_etfs)
    """
    print("=" * 50)
    print("开始获取ETF数据...")
    print("=" * 50)

    # 获取上交所数据
    print("\n[1/4] 获取上交所ETF数据...")
    sse_etfs, szse_etfs = fetch_all_tushare_etf()

    print(f"\n数据获取完成: 上交所{len(sse_etfs)}只, 深交所{len(szse_etfs)}只")

    return sse_etfs, szse_etfs


def main():
    parser = argparse.ArgumentParser(description="ETF规模监控")
    parser.add_argument("--date", type=str, default=None, help="指定日期 YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="仅获取数据，不发送通知")
    parser.add_argument("--no-cleanup", action="store_true", help="不清理旧数据")
    args = parser.parse_args()

    date_str = get_date_str(args.date)

    print(f"\n{'=' * 50}")
    print(f"ETF规模监控 - {date_str}")
    print(f"{'=' * 50}\n")

    # 获取数据
    sse_etfs, szse_etfs = fetch_all_etf_data(date_str)  

    if not sse_etfs and not szse_etfs:
        print("错误: 未能获取任何ETF数据")
        sys.exit(1)

    # 保存当日数据
    print("\n[3/4] 保存ETF数据...")
    save_etf_data(date_str, sse_etfs, szse_etfs)

    # 比较与告警
    print("\n[4/4] 分析规模变动...")
    alerts, summary = run_comparison(date_str, sse_etfs, szse_etfs)

    # 发送通知
    if not args.dry_run:
        print("\n发送飞书通知...")
        success = send_alert(date_str, alerts, summary)
        if success:
            print("通知发送完成!")
        else:
            print("通知发送失败，请检查配置")
    else:
        print("\n[DryRun] 跳过通知发送")

    # 清理旧数据
    if not args.no_cleanup:
        from scripts.storage import cleanup_old_data
        print("\n清理旧数据...")
        cleanup_old_data(30)

    print("\n" + "=" * 50)
    print("监控完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
