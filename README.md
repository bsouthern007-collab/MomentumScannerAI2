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

The TradingView-style chart includes 15/30/45/90/180/1-day window presets, zoom in/out, back/forward, latest, fit-to-context, a bottom range strip for 1D/5D/month/YTD/all views, a buy-zone band, beginner-readable Buy/Stop/TP chips, a dedicated AI plan side panel, session dividers, and compact TP/stop direction hints when levels are outside the visible price range. Candles stay green for up candles and red for down candles. The chart prioritizes candle autoscaling, resets VWAP by intraday session, and draws sharper candle bodies/wicks so one-minute bars stay readable when zoomed in.

Scanner tables include a plain-English `Priority` column and a `Rules ready` count so beginners can see whether price, gain, float, and RVOL are actually lining up before opening the chart.

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

## Market pulse

Dashboard, Daily Gameplan, Scanner, Market Scan, and Live Tracker include a scan-wide market pulse panel. It summarizes data trust, active paper setups, the top stock, average RVOL, source mix, risk flags, and the best next move for beginners. The Learn page includes a matching lesson at:

```text
/Learn?track=Market%20pulse
```

## Branding and AI characters

The app includes an inline SVG brand mark and selectable AI characters: Scout, Null, Nova, and Flux. The selected character appears in the sidebar and dashboard, then summarizes the current top stock with plain-English entry, stop, target, and data-confidence context. Character art ships in `assets/`, so it does not require image hosting, paid services, or extra deployment files.

The app also includes a floating animated companion overlay. Turn it on from the sidebar, choose Wander, Docked, or Focus mode, drag the character around the app, and use the tip button to rotate beginner-friendly reminders. This runs inside the Streamlit app/browser. A true always-on desktop pet that floats over other Windows apps would need a separate desktop wrapper.

For a local Windows desktop companion, double-click:

```text
Start_Desktop_Companion.bat
```

Or run:

```text
.venv\Scripts\python.exe desktop_companion.py
```

That opens a small always-on-top companion you can drag around your PC. Right-click cycles Scout, Null, Nova, and Flux. Space changes the tip. Esc closes it.

## Paper approval gate

Trade Desk includes a paper-order approval checklist for data source, chart entry, stop loss, target reward, news, spread, volume, and halt risk. The final approval button stays locked until the checklist is complete and no hard blocker is active.

## Quick local check

```text
.venv\Scripts\python.exe tests\smoke_app.py
```

That checks the scanner, AI plan, and backtester without making live trades.
