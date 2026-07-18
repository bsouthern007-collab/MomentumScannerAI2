from __future__ import annotations

import json
import math
import os
import html
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote as url_quote

import altair as alt
import numpy as np
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

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

try:
    from alpaca.data.enums import DataFeed
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
except Exception:  # pragma: no cover - Alpaca is an optional free data upgrade
    DataFeed = None
    StockBarsRequest = None
    StockHistoricalDataClient = None
    TimeFrame = None
    TimeFrameUnit = None


APP_DIR = Path(__file__).resolve().parent
APP_NAME = "Trading for Dummys 101"
DATA_DIR = APP_DIR / "data"
ASSETS_DIR = APP_DIR / "assets"
LIGHTWEIGHT_CHARTS_FILE = ASSETS_DIR / "lightweight-charts.standalone.production.js"
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
SYMBOL_ALIASES = {
    "S&P500": "^GSPC",
    "S&P 500": "^GSPC",
    "SP500": "^GSPC",
    "SPX": "^GSPC",
    "GSPC": "^GSPC",
    "NASDAQ": "^IXIC",
    "NASDAQ COMPOSITE": "^IXIC",
    "IXIC": "^IXIC",
    "DOW": "^DJI",
    "DOW JONES": "^DJI",
    "DJIA": "^DJI",
    "DJI": "^DJI",
    "RUSSELL 2000": "^RUT",
    "RUSSELL2000": "^RUT",
    "RUT": "^RUT",
    "VIX": "^VIX",
}
INDEX_PROFILES = {
    "^GSPC": {"company": "S&P 500 Index", "sector": "Broad market index", "float_m": 0.0, "catalyst": "Broad US large-cap market movement"},
    "^IXIC": {"company": "Nasdaq Composite Index", "sector": "Technology-heavy market index", "float_m": 0.0, "catalyst": "Broad Nasdaq market movement"},
    "^DJI": {"company": "Dow Jones Industrial Average", "sector": "Blue-chip market index", "float_m": 0.0, "catalyst": "Broad Dow market movement"},
    "^RUT": {"company": "Russell 2000 Index", "sector": "Small-cap market index", "float_m": 0.0, "catalyst": "Broad small-cap market movement"},
    "^VIX": {"company": "CBOE Volatility Index", "sector": "Volatility index", "float_m": 0.0, "catalyst": "Market volatility movement"},
}
DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
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
    if "alpaca" in lowered:
        return "Alpaca IEX", "green"
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


NEWS_IMPORTANCE: dict[str, int] = {
    "Risk headline": 7,
    "FDA/regulatory": 6,
    "M&A": 6,
    "Earnings": 5,
    "Contract": 5,
    "Analyst": 3,
    "Sector": 2,
}


def news_age_hours(item: dict[str, Any]) -> float:
    published = safe_float(item.get("datetime"))
    if published is None:
        return 999.0
    if published > 10_000_000_000:
        published = published / 1000
    try:
        return max((datetime.now() - datetime.fromtimestamp(float(published))).total_seconds() / 3600, 0)
    except Exception:
        return 999.0


def news_impact_score(item: dict[str, Any]) -> int:
    headline = str(item.get("headline") or "")
    summary = str(item.get("summary") or "")
    text = f"{headline} {summary}".lower()
    tags = catalyst_tags(headline, summary)
    score = sum(NEWS_IMPORTANCE.get(tag, 1) for tag in tags)
    if any(word in text for word in ("announces", "wins", "launches", "surges", "approval", "raises", "beats")):
        score += 2
    if any(word in text for word in ("offering", "halt", "investigation", "bankruptcy", "delisting")):
        score += 3

    age = news_age_hours(item)
    if age <= 2:
        score += 4
    elif age <= 6:
        score += 3
    elif age <= 24:
        score += 2
    elif age <= 72:
        score += 1
    return score


def news_related_symbol(item: dict[str, Any]) -> str:
    for field in ("_symbol", "symbol", "related"):
        value = str(item.get(field) or "").strip()
        if not value:
            continue
        parts = [part for chunk in value.replace(";", ",").split(",") for part in chunk.split() if part]
        if parts:
            return normalize_user_symbol(parts[0])
    return "Market"


@st.cache_data(ttl=300, max_entries=30, show_spinner=False)
def biggest_stock_news(symbols: tuple[str, ...], api_marker: str, limit: int = 8) -> list[dict[str, Any]]:
    if api_marker == "no-key":
        return []

    cleaned_symbols = tuple(unique_symbols([normalize_user_symbol(symbol) for symbol in symbols if normalize_user_symbol(symbol)]))
    items: list[dict[str, Any]] = []

    for item in finnhub_market_news("general", limit=20):
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row["_symbol"] = news_related_symbol(row)
        row["_feed"] = "Market"
        row["_score"] = news_impact_score(row)
        items.append(row)

    for symbol in cleaned_symbols[:12]:
        for item in finnhub_company_news(symbol, days=3, limit=3):
            if not isinstance(item, dict):
                continue
            row = dict(item)
            row["_symbol"] = symbol
            row["_feed"] = "Stock"
            row["_score"] = news_impact_score(row)
            items.append(row)

    unique_items: dict[str, dict[str, Any]] = {}
    for item in items:
        key = str(item.get("url") or item.get("headline") or item.get("id") or "")
        if not key:
            continue
        if key not in unique_items or int(item.get("_score", 0)) > int(unique_items[key].get("_score", 0)):
            unique_items[key] = item

    return sorted(
        unique_items.values(),
        key=lambda item: (int(item.get("_score", 0)), safe_float(item.get("datetime"), 0) or 0),
        reverse=True,
    )[:limit]


def render_big_news_rail(symbols: tuple[str, ...]) -> None:
    with st.container(border=True):
        st.markdown("**Biggest news dropped**")
        st.caption("Ranks fresh headlines by catalyst strength, risk, and recency.")
        if not finnhub_enabled():
            st.info("Add your free Finnhub key to turn on ranked stock news.", icon=":material/key:")
            return

        news = biggest_stock_news(symbols, finnhub_key_marker(), limit=8)
        if not news:
            st.caption("No high-impact stock news returned yet.")
            return

        for item in news:
            headline = str(item.get("headline") or "Untitled news")
            url = str(item.get("url") or "")
            source = str(item.get("source") or "News")
            symbol = news_related_symbol(item)
            tags = catalyst_tags(headline, str(item.get("summary") or ""))
            score = int(item.get("_score", 0))
            with st.container(border=True):
                with st.container(horizontal=True):
                    st.badge(symbol, icon=":material/finance_chip:", color="blue")
                    st.badge(f"Impact {score}", icon=":material/bolt:", color="red" if "Risk headline" in tags else "green" if score >= 8 else "orange")
                if url:
                    st.markdown(f"**[{headline}]({url})**")
                else:
                    st.markdown(f"**{headline}**")
                if tags:
                    with st.container(horizontal=True):
                        for tag in tags[:3]:
                            st.badge(tag, color="red" if tag == "Risk headline" else "blue")
                st.caption(f"{source} | {timestamp_label(item.get('datetime'))}")


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


def normalize_user_symbol(symbol: Any) -> str:
    raw = str(symbol or "").strip().upper().replace("$", "")
    raw = " ".join(raw.split())
    if not raw:
        return ""
    if raw in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[raw]

    compact = raw.replace(" ", "").replace(".", "")
    if compact in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[compact]

    cleaned = raw.replace(".", "-").replace("/", "-")
    return SYMBOL_ALIASES.get(cleaned, cleaned)


def clean_market_symbol(symbol: Any) -> str:
    clean = normalize_user_symbol(symbol)
    if not clean or clean in {"N/A", "NAN", "NONE"}:
        return ""
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-^")
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
    if clean.lower() in {
        "paste-your-finnhub-key-here",
        "paste-your-alpaca-key-id-here",
        "paste-your-alpaca-secret-key-here",
        "your_key_here",
        "your-key-here",
        "your_secret_here",
        "your-secret-here",
    }:
        return ""
    return clean


def finnhub_api_key() -> str:
    return get_secret("FINNHUB_API_KEY") or get_secret("finnhub_api_key")


def finnhub_enabled() -> bool:
    return bool(finnhub_api_key())


def alpaca_api_key() -> str:
    return get_secret("ALPACA_API_KEY") or get_secret("ALPACA_API_KEY_ID") or get_secret("APCA_API_KEY_ID")


def alpaca_secret_key() -> str:
    return get_secret("ALPACA_SECRET_KEY") or get_secret("ALPACA_API_SECRET") or get_secret("APCA_API_SECRET_KEY")


def alpaca_enabled() -> bool:
    return bool(alpaca_api_key() and alpaca_secret_key() and StockHistoricalDataClient is not None)


def alpaca_key_marker() -> str:
    key = alpaca_api_key()
    secret = alpaca_secret_key()
    if not key or not secret:
        return "no-alpaca-key"
    return f"alpaca-{len(key)}-{key[-4:]}-{len(secret)}"


@st.cache_resource(show_spinner=False)
def alpaca_data_client(marker: str) -> Any | None:
    if marker == "no-alpaca-key" or StockHistoricalDataClient is None:
        return None
    key = alpaca_api_key()
    secret = alpaca_secret_key()
    if not key or not secret:
        return None
    return StockHistoricalDataClient(api_key=key, secret_key=secret)


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
        response = requests.get(NASDAQ_LISTED_URL, headers={"User-Agent": f"Mozilla/5.0 {APP_NAME}"}, timeout=10)
        response.raise_for_status()
        symbols.extend(parse_symbol_directory(response.text, "Symbol", include_etfs=include_etfs))
    except Exception:
        pass
    try:
        response = requests.get(OTHER_LISTED_URL, headers={"User-Agent": f"Mozilla/5.0 {APP_NAME}"}, timeout=10)
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
    ticker = normalize_user_symbol(ticker)
    if ticker in PROFILE_BY_TICKER:
        return dict(PROFILE_BY_TICKER[ticker])
    if ticker in INDEX_PROFILES:
        profile = INDEX_PROFILES[ticker]
        return {
            "ticker": ticker,
            "company": profile["company"],
            "sector": profile["sector"],
            "price": 5000.0,
            "prev_close": 4980.0,
            "daily_gain_pct": 0.4,
            "volume": 1_000_000,
            "avg_volume": 1_000_000,
            "rvol": 1.0,
            "float_m": 999999.0,
            "catalyst": profile["catalyst"],
        }

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
        "catalyst": "Custom stock. Verify live float, news, and volume.",
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
    ticker = normalize_user_symbol(ticker)
    response = requests.get(
        YAHOO_CHART_URL.format(ticker=url_quote(ticker, safe="")),
        params={
            "range": period,
            "interval": interval,
            "includePrePost": str(bool(prepost)).lower(),
            "events": "div,splits",
        },
        headers={"User-Agent": f"Mozilla/5.0 {APP_NAME}"},
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


def alpaca_timeframe(interval: str) -> Any | None:
    if TimeFrame is None or TimeFrameUnit is None:
        return None
    interval = str(interval or "1d").lower()
    if interval == "1d":
        return TimeFrame.Day
    if interval == "60m":
        return TimeFrame.Hour
    if interval.endswith("m"):
        minutes = safe_float(interval[:-1])
        if minutes is not None and 1 <= int(minutes) <= 59:
            return TimeFrame(int(minutes), TimeFrameUnit.Minute)
    return None


def alpaca_lookback_window(period: str, interval: str) -> tuple[datetime, datetime]:
    end = datetime.now(timezone.utc)
    days = period_days(period)
    if str(interval).endswith("m"):
        days = max(days, 2)
    start = end - timedelta(days=days)
    return start, end


@st.cache_data(ttl=20, max_entries=220, show_spinner=False)
def alpaca_iex_history(ticker: str, period: str, interval: str, api_marker: str) -> pd.DataFrame:
    ticker = normalize_user_symbol(ticker)
    if not ticker or ticker.startswith("^") or api_marker == "no-alpaca-key":
        return pd.DataFrame()
    if StockBarsRequest is None or DataFeed is None:
        return pd.DataFrame()
    timeframe = alpaca_timeframe(interval)
    if timeframe is None:
        return pd.DataFrame()
    client = alpaca_data_client(api_marker)
    if client is None:
        return pd.DataFrame()
    start, end = alpaca_lookback_window(period, interval)
    request = StockBarsRequest(
        symbol_or_symbols=ticker,
        timeframe=timeframe,
        start=start,
        end=end,
        feed=DataFeed.IEX,
        limit=10_000,
    )
    bars = client.get_stock_bars(request)
    raw = bars.dict() if hasattr(bars, "dict") else {}
    rows = raw.get(ticker) or raw.get(ticker.upper()) or []
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(
        [
            {
                "Open": row.get("open"),
                "High": row.get("high"),
                "Low": row.get("low"),
                "Close": row.get("close"),
                "Volume": row.get("volume"),
                "Time": row.get("timestamp"),
            }
            for row in rows
        ]
    ).dropna(subset=["Open", "High", "Low", "Close", "Volume", "Time"])
    if df.empty:
        return pd.DataFrame()
    df.index = pd.to_datetime(df.pop("Time"), utc=True)
    return normalize_history(df)


@st.cache_data(ttl=20, max_entries=250, show_spinner=False)
def load_history(
    ticker: str,
    period: str = "3mo",
    interval: str = "1d",
    prefer_live: bool = False,
    prepost: bool = True,
) -> tuple[pd.DataFrame, str]:
    ticker = normalize_user_symbol(ticker)
    if prefer_live:
        if alpaca_enabled():
            try:
                df = alpaca_iex_history(ticker, period=period, interval=interval, api_marker=alpaca_key_marker())
                if not df.empty and len(df) >= 5:
                    return df, f"Alpaca IEX {interval}"
                print(f"[live-history] Alpaca IEX returned no usable bars for {ticker} {period}/{interval}", flush=True)
            except Exception as exc:
                print(f"[live-history] Alpaca IEX failed for {ticker} {period}/{interval}: {exc}", flush=True)

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
    ticker = normalize_user_symbol(ticker)
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
        "Ticker": ticker,
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
    ticker = normalize_user_symbol(ticker)
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
    ticker = normalize_user_symbol(ticker)
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


@st.cache_data(ttl=20, max_entries=150, show_spinner=False)
def yahoo_quote_stats(ticker: str) -> dict[str, Any] | None:
    ticker = normalize_user_symbol(ticker)
    if yf is None:
        return None

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


@st.cache_data(ttl=20, max_entries=40, show_spinner=False)
def live_quote_stats(ticker: str) -> dict[str, Any] | None:
    ticker = normalize_user_symbol(ticker)
    finnhub_stats = finnhub_quote_stats(ticker)
    if finnhub_stats:
        return finnhub_stats
    return yahoo_quote_stats(ticker)


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
        "Ticker": normalize_user_symbol(ticker),
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
        "Market state": "Practice data" if source == "Learning data" else "Chart-derived",
        "Quote time": chart_timestamp_label(history.index[-1]),
        "Exchange": "n/a",
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
    ticker = normalize_user_symbol(ticker)
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
        "Data confidence": data_confidence_summary({**stats, **plan}).get("label", "n/a"),
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
                "Data confidence": data_confidence_summary({**row, **plan}).get("label", "n/a"),
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

        response = requests.get(SP500_SOURCE_URL, headers={"User-Agent": f"Mozilla/5.0 {APP_NAME}"}, timeout=10)
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
                "Data confidence": data_confidence_summary({**stats, **plan}).get("label", "n/a"),
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
        "Data confidence",
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
        st.caption(f"{ticker} stock selected for Charts and AI Coach.")


def show_scan_table(df: pd.DataFrame, key: str = "scan_table") -> None:
    if df.empty:
        st.info("No matches with the current filters.")
        return
    display_df = scan_columns(df)
    st.caption("Accuracy check: every row shows data confidence, data quality, source, and quote time. Open Charts for the full price audit before trusting a plan.")
    event = st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        key=key,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Ticker": st.column_config.TextColumn("Stock", pinned=True),
            "Playbook fit": st.column_config.TextColumn("Fit"),
            "Status": st.column_config.TextColumn("Status"),
            "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "Daily gain %": st.column_config.NumberColumn("Gain", format="%.1f%%"),
            "Float M": st.column_config.NumberColumn("Float", format="%.1fM"),
            "RVOL": st.column_config.NumberColumn("RVOL", format="%.1fx"),
            "AI score": st.column_config.ProgressColumn("AI score", min_value=0, max_value=100),
            "Data confidence": st.column_config.TextColumn("Data confidence"),
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
        "Data confidence",
        "Entry trigger",
        "Stop",
        "Target 1",
        "Data source",
        "Quote time",
    ]
    display_df = df[[column for column in columns if column in df.columns]]
    st.caption("Accuracy check: data confidence, source, and quote time are shown on each row. Use the chart price audit if a number looks stale or unusual.")
    event = st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        key="broad_market_table",
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Ticker": st.column_config.TextColumn("Stock", pinned=True),
            "Playbook fit": st.column_config.TextColumn("Fit"),
            "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "Daily gain %": st.column_config.NumberColumn("Gain", format="%.2f%%"),
            "RVOL": st.column_config.NumberColumn("RVOL", format="%.1fx"),
            "Volume": st.column_config.NumberColumn("Volume", format="compact"),
            "AI score": st.column_config.ProgressColumn("AI score", min_value=0, max_value=100),
            "Data confidence": st.column_config.TextColumn("Data confidence"),
        },
    )
    remember_selected_ticker(display_df, event)


