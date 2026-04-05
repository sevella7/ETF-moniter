# ETF规模监控

监控上交所和深交所全部ETF每日规模变化，当规模变动超过5%时通过飞书机器人发送提醒。

## 功能特性

- 每日自动监控上交所 + 深交所全部ETF
- 规模变动超过5%时触发告警
- 飞书群机器人实时推送
- 历史数据本地存储（保留30个交易日）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置飞书Webhook

在 GitHub Secrets 中添加:
- `FEISHU_WEBHOOK_URL`: 飞书群机器人WebHook地址

### 3. 本地运行

```bash
# 监控今日
python scripts/run_monitor.py

# 指定日期
python scripts/run_monitor.py --date 2026-04-05

# 仅获取数据，不发送通知
python scripts/run_monitor.py --dry-run
```

### 4. 配置GitHub Actions自动运行

推送代码后，GitHub Actions会在每天北京时间22:00自动运行。

如需手动触发，在GitHub Actions页面点击 "Run workflow"。

## 告警示例

```
📊 ETF规模异动提醒 (2026-04-05)

🔴 规模增幅 > 5%:
• 博时沪深300ETF (510050): 最新规模106.50亿元, 较上日+6.50%

🟢 规模降幅 > 5%:
• 易方达创业板ETF (159915): 最新规模75.30亿元, 较上日-6.10%

共计监控 600 只ETF, 其中 2 只异动
```

## 目录结构

```
etf-monitor/
├── scripts/
│   ├── run_monitor.py       # 主入口
│   ├── fetch_sse_etf.py     # 上交所数据
│   ├── fetch_szse_etf.py    # 深交所数据
│   ├── fetch_akshare.py     # AkShare备选
│   ├── storage.py           # 数据存储
│   ├── comparator.py        # 规模比较
│   └── notifier.py          # 飞书通知
├── data/etf_history/        # 历史数据
├── reports/                 # 监控报告
├── .github/workflows/       # GitHub Actions
└── requirements.txt
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| FEISHU_WEBHOOK_URL | 是 | 飞书群机器人WebHook地址 |
| FEISHU_MAX_BYTES | 否 | 消息最大字节数，默认20000 |
| ALERT_THRESHOLD | 否 | 告警阈值，默认5.0 |

## 数据来源

1. 上交所: https://www.sse.com.cn/market/funddata/volumn/etfvolumn/
2. 深交所: https://www.szse.cn/market/fundlist/etf/index.html
3. 备选: AkShare
