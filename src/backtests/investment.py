from typing import Iterable
from dataclasses import dataclass
from functools import cached_property
import datetime
import pandas as pd
import numpy as np


@dataclass
class Investment:
    name: str
    backtest_data: pd.DataFrame
    periods_per_year: int = 252

    @cached_property
    def nav(self) -> pd.Series:
        try:
            return self.backtest_data.loc[:, 'nav']
        except KeyError:
            return self.backtest_data.loc[:, f'{self.name}_nav']

    @cached_property
    def returns(self) -> pd.Series:
        data = self.nav.pct_change()
        data.name = f'{self.name}_returns'
        return data

    @cached_property
    def cumulative_returns(self) -> float:
        return (1 + self.returns).prod() - 1

    @cached_property
    def annualized_returns(self) -> float:
        n_periods = len(self.returns)
        return (
            (1 + self.cumulative_returns) 
            ** (self.periods_per_year / n_periods) - 1
            )

    @cached_property
    def annualized_volatility(self) -> float:
        return self.returns.std() * (self.periods_per_year ** 0.5)

    @property
    def raw_sharp_ratio(self) -> float:
        return self.annualized_returns / self.annualized_volatility
    
    @cached_property
    def previous_peaks(self) -> pd.Series:
        data = self.nav.cummax()
        data.name = f'{self.name}_previous_peaks'
        return data
    
    @property
    def drawdowns(self) -> pd.Series:
        data = (self.nav - self.previous_peaks) / self.previous_peaks
        data.name = f'{self.name}_drawdowns'
        return data
    
    @property
    def days_invested(self):
        return len(self.nav)

    @property
    def drawdowns_stats(self) -> pd.DataFrame:
        peaks = self.previous_peaks.groupby(
            by=self.previous_peaks.values, sort=True).groups
        
        for previous_peak, dates in peaks.items():
            peaks.update(
                {previous_peak: {date: self.drawdowns[date] for date in dates}})

        stats = {}
        for previous_peak, data in peaks.items():
            length: int = len(data)
            sorted_dates: list[datetime.date] = sorted(data.keys())
            started: datetime.date = sorted_dates[0]
            max_ddwn: float = min(data.values())
            max_ddwn_date: datetime.date = (
                [k for k, v in data.items() if v == max_ddwn][0]
            )
            stats[started] = {
                f'# of periods': length,
                f'max drawdown': max_ddwn,
                f'max drawdown timing': max_ddwn_date,
                f'periods to max dd': sorted_dates.index(max_ddwn_date)
                }
            
        res = pd.DataFrame(stats).transpose().sort_values(by=f'max drawdown')
        res = res.loc[res['max drawdown'] < 0]
        res.index.name = 'started'
        res.reset_index(inplace=True)
        res.rename(columns={
            'started': f'started ({self.name})',
            '# of periods': f'# of periods ({self.name})',
            'max drawdown': f'max drawdown ({self.name})',
            'max drawdown timing': f'max drawdown timing ({self.name})',
            'periods to max dd': f'periods to max dd ({self.name})',
            }, inplace=True)

        return res

    @property
    def replace_transactions_number(self):
        """Number of sell and buy transactions replacing stocks"""
        try:
            return (
                self.backtest_data.loc[:, 'replace_trans_counts']
                .sum(skipna=True)
            )
        except (KeyError, AttributeError):
            return float(np.nan)
    
    @property
    def replace_transactions_cost(self):
        """Total of sell and buy transactions replacing stocks"""
        try:
            return (
                self.backtest_data.loc[:, 'replace_trans_costs']
                .sum(skipna=True)
            )
        except (KeyError, AttributeError):
            return float(np.nan)

    @property
    def rebalance_transactions_number(self):
        """Number of sell and buy transactions when rebalancing"""
        try:
            return (
                self.backtest_data.loc[:, 'rebal_trans_counts']
                .sum(skipna=True)
            )
        except (KeyError, AttributeError):
            return float(np.nan)

    @property
    def rebalance_transactions_cost(self):
        """Cost of sell and buy transactions when rebalancing"""
        try:
            return (
                self.backtest_data.loc[:, 'rebal_trans_costs']
                .sum(skipna=True)
            )
        except (KeyError, AttributeError):
            return float(np.nan)

    @property
    def strategy_transactions_number(self):
        """Number of sell and buy transactions realizing strategy"""
        try:
            return self.backtest_data.loc[:, 'strategy_trans_counts'].sum()
        except (KeyError, AttributeError):
            return float(np.nan)

    @property
    def strategy_transactions_cost(self):
        """Cost of sell and buy transactions realizing strategy"""
        try:
            return (
                self.backtest_data.loc[:, 'strategy_trans_costs']
                .sum(skipna=True)
            )
        except (KeyError, AttributeError):
            return float(np.nan)
    
    @property
    def extreme_daily_returns(self):
        """Check the extremes to find potential problems with api data."""
        returns = self.backtest_data.loc[:, 'returns_on_invested']
        data = pd.Series({
            'max_daily_returns_from_invested': f'{returns.max():.2%}',
            'min_daily_returns_from_invested': f'{returns.min():.2%}'
            })
        data.name = self.name
        return data 

    @property
    def metrics(self) -> pd.DataFrame:
        metrics = pd.Series({
            'last_ptf_value': self.nav.iloc[-1],
            'max_ptf_value': self.nav.max(),
            'cumulative_returns': self.cumulative_returns,
            'annualized_returns': self.annualized_returns,
            'annualized_volatility': self.annualized_volatility,
            'positive_months': self.returns[self.returns > 0].count(),
            'negative_months': self.returns[self.returns < 0].count(),
            'max_drawdown': self.drawdowns.min(),
            'raw_sharp_ratio': self.raw_sharp_ratio,
            'days_invested': self.days_invested,
            '# of replacement transactions': self.replace_transactions_number,
            'replacement transactions cost': self.replace_transactions_cost,
            '# of rebalance transactions': self.rebalance_transactions_number,
            'rebalance transactions cost': self.rebalance_transactions_cost,
            '# of strategy transactions': self.strategy_transactions_number,
            'strategy transactions cost': self.strategy_transactions_cost,
            })
        metrics.name = self.name
        return metrics
    
    def compute_period_returns(self, selected_dates: list[str]) -> pd.Series:
        """Compute returns between selected dates."""
        data = self.nav.loc[selected_dates].pct_change()
        data.name = self.name
        return data


