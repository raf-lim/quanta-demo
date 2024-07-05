import pandas as pd


def compute_ranked_data(
        rank_input_data: dict[str, dict[str, dict[str, float]]],
        score_weights: dict[str, float],
        na_option: str = 'keep'
    ) -> dict:
    """Rank stocks by intervals data * score weights."""

    rank_output_data = {}
    
    for rank_date, stocks_data in rank_input_data.items():

        score = pd.DataFrame(stocks_data).transpose()

        # Not removing NaN values, put zero instead.
        # Prevents removing stock from ranking if e.g. only one metric is NaN.
        score.iloc[:, :9] = score.iloc[:, :9].fillna(0)

        eps_ranking = (
            score['eps_growth'].rank(na_option=na_option) * score_weights['eps_growth']
            + score['eps_growth_acceleration'].rank(na_option=na_option) * score_weights['eps_growth_acceleration']
        ).rank()
        eps_ranking.name = 'eps_rank'
        score = score.merge(
            eps_ranking, how='inner', left_index=True, right_index=True
        )

        sales_ranking = (
            score['mean_sales_growth'].rank(na_option=na_option) * score_weights['mean_sales_growth']
            + score['sales_growth_acceleration'].rank(na_option=na_option) * score_weights['sales_growth_acceleration']
        ).rank()
        sales_ranking.name = 'sales_rank'
        score = score.merge(
            sales_ranking, how='inner', left_index=True, right_index=True
        )

        price_ranking = (
            score['lq_0_perf'].rank(na_option=na_option) * score_weights['lq_0_perf']
            + score['lq_1_perf'].rank(na_option=na_option) * score_weights['lq_1_perf']
        ).rank()
        price_ranking.name = 'price_rank'
        score = score.merge(
            price_ranking, how='inner', left_index=True, right_index=True
        )

        ranking = (
            score['eps_rank'].rank(na_option=na_option) * score_weights['eps_rank']
            + score['sales_rank'].rank(na_option=na_option) * score_weights['sales_rank']
            + score['price_rank'].rank(na_option=na_option) * score_weights['price_rank']
            ).rank(na_option=na_option)
        ranking.name = 'rank'
        score = score.merge(
            ranking, how='inner', left_index=True, right_index=True
        )

        rank_output_data[rank_date] = score.to_dict()

    return rank_output_data