def action_queue_frame(df: pd.DataFrame, limit: int = 8) -> pd.DataFrame:
    if df.empty or "Ticker" not in df.columns:
        return pd.DataFrame()

    status_rank = {
        "Breakout trigger": 0,
        "In buy zone": 1,
        "Near buy zone": 2,
        "Momentum active": 3,
        "Watching": 4,
        "Below stop": 5,
        "No quote": 6,
    }
    action_map = {
        "Breakout trigger": ("Review approval", "At or above trigger. Confirm news, spread, and risk."),
        "In buy zone": ("Wait for trigger", "Inside buy area. Do not buy until confirmation."),
        "Near buy zone": ("Watch closely", "Close to the planned area."),
        "Momentum active": ("Check chart", "Momentum is active, but the entry still needs review."),
        "Below stop": ("Skip", "Plan is invalid until a new setup forms."),
        "No quote": ("Verify data", "No usable quote returned."),
    }
    confidence_rank = {
        "High confidence": 0,
        "Usable for paper": 1,
        "Verify first": 2,
        "Practice data": 3,
        "Practice only": 4,
    }
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        raw = row.to_dict()
        ticker = normalize_user_symbol(raw.get("Ticker"))
        if not ticker:
            continue
        status = str(raw.get("Status") or live_status(raw))
        action, why = action_map.get(status, ("Study", "Use it for context until the setup improves."))
        price = safe_float(raw.get("Price"))
        entry = safe_float(raw.get("Entry")) or safe_float(raw.get("Entry trigger price"))
        stop = safe_float(raw.get("Stop")) or safe_float(raw.get("Stop price"))
        target = safe_float(raw.get("Target 1")) or safe_float(raw.get("Target 1 price"))
        distance = safe_float(raw.get("Distance to entry %"))
        if distance is None and price is not None and entry is not None and price:
            distance = (entry - price) / price * 100
        score = safe_float(raw.get("AI score"), 0) or 0
        rvol = safe_float(raw.get("RVOL"), 0) or 0
        confidence = str(raw.get("Data confidence") or data_confidence_summary(raw).get("label", "n/a"))
        rows.append(
            {
                "_Rank": status_rank.get(status, 9),
                "_ConfidenceRank": confidence_rank.get(confidence, 5),
                "Stock": ticker,
                "Action": action,
                "Status": status,
                "Price": price,
                "Entry": entry,
                "Stop": stop,
                "Target 1": target,
                "To entry %": distance,
                "AI score": score,
                "RVOL": rvol,
                "Why": why,
                "Data": raw.get("Data quality") or data_quality_badge(raw.get("Data source"))[0],
                "Confidence": confidence,
            }
        )

    if not rows:
        return pd.DataFrame()
    queue = pd.DataFrame(rows).sort_values(["_Rank", "_ConfidenceRank", "AI score", "RVOL"], ascending=[True, True, False, False]).head(limit)
    return queue.drop(columns=["_Rank", "_ConfidenceRank"]).reset_index(drop=True)


def render_action_queue(df: pd.DataFrame, key: str) -> None:
    queue = action_queue_frame(df)
    with st.container(border=True):
        st.markdown("**Live action queue**")
        st.caption("Ranked by action status first, then AI score and RVOL. Data confidence flags whether the quote is usable for paper practice. Select a row to send that stock into Charts, AI Coach, and Trade Desk.")
        if queue.empty:
            st.info("No action queue rows yet. Run a scan or add stocks to the watchlist.")
            return

        event = st.dataframe(
            queue,
            width="stretch",
            hide_index=True,
            key=key,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "Stock": st.column_config.TextColumn("Stock", pinned=True),
                "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                "Entry": st.column_config.NumberColumn("Entry", format="$%.2f"),
                "Stop": st.column_config.NumberColumn("Stop", format="$%.2f"),
                "Target 1": st.column_config.NumberColumn("Target 1", format="$%.2f"),
                "To entry %": st.column_config.NumberColumn("To entry", format="%.2f%%"),
                "AI score": st.column_config.ProgressColumn("AI score", min_value=0, max_value=100),
                "RVOL": st.column_config.NumberColumn("RVOL", format="%.1fx"),
                "Confidence": st.column_config.TextColumn("Confidence"),
            },
        )
        try:
            selected_rows = list(event.selection.rows)
        except Exception:
            selected_rows = []
        if selected_rows:
            selected = str(queue.iloc[selected_rows[0]]["Stock"])
            st.session_state.selected_ticker = selected
            with st.container(horizontal=True):
                st.badge(f"{selected} selected", icon=":material/check_circle:", color="green")
                st.caption("Open Charts, AI Coach, or Trade Desk from the left menu to continue with this stock.")


def data_health_frame(df: pd.DataFrame) -> pd.DataFrame:
    labels = ["High confidence", "Usable for paper", "Verify first", "Practice data", "Practice only"]
    counts = {label: 0 for label in labels}
    if df.empty:
        return pd.DataFrame([{"Label": label, "Rows": count} for label, count in counts.items()])

    for _, row in df.iterrows():
        raw = row.to_dict()
        label = str(raw.get("Data confidence") or data_confidence_summary(raw).get("label", "n/a"))
        if label not in counts:
            label = "Practice only" if "practice" in label.lower() else "Verify first"
        counts[label] += 1
    return pd.DataFrame([{"Label": label, "Rows": count} for label, count in counts.items()])


def render_data_health_summary(df: pd.DataFrame) -> None:
    health = data_health_frame(df)
    total = int(health["Rows"].sum()) if not health.empty else 0
    values = {str(row["Label"]): int(row["Rows"]) for _, row in health.iterrows()}
    with st.container(border=True):
        st.markdown("**Data health**")
        st.caption("Use this before trusting any scanner result. Cleaner data can still be delayed, but verify-first and practice rows need extra caution.")
        cols = st.columns(4)
        cols[0].metric("High confidence", str(values.get("High confidence", 0)), border=True)
        cols[1].metric("Usable for paper", str(values.get("Usable for paper", 0)), border=True)
        cols[2].metric("Verify first", str(values.get("Verify first", 0)), border=True)
        practice_total = values.get("Practice data", 0) + values.get("Practice only", 0)
        cols[3].metric("Practice only", str(practice_total), f"{total} total rows", border=True)


def provider_status_items() -> list[dict[str, str]]:
    alpaca_ready = alpaca_enabled()
    finnhub_ready = finnhub_enabled()
    yahoo_ready = yf is not None
    chart_ready = LIGHTWEIGHT_CHARTS_FILE.exists()
    return [
        {
            "name": "Alpaca IEX",
            "state": "Connected" if alpaca_ready else "Add paper keys",
            "tone": "ready" if alpaca_ready else "watch",
            "detail": "First choice for regular-stock intraday candles when keys are present. Free IEX feed can still be limited or delayed.",
        },
        {
            "name": "Finnhub",
            "state": "Connected" if finnhub_ready else "Add key",
            "tone": "ready" if finnhub_ready else "watch",
            "detail": "Used for quotes, company news, market news, and symbol lists. News quality depends on the free endpoint.",
        },
        {
            "name": "Yahoo fallback",
            "state": "Available" if yahoo_ready else "Package missing",
            "tone": "info" if yahoo_ready else "watch",
            "detail": "Backup candles, index symbols like S&P 500, and quote estimates when the primary free feeds cannot answer.",
        },
        {
            "name": "TradingView chart",
            "state": "Local asset" if chart_ready else "Online fallback",
            "tone": "ready" if chart_ready else "watch",
            "detail": "The app uses TradingView Lightweight Charts locally for smooth candles, zooming, volume, and level overlays.",
        },
    ]


def provider_cards_html(items: list[dict[str, str]]) -> str:
    parts = ['<div class="msa-provider-grid">']
    for item in items:
        parts.append(
            '<div class="msa-provider-card msa-provider-{tone}">'
            '<div class="msa-provider-name">{name}</div>'
            '<div class="msa-provider-state">{state}</div>'
            '<div class="msa-provider-detail">{detail}</div>'
            '</div>'.format(
                tone=html.escape(item["tone"]),
                name=html.escape(item["name"]),
                state=html.escape(item["state"]),
                detail=html.escape(item["detail"]),
            )
        )
    parts.append("</div>")
    return "".join(parts)


def render_data_stack_panel(compact: bool = False) -> None:
    items = provider_status_items()
    connected = sum(1 for item in items if item["tone"] == "ready")
    with st.container(border=True):
        st.markdown("**Data stack**")
        with st.container(horizontal=True):
            st.badge(f"{connected}/{len(items)} ready", icon=":material/database:", color="green" if connected >= 3 else "orange")
            st.badge("Free feeds", icon=":material/savings:", color="blue")
            st.badge("Paper-trading only", icon=":material/edit_note:", color="blue")
        if not compact:
            st.markdown(provider_cards_html(items), unsafe_allow_html=True)
        st.markdown(
            '<div class="msa-source-flow">'
            '<b>Source order:</b> regular-stock candles try Alpaca IEX first, then Yahoo-style chart fallback, then learning data. '
            'Quotes and news use Finnhub when available. Indexes like S&P 500 use Yahoo-style symbols because Alpaca IEX is a stock feed.'
            '</div>',
            unsafe_allow_html=True,
        )


def source_explanation(source: Any) -> str:
    source_text = str(source or "Unknown")
    lowered = source_text.lower()
    if "alpaca" in lowered:
        return "Alpaca IEX candle feed. Good free intraday source for regular stocks, but still verify fast moves and after-hours behavior."
    if "finnhub" in lowered:
        return "Finnhub quote/news feed. Useful for live context, catalysts, and scanner metadata."
    if "yahoo" in lowered:
        return "Yahoo-style fallback data. Helpful for indexes and backup candles, but free data can be delayed or rate-limited."
    if "learning" in lowered:
        return "Learning fallback data. Use it to study the app and practice the workflow, not as a live market quote."
    return "Unknown source. Verify with another quote source before trusting the number."


def render_source_brief(analysis: dict[str, Any], chart_source: str | None = None) -> None:
    active_source = str(analysis.get("Data source", "n/a"))
    chart_label = chart_source or active_source
    confidence = data_confidence_summary(analysis, chart_source)
    with st.container(border=True):
        st.markdown("**Source brief**")
        cols = st.columns(3)
        cols[0].metric("Active price source", data_quality_badge(active_source)[0], active_source, border=True)
        cols[1].metric("Chart source", data_quality_badge(chart_label)[0], str(chart_label), border=True)
        cols[2].metric("Confidence", str(confidence["label"]), f"{confidence['score']}/100", border=True)
        st.caption(source_explanation(chart_label))


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
            return sorted({clean for item in data if (clean := normalize_user_symbol(item))})
        except Exception:
            pass
    return ["BBAI", "KULR", "LUNR", "SOUN"]