def get_tickers_perf_detailed_info(
    tickers_prices: pd.DataFrame,
    tickers_returns: pd.DataFrame,
    tickers_nav: pd.DataFrame,
    tickers_share_in_ptf: pd.DataFrame
    ) -> pd.DataFrame:

    """
    Create table with combined prices,
    returns, capital and share in ptf.
    """
    info = []
    for ticker in tickers_share_in_ptf.columns:
        x = pd.concat([
            tickers_prices.loc[:, f'{ticker}_open'],
            tickers_returns.loc[:, f'{ticker}_ret'],
            tickers_nav.loc[:, f'{ticker}_cap'],
            tickers_share_in_ptf.loc[:, ticker],
        ], axis=1).sort_index()
        info.append(x)

    return pd.concat(info, axis=1).sort_index()


def get_tickers_share_in_pft_stats(
        tickers_share_in_ptf: pd.DataFrame
    ) -> pd.DataFrame:
    """Compute statitistics from tickrs share in ptf for each day."""
    number_of_stocks_in_ptf = len(tickers_share_in_ptf.columns)
    share_in_ptf = tickers_share_in_ptf.copy()
    
    share_in_ptf['share_max'] = share_in_ptf.apply(
        lambda x: x.iloc[:number_of_stocks_in_ptf].max(),
        axis=1
    )
    share_in_ptf['share_min'] = share_in_ptf.apply(
        lambda x: x.iloc[:number_of_stocks_in_ptf].min(),
        axis=1
    )
    share_in_ptf['share_mean'] = share_in_ptf.apply(
        lambda x: x.iloc[:number_of_stocks_in_ptf].mean(),
        axis=1
    )

    return share_in_ptf.iloc[:, -3:]