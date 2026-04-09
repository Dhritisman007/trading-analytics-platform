"""Number formatting utilities for clean API responses."""


def format_number(value, decimals: int = 2) -> float:
    """
    Round a number to the specified decimal places.
    Used to clean up indicator calculations before serializing to JSON.
    """
    if value is None or (isinstance(value, float) and (value != value or value == float('inf') or value == float('-inf'))):
        return None
    return round(float(value), decimals)