def write_watchlist(tickers: list[str]) -> None:
    clean = sorted({clean_ticker for ticker in tickers if (clean_ticker := normalize_user_symbol(ticker))})
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
            "chart_grid": "rgba(148, 163, 184, 0.24)",
        }
    return {
        "app_bg": "#090C10",
        "panel": "#0B1117",
        "panel_alt": "#101821",
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
        "chart_grid": "rgba(148, 163, 184, 0.13)",
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
        .msa-provider-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 10px;
            margin: 10px 0 8px 0;
        }}
        .msa-provider-card {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            padding: 12px 13px;
            min-height: 126px;
            box-shadow: 0 12px 28px var(--msa-shadow);
        }}
        .msa-provider-card:before {{
            content: "";
            display: block;
            height: 4px;
            width: 44px;
            border-radius: 999px;
            background: var(--msa-muted-soft);
            margin-bottom: 10px;
        }}
        .msa-provider-ready:before {{background: var(--msa-up);}}
        .msa-provider-watch:before {{background: var(--msa-orange);}}
        .msa-provider-info:before {{background: var(--msa-blue);}}
        .msa-provider-name {{
            color: var(--msa-text);
            font-weight: 820;
            font-size: 1rem;
            line-height: 1.1;
        }}
        .msa-provider-state {{
            color: var(--msa-muted-soft);
            font-size: .76rem;
            font-weight: 760;
            text-transform: uppercase;
            margin-top: 5px;
        }}
        .msa-provider-detail {{
            color: var(--msa-muted);
            font-size: .84rem;
            line-height: 1.32;
            margin-top: 7px;
        }}
        .msa-source-flow {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: var(--msa-panel);
            color: var(--msa-muted);
            padding: 10px 12px;
            line-height: 1.35;
            margin-top: 8px;
        }}
        .msa-level-board {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin: 10px 0 14px 0;
        }}
        .msa-level-card {{
            position: relative;
            overflow: hidden;
            border: 1px solid var(--msa-border);
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            border-radius: 8px;
            padding: 15px 16px 14px 16px;
            box-shadow: 0 18px 36px var(--msa-shadow);
            min-height: 122px;
        }}
        .msa-level-card:before {{
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: var(--msa-muted-soft);
        }}
        .msa-level-profit:before {{background: var(--msa-up);}}
        .msa-level-danger:before {{background: var(--msa-down);}}
        .msa-level-neutral:before {{background: var(--msa-blue);}}
        .msa-level-label {{
            color: var(--msa-muted-soft);
            font-size: .78rem;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .msa-level-value {{
            color: var(--msa-text);
            font-size: clamp(1.8rem, 3vw, 2.45rem);
            font-weight: 820;
            line-height: 1.04;
            margin-top: 8px;
            letter-spacing: 0;
        }}
        .msa-level-profit .msa-level-value {{color: var(--msa-up);}}
        .msa-level-danger .msa-level-value {{color: var(--msa-down);}}
        .msa-level-detail {{
            color: var(--msa-muted);
            margin-top: 8px;
            font-size: .86rem;
            line-height: 1.25;
        }}
        .msa-compact-header {{
            margin: 0 0 10px 0;
            padding: 0;
        }}
        .msa-compact-header h1 {{
            margin: 0;
            font-size: clamp(1.7rem, 3vw, 2.35rem);
            line-height: 1.05;
            color: var(--msa-text);
        }}
        .msa-compact-header p {{
            margin: 5px 0 0 0;
            color: var(--msa-muted);
            font-size: .95rem;
        }}
        .msa-compact-header small {{
            display: block;
            margin-top: 4px;
            color: var(--msa-muted-soft);
            font-size: .78rem;
            line-height: 1.25;
        }}
        .msa-chart-stat-strip {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin: 10px 0 2px 0;
        }}
        .msa-chart-stat-card {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            padding: 10px 12px;
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            box-shadow: 0 12px 26px var(--msa-shadow);
        }}
        .msa-chart-stat-label {{
            color: var(--msa-muted-soft);
            font-size: .72rem;
            font-weight: 750;
            text-transform: uppercase;
        }}
        .msa-chart-stat-value {{
            color: var(--msa-text);
            font-size: 1.15rem;
            line-height: 1.1;
            font-weight: 800;
            margin-top: 5px;
        }}
        .msa-chart-stat-detail {{
            color: var(--msa-muted);
            font-size: .8rem;
            margin-top: 4px;
        }}
        .msa-chart-stat-up .msa-chart-stat-value {{color: var(--msa-up);}}
        .msa-chart-stat-down .msa-chart-stat-value {{color: var(--msa-down);}}
        .msa-readiness-command {{
            display: grid;
            grid-template-columns: minmax(180px, .8fr) minmax(260px, 1.4fr) minmax(160px, .8fr);
            gap: 12px;
            align-items: stretch;
            margin: 8px 0 12px 0;
        }}
        .msa-readiness-tile {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            padding: 13px 14px;
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            box-shadow: 0 14px 28px var(--msa-shadow);
        }}
        .msa-readiness-kicker {{
            color: var(--msa-muted-soft);
            font-size: .72rem;
            font-weight: 760;
            text-transform: uppercase;
        }}
        .msa-readiness-primary {{
            color: var(--msa-text);
            font-size: 1.45rem;
            font-weight: 840;
            line-height: 1.05;
            margin-top: 5px;
        }}
        .msa-readiness-detail {{
            color: var(--msa-muted);
            font-size: .84rem;
            line-height: 1.28;
            margin-top: 7px;
        }}
        .msa-readiness-ready {{border-left: 4px solid var(--msa-up);}}
        .msa-readiness-watch {{border-left: 4px solid var(--msa-orange);}}
        .msa-readiness-hold {{border-left: 4px solid var(--msa-muted-soft);}}
        .msa-readiness-danger {{border-left: 4px solid var(--msa-down);}}
        .msa-check-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(142px, 1fr));
            gap: 9px;
        }}
        .msa-check-card {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            padding: 10px 11px;
            background: var(--msa-panel);
        }}
        .msa-check-label {{
            color: var(--msa-muted-soft);
            font-size: .72rem;
            font-weight: 760;
            text-transform: uppercase;
        }}
        .msa-check-value {{
            color: var(--msa-text);
            font-size: 1rem;
            font-weight: 760;
            margin-top: 4px;
        }}
        .msa-check-ok {{border-left: 4px solid var(--msa-up);}}
        .msa-check-wait {{border-left: 4px solid var(--msa-orange);}}
        .msa-ai-command {{
            position: relative;
            overflow: hidden;
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0 14px 0;
            background:
                linear-gradient(135deg, rgba(0, 200, 5, 0.08), transparent 36%),
                linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            box-shadow: 0 18px 38px var(--msa-shadow);
        }}
        .msa-ai-command:before {{
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: var(--msa-muted-soft);
        }}
        .msa-ai-ready:before {{background: var(--msa-up);}}
        .msa-ai-watch:before {{background: var(--msa-orange);}}
        .msa-ai-danger:before {{background: var(--msa-down);}}
        .msa-ai-header {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 14px;
            margin-bottom: 12px;
        }}
        .msa-ai-kicker {{
            color: var(--msa-muted-soft);
            font-size: .72rem;
            font-weight: 780;
            letter-spacing: .04em;
            text-transform: uppercase;
        }}
        .msa-ai-title {{
            color: var(--msa-text);
            font-size: clamp(1.6rem, 3vw, 2.25rem);
            font-weight: 860;
            line-height: 1.02;
            margin-top: 4px;
        }}
        .msa-ai-detail {{
            color: var(--msa-muted);
            font-size: .92rem;
            line-height: 1.36;
            margin-top: 7px;
            max-width: 860px;
        }}
        .msa-ai-score {{
            min-width: 116px;
            text-align: right;
            color: var(--msa-text);
            font-weight: 820;
        }}
        .msa-ai-score span {{
            display: block;
            color: var(--msa-muted-soft);
            font-size: .74rem;
            font-weight: 760;
            text-transform: uppercase;
        }}
        .msa-ai-level-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }}
        .msa-ai-level {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: var(--msa-panel);
            padding: 12px;
            min-height: 104px;
        }}
        .msa-ai-level-label {{
            color: var(--msa-muted-soft);
            font-size: .72rem;
            font-weight: 780;
            text-transform: uppercase;
        }}
        .msa-ai-level-value {{
            color: var(--msa-text);
            font-size: clamp(1.35rem, 2.4vw, 1.95rem);
            font-weight: 860;
            line-height: 1.06;
            margin-top: 6px;
        }}
        .msa-ai-level-profit .msa-ai-level-value {{color: var(--msa-up);}}
        .msa-ai-level-danger .msa-ai-level-value {{color: var(--msa-down);}}
        .msa-ai-level-note {{
            color: var(--msa-muted);
            font-size: .78rem;
            line-height: 1.25;
            margin-top: 6px;
        }}
        .msa-ai-list {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: var(--msa-panel);
            padding: 12px 13px;
            height: 100%;
        }}
        .msa-ai-list strong {{
            display: block;
            color: var(--msa-text);
            margin-bottom: 7px;
        }}
        .msa-ai-list ul {{
            margin: 0;
            padding-left: 18px;
            color: var(--msa-muted);
        }}
        .msa-ai-list li {{
            margin: 5px 0;
            line-height: 1.32;
        }}
        .msa-ai-plain {{
            border: 1px solid var(--msa-border);
            border-left: 4px solid var(--msa-blue);
            border-radius: 8px;
            background: var(--msa-panel);
            color: var(--msa-muted);
            padding: 11px 13px;
            margin-top: 12px;
            line-height: 1.34;
        }}
        @media (max-width: 900px) {{
            .msa-readiness-command {{
                grid-template-columns: 1fr;
            }}
            .msa-ai-header {{
                display: block;
            }}
            .msa-ai-score {{
                text-align: left;
                margin-top: 10px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def dashboard_hero() -> None:
    st.markdown(
        f"""
        <div class="msa-hero">
            <h1>{html.escape(APP_NAME)}</h1>
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


def compact_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(
        """
        <div class="msa-compact-header">
          <h1>{title}</h1>
          {subtitle}
          <small>Educational paper-trading tool. Verify live data, news, float, halts, and risk before making real trades. This is not financial advice.</small>
        </div>
        """.format(
            title=html.escape(title),
            subtitle=f"<p>{html.escape(subtitle)}</p>" if subtitle else "",
        ),
        unsafe_allow_html=True,
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


def ai_trade_math(analysis: dict[str, Any]) -> dict[str, Any]:
    levels = chart_trade_levels(analysis)
    price = safe_float(analysis.get("Price"))
    entry = levels["entry"]
    stop = levels["stop"]
    target_1 = levels["target_1"]
    target_2 = levels["target_2"]
    risk = (entry - stop) if entry is not None and stop is not None and entry > stop else None
    reward_1 = (target_1 - entry) if target_1 is not None and entry is not None and target_1 > entry else None
    reward_2 = (target_2 - entry) if target_2 is not None and entry is not None and target_2 > entry else None
    distance = ((entry - price) / price * 100) if entry is not None and price else None
    rr_1 = reward_1 / risk if risk and reward_1 is not None else None
    rr_2 = reward_2 / risk if risk and reward_2 is not None else None
    return {
        **levels,
        "price": price,
        "risk": risk,
        "reward_1": reward_1,
        "reward_2": reward_2,
        "distance": distance,
        "rr_1": rr_1,
        "rr_2": rr_2,
    }


def ai_tone(label: str, status: str) -> tuple[str, str, str]:
    if label == "Plan invalid" or status == "Below stop":
        return "danger", "Stand down", "red"
    if label == "Trigger active" or status == "Breakout trigger":
        return "ready", "Review paper approval", "green"
    if label == "In buy zone" or status in {"In buy zone", "Near buy zone", "Momentum active"}:
        return "watch", "Watch for trigger", "orange"
    return "hold", "Wait", "gray"


def ai_now_steps(analysis: dict[str, Any], label: str, status: str) -> list[str]:
    math_data = ai_trade_math(analysis)
    entry = money(math_data["entry"])
    stop = money(math_data["stop"])
    risk = money(math_data["risk"])
    target = money(math_data["target_1"])
    confidence = data_confidence_summary(analysis).get("label", "Verify first")

    if label == "Trigger active" or status == "Breakout trigger":
        return [
            f"Confirm the last candle is holding above {entry}.",
            f"Check the stop at {stop}; planned risk is {risk} per share.",
            f"Only approve a paper order if volume, spread, news, and {confidence.lower()} data all make sense.",
        ]
    if label == "In buy zone" or status == "In buy zone":
        return [
            f"Price is in the buy area, but the actual trigger is still {entry}.",
            "Wait for buyers to prove it with a clean candle and stronger volume.",
            f"Target 1 is {target}; skip it if the reward no longer beats the risk.",
        ]
    if status in {"Near buy zone", "Momentum active"}:
        return [
            "Keep it on watch and let the setup come to you.",
            f"Set the mental alert around the buy zone and confirmation over {entry}.",
            "Do not chase a candle that runs too far above the plan.",
        ]
    if label == "Plan invalid" or status == "Below stop":
        return [
            f"The price is under the stop area near {stop}.",
            "Treat this plan as broken until a new base forms.",
            "Rebuild the entry, stop, and targets from fresh candles.",
        ]
    return [
        "Use this as a watchlist idea, not an active setup yet.",
        f"Wait for price to approach the buy zone and confirm over {entry}.",
        "Check news and volume again before approving any paper trade.",
    ]


def ai_cancel_rules(analysis: dict[str, Any]) -> list[str]:
    math_data = ai_trade_math(analysis)
    price = math_data["price"]
    entry = math_data["entry"]
    stop = math_data["stop"]
    rvol = safe_float(analysis.get("RVOL"), 0) or 0
    rules = []
    if stop is not None:
        rules.append(f"Price loses the stop area near {money(stop)}.")
    if entry is not None and price is not None and price > entry * 1.04:
        rules.append("Price is already more than 4% above the trigger and the trade is turning into a chase.")
    if rvol < DEFAULT_RULES["min_rvol"]:
        rules.append(f"RVOL is only {rvol:.1f}x, so momentum may not be strong enough yet.")
    for warning in analysis.get("Warnings", [])[:3]:
        rules.append(str(warning))
    rules.append("News turns negative, a halt appears, or the spread is too wide to paper-trade cleanly.")
    return list(dict.fromkeys(rules))[:5]


def beginner_trade_translation(analysis: dict[str, Any], label: str) -> str:
    math_data = ai_trade_math(analysis)
    entry = money(math_data["entry"])
    stop = money(math_data["stop"])
    target = money(math_data["target_1"])
    if label == "Trigger active":
        return f"Plain English: buyers may be confirming the idea now. The paper entry is around {entry}, the safety line is {stop}, and the first place to take profit is {target}."
    if label == "In buy zone":
        return f"Plain English: the stock is near the area you wanted, but beginners should still wait for confirmation near {entry} before approving anything."
    if label == "Plan invalid":
        return f"Plain English: this setup is broken because price is too close to or under the risk line. Do not reuse this plan until the chart resets."
    return f"Plain English: this is a watchlist idea. The app is telling you to wait for {entry}, know the stop at {stop}, and check that {target} pays enough reward."


def render_html_list(title: str, items: list[str]) -> str:
    parts = [f"<strong>{html.escape(title)}</strong><ul>"]
    for item in items:
        parts.append(f"<li>{html.escape(item)}</li>")
    parts.append("</ul>")
    return "".join(parts)


def render_ai_decision_panel(analysis: dict[str, Any], chart_source: str | None = None) -> None:
    label, message = ai_action_summary(analysis)
    status = live_status(analysis)
    math_data = ai_trade_math(analysis)
    tone, action, color = ai_tone(label, status)
    confidence = data_confidence_summary(analysis, chart_source)
    passed, total = setup_completion(analysis)
    score = safe_float(analysis.get("AI score"), 0) or 0
    rr_1 = f"{math_data['rr_1']:.2f}R" if math_data["rr_1"] is not None else "n/a"
    rr_2 = f"{math_data['rr_2']:.2f}R" if math_data["rr_2"] is not None else "n/a"
    distance = pct(math_data["distance"]) if math_data["distance"] is not None else "wait"
    level_items = [
        ("Current", money(math_data["price"]), status, "neutral"),
        ("Entry", money(math_data["entry"]), "Buy only after trigger", "profit"),
        ("Stop loss", money(math_data["stop"]), "Plan is wrong here", "danger"),
        ("Take profit 1", money(math_data["target_1"]), f"{rr_1} reward/risk", "profit"),
        ("Runner target", money(math_data["target_2"]), f"{rr_2} reward/risk", "profit"),
        ("Risk / share", money(math_data["risk"]), f"To entry: {distance}", "danger"),
    ]
    level_parts = ['<div class="msa-ai-level-grid">']
    for item_label, value, detail, item_tone in level_items:
        level_parts.append(
            '<div class="msa-ai-level msa-ai-level-{tone}">'
            '<div class="msa-ai-level-label">{label}</div>'
            '<div class="msa-ai-level-value">{value}</div>'
            '<div class="msa-ai-level-note">{detail}</div>'
            '</div>'.format(
                tone=html.escape(item_tone),
                label=html.escape(item_label),
                value=html.escape(value),
                detail=html.escape(str(detail)),
            )
        )
    level_parts.append("</div>")

    with st.container(border=True):
        st.markdown("**AI assistant**")
        with st.container(horizontal=True):
            st.badge(label, icon=":material/psychology:", color=color)
            st.badge(status, icon=":material/candlestick_chart:", color=color)
            st.badge(str(confidence["label"]), icon=":material/verified:", color=str(confidence["color"]))
            st.badge("Paper approval only", icon=":material/edit_note:", color="blue")

        st.markdown(
            """
            <div class="msa-ai-command msa-ai-{tone}">
                <div class="msa-ai-header">
                    <div>
                        <div class="msa-ai-kicker">AI command center</div>
                        <div class="msa-ai-title">{action}</div>
                        <div class="msa-ai-detail">{message}</div>
                    </div>
                    <div class="msa-ai-score"><span>Score</span>{score}/100<br><span>Checks</span>{passed}/{total}</div>
                </div>
                {levels}
            </div>
            """.format(
                tone=html.escape(tone),
                action=html.escape(action),
                message=html.escape(message),
                score=int(score),
                passed=passed,
                total=total,
                levels="".join(level_parts),
            ),
            unsafe_allow_html=True,
        )

        now_items = ai_now_steps(analysis, label, status)
        cancel_items = ai_cancel_rules(analysis)
        left, right = st.columns(2)
        left.markdown(
            f'<div class="msa-ai-list">{render_html_list("Do this now", now_items)}</div>',
            unsafe_allow_html=True,
        )
        right.markdown(
            f'<div class="msa-ai-list">{render_html_list("Cancel or wait if", cancel_items)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="msa-ai-plain">{html.escape(beginner_trade_translation(analysis, label))}</div>',
            unsafe_allow_html=True,
        )
        st.caption("Educational paper-trading decision aid. It does not place real trades and it is not financial advice.")


def render_trade_readiness_panel(analysis: dict[str, Any]) -> None:
    label, message = ai_action_summary(analysis)
    status = live_status(analysis)
    checks = setup_check_items(analysis)
    passed, total = setup_completion(analysis)
    levels = chart_trade_levels(analysis)
    risk_reward = safe_float(analysis.get("Risk/reward"))
    price = safe_float(analysis.get("Price"))
    entry = levels["entry"]
    distance = ((entry - price) / price * 100) if entry is not None and price else None

    tone = "hold"
    action = "Wait"
    if label == "Plan invalid" or status == "Below stop":
        tone = "danger"
        action = "Stand down"
    elif label == "Trigger active" or status in {"Breakout trigger", "In buy zone"}:
        tone = "ready"
        action = "Review approval"
    elif status in {"Near buy zone", "Momentum active"}:
        tone = "watch"
        action = "Watch closely"

    next_step = wait_coaching(analysis, label)[0] if label in {"Study only", "Watch only", "Plan invalid"} else "Confirm news, spread, volume, and risk before approving any paper order."
    command = [
        '<div class="msa-readiness-command">',
        '<div class="msa-readiness-tile msa-readiness-{tone}"><div class="msa-readiness-kicker">Paper action</div><div class="msa-readiness-primary">{action}</div><div class="msa-readiness-detail">{status}</div></div>'.format(
            tone=html.escape(tone),
            action=html.escape(action),
            status=html.escape(status),
        ),
        '<div class="msa-readiness-tile"><div class="msa-readiness-kicker">AI read</div><div class="msa-readiness-primary">{label}</div><div class="msa-readiness-detail">{message}</div></div>'.format(
            label=html.escape(label),
            message=html.escape(message),
        ),
        '<div class="msa-readiness-tile"><div class="msa-readiness-kicker">Readiness</div><div class="msa-readiness-primary">{passed}/{total}</div><div class="msa-readiness-detail">{next_step}</div></div>'.format(
            passed=passed,
            total=total,
            next_step=html.escape(next_step),
        ),
        "</div>",
    ]

    check_parts = ['<div class="msa-check-grid">']
    for name, ok, detail in checks:
        check_parts.append(
            '<div class="msa-check-card msa-check-{tone}"><div class="msa-check-label">{name}</div><div class="msa-check-value">{detail}</div></div>'.format(
                tone="ok" if ok else "wait",
                name=html.escape(name),
                detail=html.escape(str(detail)),
            )
        )
    check_parts.extend(
        [
            '<div class="msa-check-card"><div class="msa-check-label">To entry</div><div class="msa-check-value">{distance}</div></div>'.format(
                distance=html.escape(pct(distance) if distance is not None else "n/a")
            ),
            '<div class="msa-check-card"><div class="msa-check-label">R/R</div><div class="msa-check-value">{risk_reward}</div></div>'.format(
                risk_reward=html.escape(f"{risk_reward:.2f}R" if risk_reward is not None else "n/a")
            ),
            "</div>",
        ]
    )

    with st.container(border=True):
        st.markdown("**Trade readiness**")
        st.markdown("".join(command), unsafe_allow_html=True)
        st.markdown("".join(check_parts), unsafe_allow_html=True)


def render_training_progress_panel() -> None:
    known = len(st.session_state.get("learn_flash_known", []))
    review = len(st.session_state.get("learn_flash_review", []))
    quiz_score = st.session_state.get("learn_quiz_score") if st.session_state.get("learn_quiz_graded") else None
    quiz_set = st.session_state.get("learn_quiz_graded_set", "Not graded") if quiz_score is not None else "Not graded"
    with st.container(border=True):
        st.markdown("**Skill builder**")
        cols = st.columns(3)
        cols[0].metric("Known cards", str(known), border=True)
        cols[1].metric("Review pile", str(review), border=True)
        cols[2].metric("Last quiz", f"{quiz_score}/5" if quiz_score is not None else "n/a", str(quiz_set), border=True)
        st.write("- Use Flashcards for terms before the open.")
        st.write("- Use Quiz before approving paper trades.")
        st.write("- Mark weak topics for review, then check the same idea on Charts.")


def chart_timestamp_label(value: Any) -> str:
    try:
        timestamp = pd.Timestamp(value)
        if pd.isna(timestamp):
            return "n/a"
        return timestamp.strftime("%Y-%m-%d %I:%M %p")
    except Exception:
        return "n/a"


def parse_display_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text or text.lower() in {"n/a", "nan", "none"}:
        return None
    try:
        timestamp = pd.Timestamp(text)
        if pd.isna(timestamp):
            return None
        if timestamp.tzinfo is not None:
            timestamp = timestamp.tz_convert(None)
        return timestamp.to_pydatetime().replace(tzinfo=None)
    except Exception:
        return None


def quote_age_minutes(value: Any) -> float | None:
    timestamp = parse_display_timestamp(value)
    if timestamp is None:
        return None
    age = (datetime.now() - timestamp).total_seconds() / 60
    if age < -5:
        return None
    return max(age, 0)


def age_label(minutes: float | None) -> str:
    if minutes is None:
        return "time missing"
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{int(minutes)}m ago"
    if minutes < 1440:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h {mins}m ago"
    days = int(minutes // 1440)
    hours = int((minutes % 1440) // 60)
    return f"{days}d {hours}h ago"


def looks_like_last_regular_session(value: Any) -> bool:
    timestamp = parse_display_timestamp(value)
    if timestamp is None:
        return False
    age_hours = (datetime.now() - timestamp).total_seconds() / 3600
    if age_hours < 0 or age_hours > 96:
        return False
    return (timestamp.hour == 13 and timestamp.minute <= 10) or (timestamp.hour == 16 and timestamp.minute <= 10)


def data_confidence_summary(
    analysis: dict[str, Any],
    chart_source: str | None = None,
    chart_diff_pct: float | None = None,
) -> dict[str, Any]:
    source = str(analysis.get("Data source", "n/a"))
    source_text = f"{source} {chart_source or ''}".lower()
    quote_time = analysis.get("Quote time", "n/a")
    market_state = str(analysis.get("Market state", "n/a")).upper()
    age_minutes = quote_age_minutes(quote_time)
    score = 100
    notes: list[str] = []

    if "learning" in source_text:
        return {
            "label": "Practice data",
            "color": "orange",
            "score": 25,
            "age": age_label(age_minutes),
            "detail": "This view includes learning fallback data, so use it for practice only.",
        }

    if "alpaca" in source_text:
        notes.append("Alpaca IEX candle data is available.")
    elif "finnhub" in source_text:
        notes.append("Finnhub live quote is available.")
    elif "yahoo" in source_text:
        score -= 5
        notes.append("Yahoo data is available, but free feeds can be delayed.")
    else:
        score -= 20
        notes.append("The active source is not a recognized live quote feed.")

    if chart_diff_pct is not None:
        if chart_diff_pct > 1.0:
            score -= 30
            notes.append("The chart candle and active quote differ by more than 1%.")
        elif chart_diff_pct > 0.35:
            score -= 8
            notes.append("The chart candle and active quote are close, but not identical.")
        else:
            notes.append("The chart candle and active quote are closely aligned.")

    if age_minutes is None:
        score -= 12
        notes.append("The quote time is missing.")
    elif age_minutes <= 20:
        notes.append("The quote timestamp looks fresh.")
    elif "CLOSED" in market_state or "POST" in market_state or looks_like_last_regular_session(quote_time):
        score -= 5
        notes.append("The quote looks like a last regular-session print, which is normal after hours.")
    elif age_minutes <= 120:
        score -= 12
        notes.append("The quote may be delayed.")
    elif age_minutes <= 1440:
        score -= 22
        notes.append("The quote is older than a normal live check.")
    else:
        score -= 35
        notes.append("The quote is more than a day old.")

    score = max(0, min(100, int(score)))
    if score >= 85:
        label, color = "High confidence", "green"
    elif score >= 65:
        label, color = "Usable for paper", "blue"
    elif score >= 45:
        label, color = "Verify first", "orange"
    else:
        label, color = "Practice only", "red"

    return {
        "label": label,
        "color": color,
        "score": score,
        "age": age_label(age_minutes),
        "detail": " ".join(notes),
    }


def price_audit_frame(
    ticker: str,
    history: pd.DataFrame,
    analysis: dict[str, Any],
    chart_source: str,
) -> pd.DataFrame:
    plan_price = safe_float(analysis.get("Price"))
    rows: list[dict[str, Any]] = []

    def add_row(source: str, price: float | None, timestamp: str, notes: str) -> None:
        diff = (price - plan_price) if price is not None and plan_price is not None else None
        diff_pct = (diff / plan_price * 100) if diff is not None and plan_price else None
        rows.append(
            {
                "Source": source,
                "Price": price,
                "Difference": diff,
                "Difference %": diff_pct,
                "Time": timestamp,
                "Notes": notes,
            }
        )

    add_row(
        "Active app price",
        plan_price,
        str(analysis.get("Quote time", "n/a")),
        str(analysis.get("Data source", "n/a")),
    )

    if history is not None and not history.empty:
        last = history.iloc[-1]
        add_row(
            "Chart last candle",
            safe_float(last.get("Close")),
            chart_timestamp_label(history.index[-1]),
            chart_source,
        )

    finnhub_stats = finnhub_quote_stats(ticker)
    if finnhub_stats:
        add_row(
            "Finnhub quote",
            safe_float(finnhub_stats.get("Price")),
            str(finnhub_stats.get("Quote time", "n/a")),
            str(finnhub_stats.get("Market state", "n/a")),
        )

    yahoo_stats = yahoo_quote_stats(ticker)
    if yahoo_stats:
        add_row(
            "Yahoo quote",
            safe_float(yahoo_stats.get("Price")),
            str(yahoo_stats.get("Quote time", "n/a")),
            str(yahoo_stats.get("Market state", "n/a")),
        )

    return pd.DataFrame(rows)


def render_price_audit_panel(
    ticker: str,
    history: pd.DataFrame,
    analysis: dict[str, Any],
    chart_source: str,
) -> None:
    audit = price_audit_frame(ticker, history, analysis, chart_source)
    plan_price = safe_float(analysis.get("Price"))
    chart_price = None
    if history is not None and not history.empty:
        chart_price = safe_float(history.iloc[-1].get("Close"))
    chart_diff_pct = abs((chart_price - plan_price) / plan_price * 100) if chart_price is not None and plan_price else None
    live_rows = audit[audit["Source"].isin(["Finnhub quote", "Yahoo quote"])] if not audit.empty else pd.DataFrame()
    confidence = data_confidence_summary(analysis, chart_source, chart_diff_pct)

    status_label = "Price source unknown"
    status_color = "gray"
    if "learning" in str(chart_source).lower():
        status_label = "Learning fallback"
        status_color = "orange"
    elif plan_price is None:
        status_label = "No active quote"
        status_color = "red"
    elif chart_diff_pct is not None and chart_diff_pct > 1.0:
        status_label = "Price mismatch"
        status_color = "orange"
    elif not live_rows.empty:
        status_label = "Quote checked"
        status_color = "green"

    with st.container(border=True):
        st.markdown("**Price audit**")
        with st.container(horizontal=True):
            st.badge(status_label, icon=":material/price_check:", color=status_color)
            st.badge(str(confidence["label"]), icon=":material/verified:", color=str(confidence["color"]))
            st.badge(str(analysis.get("Data source", "n/a")), icon=":material/database:", color=data_quality_badge(analysis.get("Data source"))[1])
            st.badge(str(chart_source), icon=":material/candlestick_chart:", color=data_quality_badge(chart_source)[1])

        cols = st.columns(4)
        cols[0].metric("Active price", money(plan_price), border=True)
        cols[1].metric("Chart last", money(chart_price), border=True)
        cols[2].metric("Chart difference", pct(chart_diff_pct), border=True)
        cols[3].metric("Quote age", str(confidence["age"]), str(analysis.get("Quote time", "n/a")), border=True)

        st.progress(float(confidence["score"]) / 100)
        st.caption(f"Data confidence: {confidence['score']}/100. {confidence['detail']}")

        if status_label == "Price mismatch":
            st.warning(
                "The chart candle and active quote are not matching closely. This can happen with delayed/free feeds, premarket/after-hours data, or fast-moving stocks.",
                icon=":material/warning:",
            )
        elif status_label == "Learning fallback":
            st.warning(
                "This stock is using learning fallback data. Do not treat these prices as live market prices.",
                icon=":material/school:",
            )
        elif confidence["label"] in {"Verify first", "Practice only"}:
            st.warning(
                "Verify this stock in Charts and with your broker or another quote source before using the plan, even for paper practice.",
                icon=":material/fact_check:",
            )
        else:
            st.caption("Free feeds can still be delayed. Use this panel to verify the source and time before trusting a paper-trade plan.")

        if not audit.empty:
            st.dataframe(
                audit,
                width="stretch",
                hide_index=True,
                column_config={
                    "Source": st.column_config.TextColumn("Source", pinned=True),
                    "Price": st.column_config.NumberColumn("Price", format="$%.4f"),
                    "Difference": st.column_config.NumberColumn("Diff", format="$%.4f"),
                    "Difference %": st.column_config.NumberColumn("Diff %", format="%.3f%%"),
                },
            )


def asset_type_label(analysis: dict[str, Any]) -> str:
    ticker = str(analysis.get("Ticker", "")).upper()
    sector = str(analysis.get("Sector", "")).lower()
    if ticker.startswith("^") or "index" in sector:
        return "market index"
    if ticker in {"SPY", "QQQ", "IWM", "DIA"} or "etf" in sector:
        return "ETF"
    return "stock"


def article_for(label: str) -> str:
    return "an" if label[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def beginner_movement_text(analysis: dict[str, Any], asset_type: str) -> str:
    price = safe_float(analysis.get("Price"))
    gain = safe_float(analysis.get("Daily gain %"))
    previous = safe_float(analysis.get("Previous close"))
    if price is None:
        return f"The app does not have a usable live price for this {asset_type} yet."
    if gain is None:
        return f"It is trading around {money(price)}. The app does not have enough data to explain today's move yet."
    if abs(gain) < 0.15:
        return f"It is trading around {money(price)}, nearly flat versus the last close."
    direction = "up" if gain > 0 else "down"
    pressure = "buyers are pushing it higher" if gain > 0 else "sellers are pressuring it lower"
    previous_text = f" from the previous close near {money(previous)}" if previous else ""
    return f"It is trading around {money(price)}, {direction} {pct(abs(gain))}{previous_text}. In plain English, {pressure} today."


def beginner_attention_text(analysis: dict[str, Any]) -> str:
    rvol = safe_float(analysis.get("RVOL"))
    volume = safe_float(analysis.get("Volume"))
    volume_text = compact_number(volume) if volume is not None else "n/a"
    if rvol is None:
        return f"Volume is {volume_text}, but the app cannot compare it with normal activity yet."
    if rvol >= 5:
        level = "extremely high"
    elif rvol >= 3:
        level = "high"
    elif rvol >= 1.5:
        level = "picking up"
    else:
        level = "quiet"
    return f"Volume is {volume_text}. RVOL is {rvol:.1f}x, which means attention is {level} versus normal trading."


def beginner_float_text(analysis: dict[str, Any], asset_type: str) -> str:
    float_m = safe_float(analysis.get("Float M"))
    if asset_type in {"ETF", "market index"}:
        return f"This is {article_for(asset_type)} {asset_type}, so the small-float scanner rule is mainly market context here."
    if float_m is None:
        return "The app does not have a float estimate yet. That makes small-cap risk harder to judge."
    if float_m <= DEFAULT_RULES["max_float_m"]:
        return f"Float is about {float_m:.1f}M shares, which is low enough to match the app's small-float momentum rule."
    return f"Float is about {float_m:.1f}M shares, above the app's preferred small-float rule. It may move differently than a low-float runner."


def first_readable(items: list[Any] | tuple[Any, ...], fallback: str, limit: int = 2) -> str:
    clean = [str(item).strip() for item in items if str(item).strip()]
    if not clean:
        return fallback
    if len(clean) == 1 or limit == 1:
        return clean[0]
    return "; ".join(clean[:limit])


def stock_fact_sheet_frame(analysis: dict[str, Any], chart_source: str | None = None) -> pd.DataFrame:
    asset_type = asset_type_label(analysis)
    confidence = data_confidence_summary(analysis, chart_source)
    return pd.DataFrame(
        [
            {
                "Fact": "Company/name",
                "Value": str(analysis.get("Company", analysis.get("Ticker", "n/a"))),
                "Beginner meaning": "The business, ETF, or index you are studying.",
            },
            {
                "Fact": "Type",
                "Value": asset_type,
                "Beginner meaning": "Stocks, ETFs, and indexes behave differently. Small-float rules mostly apply to stocks.",
            },
            {
                "Fact": "Exchange",
                "Value": str(analysis.get("Exchange", "n/a")),
                "Beginner meaning": "Where the quote is listed or reported from.",
            },
            {
                "Fact": "Market state",
                "Value": str(analysis.get("Market state", "n/a")),
                "Beginner meaning": "Tells whether the feed is regular, premarket, after-hours, closed, chart-derived, or practice data.",
            },
            {
                "Fact": "Previous close",
                "Value": money(safe_float(analysis.get("Previous close"))),
                "Beginner meaning": "The reference price used to understand today's move.",
            },
            {
                "Fact": "Volume",
                "Value": compact_number(safe_float(analysis.get("Volume"))),
                "Beginner meaning": "How many shares traded in the current feed window.",
            },
            {
                "Fact": "Average volume",
                "Value": compact_number(safe_float(analysis.get("Average volume"))),
                "Beginner meaning": "Normal activity estimate used to calculate RVOL.",
            },
            {
                "Fact": "Float estimate",
                "Value": f"{safe_float(analysis.get('Float M'), 0) or 0:.1f}M",
                "Beginner meaning": "Lower float can move faster, but the estimate may come from a profile source.",
            },
            {
                "Fact": "Float source",
                "Value": str(analysis.get("Float source", "n/a")),
                "Beginner meaning": "Shows whether float came from Yahoo, a shares-outstanding proxy, or a local estimate.",
            },
            {
                "Fact": "Quote source",
                "Value": str(analysis.get("Data source", "n/a")),
                "Beginner meaning": "Where the active price came from.",
            },
            {
                "Fact": "Quote age",
                "Value": str(confidence["age"]),
                "Beginner meaning": "How old the displayed quote time looks from this computer.",
            },
            {
                "Fact": "Confidence",
                "Value": f"{confidence['label']} ({confidence['score']}/100)",
                "Beginner meaning": "Quick trust check based on source, quote age, fallback data, and mismatch risk.",
            },
        ]
    )


def risk_math_frame(analysis: dict[str, Any], paper_risk: float = 25.0) -> pd.DataFrame:
    levels = chart_trade_levels(analysis)
    entry = levels["entry"]
    stop = levels["stop"]
    target_1 = levels["target_1"]
    target_2 = levels["target_2"]
    risk_per_share = (entry - stop) if entry is not None and stop is not None else None
    reward_1 = (target_1 - entry) if target_1 is not None and entry is not None else None
    reward_2 = (target_2 - entry) if target_2 is not None and entry is not None else None
    rr_1 = (reward_1 / risk_per_share) if reward_1 is not None and risk_per_share and risk_per_share > 0 else None
    rr_2 = (reward_2 / risk_per_share) if reward_2 is not None and risk_per_share and risk_per_share > 0 else None
    shares = math.floor(paper_risk / risk_per_share) if risk_per_share and risk_per_share > 0 else None

    return pd.DataFrame(
        [
            {
                "Question": "What is the planned entry?",
                "Answer": money(entry),
                "Beginner meaning": "This is the confirmation price the practice plan waits for.",
            },
            {
                "Question": "What is the planned stop?",
                "Answer": money(stop),
                "Beginner meaning": "This is where the idea is wrong.",
            },
            {
                "Question": "Risk per share",
                "Answer": money(risk_per_share),
                "Beginner meaning": "Entry minus stop. This is the amount at risk on each paper share.",
            },
            {
                "Question": "Reward to take profit 1",
                "Answer": money(reward_1),
                "Beginner meaning": f"About {rr_1:.2f}R if target 1 hits." if rr_1 is not None else "Needs valid entry, stop, and target.",
            },
            {
                "Question": "Reward to runner target",
                "Answer": money(reward_2),
                "Beginner meaning": f"About {rr_2:.2f}R if the runner target hits." if rr_2 is not None else "Needs valid entry, stop, and target.",
            },
            {
                "Question": f"Example with {money(paper_risk)} paper risk",
                "Answer": f"{shares:,} shares" if shares else "n/a",
                "Beginner meaning": "This is practice position-size math, not a real-trade recommendation.",
            },
        ]
    )


def render_beginner_stock_summary(analysis: dict[str, Any], chart_source: str | None = None) -> None:
    ticker = str(analysis.get("Ticker", "Stock"))
    company = str(analysis.get("Company", ticker))
    sector = str(analysis.get("Sector", "n/a"))
    source = str(analysis.get("Data source", "n/a"))
    quote_time = str(analysis.get("Quote time", "n/a"))
    asset_type = asset_type_label(analysis)
    action_label, action_text = ai_action_summary(analysis)
    status = live_status(analysis)
    fit = str(analysis.get("Playbook fit", playbook_fit_label(analysis, analysis.get("AI score"))))
    data_quality, data_color = data_quality_badge(source)
    levels = chart_trade_levels(analysis)
    warnings = [str(item) for item in analysis.get("Warnings", [])]
    reasons = [str(item) for item in analysis.get("Reasons", [])]
    catalyst = str(analysis.get("Catalyst", "")).strip()
    confidence = data_confidence_summary(analysis, chart_source)

    with st.container(border=True):
        st.markdown("**Plain-English stock guide**")
        with st.container(horizontal=True):
            st.badge(action_label, icon=":material/psychology:", color="green" if action_label in {"Trigger active", "In buy zone"} else "orange")
            st.badge(status, icon=":material/radar:", color="green" if status in {"Breakout trigger", "In buy zone"} else "blue")
            st.badge(fit, icon=":material/filter_alt:", color=playbook_fit_color(fit))
            st.badge(data_quality, icon=":material/database:", color=data_color)
            st.badge(str(confidence["label"]), icon=":material/verified:", color=str(confidence["color"]))

        cols = st.columns(4)
        cols[0].metric("Stock", ticker, company[:34], border=True)
        cols[1].metric("Price now", money(safe_float(analysis.get("Price"))), pct(safe_float(analysis.get("Daily gain %"))), border=True)
        cols[2].metric("Attention", f"{safe_float(analysis.get('RVOL'), 0) or 0:.1f}x RVOL", compact_number(safe_float(analysis.get("Volume"))), border=True)
        cols[3].metric("AI score", f"{int(safe_float(analysis.get('AI score'), 0) or 0)}/100", str(analysis.get("Setup", "n/a")), border=True)

        st.markdown(markdown_text(f"**What it is:** {ticker} is {article_for(asset_type)} {asset_type}. Company/name: {company}. Group: {sector}."))
        st.markdown(markdown_text(f"**What is happening:** {beginner_movement_text(analysis, asset_type)}"))
        st.markdown(markdown_text(f"**Why traders care:** {first_readable(reasons, catalyst or 'The app has not found a strong rule-based reason yet.')}"))
        st.markdown(markdown_text(f"**What the AI helper says:** {action_text}"))

        with st.expander("Stock facts in plain English", expanded=False, icon=":material/fact_check:"):
            st.dataframe(stock_fact_sheet_frame(analysis, chart_source), width="stretch", hide_index=True)

        level_rows = pd.DataFrame(
            [
                {
                    "Level": "Buy zone",
                    "Number": f"{money(levels['buy_low'])} - {money(levels['buy_high'])}",
                    "Beginner meaning": "The practice area where a pullback still looks controlled.",
                },
                {
                    "Level": "Entry trigger",
                    "Number": money(levels["entry"]),
                    "Beginner meaning": "The confirmation price. Beginners should avoid guessing before this.",
                },
                {
                    "Level": "Stop loss",
                    "Number": money(levels["stop"]),
                    "Beginner meaning": "Where the plan is wrong. If this is hit, the practice idea is invalid.",
                },
                {
                    "Level": "Take profit 1",
                    "Number": money(levels["target_1"]),
                    "Beginner meaning": "The first planned area to lock in paper-trade reward.",
                },
                {
                    "Level": "Runner target",
                    "Number": money(levels["target_2"]),
                    "Beginner meaning": "A second planned exit if the move keeps working.",
                },
            ]
        )
        st.dataframe(level_rows, width="stretch", hide_index=True)

        with st.expander("Risk and reward math", expanded=False, icon=":material/calculate:"):
            st.caption("Paper-trade math example. Always adjust risk yourself and never treat the example share size as financial advice.")
            st.dataframe(risk_math_frame(analysis), width="stretch", hide_index=True)

        explain_cols = st.columns(2)
        with explain_cols[0]:
            st.markdown("**Beginner read**")
            st.write(f"- {beginner_attention_text(analysis)}")
            st.write(f"- {beginner_float_text(analysis, asset_type)}")
            st.write("- Entry, stop, and targets are study levels. They are not a guarantee and they are not financial advice.")
        with explain_cols[1]:
            st.markdown("**Data trust check**")
            st.write(f"- Active price source: {source}")
            st.write(f"- Quote time: {quote_time} ({confidence['age']})")
            st.write(f"- Chart candle source: {chart_source or source}")
            st.write(f"- Confidence: {confidence['label']} ({confidence['score']}/100)")
            if "learning" in f"{source} {chart_source}".lower():
                st.warning("This stock is using learning fallback data somewhere in the view. Treat it as practice only.", icon=":material/school:")
            elif warnings:
                st.write(f"- Main caution: {first_readable(warnings, 'No major warning.', limit=1)}")
            else:
                st.write("- No major rule warning from the current model, but still verify news, spread, and risk.")


def chart_trade_levels(analysis: dict[str, Any]) -> dict[str, float | None]:
    buy_low = safe_float(analysis.get("Buy low"))
    buy_high = safe_float(analysis.get("Buy high"))
    buy_mid = None
    if buy_low is not None and buy_high is not None:
        buy_mid = (buy_low + buy_high) / 2
    return {
        "buy_low": buy_low,
        "buy_high": buy_high,
        "buy_mid": buy_mid,
        "entry": safe_float(analysis.get("Entry trigger price")),
        "stop": safe_float(analysis.get("Stop price")),
        "target_1": safe_float(analysis.get("Target 1 price")),
        "target_2": safe_float(analysis.get("Target 2 price")),
    }


def render_ai_chart_trade_map(analysis: dict[str, Any]) -> None:
    levels = chart_trade_levels(analysis)
    status = live_status(analysis)
    label, _ = ai_action_summary(analysis)
    with st.container(border=True):
        st.markdown("**AI chart trade map**")
        with st.container(horizontal=True):
            st.badge(label, icon=":material/psychology:", color="green" if status in {"Breakout trigger", "In buy zone"} else "orange" if status in {"Near buy zone", "Momentum active"} else "gray")
            st.badge(status, icon=":material/candlestick_chart:", color="green" if status in {"Breakout trigger", "In buy zone"} else "orange" if status == "Near buy zone" else "gray")
            st.badge("Paper-trade only", icon=":material/edit_note:", color="blue")

        cols = st.columns(4)
        cols[0].metric("Watch buy area", analysis.get("Buy zone", "n/a"), border=True)
        cols[1].metric("Buy only after", money(levels["entry"]), border=True)
        cols[2].metric("Stop if wrong", money(levels["stop"]), border=True)
        cols[3].metric("Sell / trim target", money(levels["target_1"]), border=True)
        st.caption(
            "The chart markers show the paper buy area, confirmation trigger, invalidation stop, and sell/trim targets. "
            "They are decision aids, not real trade instructions."
        )


def render_premium_trade_ticket(analysis: dict[str, Any]) -> None:
    levels = chart_trade_levels(analysis)
    price = safe_float(analysis.get("Price"))
    entry = levels["entry"]
    stop = levels["stop"]
    target = levels["target_1"]
    risk = (entry - stop) if entry is not None and stop is not None else None
    reward = (target - entry) if target is not None and entry is not None else None
    risk_reward = (reward / risk) if risk and reward is not None and risk > 0 else None
    distance = ((entry - price) / price * 100) if entry is not None and price else None
    status = live_status(analysis)
    with st.container(border=True):
        st.markdown("**Trade ticket preview**")
        items = [
            ("Current", money(price), status, "neutral"),
            ("Entry trigger", money(entry), "Buy only after confirmation", "profit"),
            ("Stop loss", money(stop), f"Risk per share {money(risk)}" if risk else "Risk defined here", "danger"),
            ("Take profit 1", money(target), f"Reward {money(reward)}" if reward else "First trim target", "profit"),
            ("Take profit 2", money(levels["target_2"]), "Runner target", "profit"),
        ]
        card_parts = ['<div class="msa-level-board">']
        for label, value, detail, tone in items:
            card_parts.append(
                '<div class="msa-level-card msa-level-{tone}">'
                '<div class="msa-level-label">{label}</div>'
                '<div class="msa-level-value">{value}</div>'
                '<div class="msa-level-detail">{detail}</div>'
                '</div>'.format(
                    tone=html.escape(tone),
                    label=html.escape(label),
                    value=html.escape(value),
                    detail=html.escape(str(detail)),
                )
            )
        card_parts.append("</div>")
        st.markdown("".join(card_parts), unsafe_allow_html=True)
        cols = st.columns(3)
        cols[0].metric("Distance to entry", pct(distance) if distance is not None else "wait", border=True)
        cols[1].metric("Target 1 R:R", f"{risk_reward:.2f}R" if risk_reward is not None else "n/a", border=True)
        cols[2].metric("Playbook fit", str(analysis.get("Playbook fit", "n/a")), border=True)
        st.caption("Paper-trade preview only. Confirm news, spread, volume, and broker rules before any real order.")


def chart_timestamp_seconds(value: Any) -> int:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return int(timestamp.timestamp())


def chart_series_points(chart_df: pd.DataFrame, column: str) -> list[dict[str, float | int]]:
    if column not in chart_df.columns:
        return []
    rows: list[dict[str, float | int]] = []
    for _, row in chart_df.dropna(subset=[column]).iterrows():
        value = safe_float(row.get(column))
        if value is None or not math.isfinite(value):
            continue
        rows.append({"time": chart_timestamp_seconds(row["Time"]), "value": round(float(value), 4)})
    return rows


@st.cache_data(show_spinner=False)
def lightweight_charts_script() -> str:
    if LIGHTWEIGHT_CHARTS_FILE.exists():
        try:
            return LIGHTWEIGHT_CHARTS_FILE.read_text(encoding="utf-8").replace("</script", "<\\/script")
        except Exception:
            return ""
    return ""


def lightweight_chart_payload(
    chart_df: pd.DataFrame,
    analysis: dict[str, Any],
    current_price: float,
    visible_candles: int | None,
) -> dict[str, Any]:
    clean_df = chart_df.replace([np.inf, -np.inf], np.nan).dropna(subset=["Open", "High", "Low", "Close"]).copy()
    candles: list[dict[str, float | int]] = []
    volume: list[dict[str, float | int | str]] = []
    palette = theme_palette()
    up = "#00C805"
    down = "#FF375F"

    for _, row in clean_df.iterrows():
        candle_time = chart_timestamp_seconds(row["Time"])
        open_price = float(row["Open"])
        close_price = float(row["Close"])
        candles.append(
            {
                "time": candle_time,
                "open": round(open_price, 4),
                "high": round(float(row["High"]), 4),
                "low": round(float(row["Low"]), 4),
                "close": round(close_price, 4),
            }
        )
        volume.append(
            {
                "time": candle_time,
                "value": max(float(row.get("Volume", 0) or 0), 0),
                "color": "rgba(0, 200, 5, 0.42)" if close_price >= open_price else "rgba(255, 55, 95, 0.38)",
            }
        )

    active_end_index = len(candles) - 1
    for index in range(len(candles) - 1, -1, -1):
        candle = candles[index]
        vol = safe_float(volume[index].get("value"), 0) if index < len(volume) else 0
        has_range = abs(float(candle["high"]) - float(candle["low"])) > 0.001
        has_body = abs(float(candle["close"]) - float(candle["open"])) > 0.001
        if (vol or 0) > 0 and (has_range or has_body):
            active_end_index = index
            break

    levels = chart_trade_levels(analysis)
    price_lines: list[dict[str, Any]] = []

    def add_price_line(label: str, value: float | None, color: str, style: str = "dashed") -> None:
        if value is not None and math.isfinite(float(value)):
            price_lines.append(
                {
                    "title": label,
                    "price": round(float(value), 4),
                    "color": color,
                    "style": style,
                }
            )

    add_price_line("Current", safe_float(current_price), palette["text"], "solid")
    add_price_line("Buy low", levels["buy_low"], "#6B7280")
    add_price_line("Buy high", levels["buy_high"], "#6B7280")
    add_price_line("Entry", levels["entry"], up)
    add_price_line("Stop", levels["stop"], down)
    add_price_line("TP1", levels["target_1"], up)
    add_price_line("TP2", levels["target_2"], "#86EFAC")

    markers: list[dict[str, Any]] = []
    if candles:
        last_time = candles[-1]["time"]
        status = live_status(analysis)
        if status in {"Breakout trigger", "In buy zone", "Near buy zone"}:
            markers.append(
                {
                    "time": last_time,
                    "position": "belowBar",
                    "color": up,
                    "shape": "arrowUp",
                    "text": "AI entry watch",
                }
            )
        elif status == "Below stop":
            markers.append(
                {
                    "time": last_time,
                    "position": "aboveBar",
                    "color": down,
                    "shape": "square",
                    "text": f"Stop broken {money(levels['stop'])}",
                }
            )

    return {
        "ticker": str(analysis.get("Ticker", "Stock")),
        "candles": candles,
        "volume": volume,
        "ema9": chart_series_points(clean_df, "EMA 9"),
        "ema20": chart_series_points(clean_df, "EMA 20"),
        "vwap": chart_series_points(clean_df, "VWAP"),
        "priceLines": price_lines,
        "markers": markers,
        "visibleCount": int(visible_candles or min(len(candles), 390)),
        "activeEndIndex": int(active_end_index),
        "palette": palette,
        "status": live_status(analysis),
    }


def render_lightweight_trading_chart(
    chart_df: pd.DataFrame,
    analysis: dict[str, Any],
    current_price: float,
    height: int,
    visible_candles: int | None,
) -> bool:
    payload = lightweight_chart_payload(chart_df, analysis, current_price, visible_candles)
    if not payload["candles"]:
        return False

    chart_height = max(height + 190, 660)
    chart_script = lightweight_charts_script()
    chart_loader = (
        f"<script>\n{chart_script}\n</script>"
        if chart_script
        else '<script src="https://unpkg.com/lightweight-charts@4.2.3/dist/lightweight-charts.standalone.production.js"></script>'
    )
    component_html = """
<div class="tw-shell">
  <div class="tw-toolbar">
    <div class="tw-brand">
      <strong>TradingView-style candles</strong>
      <span id="tw-status"></span>
      <a class="tw-credit" href="https://www.tradingview.com/" target="_blank" rel="noreferrer">Lightweight Charts by TradingView</a>
    </div>
    <div class="tw-buttons" aria-label="Chart zoom buttons">
      <span>Zoom</span>
      <button data-range="30">30</button>
      <button data-range="45">45 candles</button>
      <button data-range="90">90</button>
      <button data-range="180">180</button>
      <button data-range="390">390 / day</button>
      <button data-range="all">Context</button>
    </div>
  </div>
  <div class="tw-subbar">
    <div id="tw-legend" class="tw-legend"></div>
    <div class="tw-hint">Wheel zoom | Drag pan | Double-click reset</div>
  </div>
  <div class="tw-stage">
    <div id="tw-chart" class="tw-chart"></div>
    <canvas id="tw-wick-layer" class="tw-wick-layer" aria-hidden="true"></canvas>
    <div class="tw-watermark">__TICKER__</div>
  </div>
</div>
__LIGHTWEIGHT_CHARTS_LOADER__
<script>
(() => {
  const payload = __PAYLOAD__;
  const palette = payload.palette;
  const shell = document.querySelector(".tw-shell");
  const container = document.getElementById("tw-chart");
  const wickCanvas = document.getElementById("tw-wick-layer");
  const wickContext = wickCanvas.getContext("2d");
  const legend = document.getElementById("tw-legend");
  const status = document.getElementById("tw-status");
  const fmt = (value) => Number.isFinite(Number(value)) ? "$" + Number(value).toFixed(2) : "n/a";
  const fmtVol = (value) => Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
  const fmtTime = (time) => new Date(Number(time) * 1000).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });

  status.textContent = payload.ticker + " | " + payload.status;
  if (!window.LightweightCharts) {
    container.innerHTML = "<div class='tw-error'>The chart library did not load. Switch Chart style to Backup Plotly in Chart controls.</div>";
    return;
  }

  const chart = LightweightCharts.createChart(container, {
    width: container.clientWidth,
    height: container.clientHeight,
    layout: {
      background: { type: "solid", color: palette.panel },
      textColor: palette.text,
      fontFamily: "Inter, Arial, sans-serif"
    },
    grid: {
      vertLines: { color: palette.chart_grid || palette.grid },
      horzLines: { color: palette.chart_grid || palette.grid }
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
      vertLine: { color: palette.muted_soft, width: 1, style: LightweightCharts.LineStyle.Dashed, labelBackgroundColor: palette.blue },
      horzLine: { color: palette.muted_soft, width: 1, style: LightweightCharts.LineStyle.Dashed, labelBackgroundColor: palette.blue }
    },
    localization: {
      priceFormatter: fmt,
      timeFormatter: fmtTime
    },
    rightPriceScale: {
      borderColor: palette.border,
      scaleMargins: { top: 0.08, bottom: 0.14 },
      entireTextOnly: true,
      ticksVisible: true,
      minimumWidth: 78
    },
    timeScale: {
      borderColor: palette.border,
      timeVisible: true,
      secondsVisible: false,
      rightOffset: 12,
      barSpacing: 18,
      minBarSpacing: 8,
      fixLeftEdge: false,
      fixRightEdge: false,
      lockVisibleTimeRangeOnResize: true,
      rightBarStaysOnScroll: true,
      shiftVisibleRangeOnNewBar: true
    },
    handleScroll: {
      mouseWheel: true,
      pressedMouseMove: true,
      horzTouchDrag: true,
      vertTouchDrag: true
    },
    handleScale: {
      axisPressedMouseMove: true,
      mouseWheel: true,
      priceScale: true,
      pinch: true
    }
  });

  const ro = new ResizeObserver((entries) => {
    const entry = entries[0];
    if (!entry) return;
    const width = Math.max(Math.floor(entry.contentRect.width), 320);
    const height = Math.max(Math.floor(entry.contentRect.height), 360);
    chart.applyOptions({ width, height });
    requestAnimationFrame(drawWicks);
  });
  ro.observe(container);

  const candleSeries = chart.addCandlestickSeries({
    upColor: "#00C805",
    downColor: "#FF375F",
    borderVisible: true,
    borderUpColor: "#00C805",
    borderDownColor: "#FF375F",
    wickUpColor: "#00C805",
    wickDownColor: "#FF375F",
    wickVisible: true,
    priceFormat: { type: "price", precision: 2, minMove: 0.01 },
    lastValueVisible: true,
    priceLineVisible: true,
    priceLineColor: palette.text,
    priceLineWidth: 1,
    priceLineStyle: LightweightCharts.LineStyle.Dotted,
    autoscaleInfoProvider: (original) => {
      const result = original();
      if (!result || !result.priceRange) return result;
      const minValue = Number(result.priceRange.minValue);
      const maxValue = Number(result.priceRange.maxValue);
      if (!Number.isFinite(minValue) || !Number.isFinite(maxValue)) return result;
      const span = Math.max(maxValue - minValue, Math.max(Math.abs(maxValue) * 0.0025, 0.02));
      return {
        priceRange: {
          minValue: minValue - span * 0.16,
          maxValue: maxValue + span * 0.18
        },
        margins: {
          above: 8,
          below: 10
        }
      };
    }
  });
  candleSeries.setData(payload.candles);

  const volumeSeries = chart.addHistogramSeries({
    priceFormat: { type: "volume" },
    priceScaleId: "volume",
    lastValueVisible: false,
    priceLineVisible: false
  });
  volumeSeries.setData(payload.volume);
  chart.priceScale("volume").applyOptions({
    scaleMargins: { top: 0.88, bottom: 0 },
    visible: false
  });

  const addLineSeries = (data, color, title, width) => {
    if (!data.length) return;
    const series = chart.addLineSeries({
      color,
      lineWidth: width,
      title,
      priceLineVisible: false,
      lastValueVisible: false
    });
    series.setData(data);
  };
  addLineSeries(payload.ema9, palette.blue, "EMA 9", 2);
  addLineSeries(payload.ema20, palette.violet, "EMA 20", 2);
  addLineSeries(payload.vwap, palette.orange, "VWAP", 2);

  payload.priceLines.forEach((line) => {
    candleSeries.createPriceLine({
      price: line.price,
      color: line.color,
      lineWidth: line.style === "solid" ? 2 : 1,
      lineStyle: line.style === "solid" ? LightweightCharts.LineStyle.Solid : LightweightCharts.LineStyle.Dashed,
      axisLabelVisible: true,
      title: line.title
    });
  });

  if (payload.markers.length && candleSeries.setMarkers) {
    candleSeries.setMarkers(payload.markers);
  }

  const resizeWickCanvas = () => {
    const rect = container.getBoundingClientRect();
    const ratio = window.devicePixelRatio || 1;
    const width = Math.max(Math.floor(rect.width), 320);
    const height = Math.max(Math.floor(rect.height), 360);
    wickCanvas.style.width = width + "px";
    wickCanvas.style.height = height + "px";
    if (wickCanvas.width !== Math.floor(width * ratio) || wickCanvas.height !== Math.floor(height * ratio)) {
      wickCanvas.width = Math.floor(width * ratio);
      wickCanvas.height = Math.floor(height * ratio);
    }
    wickContext.setTransform(ratio, 0, 0, ratio, 0, 0);
    return { width, height };
  };

  const visibleSpacing = (size) => {
    const range = chart.timeScale().getVisibleLogicalRange();
    const count = range ? Math.max(range.to - range.from, 1) : Math.max(payload.visibleCount || 90, 1);
    return Math.max(size.width / count, 2);
  };

  const drawSegment = (x, y1, y2, color, width) => {
    if (!Number.isFinite(x) || !Number.isFinite(y1) || !Number.isFinite(y2)) return;
    wickContext.strokeStyle = color;
    wickContext.lineWidth = width;
    wickContext.lineCap = "round";
    wickContext.beginPath();
    wickContext.moveTo(Math.round(x) + 0.5, y1);
    wickContext.lineTo(Math.round(x) + 0.5, y2);
    wickContext.stroke();
  };

  const drawSmallBody = (x, y, color, spacing) => {
    if (!Number.isFinite(x) || !Number.isFinite(y)) return;
    const half = Math.max(3, Math.min(10, spacing * 0.42));
    wickContext.strokeStyle = color;
    wickContext.lineWidth = Math.max(2.4, Math.min(4, spacing * 0.20));
    wickContext.lineCap = "round";
    wickContext.beginPath();
    wickContext.moveTo(x - half, y);
    wickContext.lineTo(x + half, y);
    wickContext.stroke();
  };

  const drawWicks = () => {
    if (!wickContext || !payload.candles.length) return;
    const size = resizeWickCanvas();
    wickContext.clearRect(0, 0, size.width, size.height);
    const spacing = visibleSpacing(size);
    const wickWidth = spacing >= 18 ? 2.8 : spacing >= 10 ? 2.2 : spacing >= 6 ? 1.65 : 1.25;
    wickContext.shadowColor = "rgba(0, 0, 0, 0.18)";
    wickContext.shadowBlur = 1.5;
    const range = chart.timeScale().getVisibleLogicalRange();
    const from = Math.max(0, Math.floor((range ? range.from : 0) - 8));
    const to = Math.min(payload.candles.length - 1, Math.ceil((range ? range.to : payload.candles.length - 1) + 8));
    for (let index = from; index <= to; index += 1) {
      const bar = payload.candles[index];
      if (!bar) continue;
      const x = chart.timeScale().timeToCoordinate(bar.time);
      const yHigh = candleSeries.priceToCoordinate(bar.high);
      const yLow = candleSeries.priceToCoordinate(bar.low);
      const yBodyTop = candleSeries.priceToCoordinate(Math.max(bar.open, bar.close));
      const yBodyBottom = candleSeries.priceToCoordinate(Math.min(bar.open, bar.close));
      const color = bar.close >= bar.open ? "#00C805" : "#FF375F";
      drawSegment(x, yHigh, yBodyTop, color, wickWidth);
      drawSegment(x, yBodyBottom, yLow, color, wickWidth);
      if (Number.isFinite(yBodyTop) && Number.isFinite(yBodyBottom) && Math.abs(yBodyTop - yBodyBottom) < 2.4) {
        drawSmallBody(x, yBodyTop, color, spacing);
      }
    }
    wickContext.shadowBlur = 0;
  };

  chart.timeScale().subscribeVisibleLogicalRangeChange(() => requestAnimationFrame(drawWicks));

  const lastBar = payload.candles[payload.candles.length - 1];
  const updateLegend = (bar, time) => {
    if (!bar) return;
    const volume = payload.volume.find((item) => item.time === time);
    const change = ((Number(bar.close) - Number(bar.open)) / Math.max(Number(bar.open), 0.01)) * 100;
    legend.innerHTML =
      "<span>" + fmtTime(time) + "</span>" +
      "<b>O</b> " + fmt(bar.open) +
      "<b>H</b> " + fmt(bar.high) +
      "<b>L</b> " + fmt(bar.low) +
      "<b>C</b> " + fmt(bar.close) +
      "<b>Vol</b> " + fmtVol(volume ? volume.value : 0) +
      "<b class='" + (change >= 0 ? "up" : "down") + "'>" + change.toFixed(2) + "%</b>";
  };
  updateLegend(lastBar, lastBar.time);

  chart.subscribeCrosshairMove((param) => {
    const bar = param && param.seriesData ? param.seriesData.get(candleSeries) : null;
    if (!param || !param.time || !bar) {
      updateLegend(lastBar, lastBar.time);
      return;
    }
    updateLegend(bar, param.time);
  });

  const setRange = (range) => {
    if (range === "all") {
      chart.timeScale().fitContent();
      chart.timeScale().applyOptions({ barSpacing: 8, minBarSpacing: 5 });
      markActive("all");
      requestAnimationFrame(drawWicks);
      return;
    }
    const count = Math.max(Number(range) || 90, 10);
    const spacing = count <= 30 ? 24 : count <= 45 ? 20 : count <= 90 ? 16 : count <= 180 ? 12 : 9;
    chart.timeScale().applyOptions({ barSpacing: spacing, minBarSpacing: 8 });
    const anchor = Math.min(Math.max(Number(payload.activeEndIndex ?? payload.candles.length - 1), 0), payload.candles.length - 1);
    const end = anchor + 8;
    const start = Math.max(anchor - count + 1, 0);
    chart.timeScale().setVisibleLogicalRange({ from: start, to: end });
    markActive(String(range));
    requestAnimationFrame(drawWicks);
  };

  const rangeButtons = Array.from(document.querySelectorAll(".tw-buttons button"));
  const markActive = (range) => {
    rangeButtons.forEach((button) => button.classList.toggle("active", button.dataset.range === String(range)));
  };
  rangeButtons.forEach((button) => {
    button.addEventListener("click", () => setRange(button.dataset.range));
  });
  container.addEventListener("dblclick", () => setRange(Math.min(payload.visibleCount || 90, payload.candles.length)));

  setRange(Math.min(payload.visibleCount || 90, payload.candles.length));
  requestAnimationFrame(() => {
    chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
    drawWicks();
  });
})();
</script>
<style>
  html, body {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    overflow: hidden;
    background: __PANEL__;
  }
  * {
    box-sizing: border-box;
  }
  .tw-shell {
    height: __CHART_HEIGHT__px;
    background: linear-gradient(180deg, __PANEL__ 0%, __PANEL_ALT__ 100%);
    border: 1px solid __BORDER__;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
    color: __TEXT__;
    font-family: Inter, Arial, sans-serif;
    box-shadow: 0 18px 44px rgba(0, 0, 0, 0.22);
  }
  .tw-toolbar {
    min-height: 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 12px;
    border-bottom: 1px solid __BORDER__;
    background: __PANEL_ALT__;
  }
  .tw-brand {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    color: __TEXT__;
  }
  .tw-brand strong {
    font-size: 14px;
    letter-spacing: 0;
  }
  .tw-brand span {
    color: __MUTED__;
    font-size: 12px;
  }
  .tw-credit {
    color: __MUTED__;
    font-size: 11px;
    text-decoration: none;
    border-left: 1px solid __BORDER__;
    padding-left: 8px;
  }
  .tw-credit:hover {
    color: __BLUE__;
  }
  .tw-buttons {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
  }
  .tw-buttons span {
    color: __MUTED__;
    font-size: 12px;
    margin-right: 2px;
  }
  .tw-buttons button {
    border: 1px solid __BORDER__;
    background: __PANEL__;
    color: __TEXT__;
    border-radius: 6px;
    padding: 6px 9px;
    cursor: pointer;
    font: inherit;
    font-size: 12px;
  }
  .tw-buttons button:hover {
    border-color: __BLUE__;
    color: __BLUE__;
  }
  .tw-buttons button.active {
    border-color: __UP__;
    background: rgba(0, 200, 5, 0.10);
    color: __UP__;
  }
  .tw-legend {
    min-height: 30px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
    padding: 6px 12px;
    background: transparent;
    color: __MUTED__;
    font-size: 12px;
  }
  .tw-legend b {
    color: __TEXT__;
    margin-left: 4px;
  }
  .tw-legend .up { color: __UP__; }
  .tw-legend .down { color: __DOWN__; }
  .tw-subbar {
    min-height: 34px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    border-bottom: 1px solid __BORDER__;
    background: __PANEL__;
  }
  .tw-hint {
    color: __MUTED__;
    font-size: 12px;
    white-space: nowrap;
    padding-right: 12px;
  }
  .tw-stage {
    position: relative;
    height: calc(100% - 82px);
    background: __PANEL__;
  }
  .tw-chart {
    height: 100%;
    background: __PANEL__;
    position: relative;
    z-index: 1;
  }
  .tw-wick-layer {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 2;
  }
  .tw-watermark {
    position: absolute;
    left: 22px;
    top: 18px;
    color: __MUTED__;
    opacity: 0.14;
    font-size: clamp(30px, 7vw, 88px);
    font-weight: 800;
    pointer-events: none;
    user-select: none;
    letter-spacing: 0;
    z-index: 0;
  }
  .tw-chart canvas {
    image-rendering: auto;
  }
  @media (max-width: 760px) {
    .tw-toolbar, .tw-subbar {
      align-items: flex-start;
      flex-direction: column;
    }
    .tw-hint {
      padding: 0 12px 8px;
    }
    .tw-stage {
      height: calc(100% - 130px);
    }
  }
  .tw-error {
    min-height: 320px;
    display: grid;
    place-items: center;
    color: __MUTED__;
    padding: 24px;
    text-align: center;
  }
</style>
"""
    replacements = {
        "__PAYLOAD__": json.dumps(payload),
        "__LIGHTWEIGHT_CHARTS_LOADER__": chart_loader,
        "__CHART_HEIGHT__": str(chart_height),
        "__TICKER__": html.escape(str(payload["ticker"])),
        "__PANEL__": payload["palette"]["panel"],
        "__PANEL_ALT__": payload["palette"]["panel_alt"],
        "__BORDER__": payload["palette"]["border"],
        "__TEXT__": payload["palette"]["text"],
        "__MUTED__": payload["palette"]["muted_soft"],
        "__BLUE__": payload["palette"]["blue"],
        "__UP__": payload["palette"]["up_bright"],
        "__DOWN__": payload["palette"]["down"],
    }
    for key, value in replacements.items():
        component_html = component_html.replace(key, str(value))

    components.html(component_html, height=chart_height + 6, width=1280, scrolling=False)
    return True


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
    show_ai_signals = bool(st.session_state.get("chart_layer_ai_signals", True))
    levels = chart_trade_levels(analysis)
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
    buy_low = levels["buy_low"]
    buy_high = levels["buy_high"]
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
        add_level("Buy low", levels["buy_low"], palette["cyan"])
        add_level("Buy high", levels["buy_high"], palette["cyan"])
        add_level("Stop", levels["stop"], down)
        add_level("Sell / trim", levels["target_1"], up)
        add_level("Runner target", levels["target_2"], palette["blue"])
        add_level("Previous close", analysis.get("Previous close"), muted)

    if show_ai_signals:
        signal_specs = [
            ("AI buy zone", levels["buy_mid"], palette["cyan"], "triangle-up", "Paper buy area"),
            ("Entry trigger", levels["entry"], up, "triangle-up", "Buy only after confirmation"),
            ("Stop / invalid", levels["stop"], down, "x", "Plan is wrong here"),
            ("Sell / trim T1", levels["target_1"], up, "triangle-down", "First sell/trim target"),
            ("Runner T2", levels["target_2"], palette["blue"], "triangle-down", "Second target"),
        ]
        signal_rows = [
            {"Label": label, "Price": price, "Color": color, "Symbol": symbol, "Note": note}
            for label, price, color, symbol, note in signal_specs
            if price is not None
        ]
        if signal_rows:
            fig.add_trace(
                go.Scatter(
                    x=[end_time for _ in signal_rows],
                    y=[row["Price"] for row in signal_rows],
                    mode="markers+text",
                    marker=dict(
                        color=[row["Color"] for row in signal_rows],
                        symbol=[row["Symbol"] for row in signal_rows],
                        size=15,
                        line=dict(width=1.8, color=panel_bg),
                    ),
                    text=[row["Label"] for row in signal_rows],
                    textposition="middle left",
                    textfont=dict(color=text, size=12),
                    customdata=[[row["Note"]] for row in signal_rows],
                    name="AI trade map",
                    hovertemplate="<b>%{text}</b><br>Price: $%{y:.2f}<br>%{customdata[0]}<extra></extra>",
                ),
                row=1,
                col=1,
            )

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
    overlay_values = []
    if show_plan_levels or show_ai_signals:
        overlay_values = [
            value
            for value in [
                levels["buy_low"],
                levels["buy_high"],
                levels["entry"],
                levels["stop"],
                levels["target_1"],
                levels["target_2"],
                safe_float(analysis.get("Previous close")),
            ]
            if value is not None and math.isfinite(float(value))
        ]
    if overlay_values:
        visible_high = max(visible_high, max(overlay_values))
        visible_low = min(visible_low, min(overlay_values))
    pad = max((visible_high - visible_low) * 0.10, max(current_price * 0.004, 0.03))
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
        st.info("No chart data available for this stock.")
        return

    chart_engine = st.session_state.get("chart_engine", "TradingView-style")
    if chart_engine == "TradingView-style":
        visible_count = max_candles or min(len(history), 390)
        load_limit = max(int(visible_count), 2600)
        chart_df = history.tail(load_limit).copy()
        flat_zero_volume = (
            (chart_df["Volume"].fillna(0).astype(float) <= 0)
            & ((chart_df["High"].astype(float) - chart_df["Low"].astype(float)).abs() <= 0.001)
            & ((chart_df["Open"].astype(float) - chart_df["Close"].astype(float)).abs() <= 0.001)
        )
        cleaned_chart_df = chart_df.loc[~flat_zero_volume].copy()
        if len(cleaned_chart_df) >= max(20, min(int(visible_count), 90)):
            chart_df = cleaned_chart_df
        active_volume_df = chart_df.loc[chart_df["Volume"].fillna(0).astype(float) > 0].copy()
        if len(active_volume_df) >= max(20, min(int(visible_count), 90)):
            chart_df = active_volume_df
    elif max_candles:
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

    def render_chart_stats() -> None:
        stats = [
            ("Last candle", money(current_price), pct(candle_delta), "up" if candle_delta >= 0 else "down"),
            ("Loaded high", money(range_high), f"{len(chart_df):,} candles", "neutral"),
            ("Loaded low", money(range_low), "drag left to review", "neutral"),
            ("VWAP", money(latest_vwap), "intraday control line", "neutral"),
        ]
        parts = ['<div class="msa-chart-stat-strip">']
        for label, value, detail, tone in stats:
            parts.append(
                '<div class="msa-chart-stat-card msa-chart-stat-{tone}">'
                '<div class="msa-chart-stat-label">{label}</div>'
                '<div class="msa-chart-stat-value">{value}</div>'
                '<div class="msa-chart-stat-detail">{detail}</div>'
                "</div>".format(
                    tone=html.escape(tone),
                    label=html.escape(label),
                    value=html.escape(value),
                    detail=html.escape(detail),
                )
            )
        parts.append("</div>")
        st.markdown("".join(parts), unsafe_allow_html=True)

    candle_size = 16 if len(chart_df) <= 90 else 12 if len(chart_df) <= 180 else 8 if len(chart_df) <= 390 else 4
    if chart_engine == "TradingView-style":
        rendered = render_lightweight_trading_chart(chart_df, analysis, current_price, height, max_candles)
        if rendered:
            render_chart_stats()
            return

    if go is not None and make_subplots is not None:
        render_plotly_trading_chart(chart_df, analysis, current_price, height)
        render_chart_stats()
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
    render_chart_stats()


def render_chart_panel(
    ticker: str,
    period: str,
    interval: str,
    prefer_live: bool,
    max_candles: int | None = 180,
) -> None:
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

    analysis = rebuild_analysis_from_history(ticker, history, source, prefer_live=prefer_live)

    chart_quality, chart_color = data_quality_badge(source)
    st.badge(f"Chart source: {chart_quality}", icon=":material/candlestick_chart:", color=chart_color)
    if prefer_live and source == "Learning data":
        st.warning(
            "The live chart feed did not return enough candles, so this view is showing learning fallback data.",
            icon=":material/wifi_off:",
        )

    render_candlestick_chart(history, analysis, max_candles=max_candles)
    st.caption(
        f"Chart source: {source}. Last screen refresh: {datetime.now().strftime('%I:%M:%S %p')}. "
        "Free market data can be real-time or delayed depending on source, exchange, and availability."
    )
    render_source_brief(analysis, source)
    render_price_audit_panel(ticker, history, analysis, source)
    render_beginner_stock_summary(analysis, source)
    render_trade_readiness_panel(analysis)
    render_premium_trade_ticket(analysis)
    render_ai_decision_panel(analysis, source)
    render_ai_chart_trade_map(analysis)
    render_plan_card(analysis)
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
        "Data confidence": analysis.get("Data confidence") or data_confidence_summary(analysis).get("label", "n/a"),
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
        clean_ticker = normalize_user_symbol(ticker)
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
        st.info("No live rows returned yet. Free data may be rate-limiting or the current filters may be too tight.")
        return

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Stock", pinned=True),
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
    render_action_queue(df, key="live_tracker_action_queue")
    render_data_health_summary(df)

    st.caption(
        f"Auto-refresh target: every {LIVE_REFRESH_SECONDS} seconds. "
        f"Last refresh: {datetime.now().strftime('%I:%M:%S %p')}. Free market data may be delayed or rate-limited."
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
        f"Free mode uses Alpaca IEX, Finnhub, and Yahoo-style fallbacks with a {LIVE_REFRESH_SECONDS}-second refresh target. "
        "It can be delayed or rate-limited, but it is enough for paper-trading practice."
    )
    render_data_stack_panel(compact=True)

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
        "Alpaca + Finnhub connected" if alpaca_enabled() and finnhub_enabled() else "Check data keys",
        icon=":material/key:",
        color="green" if alpaca_enabled() and finnhub_enabled() else "orange",
    )
    control_cols[2].caption("Home base: scanner candidates, AI plan, market clocks, and the latest news.")

    with st.skeleton(height=240):
        df = default_scan(prefer_live=prefer_live)
    best = df.iloc[0].to_dict()

    status_cards(
        [
            ("Candidates", str(len(df)), "calm"),
            ("Top stock", str(best["Ticker"]), "good"),
            ("Top score", f"{int(best['AI score'])}/100", "hot"),
            ("Top gain", pct(best["Daily gain %"]), "good"),
            ("Top RVOL", f"{best['RVOL']:.1f}x", "calm"),
        ]
    )
    render_action_queue(df, key="dashboard_action_queue")

    news_symbols = tuple(unique_symbols([str(item) for item in df["Ticker"].head(10).tolist()] + read_watchlist() + CORE_MARKET_TICKERS[:8]))
    news_col, main_col, right_col = st.columns([0.95, 1.35, 0.85], vertical_alignment="top")
    with news_col:
        render_big_news_rail(news_symbols)
    with main_col:
        st.subheader("Primary watch")
        render_ai_decision_panel(best)
        render_beginner_stock_summary(best, str(best.get("Data source", "n/a")))
        render_trade_readiness_panel(best)
        render_plan_card(best)
    with right_col:
        render_data_stack_panel(compact=True)
        render_data_health_summary(df)
        with st.container(border=True):
            st.markdown("**Market clocks**")
            st.dataframe(market_clock_frame(), width="stretch", hide_index=True)
        with st.container(border=True):
            st.markdown("**What to check next**")
            st.write("- Open Charts for 1-minute candles and AI buy/sell levels.")
            st.write("- Read the news before approving any paper plan.")
            st.write("- Use Journal even when the best decision is no trade.")
        with st.container(border=True):
            st.markdown("**New trader path**")
            st.write("1. Learn: read Start here and Glossary.")
            st.write("2. Dashboard: find the main watch.")
            st.write("3. Charts: check candles, entry, stop, profit.")
            st.write("4. Trade Desk: approve paper trades only.")
            st.write("5. Journal: save what happened.")
        render_training_progress_panel()

    st.subheader("Scanner candidates")
    show_scan_table(df, key="dashboard_scan_table")


def page_daily_gameplan() -> None:
    header("Daily Gameplan", "Your default scan: $2 to $20, gain over 10%, float under 10M, RVOL over 3x.")
    prefer_live = st.toggle("Use live data", value=True, key="gameplan_live")
    render_data_stack_panel(compact=True)
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
    render_action_queue(df, key="gameplan_action_queue")
    render_data_health_summary(df)

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
        prefer_live = options[0].toggle("Use live data", value=True)
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
                ("Best stock", str(top["Ticker"]), "good"),
                ("Best gain", pct(top["Daily gain %"]), "good"),
                ("Best score", f"{int(top['AI score'])}/100", "hot"),
            ]
        )
        render_action_queue(df, key="scanner_action_queue")
        render_data_health_summary(df)
    show_scan_table(df, key="scanner_results_table")


def page_market_scan() -> None:
    header("Market Scan", "Track core movers, S&P 500 names, global ETFs, crypto, and the full US stock universe in batches.")

    render_data_stack_panel(compact=True)

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
            "Add stocks",
            value="",
            height=80,
            placeholder="Example stocks: NVDA, SPY, TSM, BTC-USD",
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
    render_action_queue(df, key="market_scan_action_queue")
    render_data_health_summary(df)

    show_broad_market_table(df)

    if include_news:
        with st.expander(":material/newspaper: General market news", expanded=True):
            render_news_items(finnhub_market_news("general", limit=8), "No general market news returned yet.")


def page_charts() -> None:
    compact_header("Charts", "Chart the stock, trend, volume, and paper-trade levels.")
    selected_from_scan = normalize_user_symbol(st.session_state.get("selected_ticker", ""))
    tickers = [row["ticker"] for row in DEMO_PROFILES] + list(INDEX_PROFILES) + read_watchlist()
    if selected_from_scan:
        tickers.append(selected_from_scan)
    ticker_options = sorted(set(tickers))
    selected_index = ticker_options.index(selected_from_scan) if selected_from_scan in ticker_options else 0

    with st.container(border=True):
        control_top = st.columns([1.05, 1.05, 2.0, 0.75], vertical_alignment="bottom")
        selected_ticker = control_top[0].selectbox("Stock", ticker_options, index=selected_index)
        custom_ticker = normalize_user_symbol(control_top[1].text_input("Custom stock", value=""))
        interval = control_top[2].segmented_control(
            "Candle size",
            ["1m", "2m", "5m", "15m", "30m", "60m", "1d"],
            default="1m",
            key="chart_interval",
        )
        interval = str(interval or "1m")

        if interval == "1m":
            period_options = ["1d", "5d"]
        elif interval in {"2m", "5m", "15m", "30m", "60m"}:
            period_options = ["1d", "5d", "1mo", "3mo"]
        else:
            period_options = ["1mo", "3mo", "6mo", "1y", "2y"]

        period = control_top[3].segmented_control(
            "Chart range",
            period_options,
            default="5d" if interval == "1m" and "5d" in period_options else period_options[0],
            key=f"chart_period_{interval}",
        )
        period = str(period or period_options[0])

        candle_windows = {
            "45": 45,
            "90": 90,
            "180": 180,
            "390": 390,
            "All": None,
        }
        control_bottom = st.columns([1.75, 1.85, 0.62, 0.72, 0.62, 0.62, 0.68], vertical_alignment="bottom")
        default_window = "90" if interval == "1m" else "180"
        window_label = control_bottom[0].segmented_control(
            "Visible candles",
            list(candle_windows),
            default=default_window,
            key=f"chart_visible_candles_{interval}",
        )
        default_engine_label = "TradingView" if st.session_state.get("chart_engine", "TradingView-style") == "TradingView-style" else "Backup"
        engine_label = control_bottom[1].segmented_control(
            "Chart style",
            ["TradingView", "Backup"],
            default=default_engine_label,
            key="chart_engine_label",
        )
        chart_engine = "TradingView-style" if str(engine_label or "TradingView") == "TradingView" else "Backup Plotly"
        st.session_state.chart_engine = chart_engine
        live_toggle = control_bottom[2].toggle("Live", value=True, key="chart_live_enabled")
        auto_refresh = control_bottom[3].toggle("Refresh", value=True, key="chart_auto_refresh_enabled")
        control_bottom[4].toggle("EMAs", value=True, key="chart_layer_emas")
        control_bottom[5].toggle("VWAP", value=True, key="chart_layer_vwap")
        control_bottom[6].toggle("Levels", value=True, key="chart_layer_ai_signals")
        provisional_prefer_live = bool(live_toggle) or interval in {"1m", "2m", "5m", "15m", "30m", "60m"}
        st.caption(
            f"Wheel zoom, drag pan, double-click reset. Data mode: {'live intraday' if provisional_prefer_live else 'learning'}. "
            "1-minute charts load multiple days when available; use 45/90/180/390 for readable candle width, then drag left to review older candles."
        )
    render_data_stack_panel(compact=True)

    st.session_state.chart_layer_ema9 = bool(st.session_state.get("chart_layer_emas", True))
    st.session_state.chart_layer_ema20 = bool(st.session_state.get("chart_layer_emas", True))
    st.session_state.chart_layer_buy_zone = bool(st.session_state.get("chart_layer_ai_signals", True))
    st.session_state.chart_layer_plan_levels = bool(st.session_state.get("chart_layer_ai_signals", True))

    ticker = normalize_user_symbol(custom_ticker or selected_ticker)
    st.session_state.selected_ticker = ticker
    max_candles = candle_windows[window_label]
    prefer_live = bool(live_toggle) or interval in {"1m", "2m", "5m", "15m", "30m", "60m"}

    if prefer_live and auto_refresh:
        auto_refresh_chart_panel(ticker, period, interval, prefer_live, max_candles=max_candles)
    else:
        render_chart_panel(ticker, period, interval, prefer_live, max_candles=max_candles)


def page_ai_coach() -> None:
    header("AI Coach", "Turn a stock into a structured paper-trade plan.")
    cols = st.columns([1, 1, 2])
    ticker = normalize_user_symbol(cols[0].text_input("Stock", value=st.session_state.get("selected_ticker", "SOUN")))
    period = cols[1].selectbox("Lookback", ["1mo", "3mo", "6mo", "1y"], index=1)
    prefer_live = cols[2].toggle("Use live data", value=True, key="ai_live")

    history, source = load_history(ticker, period=period, interval="1d", prefer_live=prefer_live)
    analysis = rebuild_analysis_from_history(ticker, history, source, prefer_live=prefer_live)
    render_source_brief(analysis, source)
    render_price_audit_panel(ticker, history, analysis, source)
    render_beginner_stock_summary(analysis, source)
    render_ai_decision_panel(analysis, source)
    render_plan_card(analysis)
    with st.expander(f":material/article: News catalyst for {analysis.get('Ticker', ticker)}", expanded=True):
        render_news_items(finnhub_company_news(str(analysis.get("Ticker", ticker)), days=5, limit=5))

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
    prefer_live = st.toggle("Use live data", value=True, key="watchlist_live")

    with st.form("add_watchlist"):
        cols = st.columns([1, 3])
        new_ticker = normalize_user_symbol(cols[0].text_input("Stock"))
        add = cols[1].form_submit_button("Add stock", type="primary")
        if add and new_ticker:
            watchlist.append(new_ticker)
            write_watchlist(watchlist)
            st.rerun()

    analyses = [analyze_ticker(ticker, prefer_live=prefer_live) for ticker in watchlist]
    render_action_queue(pd.DataFrame(analyses), key="watchlist_action_queue")

    for analysis in analyses:
        ticker = str(analysis.get("Ticker", ""))
        data_quality, data_color = data_quality_badge(analysis.get("Data source"))
        with st.container(border=True):
            cols = st.columns([1, 1, 1, 1, 1])
            cols[0].metric(ticker, analysis["Setup"])
            cols[1].metric("Price", money(analysis["Price"]), pct(analysis["Daily gain %"]))
            cols[2].metric("RVOL", f"{analysis['RVOL']:.1f}x")
            cols[3].metric("AI score", f"{analysis['AI score']}/100")
            with st.container(horizontal=True):
                st.badge(data_quality, icon=":material/database:", color=data_color)
                st.badge(f"Quote {analysis.get('Quote time', 'n/a')}", icon=":material/schedule:", color="gray")
            st.caption(
                markdown_text(
                    f"Beginner read: {beginner_movement_text(analysis, asset_type_label(analysis))} "
                    f"{beginner_attention_text(analysis)}"
                )
            )
            if cols[4].button("Study", key=f"study_{ticker}"):
                st.session_state.selected_ticker = ticker
                st.session_state.watchlist_study_ticker = ticker
            if cols[4].button("Remove", key=f"remove_{ticker}"):
                write_watchlist([item for item in watchlist if item != ticker])
                st.rerun()

    study_ticker = st.session_state.get("watchlist_study_ticker")
    if study_ticker:
        st.subheader(f"{study_ticker} study plan")
        study_analysis = analyze_ticker(study_ticker, prefer_live=prefer_live)
        render_beginner_stock_summary(study_analysis, str(study_analysis.get("Data source", "n/a")))
        render_plan_card(study_analysis)
        render_news_items(finnhub_company_news(study_ticker, days=5, limit=5))


def page_trade_desk() -> None:
    header("Trade Desk", "Stage AI trade plans, approve them manually, and record paper orders.")
    render_data_stack_panel(compact=True)
    st.warning(
        "This page records approved paper orders only. Real broker execution needs a separate broker connection and another explicit approval step.",
        icon=":material/warning:",
    )

    cols = st.columns([1, 1, 1, 1])
    ticker = normalize_user_symbol(cols[0].text_input("Stock", value=st.session_state.get("selected_ticker", "NVDA")))
    risk_dollars = cols[1].number_input("Max paper risk $", min_value=1.0, max_value=10000.0, value=25.0, step=5.0)
    period = cols[2].selectbox("Lookback", ["1d", "5d", "1mo", "3mo"], index=1)
    interval = cols[3].selectbox("Candle", ["1m", "5m", "15m", "1d"], index=1)

    history, source = load_history(ticker, period=period, interval=interval, prefer_live=True)
    analysis = rebuild_analysis_from_history(ticker, history, source, prefer_live=True)
    render_source_brief(analysis, source)
    render_price_audit_panel(ticker, history, analysis, source)
    render_beginner_stock_summary(analysis, source)
    render_ai_decision_panel(analysis, source)

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
        ticker = normalize_user_symbol(top[1].text_input("Stock", value=st.session_state.get("selected_ticker", "SOUN")))
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
        ticker = normalize_user_symbol(cols[0].text_input("Stock", value="SOUN"))
        period = cols[1].selectbox("Period", ["3mo", "6mo", "1y", "2y"], index=1)
        min_gap = cols[2].number_input("Min gap %", 1.0, 50.0, 10.0, step=1.0)
        min_rvol = cols[3].number_input("Min RVOL", 0.5, 20.0, 3.0, step=0.5)
        hold_days = cols[4].number_input("Hold days", 1, 10, 3, step=1)
        prefer_live = st.toggle("Use live data", value=True, key="backtest_live")
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

    track_options = [
        "Start here",
        "Place a paper trade",
        "Order ticket",
        "Playbook",
        "Routine",
        "Chart reading",
        "Risk",
        "Data sources",
        "News",
        "Flashcards",
        "Quiz",
        "Practice",
        "Glossary",
        "iPad",
    ]
    requested_track = str(st.query_params.get("track", "") or "").replace("_", " ").strip()
    requested_match = next((option for option in track_options if option.lower() == requested_track.lower()), "Start here")
    track = st.selectbox(
        "Learning track",
        track_options,
        index=track_options.index(requested_match),
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
                st.write("- Pick one stock from Scanner or Market Scan.")
                st.write("- Open Charts and check trend, volume, news, and levels.")
                st.write("- Open Trade Desk and stage a paper order.")
                st.write("- Save the result in Journal after the trade is done.")

        with st.container(border=True):
            st.markdown("**The app workflow for a brand-new trader**")
            st.write("1. Go to Market Scan to see what the broad market and big names are doing.")
            st.write("2. Go to Scanner for small-cap momentum candidates that match the app rules.")
            st.write("3. Click a stock row, then open Charts to inspect the candle trend and plan levels.")
            st.write("4. Read the AI decision. If it says Study only or Watch only, do not force a trade.")
            st.write("5. Open Trade Desk, set your max paper risk, review the staged order, and only approve if every checklist item makes sense.")
            st.write("6. Open Journal and record what happened, even if you skipped the trade.")

        with st.container(border=True):
            st.markdown("**How to read any stock page**")
            reading_guide = pd.DataFrame(
                [
                    {"Field": "Price now", "What it means": "Where the stock is trading right now.", "Beginner move": "Compare it with entry, stop, and target before doing anything."},
                    {"Field": "Daily move", "What it means": "How far price moved from the previous close.", "Beginner move": "A big green number means attention, not an automatic buy."},
                    {"Field": "RVOL", "What it means": "Today's volume compared with normal volume.", "Beginner move": "The app wants high attention, usually 3x or more for this playbook."},
                    {"Field": "Float", "What it means": "Roughly how many shares can trade publicly.", "Beginner move": "Low float can move fast, but it can also reverse fast."},
                    {"Field": "Price audit", "What it means": "The app checks source, time, and whether price feeds disagree.", "Beginner move": "If it says mismatch or fallback, use the stock for study only."},
                    {"Field": "Data confidence", "What it means": "A quick trust label based on source, quote age, fallback data, and feed agreement.", "Beginner move": "High confidence is cleaner for paper practice. Verify first means slow down and check another source."},
                    {"Field": "AI score", "What it means": "A checklist score based on the app's rules.", "Beginner move": "Use it to focus your study, not as a profit promise."},
                    {"Field": "Entry trigger", "What it means": "The confirmation price.", "Beginner move": "Avoid guessing early. Wait for confirmation on the chart."},
                    {"Field": "Stop loss", "What it means": "Where the idea is wrong.", "Beginner move": "If this loss feels too big, reduce paper size or skip."},
                    {"Field": "Take profit", "What it means": "A planned exit where reward starts to pay for risk.", "Beginner move": "Know the reward before the entry."},
                ]
            )
            st.dataframe(reading_guide, width="stretch", hide_index=True)
            st.caption("Data confidence labels: High confidence is cleaner for paper practice, Usable for paper is acceptable for learning, Verify first means check another source, and Practice data means do not treat it as live.")

        with st.container(border=True):
            st.markdown("**What the app levels mean**")
            level_guide = pd.DataFrame(
                [
                    {"Level": "Current", "Plain English": "Where the stock is trading now.", "Beginner rule": "Do not buy just because this number is moving."},
                    {"Level": "Entry trigger", "Plain English": "The price that confirms buyers are showing strength.", "Beginner rule": "Paper buy only after confirmation, not before."},
                    {"Level": "Stop loss", "Plain English": "The price where the idea is wrong.", "Beginner rule": "If you cannot accept this planned loss, the trade is too big."},
                    {"Level": "Take profit 1", "Plain English": "The first planned sell/trim area.", "Beginner rule": "This is where reward starts paying for the risk."},
                    {"Level": "Runner target", "Plain English": "A second target if the move keeps working.", "Beginner rule": "Do not hold a runner without a written exit plan."},
                ]
            )
            st.dataframe(level_guide, width="stretch", hide_index=True)

        with st.container(border=True):
            st.markdown("**Beginner roadmap**")
            st.write("1. Learn the words: use Glossary until the order ticket terms make sense.")
            st.write("2. Learn the levels: current price, entry trigger, stop loss, take profit 1, runner target.")
            st.write("3. Learn the scanner: price, gap, float, RVOL, volume, catalyst.")
            st.write("4. Learn the chart: candles, VWAP, EMAs, support, resistance, breakout, pullback.")
            st.write("5. Paper trade only: approve practice orders and journal every result.")
            st.write("6. Review mistakes: missed entry, chase, bad stop, bad news read, oversized risk.")
            st.write("7. Repeat until you can explain every trade idea without guessing.")

        with st.container(border=True):
            st.markdown("**Study tools inside Learn**")
            tool_cols = st.columns(3)
            with tool_cols[0]:
                st.markdown("**Flashcards**")
                st.write("Practice the words until entry, stop loss, take profit, RVOL, VWAP, and spread feel natural.")
            with tool_cols[1]:
                st.markdown("**Quiz**")
                st.write("Grade yourself on the most common beginner mistakes before approving a paper trade.")
            with tool_cols[2]:
                st.markdown("**Practice drill**")
                st.write("Pick a real stock, read the AI plan, and complete the checklist without risking money.")

        render_training_progress_panel()

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
                st.write("1. Pick a stock from Scanner or Market Scan.")
                st.write("2. Open Charts and confirm the 1-minute or 5-minute candle trend.")
                st.write("3. Check that price is not far above the buy zone.")
                st.write("4. Check news, volume, RVOL, float, and spread risk.")
                st.write("5. Decide your max paper risk before thinking about shares.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**Inside Trade Desk**")
                st.write("1. Enter the stock symbol.")
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
                st.write("- Symbol: the stock symbol, like NVDA or SOUN.")
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
                    {"App field": "Stock", "Broker ticket field": "Symbol", "Beginner meaning": "The stock you are practicing."},
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
                st.write("- Check news, float, relative volume, and whether the stock is easy to borrow or has special risk.")
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

    elif track == "Data sources":
        render_data_stack_panel(compact=False)
        cols = st.columns(3)
        with cols[0]:
            with st.container(border=True, height="stretch"):
                st.markdown("**What live means**")
                st.write("- Live data can still be exchange-limited, delayed, or missing for some symbols.")
                st.write("- The app shows source and confidence so you know when to slow down.")
                st.write("- Free feeds are good for learning and paper-trading practice, not perfect execution truth.")
        with cols[1]:
            with st.container(border=True, height="stretch"):
                st.markdown("**How to read confidence**")
                st.write("- High confidence: source and time look cleaner.")
                st.write("- Usable for paper: acceptable for practice, still verify.")
                st.write("- Verify first: check another source before trusting the idea.")
                st.write("- Practice data: learning fallback, not live market data.")
        with cols[2]:
            with st.container(border=True, height="stretch"):
                st.markdown("**When to double-check**")
                st.write("- Price is moving very fast.")
                st.write("- The chart and quote differ.")
                st.write("- The spread is wide.")
                st.write("- News dropped in premarket or after-hours.")
                st.write("- You are about to approve a paper order.")

        with st.container(border=True):
            st.markdown("**Beginner rule**")
            st.write("If the app says verify first, treat the stock as a study idea until another quote source agrees with the chart and the news.")

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
            st.markdown("**How to use the Dashboard news rail**")
            st.write("- Biggest news dropped ranks headlines by freshness, catalyst words, risk words, and symbols the app is already scanning.")
            st.write("- Impact is not a buy signal. It means the headline deserves attention before you stage a paper trade.")
            st.write("- Risk headlines like offerings, halts, lawsuits, investigations, or delisting warnings should slow you down.")
            st.write("- Good news still needs chart confirmation: volume, VWAP/EMA hold, clean entry, written stop, and enough reward.")

        with st.container(border=True):
            st.markdown("**Live market news**")
            render_news_items(finnhub_market_news("general", limit=6), "Add your Finnhub key or try again later for live news.")

    elif track == "Flashcards":
        cards = [
            {"term": "Entry trigger", "category": "Risk", "answer": "The price that confirms buyers are stepping in. You wait for this instead of guessing early.", "example": "If the plan says entry above $5.12, a beginner waits for that confirmation."},
            {"term": "Stop loss", "category": "Risk", "answer": "The level where the setup is wrong. It defines the planned loss before entry.", "example": "If entry is $5.12 and stop is $4.92, the risk is $0.20 per share."},
            {"term": "Take profit 1", "category": "Risk", "answer": "The first planned area to sell or trim because reward is starting to pay for the risk.", "example": "A first target near 1.5R to 2R lets you measure reward before entering."},
            {"term": "Runner target", "category": "Risk", "answer": "A second target for any remaining shares if the move keeps working.", "example": "A runner still needs a written exit instead of hoping."},
            {"term": "R multiple", "category": "Risk", "answer": "Reward or loss measured against the planned risk.", "example": "If you risk $20 and make $40, that is +2R."},
            {"term": "RVOL", "category": "Scanner", "answer": "Relative volume. It compares today's volume with normal volume and shows whether attention is unusual.", "example": "A 5x RVOL stock is trading far more activity than normal."},
            {"term": "Float", "category": "Scanner", "answer": "Shares available for public trading. Lower float can move faster, but it can also be more dangerous.", "example": "A 7M float stock can move sharply when demand spikes."},
            {"term": "Gapper", "category": "Scanner", "answer": "A stock trading much higher than yesterday's close.", "example": "The app looks for at least a 10% daily move in the small-cap playbook."},
            {"term": "Liquidity", "category": "Scanner", "answer": "How easy it is to buy or sell without moving the price too much.", "example": "Thin liquidity can make exits ugly even if the chart looked good."},
            {"term": "VWAP", "category": "Charts", "answer": "Volume-weighted average price. Many intraday traders use it as a control line.", "example": "A stock holding above VWAP is often healthier than one fading below it."},
            {"term": "EMA 9", "category": "Charts", "answer": "A fast moving average that helps show short-term momentum.", "example": "Strong trends often ride the 9 EMA instead of breaking below it."},
            {"term": "Support", "category": "Charts", "answer": "A price area where buyers recently defended the stock.", "example": "A pullback holding support can be cleaner than buying straight up."},
            {"term": "Resistance", "category": "Charts", "answer": "A price area where sellers recently stopped the stock.", "example": "Breakouts need to clear resistance with volume."},
            {"term": "Spread", "category": "Orders", "answer": "The gap between bid and ask. Wide spreads make entries and exits harder.", "example": "A $5.00 bid and $5.18 ask is expensive for a beginner setup."},
            {"term": "Limit order", "category": "Orders", "answer": "An order that sets the worst price you are willing to accept. It may not fill.", "example": "A buy limit at $5.10 will not intentionally pay above $5.10."},
            {"term": "Market order", "category": "Orders", "answer": "An order that tries to fill immediately. It can slip badly in fast stocks.", "example": "A market order in a fast small cap may fill far away from the price you saw."},
            {"term": "Stop order", "category": "Orders", "answer": "An order that activates after a stop price is reached.", "example": "Some stop orders become market orders after triggering."},
            {"term": "Time in force", "category": "Orders", "answer": "How long an order stays active.", "example": "A day order expires after the session; a GTC order can stay open longer."},
            {"term": "Offering", "category": "News", "answer": "A company sells more shares. This can pressure price because supply increases.", "example": "An offering headline can quickly break a momentum move."},
            {"term": "Dilution", "category": "News", "answer": "Existing shares represent a smaller slice after new shares are issued.", "example": "Small caps can reverse fast when dilution risk appears."},
            {"term": "Halt", "category": "News", "answer": "A temporary pause in trading. A halted stock can reopen far above or below the last price.", "example": "New traders should be careful around halt risk."},
            {"term": "Catalyst", "category": "News", "answer": "The reason traders are paying attention today.", "example": "Earnings, FDA news, contracts, and upgrades can all be catalysts."},
        ]
        deck_options = ["All", "Orders", "Risk", "Charts", "Scanner", "News"]
        deck = st.segmented_control("Deck", deck_options, default="All", key="learn_flash_deck")
        deck = str(deck or "All")
        filtered_cards = [card for card in cards if deck == "All" or card["category"] == deck]
        st.session_state.learn_flash_index = int(st.session_state.get("learn_flash_index", 0)) % len(filtered_cards)
        index = st.session_state.learn_flash_index
        card = filtered_cards[index]
        term = str(card["term"])
        known_terms = set(st.session_state.get("learn_flash_known", []))
        review_terms = set(st.session_state.get("learn_flash_review", []))

        stat_cols = st.columns(4)
        stat_cols[0].metric("Deck", deck, border=True)
        stat_cols[1].metric("Cards", str(len(filtered_cards)), border=True)
        stat_cols[2].metric("Known", str(len(known_terms)), border=True)
        stat_cols[3].metric("Review", str(len(review_terms)), border=True)

        with st.container(border=True):
            st.markdown("**Flashcard deck**")
            st.progress((index + 1) / len(filtered_cards))
            st.caption(f"Card {index + 1} of {len(filtered_cards)} | {card['category']}")
            st.markdown(f"### {term}")
            safe_deck = deck.lower().replace(" ", "_")
            if st.toggle("Show answer", key=f"flash_show_{safe_deck}_{index}"):
                st.write(card["answer"])
                st.caption(f"Example: {card['example']}")
            cols = st.columns([1, 1, 1, 1, 1.2])
            if cols[0].button("Previous", icon=":material/chevron_left:"):
                st.session_state.learn_flash_index = (index - 1) % len(filtered_cards)
                st.rerun()
            if cols[1].button("Next", icon=":material/chevron_right:", type="primary"):
                st.session_state.learn_flash_index = (index + 1) % len(filtered_cards)
                st.rerun()
            if cols[2].button("I knew it", icon=":material/check_circle:"):
                known_terms.add(term)
                review_terms.discard(term)
                st.session_state.learn_flash_known = sorted(known_terms)
                st.session_state.learn_flash_review = sorted(review_terms)
                st.session_state.learn_flash_index = (index + 1) % len(filtered_cards)
                st.rerun()
            if cols[3].button("Review", icon=":material/replay:"):
                review_terms.add(term)
                known_terms.discard(term)
                st.session_state.learn_flash_known = sorted(known_terms)
                st.session_state.learn_flash_review = sorted(review_terms)
                st.session_state.learn_flash_index = (index + 1) % len(filtered_cards)
                st.rerun()
            if cols[4].button("Reset", icon=":material/restart_alt:"):
                st.session_state.learn_flash_index = 0
                st.session_state.learn_flash_known = []
                st.session_state.learn_flash_review = []
                st.rerun()

        with st.container(border=True):
            st.markdown("**How to study these**")
            st.write("- Say the answer out loud before revealing it.")
            st.write("- Use Charts after every few cards and point to the same concept on the live chart.")
            st.write("- Mark fuzzy words for Review, then come back after reading Glossary.")

    elif track == "Quiz":
        quiz_bank = {
            "Beginner basics": [
                {"question": "What should happen before a beginner paper-buys a momentum setup?", "options": ["Price confirms the entry trigger", "Price is moving fast", "Someone online likes it"], "answer": "Price confirms the entry trigger", "why": "The trigger is confirmation. Moving fast alone can lead to chasing."},
                {"question": "What does the stop loss define?", "options": ["Where the idea is wrong", "Where to add more shares", "Where news is best"], "answer": "Where the idea is wrong", "why": "The stop is the invalidation point and planned risk line."},
                {"question": "Why does RVOL matter?", "options": ["It shows unusual trading attention", "It guarantees profit", "It replaces the need for news"], "answer": "It shows unusual trading attention", "why": "High RVOL means today is more active than normal, but it never guarantees a win."},
                {"question": "What should you do if a stock is far above the planned entry?", "options": ["Avoid chasing and wait for a new setup", "Buy because it is strong", "Remove the stop loss"], "answer": "Avoid chasing and wait for a new setup", "why": "Chasing ruins risk/reward and makes the stop harder to respect."},
                {"question": "What belongs in a complete paper-trade plan?", "options": ["Entry, stop, target, size, and reason", "Only the stock symbol", "Only the biggest news headline"], "answer": "Entry, stop, target, size, and reason", "why": "A plan needs a reason and defined risk before the order is staged."},
            ],
            "Order ticket": [
                {"question": "Which order gives price control but may not fill?", "options": ["Limit order", "Market order", "Stop order"], "answer": "Limit order", "why": "A limit order controls worst acceptable price, but price may move away."},
                {"question": "What does quantity mean on a broker ticket?", "options": ["How many shares", "The stock's float", "The daily gain"], "answer": "How many shares", "why": "Quantity is share count. The app estimates paper shares from max risk and stop distance."},
                {"question": "Why can a market order be dangerous in a fast small-cap stock?", "options": ["It can fill at a worse price than expected", "It always waits for your exact price", "It removes all risk"], "answer": "It can fill at a worse price than expected", "why": "Fast candles and wide spreads can create slippage."},
                {"question": "What does time in force control?", "options": ["How long the order stays active", "The company's float", "The chart candle color"], "answer": "How long the order stays active", "why": "A forgotten open order can create surprises if you do not understand duration."},
                {"question": "What should happen before any real broker order is sent?", "options": ["Review the confirmation screen and broker rules", "Ignore the spread", "Skip the stop plan"], "answer": "Review the confirmation screen and broker rules", "why": "The app is a paper-trade planner. Real orders require careful broker review."},
            ],
            "Charts and risk": [
                {"question": "What does VWAP help you judge?", "options": ["Intraday control and price location", "The company's exact cash balance", "Whether profit is guaranteed"], "answer": "Intraday control and price location", "why": "VWAP is a useful intraday reference, but it is only one piece of context."},
                {"question": "What is usually healthier after a big push?", "options": ["A controlled pullback holding support", "A huge chase far above the trigger", "Removing the stop"], "answer": "A controlled pullback holding support", "why": "Better entries often come from controlled pullbacks or clean breakouts, not chasing."},
                {"question": "Why should target 1 be checked before entry?", "options": ["To confirm reward is worth the risk", "To avoid reading news", "To make the candle bigger"], "answer": "To confirm reward is worth the risk", "why": "If reward is too small compared with risk, the setup is not worth forcing."},
                {"question": "Why are offering and dilution headlines risky?", "options": ["They can add share supply and pressure price", "They always make stocks go up", "They remove all volatility"], "answer": "They can add share supply and pressure price", "why": "New share supply can hurt momentum, especially in small caps."},
                {"question": "What should you journal after a skipped setup?", "options": ["Why it was skipped and what happened next", "Nothing because no trade happened", "Only the highest price"], "answer": "Why it was skipped and what happened next", "why": "Skipped trades teach discipline and help you learn which filters worked."},
            ],
        }
        quiz_set = st.segmented_control("Quiz set", list(quiz_bank), default="Beginner basics", key="learn_quiz_set")
        quiz_set = str(quiz_set or "Beginner basics")
        questions = quiz_bank[quiz_set]
        quiz_slug = quiz_set.lower().replace(" ", "_").replace("/", "_")
        with st.container(border=True):
            st.markdown(f"**{quiz_set} quiz**")
            st.caption("Answer each question, then grade it. This is for learning, not certification.")
            answers: list[str] = []
            for index, question in enumerate(questions):
                choice = st.radio(
                    question["question"],
                    question["options"],
                    key=f"learn_quiz_{quiz_slug}_{index}",
                    horizontal=False,
                )
                answers.append(str(choice))
            if st.button("Grade quiz", type="primary", icon=":material/check_circle:"):
                score = sum(answer == question["answer"] for answer, question in zip(answers, questions))
                st.session_state.learn_quiz_score = score
                st.session_state.learn_quiz_graded = True
                st.session_state.learn_quiz_graded_set = quiz_set
            if st.button("Reset answers", icon=":material/restart_alt:"):
                st.session_state.learn_quiz_graded = False
                st.session_state.learn_quiz_score = 0
                st.rerun()

        if st.session_state.get("learn_quiz_graded") and st.session_state.get("learn_quiz_graded_set") == quiz_set:
            score = int(st.session_state.get("learn_quiz_score", 0))
            st.success(f"You scored {score}/{len(questions)}.")
            for index, question in enumerate(questions):
                selected = st.session_state.get(f"learn_quiz_{quiz_slug}_{index}")
                passed = selected == question["answer"]
                with st.container(border=True):
                    st.badge("Correct" if passed else "Review", color="green" if passed else "orange")
                    st.markdown(f"**{question['question']}**")
                    st.write(f"Your answer: {selected}")
                    st.write(f"Best answer: {question['answer']}")
                    st.caption(question["why"])

    elif track == "Practice":
        with st.container(border=True):
            st.markdown("**Paper-trade drill**")
            drill_ticker = normalize_user_symbol(st.text_input("Practice stock", value=st.session_state.get("selected_ticker", "NVDA")))
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
                {"Term": "IEX feed", "Meaning": "A market data feed from the Investors Exchange.", "Why it matters": "Alpaca's free stock candles can use IEX, which is useful but not the full consolidated market tape."},
                {"Term": "SIP feed", "Meaning": "A consolidated exchange data feed across major US markets.", "Why it matters": "It is closer to full professional real-time data, but it usually costs money because exchanges charge fees."},
                {"Term": "Delayed quote", "Meaning": "A price that may be behind the current market.", "Why it matters": "A delayed quote can make entries, stops, and targets look safer than they really are."},
                {"Term": "Data confidence", "Meaning": "The app's trust label based on source, quote age, fallback data, and price mismatch risk.", "Why it matters": "It tells beginners when to slow down and verify before using a setup."},
                {"Term": "Premarket", "Meaning": "Trading before the regular market open.", "Why it matters": "Moves can be fast, spreads can be wide, and volume can be thinner."},
                {"Term": "After-hours", "Meaning": "Trading after the regular market close.", "Why it matters": "News often drops after the bell, but fills can be less predictable."},
                {"Term": "Gapper", "Meaning": "A stock opening or trading far above the prior close.", "Why it matters": "It can reveal fresh demand, but late entries can fade fast."},
                {"Term": "Float", "Meaning": "Shares available for public trading.", "Why it matters": "Lower float can move faster because there is less supply."},
                {"Term": "RVOL", "Meaning": "Relative volume compared with normal trading volume.", "Why it matters": "High RVOL shows unusual attention today."},
                {"Term": "Liquidity", "Meaning": "How easy it is to buy or sell without moving price too much.", "Why it matters": "Low liquidity can make exits harder."},
                {"Term": "Slippage", "Meaning": "The difference between the price you expected and the price you actually get.", "Why it matters": "Fast stocks and market orders can slip badly."},
                {"Term": "VWAP", "Meaning": "Volume-weighted average price.", "Why it matters": "Many traders use it as an intraday control line."},
                {"Term": "Support", "Meaning": "A price area where buyers have recently defended the stock.", "Why it matters": "Pullbacks often need support to hold before a safe plan forms."},
                {"Term": "Resistance", "Meaning": "A price area where sellers have recently stopped the stock.", "Why it matters": "Breakouts usually need to clear resistance with volume."},
                {"Term": "Breakout", "Meaning": "Price pushes above a watched level with momentum.", "Why it matters": "The app's entry trigger is a breakout confirmation idea."},
                {"Term": "Pullback", "Meaning": "A controlled dip after a move up.", "Why it matters": "Better entries often come from controlled pullbacks, not chasing highs."},
                {"Term": "Consolidation", "Meaning": "Price pauses in a tighter range after moving.", "Why it matters": "A clean range can create a clearer trigger and stop."},
                {"Term": "Entry trigger", "Meaning": "The level that confirms buyers are stepping in.", "Why it matters": "It helps avoid buying only because price is moving."},
                {"Term": "Stop", "Meaning": "The level where the idea is invalid.", "Why it matters": "It defines risk before the trade."},
                {"Term": "Target", "Meaning": "A planned exit area for taking profit.", "Why it matters": "Targets make reward measurable before entry."},
                {"Term": "Trim", "Meaning": "Selling part of a position at a target while keeping some open.", "Why it matters": "It can lock in a partial result while still leaving room for a runner."},
                {"Term": "Runner", "Meaning": "The remaining shares kept after a partial exit.", "Why it matters": "A runner needs a written exit plan too."},
                {"Term": "R multiple", "Meaning": "Reward or loss measured against the planned risk.", "Why it matters": "It lets you compare trades fairly."},
                {"Term": "Halt", "Meaning": "A temporary pause in trading by an exchange.", "Why it matters": "Halts can reopen far above or below the last price."},
                {"Term": "Offering", "Meaning": "A company sells more shares to raise money.", "Why it matters": "Offerings can pressure price because supply increases."},
                {"Term": "Dilution", "Meaning": "Existing shares represent a smaller slice after new shares are issued.", "Why it matters": "Small-cap momentum can reverse quickly on dilution news."},
                {"Term": "Short interest", "Meaning": "Shares borrowed and sold by traders betting price will fall.", "Why it matters": "High short interest can add volatility, but it is not automatically bullish."},
                {"Term": "Easy to borrow", "Meaning": "A broker label showing shares may be available to short.", "Why it matters": "Borrow status can affect short-side trading and squeeze risk."},
                {"Term": "Margin account", "Meaning": "A brokerage account that can borrow from the broker under rules.", "Why it matters": "Margin can increase risk and trigger pattern day trader rules."},
                {"Term": "Cash account", "Meaning": "A brokerage account using settled cash instead of margin.", "Why it matters": "Cash accounts have settlement rules that can limit how often funds are reused."},
                {"Term": "Settlement", "Meaning": "The process where cash and shares officially exchange after a trade.", "Why it matters": "Using unsettled funds incorrectly can create broker restrictions."},
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
    st.set_page_config(page_title=APP_NAME, page_icon=":material/monitoring:", layout="wide")
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
