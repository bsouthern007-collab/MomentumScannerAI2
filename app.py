from __future__ import annotations

import json
import math
import os
import html
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import altair as alt
import numpy as np
import pandas as pd
import requests
import streamlit as st

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except Exception:  # pragma: no cover - optional chart upgrade
    go = None
    make_subplots = None

try:
    import yfinance as yf
except Exception:  # pragma: no cover - the app still works without yfinance
    yf = None


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
WATCHLIST_FILE = DATA_DIR / "watchlist.json"
JOURNAL_FILE = DATA_DIR / "trade_journal.csv"
ORDERS_FILE = DATA_DIR / "paper_orders.csv"
YFINANCE_CACHE_DIR = DATA_DIR / "yfinance_cache"
LIVE_REFRESH_SECONDS = 30
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
FINNHUB_API_URL = "https://finnhub.io/api/v1/{endpoint}"
SP500_SOURCE_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
DEFAULT_MARKET_SCAN_BATCH = 80
DATA_DIR.mkdir(exist_ok=True)
YFINANCE_CACHE_DIR.mkdir(exist_ok=True)

if yf is not None:
    try:
        yf.set_tz_cache_location(str(YFINANCE_CACHE_DIR))
    except Exception:
        pass

DEFAULT_RULES = {
    "min_price": 2.0,
    "max_price": 20.0,
    "min_gain_pct": 10.0,
    "max_float_m": 10.0,
    "min_rvol": 3.0,
}

CORE_MARKET_TICKERS = [
    "NVDA",
    "AAPL",
    "MSFT",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
    "AMD",
    "PLTR",
    "SMCI",
    "AVGO",
    "QQQ",
    "SPY",
    "IWM",
    "DIA",
]

SP500_SAMPLE_TICKERS = [
    "NVDA",
    "AAPL",
    "MSFT",
    "AMZN",
    "META",
    "GOOGL",
    "GOOG",
    "AVGO",
    "TSLA",
    "BRK-B",
    "JPM",
    "WMT",
    "LLY",
    "V",
    "MA",
    "XOM",
    "UNH",
    "COST",
    "NFLX",
    "HD",
    "PG",
    "ORCL",
    "JNJ",
    "BAC",
    "ABBV",
    "KO",
    "AMD",
    "CRM",
    "PLTR",
    "CSCO",
    "MCD",
    "IBM",
    "GE",
    "NOW",
    "WFC",
    "PM",
    "ABT",
    "DIS",
    "LIN",
    "MS",
]

GLOBAL_MARKET_WATCH = {
    "United States": ["SPY", "QQQ", "IWM", "DIA", "NVDA", "TSLA", "AMD"],
    "Europe": ["EWG", "EWU", "FEZ", "VGK", "ASML", "SAP"],
    "Asia": ["EWJ", "MCHI", "FXI", "INDA", "EWT", "TSM"],
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD"],
}

MARKET_CLOCKS = [
    {"Market": "New York", "Timezone": "America/New_York", "Typical session": "9:30 AM - 4:00 PM"},
    {"Market": "Phoenix", "Timezone": "America/Phoenix", "Typical session": "6:30 AM - 1:00 PM"},
    {"Market": "London", "Timezone": "Europe/London", "Typical session": "8:00 AM - 4:30 PM"},
    {"Market": "Frankfurt", "Timezone": "Europe/Berlin", "Typical session": "9:00 AM - 5:30 PM"},
    {"Market": "Tokyo", "Timezone": "Asia/Tokyo", "Typical session": "9:00 AM - 3:00 PM"},
    {"Market": "Hong Kong", "Timezone": "Asia/Hong_Kong", "Typical session": "9:30 AM - 4:00 PM"},
    {"Market": "Sydney", "Timezone": "Australia/Sydney", "Typical session": "10:00 AM - 4:00 PM"},
]

DEMO_PROFILES: list[dict[str, Any]] = [
    {
        "ticker": "KULR",
        "company": "KULR Technology",
        "sector": "Battery systems",
        "price": 3.12,
        "daily_gain_pct": 21.4,
        "float_m": 4.7,
        "rvol": 9.6,
        "volume": 38_400_000,
        "catalyst": "Momentum news and unusual volume",
    },
    {
        "ticker": "BBAI",
        "company": "BigBear.ai",
        "sector": "AI analytics",
        "price": 4.92,
        "daily_gain_pct": 18.3,
        "float_m": 9.7,
        "rvol": 7.9,
        "volume": 52_700_000,
        "catalyst": "AI sector strength and gapper scan hit",
    },
    {
        "ticker": "LUNR",
        "company": "Intuitive Machines",
        "sector": "Space",
        "price": 10.18,
        "daily_gain_pct": 16.6,
        "float_m": 9.2,
        "rvol": 5.9,
        "volume": 44_900_000,
        "catalyst": "Contract speculation and heavy premarket interest",
    },
    {
        "ticker": "SERV",
        "company": "Serve Robotics",
        "sector": "Robotics",
        "price": 13.38,
        "daily_gain_pct": 15.2,
        "float_m": 5.4,
        "rvol": 7.2,
        "volume": 25_100_000,
        "catalyst": "Small-float robotics momentum",
    },
    {
        "ticker": "SOUN",
        "company": "SoundHound AI",
        "sector": "AI voice",
        "price": 7.84,
        "daily_gain_pct": 14.0,
        "float_m": 8.8,
        "rvol": 6.6,
        "volume": 68_400_000,
        "catalyst": "AI name with high retail volume",
    },
    {
        "ticker": "QBTS",
        "company": "D-Wave Quantum",
        "sector": "Quantum",
        "price": 8.36,
        "daily_gain_pct": 13.1,
        "float_m": 6.5,
        "rvol": 4.8,
        "volume": 31_800_000,
        "catalyst": "Quantum momentum and volume expansion",
    },
    {
        "ticker": "IONQ",
        "company": "IonQ",
        "sector": "Quantum",
        "price": 16.28,
        "daily_gain_pct": 12.4,
        "float_m": 9.9,
        "rvol": 3.8,
        "volume": 29_700_000,
        "catalyst": "Sector sympathy move",
    },
    {
        "ticker": "RGTI",
        "company": "Rigetti Computing",
        "sector": "Quantum",
        "price": 12.45,
        "daily_gain_pct": 11.8,
        "float_m": 7.4,
        "rvol": 5.1,
        "volume": 36_200_000,
        "catalyst": "Quantum breakout watch",
    },
    {
        "ticker": "ACHR",
        "company": "Archer Aviation",
        "sector": "Aviation",
        "price": 6.74,
        "daily_gain_pct": 10.9,
        "float_m": 8.1,
        "rvol": 4.2,
        "volume": 41_600_000,
        "catalyst": "EV aviation momentum",
    },
    {
        "ticker": "RKLB",
        "company": "Rocket Lab",
        "sector": "Space",
        "price": 9.61,
        "daily_gain_pct": 10.7,
        "float_m": 8.6,
        "rvol": 3.5,
        "volume": 22_400_000,
        "catalyst": "Space sector follow-through",
    },
]

PROFILE_BY_TICKER = {row["ticker"]: row for row in DEMO_PROFILES}


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        number = float(value)
        if not math.isfinite(number):
            return default
        return number
    except Exception:
        return default


def first_number(*values: Any, default: float | None = None) -> float | None:
    for value in values:
        number = safe_float(value)
        if number is not None:
            return number
    return default


def timestamp_label(value: Any) -> str:
    seconds = safe_float(value)
    if seconds is None:
        return "n/a"
    try:
        return datetime.fromtimestamp(seconds).strftime("%Y-%m-%d %I:%M %p")
    except Exception:
        return "n/a"


def money(value: float | int | None) -> str:
    if value is None or not math.isfinite(float(value)):
        return "n/a"
    return f"${float(value):,.2f}"


def pct(value: float | int | None) -> str:
    if value is None or not math.isfinite(float(value)):
        return "n/a"
    return f"{float(value):.1f}%"


def compact_number(value: float | int | None) -> str:
    if value is None or not math.isfinite(float(value)):
        return "n/a"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.0f}"


def markdown_text(value: Any) -> str:
    return str(value).replace("$", "\\$")


def playbook_fit_label(stats: dict[str, Any], score: float | int | None = None) -> str:
    price = safe_float(stats.get("Price"), 0) or 0
    gain = safe_float(stats.get("Daily gain %"), 0) or 0
    float_m = safe_float(stats.get("Float M"), 999) or 999
    rvol = safe_float(stats.get("RVOL"), 0) or 0
    score_value = safe_float(score, safe_float(stats.get("AI score"), 0)) or 0

    price_ok = DEFAULT_RULES["min_price"] <= price <= DEFAULT_RULES["max_price"]
    gain_ok = gain >= DEFAULT_RULES["min_gain_pct"]
    float_ok = float_m <= DEFAULT_RULES["max_float_m"]
    rvol_ok = rvol >= DEFAULT_RULES["min_rvol"]
    fit_count = sum([price_ok, gain_ok, float_ok, rvol_ok])

    if fit_count == 4 and score_value >= 74:
        return "Playbook fit"
    if price_ok and rvol_ok and fit_count >= 3:
        return "Developing setup"
    if not price_ok or not float_ok:
        return "Market context"
    if fit_count <= 1:
        return "Study only"
    return "Wait for confirmation"


def playbook_fit_color(label: str) -> str:
    if label == "Playbook fit":
        return "green"
    if label == "Developing setup":
        return "blue"
    if label == "Wait for confirmation":
        return "orange"
    if label == "Market context":
        return "violet"
    return "gray"


def data_quality_badge(source: Any) -> tuple[str, str]:
    source_text = str(source or "Unknown")
    lowered = source_text.lower()
    if "finnhub" in lowered:
        return "Finnhub quote", "green"
    if "yahoo finance api" in lowered:
        return "Yahoo candles", "blue"
    if "yahoo finance" in lowered:
        return "Yahoo quote", "blue"
    if "learning" in lowered:
        return "Learning fallback", "orange"
    return source_text[:22], "gray"


CATALYST_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Earnings": ("earnings", "eps", "revenue", "guidance", "quarter", "q1", "q2", "q3", "q4"),
    "Contract": ("contract", "award", "deal", "partnership", "customer", "order", "launch"),
    "FDA/regulatory": ("fda", "approval", "clinical", "trial", "phase", "patent", "regulatory"),
    "Analyst": ("upgrade", "downgrade", "price target", "initiates", "rating"),
    "Sector": ("ai", "quantum", "crypto", "semiconductor", "space", "robotics", "ev"),
    "M&A": ("acquisition", "merger", "buyout", "takeover"),
}

RISK_NEWS_KEYWORDS: tuple[str, ...] = (
    "offering",
    "dilution",
    "bankruptcy",
    "investigation",
    "sec",
    "lawsuit",
    "halt",
    "delisting",
    "reverse split",
)


def catalyst_tags(headline: str, summary: str = "") -> list[str]:
    text = f"{headline} {summary}".lower()
    tags = [label for label, words in CATALYST_KEYWORDS.items() if any(word in text for word in words)]
    if any(word in text for word in RISK_NEWS_KEYWORDS):
        tags.insert(0, "Risk headline")
    return list(dict.fromkeys(tags))[:4]


def catalyst_score(news: list[dict[str, Any]]) -> tuple[str, str]:
    if not news:
        return "No news", "gray"

    score = 0
    for item in news[:5]:
        tags = catalyst_tags(str(item.get("headline") or ""), str(item.get("summary") or ""))
        for tag in tags:
            if tag in {"Contract", "FDA/regulatory", "Earnings"}:
                score += 2
            elif tag in {"Analyst", "Sector", "M&A"}:
                score += 1
            elif tag == "Risk headline":
                score -= 3

    if score >= 4:
        return "Strong catalyst", "green"
    if score >= 2:
        return "Catalyst watch", "blue"
    if score < 0:
        return "News risk", "red"
    return "Unclear catalyst", "gray"


def setup_check_items(analysis: dict[str, Any]) -> list[tuple[str, bool, str]]:
    price = safe_float(analysis.get("Price"))
    gain = safe_float(analysis.get("Daily gain %"), 0) or 0
    float_m = safe_float(analysis.get("Float M"))
    rvol = safe_float(analysis.get("RVOL"), 0) or 0
    ema9 = safe_float(analysis.get("EMA 9"))
    ema20 = safe_float(analysis.get("EMA 20"))
    risk_reward = safe_float(analysis.get("Risk/reward"), 0) or 0
    status = live_status(analysis)

    price_ok = price is not None and DEFAULT_RULES["min_price"] <= price <= DEFAULT_RULES["max_price"]
    float_ok = float_m is not None and float_m <= DEFAULT_RULES["max_float_m"]
    trend_ok = price is not None and ema9 is not None and ema20 is not None and price > ema9 > ema20
    action_ok = status in {"Breakout trigger", "In buy zone", "Near buy zone"}
    return [
        ("Price", price_ok, money(price)),
        ("Gap", gain >= DEFAULT_RULES["min_gain_pct"], pct(gain)),
        ("Float", float_ok, f"{float_m:.1f}M" if float_m is not None else "n/a"),
        ("RVOL", rvol >= DEFAULT_RULES["min_rvol"], f"{rvol:.1f}x"),
        ("Trend", trend_ok, "above EMAs" if trend_ok else "needs hold"),
        ("Risk", risk_reward >= 1.4, f"{risk_reward:.2f}R"),
        ("Action", action_ok, status),
    ]


def setup_completion(analysis: dict[str, Any]) -> tuple[int, int]:
    checks = setup_check_items(analysis)
    return sum(1 for _, passed, _ in checks if passed), len(checks)


def clean_market_symbol(symbol: Any) -> str:
    clean = str(symbol or "").strip().upper().replace(".", "-").replace("/", "-")
    if not clean or clean in {"N/A", "NAN", "NONE"}:
        return ""
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")
    if any(char not in allowed for char in clean):
        return ""
    excluded_suffixes = ("-W", "-WS", "-WT", "-U", "-R", "-RT", "-PR", "-P")
    if clean.endswith(excluded_suffixes):
        return ""
    return clean


def tradeable_security_name(name: Any, include_etfs: bool) -> bool:
    text = str(name or "").lower()
    if not text:
        return True
    normalized = text
    for char in ",.;:/()[]{}-":
        normalized = normalized.replace(char, " ")
    words = set(normalized.split())
    blocked_words = {
        "warrant",
        "warrants",
        "right",
        "rights",
        "unit",
        "units",
        "preferred",
        "preference",
        "note",
        "notes",
        "bond",
        "bonds",
        "debenture",
        "debentures",
        "redeemable",
    }
    blocked_phrases = ("preferred stock", "depositary share", "depositary shares")
    if words.intersection(blocked_words) or any(phrase in text for phrase in blocked_phrases):
        return False
    if not include_etfs and any(word in text for word in ("etf", "fund", "trust", "etn")):
        return False
    return True


def unique_symbols(symbols: list[str]) -> list[str]:
    return [symbol for symbol in dict.fromkeys(symbols) if symbol]


def get_secret(name: str) -> str:
    value = ""
    try:
        value = str(st.secrets.get(name, "") or "")
    except Exception:
        value = ""
    clean = (value or os.environ.get(name, "")).strip()
    if clean.lower() in {"paste-your-finnhub-key-here", "your_key_here", "your-key-here"}:
        return ""
    return clean


def finnhub_api_key() -> str:
    return get_secret("FINNHUB_API_KEY") or get_secret("finnhub_api_key")


def finnhub_enabled() -> bool:
    return bool(finnhub_api_key())


