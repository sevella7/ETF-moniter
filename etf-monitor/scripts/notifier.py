"""
飞书通知发送模块
"""

import os
import requests
from typing import Dict, Any, List


# 飞书Webhook配置
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")
max_bytes_str = os.getenv("FEISHU_MAX_BYTES", "20000")
if not max_bytes_str:
    max_bytes_str = "20000"
FEISHU_MAX_BYTES = int(max_bytes_str)


def send_feishu_message(message: str) -> bool:
    """
    发送飞书群机器人消息

    Args:
        message: 消息内容

    Returns:
        是否发送成功
    """
    if not FEISHU_WEBHOOK_URL:
        print("未配置FEISHU_WEBHOOK_URL，跳过发送")
        return False

    # 飞书卡片消息格式
    payload = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }

    try:
        response = requests.post(
            FEISHU_WEBHOOK_URL,
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

        if result.get("code") == 0 or result.get("StatusCode") == 0:
            print("飞书消息发送成功")
            return True
        else:
            print(f"飞书消息发送失败: {result}")
            return False

    except Exception as e:
        print(f"发送飞书消息异常: {e}")
        return False


def send_feishu_card(message: str) -> bool:
    """
    发送飞书卡片消息（更美观）

    Args:
        message: 消息内容

    Returns:
        是否发送成功
    """
    if not FEISHU_WEBHOOK_URL:
        print("未配置FEISHU_WEBHOOK_URL，跳过发送")
        return False

    # 飞书卡片消息格式
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "📊 ETF规模异动提醒"
                },
                "template": "red" if "🔴" in message else "green"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "text",
                        "content": message.replace("📊 ", "").replace("\n", "\n")
                    }
                }
            ]
        }
    }

    try:
        response = requests.post(
            FEISHU_WEBHOOK_URL,
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

        if result.get("code") == 0 or result.get("StatusCode") == 0:
            print("飞书卡片消息发送成功")
            return True
        else:
            print(f"飞书卡片消息发送失败: {result}")
            return False

    except Exception as e:
        print(f"发送飞书卡片消息异常: {e}")
        return False


def send_alert(date_str: str, alerts: List[Dict], summary: Dict) -> bool:
    """
    发送告警通知

    Args:
        date_str: 日期字符串
        alerts: 告警列表
        summary: 汇总信息

    Returns:
        是否发送成功
    """
    # 优先使用卡片消息
    if alerts:
        # 构建表格内容
        increase_alerts = [a for a in alerts if a["change_pct"] > 0]
        decrease_alerts = [a for a in alerts if a["change_pct"] < 0]

        elements = []

        # 汇总信息
        elements.append({
            "tag": "div",
            "text": {
                "tag": "text",
                "content": f"📅 日期: {date_str}\n"
                           f"📈 监控ETF总数: {summary.get('total_count', 0)}\n"
                           f"⚠️ 异动数量: {summary.get('alert_count', 0)}"
            }
        })

        elements.append({"tag": "hr"})

        if increase_alerts:
            content = "🔴 **规模增幅 > 5%:**\n"
            for alert in increase_alerts:
                content += f"• {alert['name']} ({alert['code']}): {alert['current_amount']:.2f}亿元, +{alert['change_pct']:.2f}%\n"
            elements.append({
                "tag": "div",
                "text": {"tag": "text", "content": content}
            })

        if decrease_alerts:
            content = "🟢 **规模降幅 > 5%:**\n"
            for alert in decrease_alerts:
                content += f"• {alert['name']} ({alert['code']}): {alert['current_amount']:.2f}亿元, {alert['change_pct']:.2f}%\n"
            elements.append({
                "tag": "div",
                "text": {"tag": "text", "content": content}
            })

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "📊 ETF规模异动提醒"
                    },
                    "template": "red"
                },
                "elements": elements
            }
        }
    else:
        # 无告警
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "✅ ETF规模监控报告"
                    },
                    "template": "green"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "text",
                            "content": f"📅 日期: {date_str}\n\n✅ 今日无ETF规模异动\n\n共计监控 **{summary.get('total_count', 0)}** 只ETF，规模变动均未超过5%"
                        }
                    }
                ]
            }
        }

    try:
        response = requests.post(
            FEISHU_WEBHOOK_URL,
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()

        if result.get("code") == 0 or result.get("StatusCode") == 0:
            print("飞书告警发送成功")
            return True
        else:
            print(f"飞书告警发送失败: {result}")
            return False

    except Exception as e:
        print(f"发送飞书告警异常: {e}")
        return False


if __name__ == "__main__":
    # 测试
    test_message = """📊 ETF规模异动提醒 (2026-04-05)

🔴 规模增幅 > 5%:
• 博时沪深300ETF (510050): 最新规模106.50亿元, 较上日+6.50%
• 华泰柏瑞沪深300ETF (510300): 最新规模215.20亿元, 较上日+7.20%

🟢 规模降幅 > 5%:
• 易方达创业板ETF (159915): 最新规模75.30亿元, 较上日-6.10%

共计监控 600 只ETF, 其中 3 只异动
"""
    send_feishu_message(test_message)
