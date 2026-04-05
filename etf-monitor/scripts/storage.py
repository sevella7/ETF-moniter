"""
ETF数据存储模块 - 管理历史数据存储和读取
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


# 数据存储目录
DATA_DIR = Path(__file__).parent.parent / "data" / "etf_history"
REPORT_DIR = Path(__file__).parent.parent / "reports"


def ensure_dirs():
    """确保存储目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def get_history_file_path(date_str: str) -> Path:
    """
    获取指定日期的历史数据文件路径

    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD

    Returns:
        文件路径
    """
    return DATA_DIR / f"{date_str}.json"


def save_etf_data(date_str: str, sse_etfs: List[Dict], szse_etfs: List[Dict]) -> bool:
    """
    保存当日ETF数据到JSON文件

    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD
        sse_etfs: 上交所ETF数据列表
        szse_etfs: 深交所ETF数据列表

    Returns:
        是否保存成功
    """
    ensure_dirs()

    data = {
        "date": date_str,
        "sse_etfs": sse_etfs,
        "szse_etfs": szse_etfs,
        "updated_at": datetime.now().strftime("%H:%M:%S")
    }

    file_path = get_history_file_path(date_str)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存: {file_path}")
        return True
    except Exception as e:
        print(f"保存数据失败: {e}")
        return False


def load_etf_data(date_str: str) -> Optional[Dict[str, Any]]:
    """
    加载指定日期的ETF数据

    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD

    Returns:
        数据字典，如不存在则返回None
    """
    file_path = get_history_file_path(date_str)
    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None


def get_previous_trading_day(date_str: str, days: int = 1) -> Optional[str]:
    """
    获取指定日期之前指定交易日的日期

    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD
        days: 往回多少个交易日

    Returns:
        日期字符串，如不存在历史数据则返回None
    """
    from datetime import datetime, timedelta

    current = datetime.strptime(date_str, "%Y-%m-%d")

    for i in range(1, days + 30):  # 最多尝试30个自然日
        check_date = current - timedelta(days=i)
        check_str = check_date.strftime("%Y-%m-%d")
        if get_history_file_path(check_str).exists():
            if days == 1:
                return check_str
            days -= 1
            if days == 0:
                return check_str

    return None


def load_latest_data() -> Optional[Dict[str, Any]]:
    """
    加载最近一个有数据的交易日数据

    Returns:
        最近一日的数据字典
    """
    ensure_dirs()

    # 尝试从今天开始往前找
    today = datetime.now()
    for i in range(30):  # 最多找30天
        check_date = today - timedelta(days=i)
        check_str = check_date.strftime("%Y-%m-%d")
        data = load_etf_data(check_str)
        if data:
            return data

    return None


def save_report(date_str: str, alerts: List[Dict], summary: Dict) -> bool:
    """
    保存监控报告

    Args:
        date_str: 日期字符串
        alerts: 告警ETF列表
        summary: 汇总信息

    Returns:
        是否保存成功
    """
    ensure_dirs()

    report_dir = REPORT_DIR / date_str
    report_dir.mkdir(parents=True, exist_ok=True)

    # 保存JSON格式
    json_path = report_dir / "etf_alerts.json"
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "date": date_str,
                "alerts": alerts,
                "summary": summary
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存告警JSON失败: {e}")

    # 保存Markdown格式
    md_path = report_dir / "etf_monitor.md"
    try:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# ETF规模监控报告\n\n")
            f.write(f"**日期**: {date_str}\n\n")
            f.write(f"**监控ETF总数**: {summary.get('total_count', 0)}\n\n")
            f.write(f"**告警ETF数量**: {summary.get('alert_count', 0)}\n\n")

            if alerts:
                f.write("## 告警明细\n\n")
                f.write("| 代码 | 名称 | 最新规模(亿元) | 昨日规模(亿元) | 变动比例 |\n")
                f.write("|------|------|---------------|---------------|----------|\n")
                for alert in alerts:
                    f.write(f"| {alert.get('code', '')} | {alert.get('name', '')} | "
                            f"{alert.get('current_amount', 0):.2f} | {alert.get('previous_amount', 0):.2f} | "
                            f"{alert.get('change_pct', 0):+.2f}% |\n")
            else:
                f.write("## 无告警\n\n今日无ETF规模变动超过5%。\n")

    except Exception as e:
        print(f"保存报告Markdown失败: {e}")

    print(f"报告已保存: {report_dir}")
    return True


def cleanup_old_data(days: int = 30):
    """
    清理超过指定天数的旧数据

    Args:
        days: 保留天数
    """
    ensure_dirs()

    cutoff = datetime.now() - timedelta(days=days)
    removed = 0

    for file in DATA_DIR.glob("*.json"):
        try:
            file_date = datetime.strptime(file.stem, "%Y-%m-%d")
            if file_date < cutoff:
                file.unlink()
                removed += 1
        except:
            continue

    print(f"已清理 {removed} 个旧数据文件")


if __name__ == "__main__":
    # 测试
    print(f"数据目录: {DATA_DIR}")
    print(f"报告目录: {REPORT_DIR}")

    # 测试保存
    save_etf_data("2026-04-05", [{"code": "510050", "name": "测试ETF", "total_amount": 100}], [])
    load_etf_data("2026-04-05")
