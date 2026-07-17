from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app  # noqa: E402


def main() -> None:
    scan = app.run_scan(2, 20, 10, 10, 3, prefer_live=False, include_learning=True)
    assert not scan.empty, "scanner should return learning candidates"
    assert {"Ticker", "AI score", "Buy zone", "Entry trigger", "Playbook fit", "Status"}.issubset(scan.columns)

    analysis = app.analyze_ticker("SOUN", prefer_live=False)
    assert analysis["AI score"] > 0
    assert analysis["Entry trigger"].startswith("Break over")
    assert app.setup_completion(analysis)[1] == 7
    assert app.clean_market_symbol("brk.b") == "BRK-B"
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
