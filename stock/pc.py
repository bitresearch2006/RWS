import yfinance as yf

def pc(symbol: str):
    """Return the previous day's closing price for a given stock symbol."""
    try:
        stock = yf.Ticker(symbol)
        close_price = stock.history(period="2d")["Close"].iloc[-2]  # Previous day's close
        return {"symbol": symbol, "previous_close": close_price}
    except Exception as e:
        return {"error": f"Failed to fetch previous close price: {e}"}
