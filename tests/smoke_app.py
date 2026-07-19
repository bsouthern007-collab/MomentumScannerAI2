from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app  # noqa: E402


def main() -> None:
    scan = app.run_scan(2, 20, 10, 10, 3, prefer_live=False, include_learning=True)
    assert not scan.empty, "scanner should return learning candidates"
    assert {"Ticker", "AI score", "Buy zone", "Entry trigger", "Playbook fit", "Status"}.issubset(scan.columns)
    health = app.data_health_frame(scan)
    assert int(health["Rows"].sum()) == len(scan)
    assert health["Rows"].max() > 0
    assert app.data_source_mix(scan) != "No source rows yet"

    analysis = app.analyze_ticker("SOUN", prefer_live=False)
    assert analysis["AI score"] > 0
    assert analysis["Entry trigger"].startswith("Break over")
    assert app.ai_signal_light(analysis)["color"] in {"red", "green", "blue"}
    green_case = dict(analysis)
    green_case["Data source"] = "Finnhub quote"
    green_case["Market state"] = "OPEN"
    green_case["Quote time"] = app.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    green_case["Price"] = float(green_case["Entry trigger price"]) * 1.001
    assert app.ai_signal_light(green_case)["color"] == "green"
    assert app.ai_now_steps(green_case, "Trigger active", "Breakout trigger")[0].startswith("Green light")
    assert "green means" in app.beginner_trade_translation(green_case, "Trigger active").lower()
    blue_case = dict(green_case)
    blue_case["Price"] = float(blue_case["Target 1 price"]) * 1.001
    assert app.ai_signal_light(blue_case)["color"] == "blue"
    assert app.ai_now_steps(blue_case, "Trigger active", "Breakout trigger")[0].startswith("Blue light")
    assert "blue means" in app.beginner_trade_translation(blue_case, "Trigger active").lower()
    red_steps = app.ai_now_steps(analysis, "Watch only", "Watching")
    assert red_steps[0].startswith("Red light")
    assert app.setup_completion(analysis)[1] == 7
    levels = app.chart_trade_levels(analysis)
    assert levels["entry"] and levels["stop"] and levels["target_1"]
    history, _ = app.load_history("SOUN", period="5d", interval="1m", prefer_live=False)
    chart_df = history.tail(45).copy()
    chart_df["EMA 9"] = chart_df["Close"].ewm(span=9, adjust=False).mean()
    chart_df["EMA 20"] = chart_df["Close"].ewm(span=20, adjust=False).mean()
    typical_price = (chart_df["High"] + chart_df["Low"] + chart_df["Close"]) / 3
    chart_df["VWAP"] = (typical_price * chart_df["Volume"]).cumsum() / chart_df["Volume"].replace(0, 1).cumsum()
    chart_df["Time"] = chart_df.index
    chart_payload = app.lightweight_chart_payload(chart_df, analysis, float(chart_df["Close"].iloc[-1]), 45)
    assert chart_payload["candles"]
    assert chart_payload["priceLines"]
    assert chart_payload["markers"]
    json.dumps(chart_payload)
    assert app.clean_market_symbol("brk.b") == "BRK-B"
    assert app.normalize_user_symbol("S&P 500") == "^GSPC"
    assert app.normalize_user_symbol("SP500") == "^GSPC"
    assert app.normalize_user_symbol("SPX") == "^GSPC"
    index_analysis = app.analyze_ticker("S&P 500", prefer_live=False)
    assert index_analysis["Ticker"] == "^GSPC"
    assert index_analysis["Price"] > 0
    assert app.tradeable_security_name("Community Bancorp Common Stock", include_etfs=True)
    assert not app.tradeable_security_name("Example Acquisition Units", include_etfs=True)
    assert app.ticker_batch(["A", "B", "C", "D"], 1, 2) == ["B", "C"]
    assert app.next_batch_start(2, 2, 4) == 0

    result = app.backtest_strategy("SOUN", "6mo", False, 10, 3, 3)
    assert "summary" in result
    assert "trades" in result

    print("smoke tests passed")


if __name__ == "__main__":
    main()
