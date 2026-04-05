# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JusticePlutus is a local A-share stock analysis pipeline that:
1. Fetches market data (historical + realtime + chip distribution)
2. Retrieves news/intelligence via search APIs
3. Generates structured analysis via LLM
4. Produces Markdown/JSON reports
5. Sends notifications to configured channels (Telegram, Feishu, etc.)

## Common Commands

```bash
# Install dependencies
pip install -e .

# Run analysis (local)
python -m justice_plutus run --stocks "600519,000001" --no-notify

# Run with notifications
python -m justice_plutus run --stocks "600519" --notify

# Dry run (data fetch only, no AI analysis)
python -m justice_plutus run --stocks "600519" --dry-run

# Using the skill wrapper script
sh justice-plutus/scripts/run_analysis.sh "688200"

# Run tests
pytest
```

## Architecture

```
justice_plutus/
├── justice_plutus/          # Skill wrapper layer
│   ├── cli.py               # CLI entry point
│   └── runtime.py           # Runtime utilities
├── src/
│   ├── core/pipeline.py     # StockAnalysisPipeline - main orchestrator
│   ├── config.py             # Config singleton - loads .env, manages all settings
│   ├── analyzer.py          # GeminiAnalyzer - LLM analysis using LiteLLM
│   ├── search_service.py    # SearchService - Bocha/Tavily/SerpAPI
│   ├── notification.py      # NotificationService - multi-channel sender
│   ├── ifind/               # iFinD (同花顺) professional data integration
│   │   ├── client.py        # IFind HTTP client
│   │   ├── auth.py          # Token refresh logic
│   │   ├── service.py       # High-level iFinD service
│   │   └── mappers.py       # Response field mapping
│   ├── data/                # Data layer
│   │   └── stock_mapping.py # Static stock name mappings
│   ├── enums.py             # ReportType, NotificationChannel, etc.
│   └── formatters.py        # Report formatting utilities
├── data_provider/           # Market data fetchers (fallback chain)
│   ├── base.py              # BaseFetcher interface
│   ├── tushare_fetcher.py   # Tushare Pro
│   ├── efinance_fetcher.py  # Eastmoney/Efinance
│   ├── akshare_fetcher.py   # Akshare
│   ├── ifind_fetcher.py     # iFinD fetcher
│   ├── pytdx_fetcher.py     # Pytdx (通花顺)
│   ├── baostock_fetcher.py  # Baostock
│   ├── wencai_fetcher.py    # 问财 chip data
│   └── hscloud_fetcher.py   # HSCloud chip data
└── reports/                  # Output reports (auto-generated)
    └── YYYY-MM-DD/
        ├── stocks/<code>.md
        ├── stocks/<code>.json
        ├── summary.md
        └── summary.json
```

## Key Design Patterns

### Fallback Chains
Every data source has a fallback chain. If one source fails, the next is tried automatically:
- **Daily history**: iFinD → Tushare → Efinance → Akshare → Pytdx → Baostock → YFinance
- **Realtime quotes**: iFinD → (configured priority via `realtime_source_priority`)
- **Chip distribution**: HSCloud → Wencai → Akshare → Tushare → Efinance
- **Search**: Bocha → Tavily → SerpAPI (per-dimension fallback)

### Config Singleton
`Config.get_instance()` loads from `.env` file. All modules share the same config instance. Key settings:
- `STOCK_LIST`: Default stock list
- `LITELLM_MODEL` / `LITELLM_FALLBACK_MODELS`: LLM configuration
- `REALTIME_SOURCE_PRIORITY`: Realtime data source order
- `ENABLE_CHIP_DISTRIBUTION`: Chip data toggle

### LLM Integration via LiteLLM
The analyzer uses LiteLLM for unified LLM access. Model resolution order:
1. `LITELLM_CONFIG` (YAML file)
2. `LLM_CHANNELS` (env-based multi-channel)
3. Legacy keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`, etc.)

### Report Output
Reports are saved locally regardless of notification settings:
- `reports/YYYY-MM-DD/stocks/<code>.md|json` - Per-stock reports
- `reports/YYYY-MM-DD/summary.md|json` - Batch summary
- `reports/YYYY-MM-DD/run_meta.json` - Run metadata

## Environment Setup

Required `.env` file at project root:
```bash
# LLM (at least one required)
OPENAI_API_KEY=sk-...           # or AIHUBMIX_KEY
LITELLM_MODEL=minimax/MiniMax-M2.7

# Optional data enhancements
TUSHARE_TOKEN=...
WENCAI_COOKIE=...
HSCLOUD_AUTH_TOKEN=...

# Optional search
BOCHA_API_KEYS=...
TAVILY_API_KEYS=...

# Optional notifications
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
FEISHU_WEBHOOK_URL=...
```

## Important Files

- `src/core/pipeline.py:44` - `StockAnalysisPipeline` class: main analysis orchestrator
- `src/config.py:80` - `Config` dataclass: all configuration fields
- `src/analyzer.py` - `GeminiAnalyzer`: LLM prompt construction and response parsing
- `src/notification.py` - `NotificationService`: multi-channel notification dispatch
- `data_provider/` - All market data fetchers implementing fallback logic
