from typing import Iterable
import logging
import tomllib
import json
from symbols import getters as symb_get
from symbols import cleaners as symb_clean
from financials import cleaners as fin_clean 
from ranks.esr import processors as rank_proc


def main() -> None:

    with open('config.toml', 'rb') as file:
        config = tomllib.load(file)

    PERIOD_TICKERS_FILE = config['repo_files']['period_tickers']
    IS_DATA_FILE = config['repo_files']['income_statements']
    BS_DATA_FILE = config['repo_files']['balance_sheets']
    EC_DATA_FILE = config['repo_files']['earning_calendars']
    TICKERS_TO_REMOVE = config['portfolio']['tickers_to_remove']
    
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

    output = {}
    ciks = {}
    for ticker in all_tickers:
        try:
            output[ticker] = {i.get('date')[:-3]: i.get('eps') for i in stocks_financial_data.get(ticker)}
            ciks[ticker] = stocks_financial_data.get(ticker)[0].get('cik')
        except TypeError:
            continue
    
    import pandas as pd
    x = pd.DataFrame(output).sort_index().transpose().loc[:, '2013-12':]
    y = pd.Series(ciks, name='CIK').sort_index()

    y.to_frame().merge(x, how='right', left_index=True, right_index=True).to_excel('files_output/eps_adj.xlsx')


if __name__ == '__name__':
    main()