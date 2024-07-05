from dataclasses import dataclass
from typing import Literal

import pandas as pd
import numpy as np
from scipy import stats


def compute_quarterly_yoy_growth(
        readings: pd.Series,
        number_of_last_quarters: int
    ) -> pd.Series:
    try:
        growth_rate = readings.diff(periods=4) / abs(readings.shift(periods=4))
        return growth_rate.iloc[-number_of_last_quarters:]
    except (ZeroDivisionError, Exception):
        return float(np.nan)


def compute_quarterly_qtq_growth(
        readings: pd.Series, number_of_last_quarters: int
    ) -> pd.Series:
    try:
        growth_rate = readings.diff() / abs(readings.shift())
        return growth_rate.iloc[-number_of_last_quarters:]
    except (ZeroDivisionError, Exception):
        return float(np.nan)


def compute_quarterly_yoy_difference(
        readings: pd.Series, number_of_last_quarters: int
    ) -> pd.Series:
    try:
        difference = readings.diff(periods=4)
        return difference.iloc[-number_of_last_quarters:]
    except (ZeroDivisionError, Exception):
        return float(np.nan)


def compute_quarterly_qtq_difference(
        readings: pd.Series, number_of_last_quarters: int
    ) -> pd.Series:
    try:
        difference = readings.diff()
        return difference.iloc[-number_of_last_quarters:]
    except (ZeroDivisionError, Exception):
        return float(np.nan)


def compute_eps_growth(eps: pd.Series) -> float:
    try:
        return (
            (sum(eps[-4:]) - sum(eps[-8:-4])) / abs(sum(eps[-8:-4]))
        )
    except (ZeroDivisionError, Exception):
        return float(np.nan)
    

def compute_mean_sales_growth(sales_growth: pd.Series) -> float:
    try:
        return sales_growth.mean()
    except (ValueError, Exception):
        return float(np.nan)
    

@dataclass
class GrowthAcceleration:
    """Computing linear regression metrics"""
    growth_readings: pd.Series

    def compute_slope(self) -> float:
        """Compute slope of regression line of EPS growth rates 
        representing compound EPS growth rate (or growth accelaration).

        :param Iterable[int] x: x-axis index
        :param Iterable[float] y: EPS growth rate Y/Y (last 4 quarters)
        :return float: slope
        """
        try:
            return stats.linregress(
                self.growth_readings.index,
                self.growth_readings.values,
            ).slope
        except (ValueError, Exception):
            return float(np.nan)
    
    def compute_standard_deviation(self) -> float:
        try:
            return self.growth_readings.std()
        except (ValueError, Exception):
            return float(np.nan)


def compute_period_price_performance(
        prices: dict[str, float],
        rs_dates: pd.IntervalIndex,
        frequency: str,
        period: Literal[0, 1, 2, 3]) -> float:
    """Computing price performance for the quarter."""
    start = rs_dates[period + 1].right.date()
    end = rs_dates[period].right.date()
    dates = pd.date_range(start, end, freq=frequency)
    trading_dates = sorted(
        set(prices.keys()).intersection(
            set(str(date.date()) for date in dates)
            )
        )
    try:
        start_price = prices.get(trading_dates[0])['Close']
        end_price = prices.get(trading_dates[-1])['Close']
        return end_price / start_price - 1
    except (IndexError, TypeError, ZeroDivisionError):
        return float(np.nan)
