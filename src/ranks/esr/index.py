import os
from typing import Iterable
import logging
import tomllib
import json
from libs.helpers.interfaces import ReplaceIntervals
from symbols import getters as symb_get
from symbols import cleaners as symb_clean
from prices import prices
from financials import cleaners as fin_clean 
from ranks.esr import processors as rank_proc
from indicators.rsi import compute_rsi


def main() -> None:

    with open('config.toml', 'rb') as file:
        config = tomllib.load(file)

    PERIOD_TICKERS_FILE = config['repo_files']['period_tickers']
    IS_DATA_FILE = config['repo_files']['income_statements']
    BS_DATA_FILE = config['repo_files']['balance_sheets']
    EC_DATA_FILE = config['repo_files']['earning_calendars']
    DB_FILE = config['repo_files']['db']

    TICKERS_TO_REMOVE = config['portfolio']['tickers_to_remove']
    SMA_PERIOD_STOCKS = config['rank_input']['sma_stocks']
    RANK_WITH_TECH_INDICATORS = config['rank_input']['with_tech_indicators']

    RANK_STRATEGY = config['rank']['strategy']

    REPLACEMENT_FREQUENCY = config['replacement']['frequency']
    if REPLACEMENT_FREQUENCY == ReplaceIntervals.MONTHLY:
        INTERVAL_FREQ = 'ME'
        RANK_INTERVAL = 'monthly'
    elif REPLACEMENT_FREQUENCY == ReplaceIntervals.WEEKLY:
        INTERVAL_FREQ = 'W-FRI'
        RANK_INTERVAL = 'weekly'
    
    RANK_INPUT_FILE = os.path.join(
        config['repo_files']['path'],
        f'rank_input_data_{RANK_STRATEGY}_{RANK_INTERVAL}.json'
    )

    with open(PERIOD_TICKERS_FILE) as file:
        raw_period_tickers: dict[str, Iterable[str]] = (json.load(file))

    period_tickers = symb_clean.clean_period_tickers(
        period_tickers=raw_period_tickers,
        tickers_to_remove=TICKERS_TO_REMOVE
    )

    with open(IS_DATA_FILE) as file:
        raw_is: dict[str, list[dict[str | float]]] = (json.load(file))
    income_statements = fin_clean.clean_income_statements_data(raw_is)
    logging.info(f'Income Statements: {len(income_statements)}')

    with open(BS_DATA_FILE) as file:
        raw_bs: dict[str, list[dict[str | float]]] = (json.load(file))
    balance_sheets = fin_clean.clean_balance_sheets_data(raw_bs)
    logging.info(f'Balance Sheets: {len(balance_sheets)}')

    with open(EC_DATA_FILE) as file:
        raw_ec: dict[str, list[dict[str | float]]] = (json.load(file))
    earning_calendars = fin_clean.clean_earning_calendar_data(raw_ec)
    logging.info(f'Earning Calendars: {len(earning_calendars)}')

    financial_statements_data = rank_proc.merge_financial_data(
        income_statements,
        balance_sheets,
    )

    stocks_financial_data = rank_proc.merge_earning_calendars(
        financial_statements_data,
        earning_calendars
    )
    logging.info(
        f'Successfully processed financial_data: {len(stocks_financial_data)}'
    )

    all_tickers = symb_get.get_all_ptf_tickers(period_tickers)
    stocks_prices = prices.get_stocks_prices_form_db(
        all_tickers,
        DB_FILE
    )

    rank_dates = tuple(period_tickers.keys())
    
    logging.info(f'first rank date: {rank_dates[-1]}')
    logging.info(f'last rank date: {rank_dates[0]}')

    stock_interval_report_position = rank_proc.create_starting_positions(
        tickers=all_tickers,
        financial_data=stocks_financial_data,
        rank_dates=rank_dates,
        interval_freq=INTERVAL_FREQ
    )

    rank_input_data = rank_proc.process_data_for_ranking(
        period_symbols=period_tickers,
        interval_freq=INTERVAL_FREQ,
        stocks_prices=stocks_prices,
        stocks_financial_data=stocks_financial_data,
        stock_interval_report_position=stock_interval_report_position,
        tickers_sma_periods=SMA_PERIOD_STOCKS,
        rsi_fn=compute_rsi,
        with_tech_indicators=RANK_WITH_TECH_INDICATORS
    )

    with open(RANK_INPUT_FILE, 'w') as file:
        json.dump(rank_input_data, file, indent=4)

    logging.info('repo interval data for ranking saved.')