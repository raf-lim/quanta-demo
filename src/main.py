import logging
import tomllib
from libs.helpers.argparser import parser


logging.basicConfig(level=logging.INFO)

args = parser.parse_args()


def main() -> None:

    if args.get_tickers:
        from symbols.index import main
        main()
    
    if args.get_fs:
        from financials.index import main
        main()

    if args.get_prices:
        from prices.index import main
        main()

    if args.rank_input:
        from ranks.esr.index import main
        main()

    if args.backtest:
        from backtests import index

        scenarios_name = 'multi_price_0'
        first_rank_date = '2019-12-31'

        with open('config.toml', 'rb') as file:
            config = tomllib.load(file)
        rank_strategy = config['rank']['strategy']
        with open('rank_scenarios.toml', 'rb') as file:
            scenarios = tomllib.load(file)[rank_strategy][scenarios_name]

        index.main(scenarios, first_rank_date)
        

if __name__ == '__main__':
    main()