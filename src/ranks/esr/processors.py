from typing import Callable, Iterable, Literal
from math import inf
from statistics import mean
import pandas as pd
import numpy as np
from . import scorings


def merge_financial_data(
        income_statements_data: dict[str, list[dict[str, str]]],
        balance_sheets_data: dict[str, list[dict[str, str]]],
        #earning_calendar_data: dict[str, list[dict[str, str]]]
    ) ->  dict[str, list[dict[str, str]]]:
    """Merge income statements, balance sheets"""
    symbols_data = income_statements_data.copy()
    for symbol, data_sets in balance_sheets_data.items():
        for data in data_sets:
            for is_data in symbols_data[symbol]:
                if is_data['date'] == data['date']:
                    is_data.update(data)
    
    return symbols_data


def merge_earning_calendars(
        financial_statements_data: dict[str, list[dict[str, str]]],
        earning_calendars_data: dict[str, list[dict[str, str]]]
    ) -> dict[str, list[dict[str, str]]]:
    """Merge income statements, balance sheets and earning calendars"""
    symbols_data = financial_statements_data.copy()
    for symbol, data_sets in earning_calendars_data.items():
        for data in data_sets:
            if symbols_data.get(symbol):
                for is_data in symbols_data[symbol]:
                    if is_data['end'] == data['end']:
                        is_data.update(data)

    return symbols_data
    

def create_starting_positions(
        tickers: list[str],
        financial_data: dict[str, list[dict[str, str]]],
        rank_dates: Iterable[str],
        interval_freq: Literal['ME', 'W-FRI']
    ) -> dict[str, str | float]:
    """
    Dictionary with starting position of report
    in the list for interval for the ticker.
    """
    ticker_interval_report_position = {}
    for ticker in tickers:
        position_for_interval = {}
        position_in_report_list = 0
        if ticker in financial_data.keys():
            for rank_date in rank_dates:
                rank_month = pd.interval_range(
                    end=pd.Timestamp(rank_date), periods=1, freq=interval_freq
                )
                # finding which income statement falls into the interval,
                # every quarter -> every third monthly interval
                report_falling_into_interval = tuple(
                    filter(
                        lambda x: pd.Timestamp(x['date']) in rank_month[0],
                        financial_data[ticker]
                    )
                )
                if not report_falling_into_interval:
                    # starting position (index) to count reports back
                    # for given month interval
                    position_for_interval[rank_date] = position_in_report_list
                else:
                    # starting position (index) to count reports back
                    # for given month interval
                    position_for_interval[rank_date] = position_in_report_list
                    position_in_report_list += 1

        ticker_interval_report_position[ticker] = position_for_interval

    return ticker_interval_report_position


