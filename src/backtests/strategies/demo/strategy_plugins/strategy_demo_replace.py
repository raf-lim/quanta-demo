from typing import Iterable
import logging
import pandas as pd
import numpy as np

pd.set_option('future.no_silent_downcasting', True)


def compute_ptf_performance(
        stocks_dates_in_ptf: dict[str, Iterable[str]],
        ptf_dates: Iterable[str],
        stocks_prices: dict[str, dict[str, float | None]],
        first_trading_dates_of_month: list[str],
        is_rebalanced: bool,
        transaction_fee: float,
        init_capital: float,
    ) -> Iterable[pd.DataFrame]:
    """
    Compute ptf returns based on strategy applied.
    """

    cap_invested: float = init_capital
    tickers = []
    tickers_cap= {}
    free_cash: float = 0
    ptf = {}
    # Informative:
    price_in_ptf = {}
    returns_in_ptf = {}
    cap_in_ptf = {}
    share_in_ptf = {}

    for n, date in enumerate(ptf_dates):
        
        if n == 0:
            tickers = sorted([
                ticker for ticker, dates in stocks_dates_in_ptf.items()
                if date in dates
                ])

            ticker_init_cap = cap_invested / len(tickers)

            tickers_cap= {
                ticker: ticker_init_cap - (ticker_init_cap * transaction_fee)
                for ticker in tickers
            }
            # Informative:
            tick_price = {}
            tick_returns = {}
            tick_cap = {}
            for ticker in tickers:
                tick_price[f'{ticker}_open'] = stocks_prices[ticker][date]['Open']
                tick_returns[f'{ticker}_ret'] = 0
                tick_cap[f'{ticker}_cap'] = ticker_init_cap - (ticker_init_cap * transaction_fee)
            
            price_in_ptf[date] = tick_price
            returns_in_ptf[date] = tick_returns
            cap_in_ptf[date] = tick_cap
            
            share_in_ptf[date] = {
                ticker: cap/cap_invested for ticker, cap in tickers_cap.items()
            }

            ptf[date] = {
                    'invested': cap_invested,
                    'returns_on_invested': 0,
                    'free_cash': free_cash,
                    'tickers': tickers,
                    'sell_trans': 0,
                    'buy_trans': len(tickers),
                    'stocks_in_ptf': len(tickers),
                    'replace_trans_costs': cap_invested * transaction_fee,
                    'replace_trans_counts': len(tickers),
                    'tickers_to_buy': tickers,
                    'bought': tickers,
            }

            '''
            Returns are computed from yesterday's open to today's open !!!
            strategy applies actually from the init cap invested as it gets
            adjusted next day morning.
            '''
        elif n > 0:

            # RETURNS (timing: open on the day)
            
            tickers_new_cap = {}
            replace_trans_costs: float = 0
            replace_trans_count: int = 0
            # Informative:
            tick_price = {}
            tick_returns = {}

            for ticker in tickers:
                try:
                    start_cap = tickers_cap[ticker]
                    start_price = stocks_prices[ticker][ptf_dates[n-1]]['Open']
                except KeyError:
                    logging.warning(f'{ticker} not in tickers cap on {date}')
                try:
                    end_price = stocks_prices[ticker][date]['Open']
                except KeyError:
                    stop_trans_cost = start_cap * transaction_fee
                    free_cash += start_cap - stop_trans_cost
                    replace_trans_costs += stop_trans_cost
                    replace_trans_count +=1
                    tickers_cap.pop(ticker)
                    logging.warning(f'{ticker} stopped trading {ptf_dates[n-1]}')
                    continue
                
                returns = end_price / start_price - 1

                ticker_new_cap = start_cap + (start_cap * returns)
                tickers_new_cap[ticker] = ticker_new_cap

                # Informative:
                tick_price[f'{ticker}_open'] = end_price
                tick_returns[f'{ticker}_ret'] = returns
                #tick_cap[f'{ticker}_cap'] = ticker_new_cap 
                

            cap_invested = sum(cap for cap in tickers_new_cap.values())

            try:
                returns_invested = (
                    cap_invested / sum(cap for cap in tickers_cap.values()) - 1
                    )
            except ZeroDivisionError:
                returns_invested = float(np.nan)
                pass

            tickers_cap = tickers_new_cap

            new_tickers = sorted([
                ticker for ticker, dates in stocks_dates_in_ptf.items()
                if date in dates
                ])

            # SHOW POSITIONS' VALUE OF TICKERS TO SELL
            tickers_to_sell_released_cap = {}

            # REPLACE STOCKS IN PORTFOLIO
            tickers_to_sell = set(tickers).difference(set(new_tickers))
            tickers_to_buy = set(new_tickers).difference(set(tickers))

            if tickers_to_sell:
                for ticker in tickers_to_sell:
                    try:
                        ticker_cap = tickers_cap[ticker]
                        sell_trans_cost = ticker_cap * transaction_fee
                        free_cash += ticker_cap - sell_trans_cost
                    except KeyError:
                        continue

                    # SHOW POSITIONS' VALUE OF TICKERS TO SELL
                    try:
                        tickers_to_sell_released_cap[ticker] = (
                            (tickers_cap[ticker] - sell_trans_cost) / cap_invested
                        )
                    except ZeroDivisionError:
                        tickers_to_sell_released_cap[ticker] = float(np.nan)

                    replace_trans_costs += sell_trans_cost
                    replace_trans_count += 1
                    tickers_cap.pop(ticker)
                cap_invested = sum(cap for cap in tickers_cap.values())

            if tickers_to_buy:
                capital_to_invest = free_cash / len(tickers_to_buy)
                for ticker in tickers_to_buy:
                    buy_trans_cost = capital_to_invest * transaction_fee
                    tickers_cap.update({ticker: capital_to_invest - buy_trans_cost})
                    replace_trans_costs += buy_trans_cost
                    replace_trans_count += 1
                free_cash = 0
                cap_invested = sum(cap for cap in tickers_cap.values())

            # REBALANCE
            rebalance_trans_costs: float = 0
            rebalance_trans_count: int = 0

            if is_rebalanced:
                if date in first_trading_dates_of_month:
                    ptf_cap = sum(cap for cap in tickers_cap.values())
                    rebalanced_stock_cap = ptf_cap / len(tickers_cap)
                    rebalanced_tickers_cap = {}
                    for ticker, cap in tickers_cap.items():
                        rebalanced_tickers_cap[ticker] = (
                            rebalanced_stock_cap
                            - (abs(cap - rebalanced_stock_cap) * transaction_fee)
                        )
                        rebalance_trans_costs += (
                            abs(cap - rebalanced_stock_cap) * transaction_fee
                        )
                        rebalance_trans_count += 1
                    tickers_cap = rebalanced_tickers_cap
                    cap_invested = sum(cap for cap in tickers_cap.values())
            

            tickers = new_tickers

            # Informative
            price_in_ptf[date] = tick_price
            returns_in_ptf[date] = tick_returns
            cap_in_ptf[date] = {f'{ticker}_cap': cap for ticker, cap in tickers_cap.items()}

            try:
                share_in_ptf[date] = {
                    ticker: cap/cap_invested for ticker, cap in tickers_cap.items()
                }
            except ZeroDivisionError:
                share_in_ptf[date] = {}

            ptf[date] = {
                'invested': cap_invested,
                'returns_on_invested': returns_invested,
                'free_cash': free_cash,
                'tickers': tickers,
                'sell_trans': len(tickers_to_sell),
                'buy_trans': len(tickers_to_buy),
                'stocks_in_ptf': len(tickers),
                'replace_trans_costs': replace_trans_costs,
                'replace_trans_counts': replace_trans_count,
                'rebal_trans_costs': rebalance_trans_costs,
                'rebal_trans_counts': rebalance_trans_count, 
                'sold': sorted(tickers_to_sell) if tickers_to_sell else np.nan,
                'bought': sorted(tickers_to_buy) if tickers_to_buy else np.nan,
                'to_sell_share': {
                    ticker: f"{share:.1%}"
                      for ticker, share in tickers_to_sell_released_cap.items()
                    } if tickers_to_sell_released_cap else np.nan,
                'to_sell_average_share': f"{np.average(
                    [share for share in tickers_to_sell_released_cap.values()]
                    ):.2%}" if tickers_to_sell_released_cap else np.nan
                }
            
    ptf_df = pd.DataFrame(ptf).transpose()
    ptf_df['nav'] = ptf_df['invested'] + ptf_df['free_cash']

    ptf_df = ptf_df.loc[:, [
        'invested',
        'returns_on_invested',
        'free_cash',
        'nav',
        'stocks_in_ptf',
        'tickers',
        'sell_trans',
        'buy_trans',
        'replace_trans_counts',
        'replace_trans_costs',
        'rebal_trans_counts',
        'rebal_trans_costs',
        'sold',
        'bought',
        'to_sell_share',
        'to_sell_average_share',
    ]]

    return (
        ptf_df,
        pd.DataFrame(price_in_ptf).transpose(),
        pd.DataFrame(returns_in_ptf).transpose(),
        pd.DataFrame(cap_in_ptf).transpose(),
        pd.DataFrame(share_in_ptf).transpose()
    )