def finnhub_get(endpoint: str, params: dict[str, Any] | None = None) -> Any:
    key = finnhub_api_key()
    if not key:
        return None
    clean_endpoint = endpoint.strip("/")
    response = requests.get(
        FINNHUB_API_URL.format(endpoint=clean_endpoint),
        params={**(params or {}), "token": key},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def finnhub_key_marker() -> str:
    key = finnhub_api_key()
    return f"key-{len(key)}-{key[-4:]}" if key else "no-key"


@st.cache_data(ttl=86400, max_entries=4, show_spinner=False)
def finnhub_us_symbols(api_marker: str, include_etfs: bool = True) -> list[str]:
    if api_marker == "no-key":
        return []
    try:
        payload = finnhub_get("stock/symbol", {"exchange": "US"})
        if not isinstance(payload, list):
            return []
        symbols: list[str] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            symbol = clean_market_symbol(item.get("symbol"))
            if not symbol:
                continue
            security_type = str(item.get("type") or "").lower()
            description = item.get("description")
            if not include_etfs and "etf" in security_type:
                continue
            if tradeable_security_name(description, include_etfs):
                symbols.append(symbol)
        return sorted(unique_symbols(symbols))
    except Exception:
        return []


def parse_symbol_directory(text: str, symbol_column: str, include_etfs: bool = True) -> list[str]:
    lines = [line for line in text.splitlines() if line and not line.startswith("File Creation")]
    if not lines:
        return []
    headers = lines[0].split("|")
    symbols: list[str] = []
    for line in lines[1:]:
        values = line.split("|")
        if len(values) != len(headers):
            continue
        row = dict(zip(headers, values))
        if str(row.get("Test Issue", "")).upper() == "Y":
            continue
        if not include_etfs and str(row.get("ETF", "")).upper() == "Y":
            continue
        if not tradeable_security_name(row.get("Security Name"), include_etfs):
            continue
        symbol = clean_market_symbol(row.get(symbol_column))
        if symbol:
            symbols.append(symbol)
    return symbols


@st.cache_data(ttl=86400, max_entries=4, show_spinner=False)
def nasdaqtrader_symbols(include_etfs: bool = True) -> list[str]:
    symbols: list[str] = []
    try:
        response = requests.get(NASDAQ_LISTED_URL, headers={"User-Agent": "Mozilla/5.0 MomentumScannerAI"}, timeout=10)
        response.raise_for_status()
        symbols.extend(parse_symbol_directory(response.text, "Symbol", include_etfs=include_etfs))
    except Exception:
        pass
    try:
        response = requests.get(OTHER_LISTED_URL, headers={"User-Agent": "Mozilla/5.0 MomentumScannerAI"}, timeout=10)
        response.raise_for_status()
        symbols.extend(parse_symbol_directory(response.text, "ACT Symbol", include_etfs=include_etfs))
    except Exception:
        pass
    return sorted(unique_symbols(symbols))


@st.cache_data(ttl=86400, max_entries=6, show_spinner=False)
def full_us_market_universe(include_etfs: bool = True, api_marker: str = "no-key") -> tuple[list[str], str]:
    symbols = finnhub_us_symbols(api_marker, include_etfs=include_etfs)
    if symbols:
        return symbols, "Finnhub US symbol list"
    symbols = nasdaqtrader_symbols(include_etfs=include_etfs)
    if symbols:
        return symbols, "Nasdaq Trader symbol directory"
    return [], "Full universe unavailable"


def ticker_seed(ticker: str) -> int:
    return sum((index + 1) * ord(char) for index, char in enumerate(ticker.upper())) % (2**32)


def profile_for(ticker: str) -> dict[str, Any]:
    ticker = ticker.strip().upper()
    if ticker in PROFILE_BY_TICKER:
        return dict(PROFILE_BY_TICKER[ticker])

    seed = ticker_seed(ticker)
    rng = np.random.default_rng(seed)
    price = round(float(rng.uniform(2.25, 18.75)), 2)
    gain = round(float(rng.uniform(7.0, 18.0)), 1)
    rvol = round(float(rng.uniform(2.0, 8.5)), 1)
    float_m = round(float(rng.uniform(4.0, 18.0)), 1)
    return {
        "ticker": ticker,
        "company": f"{ticker} learning profile",
        "sector": "Custom watch",
        "price": price,
        "daily_gain_pct": gain,
        "float_m": float_m,
        "rvol": rvol,
        "volume": int(rng.uniform(4_000_000, 55_000_000)),
        "catalyst": "Custom ticker. Verify live float, news, and volume.",
    }


def period_days(period: str) -> int:
    return {
        "1d": 2,
        "5d": 7,
        "1mo": 24,
        "3mo": 66,
        "6mo": 132,
        "1y": 252,
        "2y": 504,
    }.get(period, 132)


def normalize_history(raw: pd.DataFrame) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()

    df = raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    keep = [column for column in ["Open", "High", "Low", "Close", "Volume"] if column in df.columns]
    df = df[keep].dropna()
    if set(["Open", "High", "Low", "Close", "Volume"]) - set(df.columns):
        return pd.DataFrame()
    index = pd.to_datetime(df.index)
    if getattr(index, "tz", None) is not None:
        index = index.tz_convert(None)
    df.index = index
    return df.sort_index()


@st.cache_data(ttl=600, max_entries=200, show_spinner=False)
def learning_history(ticker: str, days: int) -> pd.DataFrame:
    profile = profile_for(ticker)
    rng = np.random.default_rng(ticker_seed(ticker))

    price = float(profile["price"])
    final_gain = float(profile["daily_gain_pct"]) / 100
    prev_close = price / (1 + final_gain)
    avg_volume = max(float(profile["volume"]) / max(float(profile["rvol"]), 1.1), 250_000)

    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=max(days, 32))
    closes = [prev_close * float(rng.uniform(0.58, 0.78))]
    for _ in range(1, len(dates) - 2):
        drift = 0.0025 + rng.normal(0, 0.018)
        closes.append(max(0.5, closes[-1] * (1 + drift)))

    closes = np.array(closes, dtype=float)
    event_start = 28 + int(ticker_seed(ticker) % 7)
    for index in range(event_start, len(closes) - 8, 31):
        jump = 1 + float(rng.uniform(0.08, 0.16))
        closes[index] = closes[index - 1] * jump
        for follow_index in range(index + 1, min(index + 5, len(closes))):
            closes[follow_index] = max(0.5, closes[follow_index - 1] * (1 + rng.normal(0.01, 0.03)))

    closes *= prev_close / max(closes[-1], 0.01)
    closes = np.concatenate([closes, [prev_close, price]])

    opens = np.empty_like(closes)
    opens[0] = closes[0] * (1 + rng.normal(0, 0.01))
    opens[1:] = closes[:-1] * (1 + rng.normal(0, 0.015, len(closes) - 1))
    highs = np.maximum(opens, closes) * (1 + np.abs(rng.normal(0.025, 0.012, len(closes))))
    lows = np.minimum(opens, closes) * (1 - np.abs(rng.normal(0.022, 0.01, len(closes))))
    volumes = rng.normal(avg_volume, avg_volume * 0.16, len(closes)).clip(avg_volume * 0.35, None)

    for index in range(event_start, len(closes) - 8, 31):
        volumes[index] = avg_volume * float(rng.uniform(3.4, 6.8))

    opens[-1] = prev_close * (1 + final_gain * 0.55)
    highs[-1] = max(opens[-1], price) * 1.045
    lows[-1] = min(opens[-1], price) * 0.955
    volumes[-1] = float(profile["volume"])

    return pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": volumes.astype(int),
        },
        index=dates,
    )


