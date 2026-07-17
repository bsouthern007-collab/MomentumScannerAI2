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

## Quick local check

```text
.venv\Scripts\python.exe tests\smoke_app.py
```

That checks the scanner, AI plan, and backtester without making live trades.
