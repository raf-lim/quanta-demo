import os
import logging
from typing import Iterable
import importlib
import tomllib
import json
import pandas as pd
from libs.helpers import writers
from libs.helpers.interfaces import ReplaceIntervals
from symbols import getters as symb_proc
from prices import prices
from ranks.esr import rank
from ranks.esr import processors as rank_proc
from backtests.dates import backtest_dates, period_first_dates
from backtests import benchmark, investment


def main(scenarios: Iterable[Iterable[float]], first_rank_date: str) -> None: 

    with open('config.toml', 'rb') as file:
        config = tomllib.load(file)

    TOP = config['portfolio']['top']
    PTF_NAME = config['portfolio']['investment_name']
    
    INITIAL_CAPITAL = config['portfolio']['initial_capital']
    BENCHMARK_TICKER = config['portfolio']['benchmark']

    PERIODS_PER_YEAR = config['performance']['periods_per_year']
    IS_REBALANCED = config['performance']['is_rebalanced']

    RANK_STRATEGY = config['rank']['strategy']
    IS_RANK_BONGO_FILTERED = config['rank']['is_rank_sma_filtered']
    IS_RANK_SMA_FILTERED = config['rank']['is_rank_sma_filtered']
    IS_RANK_RS_LIMITED = config['rank']['is_rank_rs_limited']
    RS_LIMIT = config['rank']['rs_limit']
    
    PERIOD_TICKERS_FILE = config['repo_files']['period_tickers']
    DB_FILE = config['repo_files']['db']

    SCORING = config['scoring']

    REPLACE_STRATEGY = config['replacement']['replace_strategy']
    TRANSACTION_FEE = config['replacement']['transaction_fee']

    REPLACEMENT_FREQUENCY = config['replacement']['frequency']
    if REPLACEMENT_FREQUENCY == ReplaceIntervals.MONTHLY:
        RANK_INTERVAL = 'monthly'
    elif REPLACEMENT_FREQUENCY == ReplaceIntervals.WEEKLY:
        RANK_INTERVAL = 'weekly'

    RANK_INPUT_FILE = os.path.join(
        config['repo_files']['path'],
        f'rank_input_data_{RANK_STRATEGY}_{RANK_INTERVAL}.json'
    )

    RANK_OUTPUT_FILE = os.path.join(
        config['output_files']['path'],
        f'ranked_{RANK_STRATEGY}_{RANK_INTERVAL}'
    )
    BACKTEST_OUTPUT_FILE = os.path.join(
        config['output_files']['path'],
        f'backtest_{RANK_STRATEGY}_{RANK_INTERVAL}_top{TOP}_{REPLACE_STRATEGY}'
    )
    PERF_OUTPUT_FILE = os.path.join(
        config['output_files']['path'],
        f'perform_{RANK_STRATEGY}_{RANK_INTERVAL}_top{TOP}_{REPLACE_STRATEGY}'
    )

    with open(PERIOD_TICKERS_FILE) as file:
        period_tickers: Iterable[str] = (json.load(file))

    all_tickers = symb_proc.get_all_ptf_tickers(period_tickers)

    stocks_prices = prices.get_stocks_prices_form_db(
        all_tickers,
        DB_FILE
    )

    with open(RANK_INPUT_FILE) as file:
        rank_input_data: dict[str, dict[str, dict[str, float]]] = json.load(file)

    ranked_data_output: dict[str, dict[str, pd.DataFrame| None]] = {}

    ptfs_backtests: dict[str, pd.DataFrame] = {}
    ptfs_tickers_share_in_ptf_stats: dict[str, pd.DataFrame] = {}
    ptfs_tickers_infos: dict[str, pd.DataFrame] = {}

    ptfs_perf_metrics: dict[str, dict[str, float | None]] = {}
    m_ptfs_perf_returns: dict[str, dict[str, float | None]] = {}
    y_ptfs_perf_returns: dict[str, dict[str, float | None]] = {}
    ptfs_drawdowns_stats: dict[str, dict[str, float | None]] = {}

    for scenario in scenarios:
        score_weights = SCORING
        score_weights['eps_rank'] = scenario[0]
        score_weights['sales_rank'] = scenario[1]
        score_weights['price_rank'] = scenario[2]

        ptf_name = (
            f"{PTF_NAME.upper()}_{scenario[0]*100:.0f}-"
            f"{scenario[1]*100:.0f}-{scenario[2]*100:.0f}"
        )

        full_ranked_data = rank.compute_ranked_data(
            rank_input_data=rank_input_data,
            score_weights=score_weights,
        )
        ranked_data = rank_proc.limit_ranked_data_from_start_date(
            ranked_data=full_ranked_data,
            first_ranking_date=first_rank_date
        )
        ranked_data: dict[str, pd.DataFrame] = (
            {date: pd.DataFrame(score) for date, score in ranked_data.items()}
            )
        ranked_data = {
            date: ranked_data[date] for date in sorted(ranked_data)
        }
        ranked_data_output[ptf_name] = ranked_data

        dates_in_ptf_module = importlib.import_module(
            name=f'.dates_{RANK_INTERVAL}',
            package='backtests.dates.dates_in_ptf_plugins'
        )

        stocks_dates_in_ptf = dates_in_ptf_module.get_stocks_dates_in_ptf(
            ranked_data,
            stocks_prices,
            number_of_top_stocks=TOP,
            is_ranking_sma_filtered=IS_RANK_SMA_FILTERED,
            is_ranking_rs_limited=IS_RANK_RS_LIMITED,
            rs_limit=RS_LIMIT
        )

        ptf_all_dates = backtest_dates.get_backtest_dates(stocks_dates_in_ptf)

        m_first_trading_dates = (
            period_first_dates.get_first_trading_dates_of_month(
                ranked_data=ranked_data,
                backtest_dates=ptf_all_dates
            )
        )
        y_first_trading_dates = (
            period_first_dates.get_first_trading_dates_of_year(
                ranked_data=ranked_data,
                backtest_dates=ptf_all_dates
            )
        )

        strategy_module = importlib.import_module(
            name=f'.strategy_{REPLACE_STRATEGY}',
            package=f'backtests.strategies.{RANK_STRATEGY}.strategy_plugins'
        )

        backtest_data = strategy_module.compute_ptf_performance(
            stocks_dates_in_ptf,
            ptf_all_dates,
            stocks_prices,
            m_first_trading_dates,
            is_rebalanced=IS_REBALANCED,
            transaction_fee=TRANSACTION_FEE,
            init_capital=INITIAL_CAPITAL,
        )

        invest = investment.Investment(
            name=PTF_NAME,
            backtest_data=backtest_data[0],
            periods_per_year=252
        )
        ptfs_backtests[ptf_name] = pd.concat([
            backtest_data[0], invest.returns, invest.drawdowns
        ], axis=1)
        ptfs_drawdowns_stats[ptf_name] = invest.drawdowns_stats
        ptfs_perf_metrics[ptf_name] = invest.metrics.to_dict()

        tickers_share_in_ptf_stats = investment.get_tickers_share_in_pft_stats(
            tickers_share_in_ptf=backtest_data[4]
        )
        ptfs_tickers_share_in_ptf_stats[ptf_name] = tickers_share_in_ptf_stats

        tickers_infos = investment.get_tickers_perf_detailed_info(
            tickers_prices=backtest_data[1],
            tickers_returns=backtest_data[2],
            tickers_nav=backtest_data[3],
            tickers_share_in_ptf=backtest_data[4]
        )
        ptfs_tickers_infos[ptf_name] = tickers_infos

        # PTF RETURNS MONTHLY
        m_ptfs_returns = invest.compute_period_returns(
            selected_dates=m_first_trading_dates
        )
        m_ptfs_perf_returns[ptf_name] = m_ptfs_returns.to_dict()

        # PTF RETURNS YEARLY
        y_ptfs_returns = invest.compute_period_returns(
            selected_dates=y_first_trading_dates
        )
        y_ptfs_perf_returns[ptf_name] = y_ptfs_returns.to_dict()
    
    # BENCHMARK
    bench_prices = prices.get_stocks_prices_form_db(
        symbols=[BENCHMARK_TICKER],
        db_file_path=DB_FILE
    )

    bench = benchmark.Benchmark(
        ticker=BENCHMARK_TICKER,
        start_date=ptf_all_dates[0],
        end_date=ptf_all_dates[-1],
        init_capital=INITIAL_CAPITAL,
        prices=bench_prices
    )

    bench_invest = investment.Investment(
        BENCHMARK_TICKER.upper(), bench.nav.to_frame(), PERIODS_PER_YEAR
    )

    # METRICS
    ptfs_perf_metrics_df = pd.DataFrame(ptfs_perf_metrics)
    bench_metrics = bench_invest.metrics
    metrics = bench_metrics.to_frame().merge(
        ptfs_perf_metrics_df, how='left', left_index=True, right_index=True
    )

    # PERIOD RETURNS
    m_ptfs_perf_returns_df = pd.DataFrame(m_ptfs_perf_returns)
    m_bench_returns = bench.compute_period_returns(m_first_trading_dates)
    m_returns = m_bench_returns.to_frame().merge(
        m_ptfs_perf_returns_df, how='left', left_index=True, right_index=True
    )
    y_ptfs_perf_returns_df = pd.DataFrame(y_ptfs_perf_returns)
    y_bench_returns = bench.compute_period_returns(y_first_trading_dates)
    y_returns = y_bench_returns.to_frame().merge(
        y_ptfs_perf_returns_df, how='left', left_index=True, right_index=True
    )

    # ALPHA
    m_alpha = {}
    for ptf_name in m_ptfs_perf_returns_df.columns:
        m_scenario_returns = m_ptfs_perf_returns_df.loc[:, ptf_name]
        m_alpha[f'{ptf_name} alpha'] = m_scenario_returns - m_bench_returns
    m_alpha_df = pd.DataFrame(
        data=m_alpha.values(),
        index=m_alpha.keys()
    ).transpose()

    y_alpha = {}
    for ptf_name in y_ptfs_perf_returns_df.columns:
        y_scenario_returns = y_ptfs_perf_returns_df.loc[:, ptf_name]
        y_alpha[f'{ptf_name} alpha'] = y_scenario_returns - y_bench_returns
    y_alpha_df = pd.DataFrame(
        data=y_alpha.values(),
        index=y_alpha.keys()
    ).transpose()

    # PRINT RESULTS
    print(round(metrics, 2))
    print(round(y_returns * 100, 2))
    print(round(y_alpha_df * 100, 2))

    # SAVE MULTI BACKTEST OUTPUT
    save_backtest_decision = input(
        'Would you like to save backtest data to file? (y/n, default is no): '
    )
    if save_backtest_decision != 'y':
        save_backtest = False
    else:
        save_backtest = True

    if save_backtest:
        with pd.ExcelWriter(
            f'{BACKTEST_OUTPUT_FILE}_demo_{int(scenarios[0][-1]*100)}_from_{first_rank_date}.xlsx'
            ) as writer:
            metrics.to_excel(
                writer, sheet_name='metrics',
                freeze_panes=(1, 0)
            )
            y_returns.to_excel(
                writer, sheet_name='y_returns',
                freeze_panes=(1, 0)
            )
            y_alpha_df.to_excel(
                writer, sheet_name='y_alpha',
                freeze_panes=(1, 0)
            )
            m_returns.to_excel(
                writer, sheet_name='m_returns',
                freeze_panes=(1, 0)
            )
            m_alpha_df.to_excel(
                writer, sheet_name='m_alpha',
                freeze_panes=(1, 0)
            )
            writers.adjust_columns_width(metrics, 'metrics', writer) 
            writers.adjust_columns_width(y_returns, 'y_returns', writer)
            writers.adjust_columns_width(y_alpha_df, 'y_alpha', writer) 
            writers.adjust_columns_width(m_returns, 'm_returns', writer) 
            writers.adjust_columns_width(m_alpha_df, 'm_alpha', writer) 
        logging.info('backtest data saved to file.')

    # SAVE RANKED DATA OUTPUT
    save_ranked_decision = input(
        'Would you like to save ranked data to file? (y/n, default is no): '
    )
    if save_ranked_decision != 'y':
        save_ranked = False
    else:
        save_ranked = True

    if save_ranked:
        for ptf_name, ranked_data in ranked_data_output.items():
            data: dict[str, pd.DataFrame] = (
                {date: pd.DataFrame(score) for date, score in ranked_data.items()}
                )
            with pd.ExcelWriter(f"{RANK_OUTPUT_FILE}_{ptf_name}.xlsx") as writer:
                    for date in sorted(data):
                        new_ranking = data[date]
                        new_ranking = new_ranking.loc[new_ranking['rank'].notna()]
                        if IS_RANK_RS_LIMITED:
                            new_ranking = new_ranking.sort_values(
                                by='price_rank', ascending=False
                            ).iloc[:RS_LIMIT- 1, :]
                        if IS_RANK_SMA_FILTERED:
                            new_ranking = new_ranking.query('sma == 0')
                        new_ranking = new_ranking.sort_values(
                            by='rank', ascending=False
                        ).iloc[:TOP, :]
                        new_ranking.to_excel(
                            writer, sheet_name=date, freeze_panes=(1, 0)
                        )
                        writers.adjust_columns_width(new_ranking, date, writer)
            logging.info(f'ranked data for {ptf_name} saved to file.')

    # SAVE FULL BACKTEST DATA OUTPUT    
    save_perf_decision= input(
        'Would you like to save full backtest data to file? (y/n, default is no): '
    )
    if save_perf_decision != 'y':
        save_perf = False
    else:
        save_perf = True

    if save_perf:
        for ptf_name in ptfs_backtests.keys():
            scenario_metrics = pd.concat(
                [ptfs_perf_metrics_df.loc[:, ptf_name], bench_metrics],
                axis=1
            )
            scenario_full_data = pd.concat([
                ptfs_backtests.get(ptf_name),
                bench.open_prices,
                bench.returns,
                bench.nav,
                bench_invest.drawdowns,
                ptfs_tickers_share_in_ptf_stats.get(ptf_name),
                ptfs_tickers_infos.get(ptf_name)
            ], axis=1)
            scenario_y_returns = pd.concat([
                y_returns.loc[:, ptf_name],
                y_bench_returns,
                y_alpha_df.loc[:, f'{ptf_name} alpha']
                ], axis=1
            )
            scenario_m_returns = pd.concat([
                m_returns.loc[:, ptf_name],
                m_bench_returns,
                m_alpha_df.loc[:, f'{ptf_name} alpha']
                ], axis=1
            )
            scenario_drawdowns_stats = pd.concat((
                ptfs_drawdowns_stats.get(ptf_name),
                bench_invest.drawdowns_stats
            ), axis=1)

            with pd.ExcelWriter(f'{PERF_OUTPUT_FILE}_{ptf_name}.xlsx') as writer:
                scenario_metrics.to_excel(
                    writer, sheet_name='metrics',
                    freeze_panes=(1, 0)
                )
                scenario_full_data.to_excel(
                    writer, sheet_name='d_full_data',
                    freeze_panes=(1, 0)
                )
                scenario_y_returns.to_excel(
                    writer, sheet_name='y_returns', index=True,
                    freeze_panes=(1, 0)
                )
                scenario_m_returns.to_excel(
                    writer, sheet_name='m_returns', index=True,
                    freeze_panes=(1, 0)
                )
                scenario_drawdowns_stats.to_excel(
                    writer, sheet_name='drawdowns_stats', index=False,
                    freeze_panes=(1, 0)
                )
                writers.adjust_columns_width(scenario_metrics, 'metrics', writer)
                writers.adjust_columns_width(scenario_full_data, 'd_full_data', writer) 
                writers.adjust_columns_width(scenario_y_returns, 'y_returns', writer) 
                writers.adjust_columns_width(scenario_m_returns, 'm_returns', writer) 
                writers.adjust_columns_width(scenario_drawdowns_stats, 'drawdowns_stats', writer) 

                logging.info(f'full backtest data for {ptf_name} saved to file.')


if __name__ == '__main__':
    main()