def yahoo_chart_api_history(ticker: str, period: str, interval: str, prepost: bool = True) -> pd.DataFrame:
    response = requests.get(
        YAHOO_CHART_URL.format(ticker=ticker),
        params={
            "range": period,
            "interval": interval,
            "includePrePost": str(bool(prepost)).lower(),
            "events": "div,splits",
        },
        headers={"User-Agent": "Mozilla/5.0 MomentumScannerAI"},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    chart = payload.get("chart") or {}
    results = chart.get("result") or []
    if not results:
        return pd.DataFrame()

    result = results[0]
    timestamps = result.get("timestamp") or []
    quotes = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    if not timestamps or not quotes:
        return pd.DataFrame()

    df = pd.DataFrame(
        {
            "Open": quotes.get("open"),
            "High": quotes.get("high"),
            "Low": quotes.get("low"),
            "Close": quotes.get("close"),
            "Volume": quotes.get("volume"),
        },
        index=pd.to_datetime(timestamps, unit="s", utc=True),
    )
    return normalize_history(df)


@st.cache_data(ttl=20, max_entries=250, show_spinner=False)
def load_history(
    ticker: str,
    period: str = "3mo",
    interval: str = "1d",
    prefer_live: bool = False,
    prepost: bool = True,
) -> tuple[pd.DataFrame, str]:
    ticker = ticker.strip().upper()
    if prefer_live:
        try:
            df = yahoo_chart_api_history(ticker, period=period, interval=interval, prepost=prepost)
            if not df.empty and len(df) >= 5:
                return df, f"Yahoo Finance API {interval}"
            print(f"[live-history] Yahoo chart API returned no usable bars for {ticker} {period}/{interval}", flush=True)
        except Exception as exc:
            print(f"[live-history] Yahoo chart API failed for {ticker} {period}/{interval}: {exc}", flush=True)

        if yf is not None:
            try:
                yf.set_tz_cache_location(str(DATA_DIR / "yfinance_cache"))
                raw = yf.Ticker(ticker).history(
                    period=period,
                    interval=interval,
                    auto_adjust=False,
                    prepost=prepost,
                    timeout=10,
                )
                df = normalize_history(raw)
                if not df.empty and len(df) >= 5:
                    return df, f"Yahoo Finance {interval}"
                print(f"[live-history] yfinance returned no usable bars for {ticker} {period}/{interval}", flush=True)
            except Exception as exc:
                print(f"[live-history] yfinance failed for {ticker} {period}/{interval}: {exc}", flush=True)

    return learning_history(ticker, period_days(period)), "Learning data"


def quote_to_stats(quote: dict[str, Any]) -> dict[str, Any] | None:
    ticker = str(quote.get("symbol") or "").strip().upper()
    if not ticker:
        return None

    price = first_number(
        quote.get("regularMarketPrice"),
        quote.get("postMarketPrice"),
        quote.get("preMarketPrice"),
        quote.get("intradayprice"),
    )
    previous_close = first_number(quote.get("regularMarketPreviousClose"), quote.get("previousClose"))
    gain_pct = first_number(quote.get("regularMarketChangePercent"), quote.get("percentchange"))
    volume = first_number(quote.get("regularMarketVolume"), quote.get("dayvolume"), quote.get("volume"), default=0)
    average_volume = first_number(
        quote.get("averageDailyVolume10Day"),
        quote.get("averageDailyVolume3Month"),
        quote.get("avgdailyvol3m"),
        default=0,
    )
    rvol = (volume / average_volume) if volume and average_volume else 0.0
    float_shares = first_number(quote.get("floatShares"))
    shares_outstanding = first_number(quote.get("sharesOutstanding"), quote.get("impliedSharesOutstanding"))
    share_count = float_shares if float_shares else shares_outstanding

    if price is None:
        return None

    profile = profile_for(ticker)
    return {
        "Ticker": ticker,
        "Company": quote.get("shortName") or quote.get("longName") or quote.get("displayName") or profile["company"],
        "Sector": quote.get("sector") or profile["sector"],
        "Price": price,
        "Previous close": previous_close or price,
        "Daily gain %": gain_pct if gain_pct is not None else 0.0,
        "Volume": volume or 0.0,
        "Average volume": average_volume or 0.0,
        "RVOL": rvol,
        "Float M": (share_count / 1_000_000) if share_count else float(profile["float_m"]),
        "Catalyst": quote.get("quoteSourceName") or "Yahoo Finance live quote",
        "Data source": f"Yahoo Finance ({quote.get('quoteSourceName', 'quote')})",
        "Float source": "Yahoo floatShares" if float_shares else "Yahoo shares outstanding proxy",
        "Market state": quote.get("marketState", "n/a"),
        "Quote time": timestamp_label(quote.get("regularMarketTime") or quote.get("postMarketTime") or quote.get("preMarketTime")),
        "Exchange": quote.get("fullExchangeName") or quote.get("exchange") or "n/a",
    }


def finnhub_quote_to_stats(ticker: str, quote: dict[str, Any]) -> dict[str, Any] | None:
    price = safe_float(quote.get("c"))
    prev = safe_float(quote.get("pc"))
    if price is None:
        return None

    profile = profile_for(ticker)
    gain_pct = safe_float(quote.get("dp"))
    if gain_pct is None and prev:
        gain_pct = ((price - prev) / prev) * 100
    volume = safe_float(quote.get("v"), profile["volume"]) or profile["volume"]
    avg_volume = max(float(profile["volume"]) / max(float(profile["rvol"]), 1.1), 1)
    return {
        "Ticker": ticker.strip().upper(),
        "Company": profile["company"],
        "Sector": profile["sector"],
        "Price": price,
        "Previous close": prev or price,
        "Daily gain %": gain_pct or 0.0,
        "Volume": volume,
        "Average volume": avg_volume,
        "RVOL": volume / avg_volume,
        "Float M": float(profile["float_m"]),
        "Catalyst": "Finnhub live quote",
        "Data source": "Finnhub quote",
        "Float source": "Profile estimate",
        "Market state": "n/a",
        "Quote time": timestamp_label(quote.get("t")),
        "Exchange": "US",
    }


@st.cache_data(ttl=20, max_entries=150, show_spinner=False)
def finnhub_quote_stats(ticker: str) -> dict[str, Any] | None:
    ticker = ticker.strip().upper()
    if not ticker:
        return None
    try:
        quote = finnhub_get("quote", {"symbol": ticker})
        if not isinstance(quote, dict):
            return None
        return finnhub_quote_to_stats(ticker, quote)
    except Exception:
        return None


@st.cache_data(ttl=300, max_entries=300, show_spinner=False)
def finnhub_company_news(ticker: str, days: int = 3, limit: int = 5) -> list[dict[str, Any]]:
    ticker = ticker.strip().upper()
    if not ticker:
        return []
    end = date.today()
    start = end - timedelta(days=days)
    try:
        payload = finnhub_get(
            "company-news",
            {"symbol": ticker, "from": start.isoformat(), "to": end.isoformat()},
        )
        if not isinstance(payload, list):
            return []
        return sorted(payload, key=lambda item: item.get("datetime", 0), reverse=True)[:limit]
    except Exception:
        return []


@st.cache_data(ttl=300, max_entries=50, show_spinner=False)
def finnhub_market_news(category: str = "general", limit: int = 8) -> list[dict[str, Any]]:
    try:
        payload = finnhub_get("news", {"category": category})
        if not isinstance(payload, list):
            return []
        return sorted(payload, key=lambda item: item.get("datetime", 0), reverse=True)[:limit]
    except Exception:
        return []


def render_news_items(news: list[dict[str, Any]], empty_message: str = "No Finnhub news returned yet.") -> None:
    if not finnhub_enabled():
        st.info("Add your free Finnhub key to turn on live news.", icon=":material/key:")
        return
    if not news:
        st.caption(empty_message)
        return

    label, color = catalyst_score(news)
    st.badge(label, icon=":material/article:", color=color)

    for item in news:
        headline = str(item.get("headline") or "Untitled news")
        source = str(item.get("source") or "News")
        url = str(item.get("url") or "")
        published = timestamp_label(item.get("datetime"))
        summary = str(item.get("summary") or "").strip()
        tags = catalyst_tags(headline, summary)
        with st.container(border=True):
            if url:
                st.markdown(f"**[{headline}]({url})**")
            else:
                st.markdown(f"**{headline}**")
            if tags:
                with st.container(horizontal=True):
                    for tag in tags:
                        st.badge(tag, color="red" if tag == "Risk headline" else "blue")
            st.caption(f"{source} | {published}")
            if summary:
                st.markdown(markdown_text(summary[:360] + ("..." if len(summary) > 360 else "")))


@st.cache_data(ttl=20, max_entries=40, show_spinner=False)
def live_quote_stats(ticker: str) -> dict[str, Any] | None:
    finnhub_stats = finnhub_quote_stats(ticker)
    if finnhub_stats:
        return finnhub_stats

    if yf is None:
        return None

    ticker = ticker.strip().upper()
    try:
        yf.set_tz_cache_location(str(YFINANCE_CACHE_DIR))
        stock = yf.Ticker(ticker)
        fast_info = dict(stock.fast_info or {})
        info = stock.info or {}
        quote = {
            "symbol": ticker,
            "shortName": info.get("shortName") or info.get("longName"),
            "longName": info.get("longName"),
            "sector": info.get("sector") or info.get("industry"),
            "regularMarketPrice": first_number(
                fast_info.get("last_price"),
                info.get("currentPrice"),
                info.get("regularMarketPrice"),
                info.get("previousClose"),
            ),
            "regularMarketPreviousClose": first_number(fast_info.get("previous_close"), info.get("previousClose")),
            "regularMarketChangePercent": info.get("regularMarketChangePercent"),
            "regularMarketVolume": first_number(info.get("regularMarketVolume"), info.get("volume")),
            "averageDailyVolume10Day": first_number(info.get("averageVolume10days"), info.get("averageVolume10Day")),
            "averageDailyVolume3Month": first_number(info.get("averageVolume"), info.get("averageDailyVolume3Month")),
            "floatShares": info.get("floatShares"),
            "sharesOutstanding": info.get("sharesOutstanding"),
            "impliedSharesOutstanding": info.get("impliedSharesOutstanding"),
            "quoteSourceName": info.get("quoteSourceName") or "Yahoo Finance quote",
            "marketState": info.get("marketState", "n/a"),
            "regularMarketTime": info.get("regularMarketTime"),
            "exchange": info.get("exchange"),
            "fullExchangeName": info.get("fullExchangeName"),
        }

        price = safe_float(quote["regularMarketPrice"])
        prev = safe_float(quote["regularMarketPreviousClose"])
        if price is not None and prev:
            quote["regularMarketChangePercent"] = ((price - prev) / prev) * 100
        return quote_to_stats(quote)
    except Exception:
        return None


@st.cache_data(ttl=20, max_entries=20, show_spinner=False)
def live_screener_rows(
    min_price: float,
    max_price: float,
    min_gain_pct: float,
    min_day_volume: int = 100_000,
    result_size: int = 100,
) -> list[dict[str, Any]]:
    if yf is None:
        return []

    try:
        from yfinance import EquityQuery

        yf.set_tz_cache_location(str(YFINANCE_CACHE_DIR))
        query = EquityQuery(
            "and",
            [
                EquityQuery("btwn", ["intradayprice", float(min_price), float(max_price)]),
                EquityQuery("gte", ["percentchange", float(min_gain_pct)]),
                EquityQuery("eq", ["region", "us"]),
                EquityQuery("gt", ["dayvolume", int(min_day_volume)]),
            ],
        )
        response = yf.screen(query, size=min(result_size, 250), sortField="percentchange", sortAsc=False)
        quotes = response.get("quotes", []) if isinstance(response, dict) else []
        rows = [row for quote in quotes if (row := quote_to_stats(quote))]
        return rows
    except Exception:
        return []


def latest_market_stats(
    ticker: str,
    history: pd.DataFrame,
    source: str,
    live_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if live_stats:
        return live_stats

    profile = profile_for(ticker)
    df = history.tail(80).copy()
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    close = float(last["Close"])
    prev_close = float(prev["Close"]) if float(prev["Close"]) else close
    gain_pct = ((close - prev_close) / prev_close) * 100
    volume = float(last["Volume"])
    avg_volume = float(df["Volume"].iloc[:-1].tail(20).mean()) if len(df) > 22 else float(profile["volume"]) / float(profile["rvol"])
    rvol = volume / max(avg_volume, 1)

    return {
        "Ticker": ticker.strip().upper(),
        "Company": profile["company"],
        "Sector": profile["sector"],
        "Price": close,
        "Previous close": prev_close,
        "Daily gain %": gain_pct,
        "Volume": volume,
        "Average volume": avg_volume,
        "RVOL": rvol,
        "Float M": float(profile["float_m"]),
        "Catalyst": profile["catalyst"],
        "Data source": source,
        "Float source": "Learning estimate" if source == "Learning data" else "Profile estimate",
    }


def build_trade_plan(stats: dict[str, Any], history: pd.DataFrame) -> dict[str, Any]:
    close = history["Close"].astype(float)
    high = history["High"].astype(float)
    low = history["Low"].astype(float)
    price = float(stats["Price"])

    ema9 = float(close.ewm(span=9, adjust=False).mean().iloc[-1])
    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    atr = float((high - low).tail(14).mean())
    if not math.isfinite(atr) or atr <= 0:
        atr = max(price * 0.045, 0.1)

    buy_low = max(0.01, max(ema9, price - atr * 0.45))
    buy_high = max(buy_low * 1.01, price + atr * 0.12)
    entry_trigger = max(float(high.iloc[-1]) * 1.002, price * 1.01)
    stop = max(0.01, min(buy_low - atr * 0.65, price * 0.925))
    risk = max(entry_trigger - stop, price * 0.025)
    target1 = entry_trigger + risk * 1.5
    target2 = entry_trigger + risk * 2.4

    return {
        "EMA 9": ema9,
        "EMA 20": ema20,
        "ATR": atr,
        "Buy low": buy_low,
        "Buy high": buy_high,
        "Entry trigger price": entry_trigger,
        "Stop price": stop,
        "Target 1 price": target1,
        "Target 2 price": target2,
        "Buy zone": f"{money(buy_low)} - {money(buy_high)}",
        "Entry trigger": f"Break over {money(entry_trigger)}",
        "Stop": money(stop),
        "Target 1": money(target1),
        "Target 2": money(target2),
        "Risk/reward": round((target1 - entry_trigger) / max(entry_trigger - stop, 0.01), 2),
    }


def entry_confirmation_text(plan: dict[str, Any]) -> str:
    trigger = safe_float(plan.get("Entry trigger price"))
    if trigger is not None:
        return f"a break over {money(trigger)}"
    return str(plan.get("Entry trigger", "confirmation")).replace("Break over", "a break over")


def score_setup(stats: dict[str, Any], plan: dict[str, Any]) -> tuple[int, str, str, list[str], list[str]]:
    price = float(stats["Price"])
    gain = float(stats["Daily gain %"])
    float_m = float(stats["Float M"])
    rvol = float(stats["RVOL"])
    ema9 = float(plan["EMA 9"])
    ema20 = float(plan["EMA 20"])

    score = 0
    reasons: list[str] = []
    warnings: list[str] = []

    if DEFAULT_RULES["min_price"] <= price <= DEFAULT_RULES["max_price"]:
        score += 20
        reasons.append("Price is inside the $2 to $20 momentum range.")
    else:
        warnings.append("Price is outside the preferred $2 to $20 range.")

    if gain >= DEFAULT_RULES["min_gain_pct"]:
        score += 25
        reasons.append("Daily gain is above the 10% gapper threshold.")
    else:
        warnings.append("Daily gain has not cleared the 10% gapper threshold.")

    if float_m <= DEFAULT_RULES["max_float_m"]:
        score += 20
        reasons.append("Float estimate is under 10 million shares.")
    else:
        warnings.append("Float estimate is over 10 million shares.")

    if rvol >= DEFAULT_RULES["min_rvol"]:
        score += 20
        reasons.append("Relative volume is high versus its recent average.")
    elif rvol >= 2:
        score += 10
        warnings.append("RVOL is active, but below the preferred 3.0x level.")
    else:
        warnings.append("RVOL is light for this strategy.")

    if price > ema9 > ema20:
        score += 15
        reasons.append("Price is holding above short-term trend lines.")
    elif price > ema20:
        score += 8
        reasons.append("Price is still above the 20-day trend.")
    else:
        warnings.append("Trend is weak or below key moving averages.")

    if score >= 88:
        return score, "A+ momentum gapper", "High", reasons, warnings
    if score >= 74:
        return score, "Strong watch", "Medium-high", reasons, warnings
    if score >= 60:
        return score, "Watch only", "Medium", reasons, warnings
    return score, "Study setup", "Low", reasons, warnings


@st.cache_data(ttl=20, max_entries=300, show_spinner=False)
def analyze_ticker(
    ticker: str,
    period: str = "3mo",
    interval: str = "1d",
    prefer_live: bool = False,
) -> dict[str, Any]:
    ticker = ticker.strip().upper()
    history, source = load_history(ticker, period=period, interval=interval, prefer_live=prefer_live)
    live_stats = live_quote_stats(ticker) if prefer_live else None
    stats = latest_market_stats(ticker, history, source, live_stats=live_stats)
    plan = build_trade_plan(stats, history)
    score, setup, confidence, reasons, warnings = score_setup(stats, plan)
    fit = playbook_fit_label(stats, score)
    data_quality, _ = data_quality_badge(stats.get("Data source", source))
    status = live_status({**stats, **plan})

    return {
        **stats,
        **plan,
        "AI score": int(score),
        "Setup": setup,
        "Confidence": confidence,
        "Playbook fit": fit,
        "Data quality": data_quality,
        "Status": status,
        "Reasons": reasons,
        "Warnings": warnings,
        "Plan": (
            f"Watch {stats['Ticker']} for a clean hold inside {plan['Buy zone']} and only consider a "
            f"paper entry after {entry_confirmation_text(plan)}. Keep risk defined near {plan['Stop']}."
        ),
    }


def row_matches_rules(row: dict[str, Any], rules: dict[str, float]) -> bool:
    return (
        rules["min_price"] <= float(row["Price"]) <= rules["max_price"]
        and float(row["Daily gain %"]) >= rules["min_gain_pct"]
        and float(row["Float M"]) <= rules["max_float_m"]
        and float(row["RVOL"]) >= rules["min_rvol"]
    )


@st.cache_data(ttl=20, max_entries=80, show_spinner=False)
def run_scan(
    min_price: float,
    max_price: float,
    min_gain_pct: float,
    max_float_m: float,
    min_rvol: float,
    prefer_live: bool = False,
    include_learning: bool = True,
) -> pd.DataFrame:
    rules = {
        "min_price": float(min_price),
        "max_price": float(max_price),
        "min_gain_pct": float(min_gain_pct),
        "max_float_m": float(max_float_m),
        "min_rvol": float(min_rvol),
    }
    rows = []
    if prefer_live:
        live_rows = live_screener_rows(min_price, max_price, min_gain_pct)
        for row in live_rows:
            if not row_matches_rules(row, rules):
                continue
            history, _ = load_history(row["Ticker"], period="3mo", interval="1d", prefer_live=True)
            plan = build_trade_plan(row, history) if not history.empty else {}
            score, setup, confidence, reasons, warnings = score_setup(row, plan) if plan else (0, "Live watch", "Low", [], [])
            fit = playbook_fit_label(row, score)
            data_quality, _ = data_quality_badge(row.get("Data source"))
            status = live_status({**row, **plan}) if plan else "Watching"
            enriched = {
                **row,
                **plan,
                "AI score": int(score),
                "Setup": setup,
                "Confidence": confidence,
                "Playbook fit": fit,
                "Data quality": data_quality,
                "Status": status,
                "Reasons": reasons,
                "Warnings": warnings,
                "Plan": (
                    f"Watch {row['Ticker']} for a clean hold inside {plan.get('Buy zone', 'the pullback zone')} "
                    f"and only consider a paper entry after {entry_confirmation_text(plan)}."
                ),
            }
            rows.append(enriched)
            if len(rows) >= 12:
                break

    if (not prefer_live) or (not rows and include_learning):
        for profile in DEMO_PROFILES:
            analysis = analyze_ticker(profile["ticker"], prefer_live=False)
            if row_matches_rules(analysis, rules):
                rows.append(analysis)

    if not rows and include_learning:
        for profile in DEMO_PROFILES[:6]:
            rows.append(analyze_ticker(profile["ticker"], prefer_live=False))

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["AI score", "Daily gain %", "RVOL"], ascending=False).reset_index(drop=True)


@st.cache_data(ttl=86400, max_entries=3, show_spinner=False)
def sp500_tickers() -> list[str]:
    try:
        from bs4 import BeautifulSoup

        response = requests.get(SP500_SOURCE_URL, headers={"User-Agent": "Mozilla/5.0 MomentumScannerAI"}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"id": "constituents"})
        if table is None:
            return SP500_SAMPLE_TICKERS
        tickers = []
        for row in table.select("tbody tr"):
            first_cell = row.find("td")
            if first_cell is None:
                continue
            ticker = first_cell.get_text(strip=True).replace(".", "-").upper()
            if ticker:
                tickers.append(ticker)
        return tickers or SP500_SAMPLE_TICKERS
    except Exception:
        return SP500_SAMPLE_TICKERS


def market_scan_universe(presets: list[str], custom_tickers: str = "", include_etfs: bool = True) -> list[str]:
    tickers: list[str] = []
    if "Core movers" in presets:
        tickers.extend(CORE_MARKET_TICKERS)
    if "S&P 500" in presets or "S&P 500 sample" in presets:
        tickers.extend(sp500_tickers())
    if "Watchlist" in presets:
        tickers.extend(read_watchlist())
    if "All US stocks" in presets:
        full_universe, _ = full_us_market_universe(include_etfs=include_etfs, api_marker=finnhub_key_marker())
        tickers.extend(full_universe)
    for preset, values in GLOBAL_MARKET_WATCH.items():
        if preset in presets:
            tickers.extend(values)
    tickers.extend(clean_market_symbol(part) for part in custom_tickers.replace("\n", ",").split(",") if part.strip())
    return unique_symbols(tickers)


def ticker_batch(tickers: list[str], start_at: int, batch_size: int) -> list[str]:
    if not tickers:
        return []
    start = min(max(int(start_at), 0), max(len(tickers) - 1, 0))
    end = min(start + max(int(batch_size), 1), len(tickers))
    return tickers[start:end]


def next_batch_start(start_at: int, batch_size: int, total: int) -> int:
    if total <= 0:
        return 0
    next_start = int(start_at) + int(batch_size)
    return 0 if next_start >= total else next_start


def merge_market_scan_results(existing: pd.DataFrame, latest: pd.DataFrame) -> pd.DataFrame:
    frames = [frame for frame in [existing, latest] if isinstance(frame, pd.DataFrame) and not frame.empty]
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    if "Ticker" in combined.columns:
        combined = combined.drop_duplicates("Ticker", keep="last")
    sort_columns = [column for column in ["Daily gain %", "RVOL", "AI score"] if column in combined.columns]
    if sort_columns:
        combined = combined.sort_values(sort_columns, ascending=False)
    return combined.reset_index(drop=True)


@st.cache_data(ttl=30, max_entries=60, show_spinner=False)
def broad_market_scan(tickers: tuple[str, ...], max_names: int = 80) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for ticker in tickers[:max_names]:
        history, source = load_history(ticker, period="5d", interval="5m", prefer_live=True)
        live_stats = live_quote_stats(ticker)
        if history.empty and live_stats is None:
            continue
        stats = latest_market_stats(ticker, history, source, live_stats=live_stats)
        if history.empty:
            history, _ = load_history(ticker, period="3mo", interval="1d", prefer_live=False)
        plan = build_trade_plan(stats, history) if not history.empty else {}
        if plan:
            score, setup, confidence, reasons, warnings = score_setup(stats, plan)
        else:
            score, setup, confidence, reasons, warnings = 0, "Live watch", "Low", [], []
        rows.append(
            {
                **stats,
                **plan,
                "AI score": int(score),
                "Setup": setup,
                "Confidence": confidence,
                "Playbook fit": playbook_fit_label(stats, score),
                "Data quality": data_quality_badge(stats.get("Data source", source))[0],
                "Status": live_status({**stats, **plan}) if plan else "Watching",
                "Reasons": reasons,
                "Warnings": warnings,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["Daily gain %", "RVOL", "AI score"], ascending=False).reset_index(drop=True)


def scan_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "Ticker",
        "Playbook fit",
        "Company",
        "Status",
        "Price",
        "Daily gain %",
        "Float M",
        "RVOL",
        "AI score",
        "Setup",
        "Confidence",
        "Data quality",
        "Buy zone",
        "Entry trigger",
        "Stop",
        "Target 1",
        "Risk/reward",
        "Data source",
        "Float source",
        "Market state",
        "Quote time",
    ]
    return df[[column for column in columns if column in df.columns]]


def remember_selected_ticker(display_df: pd.DataFrame, event: Any) -> None:
    try:
        rows = list(event.selection.rows)
    except Exception:
        rows = []
    if not rows or "Ticker" not in display_df.columns:
        return
    ticker = str(display_df.iloc[rows[0]]["Ticker"]).upper()
    if ticker:
        st.session_state.selected_ticker = ticker
        st.caption(f"{ticker} selected for Charts and AI Coach.")


def show_scan_table(df: pd.DataFrame, key: str = "scan_table") -> None:
    if df.empty:
        st.info("No matches with the current filters.")
        return
    display_df = scan_columns(df)
    event = st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        key=key,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", pinned=True),
            "Playbook fit": st.column_config.TextColumn("Fit"),
            "Status": st.column_config.TextColumn("Status"),
            "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "Daily gain %": st.column_config.NumberColumn("Gain", format="%.1f%%"),
            "Float M": st.column_config.NumberColumn("Float", format="%.1fM"),
            "RVOL": st.column_config.NumberColumn("RVOL", format="%.1fx"),
            "AI score": st.column_config.ProgressColumn("AI score", min_value=0, max_value=100),
            "Risk/reward": st.column_config.NumberColumn("R/R", format="%.2f"),
        },
    )
    remember_selected_ticker(display_df, event)


def show_broad_market_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No market rows returned yet. Try a smaller preset or check your data key/network.")
        return
    columns = [
        "Ticker",
        "Playbook fit",
        "Company",
        "Status",
        "Price",
        "Daily gain %",
        "RVOL",
        "Volume",
        "AI score",
        "Data quality",
        "Entry trigger",
        "Stop",
        "Target 1",
        "Data source",
        "Quote time",
    ]
    display_df = df[[column for column in columns if column in df.columns]]
    event = st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        key="broad_market_table",
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", pinned=True),
            "Playbook fit": st.column_config.TextColumn("Fit"),
            "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "Daily gain %": st.column_config.NumberColumn("Gain", format="%.2f%%"),
            "RVOL": st.column_config.NumberColumn("RVOL", format="%.1fx"),
            "Volume": st.column_config.NumberColumn("Volume", format="compact"),
            "AI score": st.column_config.ProgressColumn("AI score", min_value=0, max_value=100),
        },
    )
    remember_selected_ticker(display_df, event)


