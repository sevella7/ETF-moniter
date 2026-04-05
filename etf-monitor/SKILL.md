---
name: etf-monitor
description: 监控上交所和深交所全部ETF每日规模变化，当规模变动超过5%时通过飞书机器人发送提醒。Use this skill whenever the user wants to monitor ETF size changes, track ETF flow data, or get alerts when ETF holdings shift significantly. Trigger phrases include "监控ETF规模", "ETF规模变化", "etf monitor", "ETF流量监控".
---

# ETF规模监控技能

## 用途
每日定时监控上交所和深交所全部ETF的规模变动，当某只ETF规模较上一交易日变动超过5%时，通过飞书群机器人发送提醒。

## 触发方式
- GitHub Actions 定时触发（每天22:00北京时间，即14:00 UTC）
- 也可手动触发

## 数据来源
1. **上交所ETF**: https://www.sse.com.cn/market/funddata/volumn/etfvolumn/
2. **深交所ETF**: https://www.szse.cn/market/fundlist/etf/index.html
3. **备选数据源**: AkShare (`akshare.fund_etf_hist_em`, `akshare.fund_etf_sse`, `akshare.fund_etf_szse`)

## 数据存储
- 本地JSON文件存储历史数据: `data/etf_history/<date>.json`
- 每次运行后保存当日数据，保留最近30个交易日数据
- 数据结构:
```json
{
  "date": "2026-04-05",
  "sse_etfs": [...],
  "szse_etfs": [...],
  "updated_at": "22:00:00"
}
```

## 输出文件
- `data/etf_history/<YYYY-MM-DD>.json` - 当日ETF规模数据
- `reports/<date>/etf_monitor.md` - 监控报告
- `reports/<date>/etf_alerts.json` - 触发告警的ETF列表

## 告警判断逻辑
1. 获取今日ETF规模数据（上交所 + 深交所）
2. 读取昨日数据（如不存在则跳过告警判断，仅记录今日数据）
3. 对每只ETF计算: `(今日规模 - 昨日规模) / 昨日规模 * 100%`
4. 变动比例绝对值 > 5% 的ETF进入告警列表
5. 发送飞书通知

## 告警内容格式
```
📊 ETF规模异动提醒 (2026-04-05)

🔴 规模增幅 > 5%:
• 基金名称1 (代码1): 最新规模X亿元, 较上日+6.5%
• 基金名称2 (代码2): 最新规模Y亿元, 较上日+7.2%

🟢 规模降幅 > 5%:
• 基金名称3 (代码3): 最新规模Z亿元, 较上日-6.1%

共计监控XXX只ETF, 其中XX只异动
```

## 飞书通知配置
需要配置以下环境变量:
- `FEISHU_WEBHOOK_URL`: 飞书群机器人WebHook地址
- `FEISHU_MAX_BYTES`: 单条消息最大字节数（默认20000）

## 运行命令

### 本地运行
```bash
cd etf-monitor
pip install -r requirements.txt
python scripts/run_monitor.py --date 2026-04-05
```

### GitHub Actions 自动运行
推送代码后，GitHub Actions会在每天22:00北京时间自动运行

## 目录结构
```
etf-monitor/
├── SKILL.md
├── scripts/
│   ├── run_monitor.py      # 主入口脚本
│   ├── fetch_sse_etf.py   # 获取上交所ETF数据
│   ├── fetch_szse_etf.py  # 获取深交所ETF数据
│   ├── fetch_akshare.py    # AkShare备选数据源
│   ├── storage.py          # 数据存储（读写JSON）
│   ├── comparator.py        # 规模比较与告警判断
│   └── notifier.py         # 飞书通知发送
├── data/
│   └── etf_history/       # 历史数据存储
├── reports/                # 报告输出
├── .github/workflows/
│   └── etf_monitor.yml    # GitHub Actions工作流
├── requirements.txt
└── README.md
```

## 依赖
- requests
- pandas
- akshare
- beautifulsoup4

## 注意事项
1. 深交所网站结构需要确认，可能需要调整爬虫策略
2. 如果网站反爬，需要加入适当的延迟和请求头
3. 首次运行无法计算变动（无历史数据），只会保存数据
4. 告警阈值5%可通过环境变量`ALERT_THRESHOLD`调整
