from typing import Iterable
import logging
import tomllib
import json
from api import fmp
from symbols import getters as symb_get
from symbols import cleaners as symb_clean
from financials import getters as fin_get


def main() -> None:

    with open('config.toml', 'rb') as file:
        config = tomllib.load(file)

    PERIOD_TICKERS_FILE = config['repo_files']['period_tickers']
    IS_DATA_FILE = config['repo_files']['income_statements']
    BS_DATA_FILE = config['repo_files']['balance_sheets']
    EC_DATA_FILE = config['repo_files']['earning_calendars']

    FS_LIMIT = config['collect']['financial_statements_limit']
    TICKERS_TO_REMOVE = config['portfolio']['tickers_to_remove']

    with open(PERIOD_TICKERS_FILE) as file:
        raw_period_tickers: dict[str, Iterable[str]] = (json.load(file))

    period_tickers = symb_clean.clean_period_tickers(
        period_tickers=raw_period_tickers,
        tickers_to_remove=TICKERS_TO_REMOVE
    )

    all_tickers = symb_get.get_all_ptf_tickers(period_tickers)

    urls = fmp.EndPoints()

    is_data = fin_get.get_raw_financial_data(
        all_tickers=all_tickers,
        url_fn=urls.get_url_income_statement,
        fs_limit=FS_LIMIT
    )
    with open(IS_DATA_FILE, 'w') as file:
        json.dump(is_data, file)

    logging.info(f'Income Statements: {len(is_data)}')

    bs_data = fin_get.get_raw_financial_data(
        all_tickers=all_tickers,
        url_fn=urls.get_url_balance_sheets,
        fs_limit=FS_LIMIT
    )
    with open(BS_DATA_FILE, 'w') as file:
        json.dump(bs_data, file)

    logging.info(f'Balance Sheets: {len(bs_data)}')

    ec_data = fin_get.get_raw_financial_data(
        all_tickers=all_tickers,
        url_fn=urls.get_url_earning_calendar,
        fs_limit=FS_LIMIT + 12
    )
    with open(EC_DATA_FILE, 'w') as file:
        json.dump(ec_data, file)

    logging.info(f'Earning Calendars: {len(ec_data)}')


if __name__ == '__main__':
    main()