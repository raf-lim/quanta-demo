from typing import Iterable
import datetime
import pandas as pd


def get_backtest_dates(
        stocks_dates_in_ptf: dict[str, Iterable[str]]
    ) -> Iterable[str]:
    """Get all dates of portfolio existence."""
    ptf_dates = []
    for dates in stocks_dates_in_ptf.values():
        ptf_dates.extend(dates)
    
    return sorted(set(ptf_dates))
