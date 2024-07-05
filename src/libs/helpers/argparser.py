import argparse


parser = argparse.ArgumentParser()

parser.add_argument(
    '--get_tickers',
    action='store_true',
    help='load, process and save tickers'
)
parser.add_argument(
    '--get_fs',
    action='store_true',
    help='load, process and save financial statements data '
)
parser.add_argument(
    '--get_prices',
    action='store_true',
    help='load, process and save prices data from API.'
)
parser.add_argument(
    '--bongo_weekly',
    action='store_true',
    help='compute and save bongo weekly data for all stocks'
)
parser.add_argument(
    '--rank_input',
    action='store_true',
    help='create and save interval data of stocks for ranking.'
)
parser.add_argument(
    '--perf_esr_vanilla',
    action='store_true',
    help='run basic (vanilla) ESR replacement strategy on top ranked'
)
parser.add_argument(
    '--latest_rank',
    action='store_true',
    help='compute latest ranking'
)
parser.add_argument(
    '--data_check',
    action='store_true',
    help='get selected metrics for data cross check'
)
parser.add_argument(
    '--backtest',
    action='store_true',
    help='check multiple score weights for performance'
)
parser.add_argument(
    '--save_backtest',
    action='store_true',
    help='save backtest results to file'
)
parser.add_argument(
    '--save_ranked',
    action='store_true',
    help='save scenario ranked data to files\' series'
)
