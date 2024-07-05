from dataclasses import dataclass
import pandas as pd


@dataclass
class Benchmark:
    ticker: str
    start_date: str
    end_date: str
    init_capital: float
    prices: dict[str, dict[str, float | None]]

    @property
    def open_prices(self) -> pd.Series:
        """Extracts open prices and converts into series."""
        data = (
            pd.DataFrame(self.prices.get(self.ticker.upper())).transpose()
            .loc[:, 'Open']
            .sort_index()
            .loc[self.start_date:self.end_date]
        )
        data.name = f'{self.ticker}_open'

        return data

    @property
    def returns(self) -> pd.Series:
        """Compte returns from prices"""
        data = self.open_prices.pct_change()
        data.name = f'{self.ticker}_returns'
        
        return data
    
    @property
    def nav(self) -> pd.Series:
        """Compute Net Asset Value."""
        data = (1 + self.returns).cumprod() * self.init_capital
        data.iloc[0] = self.init_capital
        data.name = f'{self.ticker}_nav'

        return data

    def compute_period_returns(self, selected_dates: list[str]) -> pd.Series:
        """Compute returns between selected dates."""
        data = self.open_prices.loc[selected_dates].pct_change()
        data.name = self.ticker.upper()

        return data