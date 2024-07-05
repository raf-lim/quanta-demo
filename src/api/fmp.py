import logging
import os
from dataclasses import dataclass
from typing import Optional, Literal


@dataclass
class EndPoints:
    """End points urls for a given company symbol."""
    api_base_url: str = 'https://financialmodelingprep.com/api'
    api_key: str = os.getenv('API_KEY')
    stock_exchange_index: Literal['sp500', 'nasdaq'] = 'sp500'

    @property
    def url_index_constituents(self) -> str:
        """End point for all stock_exchange_index constituents."""
        return (
            f'{self.api_base_url}/v3/'
            f'{self.stock_exchange_index}_constituent'
            f'?apikey={self.api_key}'
        )
    
    @property
    def url_index_historical(self) -> str:
        """End point for all stock_exchange_index constituents."""
        return (
            f'{self.api_base_url}/v3/historical/'
            f'{self.stock_exchange_index}_constituent'
            f'?apikey={self.api_key}'
        )
    
    @property
    def url_symbol_changes(self) -> str:
        """End point for stocks' symbols changes."""
        return (
            f'{self.api_base_url}/v4/symbol_change'
            f'?apikey={self.api_key}'
        )

    def get_url_income_statement(self, symbol: str, limit: Optional[int]) -> str:
        """
        End point for quarterly income statements.
        """
        try:
            return (
                f'{self.api_base_url}/v3/income-statement/{symbol.upper()}'
                f'?period=quarter&limit={limit}&apikey={self.api_key}'
            )
        except AttributeError as e:
            logging.info(f'income statement url error with {symbol}, {e}')

    def get_url_balance_sheets(self, symbol: str, limit: Optional[int]) -> str:
        """
        End point for quarterly balance sheets.
        """
        try:
            return (
                f'{self.api_base_url}/v3/balance-sheet-statement/{symbol.upper()}'
                f'?period=quarter&limit={limit}&apikey={self.api_key}'
            )
        except AttributeError as e:
            logging.info(f'balance sheet url error with {symbol}, {e}')

    def get_url_earning_calendar(self, symbol: str, limit: Optional[int]) -> str:
        """
        End point for historical earnigs calendar to pull adjusted earnings.
        """
        try:
            return (
                f'{self.api_base_url}/v3/historical/earning_calendar/{symbol.upper()}'
                f'?limit={limit}&apikey={self.api_key}'
            )
        except AttributeError as e:
            logging.info(f'earning calendar url error with {symbol}, {e}')

    def get_url_prices(self, ticker: str, start_date: str) -> str:
        """End point for daily prices
        :param str start_date: format YYYY-MM-DD
        """
        return (
            f'{self.api_base_url}/v3/historical-price-full/{ticker}?'
            f'from={start_date}&apikey={self.api_key}'
        )
    