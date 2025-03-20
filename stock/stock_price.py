import random

def sp(symbol: str):
    """Return a dummy stock price for testing."""
    dummy_price = round(random.uniform(100, 500), 2)  # Generate a random price
    return {"symbol": symbol, "price": dummy_price}