def process_data_for_ranking(
        period_symbols: dict[str, list[str]],
        interval_freq: Literal['ME', 'W-FRI'],
        stocks_prices: dict[str, dict[str, float | None]],
        stocks_financial_data: dict[str, list[dict[str | float]]],
        stock_interval_report_position: dict[str, str | float],
        tickers_sma_periods: int,
        rsi_fn: Callable[[pd.Series, int], float],
        with_tech_indicators: bool = False,
    ) -> dict[str, dict[str, dict[str, float]]]:
    
    intervals_data: dict[str, dict[str, dict[str, float]]] = {}

    for rank_date, tickers in period_symbols.items():

        rs_dates = pd.interval_range(
            end=pd.Timestamp(rank_date), periods=13, freq='ME'
        )[::-3]

        current_interval_dates = pd.interval_range(
            end=pd.Timestamp(rank_date),
            periods=1, freq=interval_freq)[::-1]
        
        next_interval_dates = pd.interval_range(
            start=pd.Timestamp(rank_date),
            periods=1, freq=interval_freq)[::-1]

        stocks_data: dict[str, dict[str, float | None]] = {}

        for ticker in tickers:
            ticker_prices = stocks_prices.get(ticker)
            if ticker_prices and stock_interval_report_position.get(ticker):
                starting_point = (
                    stock_interval_report_position[ticker][rank_date]
                )
                symbol_data = (
                    stocks_financial_data[ticker][
                        starting_point : starting_point + 16
                    ]
                )
                
                # EPS
                eps = pd.Series(
                    tuple(map(
                        lambda x: x.get('eps') if x.get('eps') else x.get('eps_dill'),
                        symbol_data
                    ))[::-1]
                )
                
                # EPS Growth Rate
                eps_growth = scorings.compute_eps_growth(eps)

                # EPS Growth Acceleration
                eps_yoy_growth = scorings.compute_quarterly_yoy_growth(
                    eps, number_of_last_quarters=2
                )
                eps_growth_acceleration = scorings.GrowthAcceleration(
                    eps_yoy_growth
                ).compute_slope()
                
                # SALES
                sales: pd.Series = pd.Series(
                    [i.get('revenue') for i in symbol_data][::-1],
                )
                sales_growth = scorings.compute_quarterly_yoy_growth(
                    sales, number_of_last_quarters=2
                )
                # Sales Growth Rate
                mean_sales_growth = scorings.compute_mean_sales_growth(
                        sales_growth
                    )
                # Sales Growth Acceleration
                sales_growth_acceleration = scorings.GrowthAcceleration(
                    sales_growth
                ).compute_slope()

                # PRICE ACTION
                lq_0_perf = scorings.compute_period_price_performance(
                    ticker_prices, rs_dates, frequency='D', period=0)
                lq_1_perf = scorings.compute_period_price_performance(
                    ticker_prices, rs_dates, frequency='D', period=1)

                stocks_data[ticker] = {
                    'eps_growth': eps_growth,
                    'eps_growth_acceleration': eps_growth_acceleration,
                    'mean_sales_growth': mean_sales_growth,
                    'sales_growth_acceleration': sales_growth_acceleration,
                    'lq_0_perf': lq_0_perf,
                    'lq_1_perf': lq_1_perf,
                }

                if with_tech_indicators:

                    # COMPUTING SINGLE STOCK RETURNS FOR EACH PERIOD
                    price_set_current_period = sorted(
                        set(ticker_prices.keys()).intersection(
                            set(str(i.date()) for i in pd.date_range(
                                start=current_interval_dates[0].left.date(),
                                end=current_interval_dates[0].right.date(),
                                freq='D'))))

                    price_set_next_period = sorted(
                        set(ticker_prices.keys()).intersection(
                            set(str(i.date()) for i in pd.date_range(
                                start=next_interval_dates[0].left.date(),
                                end=next_interval_dates[0].right.date(),
                                freq='D'))))
                    
                    try:
                        start_date = price_set_current_period[-1]
                        end_date = price_set_next_period[-1]
                        interval_returns = (
                            (ticker_prices[end_date]['Close'] 
                                - ticker_prices[start_date]['Close'])
                                / ticker_prices[start_date]['Close']
                                )
                    except IndexError:
                        interval_returns = float(np.nan)
                    
                    stocks_data[ticker].update({'interval_returns': interval_returns})

                    # COMPUTING TECHNICAL INDICATORS FOR THE STOCK

                    try:
                        last_trading_date = price_set_current_period[-1]

                        ticker_prices_to_date = pd.Series(
                            {date: price['Close'] for date, price in stocks_prices[ticker].items()}
                            ).loc[:last_trading_date]

                        ticker_weekly_prices_to_date = ticker_prices_to_date.iloc[::-5][::-1]

                        # SMA
                        sma = ticker_weekly_prices_to_date.iloc[-9:].mean()
                        stocks_data[ticker].update({'sma': sma})
                    
                        # RSI
                        rsi_fast = rsi_fn(ticker_weekly_prices_to_date, 8)
                        stocks_data[ticker].update({'rsi_fast': rsi_fast})

                    except IndexError:
                        stocks_data[ticker].update({'sma': float(np.nan)})
                        stocks_data[ticker].update({'rsi_fast': float(np.nan)})

                    # COMPUTING SINGLE STOCKS AV. PRICE BELOW OR ABOVE ITS SMA
                    try:
                        last_trading_date = price_set_current_period[-1]

                        ticker_prices_to_date = pd.Series(
                            {date: price['Close'] for date, price in stocks_prices[ticker].items()}
                            ).loc[:last_trading_date].iloc[::-5].iloc[:tickers_sma_periods]
                        
                        is_sma_below: int = 0 
                        if ticker_prices_to_date.iloc[0] < ticker_prices_to_date.mean():
                            is_sma_below = 1
                    except IndexError:
                        is_sma_below = float(np.nan)

                    stocks_data[ticker].update({'is_sma_below': is_sma_below})
            
        intervals_data[rank_date] = stocks_data

    return intervals_data


def limit_ranked_data_from_start_date(
        ranked_data: dict[str, dict[str, float | None]],
        first_ranking_date: str | None = None
    ) -> None:
    
    timed_ranked_data = {}
    for date, data in ranked_data.items():
        timed_ranked_data[date] = data
        if date == first_ranking_date:
            break
    
    return timed_ranked_data