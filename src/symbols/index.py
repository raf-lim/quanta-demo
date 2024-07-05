import logging
import datetime
import tomllib
import json
import pandas as pd
from api import fmp, http_get
from symbols import getters as symb_proc
from libs.helpers.interfaces import ReplaceIntervals


def main() -> None:

    with open('config.toml', 'rb') as file:
        config = tomllib.load(file)
    
    REPLACEMENT_FREQUENCY = config['replacement']['frequency']
    if REPLACEMENT_FREQUENCY == ReplaceIntervals.MONTHLY:
        NUMBER_OF_PERIODS = config['collect']['number_of_months']
        INTERVAL_FREQ = 'ME'
    elif REPLACEMENT_FREQUENCY == ReplaceIntervals.WEEKLY:
        NUMBER_OF_PERIODS = config['collect']['number_of_weeks']
        INTERVAL_FREQ = 'W-FRI'
    
    PERIOD_TICKERS = config['repo_files']['period_tickers']

    urls = fmp.EndPoints()

    current_index_data  = http_get.http_get_sync(urls.url_index_constituents)
    historical_index_data = http_get.http_get_sync(urls.url_index_historical)
    
    current_tickers = symb_proc.get_current_index_tickers(current_index_data)

    logging.info(f'Number of current symbols: {len(current_tickers)}')

    intervals = pd.interval_range(
        end=pd.Timestamp(datetime.date.today() + datetime.timedelta(weeks=4)),
        periods=NUMBER_OF_PERIODS,
        freq=INTERVAL_FREQ
    )[::-1]

    logging.info(f'first interval: {intervals[-1].right}')
    logging.info(f'last interval: {intervals[0].right}')

    period_tickers = symb_proc.get_index_tickers_for_periods(
        current_tickers,
        intervals,
        historical_index_data,
    )

    with open(PERIOD_TICKERS, 'w') as file:
        json.dump(period_tickers, file, indent=4)
    logging.info('repo period tickers saved.')


if __name__ == '__main__':
    main()
