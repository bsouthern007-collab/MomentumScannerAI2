# MomentumScannerAI

Clean Streamlit rebuild for learning low-priced momentum day-trade setups.

Default scanner rules:

- Price: $2 to $20
- Daily gain: 10% or higher
- Float: under 10 million shares
- Relative volume: 3x or higher

The app includes learning data so it never opens blank, plus optional live data.

## Add your Finnhub key

Do not paste API keys into chat.

1. Open `.streamlit/secrets.example.toml`.
2. Save a copy named `.streamlit/secrets.toml`.
3. Replace `paste-your-finnhub-key-here` with your Finnhub key:

```toml
FINNHUB_API_KEY = "your_key_here"
```

Restart the app after saving. Finnhub turns on better live quotes and stock news.