def market_clock_frame() -> pd.DataFrame:
    rows = []
    now_utc = pd.Timestamp.now(tz="UTC")
    for item in MARKET_CLOCKS:
        local = now_utc.tz_convert(item["Timezone"])
        weekday_open = local.weekday() < 5
        rows.append(
            {
                "Market": item["Market"],
                "Local time": local.strftime("%a %I:%M %p"),
                "Typical session": item["Typical session"],
                "Weekday": "Open day" if weekday_open else "Weekend",
            }
        )
    return pd.DataFrame(rows)


def read_watchlist() -> list[str]:
    if WATCHLIST_FILE.exists():
        try:
            data = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
            return sorted({str(item).strip().upper() for item in data if str(item).strip()})
        except Exception:
            pass
    return ["BBAI", "KULR", "LUNR", "SOUN"]


def write_watchlist(tickers: list[str]) -> None:
    clean = sorted({ticker.strip().upper() for ticker in tickers if ticker.strip()})
    WATCHLIST_FILE.write_text(json.dumps(clean, indent=2), encoding="utf-8")


def empty_journal() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "Date",
            "Ticker",
            "Setup",
            "Entry",
            "Exit",
            "Stop",
            "Shares",
            "P/L $",
            "P/L %",
            "R multiple",
            "Notes",
        ]
    )


def read_journal() -> pd.DataFrame:
    if JOURNAL_FILE.exists():
        try:
            return pd.read_csv(JOURNAL_FILE)
        except Exception:
            pass
    return empty_journal()


def save_journal(df: pd.DataFrame) -> None:
    df.to_csv(JOURNAL_FILE, index=False)


def append_journal(row: dict[str, Any]) -> None:
    df = read_journal()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_journal(df)


def empty_orders() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "Created",
            "Status",
            "Ticker",
            "Side",
            "Order type",
            "Entry",
            "Stop",
            "Target 1",
            "Shares",
            "Risk $",
            "Reason",
        ]
    )


def read_orders() -> pd.DataFrame:
    if ORDERS_FILE.exists():
        try:
            return pd.read_csv(ORDERS_FILE)
        except Exception:
            pass
    return empty_orders()


def save_order(row: dict[str, Any]) -> None:
    df = read_orders()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(ORDERS_FILE, index=False)


