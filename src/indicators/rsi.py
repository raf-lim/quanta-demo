from math import inf
import pandas as pd


def compute_rsi_series(prices: pd.Series, period: int) -> pd.Series:
    """Compute relative strength index of prices"""
    delta = prices.diff()
    gain = delta.where(delta > 0, other=0)
    loss = delta.where(delta < 0, other=0)
    rs = gain.rolling(period).mean() / loss.rolling(period).mean()
    rsi = 100 - (100 / (1 - rs))
    
    return rsi


def compute_rsi(prices: pd.Series, period: int) -> float:
    """Compute relative strength index of prices"""
    period_prices = prices.iloc[-period:]
    delta = period_prices.diff()
    gain = delta.where(delta > 0, other=0)
    loss = delta.where(delta < 0, other=0)
    rs = gain.mean() / loss.mean()
    rsi = 100 - (100 / (1 - rs))
    
    return rsi