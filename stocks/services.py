import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

INDIAN_STOCKS = [
    "TATASTEEL",
    "RELIANCE",
    "INFY",
    "HDFCBANK",
    "AIRTEL",
    "WIPRO",
    "TCS",
    "BAJFINANCE",
]


def _ticker_with_suffix(ticker, exchange="NSE"):
    if ticker.startswith("^"):
        return ticker
    if exchange.upper() == "NSE":
        return f"{ticker}.NS"
    if exchange.upper() == "BSE":
        return f"{ticker}.BO"
    return ticker


def format_indian_price(value):
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "₹0.00"

    sign = "-" if value < 0 else ""
    value = abs(value)
    integer_part = int(value)
    decimal_part = f"{value:.2f}".split(".")[1]

    int_str = str(integer_part)
    if len(int_str) <= 3:
        formatted = int_str
    else:
        last_three = int_str[-3:]
        remaining = int_str[:-3]
        chunks = []
        while len(remaining) > 2:
            chunks.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            chunks.insert(0, remaining)
        formatted = ",".join(chunks + [last_three])

    return f"{sign}₹{formatted}.{decimal_part}"


def _mock_price_history(period="3mo"):
    periods = {"1d": 24, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "3y": 1095}
    count = periods.get(period, 90)
    base = random.uniform(400, 3500)
    dates = [datetime.now() - timedelta(days=item) for item in range(count)][::-1]
    prices = [base]
    for _ in range(1, count):
        prices.append(max(10, prices[-1] * (1 + random.uniform(-0.02, 0.02))))

    df = pd.DataFrame(
        {
            "Date": dates,
            "Open": prices,
            "High": [price * random.uniform(1.0, 1.02) for price in prices],
            "Low": [price * random.uniform(0.98, 1.0) for price in prices],
            "Close": prices,
            "Volume": [random.randint(100000, 5000000) for _ in prices],
        }
    )
    df.set_index("Date", inplace=True)
    return df


def get_historical_data(ticker, period="3mo", exchange="NSE"):
    import yfinance as yf
    
    yf_ticker = _ticker_with_suffix(ticker, exchange)
    try:
        data = yf.Ticker(yf_ticker).history(period=period)
        if data.empty:
            return _mock_price_history(period)
        return data
    except Exception:
        return _mock_price_history(period)


def get_live_price(ticker, exchange="NSE"):
    try:
        data = get_historical_data(ticker, period="5d", exchange=exchange)
        close = data["Close"].dropna()
        if close.empty:
            raise ValueError("No close data")
        current = float(close.iloc[-1])
        previous = float(close.iloc[-2]) if len(close) > 1 else current
        change = current - previous
        change_pct = (change / previous) * 100 if previous else 0
        return {
            "ticker": ticker,
            "exchange": exchange,
            "price": round(current, 2),
            "price_display": format_indian_price(current),
            "change": round(change, 2),
            "change_display": format_indian_price(change),
            "change_percent": round(change_pct, 2),
            "is_up": change >= 0,
            "series": [round(float(item), 2) for item in close.tail(30).tolist()],
        }
    except Exception:
        fallback = random.uniform(100, 3000)
        move = random.uniform(-50, 50)
        return {
            "ticker": ticker,
            "exchange": exchange,
            "price": round(fallback, 2),
            "price_display": format_indian_price(fallback),
            "change": round(move, 2),
            "change_display": format_indian_price(move),
            "change_percent": round((move / fallback) * 100, 2) if fallback else 0,
            "is_up": move >= 0,
            "series": [round(float(item), 2) for item in np.linspace(fallback - 20, fallback + 20, 30)],
        }


def get_market_indices():
    indices = [
        ("NIFTY 50", "^NSEI"),
        ("SENSEX", "^BSESN"),
        ("BANKNIFTY", "^NSEBANK"),
    ]
    output = []
    for name, ticker in indices:
        try:
            df = yf.Ticker(ticker).history(period="5d")
            if df.empty:
                raise ValueError("empty")
            close = df["Close"].dropna()
            current = float(close.iloc[-1])
            previous = float(close.iloc[-2]) if len(close) > 1 else current
            change = current - previous
            change_pct = (change / previous) * 100 if previous else 0
            output.append(
                {
                    "name": name,
                    "value": current,
                    "value_display": format_indian_price(current),
                    "change": round(change, 2),
                    "change_percent": round(change_pct, 2),
                    "is_up": change >= 0,
                }
            )
        except Exception:
            current = random.uniform(10000, 55000)
            change = random.uniform(-200, 200)
            output.append(
                {
                    "name": name,
                    "value": current,
                    "value_display": format_indian_price(current),
                    "change": round(change, 2),
                    "change_percent": round((change / current) * 100, 2),
                    "is_up": change >= 0,
                }
            )
    return output


def _rank_stocks(reverse=True):
    scored = []
    for ticker in INDIAN_STOCKS:
        data = get_live_price(ticker, "NSE")
        scored.append(data)
    return sorted(scored, key=lambda item: item["change_percent"], reverse=reverse)


def get_top_gainers():
    return _rank_stocks(reverse=True)[:5]


def get_top_losers():
    return _rank_stocks(reverse=False)[:5]


def get_market_sentiment(ticker):
    random.seed(ticker)
    return round(random.uniform(0.35, 0.89), 2)
