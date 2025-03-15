def divide(a: float, b: float):
    """Return the division of two numbers (avoid divide by zero)."""
    if b == 0:
        return {"error": "Division by zero is not allowed"}
    return {"result": a / b}
