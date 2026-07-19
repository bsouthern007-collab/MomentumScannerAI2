# Trading for Dummys 101

Clean Streamlit app for learning low-priced momentum day-trade setups, live charts, watchlists, ranked news, and paper-trade planning.

Default scanner rules:

- Price: $2 to $20
- Daily gain: 10% or higher
- Float: under 10 million shares
- Relative volume: 3x or higher

The app includes learning data so it never opens blank, plus optional live data.

## Streamlit Cloud

Use this as the main file path when deploying:

```text
app.py
```

If your app is already set to the older uploaded-folder path, it will still forward into the root app. For new deployments, `app.py` is cleaner.

## Add your Finnhub key

Do not paste API keys into chat.

1. Open `.streamlit/secrets.example.toml`.
2. Save a copy named `.streamlit/secrets.toml`.
3. Replace `paste-your-finnhub-key-here` with your Finnhub key:

```toml
FINNHUB_API_KEY = "your_key_here"
```

Restart the app after saving. Finnhub turns on better live quotes and stock news.

## Optional free Alpaca IEX data

Use Alpaca paper-trading keys first. Add these to `.streamlit/secrets.toml`:

```toml
ALPACA_API_KEY = "your_key_id_here"
ALPACA_SECRET_KEY = "your_secret_key_here"
```

When those keys are present, the app tries Alpaca IEX candles for regular stocks before falling back to Yahoo and learning data. Broad indexes like S&P 500 still use Yahoo-style symbols.

## Chart engine

The premium candle chart uses TradingView Lightweight Charts from `assets/lightweight-charts.standalone.production.js`, with an online fallback if that local file is missing.

The TradingView-style chart includes window presets, zoom in/out, back/forward, latest, fit-to-context, a buy-zone band, and entry/stop/take-profit chips. Candles stay green for up candles and red for down candles.

## Data confidence

The app shows a data stack panel and source brief so users can see whether Alpaca IEX, Finnhub, Yahoo fallback, or learning data is powering the current view. The Learn page includes a direct data-source lesson at:

```text
/Learn?track=Data%20sources
```

## Beginner AI ladder

The AI assistant includes a five-step ladder for paper-trade review: data check, setup check, entry trigger, stop loss, and take profit. The Learn page includes a matching lesson at:

```text
/Learn?track=AI%20ladder
```

## Workflow cockpit

The app includes a guided workflow cockpit that tells users the next step for the current stock: keep scanning, verify data, watch the chart, review a paper plan, or journal the result. The Learn page includes a matching lesson at:

```text
/Learn?track=Workflow%20cockpit
```

## Paper approval gate

Trade Desk includes a paper-order approval checklist for data source, chart entry, stop loss, target reward, news, spread, volume, and halt risk. The final approval button stays locked until the checklist is complete and no hard blocker is active.

## Quick local check

```text
.venv\Scripts\python.exe tests\smoke_app.py
```

That checks the scanner, AI plan, and backtester without making live trades.
