from typing import Iterable, Callable
import sqlite3
import pandas as pd


def get_stocks_prices_form_db(
        symbols: Iterable[str], db_file_path: str
        ) -> dict[str, dict[str, dict[str, float | None]]]:
    connection = sqlite3.connect(db_file_path)
    cursor = connection.cursor()
    stocks_prices = {}
    for symbol in symbols:
        try:
            row = cursor.execute(
                f"SELECT date, open, close FROM '{symbol.lower()}' ORDER BY date"
                ).fetchall()
            stocks_prices[symbol.upper()] = (
                {i[0]: {'Open': i[1], 'Close': i[2]} for i in row}
                )
        except sqlite3.OperationalError:
            continue
    connection.close()

    return stocks_prices


def create_weekly_intervals(
        start_date: pd.Timestamp, end_date: pd.Timestamp
    ) -> pd.IntervalIndex:
    """Create weekly intervals for weekly close prices."""
    fridays = pd.date_range(start=start_date, end=end_date, freq='W-FRI')
    weekly_intervals = [
        pd.interval_range(end=pd.Timestamp(friday), freq='4D', periods=1)
          for friday in fridays
    ]
    return weekly_intervals


WeeklyIntervalsCreatorFn = (
    Callable[[pd.Timestamp, pd.Timestamp], pd.IntervalIndex]
)


def find_weekly_close_prices(
        ticker_prices: dict[str, float],
        weekly_intervals_creator: WeeklyIntervalsCreatorFn
    ):
    """Find last trading dates and close prices in a week."""
    ticker_prices_df = pd.DataFrame(
        {'date': ticker_prices.keys(), 'close': ticker_prices.values()}
    ).set_index('date').sort_index()

    ticker_trading_dates = pd.DatetimeIndex(ticker_prices_df.index)

    weekly_intervals = weekly_intervals_creator(
        start_date=ticker_trading_dates[0],
        end_date=ticker_trading_dates[-1]
    )
    trading_dates = []
    for interval in weekly_intervals:
        week_dates = pd.date_range(
            start=interval[0].left,
            end=interval[0].right,
            freq='1D'
        )
        try:
            last_trading_date = max(
                set(week_dates).intersection(set(ticker_trading_dates))
                )
            trading_dates.append(str(last_trading_date.date()))
        except IndexError:
            continue
        except ValueError:
            continue

    return ticker_prices_df.loc[trading_dates].reset_index()
