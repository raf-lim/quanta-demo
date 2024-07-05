import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def plot_returns(
        data: pd.Series, series_name: str, figsize: tuple[int, int] = (16, 7)):
    x = [n[0] for n in enumerate(data.index)]
    y = data.values
    slope = stats.linregress(x, y).slope
    intercept = stats.linregress(x, y).intercept

    color = (data > 0).apply(lambda x: 'g' if x else 'r')
    fig = plt.figure(figsize=figsize, tight_layout=True)
    data.plot.bar(rot=90, color=color)
    plt.axhline(y=0, lw=0.5, color='grey')
    plt.xlabel('')
    plt.xticks(np.arange(1, len(data), 3), fontsize=8)
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter('{:.0%}'.format))
    plt.legend([f'Last: {data[-1]:.2%}'])
    plt.title(
        f'{series_name} monthly returns in %, '
        f'last {len(y)} months\nSlope: {slope:.3f}, '
        f'Intercept: {intercept:.3f}',
        loc='left')
    plt.grid(axis='y', visible=True, ls='--', which='both')
    plt.grid(axis='x', visible=True, ls='--', which='major')


def plot_performance(
    performance: pd.DataFrame, number_of_top_stocks: int,
    compound_returns: float, annualized_returns: float,
    annualized_vol: float, raw_sharp_ratio: float,
    yscale: str, figsize: tuple[int, int] = (8, 6),
    annotation: bool = True) -> None:

    wealth = performance['wealth_index']
    drawdowns = performance['drawdowns']

    plt.plot(wealth)
    plt.axhline(y=0, lw=0.5, color='grey')
    plt.xlabel('')
    plt.xticks()
    plt.yscale(value=yscale)
    plt.title(
        f'TOP {number_of_top_stocks} Wealth Index in % for '
        f'last {len(wealth)} periods ({yscale.title()})')
    plt.grid(axis='y', visible=True, ls='--', which='both')
    plt.grid(axis='x', visible=True, ls='--', which='major')
    if annotation:
        plt.annotate(
            f'Compound Returns: {compound_returns:.1%}\n'
            f'Annualized Returns: {annualized_returns:.1%}\n'
            f'Annualized Volatility: {annualized_vol:.1%}\n'
            f'Raw Sharp Ratio: {raw_sharp_ratio:.2f}\n'
            f'Max Drawdown: {drawdowns.min():.1%}',
            xy=(wealth.index[0], wealth.max() * 3/4))
    plt.plot(drawdowns.idxmin(), 0, marker='^', markersize=12, color='r')


def plot_drawdowns(performance: pd.DataFrame) -> None:
    drawdowns = performance['drawdowns']
    max_drawdown = drawdowns.min()
    max_drawdown_date = drawdowns.idxmin()
    plt.plot(drawdowns, lw=0.75)
    plt.annotate(
        f'Max drawdown: {drawdowns.min():.1%}',
        xy=(max_drawdown_date, max_drawdown),
        xytext=(max_drawdown_date + pd.DateOffset(years=2), max_drawdown),
        arrowprops=dict(arrowstyle='->', lw=1, color='r'),
        color='r')
    plt.title('Portfolio drawdowns')
    plt.grid()
