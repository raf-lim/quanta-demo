from typing import Iterable
import pandas as pd
from api.http_get import JSON


def get_current_index_tickers(constituents: JSON) -> list[str]:
    """Extract current S&P 500 symbols."""
    return [obj.get("symbol") for obj in constituents]


def get_index_tickers_for_periods(
        current_tickers: Iterable[str],
        intervals: pd.IntervalIndex,
        sp500_historical: JSON,
        #sp500_symbol_change: JSON
    ) -> dict[str, list[str]]:
    """Get S&P500 symbols for each period based on
    historical symbol changes in the index. Processes symbols
    backwards ie. remove symbol if "newTicker" and add symbol
    if "removedTicker"."""
    tickers = set(current_tickers.copy())
    historical_sp500_tickers = {}

    to_add_in_prev_interval = set()
    to_remove_in_prev_interval = set()
    
    for interval in intervals:
        # shift removing tickers in preceiding month
        for symb in to_remove_in_prev_interval:
            tickers.discard(symb)
        to_remove_in_prev_interval.clear()

        # shift removing tickers in preceiding month
        for symb in to_add_in_prev_interval:
            #for obj in sp500_symbol_change:
                #if obj.get('oldSymbol') == symb:
                    #print(obj)
            tickers.add(symb)
        to_add_in_prev_interval.clear()
        
        for record in sp500_historical:
            if pd.Timestamp(record.get('date')) in interval:
                if record.get('addedSecurity') == '' and record.get('removedSecurity') != '':
                    to_add_in_prev_interval.add(record.get('removedTicker'))
                elif record.get('addedSecurity') != '' and record.get('removedSecurity') == '':
                    to_remove_in_prev_interval.add(record.get('symbol'))
                else:
                    to_add_in_prev_interval.add(record.get('removedTicker'))
                    to_remove_in_prev_interval.add(record.get('symbol'))
        historical_sp500_tickers[str(pd.Timestamp(interval.right).date())] = (
            sorted(tickers).copy()
        )

    return historical_sp500_tickers


def get_all_ptf_tickers(period_tickers: dict[str, Iterable[str]]) -> Iterable[str]:
    """Create list with all S&P500 tickers throughout the backtest period."""
    tickers = []
    for ticks in period_tickers.values(): 
        tickers.extend(ticks)
    tickers = filter(lambda x: x != '', tickers)
    
    return sorted(set(tickers))
