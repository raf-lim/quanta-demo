import pandas as pd


def compute_sma(prices: pd.Series, period: int) -> pd.Series:
    """Compute simple moving average."""
    
    return prices.rolling(period).mean()
    