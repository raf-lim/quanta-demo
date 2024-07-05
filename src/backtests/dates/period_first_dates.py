import datetime
import pandas as pd


def get_first_trading_dates_of_month(
        ranked_data: dict,
        backtest_dates: list[str]
    ) -> list[str]:
    """Extract first trading days of month"""
    int_dates = tuple(ranked_data.keys())

    dates_intervals = pd.interval_range(
        start=pd.to_datetime(int_dates[0]),
        end=pd.to_datetime(int_dates[-1]) + datetime.timedelta(weeks=4),
        freq='MS',
        closed='neither'
    )

    first_trading_days = []
    for interval in dates_intervals:
        dates = pd.date_range(start=interval.left, end=interval.right)
        dates = [str(date.date()) for date in dates]
        trading_dates = sorted(set(dates[:-1]).intersection(set(backtest_dates)))
        if trading_dates:
            first_trading_days.append(trading_dates[0])

    return first_trading_days


def get_first_trading_dates_of_year(
        ranked_data: dict,
        backtest_dates: list[str]
    ) -> list[str]:
    """Extract first trading days of year"""
    int_dates = tuple(ranked_data.keys())

    dates_intervals = pd.interval_range(
        start=pd.to_datetime(int_dates[0]),
        end=pd.to_datetime(int_dates[-1]) + datetime.timedelta(weeks=52),
        freq='YS',
        closed='neither'
    )

    first_trading_days = []
    for interval in dates_intervals:
        dates = pd.date_range(start=interval.left, end=interval.right)
        dates = [str(date.date()) for date in dates]
        trading_dates = sorted(set(dates[:-1]).intersection(set(backtest_dates)))
        first_trading_days.append(trading_dates[0])

    return first_trading_days