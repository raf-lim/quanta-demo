import logging
import os
from typing import Iterable
import logging
import datetime
import sqlite3
import tomllib
import json
from api import http_get, fmp
from symbols import getters


def main() -> None:

    with open('config.toml', 'rb') as file:
        config = tomllib.load(file)

    PERIOD_TICKERS_FILE = config['repo_files']['period_tickers']
    DB_FILE = config['repo_files']['db']
    BENCHMARK_TICKER = config['portfolio']['benchmark']
    PRICES_WEEKS_DELTA = config['collect']['prices_weeks_delta']

    try:
        os.remove(DB_FILE)
    except FileNotFoundError:
        pass

    with open(PERIOD_TICKERS_FILE) as file:
        period_tickers: Iterable[str] = (json.load(file))

    all_tickers = getters.get_all_ptf_tickers(period_tickers)
    all_tickers.append(BENCHMARK_TICKER.upper())

    start_date = (
        datetime.datetime.strptime(
            tuple(period_tickers.keys())[-1], '%Y-%m-%d'
            )
        - datetime.timedelta(weeks=PRICES_WEEKS_DELTA)
        )
    start_date = str(start_date.date())
    logging.info(f'prices starting date: {start_date}')

    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()

    urls = fmp.EndPoints()

    for tick in all_tickers:
        raw_data = http_get.http_get_sync(
            urls.get_url_prices(tick, start_date)
            )
        if raw_data:
            ticker = raw_data.get('symbol').replace('.', '-')
            data = raw_data.get('historical')

        prices_data = [(i['date'], i['open'], i['high'], i['low'], i['close']) for i in data]

        try:
            cur.execute(f'''
                        CREATE TABLE IF NOT EXISTS '{ticker.lower()}' (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date DATETIME,
                            open FLOAT,
                            high FLOAT,
                            low FLOAT,
                            close FLOAT
                        )''')
        except sqlite3.OperationalError:
            logging.warning(ticker)
            continue

        for row in prices_data:
            cur.execute(f'''
                        INSERT INTO '{ticker.lower()}' (date, open, high, low, close)
                        VALUES {row}''')

        cur.execute(f'''
                    SELECT date, open, high, low, close
                    FROM '{ticker.lower()}'
                    ORDER BY date'''
                    )

    con.commit()
    con.close()
        
    logging.info('prices saved to database.')


if __name__ == '__main__':
    main()