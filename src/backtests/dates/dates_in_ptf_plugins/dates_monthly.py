from typing import Optional, Iterable
import pandas as pd


def get_stocks_dates_in_ptf(
        rank_input_data: dict[str, pd.DataFrame],
        stocks_prices: dict[str, dict[str, float | None]],
        number_of_top_stocks: int,
        is_ranking_rs_limited: bool = False,
        is_ranking_sma_filtered: bool = False,
        rs_limit: Optional[int] = 0
    ) -> dict[str, Iterable[str]]:
    """
    Get ranked symbols and their all days in portfolio
    within current month (not incl. last trading dates of previous month.)
    Used for strategy computation.
    """
    dates_in_portfolio: dict[str, Iterable[str]] = {}

    for rank_date, stocks_ranking in rank_input_data.items():

        #stocks_ranking = stocks_ranking.loc[stocks_ranking['esr_rank'].notna()]

        # Filters out stocks with RS rank not in first 200.
        if is_ranking_rs_limited:
            stocks_ranking = stocks_ranking.sort_values(
                by='rank', ascending=False
            ).iloc[:rs_limit - 1, :]

        # Filters out from TOP stocks with SMA_STOCK < last
        if is_ranking_sma_filtered:
            stocks_ranking = stocks_ranking.query('is_sma_below == 0')

        # Sorted list by esr_rank (descending)
        top_stocks = sorted(
            stocks_ranking.loc[:, 'rank'].sort_values(ascending=False)
            .iloc[:number_of_top_stocks].index
        )
        
        rank_date = pd.to_datetime(rank_date)

        next_month_interval_range = pd.interval_range(
            start=rank_date, periods=1, freq='ME')
        
        next_month_dates_range = pd.date_range(
            start=next_month_interval_range[0].left,
            end=next_month_interval_range[0].right,
            freq='D',
        )
        next_month_dates = (
            [str(i.date()) for i in next_month_dates_range[1:]]
        )
        
        for stock in top_stocks:

            stock_trading_dates = stocks_prices[stock].keys()
            
            next_month_trading_dates = sorted(
                set(stock_trading_dates).intersection(set(next_month_dates))
            )

            if stock not in dates_in_portfolio:
                dates_in_portfolio[stock] = next_month_trading_dates
            else:
                trading_dates = dates_in_portfolio[stock]
                trading_dates.extend(next_month_trading_dates)
                dates_in_portfolio[stock] = sorted(set(trading_dates))
            
    return dates_in_portfolio