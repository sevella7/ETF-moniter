"""
ETF规模比较与告警判断模块
"""

import os
from typing import List, Dict, Any, Tuple
from storage import load_etf_data, get_previous_trading_day, save_report


# 告警阈值，默认5%
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "5.0"))


def merge_etf_lists(sse_etfs: List[Dict], szse_etfs: List[Dict]) -> Dict[str, Dict]:
    """
    合并上交所和深交所ETF列表，按代码索引

    Args:
        sse_etfs: 上交所ETF列表
        szse_etfs: 深交所ETF列表

    Returns:
        {code: {name, total_amount, source}} 的字典
    """
    merged = {}

    for etf in sse_etfs:
        code = etf.get("code", "")
        if code:
            merged[code] = {
                "code": code,
                "name": etf.get("name", ""),
                "total_amount": etf.get("total_amount", 0),
                "source": "sse"
            }

    for etf in szse_etfs:
        code = etf.get("code", "")
        if code:
            if code in merged:
                # 如果代码已存在但新数据有规模，更新
                if etf.get("total_amount", 0) > 0:
                    merged[code]["total_amount"] = etf.get("total_amount", 0)
            else:
                merged[code] = {
                    "code": code,
                    "name": etf.get("name", ""),
                    "total_amount": etf.get("total_amount", 0),
                    "source": "szse"
                }

    return merged


def calculate_changes(
    current_etfs: Dict[str, Dict],
    previous_etfs: Dict[str, Dict]
) -> List[Dict[str, Any]]:
    """
    计算ETF规模变动，筛选超过阈值的

    Args:
        current_etfs: 今日ETF数据
        previous_etfs: 昨日ETF数据

    Returns:
        变动超过阈值的ETF列表
    """
    alerts = []

    for code, current_info in current_etfs.items():
        current_amount = current_info.get("total_amount", 0)
        if current_amount <= 0:
            continue  # 跳过无效规模数据

        previous_info = previous_etfs.get(code, {})
        previous_amount = previous_info.get("total_amount", 0)

        if previous_amount <= 0:
            continue  # 跳过昨日无数据的

        # 计算变动比例
        change_pct = (current_amount - previous_amount) / previous_amount * 100

        # 判断是否触发告警
        if abs(change_pct) > ALERT_THRESHOLD:
            alerts.append({
                "code": code,
                "name": current_info.get("name", ""),
                "current_amount": current_amount,
                "previous_amount": previous_amount,
                "change_pct": round(change_pct, 2),
                "change_amount": round(current_amount - previous_amount, 2)
            })

    # 按变动比例绝对值排序
    alerts.sort(key=lambda x: abs(x["change_pct"]), reverse=True)

    return alerts


def format_alert_message(date_str: str, alerts: List[Dict], total_count: int) -> str:
    """
    格式化告警消息为飞书消息

    Args:
        date_str: 日期字符串
        alerts: 告警ETF列表
        total_count: 监控ETF总数

    Returns:
        格式化后的消息文本
    """
    if not alerts:
        message = f"""📊 ETF规模监控报告 ({date_str})

✅ 今日无ETF规模异动

共计监控 **{total_count}** 只ETF，规模变动均未超过 {ALERT_THRESHOLD}%
"""
        return message

    # 分类：增幅>5% 和 降幅>5%
    increase_alerts = [a for a in alerts if a["change_pct"] > 0]
    decrease_alerts = [a for a in alerts if a["change_pct"] < 0]

    lines = [f"📊 ETF规模异动提醒 ({date_str})\n"]

    if increase_alerts:
        lines.append("🔴 规模增幅 > 5%:\n")
        for alert in increase_alerts:
            lines.append(
                f"• {alert['name']} ({alert['code']}): "
                f"最新规模{alert['current_amount']:.2f}亿元, "
                f"较上日+{alert['change_pct']:.2f}%\n"
            )
        lines.append("\n")

    if decrease_alerts:
        lines.append("🟢 规模降幅 > 5%:\n")
        for alert in decrease_alerts:
            lines.append(
                f"• {alert['name']} ({alert['code']}): "
                f"最新规模{alert['current_amount']:.2f}亿元, "
                f"较上日{alert['change_pct']:.2f}%\n"
            )
        lines.append("\n")

    lines.append(f"共计监控 **{total_count}** 只ETF, 其中 **{len(alerts)}** 只异动")

    return "".join(lines)


def run_comparison(date_str: str, sse_etfs: List[Dict], szse_etfs: List[Dict]) -> Tuple[List[Dict], Dict]:
    """
    运行完整的比较流程

    Args:
        date_str: 日期字符串
        sse_etfs: 上交所ETF数据
        szse_etfs: 深交所ETF数据

    Returns:
        (告警列表, 汇总信息)
    """
    # 合并今日数据
    current_etfs = merge_etf_lists(sse_etfs, szse_etfs)
    total_count = len(current_etfs)

    print(f"今日监控ETF总数: {total_count} 只（上交所{len(sse_etfs)} + 深交所{len(szse_etfs)}）")

    # 获取上一交易日数据
    previous_date = get_previous_trading_day(date_str)

    if not previous_date:
        print("无上一交易日数据，跳过告警判断")
        # 保存报告
        save_report(date_str, [], {"total_count": total_count, "alert_count": 0, "no_history": True})
        return [], {"total_count": total_count, "alert_count": 0, "no_history": True}

    print(f"上一交易日: {previous_date}")
    previous_data = load_etf_data(previous_date)

    if not previous_data:
        print("无法加载上一交易日数据，跳过告警判断")
        save_report(date_str, [], {"total_count": total_count, "alert_count": 0, "no_history": True})
        return [], {"total_count": total_count, "alert_count": 0, "no_history": True}

    # 合并历史数据
    previous_etfs = merge_etf_lists(
        previous_data.get("sse_etfs", []),
        previous_data.get("szse_etfs", [])
    )

    # 计算变动
    alerts = calculate_changes(current_etfs, previous_etfs)

    print(f"触发告警ETF数量: {len(alerts)} 只")

    # 保存报告
    summary = {
        "total_count": total_count,
        "alert_count": len(alerts),
        "previous_date": previous_date,
        "current_date": date_str
    }
    save_report(date_str, alerts, summary)

    return alerts, summary


if __name__ == "__main__":
    # 测试
    test_sse = [
        {"code": "510050", "name": "博时沪深300ETF", "total_amount": 100},
        {"code": "510300", "name": "华泰柏瑞沪深300ETF", "total_amount": 200},
        {"code": "159919", "name": "嘉实沪深300ETF", "total_amount": 150},
    ]
    test_szse = [
        {"code": "159915", "name": "易方达创业板ETF", "total_amount": 80},
    ]

    alerts, summary = run_comparison("2026-04-05", test_sse, test_szse)
    print(f"告警数量: {len(alerts)}")
    print(f"汇总: {summary}")