def stage_order_from_analysis(analysis: dict[str, Any], risk_dollars: float = 25.0) -> dict[str, Any]:
    entry = safe_float(analysis.get("Entry trigger price"), safe_float(analysis.get("Price"), 0)) or 0
    stop = safe_float(analysis.get("Stop price"), max(entry * 0.95, 0.01)) or max(entry * 0.95, 0.01)
    risk_per_share = max(entry - stop, entry * 0.01, 0.01)
    shares = max(1, int(float(risk_dollars) // risk_per_share))
    label, reason = ai_action_summary(analysis)
    return {
        "Created": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
        "Status": "Staged",
        "Ticker": analysis.get("Ticker", ""),
        "Side": "Buy",
        "Order type": "Paper stop-limit plan",
        "Entry": round(entry, 4),
        "Stop": round(stop, 4),
        "Target 1": round(safe_float(analysis.get("Target 1 price"), entry) or entry, 4),
        "Shares": shares,
        "Risk $": round(shares * risk_per_share, 2),
        "Reason": f"{label}: {reason}",
    }


def approve_paper_order(order: dict[str, Any]) -> None:
    approved = {**order, "Status": "Approved paper order", "Created": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")}
    save_order(approved)
    append_journal(
        {
            "Date": date.today().isoformat(),
            "Ticker": approved["Ticker"],
            "Setup": "AI-approved paper order",
            "Entry": approved["Entry"],
            "Exit": approved["Entry"],
            "Stop": approved["Stop"],
            "Shares": approved["Shares"],
            "P/L $": 0,
            "P/L %": 0,
            "R multiple": 0,
            "Notes": approved["Reason"],
        }
    )


def journal_stats(df: pd.DataFrame) -> dict[str, float]:
    if df.empty:
        return {"trades": 0, "win_rate": 0.0, "total_pl": 0.0, "avg_r": 0.0}
    pl = pd.to_numeric(df["P/L $"], errors="coerce").fillna(0)
    r_mult = pd.to_numeric(df["R multiple"], errors="coerce").fillna(0)
    wins = int((pl > 0).sum())
    return {
        "trades": int(len(df)),
        "win_rate": wins / max(len(df), 1) * 100,
        "total_pl": float(pl.sum()),
        "avg_r": float(r_mult.mean()) if len(r_mult) else 0.0,
    }


def backtest_strategy(
    ticker: str,
    period: str,
    prefer_live: bool,
    min_gap_pct: float,
    min_rvol: float,
    hold_days: int,
) -> dict[str, Any]:
    history, source = load_history(ticker, period=period, prefer_live=prefer_live)
    df = history.copy()
    df["Prev close"] = df["Close"].shift(1)
    df["Gap %"] = ((df["Close"] - df["Prev close"]) / df["Prev close"]) * 100
    df["Avg volume"] = df["Volume"].shift(1).rolling(20).mean()
    df["RVOL"] = df["Volume"] / df["Avg volume"]
    df["EMA 9"] = df["Close"].ewm(span=9, adjust=False).mean()
    df["EMA 20"] = df["Close"].ewm(span=20, adjust=False).mean()

    trades = []
    for index in range(25, len(df) - hold_days):
        row = df.iloc[index]
        price_ok = 2 <= float(row["Close"]) <= 20
        signal = (
            price_ok
            and float(row["Gap %"]) >= min_gap_pct
            and float(row["RVOL"]) >= min_rvol
            and float(row["Close"]) > float(row["EMA 9"]) > float(row["EMA 20"])
        )
        if not signal:
            continue

        entry = max(float(row["Close"]), float(row["High"]) * 1.001)
        exit_row = df.iloc[index + hold_days]
        exit_price = float(exit_row["Close"])
        stop = max(0.01, float(row["Low"]) * 0.985)
        risk = max(entry - stop, entry * 0.02)
        trades.append(
            {
                "Date": df.index[index].date().isoformat(),
                "Entry": entry,
                "Exit": exit_price,
                "Stop": stop,
                "Gain %": (exit_price - entry) / entry * 100,
                "R multiple": (exit_price - entry) / risk,
                "RVOL": float(row["RVOL"]),
                "Gap %": float(row["Gap %"]),
            }
        )

    trades_df = pd.DataFrame(trades)
    if trades_df.empty:
        return {
            "source": source,
            "history": df,
            "trades": trades_df,
            "summary": {"Trades": 0, "Win rate": 0.0, "Average gain %": 0.0, "Average R": 0.0},
        }

    wins = (trades_df["Gain %"] > 0).sum()
    return {
        "source": source,
        "history": df,
        "trades": trades_df,
        "summary": {
            "Trades": int(len(trades_df)),
            "Win rate": float(wins / len(trades_df) * 100),
            "Average gain %": float(trades_df["Gain %"].mean()),
            "Average R": float(trades_df["R multiple"].mean()),
        },
    }


def theme_palette(mode: str | None = None) -> dict[str, str]:
    mode = (mode or st.session_state.get("display_mode", "Dark")).lower()
    if mode == "light":
        return {
            "app_bg": "#F7F8FA",
            "panel": "#FFFFFF",
            "panel_alt": "#F1F5F9",
            "border": "#D9E0E8",
            "text": "#101418",
            "muted": "#475569",
            "muted_soft": "#64748B",
            "shadow": "rgba(15, 23, 42, 0.08)",
            "hero": "linear-gradient(135deg, #FFFFFF 0%, #F1F8F4 58%, #EFF6FF 100%)",
            "up": "#008F2D",
            "up_bright": "#00A854",
            "down": "#D92D20",
            "blue": "#2563EB",
            "cyan": "#0891B2",
            "violet": "#7C3AED",
            "orange": "#B45309",
            "grid": "#DDE5EE",
        }
    return {
        "app_bg": "#090C10",
        "panel": "#111820",
        "panel_alt": "#0F151D",
        "border": "#293546",
        "text": "#F3F7FA",
        "muted": "#B7C2D0",
        "muted_soft": "#A8B3C2",
        "shadow": "rgba(0, 0, 0, 0.28)",
        "hero": "linear-gradient(135deg, #121A24 0%, #0B1118 72%)",
        "up": "#00C805",
        "up_bright": "#00C805",
        "down": "#FF375F",
        "blue": "#38BDF8",
        "cyan": "#22D3EE",
        "violet": "#A78BFA",
        "orange": "#F59E0B",
        "grid": "#223041",
    }


def display_mode_control() -> str:
    options = ["Dark", "Light"]
    default = st.session_state.get("display_mode", "Dark")
    index = options.index(default) if default in options else 0
    with st.sidebar:
        mode = st.selectbox(
            "Display mode",
            options,
            index=index,
            key="display_mode",
        )
    return str(mode or default)


def apply_style(mode: str | None = None) -> None:
    palette = theme_palette(mode)
    st.markdown(
        f"""
        <style>
        :root {{
            --msa-app-bg: {palette["app_bg"]};
            --msa-panel: {palette["panel"]};
            --msa-panel-alt: {palette["panel_alt"]};
            --msa-border: {palette["border"]};
            --msa-text: {palette["text"]};
            --msa-muted: {palette["muted"]};
            --msa-muted-soft: {palette["muted_soft"]};
            --msa-shadow: {palette["shadow"]};
            --msa-up: {palette["up"]};
            --msa-down: {palette["down"]};
            --msa-blue: {palette["blue"]};
            --msa-orange: {palette["orange"]};
        }}
        .stApp {{background: var(--msa-app-bg);}}
        .block-container {{max-width: 1320px; padding-top: 1.15rem; padding-bottom: 3rem;}}
        h1, h2, h3 {{letter-spacing: 0; color: var(--msa-text);}}
        [data-testid="stMetric"] {{
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            padding: 15px 16px;
            box-shadow: 0 18px 36px var(--msa-shadow);
        }}
        div[data-testid="stMetricLabel"] {{color: var(--msa-muted-soft);}}
        div[data-testid="stMetricValue"] {{font-weight: 750; color: var(--msa-text);}}
        div[data-testid="stMetricDelta"] {{font-weight: 650;}}
        div[data-testid="stDataFrame"] {{border: 1px solid var(--msa-border); border-radius: 8px; overflow: hidden;}}
        .stAlert {{border-radius: 8px;}}
        .msa-hero {{
            position: relative;
            overflow: hidden;
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            padding: 26px 28px;
            background:
                radial-gradient(circle at 18% -10%, rgba(0, 200, 5, 0.20), transparent 30%),
                radial-gradient(circle at 85% 20%, rgba(56, 189, 248, 0.18), transparent 34%),
                {palette["hero"]};
            box-shadow: 0 24px 60px var(--msa-shadow);
        }}
        .msa-hero:after {{
            content: "";
            position: absolute;
            inset: auto -20% -48px -20%;
            height: 96px;
            background:
                linear-gradient(90deg, transparent 0%, rgba(0, 168, 84, 0.25) 35%, rgba(37, 99, 235, 0.22) 55%, transparent 100%);
            animation: msa-pulse 5.5s ease-in-out infinite;
            transform: skewY(-3deg);
        }}
        @keyframes msa-pulse {{
            0%, 100% {{transform: translateX(-18%) skewY(-3deg); opacity: .55;}}
            50% {{transform: translateX(18%) skewY(-3deg); opacity: .95;}}
        }}
        .msa-hero h1 {{margin: 0 0 8px 0; font-size: 2.5rem; line-height: 1.05;}}
        .msa-hero p {{max-width: 820px; margin: 0; color: var(--msa-muted); font-size: 1.02rem;}}
        .msa-status-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 12px;
            margin: 14px 0 16px 0;
        }}
        .msa-status-card {{
            border: 1px solid var(--msa-border);
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 18px 36px var(--msa-shadow);
        }}
        .msa-label {{font-size: .78rem; color: var(--msa-muted-soft); text-transform: uppercase; letter-spacing: .04em;}}
        .msa-value {{font-size: 1.4rem; font-weight: 750; color: var(--msa-text); margin-top: 4px;}}
        .msa-good {{border-left: 4px solid var(--msa-up);}}
        .msa-hot {{border-left: 4px solid var(--msa-orange);}}
        .msa-calm {{border-left: 4px solid var(--msa-blue);}}
        .msa-danger {{border-left: 4px solid var(--msa-down);}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def dashboard_hero() -> None:
    st.markdown(
        """
        <div class="msa-hero">
            <h1>MomentumScannerAI</h1>
            <p>Live scanners, chart levels, stock news, paper-trade planning, and a learning system for studying momentum without guessing.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_cards(cards: list[tuple[str, str, str]]) -> None:
    parts = ['<div class="msa-status-row">']
    for label, value, tone in cards:
        parts.append(
            f'<div class="msa-status-card msa-{html.escape(tone)}"><div class="msa-label">{html.escape(label)}</div><div class="msa-value">{html.escape(value)}</div></div>'
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def header(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.caption(markdown_text(subtitle))
    st.caption(
        "Educational paper-trading tool. Verify live data, news, float, halts, and risk before making real trades. "
        "This is not financial advice."
    )


def render_setup_checks(analysis: dict[str, Any]) -> None:
    passed, total = setup_completion(analysis)
    st.markdown(f"**Setup checks: {passed}/{total} ready**")
    with st.container(horizontal=True):
        for name, ok, detail in setup_check_items(analysis):
            st.badge(
                f"{name}: {detail}",
                icon=":material/check_circle:" if ok else ":material/radio_button_unchecked:",
                color="green" if ok else "orange",
            )


def default_scan(prefer_live: bool = True) -> pd.DataFrame:
    return run_scan(
        DEFAULT_RULES["min_price"],
        DEFAULT_RULES["max_price"],
        DEFAULT_RULES["min_gain_pct"],
        DEFAULT_RULES["max_float_m"],
        DEFAULT_RULES["min_rvol"],
        prefer_live=prefer_live,
        include_learning=True,
    )


def render_plan_card(analysis: dict[str, Any]) -> None:
    with st.container(border=True):
        top = st.columns([1.1, 1, 1, 1])
        top[0].metric(analysis["Ticker"], analysis["Setup"], analysis["Confidence"])
        top[1].metric("Price", money(analysis["Price"]), pct(analysis["Daily gain %"]))
        top[2].metric("RVOL", f"{analysis['RVOL']:.1f}x", f"Float {analysis['Float M']:.1f}M")
        top[3].metric("AI score", f"{analysis['AI score']}/100", analysis["Data source"])
        fit = analysis.get("Playbook fit", playbook_fit_label(analysis, analysis.get("AI score")))
        data_quality, data_color = data_quality_badge(analysis.get("Data source"))
        with st.container(horizontal=True):
            st.badge(str(fit), icon=":material/filter_alt:", color=playbook_fit_color(str(fit)))
            st.badge(data_quality, icon=":material/database:", color=data_color)
        st.caption(
            f"Source: {analysis.get('Data source', 'n/a')} | "
            f"Market: {analysis.get('Market state', 'n/a')} | "
            f"Quote time: {analysis.get('Quote time', 'n/a')} | "
            f"Float: {analysis.get('Float source', 'estimate')}"
        )

        render_setup_checks(analysis)
        st.markdown(markdown_text(analysis["Plan"]))
        levels = st.columns(4)
        levels[0].metric("Buy zone", analysis["Buy zone"])
        levels[1].metric("Entry", analysis["Entry trigger"])
        levels[2].metric("Stop", analysis["Stop"])
        levels[3].metric("Targets", f"{analysis['Target 1']} / {analysis['Target 2']}")

        reason_col, warning_col = st.columns(2)
        with reason_col:
            st.markdown("**Why it is on watch**")
            for reason in analysis["Reasons"]:
                st.markdown(markdown_text(f"- {reason}"))
        with warning_col:
            st.markdown("**Risk checks**")
            if analysis["Warnings"]:
                for warning in analysis["Warnings"]:
                    st.markdown(markdown_text(f"- {warning}"))
            else:
                st.write("- No major rule warnings in this model.")


def ai_action_summary(analysis: dict[str, Any]) -> tuple[str, str]:
    status = live_status(analysis)
    ticker = analysis.get("Ticker", "This ticker")
    price = money(safe_float(analysis.get("Price")))
    entry = str(analysis.get("Entry trigger", "the trigger"))
    entry_level = entry.removeprefix("Break over ").strip()
    entry_phrase = f"over {entry_level}" if entry_level and entry_level != entry else entry
    buy_zone = analysis.get("Buy zone", "the buy zone")
    stop = analysis.get("Stop", "the stop")
    target = analysis.get("Target 1", "target 1")
    score = safe_float(analysis.get("AI score"), 0) or 0
    warnings = [str(warning) for warning in analysis.get("Warnings", [])]
    major_rule_misses = sum(
        any(fragment in warning for fragment in ["outside the preferred", "over 10 million", "not cleared the 10%"])
        for warning in warnings
    )

    if score < 50 or major_rule_misses >= 2:
        return (
            "Study only",
            f"{ticker} is useful to watch, but it does not cleanly match the low-priced momentum playbook right now. Treat it as market context unless the scanner rules, news, volume, and risk line up.",
        )

    if status == "Breakout trigger":
        return (
            "Trigger active",
            f"{ticker} is at or above the planned trigger. For paper trading, only consider it if volume is still expanding and risk to {stop} is acceptable. First target is {target}.",
        )
    if status == "In buy zone":
        return (
            "In buy zone",
            f"{ticker} is trading around {price}, inside the planned buy zone of {buy_zone}. Wait for confirmation {entry_phrase}; do not buy just because it touched the zone.",
        )
    if status == "Near buy zone":
        return (
            "Getting close",
            f"{ticker} is near the plan area. Let it come to you, then look for a clean hold and a break {entry_phrase}.",
        )
    if status == "Below stop":
        return (
            "Plan invalid",
            f"{ticker} is below the planned stop. For this strategy, that means stand down and wait for a new setup.",
        )
    return (
        "Watch only",
        f"{ticker} is not at the ideal action point yet. The current plan is buy zone {buy_zone}, confirmation {entry_phrase}, stop {stop}, and target {target}.",
    )


def wait_coaching(analysis: dict[str, Any], label: str) -> list[str]:
    warnings = [str(warning) for warning in analysis.get("Warnings", [])]
    guidance: list[str] = []
    if label == "Study only":
        guidance.append("Use it for context or learning, not as a primary low-float momentum idea.")
    if label == "Watch only":
        guidance.append("Wait for price to come into the buy zone or break the trigger with real volume.")
    if label == "Plan invalid":
        guidance.append("Do not force a new entry from this plan. Rebuild the setup after a fresh base forms.")
    if any("10% gapper" in warning for warning in warnings):
        guidance.append("Skip the aggressive gapper playbook until the daily move and volume confirm demand.")
    if any("over 10 million" in warning for warning in warnings):
        guidance.append("Treat this as a slower context stock unless it has exceptional volume and a fresh catalyst.")
    if any("RVOL" in warning or "volume" in warning.lower() for warning in warnings):
        guidance.append("Volume is not strong enough yet; avoid guessing before buyers show up.")
    if not guidance:
        guidance.append("Keep the stop and target written before any paper order is approved.")
    return list(dict.fromkeys(guidance))[:4]


def render_ai_decision_panel(analysis: dict[str, Any]) -> None:
    label, message = ai_action_summary(analysis)
    status = live_status(analysis)
    color = "gray"
    if label == "Plan invalid":
        color = "red"
    elif label == "Study only":
        color = "gray"
    elif status in {"Breakout trigger", "In buy zone"}:
        color = "green"
    elif status in {"Near buy zone", "Momentum active"}:
        color = "orange"
    with st.container(border=True):
        st.badge(label, icon=":material/psychology:", color=color)
        st.markdown(markdown_text(message))
        if label in {"Study only", "Watch only", "Plan invalid"}:
            st.markdown("**Best next action**")
            for item in wait_coaching(analysis, label):
                st.write(f"- {item}")
        st.caption("This is a paper-trading decision aid. It does not execute orders and it is not financial advice.")


def rebuild_analysis_from_history(
    ticker: str,
    history: pd.DataFrame,
    source: str,
    prefer_live: bool,
) -> dict[str, Any]:
    live_stats = live_quote_stats(ticker) if prefer_live else None
    stats = latest_market_stats(ticker, history, source, live_stats=live_stats)
    plan = build_trade_plan(stats, history)
    score, setup, confidence, reasons, warnings = score_setup(stats, plan)
    fit = playbook_fit_label(stats, score)
    data_quality, _ = data_quality_badge(stats.get("Data source", source))
    status = live_status({**stats, **plan})
    return {
        **stats,
        **plan,
        "AI score": int(score),
        "Setup": setup,
        "Confidence": confidence,
        "Playbook fit": fit,
        "Data quality": data_quality,
        "Status": status,
        "Reasons": reasons,
        "Warnings": warnings,
        "Plan": (
            f"Watch {stats['Ticker']} for a clean hold inside {plan['Buy zone']} and only consider a "
            f"paper entry after {entry_confirmation_text(plan)}. Keep risk defined near {plan['Stop']}."
        ),
    }


def render_plotly_trading_chart(
    chart_df: pd.DataFrame,
    analysis: dict[str, Any],
    current_price: float,
    height: int,
) -> None:
    if go is None or make_subplots is None:
        return

    chart_height = max(height + 280, 760)
    palette = theme_palette()
    is_light = st.session_state.get("display_mode", "Dark") == "Light"
    chart_bg = palette["app_bg"]
    panel_bg = palette["panel"]
    grid = palette["grid"]
    text = palette["text"]
    muted = palette["muted_soft"]
    up = palette["up_bright"]
    down = palette["down"]
    show_ema9 = bool(st.session_state.get("chart_layer_ema9", True))
    show_ema20 = bool(st.session_state.get("chart_layer_ema20", True))
    show_vwap = bool(st.session_state.get("chart_layer_vwap", True))
    show_buy_zone = bool(st.session_state.get("chart_layer_buy_zone", True))
    show_plan_levels = bool(st.session_state.get("chart_layer_plan_levels", True))
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.018,
        row_heights=[0.76, 0.24],
    )

    fig.add_trace(
        go.Candlestick(
            x=chart_df["Time"],
            open=chart_df["Open"],
            high=chart_df["High"],
            low=chart_df["Low"],
            close=chart_df["Close"],
            name="Candles",
            increasing=dict(line=dict(color=up, width=1.35), fillcolor=up),
            decreasing=dict(line=dict(color=down, width=1.35), fillcolor=down),
            whiskerwidth=0.65,
        ),
        row=1,
        col=1,
    )

    line_specs = []
    if show_ema9:
        line_specs.append(("EMA 9", palette["blue"], 1.7))
    if show_ema20:
        line_specs.append(("EMA 20", palette["violet"], 1.7))
    if show_vwap:
        line_specs.append(("VWAP", palette["orange"], 2.1))

    for line_name, color, width in line_specs:
        fig.add_trace(
            go.Scatter(
                x=chart_df["Time"],
                y=chart_df[line_name],
                mode="lines",
                line=dict(color=color, width=width),
                name=line_name,
                hovertemplate=f"{line_name}: $%{{y:.2f}}<extra></extra>",
            ),
            row=1,
            col=1,
        )

    volume_colors = np.where(
        chart_df["Close"] >= chart_df["Open"],
        "rgba(0, 200, 5, 0.58)" if not is_light else "rgba(0, 143, 45, 0.55)",
        "rgba(255, 55, 95, 0.58)" if not is_light else "rgba(217, 45, 32, 0.50)",
    )
    fig.add_trace(
        go.Bar(
            x=chart_df["Time"],
            y=chart_df["Volume"],
            marker_color=volume_colors,
            name="Volume",
            hovertemplate="Volume: %{y:,.0f}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    start_time = chart_df["Time"].iloc[0]
    end_time = chart_df["Time"].iloc[-1]
    buy_low = safe_float(analysis.get("Buy low"))
    buy_high = safe_float(analysis.get("Buy high"))
    if show_buy_zone and buy_low is not None and buy_high is not None:
        fig.add_shape(
            type="rect",
            x0=start_time,
            x1=end_time,
            y0=buy_low,
            y1=buy_high,
            fillcolor="rgba(34, 211, 238, 0.14)" if not is_light else "rgba(8, 145, 178, 0.12)",
            line=dict(width=0),
            layer="below",
            row=1,
            col=1,
        )

    def add_level(label: str, value: Any, color: str, dash: str = "dot") -> None:
        price = safe_float(value)
        if price is None:
            return
        fig.add_hline(
            y=price,
            line_color=color,
            line_dash=dash,
            line_width=1.2,
            annotation_text=f"{label} {money(price)}",
            annotation_position="top right",
            annotation_font_color=color,
            annotation_bgcolor="rgba(9, 12, 16, 0.86)" if not is_light else "rgba(255, 255, 255, 0.90)",
            annotation_bordercolor=color,
            row=1,
            col=1,
        )

    if show_plan_levels:
        add_level("Current", current_price, text, "solid")
        add_level("Buy low", analysis.get("Buy low"), palette["cyan"])
        add_level("Buy high", analysis.get("Buy high"), palette["cyan"])
        add_level("Stop", analysis.get("Stop price"), down)
        add_level("Target 1", analysis.get("Target 1 price"), up)
        add_level("Previous close", analysis.get("Previous close"), muted)

    fig.update_layout(
        height=chart_height,
        margin=dict(l=8, r=72, t=40, b=8),
        template="plotly_white" if is_light else "plotly_dark",
        paper_bgcolor=chart_bg,
        plot_bgcolor=panel_bg,
        font=dict(color=text, family="Inter, Arial, sans-serif", size=12),
        dragmode="pan",
        hovermode="x unified",
        bargap=0,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(255, 255, 255, 0.78)" if is_light else "rgba(9, 12, 16, 0.70)",
            bordercolor=palette["border"],
            borderwidth=1,
        ),
        hoverlabel=dict(bgcolor=palette["panel"], bordercolor=palette["border"], font_color=text),
        uirevision=f"{analysis.get('Ticker', 'chart')}-trading-chart",
        xaxis_rangeslider_visible=False,
        modebar=dict(bgcolor="rgba(9, 12, 16, 0)" if not is_light else "rgba(255, 255, 255, 0)", color=muted, activecolor=up),
    )
    fig.update_xaxes(
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikecolor=muted,
        spikethickness=1,
        showline=True,
        linecolor=palette["border"],
        gridcolor=grid,
        zeroline=False,
        rangeslider_visible=False,
        row=1,
        col=1,
    )
    fig.update_xaxes(
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikecolor=muted,
        spikethickness=1,
        showline=True,
        linecolor=palette["border"],
        gridcolor=grid,
        zeroline=False,
        rangeslider_visible=False,
        row=2,
        col=1,
    )
    visible_high = float(chart_df["High"].max())
    visible_low = float(chart_df["Low"].min())
    pad = max((visible_high - visible_low) * 0.08, max(current_price * 0.004, 0.03))
    volume_max = max(float(chart_df["Volume"].max()), 1.0)
    fig.update_yaxes(
        title_text="Price",
        fixedrange=False,
        side="right",
        showgrid=True,
        gridcolor=grid,
        zeroline=False,
        range=[visible_low - pad, visible_high + pad],
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text="Volume",
        fixedrange=False,
        side="right",
        showgrid=True,
        gridcolor=grid,
        zeroline=False,
        range=[0, volume_max * 1.18],
        row=2,
        col=1,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "doubleClick": "reset+autosize",
            "modeBarButtonsToAdd": ["drawline", "drawrect", "eraseshape"],
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            "displaylogo": False,
        },
    )


def render_candlestick_chart(
    history: pd.DataFrame,
    analysis: dict[str, Any],
    height: int = 470,
    max_candles: int | None = 180,
) -> None:
    if history.empty:
        st.info("No chart data available for this ticker.")
        return

    if max_candles:
        chart_df = history.tail(max_candles).copy()
    else:
        chart_df = history.tail(900).copy()
    chart_df["EMA 9"] = chart_df["Close"].ewm(span=9, adjust=False).mean()
    chart_df["EMA 20"] = chart_df["Close"].ewm(span=20, adjust=False).mean()
    typical_price = (chart_df["High"] + chart_df["Low"] + chart_df["Close"]) / 3
    cumulative_volume = chart_df["Volume"].replace(0, np.nan).cumsum()
    chart_df["VWAP"] = (typical_price * chart_df["Volume"]).cumsum() / cumulative_volume
    chart_df["VWAP"] = chart_df["VWAP"].ffill().bfill()
    chart_df["Time"] = chart_df.index
    chart_df["Direction"] = np.where(chart_df["Close"] >= chart_df["Open"], "Up", "Down")
    chart_df["Body low"] = chart_df[["Open", "Close"]].min(axis=1)
    chart_df["Body high"] = chart_df[["Open", "Close"]].max(axis=1)
    chart_df["Volume color"] = chart_df["Direction"]

    last = chart_df.iloc[-1]
    candle_delta = ((float(last["Close"]) - float(last["Open"])) / max(float(last["Open"]), 0.01)) * 100
    range_high = float(chart_df["High"].max())
    range_low = float(chart_df["Low"].min())
    current_price = float(last["Close"])
    latest_vwap = float(last["VWAP"]) if math.isfinite(float(last["VWAP"])) else current_price

    metric_cols = st.columns(4)
    metric_cols[0].metric("Last candle", money(current_price), pct(candle_delta), border=True)
    metric_cols[1].metric("Range high", money(range_high), border=True)
    metric_cols[2].metric("Range low", money(range_low), border=True)
    metric_cols[3].metric("VWAP", money(latest_vwap), border=True)

    candle_size = 13 if len(chart_df) <= 90 else 9 if len(chart_df) <= 180 else 6 if len(chart_df) <= 390 else 3

    if go is not None and make_subplots is not None:
        render_plotly_trading_chart(chart_df, analysis, current_price, height)
        return

    base = alt.Chart(chart_df).encode(
        x=alt.X("Time:T", title="Time"),
        color=alt.Color(
            "Direction:N",
            scale=alt.Scale(domain=["Up", "Down"], range=["#059669", "#dc2626"]),
            legend=None,
        ),
    )
    tooltip = [
        alt.Tooltip("Time:T", title="Time", format="%b %d, %I:%M %p"),
        alt.Tooltip("Open:Q", title="Open", format="$,.2f"),
        alt.Tooltip("High:Q", title="High", format="$,.2f"),
        alt.Tooltip("Low:Q", title="Low", format="$,.2f"),
        alt.Tooltip("Close:Q", title="Close", format="$,.2f"),
        alt.Tooltip("VWAP:Q", title="VWAP", format="$,.2f"),
        alt.Tooltip("Volume:Q", title="Volume", format=",.0f"),
    ]

    wick = base.mark_rule(strokeWidth=1.2).encode(
        y=alt.Y("Low:Q", title="Price"),
        y2="High:Q",
        tooltip=tooltip,
    )
    candle = base.mark_bar(size=candle_size).encode(
        y="Body low:Q",
        y2="Body high:Q",
        tooltip=tooltip,
    )

    overlay_frame = chart_df[["Time", "EMA 9", "EMA 20", "VWAP"]].melt("Time", var_name="Line", value_name="Price")
    ema_chart = (
        alt.Chart(overlay_frame)
        .mark_line(strokeWidth=1.7)
        .encode(
            x="Time:T",
            y="Price:Q",
            color=alt.Color(
                "Line:N",
                scale=alt.Scale(domain=["EMA 9", "EMA 20", "VWAP"], range=["#2563eb", "#7c3aed", "#f59e0b"]),
            ),
            tooltip=[
                alt.Tooltip("Time:T", title="Time", format="%b %d, %I:%M %p"),
                alt.Tooltip("Line:N", title="Line"),
                alt.Tooltip("Price:Q", title="Price", format="$,.2f"),
            ],
        )
    )

    start_time = chart_df["Time"].min()
    end_time = chart_df["Time"].max()
    buy_low = safe_float(analysis.get("Buy low"))
    buy_high = safe_float(analysis.get("Buy high"))
    band = alt.Chart(pd.DataFrame())
    if buy_low is not None and buy_high is not None:
        band = (
            alt.Chart(pd.DataFrame([{"Start": start_time, "End": end_time, "Low": buy_low, "High": buy_high}]))
            .mark_rect(color="#0891b2", opacity=0.11)
            .encode(x="Start:T", x2="End:T", y="Low:Q", y2="High:Q")
        )

    levels = pd.DataFrame(
        [
            {"Level": "Buy low", "Price": analysis.get("Buy low")},
            {"Level": "Buy high", "Price": analysis.get("Buy high")},
            {"Level": "Stop", "Price": analysis.get("Stop price")},
            {"Level": "Target 1", "Price": analysis.get("Target 1 price")},
            {"Level": "Current", "Price": current_price},
            {"Level": "Previous close", "Price": analysis.get("Previous close")},
        ]
    ).dropna()
    levels["Start"] = start_time
    levels["End"] = end_time
    level_chart = (
        alt.Chart(levels)
        .mark_rule(strokeDash=[5, 4], strokeWidth=1.2)
        .encode(
            y="Price:Q",
            color=alt.Color(
                "Level:N",
                scale=alt.Scale(
                    domain=["Buy low", "Buy high", "Stop", "Target 1", "Current", "Previous close"],
                    range=["#0891b2", "#0891b2", "#dc2626", "#16a34a", "#111827", "#6b7280"],
                ),
            ),
            tooltip=[alt.Tooltip("Level:N"), alt.Tooltip("Price:Q", format="$,.2f")],
        )
    )

    price_chart = (band + wick + candle + ema_chart + level_chart).properties(height=height).interactive()
    price_chart = price_chart.resolve_scale(color="independent")
    st.altair_chart(price_chart, width="stretch")

    volume_chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("Time:T", title="Time"),
            y=alt.Y("Volume:Q", title="Volume"),
            color=alt.Color(
                "Volume color:N",
                scale=alt.Scale(domain=["Up", "Down"], range=["#34d399", "#f87171"]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Time:T", title="Time", format="%b %d, %I:%M %p"),
                alt.Tooltip("Volume:Q", title="Volume", format=",.0f"),
                alt.Tooltip("Close:Q", title="Close", format="$,.2f"),
            ],
        )
        .properties(height=170)
    )
    st.altair_chart(volume_chart, width="stretch")


def render_chart_panel(
    ticker: str,
    period: str,
    interval: str,
    prefer_live: bool,
    max_candles: int | None = 180,
) -> None:
    analysis = analyze_ticker(ticker, period=period, interval=interval, prefer_live=prefer_live)
    history, source = load_history(ticker, period=period, interval=interval, prefer_live=prefer_live)
    if prefer_live and source == "Learning data":
        try:
            live_history = yahoo_chart_api_history(ticker, period=period, interval=interval, prepost=True)
            if not live_history.empty and len(live_history) >= 5:
                history = live_history
                source = f"Yahoo Finance API {interval}"
                print(f"[chart-panel] direct live retry recovered {ticker} {period}/{interval}: {len(history)} bars", flush=True)
            else:
                print(f"[chart-panel] direct live retry returned no usable bars for {ticker} {period}/{interval}", flush=True)
        except Exception as exc:
            print(f"[chart-panel] direct live retry failed for {ticker} {period}/{interval}: {exc}", flush=True)
    if prefer_live and source != "Learning data" and analysis.get("Data source") == "Learning data":
        analysis = rebuild_analysis_from_history(ticker, history, source, prefer_live=True)

    chart_quality, chart_color = data_quality_badge(source)
    st.badge(f"Chart source: {chart_quality}", icon=":material/candlestick_chart:", color=chart_color)
    if prefer_live and source == "Learning data":
        st.warning(
            "The live chart feed did not return enough candles, so this view is showing learning fallback data.",
            icon=":material/wifi_off:",
        )

    render_ai_decision_panel(analysis)
    render_plan_card(analysis)
    render_candlestick_chart(history, analysis, max_candles=max_candles)
    st.caption(
        f"Chart source: {source}. Last screen refresh: {datetime.now().strftime('%I:%M:%S %p')}. "
        "Free Yahoo data can be real-time or delayed depending on exchange and availability."
    )
    with st.expander(f":material/article: Latest {ticker.upper()} news", expanded=True):
        render_news_items(finnhub_company_news(ticker, days=5, limit=5))


@st.fragment(run_every=f"{LIVE_REFRESH_SECONDS}s")
def auto_refresh_chart_panel(
    ticker: str,
    period: str,
    interval: str,
    prefer_live: bool,
    max_candles: int | None = 180,
) -> None:
    render_chart_panel(ticker, period, interval, prefer_live, max_candles=max_candles)


def live_status(analysis: dict[str, Any]) -> str:
    price = safe_float(analysis.get("Price"))
    buy_low = safe_float(analysis.get("Buy low"))
    buy_high = safe_float(analysis.get("Buy high"))
    entry = safe_float(analysis.get("Entry trigger price"))
    stop = safe_float(analysis.get("Stop price"))
    gain = safe_float(analysis.get("Daily gain %"), 0) or 0
    rvol = safe_float(analysis.get("RVOL"), 0) or 0

    if price is None:
        return "No quote"
    if stop is not None and price <= stop:
        return "Below stop"
    if entry is not None and price >= entry:
        return "Breakout trigger"
    if buy_low is not None and buy_high is not None and buy_low <= price <= buy_high:
        return "In buy zone"
    if buy_low is not None and price < buy_low and ((buy_low - price) / max(buy_low, 0.01)) <= 0.03:
        return "Near buy zone"
    if gain >= 10 and rvol >= 3:
        return "Momentum active"
    return "Watching"


def tracker_row(analysis: dict[str, Any], track_type: str) -> dict[str, Any]:
    price = safe_float(analysis.get("Price"))
    entry = safe_float(analysis.get("Entry trigger price"))
    stop = safe_float(analysis.get("Stop price"))
    target = safe_float(analysis.get("Target 1 price"))
    data_quality, _ = data_quality_badge(analysis.get("Data source"))
    return {
        "Track": track_type,
        "Ticker": analysis.get("Ticker"),
        "Status": live_status(analysis),
        "Playbook fit": analysis.get("Playbook fit", playbook_fit_label(analysis, analysis.get("AI score"))),
        "Price": price,
        "Daily gain %": safe_float(analysis.get("Daily gain %"), 0) or 0,
        "RVOL": safe_float(analysis.get("RVOL"), 0) or 0,
        "Volume": safe_float(analysis.get("Volume"), 0) or 0,
        "Float M": safe_float(analysis.get("Float M"), 0) or 0,
        "Entry": entry,
        "Stop": stop,
        "Target 1": target,
        "Distance to entry %": ((entry - price) / price * 100) if entry and price else None,
        "Risk to stop %": ((price - stop) / price * 100) if stop and price else None,
        "Data quality": data_quality,
        "Data source": analysis.get("Data source", "n/a"),
        "Quote time": analysis.get("Quote time", "n/a"),
    }


@st.cache_data(ttl=20, max_entries=50, show_spinner=False)
def live_tracker_frame(tickers: tuple[str, ...], include_scan: bool = True) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    if include_scan:
        scan = run_scan(
            DEFAULT_RULES["min_price"],
            DEFAULT_RULES["max_price"],
            DEFAULT_RULES["min_gain_pct"],
            DEFAULT_RULES["max_float_m"],
            DEFAULT_RULES["min_rvol"],
            prefer_live=True,
            include_learning=False,
        )
        for item in scan.head(20).to_dict("records"):
            ticker = str(item.get("Ticker", "")).upper()
            if ticker:
                rows.append(tracker_row(item, "Scanner"))
                seen.add(ticker)

    for ticker in tickers:
        clean_ticker = ticker.strip().upper()
        if not clean_ticker:
            continue
        analysis = analyze_ticker(clean_ticker, period="5d", interval="5m", prefer_live=True)
        track_type = "Scanner + Watchlist" if clean_ticker in seen else "Watchlist"
        rows.append(tracker_row(analysis, track_type))

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    status_rank = {
        "Breakout trigger": 0,
        "In buy zone": 1,
        "Near buy zone": 2,
        "Momentum active": 3,
        "Watching": 4,
        "Below stop": 5,
        "No quote": 6,
    }
    df["_rank"] = df["Status"].map(status_rank).fillna(9)
    return df.sort_values(["_rank", "Daily gain %", "RVOL"], ascending=[True, False, False]).drop(columns=["_rank"])


def show_tracker_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No live rows returned yet. Yahoo may be rate-limiting or the current filters may be too tight.")
        return

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", pinned=True),
            "Status": st.column_config.TextColumn("Status"),
            "Playbook fit": st.column_config.TextColumn("Fit"),
            "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "Daily gain %": st.column_config.NumberColumn("Gain", format="%.1f%%"),
            "RVOL": st.column_config.NumberColumn("RVOL", format="%.1fx"),
            "Volume": st.column_config.NumberColumn("Volume", format="compact"),
            "Float M": st.column_config.NumberColumn("Float", format="%.1fM"),
            "Entry": st.column_config.NumberColumn("Entry", format="$%.2f"),
            "Stop": st.column_config.NumberColumn("Stop", format="$%.2f"),
            "Target 1": st.column_config.NumberColumn("Target 1", format="$%.2f"),
            "Distance to entry %": st.column_config.NumberColumn("To entry", format="%.2f%%"),
            "Risk to stop %": st.column_config.NumberColumn("Risk", format="%.2f%%"),
        },
    )


def render_live_tracker_body(tickers: tuple[str, ...], include_scan: bool, fragment_mode: bool = False) -> None:
    if st.button(":material/refresh: Refresh now", key="live_tracker_refresh"):
        st.cache_data.clear()
        if fragment_mode:
            st.rerun(scope="fragment")
        else:
            st.rerun()

    df = live_tracker_frame(tickers, include_scan=include_scan)
    scanner_hits = int((df["Track"].astype(str).str.contains("Scanner")).sum()) if not df.empty else 0
    trigger_hits = int((df["Status"] == "Breakout trigger").sum()) if not df.empty else 0
    buy_zone_hits = int((df["Status"] == "In buy zone").sum()) if not df.empty else 0

    status_cards(
        [
            ("Tracked names", str(len(df)), "calm"),
            ("Scanner hits", str(scanner_hits), "good"),
            ("Breakout triggers", str(trigger_hits), "hot"),
            ("In buy zone", str(buy_zone_hits), "good"),
        ]
    )

    st.caption(
        f"Auto-refresh target: every {LIVE_REFRESH_SECONDS} seconds. "
        f"Last refresh: {datetime.now().strftime('%I:%M:%S %p')}. Free Yahoo data may be delayed or rate-limited."
    )
    show_tracker_table(df)


@st.fragment(run_every=f"{LIVE_REFRESH_SECONDS}s")
def auto_refresh_live_tracker(tickers: tuple[str, ...], include_scan: bool) -> None:
    render_live_tracker_body(tickers, include_scan, fragment_mode=True)


def page_live_tracker() -> None:
    header("Live Tracker", "Auto-refresh the scanner and your watchlist while you study setups.")
    watchlist = tuple(read_watchlist())
    cols = st.columns([1, 1, 2])
    include_scan = cols[0].toggle("Include live scanner", value=True, key="tracker_include_scan")
    auto_refresh = cols[1].toggle("Auto-refresh", value=True, key="tracker_auto_refresh")
    cols[2].caption(
        f"Free mode uses Yahoo Finance with a {LIVE_REFRESH_SECONDS}-second refresh target. "
        "It can be delayed or rate-limited, but it is enough for paper-trading practice."
    )

    if auto_refresh:
        auto_refresh_live_tracker(watchlist, include_scan)
    else:
        render_live_tracker_body(watchlist, include_scan)


def page_dashboard() -> None:
    dashboard_hero()
    st.caption(
        "Educational paper-trading tool. Verify live data, news, float, halts, and risk before making real trades. "
        "This is not financial advice."
    )
    control_cols = st.columns([1, 1, 2])
    prefer_live = control_cols[0].toggle("Use live data", value=True, key="dashboard_live")
    control_cols[1].badge(
        "Finnhub connected" if finnhub_enabled() else "Finnhub not connected",
        icon=":material/key:",
        color="green" if finnhub_enabled() else "orange",
    )
    control_cols[2].caption("Home base: scanner candidates, AI plan, market clocks, and the latest news.")

    with st.skeleton(height=240):
        df = default_scan(prefer_live=prefer_live)
    best = df.iloc[0].to_dict()

    status_cards(
        [
            ("Candidates", str(len(df)), "calm"),
            ("Top ticker", str(best["Ticker"]), "good"),
            ("Top score", f"{int(best['AI score'])}/100", "hot"),
            ("Top gain", pct(best["Daily gain %"]), "good"),
            ("Top RVOL", f"{best['RVOL']:.1f}x", "calm"),
        ]
    )

    left, right = st.columns([1.35, 0.85], vertical_alignment="top")
    with left:
        st.subheader("Primary watch")
        render_ai_decision_panel(best)
        render_plan_card(best)
    with right:
        with st.container(border=True):
            st.markdown("**Market clocks**")
            st.dataframe(market_clock_frame(), width="stretch", hide_index=True)
        with st.container(border=True):
            st.markdown("**Market news**")
            render_news_items(finnhub_market_news("general", limit=4), "No market news returned yet.")

    st.subheader("Scanner candidates")
    show_scan_table(df, key="dashboard_scan_table")


def page_daily_gameplan() -> None:
    header("Daily Gameplan", "Your default scan: $2 to $20, gain over 10%, float under 10M, RVOL over 3x.")
    prefer_live = st.toggle("Use live Yahoo data", value=True, key="gameplan_live")
    df = default_scan(prefer_live=prefer_live)
    best = df.iloc[0].to_dict()

    status_cards(
        [
            ("Primary watch", str(best["Ticker"]), "good"),
            ("Score", f"{int(best['AI score'])}/100", "hot"),
            ("Gain", pct(best["Daily gain %"]), "good"),
            ("RVOL", f"{best['RVOL']:.1f}x", "calm"),
        ]
    )

    st.subheader("Primary watch")
    render_ai_decision_panel(best)
    render_plan_card(best)

    st.subheader("Watchlist for the session")
    show_scan_table(df, key="gameplan_scan_table")

    with st.container(border=True):
        st.markdown("**Risk rules**")
        st.write("- Paper trade first. Do not chase a candle far above the entry trigger.")
        st.write("- Keep every idea invalidated at the stop before entering.")
        st.write("- Skip anything with halted news, unclear float, or spreads too wide to manage.")


def page_scanner() -> None:
    header("Scanner", "Find stocks matching your momentum criteria.")
    with st.form("scanner_rules"):
        cols = st.columns(5)
        min_price = cols[0].number_input("Min price", 0.1, 200.0, DEFAULT_RULES["min_price"], step=0.5)
        max_price = cols[1].number_input("Max price", 0.1, 500.0, DEFAULT_RULES["max_price"], step=0.5)
        min_gain = cols[2].number_input("Min gain %", 0.0, 200.0, DEFAULT_RULES["min_gain_pct"], step=1.0)
        max_float = cols[3].number_input("Max float M", 0.1, 500.0, DEFAULT_RULES["max_float_m"], step=1.0)
        min_rvol = cols[4].number_input("Min RVOL", 0.1, 100.0, DEFAULT_RULES["min_rvol"], step=0.5)
        options = st.columns([1, 1, 3])
        prefer_live = options[0].toggle("Use live Yahoo", value=True)
        include_learning = options[1].toggle("Fallback rows", value=True)
        submitted = st.form_submit_button("Run scan", type="primary")

    if submitted or "scanner_df" not in st.session_state:
        st.session_state.scanner_df = run_scan(
            min_price,
            max_price,
            min_gain,
            max_float,
            min_rvol,
            prefer_live=prefer_live,
            include_learning=include_learning,
        )

    df = st.session_state.scanner_df
    if not df.empty:
        top = df.iloc[0].to_dict()
        status_cards(
            [
                ("Matches", str(len(df)), "calm"),
                ("Best ticker", str(top["Ticker"]), "good"),
                ("Best gain", pct(top["Daily gain %"]), "good"),
                ("Best score", f"{int(top['AI score'])}/100", "hot"),
            ]
        )
    show_scan_table(df, key="scanner_results_table")


def page_market_scan() -> None:
    header("Market Scan", "Track core movers, S&P 500 names, global ETFs, crypto, and the full US stock universe in batches.")

    st.badge("Finnhub connected" if finnhub_enabled() else "Finnhub key needed for news/quotes", icon=":material/key:", color="green" if finnhub_enabled() else "orange")

    clock_df = market_clock_frame()
    with st.container(border=True):
        st.markdown("**Market clocks**")
        st.dataframe(clock_df, width="stretch", hide_index=True)

    with st.form("market_scan_form"):
        preset_options = ["Core movers", "S&P 500", "All US stocks", "Watchlist", "United States", "Europe", "Asia", "Crypto"]
        presets = st.pills(
            "Preset lists",
            preset_options,
            default=["Core movers", "S&P 500", "All US stocks", "Watchlist"],
            selection_mode="multi",
        )
        custom = st.text_area(
            "Add tickers",
            value="",
            height=80,
            placeholder="Example: NVDA, SPY, TSM, BTC-USD",
        )
        cols = st.columns([1, 1, 1, 1])
        batch_size = cols[0].number_input("Batch size", 5, 250, DEFAULT_MARKET_SCAN_BATCH, step=5)
        start_at = cols[1].number_input(
            "Start row",
            0,
            50000,
            int(st.session_state.get("market_scan_start", 0)),
            step=DEFAULT_MARKET_SCAN_BATCH,
        )
        include_etfs = cols[2].toggle("Include ETFs", value=True)
        include_news = cols[3].toggle("Show market news", value=True)
        st.caption("All US stocks can be thousands of names. Use Scan next batch to keep moving through the full list without freezing the app.")
        submitted = st.form_submit_button("Run market scan", type="primary", icon=":material/radar:")

    button_cols = st.columns([1, 1, 3])
    next_batch = button_cols[0].button("Scan next batch", icon=":material/skip_next:")
    reset_progress = button_cols[1].button("Reset progress", icon=":material/restart_alt:")
    button_cols[2].caption("Results are accumulated and de-duplicated as you scan more batches.")

    selected_presets = list(presets or [])
    tickers = market_scan_universe(selected_presets, custom, include_etfs=include_etfs)
    full_source = "Selected lists"
    full_count = 0
    if "All US stocks" in selected_presets:
        full_symbols, full_source = full_us_market_universe(include_etfs=include_etfs, api_marker=finnhub_key_marker())
        full_count = len(full_symbols)

    if reset_progress:
        st.session_state.market_scan_df = pd.DataFrame()
        st.session_state.market_scan_start = 0
        st.session_state.market_scan_batch_tickers = []

    should_scan = submitted or next_batch or "market_scan_df" not in st.session_state
    if should_scan:
        if submitted:
            scan_start = int(start_at)
            accumulated = pd.DataFrame()
        elif next_batch:
            prior_start = int(st.session_state.get("market_scan_start", 0))
            prior_size = int(st.session_state.get("market_scan_batch_size", batch_size))
            scan_start = next_batch_start(prior_start, prior_size, len(tickers))
            accumulated = st.session_state.get("market_scan_df", pd.DataFrame())
        else:
            scan_start = int(st.session_state.get("market_scan_start", start_at))
            accumulated = st.session_state.get("market_scan_df", pd.DataFrame())

        batch_tickers = ticker_batch(tickers, scan_start, int(batch_size))
        st.session_state.market_scan_tickers = tickers
        st.session_state.market_scan_start = scan_start
        st.session_state.market_scan_batch_size = int(batch_size)
        st.session_state.market_scan_batch_tickers = batch_tickers
        st.session_state.market_scan_next_start = next_batch_start(scan_start, int(batch_size), len(tickers))
        with st.skeleton(height=260):
            batch_df = broad_market_scan(tuple(batch_tickers), max_names=len(batch_tickers))
            st.session_state.market_scan_df = merge_market_scan_results(accumulated, batch_df)

    df = st.session_state.get("market_scan_df", pd.DataFrame())
    tickers = st.session_state.get("market_scan_tickers", tickers)
    batch_tickers = st.session_state.get("market_scan_batch_tickers", [])
    scan_start = int(st.session_state.get("market_scan_start", 0))
    next_start = int(st.session_state.get("market_scan_next_start", 0))

    if "All US stocks" in selected_presets:
        st.caption(f"Full universe source: {full_source}. Full-universe symbols loaded: {full_count:,}.")

    current_range = "n/a"
    if tickers and batch_tickers:
        current_range = f"{scan_start + 1:,}-{min(scan_start + len(batch_tickers), len(tickers)):,}"

    status_cards(
        [
            ("Universe queued", f"{len(tickers):,}", "calm"),
            ("Current batch", current_range, "good"),
            ("Rows kept", str(len(df)), "good"),
            ("Next start", f"{next_start:,}", "calm"),
            ("Top mover", str(df.iloc[0]["Ticker"]) if not df.empty else "n/a", "hot"),
            ("Best gain", pct(df.iloc[0]["Daily gain %"]) if not df.empty else "n/a", "good"),
        ]
    )

    show_broad_market_table(df)

    if include_news:
        with st.expander(":material/newspaper: General market news", expanded=True):
            render_news_items(finnhub_market_news("general", limit=8), "No general market news returned yet.")


def page_charts() -> None:
    header("Charts", "Chart the candidate, trend, volume, and paper-trade levels.")
    selected_from_scan = str(st.session_state.get("selected_ticker", "")).upper().strip()
    tickers = [row["ticker"] for row in DEMO_PROFILES] + read_watchlist()
    if selected_from_scan:
        tickers.append(selected_from_scan)
    ticker_options = sorted(set(tickers))
    selected_index = ticker_options.index(selected_from_scan) if selected_from_scan in ticker_options else 0
    cols = st.columns([1, 1, 1, 1])
    selected_ticker = cols[0].selectbox("Ticker", ticker_options, index=selected_index)
    custom_ticker = cols[1].text_input("Custom ticker", value="").upper().strip()
    interval = cols[2].selectbox("Candle", ["1m", "2m", "5m", "15m", "30m", "60m", "1d"], index=0)
    if interval == "1m":
        period_options = ["1d", "5d"]
    elif interval in {"2m", "5m", "15m", "30m", "60m"}:
        period_options = ["1d", "5d", "1mo", "3mo"]
    else:
        period_options = ["1mo", "3mo", "6mo", "1y", "2y"]
    period = cols[3].selectbox("Range", period_options, index=0)
    candle_windows = {
        "Last 90": 90,
        "Last 180": 180,
        "Last 390": 390,
        "All loaded": None,
    }
    control_cols = st.columns([1, 1, 1, 2])
    live_toggle = control_cols[0].toggle("Use live Yahoo chart data", value=True, key="chart_live_enabled")
    auto_refresh = control_cols[1].toggle("Auto-refresh chart", value=True, key="chart_auto_refresh_enabled")
    default_window_index = 0 if interval == "1m" else 1
    window_label = control_cols[2].selectbox("Visible candles", list(candle_windows), index=default_window_index)
    with control_cols[3].popover("Chart layers", icon=":material/tune:"):
        st.toggle("EMA 9", value=True, key="chart_layer_ema9")
        st.toggle("EMA 20", value=True, key="chart_layer_ema20")
        st.toggle("VWAP", value=True, key="chart_layer_vwap")
        st.toggle("Buy zone shading", value=True, key="chart_layer_buy_zone")
        st.toggle("Plan levels", value=True, key="chart_layer_plan_levels")
        st.caption("Zoom, pan, and drawing tools are in the chart toolbar.")
    ticker = custom_ticker or selected_ticker
    st.session_state.selected_ticker = ticker
    max_candles = candle_windows[window_label]
    prefer_live = bool(live_toggle) or interval in {"1m", "2m", "5m", "15m", "30m", "60m"}

    if interval == "1m":
        st.caption(
            f"Data mode: {'live intraday' if prefer_live else 'learning'}. "
            "1-minute candles are easiest to see on the 1d range with Last 90 or Last 180 selected."
        )

    if prefer_live and auto_refresh:
        auto_refresh_chart_panel(ticker, period, interval, prefer_live, max_candles=max_candles)
    else:
        render_chart_panel(ticker, period, interval, prefer_live, max_candles=max_candles)


def page_ai_coach() -> None:
    header("AI Coach", "Turn a ticker into a structured paper-trade plan.")
    cols = st.columns([1, 1, 2])
    ticker = cols[0].text_input("Ticker", value=st.session_state.get("selected_ticker", "SOUN")).upper()
    period = cols[1].selectbox("Lookback", ["1mo", "3mo", "6mo", "1y"], index=1)
    prefer_live = cols[2].toggle("Use live Yahoo data", value=True, key="ai_live")

    analysis = analyze_ticker(ticker, period=period, prefer_live=prefer_live)
    render_ai_decision_panel(analysis)
    render_plan_card(analysis)
    with st.expander(f":material/article: News catalyst for {ticker}", expanded=True):
        render_news_items(finnhub_company_news(ticker, days=5, limit=5))

    with st.container(border=True):
        st.markdown("**Paper-trade checklist**")
        st.checkbox("Price is between \\$2 and \\$20", value=2 <= analysis["Price"] <= 20)
        st.checkbox("Daily gain is at least 10%", value=analysis["Daily gain %"] >= 10)
        st.checkbox("Float is under 10M shares", value=analysis["Float M"] <= 10)
        st.checkbox("RVOL is at least 3x", value=analysis["RVOL"] >= 3)
        st.checkbox("Entry, stop, and target are written before entry", value=True)


def page_watchlist() -> None:
    header("Watchlist", "Keep the names you and your friends are studying.")
    watchlist = read_watchlist()
    prefer_live = st.toggle("Use live Yahoo data", value=True, key="watchlist_live")

    with st.form("add_watchlist"):
        cols = st.columns([1, 3])
        new_ticker = cols[0].text_input("Ticker").upper().strip()
        add = cols[1].form_submit_button("Add ticker", type="primary")
        if add and new_ticker:
            watchlist.append(new_ticker)
            write_watchlist(watchlist)
            st.rerun()

    for ticker in watchlist:
        analysis = analyze_ticker(ticker, prefer_live=prefer_live)
        with st.container(border=True):
            cols = st.columns([1, 1, 1, 1, 1])
            cols[0].metric(ticker, analysis["Setup"])
            cols[1].metric("Price", money(analysis["Price"]), pct(analysis["Daily gain %"]))
            cols[2].metric("RVOL", f"{analysis['RVOL']:.1f}x")
            cols[3].metric("AI score", f"{analysis['AI score']}/100")
            if cols[4].button("Study", key=f"study_{ticker}"):
                st.session_state.selected_ticker = ticker
                st.session_state.watchlist_study_ticker = ticker
            if cols[4].button("Remove", key=f"remove_{ticker}"):
                write_watchlist([item for item in watchlist if item != ticker])
                st.rerun()

    study_ticker = st.session_state.get("watchlist_study_ticker")
    if study_ticker:
        st.subheader(f"{study_ticker} study plan")
        render_plan_card(analyze_ticker(study_ticker, prefer_live=prefer_live))
        render_news_items(finnhub_company_news(study_ticker, days=5, limit=5))


def page_trade_desk() -> None:
    header("Trade Desk", "Stage AI trade plans, approve them manually, and record paper orders.")
    st.warning(
        "This page records approved paper orders only. Real broker execution needs a separate broker connection and another explicit approval step.",
        icon=":material/warning:",
    )

    cols = st.columns([1, 1, 1, 1])
    ticker = cols[0].text_input("Ticker", value=st.session_state.get("selected_ticker", "NVDA")).upper().strip()
    risk_dollars = cols[1].number_input("Max paper risk $", min_value=1.0, max_value=10000.0, value=25.0, step=5.0)
    period = cols[2].selectbox("Lookback", ["1d", "5d", "1mo", "3mo"], index=1)
    interval = cols[3].selectbox("Candle", ["1m", "5m", "15m", "1d"], index=1)

    analysis = analyze_ticker(ticker, period=period, interval=interval, prefer_live=True)
    render_ai_decision_panel(analysis)

    order = stage_order_from_analysis(analysis, risk_dollars=risk_dollars)
    with st.container(border=True):
        st.markdown("**Staged order**")
        st.dataframe(pd.DataFrame([order]), width="stretch", hide_index=True)
        confirm = st.checkbox(
            "I approve this paper trade plan and understand it is not financial advice.",
            key=f"approve_{ticker}_{order['Entry']}_{order['Stop']}",
        )
        if st.button("Approve paper order", type="primary", icon=":material/check_circle:", disabled=not confirm):
            approve_paper_order(order)
            st.success("Approved paper order saved to Trade Desk and Journal.")
            st.rerun()

    st.subheader("Recent approved paper orders")
    orders = read_orders()
    if orders.empty:
        st.info("No approved paper orders yet.")
    else:
        st.dataframe(orders.sort_values("Created", ascending=False), width="stretch", hide_index=True)


def page_journal() -> None:
    header("Trade Journal", "Track paper trades, wins, losses, and notes.")
    df = read_journal()
    stats = journal_stats(df)
    cols = st.columns(4)
    cols[0].metric("Trades", stats["trades"])
    cols[1].metric("Win rate", pct(stats["win_rate"]))
    cols[2].metric("Total P/L", money(stats["total_pl"]))
    cols[3].metric("Average R", f"{stats['avg_r']:.2f}R")

    with st.form("journal_entry"):
        top = st.columns([1, 1, 2])
        trade_date = top[0].date_input("Date", value=date.today())
        ticker = top[1].text_input("Ticker", value=st.session_state.get("selected_ticker", "SOUN")).upper()
        setup = top[2].text_input("Setup", value="Momentum gapper")

        nums = st.columns(4)
        entry = nums[0].number_input("Entry", min_value=0.0, value=5.00, step=0.05)
        exit_price = nums[1].number_input("Exit", min_value=0.0, value=5.40, step=0.05)
        stop = nums[2].number_input("Stop", min_value=0.0, value=4.75, step=0.05)
        shares = nums[3].number_input("Shares", min_value=1, value=100, step=10)
        notes = st.text_area("Notes", height=90)
        submitted = st.form_submit_button("Save paper trade", type="primary")

    if submitted:
        pl = (exit_price - entry) * shares
        pl_pct = ((exit_price - entry) / entry * 100) if entry else 0
        risk = max(entry - stop, entry * 0.01)
        r_multiple = (exit_price - entry) / risk
        append_journal(
            {
                "Date": trade_date.isoformat(),
                "Ticker": ticker,
                "Setup": setup,
                "Entry": entry,
                "Exit": exit_price,
                "Stop": stop,
                "Shares": shares,
                "P/L $": round(pl, 2),
                "P/L %": round(pl_pct, 2),
                "R multiple": round(r_multiple, 2),
                "Notes": notes,
            }
        )
        st.success("Paper trade saved.")
        st.rerun()

    if df.empty:
        st.info("No journal entries yet.")
    else:
        st.dataframe(df.sort_values("Date", ascending=False), width="stretch", hide_index=True)


def page_backtester() -> None:
    header("Backtester", "Test the momentum-gap rule on recent history.")
    with st.form("backtester_form"):
        cols = st.columns(5)
        ticker = cols[0].text_input("Ticker", value="SOUN").upper()
        period = cols[1].selectbox("Period", ["3mo", "6mo", "1y", "2y"], index=1)
        min_gap = cols[2].number_input("Min gap %", 1.0, 50.0, 10.0, step=1.0)
        min_rvol = cols[3].number_input("Min RVOL", 0.5, 20.0, 3.0, step=0.5)
        hold_days = cols[4].number_input("Hold days", 1, 10, 3, step=1)
        prefer_live = st.toggle("Use live Yahoo data", value=True, key="backtest_live")
        run = st.form_submit_button("Run backtest", type="primary")

    if run or "backtest_result" not in st.session_state:
        st.session_state.backtest_result = backtest_strategy(ticker, period, prefer_live, min_gap, min_rvol, hold_days)

    result = st.session_state.backtest_result
    summary = result["summary"]
    cols = st.columns(4)
    cols[0].metric("Trades", summary["Trades"])
    cols[1].metric("Win rate", pct(summary["Win rate"]))
    cols[2].metric("Average gain", pct(summary["Average gain %"]))
    cols[3].metric("Average R", f"{summary['Average R']:.2f}R")

    trades = result["trades"]
    if trades.empty:
        st.info("No completed backtest trades matched those settings.")
    else:
        st.dataframe(
            trades,
            width="stretch",
            hide_index=True,
            column_config={
                "Entry": st.column_config.NumberColumn("Entry", format="$%.2f"),
                "Exit": st.column_config.NumberColumn("Exit", format="$%.2f"),
                "Stop": st.column_config.NumberColumn("Stop", format="$%.2f"),
                "Gain %": st.column_config.NumberColumn("Gain", format="%.2f%%"),
                "R multiple": st.column_config.NumberColumn("R", format="%.2f"),
                "RVOL": st.column_config.NumberColumn("RVOL", format="%.1fx"),
                "Gap %": st.column_config.NumberColumn("Gap", format="%.1f%%"),
            },
        )
    st.caption(f"Backtest source: {result['source']}. Backtests are simplified and for learning only.")


def page_learn() -> None:
    header("Learn", "A practical day-trading study guide for the scanner, charts, news, risk, and journaling.")

    track = st.selectbox(
        "Learning track",
        [
            "Start here",
            "Place a paper trade",
            "Order ticket",
            "Playbook",
            "Routine",
            "Chart reading",
            "Risk",
            "News",
            "Practice",
            "Glossary",
            "iPad",
        ],
        index=0,
        width="stretch",
    )
    track = track or "Start here"

    if track == "Start here":
        st.warning(
            "Begin in paper trading. Do not place real orders until you understand order types, broker rules, risk, and how fast losses can happen.",
            icon=":material/warning:",
        )
        cols = st.columns(3)
        with cols[0]:
            with st.container(border=True, height="stretch"):
                st.markdown("**1. Learn the screen**")
                st.write("- Dashboard shows the best current study idea.")
                st.write("- Market Scan checks big lists like S&P 500 and all US stocks in batches.")
                st.write("- Scanner focuses on the low-priced momentum rules.")
                st.write("- Charts shows candles, VWAP, EMAs, news, and plan levels.")
        with cols[1]:
            with st.container(border=True, height="stretch"):
                st.markdown("**2. Learn the plan**")
                st.write("- Buy zone is where a pullback still looks controlled.")
                st.write("- Entry trigger is the level where buyers confirm strength.")
                st.write("- Stop is where the idea is wrong.")
                st.write("- Target is where reward starts to justify the risk.")
        with cols[2]:
            with st.container(border=True, height="stretch"):
                st.markdown("**3. Practice the workflow**")
                st.write("- Pick one ticker from Scanner or Market Scan.")
                st.write("- Open Charts and check trend, volume, news, and levels.")
                st.write("- Open Trade Desk and stage a paper order.")
                st.write("- Save the result in Journal after the trade is done.")

        with st.container(border=True):
            st.markdown("**The app workflow for a brand-new trader**")
            st.write("1. Go to Market Scan to see what the broad market and big names are doing.")
            st.write("2. Go to Scanner for small-cap momentum candidates that match the app rules.")
            st.write("3. Click a ticker row, then open Charts to inspect the candle trend and plan levels.")
            st.write("4. Read the AI decision. If it says Study only or Watch only, do not force a trade.")
            st.write("5. Open Trade Desk, set your max paper risk, review the staged order, and only approve if every checklist item makes sense.")
            st.write("6. Open Journal and record what happened, even if you skipped the trade.")

        with st.container(border=True):
            st.markdown("**Beginner safety rules**")
            st.write("- A stock moving fast is not automatically a good trade.")
            st.write("- A plan has entry, stop, target, share size, and a reason before the order is placed.")
            st.write("- Market orders can fill at a worse price than expected in fast stocks.")
            st.write("- Limit and stop orders still need care; different brokers support different instructions.")
            st.write("- Real day trading can trigger broker, margin, tax, and pattern day trader rules.")

    elif track == "Place a paper trade":
        st.info(
            "This section teaches the paper-trade process. It is a practice workflow, not a recommendation to buy or sell any stock.",
            icon=":material/school:",
        )
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**Before you stage the order**")
                st.write("1. Pick a ticker from Scanner or Market Scan.")
                st.write("2. Open Charts and confirm the 1-minute or 5-minute candle trend.")
                st.write("3. Check that price is not far above the buy zone.")
                st.write("4. Check news, volume, RVOL, float, and spread risk.")
                st.write("5. Decide your max paper risk before thinking about shares.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**Inside Trade Desk**")
                st.write("1. Enter the ticker.")
                st.markdown(markdown_text("2. Set Max paper risk, like $10, $25, or $50."))
                st.write("3. Choose the lookback and candle size.")
                st.write("4. Read the AI decision and setup checks.")
                st.write("5. Review Entry, Stop, Target, Shares, and Reason before approval.")

        with st.container(border=True):
            st.markdown("**Position size in plain English**")
            st.markdown(markdown_text("If entry is $5.00 and stop is $4.75, the risk is $0.25 per share."))
            st.markdown(markdown_text("If max paper risk is $25, then $25 / $0.25 = 100 shares."))
            st.write("If the stop is farther away, share size should be smaller. If you cannot accept the loss at the stop, the trade is too large.")

        with st.container(border=True):
            st.markdown("**What to do after approval**")
            st.write("- Paper order approved: the app saves it to Trade Desk and Journal.")
            st.write("- If price reaches the stop: mark the paper trade as invalid and record the planned loss.")
            st.write("- If price reaches target 1: record what happened and whether the plan was followed.")
            st.write("- If price never triggers: write 'no trade' in your notes. Skipping is part of trading.")

        with st.container(border=True):
            st.markdown("**Do not approve if...**")
            st.write("- You cannot explain why the stock is moving.")
            st.write("- The AI says Study only, Watch only, or Plan invalid.")
            st.write("- The entry is far above the buy zone and you would be chasing.")
            st.write("- The spread is wide, candles are erratic, or news is unclear.")
            st.write("- You are increasing size because you want to make back a loss.")

    elif track == "Order ticket":
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**Common broker ticket fields**")
                st.write("- Symbol: the ticker, like NVDA or SOUN.")
                st.write("- Side: buy, sell, sell short, or buy to cover.")
                st.write("- Quantity: how many shares.")
                st.write("- Order type: market, limit, stop, or stop-limit.")
                st.write("- Time in force: how long the order stays active.")
                st.write("- Review: final confirmation before sending.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**Order types for beginners**")
                st.write("- Market order: tries to fill immediately, but the final price can be different from what you saw.")
                st.write("- Limit order: sets the worst price you are willing to accept.")
                st.write("- Stop order: triggers after a stop price is reached, then can become a market order.")
                st.write("- Stop-limit order: triggers after a stop price, but only fills inside your limit.")
                st.write("- Not every broker supports every order instruction the same way.")

        with st.container(border=True):
            st.markdown("**How the app's staged paper order maps to a broker ticket**")
            mapping = pd.DataFrame(
                [
                    {"App field": "Ticker", "Broker ticket field": "Symbol", "Beginner meaning": "The stock you are practicing."},
                    {"App field": "Side", "Broker ticket field": "Action", "Beginner meaning": "Usually Buy for this paper long setup."},
                    {"App field": "Shares", "Broker ticket field": "Quantity", "Beginner meaning": "Calculated from max paper risk and stop distance."},
                    {"App field": "Entry", "Broker ticket field": "Stop or limit price", "Beginner meaning": "The confirmation level, not a guarantee."},
                    {"App field": "Stop", "Broker ticket field": "Stop-loss plan", "Beginner meaning": "Where the idea is wrong."},
                    {"App field": "Target 1", "Broker ticket field": "Target/exit plan", "Beginner meaning": "Where reward begins to pay for the risk."},
                ]
            )
            st.dataframe(mapping, width="stretch", hide_index=True)

        with st.container(border=True):
            st.markdown("**Real-order caution**")
            st.write("- The app records paper trades. It does not place real broker orders by itself.")
            st.write("- Before real trading, confirm your broker's order types, margin rules, fees, and day-trading restrictions.")
            st.write("- Always review the broker confirmation screen before sending any real order.")

    elif track == "Playbook":
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**The setup this app is built around**")
                st.markdown(markdown_text("- Price: $2 to $20 for the small-account momentum style."))
                st.write("- Daily gain: at least 10%, usually found through top-gapper scans.")
                st.write("- Float: preferably under 10M shares, because small supply can move faster.")
                st.write("- RVOL: at least 3x, showing today is much more active than normal.")
                st.write("- Chart: price should hold above VWAP/EMAs instead of fading immediately.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**What the AI plan is trying to do**")
                st.write("- Buy zone: where a pullback still looks controlled.")
                st.write("- Entry trigger: the price that confirms buyers are stepping in.")
                st.write("- Stop: the level where the idea is wrong.")
                st.write("- Targets: where the reward starts to justify the risk.")
                st.write("- Confidence: a study score, not a promise.")

        with st.container(border=True):
            st.markdown("**Daily routine**")
            st.write("1. Check the Market Scan for broad market strength and big-name leaders.")
            st.write("2. Run the Scanner for low-priced momentum candidates.")
            st.write("3. Open Charts and confirm 1-minute/5-minute trend, VWAP, volume, and news catalyst.")
            st.write("4. Write the entry, stop, and target before any paper trade.")
            st.write("5. Save the result in Journal and review what happened.")

        with st.container(border=True):
            st.markdown("**Scanner labels**")
            st.write("- Playbook fit: price, gain, float, RVOL, and score are all lined up.")
            st.write("- Developing setup: most rules are close, but it still needs confirmation.")
            st.write("- Wait for confirmation: do not chase; wait for the buy zone or trigger.")
            st.write("- Market context: useful for SPY, QQQ, NVDA, and leaders, but not the small-float playbook.")
            st.write("- Study only: good for learning, not a primary paper-trade idea right now.")

    elif track == "Routine":
        cols = st.columns(3)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**Before the open**")
                st.write("- Build a short watchlist instead of chasing every mover.")
                st.write("- Check news, float, relative volume, and whether the ticker is easy to borrow or has special risk.")
                st.write("- Mark the levels where the idea works and where it is wrong.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**During the open**")
                st.write("- Wait for the first clean setup instead of buying the first candle.")
                st.write("- Prefer entries near planned levels with volume confirmation.")
                st.write("- If the spread is wide or candles are chaotic, stand aside.")
        with cols[2]:
            with st.container(border=True):
                st.markdown("**After the session**")
                st.write("- Journal the plan, result, and whether you followed the rules.")
                st.write("- Review screenshots of entries you skipped and entries you took.")
                st.write("- Improve one rule at a time instead of changing everything.")

        with st.container(border=True):
            st.markdown("**Review questions**")
            st.write("- Was the trade actually part of the scanner playbook?")
            st.write("- Did the entry happen near the buy zone or after a clean trigger?")
            st.write("- Did news and volume support the move?")
            st.write("- Was the risk small enough to repeat the setup many times?")

    elif track == "Chart reading":
        cols = st.columns(3)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**VWAP**")
                st.write("VWAP is the average price weighted by volume. Above VWAP often means buyers are in control; below VWAP means caution.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**EMA 9 / EMA 20**")
                st.write("The 9 EMA tracks fast momentum. The 20 EMA is slower. Strong intraday trends often respect these lines.")
        with cols[2]:
            with st.container(border=True):
                st.markdown("**Volume**")
                st.write("Volume confirms interest. A breakout without volume is easier to fail. A pullback with lighter volume can be healthier.")

        with st.container(border=True):
            st.markdown("**Common chart states**")
            st.write("- Opening push: big candles and high volume after the bell.")
            st.write("- Controlled pullback: price dips but holds VWAP/EMA support.")
            st.write("- Breakout trigger: price clears the plan level with volume.")
            st.write("- Failed setup: price loses VWAP, loses the stop, or spreads widen.")

    elif track == "Risk":
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**Before entry**")
                st.write("- Know the stop before the entry.")
                st.write("- Make sure target 1 is at least 1.5R away.")
                st.write("- Avoid chasing far above the trigger.")
                st.write("- Skip halted stocks, huge spreads, and unclear news.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**Position sizing example**")
                st.markdown(markdown_text("If a paper account risks $25 and the entry is $5.00 with a $4.75 stop, risk is $0.25/share."))
                st.markdown(markdown_text("$25 / $0.25 = 100 shares."))
                st.write("This app helps write the plan, but you still approve every trade idea.")

        with st.container(border=True):
            st.markdown("**Loss rules**")
            st.write("- One planned loss is tuition. A chased loss is a habit problem.")
            st.write("- If the setup breaks the stop, the idea is invalid.")
            st.write("- If you miss the entry, wait for the next clean setup.")

    elif track == "News":
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**Catalysts that can move small caps**")
                st.write("- Earnings or guidance")
                st.write("- Contract wins")
                st.write("- FDA, patent, or regulatory headlines")
                st.write("- Analyst upgrades")
                st.write("- Sector sympathy, like AI/quantum/space momentum")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**News checks**")
                st.write("- Is the news fresh today?")
                st.write("- Is it real company news or just social hype?")
                st.write("- Is volume confirming the headline?")
                st.write("- Did the move already exhaust before you found it?")

        with st.container(border=True):
            st.markdown("**Live market news**")
            render_news_items(finnhub_market_news("general", limit=6), "Add your Finnhub key or try again later for live news.")

    elif track == "Practice":
        with st.container(border=True):
            st.markdown("**Paper-trade drill**")
            drill_ticker = st.text_input("Practice ticker", value=st.session_state.get("selected_ticker", "NVDA")).upper()
            analysis = analyze_ticker(drill_ticker, period="5d", interval="5m", prefer_live=True)
            render_plan_card(analysis)

        with st.container(border=True):
            st.markdown("**Before you mark this as tradable**")
            checks = [
                "I can explain the catalyst.",
                "Price is near the buy zone or waiting for the trigger.",
                "The stop is written down.",
                "Target 1 gives enough reward for the risk.",
                "I am paper trading and journaling the result.",
            ]
            completed = 0
            for index, check in enumerate(checks):
                if st.checkbox(check, key=f"learn_check_{index}"):
                    completed += 1
            st.progress(completed / len(checks))
            st.caption(f"{completed} of {len(checks)} practice checks complete.")

    elif track == "Glossary":
        terms = pd.DataFrame(
            [
                {"Term": "Paper trade", "Meaning": "A practice trade that records the plan without risking real money.", "Why it matters": "New traders can learn the process before using real capital."},
                {"Term": "Order ticket", "Meaning": "The broker screen where symbol, side, quantity, order type, and prices are entered.", "Why it matters": "Most costly mistakes happen when the ticket is rushed or misunderstood."},
                {"Term": "Market order", "Meaning": "An order that tries to fill right away at the available market price.", "Why it matters": "It can fill at a different price than expected in fast stocks."},
                {"Term": "Limit order", "Meaning": "An order that sets the worst price you are willing to accept.", "Why it matters": "It gives price control, but it may not fill."},
                {"Term": "Stop order", "Meaning": "An order that activates after a stop price is reached.", "Why it matters": "Some stop orders can become market orders after triggering."},
                {"Term": "Stop-limit order", "Meaning": "A stop order that becomes a limit order after the stop price is reached.", "Why it matters": "It controls price but can miss the fill if price moves too fast."},
                {"Term": "Bid", "Meaning": "The highest displayed price buyers are currently offering.", "Why it matters": "Sellers often transact near the bid."},
                {"Term": "Ask", "Meaning": "The lowest displayed price sellers are currently offering.", "Why it matters": "Buyers often transact near the ask."},
                {"Term": "Spread", "Meaning": "The gap between bid and ask.", "Why it matters": "Wide spreads make entries and exits more expensive and harder to control."},
                {"Term": "Time in force", "Meaning": "How long an order stays active, such as day-only or good-till-canceled.", "Why it matters": "A forgotten open order can create surprises."},
                {"Term": "Gapper", "Meaning": "A stock opening or trading far above the prior close.", "Why it matters": "It can reveal fresh demand, but late entries can fade fast."},
                {"Term": "Float", "Meaning": "Shares available for public trading.", "Why it matters": "Lower float can move faster because there is less supply."},
                {"Term": "RVOL", "Meaning": "Relative volume compared with normal trading volume.", "Why it matters": "High RVOL shows unusual attention today."},
                {"Term": "VWAP", "Meaning": "Volume-weighted average price.", "Why it matters": "Many traders use it as an intraday control line."},
                {"Term": "Entry trigger", "Meaning": "The level that confirms buyers are stepping in.", "Why it matters": "It helps avoid buying only because price is moving."},
                {"Term": "Stop", "Meaning": "The level where the idea is invalid.", "Why it matters": "It defines risk before the trade."},
                {"Term": "R multiple", "Meaning": "Reward or loss measured against the planned risk.", "Why it matters": "It lets you compare trades fairly."},
                {"Term": "Pattern day trader rule", "Meaning": "A broker/margin-account rule that can apply to frequent day trading.", "Why it matters": "Real traders must check broker rules before day trading with margin."},
            ]
        )
        st.dataframe(terms, width="stretch", hide_index=True)

    elif track == "iPad":
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**Use it like an iPad app**")
                st.write("1. Deploy or host the app so it has a web link.")
                st.write("2. Open the link in Safari on your iPad.")
                st.write("3. Tap Share.")
                st.write("4. Tap Add to Home Screen.")
                st.write("5. Open it from the icon like a normal app.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**True App Store app**")
                st.write("A real downloadable App Store app needs a mobile wrapper or rebuild, Apple Developer account, signing, review, and broker/data compliance checks.")
                st.write("The fastest no-cost path is the Home Screen web app. It still feels app-like once hosted.")


def main() -> None:
    st.set_page_config(page_title="MomentumScannerAI", page_icon=":material/monitoring:", layout="wide")
    mode = display_mode_control()
    apply_style(mode)
    pages = [
        st.Page(page_dashboard, title="Dashboard", icon=":material/dashboard:"),
        st.Page(page_daily_gameplan, title="Daily Gameplan", icon=":material/event_note:", url_path="Daily_Gameplan"),
        st.Page(page_live_tracker, title="Live Tracker", icon=":material/monitoring:", url_path="Live_Tracker"),
        st.Page(page_scanner, title="Scanner", icon=":material/search:", url_path="Scanner"),
        st.Page(page_market_scan, title="Market Scan", icon=":material/radar:", url_path="Market_Scan"),
        st.Page(page_charts, title="Charts", icon=":material/candlestick_chart:", url_path="Charts"),
        st.Page(page_ai_coach, title="AI Coach", icon=":material/psychology:", url_path="AI"),
        st.Page(page_watchlist, title="Watchlist", icon=":material/star:", url_path="Watchlist"),
        st.Page(page_trade_desk, title="Trade Desk", icon=":material/order_approve:", url_path="Trade_Desk"),
        st.Page(page_journal, title="Journal", icon=":material/edit_note:", url_path="Journal"),
        st.Page(page_backtester, title="Backtester", icon=":material/query_stats:", url_path="Backtester"),
        st.Page(page_learn, title="Learn", icon=":material/school:", url_path="Learn"),
    ]
    navigation = st.navigation(pages, position="sidebar")
    navigation.run()


if __name__ == "__main__":
    main()
