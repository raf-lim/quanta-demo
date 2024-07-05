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
    Get all symbols and their all days in portfolio
    within current week (not incl. last trading dates of previous week)
    Used for strategy computation.
    """
    dates_in_portfolio = {}

    for week_last_date, stocks_ranking in rank_input_data.items():

        # Filters out stocks with RS rank not in first 200.
        if is_ranking_rs_limited:
            stocks_ranking = stocks_ranking.sort_values(
                by='rank', ascending=False
            ).iloc[:rs_limit - 1, :]

        # Filters out from TOP stocks with SMA_STOCK < last
        if is_ranking_sma_filtered:
            stocks_ranking = stocks_ranking.query('is_sma_below == 0')

        top_stocks = sorted(stocks_ranking.iloc[:, -1].sort_values(
            ascending=False).iloc[:number_of_top_stocks].index)
        
        next_week_dates = pd.date_range(
            start=week_last_date, periods=8, freq='D')[3:]

        next_week_dates = [str(i.date()) for i in next_week_dates]
        
        for stock in top_stocks:
                
            stock_trading_dates = stocks_prices[stock].keys()

            next_week_trading_dates = sorted(
                set(next_week_dates).intersection(set(stock_trading_dates))
            )

            if stock not in dates_in_portfolio:
                dates_in_portfolio[stock] = next_week_trading_dates
            else:
                trading_dates = dates_in_portfolio[stock]
                trading_dates.extend(next_week_trading_dates)
                dates_in_portfolio[stock] = sorted(set(trading_dates))

    return dates_in_portfolio