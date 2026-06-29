import yfinance as yf
import requests
import json
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

TICKERS = {
    "KOSPI":   "^KS11",
    "KOSDAQ":  "^KQ11",
    "S&P500":  "^GSPC",
    "Nasdaq":  "^IXIC",
    "USD/KRW": "KRW=X",
}


def fetch_yf(symbol):
    tk = yf.Ticker(symbol)
    hist = tk.history(period="1y", interval="1d", auto_adjust=True)
    if hist.empty:
        return None
    hist = hist.dropna(subset=["Close"])
    prices = hist["Close"].tolist()
    dates  = [d.strftime("%m/%d") for d in hist.index]
    if len(prices) < 2:
        return None
    prev  = prices[-2]
    cur   = prices[-1]
    chg_abs = cur - prev
    chg_pct = chg_abs / prev * 100
    history = list(zip(dates, [round(p, 4) for p in prices]))
    return {
        "price":      round(cur, 4),
        "change_abs": round(chg_abs, 4),
        "change_pct": round(chg_pct, 4),
        "history":    history,
    }


def fetch_bitcoin():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": "365", "interval": "daily"}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()["prices"]  # [[timestamp_ms, price], ...]
        if len(data) < 2:
            return None
        history = [
            (datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%m/%d"), round(p, 2))
            for ts, p in data
        ]
        prev = history[-2][1]
        cur  = history[-1][1]
        chg_abs = cur - prev
        chg_pct = chg_abs / prev * 100
        return {
            "price":      round(cur, 2),
            "change_abs": round(chg_abs, 2),
            "change_pct": round(chg_pct, 4),
            "history":    history,
        }
    except Exception as e:
        print(f"[Bitcoin] CoinGecko error: {e}")
        return None


def main():
    markets = {}

    for name, symbol in TICKERS.items():
        print(f"Fetching {name} ({symbol})...")
        result = fetch_yf(symbol)
        if result:
            markets[name] = result
            print(f"  {name}: {result['price']} ({result['change_pct']:+.2f}%)")
        else:
            print(f"  {name}: FAILED")

    print("Fetching Bitcoin...")
    btc = fetch_bitcoin()
    if btc:
        markets["Bitcoin"] = btc
        print(f"  Bitcoin: {btc['price']} ({btc['change_pct']:+.2f}%)")
    else:
        print("  Bitcoin: FAILED")

    output = {
        "updated_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
        "markets": markets,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\ndata.json saved — {len(markets)} markets")


if __name__ == "__main__":
    main()
